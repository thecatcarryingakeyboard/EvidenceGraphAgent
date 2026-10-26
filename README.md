# Enterprise GraphRAG Agent

一个面向企业知识库的 GraphRAG Agent 参考实现。它把原始 AssistGen 项目中的 FastAPI、LangGraph、Microsoft GraphRAG、Neo4j、Redis、Ollama/DeepSeek 方向，收敛成一个可以直接阅读、测试和扩展的开源最小闭环：**租户隔离 → 混合检索 → 图扩展 → 证据引用 → 可拒答生成 → 轨迹审计 → 回归评测**。

项目默认使用离线规则模型和内存图谱，克隆后不需要 API Key、Neo4j、Redis 或 GPU 就能运行。接入生产环境时，可以把同一套接口替换成 OpenAI-compatible 模型、PostgreSQL/pgvector、Neo4j、Microsoft GraphRAG、OpenTelemetry 和 MCP 工具。

## 为什么做这个版本

原始目录适合学习和演示，但不适合直接公开：其中包含 vendored 的 GraphRAG 源码、索引 parquet、日志、`node_modules`、本地 `.env` 和数据库密码。这个仓库只保留可审计的业务代码和合成 demo 数据，不复制上游源码或私有配置。上游 Microsoft GraphRAG 仍通过适配器接入，许可证和版本由上游项目负责。

## 能力矩阵

| 能力 | 当前实现 | 生产替换点 |
| --- | --- | --- |
| Local / Global / Deep 查询 | 词法召回 + 实体共现图扩展 | GraphRAG/LightRAG/KAG 或 Neo4j + pgvector |
| 企业权限 | 每个文档、chunk、实体带 `tenant_id` | RBAC/ABAC、行级权限、审计策略 |
| 证据链 | 每条答案返回 chunk、文档、原文片段和分数 | 文档页码、表格单元格、图片区域、签名 URL |
| 不确定性 | 无证据时拒答；高风险动作提示人工确认 | 置信度校准、人工审批、NeMo Guardrails |
| Agent 治理 | 路由、检索、生成、审计状态清晰分层 | LangGraph durable execution、MCP allowlist、超时/预算 |
| 可观测性 | trace id、阶段耗时、租户和引用数量 | OpenTelemetry + Phoenix/OpenLLMetry |
| 评测 | 术语召回、引用率、拒答率回归集 | Ragas/DeepEval、离线集和线上反馈 |

## 30 秒运行

```bash
cd enterprise-graphrag-agent
PYTHONPATH=src python -m enterprise_graphrag.cli ask "上线前需要完成哪些工作？"
PYTHONPATH=src python -m enterprise_graphrag.cli eval --json
```

启动无依赖 demo API：

```bash
PYTHONPATH=src python -m enterprise_graphrag.cli demo
curl -s http://127.0.0.1:8765/health
curl -s http://127.0.0.1:8765/v1/query \
  -H 'content-type: application/json' \
  -d '{"query":"MCP 工具如何治理？","mode":"deep"}'
```

如果需要 FastAPI/OpenAPI：

```bash
python -m venv .venv && source .venv/bin/activate
pip install '.[api,llm]'
uvicorn enterprise_graphrag.api:create_app --factory --reload
```

## 目录

```text
src/enterprise_graphrag/
  store.py       # 租户感知的文档、chunk、实体和关系
  retrieval.py   # local/global/deep 混合检索
  pipeline.py    # 路由、检索、引用、生成、审计
  providers.py   # 离线 provider 和 OpenAI-compatible provider
  api.py         # 可选 FastAPI 服务
  server.py      # Python 标准库 demo 服务
  eval.py        # 可放入 CI 的回归评测
tests/           # 不依赖外部服务的测试
docs/            # 架构、评测和部署说明
demo/knowledge/  # 合成企业文档
```

## 面向企业的设计约束

1. **证据优先。** 生成器接收的是结构化 `Citation`，不是一段无来源的拼接文本。客户端可以把引用映射回原文或文档页。
2. **权限先于检索。** 检索器只看当前 `tenant_id` 的 chunk；不要在应用层检索后再过滤权限。
3. **工具可治理。** MCP/函数工具应放在显式 allowlist 中，带租户上下文、超时、预算和人工确认。工具返回值同样要进入证据链。
4. **允许拒答。** 没有足够证据时返回 `abstained=true`，避免用流畅语言掩盖知识缺口。
5. **评测和观测是接口。** 每次查询都有 `trace_id`、阶段耗时、引用数和模式；评测指标可以在替换模型后保持可比。

## 与原始 AssistGen 项目的关系

原始 AssistGen 工作树中的 LangGraph Agent、GraphRAG 查询、Neo4j 子图、Redis 语义缓存和 Vue 前端仍可作为后续适配器的来源。本仓库不直接复制原始目录，以避免把本地密钥、课程资料和 GraphRAG vendored 源码发布出去。建议后续迁移顺序：

1. 将原始 `app/graphrag/dev/graphrag_query.py` 封装成 `AnswerProvider` 或 `Retriever` 适配器；
2. 将 `kg_neo4j_conn.py` 的查询能力映射到 `KnowledgeGraph.expand`；
3. 用原始 Vue 页面替换 demo 前端，并显示 `citations` 和 `trace`；
4. 用真实租户脱敏数据补充 `eval/`，再接入 CI 门禁。

## 参考项目与技术依据

- [Microsoft GraphRAG](https://github.com/microsoft/graphrag)：社区摘要、local/global/drift 查询和成本提示。
- [LightRAG](https://github.com/HKUDS/LightRAG)：图与向量混合检索、多后端和多模态扩展。
- [KAG](https://github.com/OpenSPG/KAG)：逻辑形式引导的精确、文本、数值和语义检索。
- [RAGFlow](https://github.com/infiniflow/ragflow)：文档解析、知识编译、Agentic Retrieval 和引用追踪。
- [PageIndex](https://github.com/VectifyAI/PageIndex)：长专业文档的树结构检索和页级引用。
- [LangGraph](https://github.com/langchain-ai/langgraph)：有状态 Agent、持久化执行和人工介入。
- [Ragas](https://github.com/explodinggradients/ragas) / [DeepEval](https://github.com/confident-ai/deepeval)：RAG、Agent 和工具调用评测。
- [Model Context Protocol servers](https://github.com/modelcontextprotocol/servers)：受控工具和知识图谱服务参考。

## 开发

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src
```

发布前的远程仓库操作见 [docs/publishing.md](docs/publishing.md)。

代码采用 MIT License。第三方依赖和参考项目的说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)；接入新的 GraphRAG、解析器、模型或数据集时，请分别遵守其许可证与使用条款。
