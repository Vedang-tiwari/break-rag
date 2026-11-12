"""RAG adapters normalizing heterogeneous RAG systems into a common schema."""

from breakrag.adapters.base import BaseRAGAdapter
from breakrag.adapters.mock import DEFAULT_MOCK_KB, MockRAGAdapter

__all__ = ["BaseRAGAdapter", "DEFAULT_MOCK_KB", "MockRAGAdapter"]

