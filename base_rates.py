"""Base rates and power behind PREDICTIONS_2026-10-28.md.
1. From the backtest (strict_v2.parquet, strict arm-blind audit): share of open signals and controls whose first
   audited paper came within 2, 3, 5, 8 years of the cutoff.
2. Power of the frozen one-sided Fisher test under three futures.
uv run python sig/base_rates.py
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import fisher_exact

D = Path(__file__).parent / "data"
O = pd.read_parquet(D / "strict_v2.parquet")
A = {json.loads(l)["pmid"]: json.loads(l) for l in (D / "abstracts.jsonl").read_text().splitlines()}
aud = json.loads((D / "strict_audit.json").read_text())


def first_year(r):
    ys = [int(A[p]["year"]) for p in json.loads(r.ids_after) if p in A and A[p]["year"].isdigit()
          and aud.get(f"{r.drug}|{r.effect}|{p}", {}).get("yes")]
    return min(ys) if ys else None


O["y"] = O.apply(first_year, axis=1)
for name, g in (("signals", O[O.arm == "signal"]), ("controls", O[O.arm != "signal"])):
    lag = g.y - g.cutoff
    print(f"{name:9s} n={len(g):5d}", "  ".join(f"<= {k}y {((lag <= k) & g.strict).mean():.1%}" for k in (2, 3, 5, 8)),
          f"  ever {g.strict.mean():.1%}")

rng = np.random.default_rng(1)
for ns, nc in ((100, 700), (200, 1000), (300, 1300)):
    for ps, pc in ((.106, .027), (.07, .03), (.05, .03)):
        w = np.mean([fisher_exact([[a := rng.binomial(ns, ps), ns - a], [b := rng.binomial(nc, pc), nc - b]],
                                  alternative="greater")[1] < .05 for _ in range(2000)])
        print(f"power  signals {ns} at {ps:.1%}, controls {nc} at {pc:.1%}: {w:.0%}")
