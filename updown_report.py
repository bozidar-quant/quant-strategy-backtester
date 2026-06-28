#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
score_diagnostic.py - Nosi li Score informaciju?
================================================

Pitanje: raste li win rate s konviktnoscu signala (|Score|)?
  - Ako DA (monotono, high-conviction iznad breakevena)  -> signal ima edge,
    vrijedi ici na korak #2 (TP/SL backtest).
  - Ako NE (ravno / nasumicno)                            -> signal nema edge,
    ni spot ga nece spasiti -> odgovor je "prihvati nalaz".

Score: znak = smjer (BUY +, SELL -), |Score| = konviktnost (prag 6).
Gleda samo WIN/LOSS (INVALID/REFUND se ignoriraju).

Pokretanje:
    python score_diagnostic.py
    python score_diagnostic.py --data-dir "C:\\BreakoutAnalysis" --since "2026-06-07 18:00"
"""

import os
import argparse
from datetime import datetime
import numpy as np
import pandas as pd

DEFAULT_DATA_DIR = r"C:\BreakoutAnalysis"
FILES = ["UpDownScanner_outcomes.csv", "UpDownScanner_M15_outcomes.csv"]
PAYOUT = 0.90
BREAKEVEN = 1.0 / (1.0 + PAYOUT)   # 0.5263

COLS = {
    "pair":      ["pair", "instrument", "symbol"],
    "direction": ["direction", "side", "signal", "dir"],
    "outcome":   ["outcome", "result", "status"],
    "score":     ["score", "totalscore", "matrixscore"],
    "time":      ["signaltime", "time", "timestamp", "datetime", "entrytime"],
}

def _norm(s):
    return str(s).strip().lower().replace(" ", "").replace("_", "").replace("-", "")

def resolve(df, key):
    nm = {_norm(c): c for c in df.columns}
    for cand in COLS[key]:
        if _norm(cand) in nm:
            return nm[_norm(cand)]
    return None

def wilson(w, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = w / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = (z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (max(0.0, c - m), min(1.0, c + m))

def norm_out(v):
    s = str(v).strip().upper()
    if s.startswith("WIN") or s in ("W", "1"):
        return 1
    if s.startswith("LOS") or s in ("L", "0"):
        return 0
    return None

def load_all(data_dir, since, until):
    frames = []
    for fn in FILES:
        p = os.path.join(data_dir, fn)
        if not os.path.isfile(p):
            continue
        try:
            d = pd.read_csv(p)
        except Exception:
            continue
        c_out, c_sc = resolve(d, "outcome"), resolve(d, "score")
        if c_out is None or c_sc is None:
            print(f"  ! {fn}: ne nalazim outcome/score kolonu, preskačem")
            continue
        sub = pd.DataFrame()
        sub["win"] = d[c_out].map(norm_out)
        sub["score"] = pd.to_numeric(d[c_sc], errors="coerce")
        c_dir = resolve(d, "direction")
        sub["dir"] = d[c_dir].astype(str).str.upper() if c_dir else "?"
        c_t = resolve(d, "time")
        sub["t"] = pd.to_datetime(d[c_t], errors="coerce") if c_t else pd.NaT
        sub["src"] = "H1" if "M15" not in fn else "M15"
        frames.append(sub)
    if not frames:
        return pd.DataFrame()
    a = pd.concat(frames, ignore_index=True)
    a = a[a["win"].notna() & a["score"].notna()].copy()
    a["win"] = a["win"].astype(int)
    a["aScore"] = a["score"].abs()
    if since is not None:
        a = a[a["t"] >= since]
    if until is not None:
        a = a[a["t"] <= until]
    return a

def line(label, w, n):
    if n == 0:
        print(f"  {label:<14} n=0")
        return
    wr = w / n
    lo, hi = wilson(w, n)
    flag = "  >= BE" if lo >= BREAKEVEN else ("  ~BE" if wr >= BREAKEVEN else "")
    bar = "#" * int(round(wr * 20))
    print(f"  {label:<14} n={n:<4} WR={wr*100:5.1f}%  CI[{lo*100:4.1f}-{hi*100:4.1f}]  {bar}{flag}")

def block(title, df):
    print("\n" + title)
    print("  " + "-" * 60)
    for s in sorted(df["aScore"].unique()):
        sub = df[df["aScore"] == s]
        line(f"|Score|={int(s)}", int(sub["win"].sum()), len(sub))
    print("  " + "." * 60)
    lo_df = df[df["aScore"] <= 7]; hi_df = df[df["aScore"] >= 8]
    line("low (6-7)", int(lo_df["win"].sum()), len(lo_df))
    line("high (8-10)", int(hi_df["win"].sum()), len(hi_df))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    ap.add_argument("--since", default=None)
    ap.add_argument("--until", default=None)
    args = ap.parse_args()
    since = pd.to_datetime(args.since) if args.since else None
    until = pd.to_datetime(args.until) if args.until else None

    a = load_all(args.data_dir, since, until)
    if len(a) == 0:
        print("Nema podataka (provjeri --data-dir i nazive kolona).")
        return

    print("=" * 64)
    print(f"SCORE -> WR DIJAGNOSTIKA   ({len(a)} decisive ishoda)")
    print(f"Breakeven WR = {BREAKEVEN*100:.1f}%   (90% payout)")
    if since or until:
        print(f"Prozor: {since or '...'} -> {until or 'sada'}")
    print("=" * 64)

    block("SVE (BUY + SELL zajedno, po |Score|)", a)
    block("SAMO BUY (Score > 0)", a[a["score"] > 0])
    block("SAMO SELL (Score < 0)", a[a["score"] < 0])

    # korelacija konviktnost <-> pobjeda
    print("\n" + "=" * 64)
    if a["aScore"].nunique() > 1:
        r = np.corrcoef(a["aScore"], a["win"])[0, 1]
        print(f"Point-biserial r(|Score|, WIN) = {r:+.3f}")
        if r > 0.10:
            print("  -> POZITIVNA veza: jaci signal pobjeduje cesce. Vrijedi ici na #2 (TP/SL backtest).")
        elif r < -0.10:
            print("  -> NEGATIVNA veza: jaci signal gubi cesce (loš znak).")
        else:
            print("  -> Veze gotovo NEMA (r~0): Score ne nosi informaciju o ishodu.")
            print("     Ako ostane ovako na punom uzorku -> signal nema edge, ni spot ga ne spasava.")
    else:
        print("Samo jedna |Score| vrijednost u uzorku - ne mogu mjeriti vezu.")

    # monotonija
    wrs = []
    for s in sorted(a["aScore"].unique()):
        sub = a[a["aScore"] == s]
        if len(sub) >= 5:
            wrs.append((int(s), sub["win"].mean()))
    if len(wrs) >= 3:
        vals = [w for _, w in wrs]
        mono = all(vals[i] <= vals[i + 1] for i in range(len(vals) - 1))
        print(f"Monotoni rast WR sa |Score| (buckets n>=5): {'DA' if mono else 'NE'}  {[ (s, round(w*100)) for s,w in wrs ]}")
    print("=" * 64)
    print("NAPOMENA: mali n po bucketu = širok CI. Definitivni run napravi na punom"
          "\n2-tjednom uzorku (s --since od deploya za čiste podatke).")

if __name__ == "__main__":
    main()