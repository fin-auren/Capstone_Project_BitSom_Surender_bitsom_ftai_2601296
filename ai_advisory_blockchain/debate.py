"""
Part 3C -- 3-agent (bull / bear / synthesizer) debate demo for one STOCK_UNIVERSE ticker.

Mock mode (MOCK_LLM unset or =1, the graded baseline): each agent's argument is built from a
template referencing the ticker's actual numeric values -- no LLM call. MOCK_LLM=0 is an
optional, ungraded extension (would call an LLM for richer arguments) -- not implemented.

Run: python debate.py
"""
import os
import json

from stock_universe import STOCK_UNIVERSE

TICKER = "PAYTECH"  # chosen ticker for this debate demo


def bull_argument(ticker: str, data: dict) -> str:
    r, b = data["analyst_expected_return"], data["beta"]
    return (f"With an analyst-expected return of {r:.1%} against a beta of {b:.2f}, {ticker} "
            f"offers attractive risk-adjusted upside for growth-oriented Paytm Money investors "
            f"-- the higher beta simply means it captures more of the market's upside in a "
            f"rising-rate, rising-market environment.")


def bear_argument(ticker: str, data: dict) -> str:
    s, b = data["std_dev"], data["beta"]
    return (f"{ticker}'s standard deviation of {s:.0%} and beta of {b:.2f} mean it will fall "
            f"harder than the market in any drawdown -- a {s:.0%} annualized volatility implies "
            f"large single-year swings, which is a real risk for any investor with a shorter "
            f"horizon or lower loss tolerance than 'Aggressive'.")


def synthesizer_summary(ticker: str, data: dict, bull: str, bear: str) -> str:
    return (f"{ticker} pairs a high expected return ({data['analyst_expected_return']:.1%}) "
            f"with high volatility ({data['std_dev']:.0%}) and a beta of {data['beta']:.2f} well "
            f"above 1 -- the bull case is real for investors who can tolerate the swings the "
            f"bear case describes, so {ticker} belongs only in allocations sized for an "
            f"Aggressive risk tier, not as a core holding for Conservative or Moderate "
            f"investors.")


def run_debate(ticker: str) -> dict:
    mock = os.environ.get("MOCK_LLM", "1") != "0"
    if not mock:
        raise NotImplementedError(
            "MOCK_LLM=0 is an optional, ungraded extension not implemented in this "
            "deterministic-baseline submission. Leave MOCK_LLM unset or =1."
        )
    data = STOCK_UNIVERSE[ticker]
    bull = bull_argument(ticker, data)
    bear = bear_argument(ticker, data)
    synthesis = synthesizer_summary(ticker, data, bull, bear)
    return {"ticker": ticker, "stock_data": data, "bull_agent": bull, "bear_agent": bear,
            "synthesizer": synthesis}


if __name__ == "__main__":
    result = run_debate(TICKER)
    print(f"=== Debate demo: {result['ticker']} ===")
    print(f"Stock data: {result['stock_data']}\n")
    print(f"BULL: {result['bull_agent']}\n")
    print(f"BEAR: {result['bear_agent']}\n")
    print(f"SYNTHESIZER: {result['synthesizer']}")

    with open("debate_run.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nSaved debate_run.json")
