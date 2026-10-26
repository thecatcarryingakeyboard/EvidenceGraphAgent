# Contributing

Small, focused pull requests are welcome. Please include:

1. a short problem statement and threat/permission impact;
2. a deterministic test that runs without external services when possible;
3. changes to the evaluation set when retrieval or prompting behavior changes;
4. documentation for new environment variables or optional dependencies.

Run the local checks before opening a pull request:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src
python scripts/check_open_source.py
```
