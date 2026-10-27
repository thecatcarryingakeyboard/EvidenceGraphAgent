"""Scan Git publication candidates and optional reachable history, without printing secrets."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    "API credential": re.compile(
        r"(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16})"
    ),
    "private key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    "personal home path": re.compile(r"/(?:Users|home)/[A-Za-z0-9_.-]+/"),
    "credential in URL": re.compile(r"(?:https?|bolt|postgres(?:ql)?|mysql)://[^/\s:@]+:[^/\s@]+@"),
}
ASSIGNMENT = re.compile(
    r"(?m)^[ \t]*[\"']?(?:[A-Z_]*(?:API_KEY|PASSWORD|SECRET|TOKEN))[\"']?[ \t]*[:=][ \t]*[\"']?([^\s\"',;#}]*)"
)
PLACEHOLDERS = {"", "...", "none", "null", "change-me", "changeme", "your-key", "your_password"}


def findings(name: str, data: bytes) -> list[str]:
    issues = []
    path = Path(name)
    if path.name.startswith(".env") and path.name != ".env.example":
        issues.append("environment file")
    if any(part in {".DS_Store", "node_modules", "__pycache__"} for part in path.parts):
        issues.append("local artifact")
    if path.suffix.lower() in {".pdf", ".parquet", ".db", ".log", ".zip", ".pyc"}:
        issues.append("private/generated artifact")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return issues
    for label, pattern in RULES.items():
        if pattern.search(text):
            issues.append(label)
    for match in ASSIGNMENT.finditer(text):
        value = match.group(1).lower()
        if value not in PLACEHOLDERS and not value.startswith(("your_", "${", "os.getenv", "str", "#")):
            issues.append("literal credential assignment")
    return list(dict.fromkeys(issues))


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", action="store_true", help="also scan all reachable Git blobs")
    args = parser.parse_args()
    failures = []
    names = git("ls-files", "-z", "--cached", "--others", "--exclude-standard").decode().split("\0")
    for name in sorted(set(names) - {""}):
        path = ROOT / name
        if path.is_file():
            failures.extend(f"{name}: {reason}" for reason in findings(name, path.read_bytes()))
    blobs = 0
    if args.history:
        for line in git("rev-list", "--objects", "--all").decode().splitlines():
            oid, _, name = line.partition(" ")
            if not name or git("cat-file", "-t", oid).strip() != b"blob":
                continue
            blobs += 1
            failures.extend(
                f"history {oid[:8]} {name}: {reason}" for reason in findings(name, git("cat-file", "blob", oid))
            )
    if failures:
        print("\n".join(failures))
        return 1
    paths_count = len(set(names) - {""})
    print(f"Publication scan passed: {paths_count} paths; {blobs} history blobs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
