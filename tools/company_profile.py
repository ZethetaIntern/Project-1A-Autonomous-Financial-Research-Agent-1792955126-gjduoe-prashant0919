"""Company profile tool for financial research."""

from typing import Any
import yfinance as yf

MOCK_COMPANIES: dict[str, dict[str, Any]] = {
    "MSFT": {
        "company_name": "Microsoft Corporation",
        "ticker": "MSFT",
        "sector": "Technology",
        "industry": "Software - Infrastructure",
        "description": "A global technology company focused on software, enterprise cloud infrastructure (Azure), productivity solutions, and AI.",
        "executives": ["Satya Nadella (CEO)", "Amy Hood (CFO)", "Brad Smith (Vice Chair & President)"],
        "data_source": "mock",
    },
    "AAPL": {
        "company_name": "Apple Inc.",
        "ticker": "AAPL",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "description": "A global leader in consumer hardware, operating systems, and services including iPhone, Mac, iPad, and Apple Intelligence.",
        "executives": ["Tim Cook (CEO)", "Luca Maestri (CFO)", "Jeff Williams (COO)"],
        "data_source": "mock",
    },
    "TSLA": {
        "company_name": "Tesla, Inc.",
        "ticker": "TSLA",
        "sector": "Consumer Cyclical",
        "industry": "Auto Manufacturers & Clean Energy",
        "description": "An electric vehicle, battery storage, and AI autonomous systems company manufacturing EVs, Megapacks, and Full Self-Driving software.",
        "executives": ["Elon Musk (Technoking/CEO)", "Vaibhav Taneja (CFO)", "Tom Zhu (SVP)"],
        "data_source": "mock",
    },
    "AMZN": {
        "company_name": "Amazon.com, Inc.",
        "ticker": "AMZN",
        "sector": "Consumer Cyclical & Technology",
        "industry": "Internet Retail & Cloud Infrastructure",
        "description": "Global e-commerce and cloud provider operating AWS (Amazon Web Services), Prime services, logistics networks, and advertising.",
        "executives": ["Andy Jassy (President & CEO)", "Brian Olsavsky (CFO)", "Matt Garman (CEO AWS)"],
        "data_source": "mock",
    },
    "GOOGL": {
        "company_name": "Alphabet Inc.",
        "ticker": "GOOGL",
        "sector": "Communication Services",
        "industry": "Internet Content & Cloud",
        "description": "Holding company of Google, Android, YouTube, and Google Cloud Platform (GCP), pioneering AI research and digital advertising.",
        "executives": ["Sundar Pichai (CEO)", "Anat Ashkenazi (CFO)", "Ruth Porat (President & CIO)"],
        "data_source": "mock",
    },
    "NVDA": {
        "company_name": "NVIDIA Corporation",
        "ticker": "NVDA",
        "sector": "Technology",
        "industry": "Semiconductors",
        "description": "Pioneer of GPU accelerated computing, leading the global AI infrastructure market with Hopper and Blackwell architectures and CUDA ecosystem.",
        "executives": ["Jensen Huang (Founder & CEO)", "Colette Kress (EVP & CFO)", "Jay Puri (EVP Worldwide Field Ops)"],
        "data_source": "mock",
    },
    "PLTR": {
        "company_name": "Palantir Technologies Inc.",
        "ticker": "PLTR",
        "sector": "Technology",
        "industry": "Software - Infrastructure & AI Platforms",
        "description": "Enterprise software and artificial intelligence platform provider operating Gotham, Foundry, and AIP (Artificial Intelligence Platform).",
        "executives": ["Alex Karp (Co-founder & CEO)", "David Glazer (CFO)", "Shyam Sankar (CTO)"],
        "data_source": "mock_and_filings",
    },
}


def get_company_profile(ticker: str) -> dict[str, Any]:
    """Return a profile for a ticker, using curated data with yfinance fallback."""
    normalized_ticker = ticker.strip().upper()

    if not normalized_ticker:
        raise ValueError("Ticker cannot be empty.")

    if normalized_ticker in MOCK_COMPANIES:
        return dict(MOCK_COMPANIES[normalized_ticker])

    # Dynamic fallback via yfinance
    try:
        stock = yf.Ticker(normalized_ticker)
        info = stock.info or {}
        return {
            "company_name": info.get("longName", f"{normalized_ticker} Corporation"),
            "ticker": normalized_ticker,
            "sector": info.get("sector", "General Industry"),
            "industry": info.get("industry", "Diversified"),
            "description": info.get("longBusinessSummary", f"Publicly traded corporation under ticker {normalized_ticker}"),
            "executives": [info.get("companyOfficers", [{}])[0].get("name", "Executive Management")] if info.get("companyOfficers") else [],
            "data_source": "yfinance_live_profile",
        }
    except Exception:
        return {
            "company_name": f"{normalized_ticker} Corporation",
            "ticker": normalized_ticker,
            "sector": "Corporate",
            "industry": "General Business",
            "description": f"Public enterprise with symbol {normalized_ticker}.",
            "executives": ["Corporate Leadership"],
            "data_source": "fallback_profile",
        }
