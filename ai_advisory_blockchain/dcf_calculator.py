"""
Part 3D -- DCF valuation calculator for a hypothetical Paytm business line (illustrative
figures only, in INR crore -- 1 crore = INR 10,000,000).

Run: python dcf_calculator.py
"""
import json
import numpy as np

from stock_universe import RISK_FREE_RATE, MARKET_RETURN, STOCK_UNIVERSE

# ---------------------------------------------------------------- stated inputs (illustrative)
# Base-year unlevered FCFF inputs for a hypothetical "Paytm Postpaid & Merchant Lending" line
EBIT_INR_CR = 500.0
TAX_RATE = 0.25
DA_INR_CR = 40.0
CAPEX_INR_CR = 60.0
DELTA_NWC_INR_CR = 20.0

BASE_FCFF_INR_CR = EBIT_INR_CR * (1 - TAX_RATE) + DA_INR_CR - CAPEX_INR_CR - DELTA_NWC_INR_CR

# 5-year growth path fading from 18% toward a low-6% handoff, then a 5% terminal growth rate
GROWTH_PATH = np.linspace(0.18, 0.06, 5)
TERMINAL_GROWTH = 0.05

# WACC inputs: cost of equity via CAPM using PAYFIN's beta as the proxy for this fintech/lending
# business line; illustrative after-tax cost of debt and capital-structure weights
EQUITY_BETA_TICKER = "PAYFIN"
BETA = STOCK_UNIVERSE[EQUITY_BETA_TICKER]["beta"]
COST_OF_EQUITY = RISK_FREE_RATE + BETA * (MARKET_RETURN - RISK_FREE_RATE)

PRE_TAX_COST_OF_DEBT = 0.09
AFTER_TAX_COST_OF_DEBT = PRE_TAX_COST_OF_DEBT * (1 - TAX_RATE)
WEIGHT_EQUITY = 0.70
WEIGHT_DEBT = 0.30

WACC = WEIGHT_EQUITY * COST_OF_EQUITY + WEIGHT_DEBT * AFTER_TAX_COST_OF_DEBT

# self-check: terminal growth must sit >=3pp below base-case WACC
assert WACC - TERMINAL_GROWTH >= 0.03, "terminal growth must be >=3pp below base-case WACC"

# illustrative EV/EBITDA cross-check inputs
ILLUSTRATIVE_EBITDA_INR_CR = EBIT_INR_CR + DA_INR_CR
ILLUSTRATIVE_EV_EBITDA_MULTIPLE = 8.0


def project_fcff(base_fcff, growth_path):
    fcffs = []
    prev = base_fcff
    for g in growth_path:
        prev = prev * (1 + g)
        fcffs.append(prev)
    return fcffs


def dcf_enterprise_value(base_fcff, growth_path, wacc, terminal_growth):
    fcffs = project_fcff(base_fcff, growth_path)
    pv_fcffs = [fcff / (1 + wacc) ** (i + 1) for i, fcff in enumerate(fcffs)]
    terminal_value = fcffs[-1] * (1 + terminal_growth) / (wacc - terminal_growth)
    pv_terminal_value = terminal_value / (1 + wacc) ** len(fcffs)
    ev = sum(pv_fcffs) + pv_terminal_value
    return ev, fcffs, pv_fcffs, terminal_value, pv_terminal_value


