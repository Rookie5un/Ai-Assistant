# AI Assistant Web

一个面向个人开发与小团队场景的 AI 助手 Web MVP，基于 `Vue 3 + FastAPI` 构建，支持多轮对话、知识库问答、助手配置以及多模型 Provider 接入。

当前项目已经接通以下真实模型能力：

- `OpenAI`
- `千问 / 阿里云百炼`
- `豆包 / 火山方舟`

其中每个助手都可以单独选择自己的 Provider 与模型，不需要全局共用一套模型配置。

## Features

- 用户登录与演示账号
- 会话列表与多轮对话
- `SSE` 流式输出
- 助手创建与模型配置
- 知识库创建、文件上传与基础检索
- 支持 `PDF / DOCX / TXT / Markdown`
- 支持 `OpenAI / 千问 / 豆包` 三种 Provider
- 默认使用 `SQLite` 本地启动
- 提供 `PostgreSQL` 的 `docker-compose` 开发入口

## Tech Stack

前端：

- `Vue 3`
- `TypeScript`
- `Vite`
- `Vue Router`
- `Pinia`

后端：

- `FastAPI`
- `SQLAlchemy`
- `Pydantic`
- `PyJWT`

AI 与数据层：

- `OpenAI Python SDK`
- `SQLite` 默认开发库
- `PostgreSQL` 可选

## Project Structure

```text
.
├── backend/                # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # API routes
│   │   ├── core/           # config / db / security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # chat / knowledge / llm / seed
│   └── requirements.txt
├── frontend/               # Vue app
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── router/
│   │   ├── stores/
│   │   └── views/
├── docker-compose.yml
├── .env.example
├── PRD.md
└── README.md
```

## Quick Start

### 1. Clone

```bash
git clone git@github.com:Rookie5un/Ai-Assistant.git
cd Ai-Assistant
```

### 2. Prepare Environment

复制环境变量文件：

```bash
cp .env.example .env
```

如果你要使用真实模型，请在 `.env` 中填入对应 Provider 的 Key。

### 3. Start Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

后端地址：

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/health`

### 4. Start Frontend

新开一个终端窗口：

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

前端地址：

- `http://127.0.0.1:5173`

### 5. Demo Account

默认演示账号：

- Email: `demo@aicontrol.dev`
- Password: `Demo123456!`

## Model Provider Configuration

项目当前支持三类 Provider。

### OpenAI

```text
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=
OPENAI_MODEL=gpt-4.1-mini
```

### Qwen / DashScope

```text
QWEN_API_KEY=your_dashscope_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/api/v2/apps/protocols/compatible-mode/v1
QWEN_MODEL=qwen3.5-plus
```

也可以使用：

```text
DASHSCOPE_API_KEY=your_dashscope_key
```

### Doubao / Ark

```text
DOUBAO_API_KEY=your_ark_key
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL=doubao-seed-2-0-pro-260215
```

也可以使用：

```text
ARK_API_KEY=your_ark_key
```

## PostgreSQL Development Setup

默认开发环境使用 `SQLite`，不依赖额外数据库服务。

如果你想切换到 `PostgreSQL`：

### 1. 启动 PostgreSQL

```bash
docker compose up -d postgres
```

### 2. 修改 `.env`

把：

```text
DATABASE_URL=sqlite:///./storage/app.db
```

改成：

```text
DATABASE_URL=postgresql+psycopg://ai_user:ai_password@localhost:5432/ai_assistant
```

### 3. 重新启动后端

## Current Capabilities

当前版本已经实现：

- 基础账号体系
- 会话管理
- 助手配置与 Provider 选择
- 知识库与文件解析
- SSE 流式聊天
- 助手级模型切换
- 知识库片段注入到模型上下文

当前版本尚未实现或仅为 MVP：

- Alembic 迁移体系
- 企业级权限与多租户
- 复杂工具调用与 Agent 工作流
- 完整后台运营系统
- 向量数据库与高质量 RAG 检索链路

## Security Notes

- `.env` 已被 `.gitignore` 忽略，不会默认提交到仓库
- 不要把真实 API Key 提交到 GitHub
- 如果密钥曾在聊天、截图或提交记录中明文出现，建议尽快旋转

## Development Notes

这个项目当前更适合作为一个“可继续扩展的 MVP 骨架”，适合继续往以下方向演进：

- 接更多模型 Provider
- 引入 `Alembic + PostgreSQL`
- 接入向量检索
- 增加消息重试、会话归档、助手编辑
- 增加管理员统计和审计日志

## Roadmap

- [ ] 补齐数据库迁移
- [ ] 增加助手编辑与删除
- [ ] 增加知识库引用高亮与来源定位
- [ ] 增加多模型回退策略
- [ ] 增加管理员后台与使用量统计
- [ ] 接入更完整的 RAG 流程

## References

本项目当前接入或参考的主要官方接口：

- OpenAI Responses API
- 阿里云百炼 OpenAI 兼容接口
- 火山方舟 OpenAI 兼容接口

