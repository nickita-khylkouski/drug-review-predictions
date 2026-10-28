"""One Decisions API call: several masked reviews, one choice question per (review, candidate effect)."""
from pathlib import Path
import json, time
import httpx

URL = "https://api.openai.com/v1/decisions"
PRICE = 0.10 / 1e6
HEAD = """Patient reviews of medications; drug names hidden as [drug]. Each review starts with what the person took the drug for.
For each question, say what the review reports about one effect, as caused by the reviewed drug:
better = the drug made this better or made a problem go away, and it is NOT what they took the drug for
reason = it is what they took the drug for (or a usual symptom of that), and the drug made it better
worse = the drug caused it or made it worse
faded = a problem the drug caused at first, which later eased or went away
none = not reported for this drug: not mentioned, no change, unclear, hypothetical, about another drug or person, or only before starting
"""
CHOICES = [{"value": v, "description": v} for v in ("better", "reason", "worse", "faded", "none")]


def build(batch):
    """batch: list of (rid, cond, text, [effects])"""
    inp = HEAD + "\n" + "\n\n".join(f"[R{j + 1}] Took it for: {c or 'not stated'}\n{t}" for j, (_, c, t, _) in enumerate(batch))
    qs = [{"type": "choice", "name": f"{j}|{e}", "instructions": f"R{j + 1}: {e}", "choices": CHOICES}
          for j, (_, _, _, effs) in enumerate(batch) for e in effs]
    return inp, qs


def call(client, key, batch, tries=6):
    inp, qs = build(batch)
    for k in range(tries):
        try:
            r = client.post(URL, headers={"Authorization": f"Bearer {key}"}, json={"model": "gpt-6-luna", "input": inp, "questions": qs}, timeout=120)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(min(30, 2 ** k)); continue
            j = r.json()
            if r.status_code != 200:
                return None, j, 0
            out = []
            for a in j.get("answers", []):
                jj, e = a["name"].split("|", 1)
                if a.get("type") == "refusal":
                    out.append((batch[int(jj)][0], e, "refusal", None)); continue
                out.append((batch[int(jj)][0], e, a["choice"], {p["value"]: round(p["probability"], 3) for p in a.get("probabilities") or []}))
            return out, None, j.get("usage", {}).get("input_tokens", 0)
        except (httpx.TransportError, json.JSONDecodeError) as ex:
            err = str(ex); time.sleep(min(30, 2 ** k))
    return None, "retries", 0


FLAG_HEAD = """Patient reviews of medications; drug names hidden as [drug]. Each review starts with what the person took the drug for.
An EXTRA BENEFIT means: besides what they took it for, the person says the reviewed drug also improved some other health problem,
symptom, habit or trait. Count any extra benefit, even a well-known one or one mentioned in passing (e.g. clearer skin, lighter
periods or fewer cramps on birth control, weight loss, quitting smoking or drinking, better sleep, less pain, fewer migraines,
hair regrowth, less OCD). Do not count: improvement of the condition they took it for, a side effect that just faded, or
effects of another drug.
"""
FLAG_Q = "R{j}: does it report an EXTRA BENEFIT?"


def flag(client, key, batch, tries=6):
    """batch: list of (rid, cond, text). Returns [(rid, probability)]."""
    inp = FLAG_HEAD + "\n" + "\n\n".join(f"[R{j + 1}] Took it for: {c or 'not stated'}\n{t}" for j, (_, c, t) in enumerate(batch))
    qs = [{"type": "predicate", "name": str(j), "instructions": FLAG_Q.format(j=j + 1)} for j in range(len(batch))]
    for k in range(tries):
        try:
            r = client.post(URL, headers={"Authorization": f"Bearer {key}"}, json={"model": "gpt-6-luna", "input": inp, "questions": qs}, timeout=120)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(min(30, 2 ** k)); continue
            j = r.json()
            if r.status_code != 200:
                return None, j, 0
            return [(batch[int(a["name"])][0], a.get("probability") if a.get("type") != "refusal" else None) for a in j["answers"]], None, j["usage"]["input_tokens"]
        except (httpx.TransportError, json.JSONDecodeError) as ex:
            time.sleep(min(30, 2 ** k))
    return None, "retries", 0


# ---- shared by extract.py / verify.py and the Reddit run ----
EFF = sorted(json.loads((Path(__file__).parent / "data/effects.json").read_text())["effects"])
EXTRACT_SYS = """You read patient reviews of medications (drug names hidden as [drug]) and list EXTRA BENEFITS.
An extra benefit: the person says the reviewed drug improved some health problem, symptom, habit or trait OTHER than what they
took it for. Be strict:
- not the condition they took it for, nor its usual symptoms (mood, anxiety, sleep, energy, focus for psychiatric drugs; pain for
  painkillers; cycle control for birth control taken for birth control is fine to count only for skin, cramps, periods, PMS, etc.)
- not a side effect that faded, not about another drug or person, not something hoped for
- well-known benefits still count (clearer skin on birth control, weight loss, fewer migraines, quitting smoking)

Map each benefit to one effect from this list, using its exact spelling, or write "other: <2-4 words>" if none fits:
""" + "; ".join(EFF) + """

Answer JSON only, one key per review, empty list if none:
{"R1": [{"benefit": "<2-5 plain words, e.g. 'hair regrowth', 'less alcohol craving'>", "effect": "<list effect or other: ...>", "quote": "<exact words, max 12>"}], "R2": [], ...}"""

VERIFY_HEAD = """Patient reviews of medications; drug names hidden as [drug]. Each review starts with what the person took the drug for.
Each question names a possible good effect. Answer yes only if the review says the reviewed drug itself made this better for
the person: an actual improvement they experienced. No if it is a side effect the drug caused, a side effect that just faded
or was absent, something hoped for or asked about, about another drug or person, or not said.
"""
