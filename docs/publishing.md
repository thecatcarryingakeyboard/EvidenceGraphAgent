# Publishing checklist

The repository is already initialized on branch `main` with a clean commit.
Create an empty public GitHub repository named `enterprise-graphrag-agent`,
then run from this directory:

```bash
python3 scripts/check_open_source.py
PYTHONPATH=src python -m unittest discover -s tests -v
git remote add origin https://github.com/<your-account>/enterprise-graphrag-agent.git
git push -u origin main
```

Do not add the original AssistGen directory as a subdirectory or commit its
`.env`, logs, uploads, PDFs, parquet outputs, `node_modules` or vendored
GraphRAG source. If any real credential has ever been committed in that
working tree, rotate it before making a public repository; removing the file
from the latest commit is not enough to make an exposed credential safe.
