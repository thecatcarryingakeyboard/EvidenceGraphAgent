"""Hybrid lexical + graph retrieval with explainable ranking reasons."""

from __future__ import annotations

import math
from collections import Counter

from .models import Chunk, RetrievalHit, SearchMode, UserContext
from .store import KnowledgeGraph, tokenize


class HybridRetriever:
    def __init__(self, graph: KnowledgeGraph) -> None:
        self.graph = graph

    def search(self, query: str, user: UserContext, mode: SearchMode = "local", top_k: int = 6) -> list[RetrievalHit]:
        query_terms = set(tokenize(query))
        if not query_terms:
            return []
        candidates = list(self.graph.visible_chunks(user))
        document_frequency = Counter(
            term
            for chunk in candidates
            for term in set(tokenize(chunk.text))
        )
        ranked: list[RetrievalHit] = []
        for chunk in candidates:
            counts = Counter(tokenize(chunk.text))
            matched = tuple(sorted(query_terms & counts.keys()))
            if not matched:
                continue
            score = 0.0
            for term in matched:
                tf = 1.0 + math.log(counts[term])
                idf = math.log((1 + len(candidates)) / (1 + document_frequency[term])) + 1
                score += tf * idf
            score /= math.sqrt(max(1, len(query_terms)))
            ranked.append(RetrievalHit(chunk, score, matched, 0, "lexical"))

        ranked.sort(key=lambda item: item.score, reverse=True)
        if mode in {"global", "deep"} and ranked:
            seed_ids = {item.chunk.id for item in ranked[: min(3, len(ranked))]}
            expanded_ids = self.graph.expand(seed_ids, user, hops=2 if mode == "deep" else 1)
            by_id = {item.chunk.id: item for item in ranked}
            for chunk_id in expanded_ids:
                if chunk_id in by_id:
                    continue
                chunk = self.graph.chunks[chunk_id]
                # Graph-supported context is useful even when lexical overlap is
                # weak; discount it so direct matches still win.
                ranked.append(RetrievalHit(chunk, 0.35, (), 1 if mode == "global" else 2, "graph_expansion"))
        ranked.sort(key=lambda item: (item.score, -item.graph_hops), reverse=True)
        return ranked[: max(1, top_k)]
