"""Dataset loader for JSON and CSV evaluation datasets."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from breakrag.models.evaluation import EvalCase


class DatasetError(ValueError):
    """Raised when an evaluation dataset cannot be parsed or validated."""


def _parse_doc_ids(raw: Any) -> list[str]:
    if raw is None or raw == "":
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, str):
        text = raw.strip()
        if text.startswith("["):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except json.JSONDecodeError:
                pass
        sep = "|" if "|" in text else ","
        return [part.strip() for part in text.split(sep) if part.strip()]
    return [str(raw).strip()]


def _parse_metadata(raw: Any) -> dict[str, Any]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {"raw_metadata": raw}
    return {"value": raw}


def load_evaluation_dataset(path: str | Path) -> list[EvalCase]:
    """Load and validate evaluation test cases from JSON or CSV files."""
    file_path = Path(path)
    if not file_path.exists():
        raise DatasetError(f"Dataset file not found: {file_path}")

    suffix = file_path.suffix.lower()
    raw_records: list[dict[str, Any]]

    if suffix == ".json":
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise DatasetError(f"Invalid JSON in dataset {file_path}: {exc}") from exc
        if isinstance(data, dict) and "cases" in data:
            data = data["cases"]
        if not isinstance(data, list):
            raise DatasetError(f"JSON dataset {file_path} must be a list of objects or {{'cases': [...]}}")
        raw_records = data
    elif suffix == ".csv":
        with file_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise DatasetError(f"CSV dataset {file_path} has no header row")
            raw_records = [dict(row) for row in reader]
    else:
        raise DatasetError(f"Unsupported dataset extension '{suffix}'. Expected .json or .csv")

    cases: list[EvalCase] = []
    seen_ids: set[str] = set()
    for idx, row in enumerate(raw_records, start=1):
        if not isinstance(row, dict):
            raise DatasetError(f"Record #{idx} in {file_path} must be an object")
        normalized = {
            "test_id": row.get("test_id") or row.get("id") or f"case_{idx:03d}",
            "question": row.get("question", ""),
            "ground_truth": row.get("ground_truth") or row.get("ground_truth_answer") or None,
            "expected_document_ids": _parse_doc_ids(
                row.get("expected_document_ids") or row.get("expected_doc_ids")
            ),
            "category": row.get("category") or "general",
            "expected_behavior": row.get("expected_behavior") or "answer_accurately",
            "metadata": _parse_metadata(row.get("metadata")),
        }
        try:
            case = EvalCase.model_validate(normalized)
        except ValidationError as exc:
            raise DatasetError(f"Invalid evaluation case at row #{idx} in {file_path}: {exc}") from exc
        if not case.question.strip():
            raise DatasetError(f"Empty question in evaluation case '{case.test_id}' in {file_path}")
        if case.test_id in seen_ids:
            raise DatasetError(f"Duplicate test_id '{case.test_id}' in {file_path}")
        seen_ids.add(case.test_id)
        cases.append(case)

    if not cases:
        raise DatasetError(f"Dataset {file_path} contains zero test cases")
    return cases

