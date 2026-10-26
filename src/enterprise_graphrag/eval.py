"""Tiny deterministic evaluation harness for CI and regression tracking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .models import QueryRequest


@dataclass(frozen=True)
class EvalCase:
    question: str
    expected_terms: tuple[str, ...]
    tenant_id: str = "demo"


@dataclass(frozen=True)
class EvalReport:
    cases: int
    answer_term_recall: float
    citation_rate: float
    abstention_rate: float

    def to_dict(self) -> dict[str, float | int]:
        return {
            "cases": self.cases,
            "answer_term_recall": round(self.answer_term_recall, 4),
            "citation_rate": round(self.citation_rate, 4),
            "abstention_rate": round(self.abstention_rate, 4),
        }


def run_eval(engine: object, cases: Iterable[EvalCase], request_factory: Callable[[EvalCase], QueryRequest] | None = None) -> EvalReport:
    rows = list(cases)
    if not rows:
        return EvalReport(0, 0.0, 0.0, 0.0)
    recalled = cited = abstained = 0
    for case in rows:
        request = request_factory(case) if request_factory else QueryRequest(case.question)
        response = engine.answer(request)
        answer = response.answer.lower()
        recalled += sum(term.lower() in answer for term in case.expected_terms) / max(1, len(case.expected_terms))
        cited += bool(response.citations)
        abstained += response.abstained
    return EvalReport(len(rows), recalled / len(rows), cited / len(rows), abstained / len(rows))
