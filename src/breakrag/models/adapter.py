"""Adapter request and normalized response schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class DocumentInput(BaseModel):
    """A controlled document injected for isolated evaluation or adversarial testing."""

    id: str
    content: str
    title: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    """Normalized citation returned by a RAG application."""

    document_id: str | None = None
    claim: str | None = None
    source_text: str | None = None
    raw: str | None = None


class TokenUsage(BaseModel):
    """Observed token usage and optional estimated cost."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None


class RAGRequest(BaseModel):
    """Input payload dispatched to a RAG adapter."""

    question: str
    top_k: int = Field(default=5, ge=1)
    injected_documents: list[DocumentInput] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGResponse(BaseModel):
    """Normalized response returned from any RAG adapter.

    Unavailable fields remain None rather than being fabricated.
    Latency is measured in seconds.
    """

    question: str
    answer: str | None = None
    retrieved_documents: list[str] | None = None
    document_ids: list[str] | None = None
    retrieval_scores: list[float] | None = None
    citations: list[Citation] | None = None
    latency: float | None = Field(default=None, ge=0.0)
    token_usage: TokenUsage | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: Literal["ok", "error", "timeout"] = "ok"
    error: str | None = None

