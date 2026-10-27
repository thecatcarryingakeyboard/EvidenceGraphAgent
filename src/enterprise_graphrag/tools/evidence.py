"""Normalize structured query rows into citable evidence."""
import json
from hashlib import sha256
from typing import Any, Iterable

from ..models import Citation


def row_citations(rows: Iterable[dict[str, Any]], source: str) -> tuple[Citation, ...]:
    output = []
    for index, row in enumerate(rows):
        text = json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)
        identifier = sha256(text.encode()).hexdigest()[:16]
        output.append(Citation(f'ROW{index + 1}', identifier, source,
                               '结构化查询结果', text, f'{source}://result/{identifier}'))
    return tuple(output)
