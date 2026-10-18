# HARVEST pages

`app.py` registers Story (`1_overview.py`), Explore 3D (`2_county_risk.py`), Insurance (`3_scenarios.py`) and Planner (`3_planner.py`) in that order.

Planner defaults to 2026; Insurance updates all results when selections change after the first run. Evidence and the Planner state-fund section are removed. `4_budget_allocation.py` and `6_credits.py` are unregistered legacy pages.

See the [architecture](../../docs/engineering/architecture.md), [scope](../../docs/project/scope.md) and [prediction contract](../../docs/engineering/predictions.md).
