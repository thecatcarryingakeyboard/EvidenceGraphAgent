# 设计来源与技术演进

项目沿用原 AssistGen 学习工程中“规划 → 选择工具 → 结构化查询 / GraphRAG → 汇总”的主线，在独立公开仓库中重构。原始工程的本地环境、课程 PDF、前端构建产物、数据库导出和整份第三方 GraphRAG 源码均不作为发布内容。

| 原有设计 | 本仓库的整理与改进 |
| --- | --- |
| Neo4j 查询与文档检索工具 | 保留不同工具入口；离线结构化查询实际执行 SQLite SQL，真实 Neo4j 另有读事务客户端。 |
| 规划与工具路由 | 保留显式子任务和工具结果；规则版本可重复运行，可替换自定义规划器、路由器。 |
| Cypher 生成、校验、重试 | 保留生成器接口和 EXPLAIN，补充保守只读策略、读事务、超时与重试历史。 |
| GraphRAG local/global/DRIFT/basic | 适配固定的 2.1.0 API，区分各方法的参数；索引从外部项目加载。 |
| LangGraph 状态图 | 使用 Send 并行派发任务；调用者可以注入 checkpoint，示例验证内存状态读取。 |
| 汇总结果 | 将结构化行和文档片段统一为 Citation；去重、全局编号并验证引用 ID。 |
| 查询失败时直接结束 | 同步 Agent 增加单次文档回退和总工具调用预算。 |

## 公开资料核对（2026-10-27）

- [GraphRAG v2.1.0 query API](https://github.com/microsoft/graphrag/blob/v2.1.0/graphrag/api/query.py)：已核对 local/global/DRIFT/basic 的函数签名。DRIFT 不接受 covariates，basic 不接受 response_type；回归测试覆盖这些差异。
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)：checkpoint 通过 thread_id 关联执行状态，持久化能力由 saver 提供。当前测试使用内存 saver，未声明跨进程持久化。
- [LightRAG README](https://github.com/HKUDS/LightRAG)：混合检索、增量处理与 reranking 可作为后续实验方向。当前没有复制其算法实现，也没有与其做质量对比。

本次 GitHub API 请求未能获取可靠的实时星数，因此不把未经核实的星数和排名写入项目介绍。技术选择以可运行实现和官方接口为依据。
