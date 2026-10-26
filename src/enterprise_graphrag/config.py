"""Environment-backed configuration with safe local defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Runtime settings.

    The demo provider is selected by default, which makes a fresh checkout
    usable without API keys.  Production deployments should set
    ``LLM_PROVIDER=openai_compatible`` and provide a secret through a secret
    manager or environment injection.
    """

    app_name: str = os.getenv("APP_NAME", "Enterprise GraphRAG Agent")
    environment: str = os.getenv("APP_ENV", "development")
    llm_provider: str = os.getenv("LLM_PROVIDER", "demo")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    max_context_chars: int = int(os.getenv("MAX_CONTEXT_CHARS", "12000"))
    max_retrieval_k: int = int(os.getenv("MAX_RETRIEVAL_K", "6"))
    allow_cross_tenant: bool = _bool("ALLOW_CROSS_TENANT", False)
    enable_trace: bool = _bool("ENABLE_TRACE", True)

    @classmethod
    def from_env(cls) -> "Settings":
        """Create a fresh settings snapshot after environment changes."""

        return cls(
            app_name=os.getenv("APP_NAME", "Enterprise GraphRAG Agent"),
            environment=os.getenv("APP_ENV", "development"),
            llm_provider=os.getenv("LLM_PROVIDER", "demo"),
            llm_base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            max_context_chars=int(os.getenv("MAX_CONTEXT_CHARS", "12000")),
            max_retrieval_k=int(os.getenv("MAX_RETRIEVAL_K", "6")),
            allow_cross_tenant=_bool("ALLOW_CROSS_TENANT", False),
            enable_trace=_bool("ENABLE_TRACE", True),
        )

    def validate_for_production(self) -> list[str]:
        errors: list[str] = []
        if self.environment == "production" and self.llm_provider != "demo" and not self.llm_api_key:
            errors.append("LLM_API_KEY is required when APP_ENV=production")
        if self.max_retrieval_k < 1:
            errors.append("MAX_RETRIEVAL_K must be >= 1")
        if self.max_context_chars < 500:
            errors.append("MAX_CONTEXT_CHARS must be >= 500")
        if self.allow_cross_tenant:
            errors.append("ALLOW_CROSS_TENANT must remain false for tenant isolation")
        return errors
