"""Small synthetic enterprise corpus used in demos and tests."""

from __future__ import annotations

from .models import Document
from .store import KnowledgeGraph


DEMO_DOCUMENTS = (
    Document(
        id="doc_handbook",
        title="企业 AI 助手上线手册",
        source_uri="demo://handbook",
        text=(
            "企业 AI 助手上线前需要完成数据分级、权限校验、离线评测和人工审批。\n"
            "知识库文档按租户隔离，回答必须返回来源片段和文档标识。\n"
            "高风险动作（付款、删除、外发）必须进入人工确认队列，Agent 不得绕过审批。\n"
            "生产环境建议使用 PostgreSQL/pgvector 或 Neo4j 保存索引，并将 trace 写入 OpenTelemetry。"
        ),
    ),
    Document(
        id="doc_eval",
        title="检索增强生成评测规范",
        source_uri="demo://eval",
        text=(
            "企业 RAG 评测至少应覆盖检索召回率、引用覆盖率、答案忠实度、延迟和成本。\n"
            "没有足够证据时应拒答或请求补充，而不是生成看似完整的答案。\n"
            "评测集需要包含权限边界、跨文档推理和时间有效性案例，并在 CI 中阻止指标回退。"
        ),
    ),
    Document(
        id="doc_architecture",
        title="GraphRAG Agent 参考架构",
        source_uri="demo://architecture",
        text=(
            "系统由路由器、混合检索器、证据编排器、工具策略和审计层组成。\n"
            "local 模式回答局部事实，global 模式使用实体关系扩展上下文，deep 模式允许多跳检索。\n"
            "MCP 工具需要显式 allowlist、租户上下文和超时限制；工具调用结果也要进入引用链。"
        ),
    ),
)


def demo_graph() -> KnowledgeGraph:
    graph = KnowledgeGraph()
    for document in DEMO_DOCUMENTS:
        graph.ingest(document)
    return graph
