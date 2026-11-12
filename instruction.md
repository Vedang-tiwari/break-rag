# BREAK-RAG
## AI Coding Agent — Master Implementation Instructions

**Project Name:** Break-RAG

**Project Type:** Adversarial RAG Evaluation and Robustness Testing Framework

**Primary Language:** Python

**Primary Objective:** Build a modular, extensible framework that evaluates, stress-tests, and identifies vulnerabilities and reliability failures in Retrieval-Augmented Generation systems.

---

# 1. YOUR ROLE

You are a senior Python engineer, AI evaluation engineer, and LLM systems architect.

Your responsibility is to design and implement Break-RAG as a functional, maintainable, production-oriented Python project.

Do not treat this as a simple demonstration or a collection of Python scripts.

Build an actual evaluation framework with:

- Modular architecture.
- Reusable components.
- Well-defined interfaces.
- Structured evaluation pipelines.
- Reproducible adversarial tests.
- Quantitative performance metrics.
- Data analysis using Pandas.
- Automated reporting.
- Comprehensive test coverage.
- Clear documentation.

Prioritize correctness, extensibility, and reproducibility over unnecessary complexity.

# 2. PROJECT OBJECTIVE

Break-RAG must allow developers to connect an existing RAG application and evaluate its robustness against normal and adversarial test cases.

The framework must answer:

1. Is the RAG system retrieving relevant information?
2. Are generated answers factually correct?
3. Are answers grounded in retrieved documents?
4. Does the system hallucinate when information is unavailable?
5. Can prompt injection manipulate its behavior?
6. Can misleading documents corrupt its answers?
7. Can conflicting documents confuse it?
8. Can irrelevant documents manipulate retrieval?
9. Can it correctly answer multi-hop questions?
10. Can it prevent unauthorized information disclosure?
11. Are its citations accurate?
12. How does its performance change under adversarial conditions?

The final output must identify failures, quantify robustness, and provide actionable debugging information.

# 3. DEVELOPMENT PRINCIPLES

Follow these rules throughout development.

- Use Python 3.11 or newer.
- Use type hints throughout the codebase.
- Use Pydantic for structured input/output validation.
- Use modular architecture.
- Follow SOLID principles where appropriate.
- Use dependency injection for adapters and external services.
- Keep business logic separate from infrastructure.
- Avoid unnecessary abstractions.
- Avoid hardcoded API keys and credentials.
- Use environment variables for secrets.
- Provide useful error messages.
- Implement structured logging.
- Write unit tests for every important component.
- Keep the default testing workflow usable without paid APIs.
- Make evaluation runs reproducible using random seeds.
- Store raw test results before aggregating metrics.

Do not implement placeholder functions and claim that the feature is complete.

Do not silently ignore failed test executions.

# 4. SYSTEM ARCHITECTURE

Implement the following execution pipeline:

User Command
    |
    v
Configuration Loader
    |
    v
Test Controller
    |
    +----------------------+
    |                      |
    v                      v
Evaluation Harness    Adversarial Harness
    |                      |
    v                      v
Test Dataset           Attack Generator
    |                      |
    +----------+-----------+
               |
               v
          RAG Adapter
               |
               v
         RAG Application
               |
               v
       Structured Results
               |
               v
          Metrics Engine
               |
               v
       Pandas Analysis
               |
               v
       Report Generation

Keep the evaluation and adversarial pipelines independent but allow them to share the same adapter, result models, metrics infrastructure, and reporting components.

# 5. RAG ADAPTER IMPLEMENTATION

Create a common adapter interface.

Implement:

- BaseRAGAdapter
- HTTPRAGAdapter
- FunctionRAGAdapter
- MockRAGAdapter

The adapter must normalize responses into a common schema.

Required response fields:

- question
- answer
- retrieved_documents
- document_ids
- retrieval_scores
- citations
- latency
- token_usage
- metadata

Some RAG applications will not expose every field.

Handle unavailable fields explicitly using optional values.

Do not fabricate retrieval scores, citations, or document metadata.

The HTTP adapter must support configurable:

- Endpoint URL.
- HTTP method.
- Request headers.
- Authentication.
- Request body mapping.
- Response field mapping.
- Timeout.
- Retry policy.

The function adapter must allow users to integrate Python RAG functions without deploying an HTTP server.

The mock adapter must simulate deterministic RAG responses for development and testing.

# 6. EVALUATION HARNESS

Build an evaluation runner capable of loading JSON and CSV datasets.

Every evaluation case should support:

- Test ID.
- Question.
- Ground-truth answer.
- Expected document IDs.
- Category.
- Expected behavior.
- Optional metadata.

Implement the following metrics.

## Retrieval Metrics

