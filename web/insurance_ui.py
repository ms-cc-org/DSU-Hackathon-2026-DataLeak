"""Visible model D workflow: future scenarios, historical replay and auditable outputs."""

import json

import pandas as pd
import streamlit as st

from src.insurance_scenarios import insuranceAnalogContext, insuranceCrops, insuranceInventory, insuranceStates
from web.insurance_data import runInsurance
from web.maps import renderCountyMap
from web.model_evidence import loadInsuranceActuals
from web.ui import CROP_NAMES, markdownSafe


def predictionDefinitions() -> pd.DataFrame:
    """Explicitly distinguish learned quantities, arithmetic and user assumptions."""
    return pd.DataFrame([
        {"Quantity": "Payout share (T1)", "Source": "Predicted by model D", "Unit / meaning": "Fraction of insured liability paid for drought loss"},
        {"Quantity": "Damaged-acre share (T2)", "Source": "Predicted by model D", "Unit / meaning": "Fraction of insured acres with drought losses"},
        {"Quantity": "X: estimated insurance payouts", "Source": "Calculated from T1", "Unit / meaning": "USD = payout share × assumed insured liability"},
        {"Quantity": "Y: estimated deductible exposure", "Source": "Calculated from T2 and coverage", "Unit / meaning": "USD = damaged-acre share × full crop value × (1 − coverage)"},
        {"Quantity": "Z: illustrative 95% relief", "Source": "Calculated policy illustration", "Unit / meaning": "USD under a 95% coverage assumption; not a program payout forecast"},
        {"Quantity": "State fund allocations", "Source": "Proportional rule in Planner", "Unit / meaning": "Based on the separate crop-value-loss lookup across all supported crops"},
    ])


def insuranceInputs() -> dict | None:
    """Collect a supported model scenario with visible exposure and climate assumptions."""
    inventory = insuranceInventory()
    mode = st.radio("Insurance calculation", ["Future insurance scenario", "Historical footprint scenario", "Historical replay"],
                    horizontal=True, key="insuranceMode")
    with st.form("insuranceModelInputs"):
        stateColumn, cropColumn, yearColumn = st.columns(3)
        state = stateColumn.selectbox("Insurance state", list(insuranceStates), format_func=insuranceStates.get,
                                       key="insuranceState")
        crop = cropColumn.selectbox("Insurance crops", ["ALL", *insuranceCrops],
                                     format_func=lambda value: "All insured crops (corn + soybeans)" if value == "ALL" else CROP_NAMES[value],
                                     key="insuranceCrop")
        if mode == "Historical replay":
            years = list(range(inventory["firstYear"], inventory["lastYear"] + 1))
            year = yearColumn.selectbox("Replay year", years, index=years.index(2023), key="insuranceReplayYear")
            st.caption("2016–2025 uses the test artifact fitted on 2000–2015. Earlier years use the full artifact "
                       "and are labeled in sample. Replay uses the historical year's observed inputs.")
            baseYear, footprint, acresScale, priceScale = year, year, 1.0, 1.0
        else:
            years = (list(range(inventory["lastYear"] + 1, 2031)) if mode == "Future insurance scenario"
                     else list(range(inventory["firstYear"], inventory["lastYear"] + 1)))
            year = yearColumn.selectbox("Insurance target year", years,
                index=0 if mode == "Future insurance scenario" else years.index(2023),
                format_func=lambda value: f"{value} (first year after data)" if value == inventory["lastYear"] + 1 else str(value),
                key="insuranceTargetYear" if mode == "Future insurance scenario" else "insuranceHistoricalYear")
            exposureColumn, climateColumn = st.columns(2)
            baseYears = list(range(inventory["firstYear"], inventory["lastYear"] + 1))
            if mode == "Future insurance scenario":
                baseIndex = 0 if "insuranceBaseYear" in st.session_state else len(baseYears) - 1
                baseYear = exposureColumn.selectbox("Insured exposure base year", baseYears, index=baseIndex,
                                                    key="insuranceBaseYear")
            else:
                baseYear = year
                exposureColumn.write(f"Insured exposure base year: **{baseYear}**")
                st.caption("Historical footprint mode uses the target year as its insured exposure base; "
                           "it is an in-sample what-if with the full model, not a held-out replay.")
            footprintOptions = ["ALL", *baseYears] if mode == "Future insurance scenario" else baseYears
            footprint = climateColumn.selectbox("Drought and weather assumption", footprintOptions,
                format_func=lambda value: "All historical seasons (equal weight)" if value == "ALL" else f"Repeat {value}'s climate footprint",
                key="insuranceFutureFootprint" if mode == "Future insurance scenario" else "insuranceHistoricalFootprint")
            st.caption("Each historical season supplies all drought and weather features together across counties "
                       "and crops. The selected base year supplies insured values, soil, irrigation and history. "
                       "Future conditions are assumptions; no future weather observations are used.")
            acresColumn, valueColumn = st.columns(2)
            st.session_state.setdefault("insuranceAcresScale", 1.0)
            st.session_state.setdefault("insurancePriceScale", 1.0)
            acresScale = acresColumn.number_input("Insured-acre multiplier", min_value=0.1, max_value=10.0,
                                                  value="min", step=0.1, key="insuranceAcresScale")
            priceScale = valueColumn.number_input("Insured crop-value multiplier", min_value=0.1, max_value=10.0,
                                                  value="min", step=0.1, key="insurancePriceScale")
            st.caption("Multipliers change exposure and dollar conversion after prediction. They do not change "
                       "model D's features or learned payout/damaged-acre shares. With the same assumptions, "
                       "2026 and 2027 have the same result: D has no future-year trend feature.")
        submitted = st.form_submit_button("Run model D", type="primary")
    return {"mode": mode, "state": state, "crop": crop, "year": year, "baseYear": baseYear,
            "footprint": footprint, "acresScale": acresScale, "priceScale": priceScale} if submitted else None


