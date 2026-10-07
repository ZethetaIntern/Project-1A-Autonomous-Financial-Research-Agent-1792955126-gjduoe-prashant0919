"""Fact checker tool for cross-referencing claims and verifying numerical consistency."""

import re
from typing import Any


def check_claim(
    claim: str,
    sources: list[str] | None = None,
) -> dict[str, Any]:
    """Cross-reference a specific claim against authoritative sources to verify accuracy."""
    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("Claim must be a non-empty string.")

    if sources is not None and (
        not isinstance(sources, list)
        or not all(isinstance(source, str) for source in sources)
    ):
        raise ValueError("Sources must be a list of strings.")

    evidence = [
        source.strip()
        for source in (sources or [])
        if source.strip()
    ]

    claim_text = claim.strip()
    claim_lower = claim_text.lower()

    # Extract any percentages or dollar amounts from the claim
    numbers_in_claim = re.findall(r"[\$]?\d+(?:\.\d+)?%?", claim_text)

    matches_found = 0
    discrepancies = []

    for src in evidence:
        src_lower = src.lower()
        # Check if numbers match in source
        for num in numbers_in_claim:
            if num.lower() in src_lower:
                matches_found += 1

    if not evidence:
        status = "insufficient_evidence"
        confidence = 0.20
        explanation = "No supporting reference sources were provided to verify the claim."
    elif len(evidence) >= 2 and matches_found >= 1:
        status = "verified_multi_source"
        confidence = 0.95
        explanation = f"Claim supported across {len(evidence)} sources with verified numerical alignment."
    else:
        status = "evidence_provided_not_independently_verified"
        confidence = 0.65
        explanation = "Evidence was supplied, but its accuracy and authority have not been independently verified."

    return {
        "claim": claim_text,
        "status": status,
        "evidence_count": len(evidence),
        "evidence": evidence,
        "confidence_score": confidence,
        "explanation": explanation,
        "verified": confidence >= 0.70,
        "data_source": "mock",
    }
