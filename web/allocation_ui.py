"""State fund form and allocation results embedded in the active Planner tab."""

import streamlit as st

from src.allocation import allocateFund
from src.projections import preferredProjectionYear, projectionYearLabel
from web.allocation_data import buildStateEstimates
from web.insurance_data import insuranceContextForFund
from web.maps import renderCountyMap
from web.render3d import CROPS, LAST_PROJECTED_YEAR, LAST_YEAR, STATES
from web.scenario_lookup import LEVELS
from web.ui import CROP_NAMES, DEFAULT_PRICE, markdownSafe, money


def allocationInputs() -> dict | None:
    """Collect one statewide scenario with independent price assumptions for every crop."""
    with st.form("stateFundInputs"):
        stateColumn, yearColumn, levelColumn = st.columns(3)
        state = stateColumn.selectbox("Fund state", list(STATES), index=list(STATES).index("IA"),
                                      format_func=STATES.get)
        years = list(range(LAST_YEAR + 1, LAST_PROJECTED_YEAR + 1))
        year = yearColumn.selectbox("Fund scenario year", years,
                                    index=years.index(preferredProjectionYear(years[0], years[-1])),
                                    format_func=projectionYearLabel)
        level = levelColumn.selectbox("Statewide drought assumption", ["Predict"] + LEVELS)
        st.caption("D0-D4 applies the same hypothetical level to every county and crop. Predict uses each "
                   "county and crop's historical drought frequencies; it is not a weather forecast.")
        fundUsd = st.number_input("State fund ($)", min_value=0.0, max_value=1_000_000_000_000.0,
                                  value=10_000_000.0, step=100_000.0, format="%.2f")
        st.write("Price assumptions ($ per bushel)")
        priceColumns = st.columns(len(CROPS))
        prices = {
            crop: priceColumn.number_input(CROP_NAMES[crop], min_value=0.0, value=DEFAULT_PRICE[crop],
                                            step=0.25, key=f"fundPrice_{crop}")
            for crop, priceColumn in zip(CROPS, priceColumns)
        }
        st.caption("All four dataset crops are considered together. Unsupported county/crop combinations "
                   "stay visible with a reason and receive no calculated allocation.")
        submitted = st.form_submit_button("Calculate state allocation", type="primary")
    return {"state": state, "year": year, "level": level, "prices": prices, "fundUsd": fundUsd} if submitted else None


def allocationColumnConfig() -> dict:
    """Human labels and units for county and crop result tables."""
    return {
        "fips": st.column_config.TextColumn("County FIPS"),
        "county": "County", "crop": "Crop", "coverage": "Data coverage",
        "estimatedLossUsd": st.column_config.NumberColumn("Estimated loss ($)", format="dollar",
                                                          help="Estimated crop-value loss in covered records."),
        "allocationUsd": st.column_config.NumberColumn("Fund allocation ($)", format="dollar",
                                                       help="Illustrative share of the selected state fund."),
        "estimatedCropRows": "Estimated crops", "unavailableCropRows": "Unavailable crops",
        "confident": "Enough matching history", "warnings": "Scenario warning",
        "unavailableReason": "Why unavailable", "allocationReason": "Allocation basis",
        "acreageYear": st.column_config.NumberColumn("Latest acreage year", format="%d"),
        "acres": st.column_config.NumberColumn("Planted acres", format="%.0f"),
        "insurancePayoutUsd": st.column_config.NumberColumn("D: insurance payout context ($)", format="dollar"),
        "insurancePayoutShare": st.column_config.NumberColumn("D predicts: payout share", format="percent"),
        "insuranceDamagedAcreShare": st.column_config.NumberColumn("D predicts: damaged-acre share", format="percent"),
    }