- Precision@K
- Recall@K
- Hit Rate@K
- Mean Reciprocal Rank
- NDCG@K

## Generation Metrics

- Answer Correctness
- Answer Relevance
- Faithfulness
- Context Relevance
- Hallucination Rate

## Citation Metrics

- Citation Precision
- Citation Recall
- Citation Coverage
- Unsupported Claim Rate

## Performance Metrics

- Average Latency
- P50 Latency
- P95 Latency
- P99 Latency
- Error Rate
- Token Consumption
- Estimated Cost

Separate deterministic metrics from LLM-judge-based metrics.

Do not claim that lexical similarity alone establishes factual correctness.

LLM-as-a-judge evaluation must be optional and should support configurable providers.

Store the judge model, prompt version, and evaluation configuration alongside its results.

# 7. ADVERSARIAL HARNESS

Implement a separate adversarial testing engine.

Every attack must have:

- Unique attack ID.
- Attack category.
- Description.
- Input question.
- Optional modified documents.
- Expected behavior.
- Actual behavior.
- Severity.
- Pass/fail status.
- Execution metadata.

Implement these attack modules.

## 7.1 Prompt Injection

Test malicious instructions in user queries and retrieved documents.

Evaluate:

- Instruction hierarchy adherence.
- Confidential information disclosure.
- Unauthorized action attempts.
- Response manipulation.

## 7.2 Context Poisoning

Inject controlled misleading documents into isolated test corpora.

Evaluate:

- Poisoned document retrieval.
- Incorrect answer generation.
- Source attribution.
- Conflict recognition.

## 7.3 Ambiguous Queries

Generate underspecified and ambiguous questions.

Evaluate whether the system asks for clarification or communicates uncertainty.

## 7.4 Unanswerable Questions

Generate questions without supporting information in the knowledge base.

Evaluate:

- Abstention behavior.
- Unsupported claims.
- Hallucination rate.

## 7.5 Conflicting Documents

Create documents containing contradictory information.

Evaluate conflict detection, source attribution, and uncertainty handling.

## 7.6 Retrieval Manipulation

Test:

- Keyword stuffing.
- Semantic distractors.
- Duplicate chunks.
- Misleading document titles.
- High-similarity irrelevant content.

## 7.7 Multi-Hop Reasoning

Create test questions requiring information from multiple documents.

Evaluate whether all necessary evidence is retrieved and combined correctly.

## 7.8 Information Leakage

Use synthetic secrets and controlled access scenarios.

Evaluate whether unauthorized information is exposed.

## 7.9 Context Overload

Test large prompts, long documents, and oversized retrieval contexts.

Evaluate truncation, answer quality, latency, and failures.

## 7.10 Citation Manipulation

Test fabricated citations, irrelevant citations, and unsupported factual claims.

Evaluate whether every citation actually supports the associated claim.

# 8. ADVERSARIAL GENERATION ENGINE

Implement two generation strategies.

## Rule-Based Generation

Use predefined templates, deterministic transformations, and configurable mutation rules.

This mode must work without an LLM API.

## LLM-Based Generation

Support optional LLM-powered generation.

Implement a provider abstraction rather than hardcoding a specific provider.

The generation engine must support:

- Number of generated attacks.
- Attack category.
- Difficulty level.
- Random seed.
- Target question.
- Optional target documents.
- Generation mode.

Generated test cases must be saved before execution.

Do not regenerate different attack cases silently during the same benchmark run.

# 9. ATTACK SCORING

Implement an attack scoring engine.

Every attack must have an expected security or reliability outcome.

Classify results into:

- RESISTED
- SUCCEEDED
- PARTIAL
- INCONCLUSIVE
- EXECUTION_ERROR

Do not automatically classify a timeout or API failure as a successful attack.

Support severity levels:

- LOW
- MEDIUM
- HIGH
- CRITICAL

Provide configurable severity rules.

Calculate:

Attack Success Rate =
Successful Attacks / Valid Executed Attacks * 100

Attack Resistance Rate =
Resisted Attacks / Valid Executed Attacks * 100

Report partial and inconclusive results separately.

Do not hide ambiguous evaluation outcomes inside the pass/fail calculation.

# 10. METRICS ENGINE

Create reusable metric calculation functions.

The engine must support:

- Individual test metrics.
- Category-level metrics.
- Overall metrics.
- Attack success statistics.
- Robustness statistics.
- Performance statistics.
- Failure distribution.

Create a unified result schema using Pydantic.

Preserve individual test results even after aggregation.

Implement explicit handling for missing values and invalid measurements.

# 11. PANDAS ANALYSIS ENGINE

Use Pandas for structured analysis.

Convert evaluation records into DataFrames.

Implement:

