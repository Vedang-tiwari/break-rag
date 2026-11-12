"""Abstract base class for all Break-RAG adapters."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from breakrag.models.adapter import RAGRequest, RAGResponse


class BaseRAGAdapter(ABC):
    """Common interface normalizing any RAG system to Break-RAG schemas."""

    adapter_type: str = "base"

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    @staticmethod
    def _coerce_request(request: RAGRequest | str) -> RAGRequest:
        if isinstance(request, str):
            return RAGRequest(question=request)
        return request

    @abstractmethod
    def query(self, request: RAGRequest | str) -> RAGResponse:
        """Execute a synchronous RAG query and return a normalized RAGResponse."""

    async def aquery(self, request: RAGRequest | str) -> RAGResponse:
        """Execute an asynchronous RAG query. Subclasses may override natively."""
        return await asyncio.to_thread(self.query, request)

    def get_metadata(self) -> dict[str, Any]:
        """Return safe, non-secret metadata describing this adapter."""
        return {
            "adapter_type": self.adapter_type,
            "timeout": self.timeout,
        }

    def health_check(self) -> bool:
        """Verify that the adapter is operational."""
        return True

