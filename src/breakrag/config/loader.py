"""YAML configuration loader, environment override resolver, and secret scrubber."""

from __future__ import annotations

import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import ValidationError

from breakrag.config.models import BreakRAGConfig

_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-(.*?))?\}")
_SENSITIVE_KEY_TOKENS = ("key", "secret", "token", "password", "authorization", "credential")


class ConfigError(ValueError):
    """Raised when a Break-RAG configuration file cannot be loaded or validated."""


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _interpolate_env_vars(value: Any) -> Any:
    if isinstance(value, str):
        def _replace(match: re.Match[str]) -> str:
            var_name = match.group(1)
            default_val = match.group(2)
            env_val = os.environ.get(var_name)
            if env_val is not None:
                return env_val
            if default_val is not None:
                return default_val
            return ""

        return _ENV_PATTERN.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _interpolate_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate_env_vars(item) for item in value]
    return value


def _apply_env_overrides(raw: dict[str, Any]) -> dict[str, Any]:
    data = deepcopy(raw)
    project = data.setdefault("project", {})
    adapter = data.setdefault("adapter", {})
    storage = data.setdefault("storage", {})
    reporting = data.setdefault("reporting", {})
    execution = data.setdefault("execution", {})

    if os.environ.get("BREAKRAG_ENV"):
        project["environment"] = os.environ["BREAKRAG_ENV"]
    if os.environ.get("BREAKRAG_LOG_LEVEL"):
        project["log_level"] = os.environ["BREAKRAG_LOG_LEVEL"]
    if os.environ.get("BREAKRAG_RANDOM_SEED"):
        try:
            project["random_seed"] = int(os.environ["BREAKRAG_RANDOM_SEED"])
        except ValueError as exc:
            raise ConfigError("BREAKRAG_RANDOM_SEED must be an integer") from exc
    if os.environ.get("BREAKRAG_ADAPTER_TYPE"):
        adapter["type"] = os.environ["BREAKRAG_ADAPTER_TYPE"]
    if os.environ.get("BREAKRAG_ENDPOINT_URL"):
        adapter["endpoint_url"] = os.environ["BREAKRAG_ENDPOINT_URL"]
    if os.environ.get("BREAKRAG_DB_PATH"):
        storage["database_path"] = os.environ["BREAKRAG_DB_PATH"]
    if os.environ.get("BREAKRAG_OUTPUT_DIR"):
        reporting["output_dir"] = os.environ["BREAKRAG_OUTPUT_DIR"]
    if os.environ.get("BREAKRAG_CONCURRENCY"):
        try:
            execution["concurrency"] = int(os.environ["BREAKRAG_CONCURRENCY"])
        except ValueError as exc:
            raise ConfigError("BREAKRAG_CONCURRENCY must be an integer") from exc
    return data


def load_config(
    config_path: str | Path | None = None,
    environment: str | None = None,
    load_env_file: bool = True,
) -> BreakRAGConfig:
    """Load, interpolate, environment-merge, and validate BreakRAGConfig."""
    if load_env_file:
        load_dotenv(override=False)

    raw: dict[str, Any] = {}
    if config_path is not None:
        path = Path(config_path)
        if not path.exists():
            raise ConfigError(f"Configuration file not found: {path}")
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc
        if loaded is not None:
            if not isinstance(loaded, dict):
                raise ConfigError(f"Configuration root in {path} must be a mapping")
            raw = loaded

    raw = _interpolate_env_vars(raw)
    raw = _apply_env_overrides(raw)

    target_env = environment or raw.get("project", {}).get("environment")
    environments_map = raw.get("environments") or {}
    if target_env and isinstance(environments_map, dict) and target_env in environments_map:
        env_override = environments_map[target_env]
        if isinstance(env_override, dict):
            raw = _deep_merge(raw, env_override)

    try:
        return BreakRAGConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"Configuration validation failed:\n{exc}") from exc


def scrub_secrets(payload: Any) -> Any:
    """Recursively redact sensitive keys before storing metadata or rendering reports."""
    if isinstance(payload, dict):
        cleaned: dict[str, Any] = {}
        for key, value in payload.items():
            lower_key = str(key).lower()
            # Keep env var *names* (e.g., token_env="BREAKRAG_RAG_API_KEY") and token counts
            if lower_key.endswith("_env") or lower_key in {
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "token_usage",
                "prompt_token_cost_per_1k",
                "completion_token_cost_per_1k",
            }:
                cleaned[key] = scrub_secrets(value)
            elif any(tok in lower_key for tok in _SENSITIVE_KEY_TOKENS):
                cleaned[key] = "***REDACTED***" if value else value
            else:
                cleaned[key] = scrub_secrets(value)
        return cleaned
    if isinstance(payload, list):
        return [scrub_secrets(item) for item in payload]
    return payload

