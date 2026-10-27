# 外部集成

## Microsoft GraphRAG 2.1.0

在单独的 Python 3.11/3.12 环境安装 `pip install -e '.[graphrag]'`，使用上游 CLI 在仓库之外创建项目并完成索引。保持 settings.yaml 与索引所用 embedding 模型一致。

```python
from enterprise_graphrag.adapters.graphrag import MicrosoftGraphRAGAdapter

adapter = MicrosoftGraphRAGAdapter.from_project(
    '/path/to/your/graphrag-project', community_level=2
)
answer, citations = adapter.query('售后问题有哪些主要主题？', mode='global')
```

在异步应用中使用 `await adapter.query_async(...)`。from_project 读取 settings.yaml 指定的 output 目录中的 entities、relationships、communities、community_reports 和 text_units parquet。密钥由该外部项目的上游配置读取；本库不会复制索引或密钥。

GraphRAG 返回的社区报告可以作为上下文证据，但不自动等价于原始文档级 provenance；不能把社区报告内容声称为已经定位到原文页码。当前兼容目标固定为 2.1.0，更换版本应重新验证索引格式和 API。

## Neo4j

参考 `examples/neo4j_demo.py`。它要求调用方显式给出 schema，执行前调用 EXPLAIN，并在读事务中执行查询。schema 用于生成器提示，不实现完整 Cypher AST/schema 语义校验。

`PredefinedCypherTool.run_named(name, parameters)` 是已审核语句入口；其默认 run 方法把任务文本视为查询名。若使用自然语言路由，需要自定义查询名和参数的选择器。`Text2CypherExecutor` 接受自定义生成器，不内置任意数据库的通用模型提示。

客户端 tenant 参数不是认证凭证，外部 Neo4j 与 GraphRAG 适配器不自动强制多租户隔离；请为每个授权范围配置独立索引/数据库或服务端授权。