if __name__ == "__main__":
    print("=== DCF inputs ===")
    print(f"Base-year FCFF = EBIT*(1-tax) + D&A - CapEx - dNWC = "
          f"{EBIT_INR_CR:.0f}*(1-{TAX_RATE}) + {DA_INR_CR:.0f} - {CAPEX_INR_CR:.0f} - "
          f"{DELTA_NWC_INR_CR:.0f} = INR {BASE_FCFF_INR_CR:.1f} cr")
    print(f"5-yr growth path: {[f'{g:.1%}' for g in GROWTH_PATH]}, terminal growth: "
          f"{TERMINAL_GROWTH:.1%}")
    print(f"Cost of equity (CAPM, beta={BETA} from {EQUITY_BETA_TICKER}): {COST_OF_EQUITY:.2%}")
    print(f"After-tax cost of debt: {AFTER_TAX_COST_OF_DEBT:.2%} "
          f"(pre-tax {PRE_TAX_COST_OF_DEBT:.1%} x (1-{TAX_RATE}))")
    print(f"Capital structure: {WEIGHT_EQUITY:.0%} equity / {WEIGHT_DEBT:.0%} debt")
    print(f"WACC = {WEIGHT_EQUITY:.0%}*{COST_OF_EQUITY:.2%} + {WEIGHT_DEBT:.0%}*"
          f"{AFTER_TAX_COST_OF_DEBT:.2%} = {WACC:.2%}")
    print(f"WACC - terminal growth (base case) = {WACC - TERMINAL_GROWTH:.2%} "
          f"(must be >= 3.00pp -- OK)")

    ev, fcffs, pv_fcffs, tv, pv_tv = dcf_enterprise_value(
        BASE_FCFF_INR_CR, GROWTH_PATH, WACC, TERMINAL_GROWTH
    )
    print("\n=== 5-year FCFF projection (INR cr) ===")
    for i, (f, pv) in enumerate(zip(fcffs, pv_fcffs), start=1):
        print(f"  Year {i}: FCFF={f:.1f}  PV={pv:.1f}")
    print(f"Terminal value (end of yr 5) = {tv:.1f}  |  PV(terminal value) = {pv_tv:.1f}")
    print(f"\nDCF-implied Enterprise Value = INR {ev:.1f} cr")

    # ---- 3x3 sensitivity table: WACC +/-1pp x terminal growth +/-1pp ----
    print("\n=== Sensitivity table (Enterprise Value, INR cr) ===")
    wacc_grid = [WACC - 0.01, WACC, WACC + 0.01]
    growth_grid = [TERMINAL_GROWTH - 0.01, TERMINAL_GROWTH, TERMINAL_GROWTH + 0.01]

    header = "WACC \\ g    " + "  ".join(f"{g:.1%}" for g in growth_grid)
    print(header)
    sensitivity = {}
    min_margin = None
    for w in wacc_grid:
        row_vals = []
        for g in growth_grid:
            margin = w - g
            min_margin = margin if min_margin is None else min(min_margin, margin)
            ev_cell, *_ = dcf_enterprise_value(BASE_FCFF_INR_CR, GROWTH_PATH, w, g)
            row_vals.append(ev_cell)
            sensitivity[f"WACC={w:.2%},g={g:.2%}"] = round(ev_cell, 1)
        print(f"{w:.2%}     " + "  ".join(f"{v:8.1f}" for v in row_vals))

    print(f"\nWorst-case (WACC - terminal growth) margin across all 9 grid cells: "
          f"{min_margin:.2%} (required >= 1.00pp)")
    assert min_margin >= 0.01, "WACC must exceed terminal growth by >=1pp in every grid cell"
    print("Sensitivity self-check passed: WACC > terminal growth in every one of the 9 cells.")

    # ---- EV/EBITDA cross-check ----
    ev_multiple_implied = ILLUSTRATIVE_EBITDA_INR_CR * ILLUSTRATIVE_EV_EBITDA_MULTIPLE
    print(f"\n=== EV/EBITDA cross-check ===")
    print(f"Illustrative EBITDA = EBIT + D&A = {EBIT_INR_CR:.0f} + {DA_INR_CR:.0f} = "
          f"{ILLUSTRATIVE_EBITDA_INR_CR:.0f} cr")
    print(f"Illustrative multiple: {ILLUSTRATIVE_EV_EBITDA_MULTIPLE:.1f}x")
    print(f"EV/EBITDA-implied Enterprise Value = INR {ev_multiple_implied:.1f} cr")
    diff_pct = (ev - ev_multiple_implied) / ev_multiple_implied
    print(f"\nDCF EV (INR {ev:.1f} cr) vs. EV/EBITDA EV (INR {ev_multiple_implied:.1f} cr): "
          f"DCF is {diff_pct:+.1%} relative to the multiple-based estimate.")
    print("The DCF value sits" + (" above" if diff_pct > 0 else " below") +
          " the multiple-based cross-check; a gap in this range is typical since the DCF "
          "embeds this specific business line's above-market near-term growth path (18% "
          "fading to 6%) directly, while the EV/EBITDA multiple is a single static snapshot "
          "that implicitly assumes this business trades like the illustrative 8x peer average "
          "regardless of its own growth trajectory. Given the DCF's explicit growth and margin "
          "assumptions are the more Paytm-specific input here, it is the primary estimate, with "
          "the multiple used only as a sanity-check bound.")

    output = {
        "base_fcff_inr_cr": round(BASE_FCFF_INR_CR, 2),
        "growth_path": [round(g, 4) for g in GROWTH_PATH],
        "terminal_growth": TERMINAL_GROWTH,
        "cost_of_equity": round(COST_OF_EQUITY, 4),
        "after_tax_cost_of_debt": round(AFTER_TAX_COST_OF_DEBT, 4),
        "wacc": round(WACC, 4),
        "fcff_projection_inr_cr": [round(f, 1) for f in fcffs],
        "terminal_value_inr_cr": round(tv, 1),
        "dcf_enterprise_value_inr_cr": round(ev, 1),
        "sensitivity_table_inr_cr": sensitivity,
        "min_wacc_minus_growth_margin": round(min_margin, 4),
        "ev_ebitda_cross_check_inr_cr": round(ev_multiple_implied, 1),
    }
    with open("dcf_run.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\nSaved dcf_run.json")
