# Case Study — Quant Strategy Backtester

> I built an end-to-end signal-generation and backtesting pipeline for FX binary
> options, then used out-of-sample validation to prove the signals had no real
> edge — and documented that result instead of hiding it behind a cherry-picked
> equity curve.

---

## TL;DR

- Designed and built a full signal + backtesting system for Dukascopy FX binary
  options (Touch and Up/Down), from data collection to PDF reporting.
- Tested four strategy families with strict **train/test separation** and
  **out-of-sample validation**.
- **Result:** no configuration beat the payout-implied breakeven win rate
  out-of-sample. I reported that honestly rather than overfit to a good-looking
  in-sample number.
- **What it demonstrates:** data discipline, correct experimental design, and the
  integrity to kill a project when the data doesn't support it.

---

## The objective

Determine whether a rule-based technical signal could profitably trade Dukascopy
binary options on FX — and, just as importantly, build the measurement
infrastructure rigorous enough to *trust the answer either way*.

The payout structure sets a hard bar: at a 90% payout, you need a win rate above
**52.6%** just to break even (1 ÷ 1.9). Any system has to clear that line
*out-of-sample*, not in a backtest you tuned to look good.

---

## What I built

**Signal engine (Java / JForex `IStrategy`)**
Breakout-based entry signals across 18 FX pairs on M15 and H1 — `BreakoutScanner`,
`BreakoutScannerM15`, and `UpDownScanner`, with expiry-based outcome evaluation
(close vs. entry at expiry, spread-adjusted).

**Custom indicators (Java / JForex)**
`OscillatorMatrix` (LuxAlgo-style multi-timeframe oscillator), support/resistance
level mapping (PDH/PDL/PDC etc.), an SMC overlay, and a faithful Pine → Java port
of a trendline-break oscillator with attribution retained.

**Backtesting pipeline (Python)**
`forex_backtest.py` — four strategy families evaluated with an explicit
train/test split and an out-of-sample test set.

**Diagnostics & reporting (Python)**
`score_diagnostic.py` for signal-quality analysis and a PDF report generator
covering win rate by pair / strike bucket / time-of-day and MAE/MFE excursion
analysis.

**Infrastructure**
Contabo VPS (Ubuntu 24.04) running the platform 24/7, with push notifications for
live signal alerts. File transfer and remote ops over SSH/SCP.

---

## Methodology — the part that actually matters

The hard part of quant work isn't writing the strategy; it's not fooling yourself.
Concretely:

- **Train/test split + out-of-sample.** Parameters were chosen on training data and
  judged only on unseen test data. The number that counts is the one the model
  never saw.
- **No cherry-picking from the parameter grid.** It's trivial to pick the single
  best-looking cell from a table of thresholds and call it a strategy — that's
  overfitting. I evaluated the *full* parameter ranges and reported the whole
  picture, not the lucky corner.
- **Correct breakeven math built in.** Every result was measured against the
  52.6% payout-implied bar, not against a vanity 50%.

---

## Results

| System | Out-of-sample win rate | Breakeven needed | Verdict |
|---|---|---|---|
| Touch binaries | ~23–25% | 52.6% | Structurally non-viable |
| Up/Down binaries | ~48.9% (across score thresholds) | 52.6% | Still below the line |

The pivot from Touch to Up/Down deliberately *lowered the bar* — Up/Down only needs
price to be on the correct side at expiry, not to reach a distant barrier. Win rate
improved substantially, but still landed below breakeven, and stayed there across
every score threshold and parameter range tested. None of the four strategy
families showed an out-of-sample edge.

---

## The finding

Lagging oscillator and breakout signals cannot reliably predict short-horizon FX
moves. Any apparent in-sample edge disappeared out-of-sample — consistent with the
broader reality that simple retail technical edges get arbitraged away once enough
participants find them.

---

## Why this is the portfolio piece, not an embarrassment

Most "trading bot" repositories open with a cherry-picked equity curve sloping up
and to the right. This one opens with a negative result that survived honest
validation.

That is exactly the signal a serious client or employer is looking for: someone who
builds the measurement correctly, runs the experiment without rigging it, and
trusts the data over the narrative. A working tool is not the same as an edge — and
knowing the difference (and being willing to say so) is the actual skill.

---

## Tech stack

Java (JForex / Dukascopy API) · Python (pandas, matplotlib) · Linux VPS
administration · Git

---

*Author: [bozidar-quant](https://github.com/bozidar-quant)*
