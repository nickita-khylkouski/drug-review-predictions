# Frozen predictions, 2026-10-26

Written before any of these outcomes are known. The list is `data/predictions_2026-10-26.csv`
(made by `freeze.py`). The sha256 of the list, this file and the scripts are in `data/predictions_2026-10-26.sha256`. Nothing in it may change after today.
If it is changed, the hash won't match.

## What is in the list

- **835 signals.** Every (drug, benefit) pair with lb >= 1.5 over all 501k reviews (`signals_2027_v2.parquet`).
- **1,638 controls.** For each signal, one control with the same drug and a different benefit (823) and one with the same benefit and a different drug (815). Patients didn't single these out (k <= 1). Seed 20261026, same rule as the backtest.

Most of the 835 are already known (bupropion for smoking, spironolactone for acne). Scoring removes those the
same way the backtest did, using only papers dated before today.

## Prediction 1: the list as a whole (main test)

**Scored on:** 2031-10-26 (five years).

**Pairs that count.** Signal and control pairs that, as of 2026-10-26, have
- no PubMed paper the judge counts as studying the drug for that benefit, and
- fewer than 10 PubMed papers that mention the drug and the benefit together at all.

**Outcome.** A first qualifying paper dated 2026-10-27 to 2031-10-26, judged the same way as the backtest:
- the paper judge (`judge_lib.py`, p > .9), then
- the arm-blind strict audit (`strict_audit.py` question, word for word).

The judge never sees which group a pair is in.

**Prediction.** Signals get a first paper more often than controls. One-sided Fisher exact test, p < .05.

**What the backtest gave.** 19.5% vs 4.5% (OR about 5) over roughly 8 to 14 years of follow-up. Five years is shorter,
so both rates should be lower. The prediction is only that the gap holds.

**Secondary outcome.** A registered interventional trial on ClinicalTrials.gov that names the drug as an intervention
and the benefit in its conditions, title or any outcome (the loose `trials_backtest.py` rule), starting in the window. Each
matching trial is checked with the `agents/trials_audit.py` question, word for word. Backtest: 6.1% vs 1.9% of all controls, which is too few
to be more than secondary.

**Failure.** If signals and controls come out the same (p >= .05), the method didn't predict anything this time, and that
gets reported the same way a success would.

## Prediction 2: the four leads

Each is "studied" if, by 2031-10-26, a paper (human or animal) or a registered trial tests that drug for that benefit.
A study that finds no effect still counts as studied. Whether it worked gets recorded separately.

| Lead | Review numbers (frozen) | Counts as studied |
|---|---|---|
| Amlodipine, migraine prevention | 9 of 881 blood-pressure reviewers vs 3 of 2,811 on unrelated BP pills; lb 1.74 (headache), 1.64 (migraine prevention) | Amlodipine on its own (not in a combo) tested for migraine or headache prevention |
| Lorcaserin, sleep | 48 of 1,008 weight-loss reviewers, about 48 per 1,000 vs 0 to 8 on every other weight-loss drug; lb 9.0 | Lorcaserin, or another 5-HT2C agonist (e.g. bexicaserin), with sleep as a reported outcome |
| Contrave, coffee craving | 10 of 2,044 vs 1 of 4,107 on bupropion and 0 of 834 on naltrexone; lb 1.64 | Bupropion + naltrexone and caffeine or coffee intake or craving |
| Progestin-only pill, migraine | 3.0% vs 0.8% on combined pills; implant, IUD, shot about 0.4 to 0.5%; norethindrone lb 2.8, drospirenone 3.0 | Norethindrone or drospirenone-only pill tested for migraine (desogestrel doesn't count, it's already studied) |

There's no p-value at this level, just four yes/no outcomes. Base rate from the backtest: about 1 in 5 open signals got a
first paper within 8 years.

## Not predictions

These were already being tested by 2026, so they can't count:
- GLP-1 drugs and alcohol
- lorcaserin and alcohol
- lorcaserin and smoking

## Rules

- The list, the controls and the judge question are fixed as of today.
- Judge models can be swapped if the old ones are gone. Any swap has to be re-run on the backtest set first and
  match it (strict audit: signal 22/113, control 49/1,080).
- Every outcome gets reported, including misses.
