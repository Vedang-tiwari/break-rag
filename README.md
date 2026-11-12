# Break-RAG

**Break-RAG** is a modular Python framework for evaluating, stress-testing, and uncovering reliability and security vulnerabilities in Retrieval-Augmented Generation (RAG) applications.

---

## Why Break-RAG?

Standard RAG benchmarks focus on average answer accuracy under clean inputs, leaving critical production failure modes untested. Break-RAG systematically answers whether your RAG system:

- Retrieves the right supporting documents (`Precision@K`, `Recall@K`, `MRR`, `NDCG@K`)
- Generates faithful, grounded answers and abstains when evidence is missing
- Produces accurate citations without fabricating sources
- Resists prompt injection, context poisoning, retrieval manipulation, conflicting documents, context overload, and synthetic information leakage
- Maintains predictable latency, error rates, and token usage under load

---

## Key Features

- **Unified RAG Adapter Layer:** Connect any RAG pipeline via `MockRAGAdapter` (deterministic offline testing), `FunctionRAGAdapter` (Python callables), or `HTTPRAGAdapter` (configurable endpoints, auth, field mapping, timeouts, and retries).
- **Offline-First & Zero Paid-API Requirement:** Deterministic evaluation metrics, rule-based adversarial attacks across 10 categories, and mock adapters run completely offline with reproducible random seeds. Optional LLM-as-a-judge and LLM attack generation are supported behind provider abstractions.
- **Honest Metric & Outcome Semantics:** Missing adapter fields remain explicit `None` values (never fabricated); deterministic overlap metrics are separated from LLM-judge scores; adapter errors/timeouts (`EXECUTION_ERROR`) and safe model refusals (`RESISTED`) are never misclassified as successful attacks.
- **10 Adversarial Attack Categories:** Prompt Injection, Context Poisoning, Ambiguous Queries, Unanswerable Questions, Conflicting Documents, Retrieval Manipulation, Multi-Hop Reasoning, Information Leakage, Context Overload, and Citation Manipulation.
- **Structured Analysis, Storage & Reporting:** Pandas-based category/severity/failure analysis, SQLite benchmark history and run comparison, and automated HTML, JSON, CSV, and Excel exports via a Typer CLI.

---

## Architecture

```text
User Command (Typer CLI)
        |
        v
Configuration Loader (YAML + Env Overrides)
        |
        v
  Test Controller
   +----+--------------------+
   |                         |
   v                         v
Evaluation Harness    Adversarial Harness
(JSON / CSV Datasets) (Rule-Based / LLM Attack Generator)
   |                         |
   +------------+------------+
                |
                v
           RAG Adapter
      (Mock | Function | HTTP)
                |
                v
         RAG Application
                |
                v
   Metrics Engine & Attack Scorer
                |
                v
     Pandas Analysis Engine
                |
        +-------+-------+
        |               |
        v               v
   SQLite Store    HTML / JSON / CSV / Excel Reports
```

---

## Tech Stack

- **Language:** Python 3.11+
- **Schemas & Validation:** Pydantic v2, `pydantic-settings`, PyYAML, `python-dotenv`
- **HTTP Client:** `httpx`
- **Analysis & Exports:** `pandas`, `openpyxl`, `jinja2`
- **CLI & Testing:** `typer`, `rich`, `pytest`, `pytest-asyncio`
- **Persistence:** SQLite (`sqlite3`)

---

## Installation

```bash
# Clone the repository and create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# Install package and development dependencies
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` if you plan to configure optional HTTP RAG credentials or LLM-judge keys:

```bash
cp .env.example .env
```

---

## Configuration

Break-RAG uses YAML configuration (see [`breakrag.example.yaml`](breakrag.example.yaml)) with `${VAR:-default}` interpolation, per-environment overrides, and `BREAKRAG_*` environment variables:

```yaml
project:
  name: Break-RAG
  environment: development
  random_seed: 42

adapter:
  type: mock
  mock_profile: healthy
  timeout: 30

evaluation:
  enabled: true
  dataset_path: datasets/evaluation/sample_questions.json
  top_k: 5

adversarial:
  enabled: true
  generation_mode: rule_based
```

---

## CLI Usage (Planned & Target Interface)

```bash
breakrag init
breakrag validate-config
breakrag test --adapter mock
breakrag evaluate --dataset datasets/evaluation/sample_questions.json
breakrag attack --category prompt_injection
breakrag attack --all
breakrag benchmark --mode full
breakrag report --run-id RUN_ID
breakrag compare --run-a RUN_001 --run-b RUN_002
breakrag history
```

---

## Project Structure

```text
Break-rag/
├── pyproject.toml
├── breakrag.example.yaml
├── .env.example
├── instruction.md
├── datasets/
│   ├── corpus/sample_kb.json
│   └── evaluation/
│       ├── sample_questions.json
│       └── sample_questions.csv
├── src/breakrag/
│   ├── logging_config.py
│   ├── config/          # YAML loader, env overrides, secret scrubbing
│   ├── models/          # Pydantic adapter, eval, adversarial & benchmark schemas
│   ├── adapters/        # BaseRAGAdapter, MockRAGAdapter (+ HTTP/Function planned)
│   └── datasets/        # JSON and CSV evaluation dataset loader
└── tests/
    └── unit/test_phase1_foundation.py
```

---

## Current Status & Running Tests

- **Implemented (Phase 1 — Foundation):** Project configuration & env overrides, Pydantic data models, structured logging, `BaseRAGAdapter`, deterministic `MockRAGAdapter` (with `healthy`, `vulnerable`, `hallucinating`, and `leaky` profiles), JSON/CSV dataset loader, and sample datasets.
- **In Progress / Planned (Phases 2–8):** Evaluation runner & metrics engine, 10-category adversarial harness & scorer, Pandas analysis engine, HTML/CSV/JSON/Excel reporting, HTTP/Function adapters, SQLite storage, and Typer CLI.

Run the existing unit tests:

```bash
PYTHONPATH=src pytest -v
```

---

## Limitations

- Deterministic lexical/overlap metrics cannot replace semantic judgment for nuanced factual equivalence; enable the optional LLM-as-a-judge integration when semantic grading is required.
- Adversarial document injection is designed strictly for isolated test or authorized staging environments—never against production knowledge bases.

