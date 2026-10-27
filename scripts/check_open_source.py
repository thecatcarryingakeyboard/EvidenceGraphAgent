"""Fail fast if common local secrets/artifacts are accidentally staged."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_NAMES = {".env", ".DS_Store", "dist.zip", "node_modules"}
SECRET_PATTERNS = [re.compile(r"sk-[A-Za-z0-9]{12,}"), re.compile(r"password\s*[:=]\s*[^\s]+", re.I)]
PLACEHOLDERS = {"...", "xxx", "changeme", "change-me", "your-key", "your_password"}


def main() -> int:
    failures: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if any(part in FORBIDDEN_NAMES for part in path.parts):
            failures.append(f"forbidden artifact: {path.relative_to(ROOT)}")
            continue
        if path.suffix.lower() not in {".md", ".py", ".toml", ".yml", ".yaml", ".json", ".env.example"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line in text.splitlines():
            # Type annotations and os.getenv defaults describe configuration;
            # they do not contain a credential.
            if "os.getenv" in line or re.search(r"password\s*:\s*\w+", line, re.I):
                continue
            for pattern in SECRET_PATTERNS:
                matches = pattern.findall(line)
                suspicious = [
                    match for match in matches
                    if not any(token in match.lower() for token in PLACEHOLDERS)
                    and "your_" not in match.lower()
                ]
                if suspicious and path.name != ".env.example":
                    failures.append(f"possible secret: {path.relative_to(ROOT)}")
    if failures:
        print("\n".join(failures))
        return 1
    print("open-source hygiene check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
