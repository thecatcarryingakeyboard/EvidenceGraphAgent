"""Legacy setuptools shim for environments whose pip predates PEP 621."""

from setuptools import find_packages, setup


setup(
    name="enterprise-graphrag-agent",
    version="0.2.0",
    description="An interview-friendly LangGraph, Neo4j and GraphRAG learning project",
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    extras_require={
        "api": ["fastapi>=0.115", "uvicorn[standard]>=0.30"],
        "llm": ["openai>=1.50"],
        "langgraph": ["langgraph>=0.3"],
        "neo4j": ["neo4j>=5.20", "langchain-neo4j>=0.4"],
        "graphrag": ["graphrag>=2.1,<3"],
        "dev": ["pytest>=8", "ruff>=0.6"],
        "all": [
            "fastapi>=0.115", "uvicorn[standard]>=0.30", "openai>=1.50",
            "langgraph>=0.3", "neo4j>=5.20", "langchain-neo4j>=0.4",
            "graphrag>=2.1,<3", "pytest>=8", "ruff>=0.6",
        ],
    },
    entry_points={"console_scripts": [
        "enterprise-graphrag=enterprise_graphrag.cli:main",
        "assistgen-agent=enterprise_graphrag.cli:main",
    ]},
)
