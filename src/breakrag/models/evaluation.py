"""Evaluation dataset, case result, and summary schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from breakrag.models.adapter import RAGResponse


class EvalCase(BaseModel):
    """Single evaluation test case loaded from JSON or CSV."""

    test_id: str
    question: str
    ground_truth: str | None = None
    expected_document_ids: list[str] = Field(default_factory=list)
    category: str = "general"
    expected_behavior: str = "answer_accurately"
    metadata: dict[str, Any] = Field(default_factory=dict)


class MetricRecord(BaseModel):
    """Individual metric score tagged with provenance."""

    name: str
    value: float | None = None
    source: Literal["deterministic", "llm_judge", "observed", "estimated"] = "deterministic"
    details: dict[str, Any] = Field(default_factory=dict)


class EvalCaseResult(BaseModel):
    """Per-case evaluation output preserving raw adapter response and metric provenance."""

    test_id: str
    category: str
    question: str
    ground_truth: str | None = None
    expected_document_ids: list[str] = Field(default_factory=list)
    expected_behavior: str = "answer_accurately"
    response: RAGResponse
    retrieval_metrics: dict[str, float | None] = Field(default_factory=dict)
    generation_metrics: dict[str, float | None] = Field(default_factory=dict)
    citation_metrics: dict[str, float | None] = Field(default_factory=dict)
    metric_sources: dict[str, str] = Field(default_factory=dict)
    judge_metadata: dict[str, Any] | None = None
    passed: bool | None = None
    failure_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationSummary(BaseModel):
    """Aggregated evaluation metrics with explicit missing-value tracking."""

    total_cases: int
    executed_cases: int
    error_cases: int
    passed_cases: int
    failed_cases: int
    retrieval_metrics: dict[str, float | None] = Field(default_factory=dict)
    generation_metrics: dict[str, float | None] = Field(default_factory=dict)
    citation_metrics: dict[str, float | None] = Field(default_factory=dict)
    performance_metrics: dict[str, float | int | None] = Field(default_factory=dict)
    category_metrics: dict[str, dict[str, Any]] = Field(default_factory=dict)
    metric_sources: dict[str, str] = Field(default_factory=dict)
    missing_counts: dict[str, int] = Field(default_factory=dict)

