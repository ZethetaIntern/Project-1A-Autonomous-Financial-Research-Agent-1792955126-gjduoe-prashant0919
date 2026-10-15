"""Setup configuration for the autonomous financial research agent package."""

from setuptools import find_packages, setup

setup(
    name="autonomous-financial-research-agent",
    version="1.0.0",
    description="Autonomous Financial Research Agent with Multi-Source Synthesis",
    author="Prashant Bastola",
    author_email="bastolaprashant0919@gmail.com",
    packages=find_packages(exclude=["tests*", "docs*", "results*"]),
    python_requires=">=3.11",
    install_requires=[
        "langchain>=0.2.0",
        "langgraph>=0.1.0",
        "chromadb>=0.4.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "tenacity>=8.2.0",
        "yfinance>=0.2.36",
        "beautifulsoup4>=4.12.0",
        "httpx>=0.27.0",
    ],
)
