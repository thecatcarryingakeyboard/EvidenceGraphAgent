FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY web ./web
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

EXPOSE 8765
CMD ["python", "-m", "enterprise_graphrag.cli", "demo", "--host", "0.0.0.0"]
