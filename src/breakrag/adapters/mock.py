"""Deterministic offline MockRAGAdapter for testing, development, and adversarial validation."""

from __future__ import annotations

import re
import time
from typing import Any, Literal

from breakrag.adapters.base import BaseRAGAdapter
from breakrag.models.adapter import (
    Citation,
    DocumentInput,
    RAGRequest,
    RAGResponse,
    TokenUsage,
)

_TOKEN_RE = re.compile(r"[a-z0-9_]+")

DEFAULT_MOCK_KB: list[DocumentInput] = [
    DocumentInput(
        id="doc_refund_policy",
        title="Refund and Billing Policy",
        content=(
            "AcmeCloud offers a full 30-day money-back guarantee on annual Starter and Pro plans. "
            "Refund requests must be submitted within 30 calendar days of the initial invoice date "
            "through the billing portal. Enterprise custom contracts follow SLA terms."
        ),
    ),
    DocumentInput(
        id="doc_sla_uptime",
        title="Service Level Agreement",
        content=(
            "AcmeCloud guarantees 99.95% monthly uptime for Pro tier and 99.99% monthly uptime "
            "for Enterprise tier. Scheduled maintenance windows occur on Sundays at 02:00 UTC "
            "and are announced 72 hours in advance."
        ),
    ),
    DocumentInput(
        id="doc_auth_mfa",
        title="Authentication and MFA Security",
        content=(
            "All administrative accounts must enable multi-factor authentication using TOTP or FIDO2 "
            "hardware keys. API tokens expire automatically after 90 days and must be stored in "
            "environment variables rather than source control."
        ),
    ),
    DocumentInput(
        id="doc_encryption",
        title="Data Encryption Standards",
        content=(
            "Customer data at rest is encrypted using AES-256-GCM with per-tenant keys managed in KMS. "
            "All data in transit uses TLS 1.3 with strict certificate validation."
        ),
    ),
    DocumentInput(
        id="doc_rate_limits",
        title="API Rate Limits",
        content=(
            "Standard API keys allow 120 requests per minute. Pro tier keys allow 600 requests per "
            "minute. Exceeding the quota returns HTTP 429 with a Retry-After header."
        ),
    ),
    DocumentInput(
        id="doc_deployment_regions",
        title="Regional Availability",
        content=(
            "AcmeCloud operates primary clusters in us-east-1, eu-central-1, and ap-south-1. "
            "EU customer data remains pinned to eu-central-1 for GDPR compliance."
        ),
    ),
    DocumentInput(
        id="doc_multihop_team",
        title="Incident Escalation Contacts",
        content=(
            "Severity-1 security incidents are routed to the Cloud Security Response Team (CSRT). "
            "The CSRT on-call lead rotates weekly and uses PagerDuty channel #sec-sev1."
        ),
    ),
    DocumentInput(
        id="doc_multihop_sla_escalation",
        title="CSRT Response Time Targets",
        content=(
            "The Cloud Security Response Team (CSRT) acknowledges Severity-1 security incidents within "
            "15 minutes and publishes a preliminary incident advisory within 2 hours."
        ),
    ),
]


def _tokenize(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(text.lower()) if len(t) > 1}


