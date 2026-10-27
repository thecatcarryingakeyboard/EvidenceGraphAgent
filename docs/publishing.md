# Publishing checklist

This repository is intended to be public and contains only synthetic demo data and optional integration boundaries.

Before pushing a release:

```bash
python scripts/check_open_source.py
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src
git diff --check
git status --short
```

The public repository should contain `.env.example`, never `.env`. Do not add the original working directory as a subdirectory, and do not copy its logs, uploads, PDFs, parquet outputs, model caches, `node_modules` or vendored GraphRAG source.

If a real credential has ever appeared in a local file or commit, rotate it before publishing. Removing the file in a later commit does not make an exposed credential safe. Review GitHub secret scanning and the full Git history before making the repository public.

The recommended first public commit should explain that this is a learning and reference project, link the upstream GraphRAG/LangGraph projects, and state which optional integrations were actually tested. Avoid claiming benchmark or production results that were not measured.
