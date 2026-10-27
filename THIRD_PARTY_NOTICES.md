# Third-party notices

This repository does not vendor third-party source code, model weights,
customer data, course material or document assets. The links in the README and
roadmap are references to independent projects and do not imply endorsement,
affiliation or official support.

The optional `MicrosoftGraphRAGAdapter` imports a separately installed
Microsoft GraphRAG package at runtime. Microsoft GraphRAG is distributed under
the MIT License; users who install it must keep its own license and copyright
notice. This repository does not redistribute that package.

FastAPI, Uvicorn, LangGraph, the Neo4j Python driver, langchain-neo4j and the
OpenAI Python SDK are optional external dependencies.
Their licenses apply to the installed distributions and should be reviewed in
the deployment lockfile. If a future adapter bundles a parser, vector store,
MCP server, model, dataset or frontend asset, add its exact version, source URL,
license and required notices here before publishing.

The name “GraphRAG” is used descriptively to identify a class of graph-backed
retrieval methods. This project is not affiliated with Microsoft.
