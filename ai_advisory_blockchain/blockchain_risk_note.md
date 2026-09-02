# Blockchain / Crypto Risk Appendix

## 1. What a "Paytm Crypto Insights" watchlist would need to get right

Before Paytm could responsibly surface a crypto-asset watchlist to retail users, it would need
to correctly classify and disclose two structurally different risk types, because collapsing
them into one generic "crypto" bucket would actively mislead a retail audience used to
regulated, insured Paytm products.

**Stablecoin type.** Not all "stable" coins carry the same risk. A **fiat-collateralized**
stablecoin (e.g., one backed 1:1 by cash and short-dated government securities held with a
regulated custodian, with regular attestations) has a materially different, and much lower,
failure mode than an **algorithmic** stablecoin, which maintains its peg purely through an
on-chain incentive mechanism (minting/burning a paired volatile token) with no off-chain asset
backing it at all. Algorithmic stablecoins have historically de-pegged and gone to
near-zero within days once market confidence breaks, because the mechanism that is supposed to
restore the peg requires exactly the market confidence that a de-peg destroys -- a
reflexive collapse, not a gradual one. A watchlist that displays both types with an identical
"stablecoin" badge, or the same green "stable" color, would misrepresent counterparty and
mechanism risk to a user who reasonably assumes "stable" means "safe."

**DeFi / DAO governance risk.** Many crypto assets bundle in tokenomics and governance risk that
has no analogue in listed equities: token supply can be inflated by a treasury or team
allocation vote, a DAO's on-chain governance can be captured by a small number of large token
holders ("whale governance"), and smart-contract upgrade keys are sometimes held by a small
multisig with no regulatory oversight. A watchlist needs to surface token-unlock schedules,
governance-concentration metrics, and audit status alongside price, or it is presenting price
data stripped of the context that determines whether that price is trustworthy.

## 2. Crypto-as-an-asset-class recommendation for Paytm Money

Standard CAPM-style portfolio theory does not favor including an asset with no intrinsic
value or cash flow -- no dividends, no earnings, no claim on any underlying enterprise -- in an
optimal portfolio purely for its expected-return contribution, because the framework prices
assets on discounted cash flows or an equity claim, neither of which cryptocurrency offers.
Crypto's low or even negative historical correlation with equities and bonds is the strongest
argument *for* a small allocation (genuine diversification benefit), but this has to be weighed
against several offsetting factors: crypto returns are heavy-tailed and positively skewed
(most of the historical return in any major crypto asset has come from a handful of extreme
days, meaning realized outcomes for most holding periods differ sharply from the
headline average return); the space suffers from **survivorship bias** (today's crypto indices
and "top 10 by market cap" lists only include the winners -- the majority of tokens launched in
any given cycle go to zero and quietly disappear from every retrospective dataset); and retail
transaction costs (spreads, gas fees, exchange fees) are typically far higher than for listed
securities, eroding any diversification benefit for all but larger, longer-horizon positions.

**Recommendation: a maximum 2-3% allocation of total portfolio value, restricted to Aggressive
risk-tolerance investors with an investment horizon of 5+ years, and 0% for Conservative and
Moderate risk-tolerance investors.** A small (2-3%) allocation captures most of the realistic
diversification benefit an uncorrelated asset can offer a portfolio without the total position
size being large enough that a 100% wipeout (a real, non-trivial-probability outcome under the
survivorship-bias framing above) meaningfully damages the investor's overall wealth or
retirement plan. Zero allocation is the right default for Conservative and Moderate investors
specifically because their profiles (see the advisory agent's allocation table) already
represent an explicit choice to prioritize capital preservation and lower volatility -- adding
an asset class this heavy-tailed to those tiers would contradict the risk tier's own stated
purpose.

## 3. T.A.N.G. fraud framework -- two vectors most relevant to a UPI/wallet + lending + wealth platform

**Authority.** A platform combining payments, lending, and wealth advisory is an attractive
target for fraudsters impersonating "Paytm support," a "loan recovery officer," or a "SEBI/RBI
compliance officer" to pressure a user into sharing an OTP, approving a UPI collect request, or
moving funds to a "safe account" during a fabricated fraud investigation -- the platform's own
brand authority is what the scammer borrows. **Bank-side real-time defense:** device- and
behavior-based anomaly detection at the moment of UPI-PIN entry or fund transfer (new-device
flag, unusual hour, transfer to a first-time payee at an amount inconsistent with the user's
history) that triggers a real-time in-app friction step -- a cooling-off delay plus an explicit
warning screen -- rather than relying only on post-hoc chargeback processing.

**Greed.** The wealth/advisory surface is a natural target for "guaranteed high-return" investment
scams (fake IPO allotments, fraudulent "insider" crypto tips, Ponzi-style returns promised
through a cloned advisory interface) that induce a user to transfer funds outside the regulated
Paytm Money flow entirely. **Bank-side real-time defense:** real-time payee-risk scoring at the
UPI/bank-transfer layer -- cross-referencing the beneficiary account against a shared
industry fraud-reporting database (mule-account and scam-payee blocklists, of the kind RBI's
UPI ecosystem participants already contribute to) and holding or blocking transfers to
recently-flagged beneficiaries before the funds leave the user's account, rather than only
after a complaint is filed.
