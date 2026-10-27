# 运行示例

```bash
PYTHONPATH=src python -m enterprise_graphrag.cli demo
```

打开 http://127.0.0.1:8765/ ，选择“多工具 Agent”。

| 问题 | 应检查的结果 |
| --- | --- |
| 哪些商品库存不足需要补货 | catalog_query 实际执行 SQLite 参数化查询，只返回 Pro（库存 8）。 |
| 比较商品库存并总结售后规则 | 两个子任务分别选择 catalog_query、graph_search，汇总为唯一 C 引用。 |
| 火星飞船发射时间 | 本地知识库无可引用证据时 abstained=true。 |

网页展示答案、证据卡片和可展开的执行响应。它使用合成数据，不连接真实业务系统。

命令行同样可运行：

```bash
PYTHONPATH=src python -m enterprise_graphrag.cli agent "比较商品库存并总结售后规则"
```

安装 `.[langgraph]` 后运行 `PYTHONPATH=src python examples/langgraph_demo.py`，验证并行工具与 checkpoint；外部 Neo4j 与 GraphRAG 接入见 integrations.md。
