# Connected application verification

Verified locally on October 18, 2026, using the repository virtual environment. No model was refitted, no model D feature/settings changed, and no commit or push was made.

## User story

The officer opens Insurance, selects a supported future/historical scenario, runs the saved model D and sees directly predicted payout and damaged-acre shares, calculated X/Y/Z, exact model inputs and downloadable provenance. The all-crop state fund retains its agreed crop-loss basis, attaches supported insurance context, and hands that result to Insurance for inspection. Evidence displays saved model errors and baselines; result maps offer public imagery and local outlines.

## Automated checks

```bash
.venv/bin/python -m unittest discover -s tests -v
# Ran 44 tests in 9.657s — OK

.venv/bin/python -m unittest discover -s tests -p 'test_connected_app.py' -v
# Final handoff/control-state check: Ran 6 tests in 6.407s — OK

.venv/bin/python -m compileall -q app.py src web tests
git diff --check
```

The full suite covers the original D reproduction against every saved statewide test total, prediction scaling and flags, all-crop fund conservation, actual state/crop coverage, future year projections, climate replacement, complete historical-footprint ensembles, in-sample/out-of-sample labels, model C neighbor context, downloads, five-page navigation, explicit prediction labels and imagery configuration. The final targeted check verifies that the fund-to-Insurance handoff also fills the form with the result's state/year and assumptions.

The browser/server check exposed a Streamlit warning from assigning both a handoff value and a widget default. The form now uses the handoff state without conflicting defaults; the connected-app handoff test additionally asserts that this path emits no widget-policy warning.

## Browser and data-flow checks

| Boundary | Status | Evidence |
|---|---|---|
| Navigation → Insurance | Passed | Five tabs visible; `/insurance` renders the model's prediction-definition table and supported state/crop controls. |
| Run button → model inputs | Passed | Target 2026, exposure base 2025 and 26 historical climate footprints are explicitly selected. Input audit displays county/crop feature values, source years and imputed fields. |
| Inputs → saved model | Passed | The result identifies `d_full.joblib`, training years 2000–2025 and hypothetical future mode. Original engine reproduction tests still pass without retraining. |
| Model → outputs | Passed | Iowa/both-crop 2026 ensemble produces X = USD 206,073,071.63, liability-weighted payout share about 1.35%, and acreage-weighted damaged-acre share about 6.21%. These values are functional checks, not accuracy claims. |
| Model C context | Passed | The inspected 2000 footprint shows a separately labeled rough neighbor range and three historical analog years. |
| Output → downloaded file | Passed | Actual browser download `model_D_IA_2026_predictions.csv` contains 198 county/crop rows, five-character FIPS, both predicted shares, model/artifact provenance and matching X total. |
| Results → imagery | Passed | Public USGS imagery tiles and county payout overlays render with attribution. The county-outline alternative also renders using local geometry. |
| Fund → Insurance handoff | Passed | An Iowa 2027 fund run shows model D context; its inspection link opens Insurance with state IA, target 2027, exposure 2025 and all historical footprints selected, matching the displayed model result. |
| Browser console | Passed | No error/warning entries during inference and imagery verification. |
| Streamlit server | Passed | Verified first on a clean temporary loopback instance. The repo's existing port 8501 server was then restarted on the finalized source to clear stale imports and expose the new navigation. |

Historical replay, historical footprint mode, Nebraska single-crop selection, actual historical comparisons, all five pages and the state-fund handoff are additionally exercised through Streamlit AppTest. Prediction CSV and manifest content are also verified directly from the backend serialization path.

## Known analytical limits

- Model D's trained coverage is IA/NE corn/soybeans. The app does not invent D predictions for CA/DE, winter wheat or sorghum.
- D has large historical errors; the saved official report and its evaluation caveats are visible. Functional tests do not improve model quality.
- Future insurance results use assumed historical climate and insured exposure. Equal footprint weights and the 10th–90th spread are sensitivity summaries, not calibrated future probabilities.
- D has no year feature. With identical exposure/climate assumptions, a target-year label change alone cannot change its prediction.
- The all-crop lookup is separate and remains unvalidated as a future loss forecast. Its fund distribution is policy arithmetic, not an insurance or relief-payment model.
- Insurance context and the all-crop fund have separately disclosed climate assumptions. Context does not change crop-loss eligibility or fund weights.
- Imagery needs network access and is geographic background, not future imagery. Local outlines and numerical workflows work without imagery tiles.
- After source/navigation changes, restart an older Streamlit process once to reload imported modules. No database or provider credential is required.


## Insurance 3D result presentation — October 18, 2026

This update replaces the former Insurance payout map with a visible 3D state map using the existing bundled three.js runtime and local county geometry. Main headings/buttons/metrics use “Predicted results” / “Run predictions”; model D remains named in source explanations, input breakdowns and exported provenance. The formatted statewide payout total appears immediately above the map. Fund allocation maps retain their existing imagery.

Focused verification:

- `test_insurance_map.py`: 2 tests passed — every IA/NE boundary remains visible, crop totals conserve payouts, county shares use exposure weights, zero estimates remain distinct from missing estimates.
- `test_connected_app.py`: 6 tests passed — active page rendering, actual prediction values, IA map total/count, NE single-crop map state/year/total, historical modes, downloads and fund handoff.
- `test_engine.py`: 8 tests passed — official payout reproduction, scaling, flags and planning-band behavior; no model artifacts/settings/features changed.
- `test_allocation_ui.py`: 4 tests passed — all-state fund UI, future year, crop filter and zero-price handling.
- JavaScript module syntax, Python compilation and `git diff --check` passed.

Browser verification: Iowa 2026, both insured crops, all historical climate footprints displays **$206,073,072** above the 99-county extruded map. Plymouth County displays **$6,259,272**, split into corn **$4,193,831** and soybeans **$2,065,441**. Clicking Jasper County updates the detail to **$3,162,954**; the Aerial control changes the camera. No browser console warnings/errors occurred. The map uses actual completed inference results, not the crop-loss lookup. A WebGL failure leaves a clear fallback message and the prediction table available.

The connected UI check exposed two pre-existing references to the removed crop-loss “Predict” mode: the county page still read a removed result key, and the fund form still defaulted to an unsupported option. The stale county block was removed; the fund now offers its supported D0–D4 inputs with D2 as default. The existing all-crop proportional allocation rule is unchanged. Legacy backend tests that still request the removed “Predict” option were outside this focused verification; this is not a new full-suite pass.

The existing port 8501 app was restarted to clear cached UI imports. No commit or push was made.


## Reactive Insurance selections and numerical reconciliation — October 18, 2026

**Reported failure:** after running both crops, selecting Corn or Soybeans still displayed both crops' costs. A regression test reproduced both failures before the fix. The submit-only form deferred changes and continued rendering the previous run. Insurance now uses reactive controls: after the first Run predictions, changing any scenario selection refreshes all outputs using the same cached inference request. The result caption identifies the actual included crops. The prediction manifest includes the requested selection and included crop list; filenames distinguish corn, soybeans and all crops. A failed refresh removes the old map, metrics and downloads, and the next valid refresh retries.

**Automated checks (20 tests passed):**

- `python -m unittest discover -s tests -p 'test_insurance_scenarios.py' -v`: **10 passed** in 5.146s. The new matrix covers 18 combinations of IA/NE × corn/soybeans/all × future/historical footprint/replay. Every county's two shares are checked directly against the saved model artifacts, X/Y/Z and damaged acres are independently recomputed from audited exposures, statewide sums/weighted shares reconcile, and exported CSV values match. Future cases evaluate every saved climate footprint. Existing official replay reproduction checks pass.
- `python -m unittest discover -s tests -p 'test_connected_app.py' -v`: **10 passed** in 15.569s. Tests change controls after results exist without another Run click, including crop, state, year, exposure year, climate footprint and acreage/value multipliers. The displayed X/Y/Z metrics, county/crop table and every county map payout are reconciled with the selected run; all historical modes, failure recovery and fund handoff pass.
- Python compilation and `git diff --check` passed. Model artifacts, features, settings and core inference files are unchanged. This is focused verification of the affected Insurance flow, not a full-suite claim.

**Live browser checks**, unchanged Iowa 2026 / exposure 2025 / all historical seasons / 1× multipliers:

| Selection | Included county/crop rows | Statewide predicted X | Plymouth County predicted X |
|---|---:|---:|---:|
| All insured crops | 198 | $206,073,071.63 | $6,259,271.79 |
| Corn | 99 | $143,831,222.52 | $4,193,830.94 |
| Soybeans | 99 | $62,241,849.11 | $2,065,440.85 |

Changing All → Corn → Soybeans in the browser, without clicking Run again, updates the headline, map crop label, county amount and crop breakdown. The UI correctly rounds these values to whole dollars. No browser console errors/warnings occurred. Screenshot: `/tmp/insurance-soybean-selection.png`. The app on port 8501 was restarted to load the updated modules. No commit or push was made.

Future model-related changes must follow the selection-to-output verification gate in `docs/PREDICTION_CONTRACT.md`. Numerical agreement establishes faithful display of existing model predictions, not improved forecast accuracy.


## Evidence page removal — October 18, 2026

Removed the Evidence navigation entry, page file, Story report-card section and links from Story/Insurance. Removed the unused report renderer; the historical insurance outcome loader remains available for replay comparisons. The active navigation is Story, Explore 3D, Planner and Insurance. Saved model reports remain in `app/model/results/` and credits remain in README.md.

`python -m unittest discover -s tests -p 'test_connected_app.py' -v`: **10 passed** in 14.577s, including all four remaining pages, no Evidence page links, the removed page file, reactive crop selection, numerical display reconciliation, historical modes, failure recovery and Planner handoff. Python compilation and `git diff --check` passed. No prediction settings or model artifacts changed.

Live browser verification confirms exactly four navigation tabs (Story, Explore 3D, Planner, Insurance), no Evidence links on Insurance, and the cleaned Story page. The existing port 8501 app was restarted. Screenshot: `/tmp/four-tab-navigation.png`.
