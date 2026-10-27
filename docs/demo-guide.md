# Demo guide

这份指南帮助第一次使用项目的人快速跑通一条完整查询链路。

## 1. 启动离线服务

```bash
PYTHONPATH=src python -m enterprise_graphrag.cli demo
```

打开 <http://127.0.0.1:8765/>，或者直接运行 Agent：

```bash
PYTHONPATH=src python -m enterprise_graphrag.cli agent "比较商品库存并总结售后规则"
```

输出中的 `steps` 展示 `guardrails → planner → tool_selection → tools → summarize → validate_answer → final_answer`，`selected_tools` 展示每个子任务实际选择的工具。

## 2. 三类查询工具

- **预定义 Cypher**：高频、稳定、容易审计的查询；
- **Text2Cypher**：根据 schema 生成只读查询，执行前做 schema 检查和 `EXPLAIN`，失败时在预算内重试；
- **GraphRAG**：处理文档语义、社区摘要、全局总结和多跳证据。

结构化查询和文档检索最后统一成 `ToolResult`，由证据编排层生成引用，再交给答案提供器。

## 3. 可靠性边界

1. Guardrails 拒绝空问题和明显越界问题；
2. Tool 层返回结构化结果和证据；
3. Neo4j 查询禁止写操作，并使用参数化查询；
4. 最终答案保留引用，证据为空或引用缺失时 abstain。

真实部署还需要接入认证上下文、文档 ACL、持久化 checkpoint、人工审批和线上评测。离线实现使用规则 Planner/Router，是为了让行为可重复并方便阅读。

## 4. 进一步实验

可以从下面的方向扩展：

- 将 `SimplePlanner` 和 `RuleToolRouter` 替换为结构化 LLM 输出；
- 在 LangGraph 工作流中加入 checkpoint、`Send` 并行和 `interrupt`；
- 比较 local/global/DRIFT 查询的质量、延迟和 token 成本；
- 增加时间有效性、权限边界和不可回答问题的评测集；
- 将 trace 接入 OpenTelemetry、Phoenix 或 Langfuse。
