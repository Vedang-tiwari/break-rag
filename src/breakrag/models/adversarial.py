"""Adversarial attack schemas, outcome statuses, and summary models."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from breakrag.models.adapter import DocumentInput, RAGResponse


class AttackCategory(str, Enum):
    """Ten adversarial RAG testing categories defined in Break-RAG."""

    PROMPT_INJECTION = "prompt_injection"
    CONTEXT_POISONING = "context_poisoning"
    AMBIGUOUS_QUERIES = "ambiguous_queries"
    UNANSWERABLE = "unanswerable"
    CONFLICTING_DOCUMENTS = "conflicting_documents"
    RETRIEVAL_MANIPULATION = "retrieval_manipulation"
    MULTI_HOP = "multi_hop"
    INFORMATION_LEAKAGE = "information_leakage"
    CONTEXT_OVERLOAD = "context_overload"
    CITATION_MANIPULATION = "citation_manipulation"


class Severity(str, Enum):
    """Vulnerability severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AttackStatus(str, Enum):
    """Explicit classification of adversarial test outcomes."""

    RESISTED = "RESISTED"
    SUCCEEDED = "SUCCEEDED"
    PARTIAL = "PARTIAL"
    INCONCLUSIVE = "INCONCLUSIVE"
    EXECUTION_ERROR = "EXECUTION_ERROR"


class DifficultyLevel(str, Enum):
    """Attack sophistication level."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class GenerationMode(str, Enum):
    """Strategy used to generate attack cases."""

    RULE_BASED = "rule_based"
    LLM_BASED = "llm_based"


class AttackCase(BaseModel):
    """Single reproducible adversarial test case."""

    attack_id: str
    category: AttackCategory
    description: str
    input_question: str
    modified_documents: list[DocumentInput] = Field(default_factory=list)
    expected_behavior: str
    severity: Severity = Severity.MEDIUM
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    generation_mode: GenerationMode = GenerationMode.RULE_BASED
    seed: int | None = None
    ground_truth: str | None = None
    forbidden_patterns: list[str] = Field(default_factory=list)
    expected_document_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AttackResult(BaseModel):
    """Result of executing and scoring one adversarial attack case."""

    attack_id: str
    category: AttackCategory
    description: str
    input_question: str
    modified_documents: list[DocumentInput] = Field(default_factory=list)
    expected_behavior: str
    actual_behavior: str
    response: RAGResponse
    severity: Severity
    status: AttackStatus
    passed: bool | None = None
    failure_reason: str | None = None
    remediation: str | None = None
    execution_metadata: dict[str, Any] = Field(default_factory=dict)


class AdversarialSummary(BaseModel):
    """Aggregated adversarial attack statistics.

    PARTIAL, INCONCLUSIVE, and EXECUTION_ERROR are tracked explicitly
    and never collapsed into binary pass/fail counts.
    """

    total_attacks: int
    valid_executed_attacks: int
    resisted_count: int
    succeeded_count: int
    partial_count: int
    inconclusive_count: int
    execution_error_count: int
    attack_success_rate: float | None = None
    attack_resistance_rate: float | None = None
    category_breakdown: dict[str, dict[str, Any]] = Field(default_factory=dict)
    severity_breakdown: dict[str, dict[str, int]] = Field(default_factory=dict)
    most_vulnerable_categories: list[str] = Field(default_factory=list)

