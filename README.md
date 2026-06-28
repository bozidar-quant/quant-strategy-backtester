# quant-strategy-backtester

End-to-end signal generation and backtesting pipeline for FX binary options, with strict out-of-sample validation.

## Case Study

[→ Full case study](CASE_STUDY.md) — methodology, results, and why a negative finding is the honest deliverable.

## What this is

A complete system for generating and testing rule-based entry signals on FX pairs (Dukascopy binary options — Touch and Up/Down). Built to answer one question honestly: does this strategy have an edge out-of-sample?

**Result: no.** That answer is documented here rather than hidden behind a cherry-picked equity curve.

## What's inside

- **Signal engine** (Java / JForex `IStrategy`) — breakout-based entry signals across 18 FX pairs on M15 and H1
- **Custom indicators** (Java / JForex) — OscillatorMatrix, support/resistance levels (PDH/PDL/PDC), SMC overlay, Pine → Java trendline-break oscillator port
- **Backtesting pipeline** (`forex_backtest.py`) — four strategy families with explicit train/test split and out-of-sample test set
- **Diagnostics & reporting** — win rate by pair / strike bucket / time-of-day, MAE/MFE excursion analysis, PDF report output

## Methodology

- Train/test split: parameters chosen on training data, judged only on unseen test data
- No cherry-picking from the parameter grid — full ranges reported, not just the lucky corner
- Correct breakeven math: at 90% payout, the bar is 52.6% win rate, not 50%

## Results

| System | Out-of-sample win rate | Breakeven needed | Verdict |
|---|---|---|---|
| Touch binaries | ~23–25% | 52.6% | Structurally non-viable |
| Up/Down binaries | ~48.9% | 52.6% | Below the line |

None of the four strategy families showed an out-of-sample edge.

## Tech stack

Java (JForex / Dukascopy API) · Python (pandas, matplotlib) · Linux VPS · Git

## License

MIT License — see [LICENSE](LICENSE).  
LuxAlgo-derived indicator (`OscillatorMatrix`) is additionally licensed under CC BY-NC-SA 4.0.

---

*[bozidar-quant](https://github.com/bozidar-quant)*
