"""LLM provider adapters and an offline, citation-preserving demo provider."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from .models import Citation


class AnswerProvider(Protocol):
    name: str

    def answer(self, query: str, context: list[Citation]) -> str:
        ...


@dataclass
class DemoProvider:
    name: str = "demo"

    def answer(self, query: str, context: list[Citation]) -> str:
        if not context:
            return "我没有在当前租户的知识库中找到足够证据，暂不回答。请补充文档或缩小问题范围。"
        lines = [f"基于 {len(context)} 条可追溯证据，关于“{query}”的要点如下："]
        for index, citation in enumerate(context[:3], 1):
            quote = " ".join(citation.quote.split())
            lines.append(f"{index}. {quote}（[{citation.citation_id}] {citation.title}）")
        lines.append("以上结论仅覆盖引用片段；涉及审批、金额或权限的决策仍应由业务流程确认。")
        return "\n".join(lines)


class OpenAICompatibleProvider:
    name = "openai_compatible"

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def answer(self, query: str, context: list[Citation]) -> str:
        if not self.api_key:
            raise ValueError("LLM_API_KEY is required for the openai_compatible provider")
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Install the 'openai' extra to use the OpenAI-compatible provider") from exc
        evidence = "\n".join(
            f"[{item.citation_id}] {item.title}: {item.quote}" for item in context
        )
        prompt = (
            "Answer only from the evidence below. Cite every material claim with [CITATION_ID]. "
            "If evidence is insufficient, say so explicitly.\n\n"
            f"Evidence:\n{evidence}\n\nQuestion: {query}"
        )
        client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": "You are an enterprise knowledge assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or ""


def provider_from_settings(settings: object) -> AnswerProvider:
    provider = getattr(settings, "llm_provider", "demo").lower()
    if provider in {"demo", "offline"}:
        return DemoProvider()
    if provider in {"openai", "openai_compatible", "deepseek", "ollama"}:
        return OpenAICompatibleProvider(
            base_url=getattr(settings, "llm_base_url"),
            api_key=getattr(settings, "llm_api_key"),
            model=getattr(settings, "llm_model"),
        )
    raise ValueError(f"Unsupported LLM_PROVIDER={provider!r}")
