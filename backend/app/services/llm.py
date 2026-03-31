from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Iterator

from fastapi import HTTPException, status
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

from app.core.config import settings


class LLMProviderError(RuntimeError):
    pass


@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    provider_response_id: str | None = None


@dataclass
class LLMStreamEvent:
    type: str
    delta: str = ""
    usage: LLMUsage | None = None


@dataclass
class ProviderConfig:
    provider: str
    api_key: str | None
    base_url: str | None
    default_model: str
    label: str


class CompatibleResponsesService:
    def __init__(self) -> None:
        self._clients: dict[str, OpenAI] = {}

    def get_provider_config(self, provider: str) -> ProviderConfig:
        normalized = provider.strip().lower()
        configs = {
            "openai": ProviderConfig(
                provider="openai",
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                default_model=settings.openai_model,
                label="OpenAI",
            ),
            "qwen": ProviderConfig(
                provider="qwen",
                api_key=settings.qwen_api_key or settings.dashscope_api_key,
                base_url=settings.qwen_base_url,
                default_model=settings.qwen_model,
                label="Qwen / DashScope",
            ),
            "doubao": ProviderConfig(
                provider="doubao",
                api_key=settings.doubao_api_key or settings.ark_api_key,
                base_url=settings.doubao_base_url,
                default_model=settings.doubao_model,
                label="Doubao / Ark",
            ),
        }

        config = configs.get(normalized)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unsupported LLM provider: {provider}",
            )
        return config

    def ensure_configured(self, provider: str) -> ProviderConfig:
        config = self.get_provider_config(provider)
        if not config.api_key:
            env_hint = {
                "openai": "OPENAI_API_KEY",
                "qwen": "QWEN_API_KEY or DASHSCOPE_API_KEY",
                "doubao": "DOUBAO_API_KEY or ARK_API_KEY",
            }[config.provider]
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{config.label} is not configured. Add {env_hint} to your .env before using this assistant.",
            )
        return config

    def get_client(self, provider: str) -> tuple[OpenAI, ProviderConfig]:
        config = self.ensure_configured(provider)
        if config.provider not in self._clients:
            client_kwargs: dict[str, Any] = {
                "api_key": config.api_key,
                "timeout": settings.openai_timeout_seconds,
            }
            if config.base_url:
                client_kwargs["base_url"] = config.base_url
            self._clients[config.provider] = OpenAI(**client_kwargs)
        return self._clients[config.provider], config

    def stream_response(
        self,
        *,
        provider: str,
        model: str,
        instructions: str,
        history: list[dict[str, str]],
        temperature: float,
        top_p: float,
        max_output_tokens: int | None,
        metadata: dict[str, str],
    ) -> Iterator[LLMStreamEvent]:
        started = perf_counter()
        saw_delta = False

        try:
            client, config = self.get_client(provider)
            request_kwargs: dict[str, Any] = {
                "model": model or config.default_model,
                "instructions": instructions,
                "input": history,
                "temperature": temperature,
                "top_p": top_p,
                "max_output_tokens": max_output_tokens or settings.default_max_output_tokens,
                "stream": True,
                "store": False,
            }
            if metadata and config.provider != "doubao":
                request_kwargs["metadata"] = metadata

            stream = client.responses.create(
                **request_kwargs,
            )
        except (APIConnectionError, APITimeoutError) as exc:
            raise LLMProviderError("无法连接到模型接口，请检查网络、代理或服务地址配置。") from exc
        except RateLimitError as exc:
            raise LLMProviderError("模型调用已触发限流，请稍后重试。") from exc
        except APIStatusError as exc:
            detail = getattr(exc, "message", None) or "模型服务返回了异常状态。"
            raise LLMProviderError(str(detail)) from exc
        except Exception as exc:  # noqa: BLE001
            raise LLMProviderError(f"初始化模型请求失败：{exc}") from exc

        try:
            for event in stream:
                event_type = getattr(event, "type", "")
                if event_type == "response.output_text.delta":
                    delta = getattr(event, "delta", "")
                    if delta:
                        saw_delta = True
                        yield LLMStreamEvent(type="delta", delta=delta)

                if event_type == "response.completed":
                    response = getattr(event, "response", None)
                    response_text = getattr(response, "output_text", "") if response else ""
                    usage = getattr(response, "usage", None) if response else None

                    if response_text and not saw_delta:
                        yield LLMStreamEvent(type="delta", delta=response_text)

                    yield LLMStreamEvent(
                        type="completed",
                        usage=LLMUsage(
                            prompt_tokens=int(getattr(usage, "input_tokens", 0) or 0),
                            completion_tokens=int(getattr(usage, "output_tokens", 0) or 0),
                            total_tokens=int(getattr(usage, "total_tokens", 0) or 0),
                            latency_ms=int((perf_counter() - started) * 1000),
                            provider_response_id=getattr(response, "id", None) if response else None,
                        ),
                    )

                if event_type in {"response.failed", "response.error"}:
                    detail = getattr(event, "error", None)
                    raise LLMProviderError(str(detail or "模型流式响应失败。"))
        except LLMProviderError:
            raise
        except (APIConnectionError, APITimeoutError) as exc:
            raise LLMProviderError("模型流式响应中断，请检查网络或稍后重试。") from exc
        except RateLimitError as exc:
            raise LLMProviderError("模型调用已触发限流，请稍后重试。") from exc
        except APIStatusError as exc:
            detail = getattr(exc, "message", None) or "模型服务返回了异常状态。"
            raise LLMProviderError(str(detail)) from exc
        except Exception as exc:  # noqa: BLE001
            raise LLMProviderError(f"模型流式响应失败：{exc}") from exc
