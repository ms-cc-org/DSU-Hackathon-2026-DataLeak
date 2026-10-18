# Simulation example: Iowa 2012, Task B (M1, trained on years through 2011, so out of sample)

Counties: 99. Mean start level (level_apr1, observed): 1.11. Observed in 2012: mean worst level Apr 1-Aug 13 = 3.82, share of counties that got worse than their Apr 1 level = 93%.

| Scenario | Mean P(worse) | Counties with P >= 0.5 | Mean predicted level | Counties with a feature outside the training range |
|---|---|---|---|---|
| 2012 weather as observed (precip x 1.0) | 0.74 | 73% | 1.84 | 4 |
| precip x 0.6, same temperatures | 0.92 | 100% | 2.11 | 88 |

Closest historical years (most frequent among each county's 3 nearest own years): observed weather 2001 (55), 2006 (54), 2002 (47); precip x 0.6: 2003 (73), 2006 (53), 2002 (38).
Features outside the training min/max under precip x 0.6 (counties affected): {'precip_90d_ratio': 78, 'precip_60d_ratio': 45, 'precip_apr1_to_cutoff_ratio': 38, 'precip_60d': 3}.
Scaling precipitation to 60% moves mean P(worse) from 0.74 to 0.92 (+0.18) and the number of counties predicted to worsen from 72 to 99 of 99.
