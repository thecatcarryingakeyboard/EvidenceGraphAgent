"""Legacy setuptools shim for environments whose pip predates PEP 621."""

from setuptools import find_packages, setup


setup(
    name="enterprise-graphrag-agent",
    version="0.3.0",
    description="Evidence-grounded agents for structured queries and graph document retrieval",
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    extras_require={
        "api": ["fastapi>=0.115", "uvicorn[standard]>=0.30"],
        "llm": ["openai>=1.50"],
        "langgraph": ["langgraph>=1.2.18,<2", "typing-extensions>=4.7"],
        "neo4j": ["neo4j>=5.20", "langchain-neo4j>=0.4"],
        "graphrag": ["graphrag==2.1.0"],
        "dev": ["pytest>=8", "ruff>=0.6"],
        "all": [
            "fastapi>=0.115", "uvicorn[standard]>=0.30", "openai>=1.50",
            "langgraph>=1.2.18,<2", "neo4j>=5.20", "langchain-neo4j>=0.4",
            "graphrag==2.1.0", "pytest>=8", "ruff>=0.6",
        ],
    },
    entry_points={"console_scripts": [
        "enterprise-graphrag=enterprise_graphrag.cli:main",
        "assistgen-agent=enterprise_graphrag.cli:main",
        "evidencegraph-agent=enterprise_graphrag.cli:main",
    ]},
)
