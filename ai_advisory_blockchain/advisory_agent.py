"""
Part 3A -- Portfolio advisory agent using an explicit think -> act (tool call) ->
observe/decide loop, with human-in-the-loop escalation above 20% portfolio volatility.

The final narrative sentence is the ONLY part gated by MOCK_LLM (default / MOCK_LLM=1 =
deterministic f-string template; MOCK_LLM=0 is an optional, ungraded extension that would
call a real LLM instead -- not required or graded).

Run: python advisory_agent.py
"""
import os
import math
import json

from stock_universe import STOCK_UNIVERSE, RISK_FREE_RATE, MARKET_RETURN
from investor_profiles import INVESTOR_PROFILES

CORRELATION_RHO = 0.3  # stated pairwise correlation for every pair in an allocation

# Prescribed, fixed lookup table -- not a free-choice mapping.
ALLOCATION_TABLE = {
    "Conservative": ["PAYBOND", "PAYGOLD", "PAYRETAIL"],
    "Moderate": ["PAYRETAIL", "PAYINFRA", "PAYGOLD"],
    "Aggressive": ["PAYTECH", "PAYFIN", "PAYINFRA"],
}

ESCALATION_THRESHOLD_STD = 0.20


# ---------------------------------------------------------------- ACT (tool call)
def get_stock_data(ticker: str) -> dict:
    """Simulates an external market-data-API tool call; data is looked up locally."""
    if ticker not in STOCK_UNIVERSE:
        raise KeyError(f"Unknown ticker: {ticker}")
    return dict(STOCK_UNIVERSE[ticker])  # copy, as a real API response would be


def capm_expected_return(beta: float) -> float:
    """E(R) = R_f + beta * (E(R_m) - R_f). Uses ONLY beta -- never analyst_expected_return."""
    return RISK_FREE_RATE + beta * (MARKET_RETURN - RISK_FREE_RATE)


def portfolio_stats(tickers: list, tool_data: dict, weights=None):
    n = len(tickers)
    if weights is None:
        weights = [1 / n] * n  # equal-weight, per the prescribed allocation table

    # CAPM expected return per stock, weight-averaged
    stock_returns = [capm_expected_return(tool_data[t]["beta"]) for t in tickers]
    portfolio_return = sum(w * r for w, r in zip(weights, stock_returns))

    # Portfolio variance: Var = sum(w_i^2 sigma_i^2) + 2*sum_{i<j} w_i w_j Cov(i,j)
    sigmas = [tool_data[t]["std_dev"] for t in tickers]
    var = sum((w ** 2) * (s ** 2) for w, s in zip(weights, sigmas))
    for i in range(n):
        for j in range(i + 1, n):
            cov_ij = CORRELATION_RHO * sigmas[i] * sigmas[j]
            var += 2 * weights[i] * weights[j] * cov_ij
    std = math.sqrt(var)
    return portfolio_return, var, std


def narrative_sentence(investor_id, risk_tolerance, tickers, ret, vol):
    """The only MOCK_LLM-gated step."""
    mock = os.environ.get("MOCK_LLM", "1") != "0"
    if mock:
        return (f"For {risk_tolerance} investor {investor_id}, we recommend an allocation "
                f"across {tickers} with an expected portfolio return of {ret:.1%} and "
                f"volatility of {vol:.1%}.")
    else:
        # Optional, ungraded MOCK_LLM=0 extension point: call a real LLM here to phrase the
        # same numbers more naturally. Not implemented -- this path is never graded.
        raise NotImplementedError(
            "MOCK_LLM=0 is an optional, ungraded extension not implemented in this "
            "deterministic-baseline submission. Leave MOCK_LLM unset or =1."
        )


def run_agent(profile: dict) -> dict:
    investor_id = profile["investor_id"]
    risk_tolerance = profile["risk_tolerance"]

    # --- THINK: determine allocation from the prescribed lookup table ---
    tickers = ALLOCATION_TABLE[risk_tolerance]
    weights = [1 / 3, 1 / 3, 1 / 3]

    # --- ACT: tool call per ticker ---
    tool_data = {t: get_stock_data(t) for t in tickers}

    # --- OBSERVE -> DECIDE: compute CAPM return + portfolio variance/std, then escalate or finalize ---
    ret, var, std = portfolio_stats(tickers, tool_data, weights)
    escalated = std > ESCALATION_THRESHOLD_STD

    result = {
        "investor_id": investor_id,
        "risk_tolerance": risk_tolerance,
        "allocation": {t: round(w, 4) for t, w in zip(tickers, weights)},
        "tool_data_used": tool_data,
        "expected_portfolio_return": round(ret, 4),
        "portfolio_variance": round(var, 6),
        "portfolio_std_dev": round(std, 4),
        "status": "ESCALATED_TO_HUMAN_ADVISOR" if escalated else "FINALIZED",
    }
    if not escalated:
        result["narrative"] = narrative_sentence(investor_id, risk_tolerance, tickers, ret, std)
    else:
        result["narrative"] = (
            f"ESCALATED_TO_HUMAN_ADVISOR: computed portfolio std dev {std:.2%} exceeds the "
            f"{ESCALATION_THRESHOLD_STD:.0%} auto-finalize threshold for {risk_tolerance} "
            f"investor {investor_id}; a human advisor must review before this recommendation "
            f"is communicated."
        )
    return result


if __name__ == "__main__":
    all_results = [run_agent(p) for p in INVESTOR_PROFILES]

    for r in all_results:
        print("=" * 90)
        print(f"{r['investor_id']} ({r['risk_tolerance']}) -> {r['status']}")
        print(f"  Allocation: {r['allocation']}")
        print(f"  Expected return: {r['expected_portfolio_return']:.2%}  "
              f"Std dev: {r['portfolio_std_dev']:.2%}")
        print(f"  {r['narrative']}")

    with open("advisory_agent_run.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("\nSaved advisory_agent_run.json")

    # deterministic sanity checks, per the brief's expected pattern
    by_id = {r["investor_id"]: r for r in all_results}
    assert by_id["INV01"]["status"] == "FINALIZED", "INV01 should NOT escalate (~8.44% std)"
    assert by_id["INV02"]["status"] == "FINALIZED", "INV02 should NOT escalate (~12.57% std)"
    assert by_id["INV04"]["status"] == "FINALIZED", "INV04 should NOT escalate (~12.57% std)"
    assert by_id["INV03"]["status"] == "ESCALATED_TO_HUMAN_ADVISOR", "INV03 should escalate (~20.58% std)"
    assert by_id["INV05"]["status"] == "ESCALATED_TO_HUMAN_ADVISOR", "INV05 should escalate (~20.58% std)"
    print("All deterministic escalation checks passed.")