def renderAllocationTables(result: dict) -> None:
    """Show county totals and crop detail without changing the statewide fund weights."""
    columnConfig = allocationColumnConfig()
    countyColumns = ["fips", "county", "estimatedLossUsd", "allocationUsd", "estimatedCropRows",
                     "unavailableCropRows", "coverage"]
    if "insurancePayoutUsd" in result["countyTable"]:
        countyColumns.append("insurancePayoutUsd")
    st.subheader("County allocations across all crops")
    countyTable = result["countyTable"].sort_values("allocationUsd", ascending=False, na_position="last")
    st.dataframe(countyTable[countyColumns], hide_index=True, width="stretch", column_config=columnConfig)
    st.caption("Partial coverage totals include only estimated crops. Unavailable estimates and allocations "
               "are blank, not zero. Counties outside the supplied boundaries are not modeled.")

    with st.expander("Fund distribution by crop"):
        cropTable = result["cropTable"].copy()
        cropTable["crop"] = cropTable["crop"].map(CROP_NAMES)
        cropColumns = [columnName for columnName in countyColumns[2:] if columnName in cropTable]
        st.dataframe(cropTable[["crop"] + cropColumns], hide_index=True,
                     width="stretch", column_config=columnConfig)

    with st.expander("County and crop detail, including unavailable estimates"):
        cropFilter = st.selectbox("Show crop detail", ["All crops"] + CROPS,
                                 format_func=lambda crop: CROP_NAMES.get(crop, crop))
        detailTable = result["countyCropTable"].copy()
        if cropFilter != "All crops":
            detailTable = detailTable.loc[detailTable["crop"] == cropFilter]
        detailTable["crop"] = detailTable["crop"].map(CROP_NAMES)
        detailColumns = ["fips", "county", "crop", "estimatedLossUsd", "allocationUsd", "acres",
                         "acreageYear", "confident", "warnings", "unavailableReason", "allocationReason"]
        if "insurancePayoutUsd" in detailTable:
            detailColumns += ["insurancePayoutShare", "insuranceDamagedAcreShare", "insurancePayoutUsd"]
        st.dataframe(detailTable[detailColumns], hide_index=True, width="stretch", column_config=columnConfig)
        st.caption("This crop filter changes the table only. The fund still covers all supported crops together.")


def renderAllocationResult(result: dict) -> None:
    """Explain the computed snapshot, budget conservation, coverage and prototype limits."""
    inputs = result["inputs"]
    summary = result["summary"]
    st.write(f"**{STATES[inputs['state']]} · {inputs['year']} · {inputs['level']} · all supported crops**")
    st.caption("Showing the last calculated inputs. Use Calculate state allocation to apply changes to the form. "
               "The county scenario above has separate controls.")
    pricesText = ", ".join(f"{CROP_NAMES[crop]} ${inputs['prices'][crop]:.2f}/bu" for crop in CROPS)
    st.caption(markdownSafe(f"Price assumptions used: {pricesText}. Latest reported planted acres are used per county and crop."))
    lossColumn, allocatedColumn, gapColumn = st.columns(3)
    lossColumn.metric("Estimated loss in covered records", money(summary["estimatedLossUsd"]))
    allocatedColumn.metric("Allocated fund", f"${summary['allocatedUsd']:,.2f}")
    gapColumn.metric("Loss above fund", money(summary["fundingGapUsd"]))
    table = result["countyCropTable"]
    warningRows = int((table["eligible"] & ~table["confident"]).sum())
    countyCount = len(result["countyTable"])
    st.write(f"{summary['estimatedCropRows']} of {len(table)} county/crop combinations estimated across "
             f"{countyCount} supplied counties. {summary['positiveCropRows']} positive loss estimates share the fund.")
    if summary["unavailableCropRows"]:
        st.warning(f"{summary['unavailableCropRows']} county/crop combinations lack usable estimates and are "
                   "excluded from fund weights. The loss total covers available records only; their need is unknown.")
    if warningRows:
        st.warning(f"{warningRows} included estimates use the nearest historical years because the chosen drought "
                   "level has too little matching history. Their allocations are uncertain; inspect the detail table.")
    if summary["unallocatedUsd"]:
        st.info(f"${summary['unallocatedUsd']:,.2f} remains unallocated because no positive loss estimates are available.")
    if summary["fundToLossRatio"] is not None:
        st.caption(f"Fund / estimated loss: {summary['fundToLossRatio']:.1%}. The proportional rule distributes the "
                   "whole fund when positive estimates exist. It has no loss cap, minimum award or extra drought trigger.")
        if summary["fundToLossRatio"] > 1:
            st.warning("The fund exceeds the estimated loss in covered records. Under this uncapped rule, "
                       "illustrative allocations exceed those losses in the same proportion.")
    st.caption("Illustrative fund allocation = state fund × county/crop estimated loss ÷ total positive estimated "
               "loss across all crops in the selected state. Cents are balanced before county totals are added.")
    context = result.get("insuranceContext")
    if context is not None:
        st.subheader("Connected insurance model D results")
        st.write("Model D predicts payout share and damaged-acre share for corn and soybeans. This comparison "
                 "uses all historical climate footprints with equal weight and the latest insured exposure; "
                 f"the crop-loss allocation above uses its separate {inputs['level']} drought assumption. "
                 "Insurance payouts are a different dollar measure and do not replace the agreed fund weights.")
        payoutColumn, shareColumn, damageColumn = st.columns(3)
        payoutColumn.metric("D · estimated insurance payouts", money(context["totals"]["X_payout_usd"]))
        shareColumn.metric("D predicts · payout share", f"{context['totals']['payoutShare']:.2%}")
        damageColumn.metric("D predicts · damaged-acre share", f"{context['totals']['damagedAcreShare']:.2%}")
    else:
        st.info(result.get("insuranceContextError") or
                "Model D insurance predictions are unavailable for this state. Its trained scope is Iowa/Nebraska "
                "corn and soybeans. The crop-loss fund still covers all supported dataset crops.")
    st.page_link("web/pages/3_scenarios.py", label="Inspect model D predictions and exact inputs", icon=":material/arrow_forward:")
    renderAllocationTables(result)
    with st.expander("State fund allocation map"):
        renderCountyMap(result["countyTable"], inputs["state"], "allocationUsd", "stateFundMap")
    st.download_button("Download full allocation and assumptions (CSV)",
                       data=table.to_csv(index=False).encode("utf-8"),
                       file_name=f"{inputs['state']}_{inputs['year']}_{inputs['level']}_state_fund.csv",
                       mime="text/csv", key="downloadStateFund")


