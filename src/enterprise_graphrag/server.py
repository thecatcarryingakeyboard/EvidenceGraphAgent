"""Dependency-free demo HTTP server, useful for a fresh clone."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .demo_data import demo_graph
from .models import QueryRequest, UserContext
from .pipeline import QueryEngine


class Handler(BaseHTTPRequestHandler):
    engine = QueryEngine(demo_graph())

    def _send(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send({"status": "ok"})
        elif self.path in {"/", "/index.html"}:
            candidates = [Path(__file__).resolve().parents[2] / "web" / "index.html", Path.cwd() / "web" / "index.html"]
            page = next((candidate for candidate in candidates if candidate.exists()), None)
            if page is not None:
                body = page.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self._send({"error": "demo page not found"}, 404)
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/query":
            self._send({"error": "not found"}, 404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(size) or b"{}")
            question = str(payload.get("query", "")).strip()
            if not question:
                self._send({"error": "query is required"}, 422)
                return
            user = UserContext(str(payload.get("tenant_id", "demo")), str(payload.get("user_id", "anonymous")))
            response = self.engine.answer(QueryRequest(question, user=user, mode=payload.get("mode", "local")))
            self._send(response.to_dict())
        except (ValueError, json.JSONDecodeError) as exc:
            self._send({"error": str(exc)}, 400)


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Enterprise GraphRAG Agent demo: http://{host}:{port}")
    print("POST /v1/query with {\"query\": \"...\"}; Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
