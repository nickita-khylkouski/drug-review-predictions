"""Arm-blind audit of trial hits from trials_backtest.py (raw matching passes comparator arms and stray words).
For every pair with no matching trial before the cutoff and >= 1 after (loose rule), the 5 earliest matching trials
after the cutoff go to gpt-6.1-sol in shuffled order with drug + benefit only. A pair counts if any trial passes.
-> agents/trials_audit.json, prints signal vs controls.  uv run python sig/agents/trials_audit.py"""
import json, random, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd
from openai import OpenAI
from scipy.stats import fisher_exact
H = Path(__file__).parent; sys.path.insert(0, str(H.parent)); import ledger
src = (H / "trials_backtest.py").read_text()
import numpy as np; D = H.parent / "data"
exec(src[src.index("EFF = "): src.index("rows = []")].replace("O = pd.read_parquet", "_O = pd.read_parquet"))
T = pd.read_parquet(H / "trials_backtest.parquet")
X = T[T.tb_l == 0].copy()


def after(d, e, Y):
    ig, ts = ingr(d), terms(e); st = cache.get(ig[0] + "|" + "|".join(ts)) or []
    rx = re.compile("|".join(re.escape(t) for t in ts)); out = []
    for s in st:
        if not s["start"].isdigit() or int(s["start"]) < Y or not all(any(i in x.lower() for x in s["intr"]) for i in ig): continue
        if rx.search(" ".join(s["cond"] + [s["title"]] + s["prim"] + s["sec"]).lower()): out.append(s)
    return sorted(out, key=lambda s: s["start"])[:5]


X["tr"] = [after(d, e, int(y)) if a > 0 else [] for d, e, y, a in zip(X.drug, X.effect, X.cutoff, X.ta_l)]
OUT = H / "trials_audit.json"; aud = json.loads(OUT.read_text()) if OUT.exists() else {}
todo = list({f"{d}|{e}|{s['id']}": (d, e, s) for d, e, tr in zip(X.drug, X.effect, X.tr) for s in tr}.items())
todo = [t for t in todo if t[0] not in aud]; random.seed(0); random.shuffle(todo)
print(len(X), "pairs,", int((X.tr.str.len() > 0).sum()), "with candidate trials,", len(todo), "trials to audit", flush=True)
key = dict(l.strip().split("=", 1) for l in open(H.parent.parent / ".env") if "=" in l)["OPENAI_API_KEY"]
ai = OpenAI(api_key=key, timeout=300, max_retries=2); cost = [0.0]


def go(t):
    k, (d, e, s) = t
    msg = (f"Clinical trial {s['id']} (start {s['start']})\nTitle: {s['title']}\nConditions: {'; '.join(s['cond'])}\n"
           f"Interventions: {'; '.join(s['intr'])}\nPrimary outcomes: {'; '.join(s['prim'])[:1500]}\nSecondary outcomes: {'; '.join(s['sec'])[:1500]}\n\n"
           f"Drug: {d}\nBenefit: {e.replace('other:', '').strip()}\n\n"
           "Answer yes only if ALL hold:\n1. The drug (or a product containing it) is an experimental treatment in the trial, not only a comparator, background therapy or challenge agent.\n"
           "2. The trial tests whether the drug improves that benefit: it is the condition treated or one of the measured outcomes.\n"
           "3. The benefit is meant in the same sense (e.g. 'edema' = fluid swelling).\n"
           'JSON only: {"yes": true/false, "why": "<max 12 words>"}')
    r = ai.chat.completions.create(model="gpt-6.1-sol", response_format={"type": "json_object"}, messages=[{"role": "user", "content": msg}])
    cost[0] += r.usage.prompt_tokens * 5e-6 + r.usage.completion_tokens * 30e-6
    return k, json.loads(r.choices[0].message.content)


with ThreadPoolExecutor(8) as ex:
    for k, v in ex.map(go, todo): aud[k] = v
OUT.write_text(json.dumps(aud, indent=1))
if cost[0]: ledger.add("arm-blind audit of trial hits", cost[0], model="gpt-6.1-sol")
X["ok"] = [any(aud.get(f"{d}|{e}|{s['id']}", {}).get("yes") for s in tr) for d, e, tr in zip(X.drug, X.effect, X.tr)]
X["first_ok"] = [min([int(s["start"]) for s in tr if aud.get(f"{d}|{e}|{s['id']}", {}).get("yes")] or [0]) for d, e, tr in zip(X.drug, X.effect, X.tr)]
for name, ctl in (("same-effect controls", X.arm == "control_drug"), ("same-drug controls", X.arm == "control_effect"), ("all controls", X.arm != "signal")):
    s, c = X[X.arm == "signal"], X[ctl]; a, b = int(s.ok.sum()), int(c.ok.sum())
    orr, p = fisher_exact([[a, len(s) - a], [b, len(c) - b]])
    print(f"audited | {name:21s} signal {a}/{len(s)} = {a / len(s):.1%}  control {b}/{len(c)} = {b / len(c):.1%}  OR {orr:.2f} p {p:.2g}")
print("pass rate of candidate pairs:", {arm: f"{int(g.ok.sum())}/{int((g.tr.str.len() > 0).sum())}" for arm, g in X.groupby(X.arm == "signal")})
for r in X[X.ok].sort_values("arm", ascending=False).itertuples():
    tr = [s for s in r.tr if aud.get(f"{r.drug}|{r.effect}|{s['id']}", {}).get("yes")][0]
    print(f"  {r.arm[:9]:9s} {r.cutoff} {r.drug[:24]:24s} {r.effect[:22]:22s} {tr['start']} {tr['id']} {tr['title'][:70]}")
X.drop(columns=["tr"]).to_parquet(H / "trials_audited.parquet")
print(f"cost ${cost[0]:.2f}, total ${ledger.total():.2f}")
