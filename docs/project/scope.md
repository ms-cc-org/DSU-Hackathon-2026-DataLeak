# HARVEST scope

## Goal and user

Help an agricultural planning officer understand county crop losses and estimate drought-related insurance exposure. The user can inspect history, compare explicit drought scenarios and identify counties with larger predicted insurance payouts. Insurance inputs represent information available around the August 15 decision point.

## Current product

Navigation order: **Story → Explore 3D → Insurance → Planner**. The brand is HARVEST; the navigation has no state/crop/date tagline.

| Part | Current behavior |
|---|---|
| Historical exploration | Supplied 2000–2025 county records, drought maps and an illustrative 3D crop/soil scene. |
| Insurance | Saved model D predicts payout share and damaged-acre share for IA/NE corn and soybeans. Results include payout dollars, supporting exposure figures, a 3D county map, exact inputs and exports. |
| Insurance scenarios | Future 2026–2030 scenarios, historical climate-footprint what-ifs and historical replay. Default future year: 2026. |
| Planner | One county/crop loss scenario using a historical lookup. Default: 2026; all 2026–2030 labels say “(projected).” No state-fund form or blue source banner. |
| Data coverage | History/Planner cover CA, DE, IA, NE and the four supplied crops where usable records exist. Missing or thin groups remain visible as unavailable or uncertain. |

After the first Insurance run, changing state, crop, mode, year, exposure year, climate footprint or multipliers automatically refreshes the results. Totals, county details, audit inputs and downloads must use the same selection; failures remove stale output.

## Boundaries

- Insurance payouts, crop-value losses and government relief are different quantities. X is estimated insurance payouts; Y is estimated deductible exposure; Z is an illustrative 95%-coverage relief calculation.
- Future weather, acreage and prices are not independently forecast. Historical climate and insured exposure are assumptions. Changing only the target-year label does not change model D's predictions.
- Planner is a separate, unvalidated historical lookup; its linear yield trend extends through 2030. It is not the insurance model.
- County averages do not support field/farm predictions, actual claim decisions or causal claims about interventions.
- Insurance does not extrapolate to CA/DE, wheat or sorghum. Missing coverage is not zero loss.
- The state-fund section and Evidence page are removed. Allocation code remains on disk as legacy code; drought-severity models remain experimental and disconnected from the site.
- No database, new live-data service or model retraining during requests is required.

## Change rules

Keep model D's existing features/settings and public output contract stable unless a new modeling decision explicitly changes them. Every model-related change must pass the [selection-to-output checks](../engineering/verification.md), including numerical agreement with saved inference. Maintain this scope and the [architecture](../engineering/architecture.md) when product structure changes.