def exportTable(table: pd.DataFrame) -> bytes:
    """Serialize list-valued flags consistently while preserving identifier text."""
    exported = table.copy()
    for columnName in exported:
        if exported[columnName].map(lambda value: isinstance(value, list)).any():
            exported[columnName] = exported[columnName].map(lambda value: json.dumps(value) if isinstance(value, list) else value)
    return exported.to_csv(index=False).encode("utf-8")


def insuranceColumnConfig() -> dict:
    """Put prediction source and units directly in the result column labels."""
    return {
        "fips": st.column_config.TextColumn("County FIPS"), "county": "County", "crop": "Crop", "year": "Target year",
        "pred_payout_share": st.column_config.NumberColumn("D predicts: payout share", format="percent"),
        "pred_damaged_acre_share": st.column_config.NumberColumn("D predicts: damaged-acre share", format="percent"),
        "X_payout_usd": st.column_config.NumberColumn("X: estimated insurance payouts", format="dollar"),
        "Y_deductible_exposure_usd": st.column_config.NumberColumn("Y: deductible exposure", format="dollar"),
        "Z_relief_95pct_usd": st.column_config.NumberColumn("Z: illustrative 95% relief", format="dollar"),
        "scenarioLiabilityUsd": st.column_config.NumberColumn("Assumed insured liability", format="dollar"),
        "scenarioInsuredAcres": st.column_config.NumberColumn("Assumed insured acres", format="localized"),
        "avg_coverage": st.column_config.NumberColumn("Input: average coverage", format="percent"),
        "out_of_range": "Beyond training range",
        "actualPayoutUsd": st.column_config.NumberColumn("Observed historical payout", format="dollar"),
        "errorUsd": st.column_config.NumberColumn("Predicted minus observed", format="dollar"),
    }


