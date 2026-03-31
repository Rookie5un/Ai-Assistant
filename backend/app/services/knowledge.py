from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from typing import Iterable

from docx import Document as DocxDocument
from fastapi import UploadFile
from pypdf import PdfReader


WORD_PATTERN = re.compile(r"[\w\u4e00-\u9fff]{2,}", re.UNICODE)


def extract_text_from_upload(upload: UploadFile) -> str:
    suffix = Path(upload.filename or "").suffix.lower()
    payload = upload.file.read()

    if suffix in {".txt", ".md", ".markdown"}:
        return payload.decode("utf-8", errors="ignore")

    if suffix == ".pdf":
        reader = PdfReader(BytesIO(payload))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if suffix == ".docx":
        document = DocxDocument(BytesIO(payload))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

    raise ValueError("Only PDF, DOCX, TXT, and Markdown files are supported in this starter.")


def chunk_text(text: str, chunk_size: int = 480, overlap: int = 80) -> list[str]:
    clean_text = re.sub(r"\s+", " ", text).strip()
    if not clean_text:
        return []

    if len(clean_text) <= chunk_size:
        return [clean_text]

    chunks: list[str] = []
    start = 0
    while start < len(clean_text):
        end = min(start + chunk_size, len(clean_text))
        chunk = clean_text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(clean_text):
            break
        start = max(end - overlap, 0)
    return chunks


def extract_keywords(text: str) -> str:
    words = WORD_PATTERN.findall(text.lower())
    unique_words = list(dict.fromkeys(words))
    return ",".join(unique_words[:50])


def score_chunk(query: str, content: str, keywords: str) -> int:
    query_terms = set(WORD_PATTERN.findall(query.lower()))
    keyword_terms = set(term for term in keywords.split(",") if term)
    content_terms = set(WORD_PATTERN.findall(content.lower()))
    return len(query_terms & keyword_terms) * 3 + len(query_terms & content_terms)


def format_citations(matches: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    citations: list[dict[str, str]] = []
    for match in matches:
        citations.append(
            {
                "title": match["title"],
                "snippet": match["content"][:180].strip(),
            }
        )
    return citations