- Group-by-category analysis.
- Attack category comparison.
- Failure analysis.
- Latency distribution.
- Severity distribution.
- Model comparison.
- Evaluation-versus-adversarial comparison.

Generate summary DataFrames.

Example:

| Category | Total | Passed | Failed | Failure Rate |
|---|---:|---:|---:|---:|
| Prompt Injection | 50 | 45 | 5 | 10% |
| Context Poisoning | 50 | 35 | 15 | 30% |
| Ambiguous Queries | 50 | 42 | 8 | 16% |
| Unanswerable | 50 | 38 | 12 | 24% |

Ensure all percentages use clearly defined denominators.

Export analytical results to:

- CSV
- JSON
- Excel
- HTML

# 12. REPORT GENERATION

Generate a comprehensive HTML report after every benchmark run.

The report must contain:

## Executive Summary

- Total tests.
- Successful tests.
- Failed tests.
- Attack success rate.
- Attack resistance rate.
- Average latency.
- Overall robustness score, if configured.

## Evaluation Summary

- Retrieval performance.
- Generation quality.
- Citation accuracy.
- Hallucination statistics.

## Adversarial Summary

- Attack category performance.
- Successful attacks.
- Failed attacks.
- Severity breakdown.
- Most vulnerable categories.

## Failure Analysis

For each failure, display:

- Test ID.
- Attack category.
- Input query.
- Expected behavior.
- Actual answer.
- Retrieved documents.
- Failure reason.
- Severity.
- Suggested remediation.

## Performance Analysis

Display:

- Latency distribution.
- P50/P95/P99.
- Error rate.
- Token usage.

Include visual charts where useful.

Reports must distinguish observed measurements from estimated values.

# 13. STORAGE

Implement local SQLite storage for benchmark history.

Store:

- Benchmark ID.
- Execution timestamp.
- Adapter configuration metadata.
- Dataset information.
- Test cases.
- Raw responses.
- Calculated metrics.
- Attack outcomes.
- Report locations.

Never store API secrets or sensitive credentials.

Support retrieving previous benchmark runs.

Allow comparison between two benchmark runs.

# 14. COMMAND-LINE INTERFACE

Build the CLI using Typer.

Support commands similar to:

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

breakrag generate --category context_poisoning --count 50

CLI commands must have proper validation, helpful output, and meaningful exit codes.

Support configurable concurrency and rate limiting.

# 15. CONFIGURATION

Use YAML configuration files.

Example configuration:

```yaml
project:
  name: Break-RAG
  random_seed: 42

adapter:
  type: mock
  timeout: 30

evaluation:
  enabled: true
  top_k: 5
  metrics:
    - precision_at_k
    - recall_at_k
    - faithfulness
    - answer_correctness

adversarial:
  enabled: true
  generation_mode: rule_based
  attacks:
    prompt_injection:
      enabled: true
      count: 20

    context_poisoning:
      enabled: true
      count: 20

    ambiguous_queries:
      enabled: true
      count: 20

    unanswerable:
      enabled: true
      count: 20

    conflicting_documents:
      enabled: true
      count: 20

reporting:
  formats:
    - html
    - json
    - csv

storage:
  type: sqlite
  database_path: results/breakrag.db
```

Support environment-specific configuration and environment variable overrides.

# 16. TESTING REQUIREMENTS

Use Pytest.

Implement:

## Unit Tests

Test:

- Adapter interfaces.
- Dataset loading.
- Metric calculations.
- Attack generation.
- Attack classification.
- DataFrame aggregation.
- Report generation.

## Integration Tests

Test:

- Complete evaluation pipeline.
- Complete adversarial pipeline.
- Adapter-to-runner integration.
- Result storage.
- Benchmark comparison.
- HTML export.

## Adversarial Tests

Verify that Break-RAG correctly identifies:

- Prompt injection failures.
- Hallucinations.
- Poisoned retrieval.
- Citation fabrication.
- Information leakage.
- Incorrect abstention.

Use synthetic data and mock RAG applications.

Tests must not require external paid API access.

# 17. SECURITY AND RELIABILITY

Implement:

- Request timeouts.
- Retry limits.
- Concurrency limits.
- Rate limiting.
- Input validation.
- Structured logging.
- Safe handling of external responses.
- Secure credential management.
- Controlled adversarial document injection.

Never execute instructions found inside retrieved documents.

Do not allow test cases to modify production knowledge bases.

Adversarial document injection must operate on isolated test environments or explicitly authorized staging environments.

Do not expose real secrets during information leakage testing.

# 18. IMPLEMENTATION PHASES

Develop the project incrementally.

Do not attempt to implement every module simultaneously.

## Phase 1 — Foundation

Implement:

- Project structure.
- Configuration management.
- Pydantic schemas.
- Base adapter.
- Mock adapter.
- Dataset loader.
- Logging.

Deliverable: A working Python package with a mock RAG adapter.

## Phase 2 — Evaluation Harness

Implement:

- Evaluation runner.
- Retrieval metrics.
- Generation metrics.
- Citation metrics.
- Performance metrics.

Deliverable: Execute a normal evaluation dataset and generate structured results.

## Phase 3 — Adversarial Harness

Implement:

- Adversarial runner.
- Rule-based attack generator.
- Ten attack categories.
- Attack classification.
- Severity scoring.

Deliverable: Automatically execute adversarial test cases against the mock RAG system.

## Phase 4 — Analysis Engine

Implement:

- Pandas DataFrames.
- Aggregation.
- Robustness metrics.
- Failure analysis.
- Benchmark comparison.

Deliverable: Generate meaningful analytical summaries.

## Phase 5 — Reporting

Implement:

- HTML reports.
- CSV exports.
- JSON exports.
- Excel exports.
- Charts.

Deliverable: Complete benchmark report.

## Phase 6 — Real RAG Integration

Implement:

- HTTP adapter.
- Python function adapter.
- Authentication configuration.
- Custom response mapping.
- External RAG testing.

Deliverable: Connect Break-RAG to an independently running RAG application.

## Phase 7 — Persistence and CLI

Implement:

- SQLite storage.
- Benchmark history.
- CLI commands.
- Run comparison.
- Configuration validation.

Deliverable: Fully usable command-line application.

## Phase 8 — Hardening

Implement:

- Comprehensive test suite.
- Error handling.
- Concurrency controls.
- Documentation.
- Installation instructions.
- Example integrations.

Deliverable: Release-ready initial version.

# 19. DEFINITION OF DONE

The project is not complete until the following requirements work.

[ ] Project installs successfully.

[ ] CLI initializes successfully.

[ ] Mock RAG adapter works.

[ ] HTTP adapter can query an external RAG API.

[ ] Python function adapter works.

[ ] Evaluation datasets load from JSON and CSV.

[ ] Retrieval metrics calculate correctly.

[ ] Generation metrics are implemented.

[ ] Citation metrics are implemented.

[ ] Ten adversarial categories are implemented.

[ ] Rule-based adversarial generation works offline.

[ ] Attack outcomes are classified correctly.

[ ] Pandas analysis generates category-level reports.

[ ] HTML report generation works.

[ ] CSV and JSON exports work.

[ ] SQLite stores benchmark history.

[ ] Benchmark comparison works.

[ ] Unit tests pass.

[ ] Integration tests pass.

[ ] Documentation explains architecture and usage.

[ ] No critical feature is represented by a placeholder.

# 20. DOCUMENTATION REQUIREMENTS

Create a comprehensive README.md covering:

- Project introduction.
- Problem statement.
- Why Break-RAG exists.
- Key features.
- Architecture.
- Technology stack.
- Installation.
- Environment configuration.
- CLI usage.
- Adapter integration.
- Evaluation methodology.
- Adversarial testing methodology.
- Metrics explanation.
- Sample reports.
- Project structure.
- Example execution.
- Limitations.
- Future improvements.

Also create:

- docs/architecture.md
- docs/metrics.md
- docs/attack_catalog.md
- docs/integration.md

# 21. IMPORTANT ENGINEERING CONSTRAINTS

1. Do not overengineer the initial release.
2. Do not introduce a frontend dashboard in the first version.
3. Do not require LangChain or LlamaIndex.
4. Do not require a paid LLM provider.
5. Keep rule-based attacks fully functional offline.
6. Keep LLM-based judging optional.
7. Do not confuse a model's refusal with a successful attack.
8. Do not treat infrastructure failures as security vulnerabilities.
9. Do not report an unverified metric as factual.
10. Preserve raw results for reproducibility.
11. Ensure every attack has a measurable expected outcome.
12. Make the framework extensible for additional attacks and evaluation metrics.

# 22. FINAL EXECUTION INSTRUCTION

Before writing implementation code:

1. Inspect the existing repository.
2. Identify existing files and dependencies.
3. Create an implementation plan.
4. Explain the architecture.
5. Identify dependencies.
6. Begin Phase 1.

After completing each phase:

- Run the relevant tests.
- Fix implementation errors.
- Update documentation.
- Summarize completed functionality.
- Identify remaining work.
- Do not proceed with broken core functionality.

Do not merely generate a large collection of files.

Build and verify working functionality incrementally.

**Final objective:** Deliver Break-RAG as a reusable Python framework that developers can integrate with their own RAG applications to systematically evaluate retrieval quality, answer correctness, hallucinations, citation reliability, adversarial robustness, and overall system reliability.