def renderInsuranceAudit(result: dict) -> None:
    """Expose exact model inputs and allow all results and provenance to be downloaded."""
    metadata = result["metadata"]
    with st.expander("Exact model inputs and assumptions"):
        st.write(f"Insured exposure and non-climate history: **{metadata['exposureBaseYear']}**. "
                 f"Climate source: **{metadata['climateSource']}**. "
                 f"Insured-acre multiplier: **{metadata['acresScale']}**; insured-value multiplier: **{metadata['priceScale']}**.")
        footprintYear = st.selectbox("Inspect input footprint year", metadata["footprintYears"], key="insuranceInputFootprint")
        inspected = result["modelInputs"].loc[lambda table: table["footprintYear"].eq(footprintYear)]
        columns = ["fips", "county_name", "state_alpha", "crop", "year", "exposureBaseYear", "footprintYear",
                   "liability", "insured_acres", "avg_coverage", *metadata["featureOrder"], "imputedFeatures"]
        st.dataframe(inspected[columns], hide_index=True, width="stretch")
        st.caption("The two share predictions use the saved model feature order. Insured exposure converts "
                   "shares to dollars afterward. Missing feature values use model D's training-fitted imputer. "
                   "In future mode, the target-year date labels a hypothetical scenario, not observations from that year.")
        model = "test" if metadata["modelArtifact"] == "d_test.joblib" else "full"
        analogContext = insuranceAnalogContext(inspected, model, metadata["acresScale"], metadata["priceScale"])
        st.write(markdownSafe(f"Model C's rough neighbor range for this inspected footprint: "
                             f"${analogContext['lowUsd']:,.0f} to ${analogContext['highUsd']:,.0f}. "
                             "This is not the ensemble spread or a calibrated probability interval."))
        st.dataframe(pd.DataFrame(analogContext["closestYears"]), hide_index=True, width="stretch")
    downloadColumns = st.columns(3)
    filePrefix = f"model_D_{metadata['state']}_{metadata['targetYear']}"
    downloadColumns[0].download_button("Download model predictions", exportTable(result["countyTable"]),
                                        file_name=f"{filePrefix}_predictions.csv", mime="text/csv")
    downloadColumns[1].download_button("Download exact model inputs", exportTable(result["modelInputs"]),
                                        file_name=f"{filePrefix}_inputs.csv", mime="text/csv")
    downloadColumns[2].download_button("Download run assumptions", json.dumps(metadata, indent=2),
                                        file_name=f"{filePrefix}_manifest.json", mime="application/json")


