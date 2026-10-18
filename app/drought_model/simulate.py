"""Task B simulation helper: what does the frozen in-season model say about a state-year if daily precipitation were scaled and temperatures shifted?

    from simulate import simulate_levels
    simulate_levels(2012, "IA", precip_scale=0.6)

Daily precipitation is multiplied, and tmax/tmin shifted, for every day from Oct 1 of the previous year to Aug 13 of the simulated year in that state (the days the
features use), then ALL weather features (windows, water balance, ratios) are rebuilt with the same code as the data build and scored by the Task B model.
Map-derived inputs (level_apr1, prev_fall_level) and static inputs stay as observed.

DEFAULT: the frozen Task B model trained on 2000-2015 (artifacts/task_b_full.joblib, built by build_artifact()). For a simulated year <= 2015 that fit has seen the year
(an "in-sample year"; the result says so in .attrs["in_sample_year"]). Pass train_through=Y to retrain on years <= Y instead (e.g. year - 1 for an out-of-sample example).
Features outside the training min/max are flagged either way. Only years <= 2015 are ever loaded. Not wired into the app.
"""
import datetime as dt
import json
import pathlib

import joblib

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

import models as M
from common import LEVELS, O, REPO, RESULTS, TASKS, load_pre_test, task_rows

T = TASKS["B"]
ARTIFACT = pathlib.Path(__file__).resolve().parent / "artifacts" / "task_b_full.joblib"


def build_artifact(path=ARTIFACT):
    """Fit the chosen Task B model on 2000-2015 and save it with what the simulation needs (training min/max, the training table for 'closest years')."""
    df = load_pre_test()
    tr = task_rows(df, "B")
    name = chosen_model_name()
    mdl = M.MODELS[name]().fit(tr, T)
    feats = T["feats"]
    payload = {"model": mdl, "model_name": name, "task": "B", "train_years": [int(tr.year.min()), int(tr.year.max())], "n_train": int(len(tr)), "features": feats,
               "step": int(mdl.step_), "train_min": tr[feats].min(), "train_max": tr[feats].max(),
               "train_table": tr[["fips", "county_name", "year"] + feats + ["y_B", "worse_B"]].reset_index(drop=True),
               "built": dt.datetime.now().isoformat(timespec="seconds"),
               "note": "Needs app/drought_model on sys.path to unpickle (models.py). Weather features must be built with organize_drought_severity.weather_windows / add_ratios."}
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(payload, path)
    return payload


def load_artifact(path=ARTIFACT):
    if not pathlib.Path(path).exists():
        raise FileNotFoundError(f"{path} not found: run `python -c \"import simulate; simulate.build_artifact()\"` from app/drought_model")
    return joblib.load(path)


def chosen_model_name():
    f = RESULTS / "chosen_models.json"
    return json.load(open(f))["B"]["chosen"] if f.exists() else "M2"


def _scenario_weather_features(year, state, precip_scale, temp_shift_c):
    w = O.read_weather(REPO, 2015)                                   # loader filters year <= 2015
    cent = O.read_centroids(REPO)
    in_state = w.fips.isin(set(cent.index[cent.state_alpha == state]))
    m = in_state & (w.date >= pd.Timestamp(f"{year - 1}-10-01")) & (w.date <= pd.Timestamp(f"{year}-08-13"))
    w.loc[m, "pcpn_mm"] = w.loc[m, "pcpn_mm"] * precip_scale
    w.loc[m, "tmax_c"] = w.loc[m, "tmax_c"] + temp_shift_c
    w.loc[m, "tmin_c"] = w.loc[m, "tmin_c"] + temp_shift_c
    wf, _ = O.weather_windows(w, cent.lat)
    wf = O.add_ratios(wf, O.FIRST_YEAR, 2015)
    return wf.xs(year, level="year")