def renderStateFundPlanner() -> None:
    """Calculate and retain a reviewable state fund snapshot after explicit form submission."""
    st.divider()
    st.subheader("Allocate a state fund")
    st.write("Share one fund across all supported crops in the selected state, in proportion to each county and "
             "crop's estimated crop-value loss. These are illustrative allocations using the same prototype "
             "lookup as the county scenario, not official relief payments or RMA insurance payouts.")
    inputs = allocationInputs()
    if inputs is not None:
        try:
            with st.spinner("Estimating all counties and crops in the state…"):
                estimates = buildStateEstimates(inputs["state"], inputs["year"], inputs["level"], inputs["prices"])
                result = allocateFund(estimates, inputs["fundUsd"])
                result["inputs"] = inputs
                try:
                    result["insuranceContext"] = insuranceContextForFund(inputs["state"], inputs["year"])
                except (OSError, ValueError, KeyError) as error:
                    result["insuranceContextError"] = f"Insurance context is unavailable: {error}"
                context = result.get("insuranceContext")
                if context is not None:
                    st.session_state["insuranceResult"] = context
                    st.session_state["insuranceHandoff"] = {
                        "insuranceMode": "Future insurance scenario", "insuranceState": inputs["state"],
                        "insuranceCrop": "ALL", "insuranceTargetYear": inputs["year"],
                        "insuranceBaseYear": context["metadata"]["exposureBaseYear"],
                        "insuranceFutureFootprint": "ALL", "insuranceAcresScale": 1.0, "insurancePriceScale": 1.0,
                    }
                    attachInsuranceContext(result, context)
                st.session_state["stateFundPlan"] = result
        except (OSError, ValueError, KeyError) as error:
            st.session_state.pop("stateFundPlan", None)
            st.error(f"The state fund could not be calculated: {error}")
    if "stateFundPlan" in st.session_state:
        renderAllocationResult(st.session_state["stateFundPlan"])
    else:
        st.info("Choose the state, scenario and fund, then calculate to review county allocations and data coverage.")


def attachInsuranceContext(result: dict, context: dict) -> None:
    """Join distinctly labeled model outputs without changing allocation amounts or eligibility."""
    contextColumns = {"pred_payout_share": "insurancePayoutShare", "pred_damaged_acre_share": "insuranceDamagedAcreShare",
                      "X_payout_usd": "insurancePayoutUsd", "predictionSource": "insurancePredictionSource",
                      "footprintYears": "insuranceFootprintYears", "exposureBaseYear": "insuranceExposureYear"}
    contextTable = context["countyTable"][["fips", "crop", *contextColumns]].rename(columns=contextColumns)
    result["countyCropTable"] = result["countyCropTable"].merge(contextTable, on=["fips", "crop"], how="left", validate="one_to_one")
    countyPayouts = contextTable.groupby("fips")["insurancePayoutUsd"].sum(min_count=1)
    result["countyTable"]["insurancePayoutUsd"] = result["countyTable"]["fips"].map(countyPayouts)
