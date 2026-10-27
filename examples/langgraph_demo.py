"""Run: PYTHONPATH=src python examples/langgraph_demo.py"""

import json
import uuid
from dataclasses import asdict

from enterprise_graphrag.agentic import demo_agent
from enterprise_graphrag.demo_data import demo_graph
from enterprise_graphrag.models import UserContext
from enterprise_graphrag.providers import DemoProvider
from enterprise_graphrag.workflows.langgraph import build_graph, memory_checkpointer

runner = demo_agent(demo_graph(), provider=DemoProvider())
graph = build_graph(list(runner.tools.values()), provider=runner.provider, checkpointer=memory_checkpointer())
config = {"configurable": {"thread_id": uuid.uuid4().hex}, "max_concurrency": 4}
result = graph.invoke({"question": "比较商品库存并总结售后规则", "user": UserContext()}, config)
print(json.dumps(result, default=asdict, ensure_ascii=False, indent=2))
print("Checkpoint available:", bool(graph.get_state(config).values))