def renderInsuranceResults(result: dict) -> None:
    """Display direct predictions separately from their X/Y/Z dollar arithmetic."""
    metadata, totals = result["metadata"], result["totals"]
    st.subheader(f"Model D results · {insuranceStates[metadata['state']]} · {metadata['targetYear']}")
    st.caption(f"{metadata['runMode']} · {metadata['modelArtifact']} · trained {metadata['trainingYears']} · "
               f"{metadata['evaluationLabel']}. Showing the last completed run; use Run model D to apply edited controls.")
    payoutColumn, shareColumn, damageColumn = st.columns(3)
    payoutColumn.metric("X · estimated insurance payouts", f"${totals['X_payout_usd']:,.0f}")
    shareColumn.metric("D predicts · payout share", f"{totals['payoutShare']:.2%}")
    damageColumn.metric("D predicts · damaged-acre share", f"{totals['damagedAcreShare']:.2%}")
    st.caption("Payout share is weighted by scenario liability; damaged-acre share is weighted by scenario insured acres. "
               "X converts the predicted payout share to dollars. Statewide percentages are not sums of county percentages.")
    deductibleColumn, reliefColumn, acresColumn = st.columns(3)
    deductibleColumn.metric("Y · estimated deductible exposure", f"${totals['Y_deductible_exposure_usd']:,.0f}")
    reliefColumn.metric("Z · illustrative 95% relief", f"${totals['Z_relief_95pct_usd']:,.0f}")
    acresColumn.metric("Calculated damaged acres", f"{totals['predDamagedAcres']:,.0f}")
    st.caption("Y and Z are arithmetic from predicted damaged-acre share and assumed insured coverage. "
               "Z is an illustration under 95% coverage, not an official payment forecast.")
    scenarioCount = len(result["scenarioTotals"])
    if scenarioCount > 1:
        st.info(markdownSafe(f"{scenarioCount} complete historical climate footprints were each evaluated once with equal weight. "
                "The headline is their mean. Their 10th–90th percentile statewide payout spread is "
                f"${result['range']['lowUsd']:,.0f} to ${result['range']['highUsd']:,.0f}. "
                "This is scenario sensitivity, not a calibrated probability interval or a weather forecast."))
    elif metadata["runMode"] != "historical replay":
        st.info(f"Single assumed climate footprint: {metadata['footprintYears'][0]}. "
                "One scenario cannot establish an uncertainty range.")
    if result["flaggedRows"] or result["imputedInputRows"]:
        st.warning(f"{result['flaggedRows']} county/crop rows have features beyond the artifact's training range "
                   f"in at least one run; {result['imputedInputRows']} input rows need missing-feature imputation. "
                   "Inspect inputs and flags before interpreting the estimate.")
    table = result["countyTable"].copy()
    if metadata["runMode"] == "historical replay" and metadata["targetYear"] >= 2016:
        actuals = loadInsuranceActuals()
        table = table.merge(actuals, on=["fips", "crop", "year"], how="left", validate="one_to_one")
        table["errorUsd"] = table["X_payout_usd"] - table["actualPayoutUsd"]
        st.write(markdownSafe(f"Observed drought insurance payouts in these covered historical records: "
                             f"${table['actualPayoutUsd'].sum(min_count=1):,.0f}. "
                             f"Predicted minus observed: ${table['errorUsd'].sum(min_count=1):,.0f}."))
    st.subheader("County and crop predictions")
    columns = ["fips", "county", "crop", "year", "pred_payout_share", "pred_damaged_acre_share",
               "X_payout_usd", "Y_deductible_exposure_usd", "Z_relief_95pct_usd", "scenarioLiabilityUsd",
               "scenarioInsuredAcres", "avg_coverage", "out_of_range"]
    if "actualPayoutUsd" in table:
        columns += ["actualPayoutUsd", "errorUsd"]
    st.dataframe(table[columns].sort_values("X_payout_usd", ascending=False), hide_index=True,
                 width="stretch", column_config=insuranceColumnConfig())
    st.caption(f"{len(table)} insured county/crop combinations are included. Other states, crops or counties "
               "are outside this model run, not zero-loss records. All-crop coverage is available in Planner.")
    with st.expander("Insurance payout map", expanded=False):
        renderCountyMap(table, metadata["state"], "X_payout_usd", "insurancePayoutMap")
    with st.expander("Predicted statewide payouts for each historical climate footprint"):
        st.dataframe(result["scenarioTotals"], hide_index=True, width="stretch")
    renderInsuranceAudit(result)


def renderInsurancePlanner() -> None:
    """Run the prefit engine from an active page with unambiguous model provenance."""
    st.title("Insurance predictions from model D.")
    st.write("Model D directly predicts **payout share** and **damaged-acre share**. Those predictions are "
             "converted into insurance payout dollars and supporting exposure figures below. "
             "Supported: Iowa and Nebraska, corn and soybeans.")
    with st.expander("What is predicted, assumed and calculated?", expanded=True):
        st.dataframe(predictionDefinitions(), hide_index=True, width="stretch")
    st.caption("California, Delaware, winter wheat and sorghum remain available in the crop-loss Planner. "
               "They are outside model D's trained scope; model D's features and settings remain unchanged.")
    handoff = st.session_state.pop("insuranceHandoff", None)
    if handoff is not None:
        for key, value in handoff.items():
            st.session_state[key] = value
    try:
        inputs = insuranceInputs()
        if inputs is not None:
            with st.spinner("Running the saved model D on the selected scenario…"):
                st.session_state["insuranceResult"] = runInsurance(inputs)
        if "insuranceResult" in st.session_state:
            renderInsuranceResults(st.session_state["insuranceResult"])
        else:
            st.info("Choose a future scenario or historical replay, then Run model D to see actual model predictions.")
    except (OSError, ValueError, KeyError, IndexError) as error:
        st.session_state.pop("insuranceResult", None)
        st.error(f"Insurance inference could not run: {error}")
    st.page_link("web/pages/3_planner.py", label="Open the all-crop loss and fund Planner", icon=":material/arrow_forward:")
    st.page_link("web/pages/5_method_and_data.py", label="Review model D's saved test results", icon=":material/fact_check:")
