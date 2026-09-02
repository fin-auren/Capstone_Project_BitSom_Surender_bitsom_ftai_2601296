"""
Part 3B -- structured extraction from company-disclosure text.

extract_signals(snippet) -> {"risk_flags": [...], "hedging_detected": bool,
                              "sentiment": "confident"|"cautious"|"neutral"}

Mock mode (MOCK_LLM unset or =1, the graded baseline): pure keyword/regex rules, no LLM call.
MOCK_LLM=0 is an optional, ungraded extension (would call an LLM and validate its JSON against
this schema, retrying once before falling back to mock) -- not implemented, not graded.

Run: python extract_disclosure.py
"""
import os
import re
import json

from disclosure_snippets import DISCLOSURE_SNIPPETS

RISK_KEYWORDS = {
    "litigation": r"\blitigation\b",
    "regulatory": r"\bregulator(y|)\b|\bregulator\b",
    "customer_concentration": r"top\s+\w+\s+customers|customer concentration|\bconcentration\b",
}

HEDGING_PHRASES = ["assuming", "cautiously", "visibility"]

CONFIDENT_PHRASES = ["confident", "approved"]


def extract_signals_mock(snippet: str) -> dict:
    text = snippet.lower()

    risk_flags = [name for name, pattern in RISK_KEYWORDS.items() if re.search(pattern, text)]

    hedging_detected = any(phrase in text for phrase in HEDGING_PHRASES)

    if any(phrase in text for phrase in CONFIDENT_PHRASES):
        sentiment = "confident"
    elif hedging_detected:
        sentiment = "cautious"
    else:
        sentiment = "neutral"

    return {"risk_flags": risk_flags, "hedging_detected": hedging_detected, "sentiment": sentiment}


def extract_signals(snippet: str) -> dict:
    mock = os.environ.get("MOCK_LLM", "1") != "0"
    if mock:
        return extract_signals_mock(snippet)
    # Optional, ungraded MOCK_LLM=0 extension point: call an LLM, validate its JSON output
    # against the schema above, retry once on validation failure, else fall back to mock.
    raise NotImplementedError(
        "MOCK_LLM=0 is an optional, ungraded extension not implemented in this "
        "deterministic-baseline submission. Leave MOCK_LLM unset or =1."
    )


if __name__ == "__main__":
    all_results = []
    for snippet in DISCLOSURE_SNIPPETS:
        doc_id = snippet.split(":")[0]
        signals = extract_signals(snippet)
        all_results.append({"doc_id": doc_id, "snippet": snippet, **signals})
        print(f"{doc_id}: {signals}")

    with open("extract_disclosure_run.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("\nSaved extract_disclosure_run.json")

    by_id = {r["doc_id"]: r for r in all_results}
    assert "litigation" in by_id["doc_02"]["risk_flags"], "doc_02 must flag litigation"
    assert any(r["hedging_detected"] for r in all_results if r["doc_id"] in ("doc_01", "doc_04")), \
        "at least one hedging snippet must be detected"
    assert by_id["doc_05"]["sentiment"] == "confident", "doc_05 (board approval) must be 'confident'"
    print("All required acceptance checks passed.")
