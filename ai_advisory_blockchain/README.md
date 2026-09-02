# Part 3 -- AI-Augmented FinTech Advisory & Blockchain Risk

Paytm vertical: Money / Wealth advisory, plus a blockchain/crypto risk appendix.

**MOCK_LLM mode used for every recorded run in this README/part: `MOCK_LLM` left unset**, i.e.
the default, fully deterministic, keyless mock path (equivalent to `MOCK_LLM=1`). No network
call to any LLM provider was made anywhere in this part. The optional `MOCK_LLM=0` extension
(Groq free tier or equivalent) was not attempted and is not required for grading.

## Setup

```bash
cd ai_advisory_blockchain
pip install -r ../requirements.txt   # numpy is the only external dependency here
```

## Run, in order (independent scripts, any order works)

```bash
python advisory_agent.py       # writes advisory_agent_run.json
python extract_disclosure.py   # writes extract_disclosure_run.json
python debate.py               # writes debate_run.json
python dcf_calculator.py       # writes dcf_run.json
```

`blockchain_risk_note.md` is a static write-up (869 words) and does not need to be run.

## Recorded example run transcripts (MOCK_LLM default / mock path)

### Advisory agent (Task A) -- all 5 investor profiles

| Investor | Risk tolerance | Allocation | Expected return | Std dev | Status |
|---|---|---|---|---|---|
| INV01 | Conservative | PAYBOND/PAYGOLD/PAYRETAIL (1/3 each) | 9.20% | 8.44% | FINALIZED |
| INV02 | Moderate | PAYRETAIL/PAYINFRA/PAYGOLD (1/3 each) | 11.30% | 12.57% | FINALIZED |
| INV03 | Aggressive | PAYTECH/PAYFIN/PAYINFRA (1/3 each) | 15.00% | 20.58% | ESCALATED_TO_HUMAN_ADVISOR |
| INV04 | Moderate | PAYRETAIL/PAYINFRA/PAYGOLD (1/3 each) | 11.30% | 12.57% | FINALIZED |
| INV05 | Aggressive | PAYTECH/PAYFIN/PAYINFRA (1/3 each) | 15.00% | 20.58% | ESCALATED_TO_HUMAN_ADVISOR |

Matches the brief's expected deterministic pattern exactly (Conservative ~8.44%, Moderate
~12.57% -- neither escalates; Aggressive ~20.58% -- both escalate). Full JSON in
`advisory_agent_run.json`.

### Disclosure extraction (Task B) -- all 6 snippets

| doc | risk_flags | hedging_detected | sentiment |
|---|---|---|---|
| doc_01 | [] | True | cautious |
| doc_02 | [litigation] | False | neutral |
| doc_03 | [customer_concentration] | False | neutral |
| doc_04 | [] | True | cautious |
| doc_05 | [] | False | confident |
| doc_06 | [regulatory] | False | neutral |

doc_02 correctly flags litigation, doc_05 (board approval) is correctly "confident", and
doc_01/doc_04 correctly trigger `hedging_detected`. Full JSON in `extract_disclosure_run.json`.

### Debate demo (Task C) -- PAYTECH (beta 1.55, analyst_expected_return 19%, std_dev 34%)

- **Bull:** cites the 19.0% expected return against the 1.55 beta as risk-adjusted upside.
- **Bear:** cites the 34% standard deviation and 1.55 beta as drawdown risk.
- **Synthesizer:** concludes PAYTECH belongs only in Aggressive-tier allocations.

Full text in `debate_run.json`.

### DCF calculator (Task D)

- Base FCFF = INR 335.0 cr (EBIT 500 x (1-25% tax) + D&A 40 - CapEx 60 - dNWC 20)
- Cost of equity (CAPM, PAYFIN beta 1.35) = 15.10%; after-tax cost of debt = 6.75%;
  70/30 equity/debt weights -> **WACC = 12.60%**
- 5-yr growth path 18% -> 6%, terminal growth 5% (7.60pp buffer below base-case WACC)
- **DCF-implied Enterprise Value = INR 6,230.8 cr**

Sensitivity table (Enterprise Value, INR cr; rows = WACC, cols = terminal growth):

| WACC \ g | 4.0% | 5.0% | 6.0% |
|---|---|---|---|
| 11.60% | 6,437.7 | 7,195.0 | 8,222.9 |
| 12.60% | 5,670.1 | 6,230.8 | 6,961.5 |
| 13.60% | 5,063.0 | 5,491.4 | 6,032.6 |

Worst-case WACC-minus-growth margin across all 9 cells: 5.60pp (>= the required 1.00pp).

EV/EBITDA cross-check: illustrative EBITDA INR 540 cr x 8.0x multiple = INR 4,320.0 cr. The
DCF estimate (INR 6,230.8 cr) sits +44.2% above the multiple-based cross-check; see
`dcf_calculator.py`'s printed commentary for the full 2-3 sentence comparison. Full JSON in
`dcf_run.json`.

## Design decisions

- **Agentic pattern (Task A):** `advisory_agent.py` separates Think (allocation lookup) / Act
  (`get_stock_data()` tool call) / Observe-decide (CAPM + variance + escalation) into distinct
  functions/stages. CAPM uses **only** `beta`, never `analyst_expected_return`, per the brief.
  Pairwise correlation rho=0.3 is applied to every pair in the prescribed 3-ticker allocation.
- **Escalation:** hard-coded 20% portfolio-std-dev threshold; deterministic given the fixed
  allocation table, so the same 3 tiers always produce the same escalate/finalize outcome
  regardless of `investment_amount_inr` or `horizon_years` (those fields are carried in the
  investor profile but do not enter the CAPM/variance calculation, per the brief's prescribed
  methodology).
- **MOCK_LLM gating:** in every script, only the single final narrative/argument-generation step
  is gated by `MOCK_LLM`; all numeric computation (CAPM, variance, keyword extraction, DCF math)
  is identical regardless of the flag. The `MOCK_LLM=0` branch raises `NotImplementedError` with
  an explicit message rather than silently doing nothing, since that path is an optional,
  ungraded extension not implemented in this submission.
- **DCF (Task D):** beta sourced from `PAYFIN` as the closest proxy in `STOCK_UNIVERSE` for a
  fintech lending business line; all other DCF inputs (EBIT, D&A, CapEx, dNWC, cost of debt,
  capital structure, EV/EBITDA multiple) are stated, illustrative assumptions, not real Paytm
  financials.
