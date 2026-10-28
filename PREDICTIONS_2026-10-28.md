# Forecasts, 2026-10-28 (add-on to the frozen 2026-10-26 list)

This adds probabilities to the four leads and to the list test. It doesn't change anything in `PREDICTIONS.md`
or `data/predictions_2026-10-26.*`, which still decide what counts as "studied". Hashes for this file and
`data/forecasts_2026-10-28.csv` are in `data/forecasts_2026-10-28.sha256`.

Each probability gets a Brier score at both dates: 2028-10-28 and 2031-10-26.

## Base rate

From the backtest (`strict_v2.parquet`, strict arm-blind audit, open pairs only):

| | first paper within 2 years | within 5 years | ever (8 to 14 years of follow-up) |
|---|---|---|---|
| signals (113) | 6.2% | 10.6% | 19.5% |
| controls (1,080) | 0.9% | 2.7% | 4.5% |

So an open signal has about a 1 in 10 chance of a first paper within five years. A control has about 1 in 40.

## Prediction 1 (the list test): P(pass) = 75%

Simulated power for the one-sided Fisher test:
- If the backtest rates hold (10.6% vs 2.7%), it passes about 99% of the time with around 200 open signals.
- If the gap halves (7% vs 3%), it passes about 73% of the time.
- If the gap mostly goes away (5% vs 3%), it passes about 32% of the time.

I give those three cases 50%, 30% and 20%.

The gap could shrink for two reasons:
- Recent reviews pick up more from news and TikTok (the GLP-1 echo).
- Review volume dropped after 2020.

Expected rates at 2031: signals 7 to 11%, controls 2.5 to 3.5%.

## Lead 1: amlodipine, migraine prevention

**New evidence (2026-10-28):**
- **Amlodipine doesn't cause extra headache.** In the Norvasc label's placebo-controlled trials, headache was 7.3% on amlodipine and 7.8% on placebo (N = 1,730 vs 1,250). The other dihydropyridines do cause it:
  - nifedipine ER: 15.8% vs 9.8%
  - nisoldipine: 22% vs 15%
  - IV nicardipine: 15% vs 2%

  The usual worry is that vasodilators trigger headache, and amlodipine is the one drug in its class where that doesn't show up.
- **Prior literature is three case reports and one pilot:**
  - case reports: 1998 (PMID 11398308), 2007 (18053876), 2008 (19057109)
  - the 2025 pilot (41036277) gave amlodipine 2.5 mg inside a three-drug combo to 30 people: −0.6 days, CI −2.9 to 1.8
- No trial of amlodipine alone is registered as of today.

**Forecasts:**

| | P |
|---|---|
| Studied (frozen rule: amlodipine alone, migraine or headache prevention) by 2028-10-28 | 8% |
| ... by 2031-10-26 | 22% |
| First study is a case report or observational (claims data, target-trial emulation) | 70% |
| First study is an RCT | 30% |
| The 2025 pilot group's next trial is still a combination, not amlodipine alone | 80% |

**If an RCT tests amlodipine alone** (5 to 10 mg, 8 or more weeks, episodic migraine):
- Placebo-adjusted change: −0.8 monthly migraine days (80% interval −2.0 to +0.3).
- P(primary endpoint significant) = 35%.
- P(headache adverse events no higher than placebo) = 85%.
- If subgroups are reported, the benefit is larger in people with high blood pressure (60%).

**Likely sponsor:** academic only. It's a generic that costs a few dollars a month. The most likely places are Asian claims databases, where amlodipine is the most-prescribed blood pressure drug, or the hypertension-and-migraine groups.

**Lowers my estimate:** a 100-plus person RCT of amlodipine alone whose CI rules out a 1-day benefit.

## Lead 2: lorcaserin (5-HT2C agonists), sleep

**New evidence (2026-10-28):**
- **What the reviews describe.** Of the 63 unique lorcaserin reviews that mention better sleep:
  - 14 describe deeper or sounder sleep
  - 12 also mention drowsiness or fatigue
  - 5 mention night eating
  - 3 mention apnea or snoring
  - 3 say they fall asleep faster
  - 5 say they stay asleep

  It reads like sedation rather than weight loss fixing apnea.
- **The Belviq RCTs match.** Fatigue was 7.2% vs 3.6% on placebo. In the bexicaserin PACIFIC trial, somnolence was the main reason people stopped.
- **The pharmacology mostly points the other way.**
  - In rats, a selective 5-HT2C agonist increased time awake and cut slow-wave and REM sleep (Monti 2015, PMID 25932720).
  - In healthy people, mCPP cut total sleep, slow-wave sleep and REM (Lawlor 1991, PMID 2015332).
