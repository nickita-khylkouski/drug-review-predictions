"""Freeze today's review signals + matched controls for a forward test -> sig/data/predictions_2026-10-26.csv (+ .sha256)
Same rules as the backtest (outcomes.py): every v2 pair with lb >= 1.5 on all reviews (signals_2027_v2.parquet),
and for each one a same-drug/other-effect and a same-effect/other-drug control with k <= 1. Seed fixed.
How it gets scored later is in PREDICTIONS.md. Nothing here calls a paid API.
uv run python sig/freeze.py
"""
import hashlib, json
from pathlib import Path
import numpy as np, pandas as pd

D = Path(__file__).parent / "data"; DAY = "2026-10-26"
EFF = json.loads((D / "effects.json").read_text())["effects"]
P = pd.read_parquet(D / "signals_2027_v2.parquet")
V = pd.read_parquet(D / "signals_2027_v2_verb.parquet").set_index(["drug", "effect"]).lb.rename("lb_verb")
sig = P[P.lb >= 1.5].copy(); sig["arm"] = "signal"
rng = np.random.default_rng(20261026)
allk = P.set_index(["drug", "effect"]).k.to_dict()
phrase = set()
for l in (D / "benefits.jsonl").read_text().splitlines():
    for b in json.loads(l)["benefits"]:
        if isinstance(b, dict) and b.get("effect"): phrase.add(str(b["effect"]).strip().lower())
eff_pool = [e for e in EFF if e in phrase]
drug_pool = P.drug.value_counts().index.tolist()
ctl = []
for d, e in zip(sig.drug, sig.effect):
    for _ in range(20):
        e2 = rng.choice(eff_pool)
        if allk.get((d, e2), 0) <= 1 and e2 != e: ctl.append((d, e2, "control_effect")); break
    for _ in range(20):
        d2 = rng.choice(drug_pool)
        if allk.get((d2, e), 0) <= 1 and d2 != d: ctl.append((d2, e, "control_drug")); break
C = pd.DataFrame(ctl, columns=["drug", "effect", "arm"])
F = pd.concat([sig, C]).drop_duplicates(["drug", "effect"]).reset_index(drop=True)
F = F.join(V, on=["drug", "effect"])
F["k"] = [allk.get((d, e), 0) for d, e in zip(F.drug, F.effect)]
F["first"] = F["first"].astype(str).str[:10].replace({"NaT": "", "nan": "", "None": ""})
cols = ["arm", "drug", "effect", "k", "n", "E", "lb", "lb_verb", "first"]
F["n"] = F["n"].astype("Int64")
F = F[cols].round({"E": 3, "lb": 3, "lb_verb": 3}).sort_values(["arm", "lb", "drug", "effect"], ascending=[False, False, True, True])
out = D / f"predictions_{DAY}.csv"
F.to_csv(out, index=False, lineterminator="\n")
h = hashlib.sha256(out.read_bytes()).hexdigest()
(D / f"predictions_{DAY}.csv.sha256").write_text(f"{h}  predictions_{DAY}.csv\n")
print(F.arm.value_counts().to_string()); print("sha256", h)
