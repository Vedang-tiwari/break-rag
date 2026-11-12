"""Configuration schemas for Break-RAG with environment variable support."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ProjectConfig(BaseModel):
    """Top-level project metadata and reproducibility settings."""

    name: str = "Break-RAG"
    environment: str = "development"
    random_seed: int = 42
    log_level: str = "INFO"
    json_logs: bool = False


class RetryPolicyConfig(BaseModel):
    """Retry configuration for HTTP and adapter requests."""

    max_retries: int = Field(default=2, ge=0, le=10)
    backoff_factor: float = Field(default=0.5, ge=0.0)
    retry_statuses: list[int] = Field(default_factory=lambda: [429, 500, 502, 503, 504])


class AuthConfig(BaseModel):
    """Authentication configuration referencing environment variable names for secrets."""

    type: Literal["none", "bearer", "api_key", "basic"] = "none"
    token_env: str | None = None
    header_name: str = "Authorization"
    header_prefix: str = "Bearer"
    username_env: str | None = None
    password_env: str | None = None


class AdapterConfig(BaseModel):
    """RAG adapter settings supporting mock, function, and HTTP integrations."""

    type: Literal["mock", "http", "function"] = "mock"
    timeout: float = Field(default=30.0, gt=0.0)
    mock_profile: Literal["healthy", "vulnerable", "hallucinating", "leaky"] = "healthy"
    endpoint_url: str | None = None
    method: Literal["POST", "GET"] = "POST"
    headers: dict[str, str] = Field(default_factory=dict)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    request_mapping: dict[str, str] = Field(
        default_factory=lambda: {"question": "question", "top_k": "top_k"}
    )
    response_mapping: dict[str, str] = Field(
        default_factory=lambda: {
            "answer": "answer",
            "retrieved_documents": "retrieved_documents",
            "document_ids": "document_ids",
            "retrieval_scores": "retrieval_scores",
            "citations": "citations",
            "token_usage": "token_usage",
            "metadata": "metadata",
        }
    )
    retry_policy: RetryPolicyConfig = Field(default_factory=RetryPolicyConfig)
    static_params: dict[str, Any] = Field(default_factory=dict)


class LLMProviderConfig(BaseModel):
    """Optional LLM provider settings for LLM-judge and LLM attack generation."""

    enabled: bool = False
    provider: Literal["openai_compatible", "ollama", "mock"] = "openai_compatible"
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    api_key_env: str = "BREAKRAG_LLM_API_KEY"
    prompt_version: str = "v1.0"
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    timeout: float = Field(default=30.0, gt=0.0)


class EvaluationConfig(BaseModel):
    """Evaluation harness settings."""

    enabled: bool = True
    dataset_path: str = "datasets/evaluation/sample_questions.json"
    top_k: int = Field(default=5, ge=1)
    metrics: list[str] = Field(
        default_factory=lambda: [
            "precision_at_k",
            "recall_at_k",
            "hit_rate_at_k",
            "mrr",
            "ndcg_at_k",
            "answer_correctness",
            "answer_relevance",
            "faithfulness",
            "context_relevance",
            "hallucination_rate",
            "citation_precision",
            "citation_recall",
            "citation_coverage",
            "unsupported_claim_rate",
        ]
    )
    prompt_token_cost_per_1k: float = Field(default=0.0, ge=0.0)
    completion_token_cost_per_1k: float = Field(default=0.0, ge=0.0)
    llm_judge: LLMProviderConfig = Field(default_factory=LLMProviderConfig)


class AttackCategoryConfig(BaseModel):
    """Per-category adversarial attack toggle, count, difficulty, and severity override."""

    enabled: bool = True
    count: int = Field(default=10, ge=1, le=500)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    severity_override: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] | None = None


def _default_attack_configs() -> dict[str, AttackCategoryConfig]:
    return {
        "prompt_injection": AttackCategoryConfig(enabled=True, count=10),
        "context_poisoning": AttackCategoryConfig(enabled=True, count=10),
        "ambiguous_queries": AttackCategoryConfig(enabled=True, count=10),
        "unanswerable": AttackCategoryConfig(enabled=True, count=10),
        "conflicting_documents": AttackCategoryConfig(enabled=True, count=10),
        "retrieval_manipulation": AttackCategoryConfig(enabled=True, count=10),
        "multi_hop": AttackCategoryConfig(enabled=True, count=10),
        "information_leakage": AttackCategoryConfig(enabled=True, count=10),
        "context_overload": AttackCategoryConfig(enabled=True, count=10),
        "citation_manipulation": AttackCategoryConfig(enabled=True, count=10),
    }


class AdversarialConfig(BaseModel):
    """Adversarial harness and attack generation settings."""

    enabled: bool = True
    generation_mode: Literal["rule_based", "llm_based"] = "rule_based"
    save_generated_path: str = "results/generated_attacks"
    attacks: dict[str, AttackCategoryConfig] = Field(default_factory=_default_attack_configs)
    llm_generator: LLMProviderConfig = Field(default_factory=LLMProviderConfig)


class ExecutionConfig(BaseModel):
    """Concurrency, rate limiting, and robustness weighting configuration."""

    concurrency: int = Field(default=4, ge=1, le=64)
    rate_limit_per_second: float | None = Field(default=None, gt=0.0)
    compute_robustness_score: bool = True
    evaluation_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    adversarial_weight: float = Field(default=0.6, ge=0.0, le=1.0)

    @field_validator("adversarial_weight")
    @classmethod
    def check_weights_non_negative(cls, v: float) -> float:
        return v


class ReportingConfig(BaseModel):
    """Output formats and report directory settings."""

    output_dir: str = "results/reports"
    formats: list[Literal["html", "json", "csv", "excel"]] = Field(
        default_factory=lambda: ["html", "json", "csv"]
    )


class StorageConfig(BaseModel):
    """SQLite persistence settings."""

    type: Literal["sqlite"] = "sqlite"
    database_path: str = "results/breakrag.db"


class BreakRAGConfig(BaseModel):
    """Root validated Break-RAG configuration."""

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    adapter: AdapterConfig = Field(default_factory=AdapterConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    adversarial: AdversarialConfig = Field(default_factory=AdversarialConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    environments: dict[str, dict[str, Any]] = Field(default_factory=dict)

