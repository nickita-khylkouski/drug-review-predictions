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