def simulate_levels(year, state, precip_scale=1.0, temp_shift_c=0.0, train_through=None, model=None, n_closest=3):
    """-> DataFrame, one row per county: P(worse), predicted level, start level (level_apr1), closest historical years, features outside the training range.
    train_through=None (default) uses the 2000-2015 artifact; an int retrains on years <= that year."""
    assert year <= 2015, "only years <= 2015 are available before the final test"
    df = load_pre_test()
    if train_through is None:
        art = load_artifact()
        mdl, feats, lo, hi = art["model"], art["features"], art["train_min"], art["train_max"]
        tr = art["train_table"]
        name, fit_years = art["model_name"], tuple(art["train_years"])
    else:
        train_through = min(train_through, 2015)
        tr = task_rows(df[df.year <= train_through], "B")
        name = model or chosen_model_name()
        mdl = M.MODELS[name]().fit(tr, T)
        feats = T["feats"]
        lo, hi = tr[feats].min(), tr[feats].max()
        fit_years = (int(tr.year.min()), train_through)
    base = df[(df.year == year) & (df.state_alpha == state)].set_index("fips")
    wf = _scenario_weather_features(year, state, precip_scale, temp_shift_c)
    x = base.copy()
    for c in O.WEATHER_FEATURES:
        x[c] = wf[c].reindex(x.index)
    x = x.reset_index()
    p = mdl.proba(x, T)
    # closest historical years per county in standardised feature space (the county's own other years in the training table)
    imp = SimpleImputer(strategy="median").fit(tr[feats])
    sc = StandardScaler().fit(imp.transform(tr[feats]))
    zt, zx = sc.transform(imp.transform(tr[feats])), sc.transform(imp.transform(x[feats]))
    rows = []
    for i, r in x.iterrows():
        mine = ((tr.fips == r.fips) & (tr.year != year)).to_numpy()          # never the simulated year itself
        dist = np.sqrt(((zt[mine] - zx[i]) ** 2).sum(axis=1))
        order = np.argsort(dist)[:n_closest]
        yrs = tr.loc[mine, "year"].to_numpy()[order]
        out = [f for f in feats if pd.notna(r[f]) and (r[f] < lo[f] or r[f] > hi[f])]
        rows.append({"fips": r.fips, "county_name": r.county_name, "start_level_apr1": int(r.level_apr1), "p_worse": float(p[i]),
                     "predicted_level": int(M.level_from_p([r.level_apr1], [p[i]], mdl.step_)[0]),
                     "closest_years": ", ".join(str(int(y)) for y in yrs), "features_outside_training_range": ", ".join(out)})
    res = pd.DataFrame(rows)
    res.attrs.update(model=name, fit_years=fit_years, train_through=fit_years[1], step=mdl.step_, precip_scale=precip_scale, temp_shift_c=temp_shift_c,
                     in_sample_year=bool(fit_years[0] <= year <= fit_years[1]))
    return res


def example_ia_2012(model=None, train_through=None):
    """IA 2012 as observed vs precip_scale 0.6. Default (train_through=None): the 2000-2015 artifact, an IN-SAMPLE year -> results/simulation_example_IA_2012_in_sample.md.
    With train_through=2011: out of sample -> results/simulation_example_IA_2012.md. Returns the text."""
    df = load_pre_test()
    act = df[(df.year == 2012) & (df.state_alpha == "IA")]
    a = simulate_levels(2012, "IA", 1.0, 0.0, train_through=train_through, model=model)
    b = simulate_levels(2012, "IA", 0.6, 0.0, train_through=train_through, model=model)
    tag = "IN-SAMPLE YEAR: the model was fitted on 2000-2015, which includes 2012" if a.attrs["in_sample_year"] else f"out of sample: fitted on years through {a.attrs['train_through']}"
    n = len(a)
    row = lambda name, r: (f"| {name} | {r.p_worse.mean():.2f} | {(r.p_worse >= 0.5).mean() * 100:.0f}% | {r.predicted_level.mean():.2f} | "
                           f"{(r.features_outside_training_range != '').sum()} |")
    top = lambda r: pd.Series(", ".join(r.closest_years).split(", ")).value_counts().head(3)
    text = f"""# Simulation example: Iowa 2012, Task B ({a.attrs['model']}, {tag})

Counties: {n}. Mean start level (level_apr1, observed): {a.start_level_apr1.mean():.2f}. Observed in 2012: mean worst level Apr 1-Aug 13 = {act.y_B.mean():.2f}, share of counties that got worse than their Apr 1 level = {act.worse_B.mean() * 100:.0f}%.

| Scenario | Mean P(worse) | Counties with P >= 0.5 | Mean predicted level | Counties with a feature outside the training range |
|---|---|---|---|---|
{row('2012 weather as observed (precip x 1.0)', a)}
{row('precip x 0.6, same temperatures', b)}

Closest historical years (most frequent among each county's 3 nearest own years): observed weather {', '.join(f'{y} ({c})' for y, c in top(a).items())}; precip x 0.6: {', '.join(f'{y} ({c})' for y, c in top(b).items())}.
Features outside the training min/max under precip x 0.6 (counties affected): {pd.Series(', '.join(b.features_outside_training_range[b.features_outside_training_range != '']).split(', ')).value_counts().head(6).to_dict() if (b.features_outside_training_range != '').any() else 'none'}.
Scaling precipitation to 60% moves mean P(worse) from {a.p_worse.mean():.2f} to {b.p_worse.mean():.2f} (+{(b.p_worse.mean() - a.p_worse.mean()):.2f}) and the number of counties predicted to worsen from {(a.p_worse >= 0.5).sum()} to {(b.p_worse >= 0.5).sum()} of {n}.
"""
    suffix = "_in_sample" if a.attrs["in_sample_year"] else ""
    (RESULTS / f"simulation_example_IA_2012{suffix}.md").write_text(text)
    b.to_csv(RESULTS / f"simulation_example_IA_2012_precip0.6_by_county{suffix}.csv", index=False)
    return text


if __name__ == "__main__":
    print(example_ia_2012())
