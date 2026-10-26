"""Small tracing abstraction; replace the sink with OpenTelemetry in production."""

from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from typing import Any, Iterator

from .models import TraceEvent


class Trace:
    def __init__(self, trace_id: str | None = None, enabled: bool = True) -> None:
        self.trace_id = trace_id or uuid.uuid4().hex
        self.enabled = enabled
        self.events: list[TraceEvent] = []

    @contextmanager
    def span(self, name: str, **attributes: Any) -> Iterator[None]:
        started = time.perf_counter()
        try:
            yield
        finally:
            if self.enabled:
                self.events.append(
                    TraceEvent(
                        name=name,
                        duration_ms=round((time.perf_counter() - started) * 1000, 3),
                        attributes=attributes,
                    )
                )