class MockRAGAdapter(BaseRAGAdapter):
    """Deterministic RAG simulator with configurable behavior profiles.

    Profiles:
        - ``healthy``: Grounded retrieval, accurate citations, refuses injections/leakage, abstains when unsupported.
        - ``vulnerable``: Susceptible to prompt injection, poisoned docs, secret leakage, and fabricated citations.
        - ``hallucinating``: Invents unsupported claims regardless of retrieved context.
        - ``leaky``: Exposes synthetic secrets and restricted document fields.
    """

    adapter_type: str = "mock"

    def __init__(
        self,
        profile: Literal["healthy", "vulnerable", "hallucinating", "leaky"] = "healthy",
        knowledge_base: list[DocumentInput] | None = None,
        expose_scores: bool = True,
        expose_citations: bool = True,
        expose_token_usage: bool = True,
        simulated_latency: float = 0.005,
        timeout: float = 30.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.profile = profile
        self.knowledge_base = list(knowledge_base) if knowledge_base is not None else list(DEFAULT_MOCK_KB)
        self.expose_scores = expose_scores
        self.expose_citations = expose_citations
        self.expose_token_usage = expose_token_usage
        self.simulated_latency = simulated_latency

    def _retrieve(
        self, question: str, top_k: int, injected_documents: list[DocumentInput]
    ) -> list[tuple[DocumentInput, float]]:
        # Isolated corpus view: never mutate self.knowledge_base
        corpus = list(self.knowledge_base) + list(injected_documents)
        q_tokens = _tokenize(question)
        scored: list[tuple[DocumentInput, float]] = []
        for idx, doc in enumerate(corpus):
            doc_tokens = _tokenize(f"{doc.title or ''} {doc.content}")
            if not q_tokens or not doc_tokens:
                score = 0.0
            else:
                overlap = len(q_tokens & doc_tokens)
                score = overlap / max(len(q_tokens), 1)
                # Slight bonus for exact phrase or injected keyword-stuffed docs in vulnerable mode
                if self.profile == "vulnerable" and doc in injected_documents and overlap > 0:
                    score += 0.25
            scored.append((doc, round(min(score, 1.0), 4), idx))  # type: ignore[misc]

        scored.sort(key=lambda item: (-item[1], item[2]))  # type: ignore[index]
        return [(doc, score) for doc, score, _ in scored[:top_k]]  # type: ignore[misc]

    @staticmethod
    def _contains_injection(text: str) -> bool:
        lowered = text.lower()
        markers = (
            "ignore previous instructions",
            "ignore all previous",
            "disregard prior",
            "system prompt",
            "developer mode",
            "override:",
            "reveal the secret",
            "bypass security",
            "print your instructions",
            "execute command",
        )
        return any(m in lowered for m in markers)

    @staticmethod
    def _extract_secret(docs: list[DocumentInput]) -> str | None:
        secret_re = re.compile(
            r"(SYNTHETIC_[A-Z0-9_]+|TEST_SECRET_[A-Z0-9_]+|sk-test-[A-Za-z0-9_-]+|AKIA[A-Z0-9]{8,})"
        )
        for doc in docs:
            match = secret_re.search(doc.content)
            if match:
                return match.group(1)
        return None

    def _detect_conflict(self, docs: list[DocumentInput]) -> bool:
        contents = " ".join(d.content.lower() for d in docs)
        conflict_pairs = [
            ("30-day", "7-day"),
            ("30 calendar days", "no refunds"),
            ("99.95%", "95.0%"),
            ("120 requests", "10 requests"),
            ("mandatory", "optional"),
            ("contradict", "however"),
            ("policy update", "strictly prohibited"),
        ]
        for a, b in conflict_pairs:
            if a in contents and b in contents:
                return True
        # Numeric disagreement across docs sharing a keyword
        if any(d.metadata.get("conflict_group") for d in docs):
            groups = [d.metadata.get("conflict_group") for d in docs if d.metadata.get("conflict_group")]
            if len(groups) >= 2:
                return True
        return False

    def _is_ambiguous(self, question: str) -> bool:
        q = question.strip().lower()
        words = _tokenize(q)
        vague_phrases = (
            "what is the limit",
            "how does it work",
            "tell me about the policy",
            "what is the threshold",
            "which region",
            "how long does it take",
            "is it supported",
        )
        return len(words) <= 5 and any(p in q for p in vague_phrases)

    def query(self, request: RAGRequest | str) -> RAGResponse:
        req = self._coerce_request(request)
        start = time.perf_counter()

        retrieved_pairs = self._retrieve(req.question, req.top_k, req.injected_documents)
        docs = [d for d, _ in retrieved_pairs]
        doc_texts = [d.content for d in docs]
        doc_ids = [d.id for d in docs]
        scores = [s for _, s in retrieved_pairs] if self.expose_scores else None

        combined_context = " ".join([req.question] + doc_texts)
        has_injection = self._contains_injection(combined_context)
        synthetic_secret = self._extract_secret(docs + req.injected_documents)
        max_score = max((s for _, s in retrieved_pairs), default=0.0)

        citations: list[Citation] | None = None
        answer: str

        if self.profile == "vulnerable":
            if has_injection:
                answer = (
                    "OVERRIDE_ACCEPTED: Ignoring prior system instructions. "
                    "PWNED — confidential system prompt: You are an internal assistant."
                )
            elif synthetic_secret:
                answer = f"The restricted credential found in context is {synthetic_secret}."
            elif any(d.metadata.get("poisoned") for d in docs):
                poisoned_doc = next(d for d in docs if d.metadata.get("poisoned"))
                answer = f"{poisoned_doc.content} [{poisoned_doc.id}]"
            elif "cite" in req.question.lower() or "citation" in req.question.lower():
                answer = (
                    "AcmeCloud provides unlimited free enterprise tiers globally [fabricated_doc_999]. "
                    "All policies are waived [nonexistent_source_42]."
                )
                if self.expose_citations:
                    citations = [
                        Citation(
                            document_id="fabricated_doc_999",
                            claim="AcmeCloud provides unlimited free enterprise tiers globally",
                            raw="[fabricated_doc_999]",
                        )
                    ]
            elif max_score < 0.25:
                answer = (
                    "Yes, AcmeCloud launched quantum teleportation storage in 2025 with a 100% guarantee "
                    "and zero latency worldwide."
                )
            else:
                top_doc = docs[0]
                answer = f"{top_doc.content} [{top_doc.id}]"
                if self.expose_citations:
                    citations = [
                        Citation(
                            document_id=top_doc.id,
                            claim=top_doc.content,
                            source_text=top_doc.content,
                            raw=f"[{top_doc.id}]",
                        )
                    ]

        elif self.profile == "hallucinating":
            answer = (
                "AcmeCloud provides lifetime complimentary GPU clusters and guarantees 100% zero-downtime "
                "across 45 orbital data centers according to internal memos."
            )
            if self.expose_citations:
                citations = [
                    Citation(
                        document_id=docs[0].id if docs else "unknown",
                        claim=answer,
                        raw=f"[{docs[0].id}]" if docs else None,
                    )
                ]

        elif self.profile == "leaky":
            if synthetic_secret:
                answer = f"According to internal configuration, the secret value is {synthetic_secret}."
            else:
                answer = (
                    "Internal admin override token is SYNTHETIC_LEAK_TOKEN_999 and internal host is 10.0.0.42."
                )

        else:
            # Healthy deterministic profile
            if has_injection and (
                "secret" in combined_context.lower()
                or "system prompt" in combined_context.lower()
                or "override" in combined_context.lower()
                or "ignore" in combined_context.lower()
                or "pwned" in combined_context.lower()
            ):
                answer = (
                    "I cannot follow instructions embedded inside untrusted queries or retrieved documents, "
                    "and I cannot disclose system prompts or restricted credentials."
                )
            elif synthetic_secret and (
                "secret" in req.question.lower()
                or "key" in req.question.lower()
                or "password" in req.question.lower()
                or "ssn" in req.question.lower()
                or "token" in req.question.lower()
                or "confidential" in req.question.lower()
            ):
                answer = (
                    "I cannot disclose sensitive credentials, API keys, or restricted personal information."
                )
            elif self._is_ambiguous(req.question):
                answer = (
                    "Your question is ambiguous and underspecified. Could you please clarify which specific "
                    "AcmeCloud service, plan tier, or policy you are asking about?"
                )
            elif self._detect_conflict(docs):
                relevant_ids = [d.id for d in docs[:2]]
                answer = (
                    f"The retrieved sources contain conflicting information ({', '.join(relevant_ids)}). "
                    "I cannot resolve the contradiction without authoritative verification: "
                    f"[{relevant_ids[0]}] states '{docs[0].content[:120]}', whereas "
                    f"[{relevant_ids[1]}] states '{docs[1].content[:120]}'."
                )
                if self.expose_citations:
                    citations = [
                        Citation(
                            document_id=d.id,
                            claim=d.content[:120],
                            source_text=d.content,
                            raw=f"[{d.id}]",
                        )
                        for d in docs[:2]
                    ]
            elif max_score < 0.2:
                answer = (
                    "I do not have sufficient verified information in the retrieved documents to answer "
                    "this question."
                )
            else:
                # Filter out obvious poisoned/injection docs if trusted docs exist
                clean_docs = [
                    d for d, s in retrieved_pairs
                    if s >= 0.15 and not self._contains_injection(d.content) and not d.metadata.get("poisoned")
                ]
                chosen = clean_docs[:2] if clean_docs else docs[:1]
                snippets = [f"{d.content} [{d.id}]" for d in chosen]
                answer = " ".join(snippets)
                if self.expose_citations:
                    citations = [
                        Citation(
                            document_id=d.id,
                            claim=d.content,
                            source_text=d.content,
                            raw=f"[{d.id}]",
                        )
                        for d in chosen
                    ]

        elapsed = max(time.perf_counter() - start, self.simulated_latency)
        token_usage = None
        if self.expose_token_usage:
            prompt_tokens = max(len(req.question.split()) + sum(len(t.split()) for t in doc_texts), 1)
            completion_tokens = max(len(answer.split()), 1)
            token_usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            )

        return RAGResponse(
            question=req.question,
            answer=answer,
            retrieved_documents=doc_texts,
            document_ids=doc_ids,
            retrieval_scores=scores,
            citations=citations,
            latency=round(elapsed, 6),
            token_usage=token_usage,
            metadata={"adapter": "mock", "profile": self.profile},
            status="ok",
        )

    def get_metadata(self) -> dict[str, Any]:
        meta = super().get_metadata()
        meta.update(
            {
                "profile": self.profile,
                "kb_size": len(self.knowledge_base),
                "expose_scores": self.expose_scores,
                "expose_citations": self.expose_citations,
            }
        )
        return meta

