# Drug review predictions, frozen 2026-10-26

I mined 501,000 drug reviews for side effects people were glad about. In a backtest, the benefits patients flagged got their first paper later 19.5% of the time, against 4.5% for matched pairs (cutoffs 2012, 2015 and 2018).

This repo freezes today's list so the same test can run forward:
- 835 signals and 1,638 matched controls in `data/predictions_2026-10-26.csv`
- the rules for scoring them on 2031-10-26 in `PREDICTIONS.md`
- the scripts that define the scoring

Check that nothing changed:

```
shasum -a 256 -c data/predictions_2026-10-26.sha256
```

The review data isn't included, so the scripts won't run on their own. They're here so the scoring rules can't drift.

## Add-on, 2026-10-28

`PREDICTIONS_2026-10-28.md` puts probabilities on the four leads and the list test, with a call on which way each effect goes, and `data/forecasts_2026-10-28.csv` has the model's 30 most likely next papers. It changes nothing in the Oct 26 files.

```
shasum -a 256 -c data/forecasts_2026-10-28.sha256
```

The sources behind those forecasts (PubMed IDs, trial IDs and the FDA-label placebo rates) are in `EVIDENCE_2026-10-28.md`. `base_rates.py` makes the base rates and power numbers.

## The write-up

[`article/`](article/README.md) explains the whole project in plain language: the known-answer tests, the backtest, the GLP-1 and alcohol story, and the four leads nobody has tested properly.
