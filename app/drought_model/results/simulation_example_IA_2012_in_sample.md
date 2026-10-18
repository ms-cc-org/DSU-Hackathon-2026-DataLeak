# Simulation example: Iowa 2012, Task B (M1, IN-SAMPLE YEAR: the model was fitted on 2000-2015, which includes 2012)

Counties: 99. Mean start level (level_apr1, observed): 1.11. Observed in 2012: mean worst level Apr 1-Aug 13 = 3.82, share of counties that got worse than their Apr 1 level = 93%.

| Scenario | Mean P(worse) | Counties with P >= 0.5 | Mean predicted level | Counties with a feature outside the training range |
|---|---|---|---|---|
| 2012 weather as observed (precip x 1.0) | 0.77 | 76% | 1.87 | 0 |
| precip x 0.6, same temperatures | 0.94 | 100% | 2.11 | 38 |

Closest historical years (most frequent among each county's 3 nearest own years): observed weather 2001 (52), 2006 (48), 2002 (43); precip x 0.6: 2003 (67), 2006 (43), 2002 (35).
Features outside the training min/max under precip x 0.6 (counties affected): {'precip_apr1_to_cutoff_ratio': 38, 'precip_90d_ratio': 20}.
Scaling precipitation to 60% moves mean P(worse) from 0.77 to 0.94 (+0.17) and the number of counties predicted to worsen from 75 to 99 of 99.
