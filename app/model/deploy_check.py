"""G (TabPFN v2) deployability check, CPU only. Run with the python of a fresh venv built from requirements.txt (+ tabpfn):

    <venv>/bin/python app/model/deploy_check.py [out.json]

Measures, with the setting G was evaluated with (TabPFN v2 weights, n_estimators=8) and device forced to CPU: weight-load + fit time, and the time
to predict all IA + NE county-crops of one year (2013, from a model fitted on 2000-2012) for T1 and T2, median of 3 runs. It also checks whether two
identical CPU runs give bit-identical predictions. Reads only training and validation data.
"""
import json
import os
import platform
import statistics
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import RESULTS, T1, T2, load_usable          # noqa: E402
from tabpfn_model import TabPFNModel                    # noqa: E402

RUNS = 3


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else str(RESULTS / "g_deployability.json")
    import torch
    torch.set_num_threads(os.cpu_count())
    train, val = load_usable("training"), load_usable("validation")
    one = val[val.year == 2013].reset_index(drop=True)
    res = {"device": "cpu", "cpu_count": os.cpu_count(), "torch_threads": torch.get_num_threads(), "torch": torch.__version__,
           "python": platform.python_version(), "machine": platform.platform(), "train_rows": len(train), "predict_rows": len(one),
           "n_estimators": 8, "tabpfn_version": __import__("tabpfn").__version__}
    models, preds = {}, {}
    for name, target in [("t1", T1), ("t2", T2)]:
        t = time.perf_counter()
        models[name] = TabPFNModel(device="cpu").fit(train, target)
        res[f"load_and_fit_seconds_{name}"] = round(time.perf_counter() - t, 2)
    per_run = []
    for r in range(RUNS):
        row = {}
        for name in ("t1", "t2"):
            t = time.perf_counter()
            p = models[name].predict(one)
            row[name] = time.perf_counter() - t
            preds.setdefault(name, []).append(p)
        row["sum"] = row["t1"] + row["t2"]
        per_run.append(row)
        print(f"run {r + 1}: t1 {row['t1']:.1f}s t2 {row['t2']:.1f}s sum {row['sum']:.1f}s", flush=True)
    res["predict_seconds_runs"] = [{k: round(v, 2) for k, v in r.items()} for r in per_run]
    res["predict_seconds_t1_median"] = round(statistics.median(r["t1"] for r in per_run), 2)
    res["predict_seconds_t2_median"] = round(statistics.median(r["t2"] for r in per_run), 2)
    res["predict_seconds_sum_t1_t2_median"] = round(statistics.median(r["sum"] for r in per_run), 2)
    res["cpu_predictions_bit_identical_across_runs"] = all(np.array_equal(preds[n][0], x) for n in preds for x in preds[n][1:])
    res["limit_seconds"] = 10
    res["under_limit"] = res["predict_seconds_sum_t1_t2_median"] < 10
    json.dump(res, open(out_path, "w"), indent=2)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