- **No sleep outcome is planned.** None of the 4 bexicaserin trials list one:
  - DEEp SEA, NCT06660394
  - NCT06719141
  - NCT06908226
  - the open-label extension, NCT05626634

  The lorcaserin Dravet trial (NCT04572243) was terminated.

**Reading of the frozen rule.** I count a sleep measure: a questionnaire, diary, actigraphy or a sleep-lab study. A count of somnolence as an adverse event doesn't count.

**Forecasts:**

| | P |
|---|---|
| A 5-HT2C agonist reports a sleep measure by 2028-10-28 | 5% |
| ... by 2031-10-26 | 15% |
| A bexicaserin phase 3 paper reports somnolence more often than placebo by 2031 | 80% |
| Any new paper on lorcaserin itself and sleep by 2031 | 5% |

**If sleep is measured:**
- Sleep-lab result: REM sleep goes down vs placebo (70%), total sleep time is the same or lower (60%).
- Self-reported sleep quality improves (55%).
- So my best guess is that the reviewers felt sleepier and rated their sleep higher, without better sleep architecture.

**Likely sponsor:** Lundbeck (bexicaserin), most likely as caregiver-reported sleep in the epilepsy trials. Poor sleep is a common complaint in Dravet syndrome.

## Lead 3: Contrave (bupropion + naltrexone), coffee craving

**New evidence (2026-10-28):**
- **The drop comes early.** One reviewer wrote, "after the second day … my 30+ year addiction to coffee and cream just vanished." The first week is the low dose, before much weight comes off.
- **It usually comes with quitting other things.** Reviewers quit coffee together with cigarettes, alcohol or sugar. That fits a general drop in reward-driven cravings.
- **4 reviewers say the opposite.** They drank more coffee to fight the drug's sleepiness or fog.
- **Sleep gets worse on Contrave.** In its RCT label, insomnia was 9.2% vs 5.9% on placebo, and sleep disorders 13.8% vs 8.4%. Worse sleep would usually push coffee up.

**Forecasts:**

| | P |
|---|---|
| Studied (bupropion + naltrexone and caffeine or coffee) by 2028-10-28 | 2% |
| ... by 2031-10-26 | 5% |
| If measured, mean caffeine intake falls in the first 8 weeks | 60% |
| If it falls, by less than one cup a day on average | 80% |
| If measured, about 1 in 3 people who change intake go up, not down | 50% |

**Most likely way it gets measured:** diet records in a weight-loss trial, or a craving or reward study that adds caffeine. Nobody has a commercial reason to fund it.

## Lead 4: progestin-only pill, migraine

The in-data checks are already in `agents/validate_new.md`:
- Without switchers, the gap is still 17/1,515 vs 85/20,820 (OR 2.8).
- Norethindrone (weaker ovulation suppression) shows the same rate as drospirenone. That points to some selection.

**Forecasts:**

| | P |
|---|---|
| Drospirenone 4 mg alone studied for migraine by 2028-10-28 | 10% |
| ... by 2031-10-26 | 30% |
| Norethindrone 0.35 mg studied for migraine by 2031 | 10% |
| Either, by 2031 | 35% |
| First study is an uncontrolled cohort with headache diaries (n 30 to 100), not an RCT | 75% |

**If studied:**
- Drospirenone 4 mg cuts migraine days by 30% or more from baseline in an uncontrolled cohort (70%). That would match the desogestrel studies.
- If both are studied, norethindrone shows a smaller effect than drospirenone (65%).

**Likely sponsor:** European headache-and-gynaecology groups, the ones who did the desogestrel work, or Exeltis/Insud. Slynd is sold in Europe as Slinda.

## The model's top 30

`data/forecasts_2026-10-28.csv` lists `predict.py`'s 30 open leads it thinks are most likely to be studied next.

- **How good the model is:** leave-one-cutoff-out AUC 0.69, against 0.61 for ranking by lb alone.
- **`p_model`:** trained on the first-pass judge outcome with 8 to 14 years of follow-up.
- **`p_5yr`:** `p_model` × 10.6 / 19.5, which is the five-year share of strict hits in the backtest. A rough scaling.

These come straight from the model and weren't read by hand. Some are probably known uses the PubMed screen missed (terbinafine and skin infection, for example). They are scored by the same frozen rule as the rest of the list.

## Reporting

At both dates I'll report:
- each yes/no outcome
- the Brier score for every probability above
- the direction calls

Misses get reported the same way as hits.
