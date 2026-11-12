"""Benchmark run and comparison schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from breakrag.models.adversarial import AdversarialSummary, AttackResult
from breakrag.models.evaluation import EvalCaseResult, EvaluationSummary


class BenchmarkRun(BaseModel):
    """Complete record of an evaluation, adversarial, or full benchmark execution."""

    run_id: str
    timestamp: str
    mode: Literal["evaluate", "attack", "full"]
    adapter_metadata: dict[str, Any] = Field(default_factory=dict)
    dataset_info: dict[str, Any] = Field(default_factory=dict)
    config_snapshot: dict[str, Any] = Field(default_factory=dict)
    eval_results: list[EvalCaseResult] = Field(default_factory=list)
    eval_summary: EvaluationSummary | None = None
    attack_results: list[AttackResult] = Field(default_factory=list)
    attack_summary: AdversarialSummary | None = None
    overall_robustness_score: float | None = None
    report_paths: dict[str, str] = Field(default_factory=dict)


class BenchmarkComparison(BaseModel):
    """Structured comparison between two stored benchmark runs."""

    run_a_id: str
    run_b_id: str
    run_a_timestamp: str
    run_b_timestamp: str
    eval_metric_deltas: dict[str, float | None] = Field(default_factory=dict)
    adversarial_deltas: dict[str, float | int | None] = Field(default_factory=dict)
    category_comparisons: list[dict[str, Any]] = Field(default_factory=list)
    summary_notes: list[str] = Field(default_factory=list)

