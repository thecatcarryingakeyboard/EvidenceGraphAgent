"""Command line entry points."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agentic import demo_agent
from .demo_data import demo_graph
from .eval import EvalCase, run_eval
from .ingest import ingest_path
from .models import QueryRequest, UserContext
from .pipeline import QueryEngine
from .server import serve
from .store import KnowledgeGraph


def main() -> None:
    parser = argparse.ArgumentParser(description="EvidenceGraph Agent")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="start the dependency-free demo server")
    demo.add_argument("--host", default="127.0.0.1")
    demo.add_argument("--port", type=int, default=8765)
    ask = sub.add_parser("ask", help="ask the built-in demo corpus")
    ask.add_argument("query")
    ask.add_argument("--mode", choices=["local", "global", "deep"], default="local")
    agent = sub.add_parser("agent", help="run the multi-stage offline Agent workflow")
    agent.add_argument("query")
    ingest = sub.add_parser("ingest", help="ingest Markdown/text files and answer a question")
    ingest.add_argument("path")
    ingest.add_argument("query")
    ingest.add_argument("--tenant", default="demo")
    evaluate = sub.add_parser("eval", help="run the deterministic regression set")
    evaluate.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.command == "demo":
        serve(host=args.host, port=args.port)
        return
    if args.command == "ask":
        response = QueryEngine(demo_graph()).answer(QueryRequest(args.query, mode=args.mode))
        print(json.dumps(response.to_dict(), ensure_ascii=False, indent=2))
        return
    if args.command == "agent":
        graph = demo_graph()
        state = demo_agent(graph).run(QueryRequest(args.query))
        print(json.dumps(state.to_dict(), ensure_ascii=False, indent=2, default=str))
        return
    if args.command == "ingest":
        graph = KnowledgeGraph()
        ingest_path(graph, Path(args.path), args.tenant)
        response = QueryEngine(graph).answer(QueryRequest(args.query, user=UserContext(tenant_id=args.tenant)))
        print(json.dumps(response.to_dict(), ensure_ascii=False, indent=2))
        return
    if args.command == "eval":
        engine = QueryEngine(demo_graph())
        report = run_eval(
            engine,
            [
                EvalCase("上线前需要完成哪些工作？", ("权限", "评测")),
                EvalCase("没有足够证据时应该怎么办？", ("拒答",)),
                EvalCase("MCP 工具如何治理？", ("allowlist", "租户")),
            ],
        )
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) if args.json else report.to_dict())


if __name__ == "__main__":
    main()
