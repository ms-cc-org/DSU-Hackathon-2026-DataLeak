# Lane 3 handoff

The user confirmed one fund per selected state, shared across **all supported crops together**, proportional to estimated crop-value loss. The active Planner now embeds that workflow below the existing single-county scenario. This supersedes the older Lane 4 notes describing allocation as removed; the four-tab navigation remains unchanged.

- `web/allocation_data.py` calls the same historical lookup as the county Planner for each supplied boundary county and crop. It records assumptions, acreage years, missing estimates and fallback warnings.
- `src/allocation.py` is pure allocation math. It balances integer cents, keeps missing estimates distinct from zero, and produces county/crop, county and crop tables with fund totals.
- `web/allocation_ui.py` shows the submitted scenario, coverage, county allocations, crop totals, a detail filter and a CSV download. The filter changes only the table; all supported crops remain in the fund weights.
- The uncapped proportional rule has no additional eligibility trigger, minimum award or per-crop budget. A fund above covered loss is explicitly flagged; a scenario with no positive estimates leaves the fund unallocated.
- State form controls are independent of the single-county controls, and the last result is labeled with its submitted assumptions. No database or additional dependency is required.

The source crop-loss estimates remain an unvalidated prototype using a hindsight trend. RMA model D is unchanged and does not cover the whole all-state/all-crop allocation scope. The later connected integration adds an active Insurance tab, D context alongside supported state fund runs, saved evidence and USGS imagery maps with an offline outline alternative. This supersedes the earlier four-tab/no-insurance handoff. Additional allocation policy comparisons remain outside the confirmed rule; see `docs/PREDICTION_CONTRACT.md` for current provenance and assumptions.

Contract: `docs/lane3_contract.md`. Run `python -m unittest discover -s tests -v` for allocation, real-data, Streamlit form and existing Lane 2 regression checks.
