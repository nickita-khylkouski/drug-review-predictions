"""Strict, arm-blind re-audit of backtest hits with few prior co-mentions (n_before <= 9, unique pairs, first cutoff).
The judge and the first audit pass tangential papers (wrong drug, opposite effect, misuse case). This asks a narrower question
about the 3 EARLIEST judged papers after the cutoff -> sig/data/strict_audit.json, then signal vs control with strict hits.
SUFFIX=_v2 uv run python sig/strict_audit.py
"""
import json, os, random, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd
from openai import OpenAI
from scipy.stats import fisher_exact
sys.path.insert(0, str(Path(__file__).parent))
import ledger

D = Path(__file__).parent / "data"; SUF = os.environ.get("SUFFIX", "")
key = dict(l.strip().split("=", 1) for l in open(D.parent.parent / ".env") if "=" in l)["OPENAI_API_KEY"]
ai = OpenAI(api_key=key, timeout=300, max_retries=2)
A = {json.loads(l)["pmid"]: json.loads(l) for l in (D / "abstracts.jsonl").read_text().splitlines()}
J = {}
for l in (D / "paper_judge.jsonl").read_text().splitlines():
    j = json.loads(l); J[(j["pair"], j["pmid"])] = j["p"]
O = pd.read_parquet(D / f"outcomes_all{SUF}.parquet")
O = O[O.new & (O.n_before.fillna(0) <= 9)].sort_values("cutoff").drop_duplicates(["arm", "drug", "effect"])


def earliest(d, e, ids):
    ps = [p for p in json.loads(ids) if (J.get((f"{d}|{e}", p)) or 0) > .9 and p in A and A[p]["year"].isdigit()]
    return sorted(ps, key=lambda p: int(A[p]["year"]))[:3]


O["ps"] = [earliest(d, e, s) for d, e, s in zip(O.drug, O.effect, O.ids_after)]
H = O[O.ps.str.len() > 0]
OUT = D / "strict_audit.json"
aud = json.loads(OUT.read_text()) if OUT.exists() else {}
todo = [(d, e, p) for d, e, ps in zip(H.drug, H.effect, H.ps) for p in ps if f"{d}|{e}|{p}" not in aud]
random.seed(0); random.shuffle(todo)                       # arm order never reaches the model
print(f"{len(H)} hit pairs ({(H.arm == 'signal').sum()} signal), {len(todo)} papers to audit", flush=True)
cost = [0.0]


def go(t):
    d, e, p = t
    msg = (f"Paper:\nTitle: {A[p]['title']}\nAbstract: {A[p]['abstract']}\n\n"
           f"Drug: {d}\nBenefit: {e.replace('other:', '').strip()}\n\n"
           "Answer yes only if ALL hold:\n"
           "1. The drug itself (or a product containing it) is one of the treatments the paper studies or reports on.\n"
           "2. The paper reports the drug IMPROVING that benefit (or tests it as a treatment for it), in people or animals.\n"
           "3. The benefit is meant in the same sense (e.g. 'edema' = fluid swelling, not brain inflammation).\n"
           "Say no for: a different drug, the opposite effect, misuse or addiction to the drug, the drug only listed in a review "
           "of many treatments without a finding, or the benefit only as an indirect result of treating something else.\n"
           'JSON only: {"yes": true/false, "why": "<max 12 words>"}')
    r = ai.chat.completions.create(model="gpt-6.1-sol", response_format={"type": "json_object"}, messages=[{"role": "user", "content": msg}])
    cost[0] += r.usage.prompt_tokens * 5e-6 + r.usage.completion_tokens * 30e-6
    return f"{d}|{e}|{p}", json.loads(r.choices[0].message.content)


with ThreadPoolExecutor(12) as ex:
    for k, v in ex.map(go, todo): aud[k] = v
OUT.write_text(json.dumps(aud, indent=1))
if cost[0]: ledger.add("strict arm-blind audit of low co-mention hits", cost[0], model="gpt-6.1-sol")
ok = lambda d, e, ps: any(aud.get(f"{d}|{e}|{p}", {}).get("yes") for p in ps)
O["strict"] = [bool(ps) and ok(d, e, ps) for d, e, ps in zip(O.drug, O.effect, O.ps)]
s, c = O[O.arm == "signal"], O[O.arm != "signal"]
for col in ("hit_ok", "strict"):
    a, b = int(s[col].sum()), int(c[col].sum())
    orr, p = fisher_exact([[a, len(s) - a], [b, len(c) - b]])
    print(f"{col:7s} signal {a}/{len(s)} = {a / len(s):.1%}  control {b}/{len(c)} = {b / len(c):.1%}  OR {orr:.2f}  p {p:.2g}")
print("share of hit_ok pairs that pass strict:", {arm: round(g[g.hit_ok].strict.mean(), 2) for arm, g in O.groupby(O.arm == "signal")})
yr = lambda d, e, ps: min(int(A[p]["year"]) for p in ps if aud.get(f"{d}|{e}|{p}", {}).get("yes"))
for _, r in O[(O.arm == "signal") & O.strict].iterrows():
    print(f"  {r.cutoff} {r.drug[:26]:26s} {r.effect[:26]:26s} {r['first'][:4]} -> {yr(r.drug, r.effect, r.ps)}")
print(f"cost ${cost[0]:.2f}, total ${ledger.total():.2f}")
O.drop(columns=["ps"]).to_parquet(D / f"strict{SUF}.parquet")
