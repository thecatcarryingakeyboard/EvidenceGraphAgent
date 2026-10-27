"""Hybrid lexical + graph retrieval with explainable ranking reasons."""

from __future__ import annotations

import math
from collections import Counter

from .models import RetrievalHit, SearchMode, UserContext
from .store import KnowledgeGraph, tokenize


class HybridRetriever:
    def __init__(self, graph: KnowledgeGraph) -> None:
        self.graph = graph

    def search(self, query: str, user: UserContext, mode: SearchMode = "local", top_k: int = 6) -> list[RetrievalHit]:
        if mode not in {"local", "global", "deep"} or top_k < 1:
            raise ValueError("mode must be local/global/deep and top_k must be positive")
        query_terms = set(tokenize(query))
        if not query_terms:
            return []
        candidates = list(self.graph.visible_chunks(user))
        if not candidates:
            return []
        counts_by_chunk = {chunk.id: Counter(tokenize(chunk.text)) for chunk in candidates}
        average_length = sum(sum(counts.values()) for counts in counts_by_chunk.values()) / len(candidates)
        document_frequency = Counter(
            term
            for chunk in candidates
            for term in set(tokenize(chunk.text))
        )
        ranked: list[RetrievalHit] = []
        for chunk in candidates:
            counts = counts_by_chunk[chunk.id]
            matched = tuple(sorted(query_terms & counts.keys()))
            if not matched:
                continue
            # One common Chinese bigram (for example 时间) is not enough to
            # support a long unrelated question. Exact ASCII terms remain useful.
            if len(query_terms) > 2 and len(matched) < 2:
                if not any(term.isascii() and len(term) >= 3 for term in matched):
                    continue
            score = 0.0
            for term in matched:
                # BM25 with explicit length normalization; all statistics are tenant-local.
                frequency = counts[term]
                idf = math.log(1 + (len(candidates) - document_frequency[term] + 0.5)
                               / (document_frequency[term] + 0.5))
                normalizer = 1.2 * (0.25 + 0.75 * sum(counts.values()) / max(1, average_length))
                score += idf * frequency * 2.2 / (frequency + normalizer)
            ranked.append(RetrievalHit(chunk, score, matched, 0, "bm25"))

        ranked.sort(key=lambda item: item.score, reverse=True)
        if mode in {"global", "deep"} and ranked:
            seed_ids = {item.chunk.id for item in ranked[: min(3, len(ranked))]}
            expanded_ids = self.graph.expand(seed_ids, user, hops=2 if mode == "deep" else 1)
            by_id = {item.chunk.id: item for item in ranked}
            for chunk_id in sorted(expanded_ids):
                if chunk_id in by_id:
                    continue
                chunk = self.graph.chunks[chunk_id]
                # Graph-supported context is useful even when lexical overlap is
                # weak; discount it so direct matches still win.
                ranked.append(RetrievalHit(chunk, 0.35, (), 1 if mode == "global" else 2, "graph_expansion"))
        ranked.sort(key=lambda item: (-item.score, item.graph_hops, item.chunk.id))
        return ranked[: max(1, top_k)]
