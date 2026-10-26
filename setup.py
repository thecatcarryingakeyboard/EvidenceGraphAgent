"""Legacy setuptools shim for environments whose pip predates PEP 621."""

from setuptools import find_packages, setup


setup(
    name="enterprise-graphrag-agent",
    version="0.1.0",
    description="A tenant-aware, evidence-grounded GraphRAG Agent reference implementation",
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    extras_require={
        "api": ["fastapi>=0.115", "uvicorn[standard]>=0.30"],
        "llm": ["openai>=1.50"],
        "dev": ["pytest>=8", "ruff>=0.6"],
        "all": ["fastapi>=0.115", "uvicorn[standard]>=0.30", "openai>=1.50", "pytest>=8", "ruff>=0.6"],
    },
    entry_points={"console_scripts": ["enterprise-graphrag=enterprise_graphrag.cli:main"]},
)
