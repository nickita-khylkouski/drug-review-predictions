"""Backtest with human trials as the outcome instead of papers ($0, ClinicalTrials.gov API v2).
Pairs = data/strict_v2.parquet (unique pairs, no judged paper before the cutoff, < 10 prior PubMed co-mentions).
A trial counts if it is interventional, one of its interventions names a drug ingredient, and the benefit (name or synonym
from effects.json) appears in its conditions, title or primary outcome ('strict') / any outcome ('loose').
Cache agents/trials_cache.json (raw studies per query). -> agents/trials_backtest.parquet
cd ~/drug-embed && nice uv run python sig/agents/trials_backtest.py"""
import json, re, time
from pathlib import Path
import httpx, numpy as np, pandas as pd
from scipy.stats import fisher_exact
H = Path(__file__).parent; D = H.parent / "data"
EFF = json.loads((D / "effects.json").read_text())["effects"]
O = pd.read_parquet(D / "strict_v2.parquet")
CACHE = H / "trials_cache.json"; cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
FIELDS = "NCTId,BriefTitle,OfficialTitle,StudyType,StartDate,StudyFirstSubmitDate,Condition,InterventionName,PrimaryOutcomeMeasure,SecondaryOutcomeMeasure,Phase,EnrollmentCount"


def ingr(d):
    ps = [re.sub(r"\s*\(.*?\)", "", p).strip().lower() for p in d.split(" / ")]
    return [p for p in ps if p != "ethinyl estradiol"] or ps


def terms(e):
    base = e.replace("other:", "").strip().lower()
    v = EFF.get(e, {})
    ts = [base] + [s.lower() for s in v.get("syn", [])] + ([v["mesh"].lower()] if v.get("mesh") and v.get("mesh_ok") else [])
    return [t for t in dict.fromkeys(ts) if len(t) >= 4]


def fetch(intr, ts):
    key = intr + "|" + "|".join(ts)
    if key in cache: return cache[key]
    q = " OR ".join(f'"{t}"' for t in ts)
    out, tok = [], None
    for _ in range(5):
        p = {"query.intr": intr, "query.term": q, "filter.advanced": "AREA[StudyType]INTERVENTIONAL", "pageSize": 1000, "fields": FIELDS}
        if tok: p["pageToken"] = tok
        for k in range(5):
            try:
                r = httpx.get("https://clinicaltrials.gov/api/v2/studies", params=p, timeout=60); r.raise_for_status(); j = r.json(); break
            except Exception:
                time.sleep(3 + 5 * k)
        else:
            return None
        for s in j.get("studies", []):
            ps = s["protocolSection"]; st = ps.get("statusModule", {}); idm = ps.get("identificationModule", {})
            om = ps.get("outcomesModule", {}); cm = ps.get("conditionsModule", {}); am = ps.get("armsInterventionsModule", {})
            out.append({"id": idm.get("nctId"), "title": (idm.get("briefTitle", "") + " | " + idm.get("officialTitle", "")),
                        "start": (st.get("startDateStruct", {}).get("date") or st.get("studyFirstSubmitDate") or "")[:4],
                        "cond": cm.get("conditions", []), "intr": [i.get("name", "") for i in am.get("interventions", [])],
                        "prim": [o.get("measure", "") for o in om.get("primaryOutcomes", [])],
                        "sec": [o.get("measure", "") for o in om.get("secondaryOutcomes", [])]})
        tok = j.get("nextPageToken")
        time.sleep(1.3)
        if not tok: break
    cache[key] = out
    return out


def score(d, e, Y):
    ig, ts = ingr(d), terms(e)
    if not ts: return np.nan, np.nan, np.nan, np.nan, []
    st = fetch(ig[0], ts)
    if st is None: return np.nan, np.nan, np.nan, np.nan, []
    rx = re.compile("|".join(re.escape(t) for t in ts))
    b_s = a_s = b_l = a_l = 0; ids = []
    for s in st:
        if not s["start"].isdigit() or not all(any(i in x.lower() for x in s["intr"]) for i in ig): continue
        strict = bool(rx.search(" ".join(s["cond"] + [s["title"]] + s["prim"]).lower()))
        loose = strict or bool(rx.search(" ".join(s["sec"]).lower()))
        y = int(s["start"])
        if y < Y: b_s += strict; b_l += loose
        else:
            a_s += strict; a_l += loose
            if strict: ids.append((y, s["id"], s["title"][:90]))
    return b_s, a_s, b_l, a_l, sorted(ids)


rows = []
for i, r in enumerate(O.itertuples()):
    rows.append(score(r.drug, r.effect, int(r.cutoff)))
    if i % 50 == 0: CACHE.write_text(json.dumps(cache)); print(i, flush=True)
CACHE.write_text(json.dumps(cache))
O[["tb_s", "ta_s", "tb_l", "ta_l", "trials"]] = pd.DataFrame(rows, index=O.index)
O["trials"] = O.trials.map(json.dumps)
O.drop(columns=[c for c in O.columns if O[c].dtype == object and c not in ("drug", "effect", "arm", "trials")]).to_parquet(H / "trials_backtest.parquet")
for lvl in ("s", "l"):
    X = O[O[f"tb_{lvl}"] == 0]
    for name, ctl in (("same-effect controls", X.arm == "control_drug"), ("all controls", X.arm != "signal")):
        s, c = X[X.arm == "signal"], X[ctl]
        a, b = int((s[f"ta_{lvl}"] > 0).sum()), int((c[f"ta_{lvl}"] > 0).sum())
        orr, p = fisher_exact([[a, len(s) - a], [b, len(c) - b]])
        print(f"{'strict' if lvl == 's' else 'loose'} | {name:21s} signal {a}/{len(s)} = {a / len(s):.1%}  control {b}/{len(c)} = {b / len(c):.1%}  OR {orr:.2f} p {p:.2g}")
