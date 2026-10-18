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
