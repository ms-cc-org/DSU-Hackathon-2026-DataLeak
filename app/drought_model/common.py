"""Shared loading and task definitions for the drought-severity model. Only years <= 2015 are ever read here (training + validation folders of
drought_severity_data); the testing folder is never opened. final_test.py builds 2016-2025 in memory and only with --i-am-sure."""
import pathlib
import sys

import numpy as np
import pandas as pd

REPO = pathlib.Path(__file__).resolve().parents[2]
DATA = REPO / "drought_severity_data"
RESULTS = pathlib.Path(__file__).resolve().parent / "results"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
import organize_drought_severity as O                       # noqa: E402  (feature lists and feature builders)

LAST_PRE_TEST_YEAR = 2015
ID_COLS = O.ID_COLS
TASKS = {"A": {"y": "y_A", "worse": "worse_A", "start": "level_last_map", "feats": O.TASK_A_FEATURES, "name": "Task A: outlook after Aug 13"},
         "B": {"y": "y_B", "worse": "worse_B", "start": "level_apr1", "feats": O.TASK_B_FEATURES, "name": "Task B: in-season severity (weather + soil)"}}
LEVELS = {0: "None", 1: "D0", 2: "D1", 3: "D2", 4: "D3", 5: "D4"}


def assert_pre_test(df, what=""):
    assert df.year.max() <= LAST_PRE_TEST_YEAR, f"rows after {LAST_PRE_TEST_YEAR} {what}: refusing (final test only, with --i-am-sure)"
    return df


def load_pre_test():
    """Training + validation (2000-2015): ID columns, every Task A / Task B input and both tasks' labels."""
    parts = []
    for split in ("training", "validation"):
        d = DATA / split
        ia = pd.read_csv(d / "all_inputs_outlook.csv", dtype={"fips": str})
        la = pd.read_csv(d / "all_labels_outlook.csv", dtype={"fips": str})[["fips", "year", "y_A", "worse_A", "change_A"]]
        lb = pd.read_csv(d / "all_labels_weather_soil.csv", dtype={"fips": str})[["fips", "year", "y_B", "worse_B", "change_B"]]
        parts.append(ia.merge(la, on=["fips", "year"], validate="one_to_one").merge(lb, on=["fips", "year"], validate="one_to_one"))
    df = pd.concat(parts, ignore_index=True)
    assert_pre_test(df, "loaded from drought_severity_data")
    assert set(O.TASK_B_FEATURES) <= set(df.columns)
    return df


def task_rows(df, task):
    """Rows of `df` with a label and a start level for the task."""
    t = TASKS[task]
    return df[df[t["worse"]].notna() & df[t["start"]].notna() & df[t["y"]].notna()].copy()
