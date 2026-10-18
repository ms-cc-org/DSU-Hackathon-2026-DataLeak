"""County results over public USGS imagery, with a local outline view for offline use."""

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import load_counties


imageryUrl = "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"


def countyMapData(table: pd.DataFrame, state: str, valueColumn: str) -> tuple[dict, pd.DataFrame]:
    """Join every supplied state boundary to known totals; absent values stay missing."""
    geometry = {"type": "FeatureCollection", "features": [feature for feature in load_counties()["features"]
                if feature["properties"]["state_alpha"] == state]}
    totals = table.groupby("fips")[valueColumn].sum(min_count=1)
    rows = pd.DataFrame([{"fips": feature["id"], "county": feature["properties"]["county_name"],
                          "value": totals.get(feature["id"], float("nan"))} for feature in geometry["features"]])
    return geometry, rows


def boundaryRings(feature: dict) -> list:
    """Return exterior county rings for polygons and multipolygons."""
    geometry = feature["geometry"]
    polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    return [polygon[0] for polygon in polygons]


def resultMap(table: pd.DataFrame, state: str, valueColumn: str, satellite: bool = True) -> go.Figure:
    """Build a result figure without making server-side network requests."""
    geometry, rows = countyMapData(table, state, valueColumn)
    figure = go.Figure()
    coordinates = [point for feature in geometry["features"] for ring in boundaryRings(feature) for point in ring]
    if not coordinates:
        raise ValueError(f"No supplied county boundaries for {state}.")
    if satellite:
        for available in (False, True):
            subset = rows.loc[rows["value"].notna().eq(available)]
            if subset.empty:
                continue
            figure.add_trace(go.Choroplethmap(
                geojson=geometry, locations=subset["fips"], z=subset["value"] if available else [0] * len(subset),
                text=subset["county"], colorscale="YlOrRd" if available else [[0, "#65717A"], [1, "#65717A"]],
                showscale=available, marker={"opacity": 0.55, "line": {"color": "#E8E4DA", "width": 1}},
                colorbar={"title": "USD", "tickprefix": "$"},
                hovertemplate="%{text}<br>$%{z:,.0f}<extra></extra>" if available else "%{text}<br>No estimate<extra></extra>",
            ))
        longitudes, latitudes = zip(*coordinates)
        centerLatitude = (min(latitudes) + max(latitudes)) / 2
        projectedLatitudeSpan = (max(latitudes) - min(latitudes)) / math.cos(math.radians(centerLatitude))
        span = max(max(longitudes) - min(longitudes), projectedLatitudeSpan * 2.3)
        figure.update_layout(map={
            "style": "white-bg", "center": {"lon": (min(longitudes) + max(longitudes)) / 2,
                                             "lat": centerLatitude},
            "zoom": max(3.0, math.log2(360 / span) + 0.85),
            "layers": [{"below": "traces", "sourcetype": "raster", "sourceattribution": "U.S. Geological Survey",
                        "source": [imageryUrl]}],
        })
    else:
        values = rows.set_index("fips")["value"]
        for feature in geometry["features"]:
            amount = values.loc[feature["id"]]
            countyName = feature["properties"]["county_name"]
            label = f"{countyName}: ${amount:,.0f}" if pd.notna(amount) else f"{countyName}: no estimate"
            for ring in boundaryRings(feature):
                longitudes, latitudes = zip(*ring)
                figure.add_trace(go.Scatter(x=longitudes, y=latitudes, mode="lines", fill="toself",
                    fillcolor="rgba(242,163,58,.45)" if pd.notna(amount) else "rgba(101,113,122,.4)",
                    line={"color": "#B9C0C7", "width": 0.6}, text=label, hoverinfo="text", showlegend=False))
        figure.update_xaxes(visible=False)
        figure.update_yaxes(visible=False, scaleanchor="x", scaleratio=1.3)
    figure.update_layout(height=440, margin={"t": 0, "r": 0, "b": 0, "l": 0},
                         paper_bgcolor="#0E1318", plot_bgcolor="#0E1318", font_color="#E8E4DA")
    return figure


def renderCountyMap(table: pd.DataFrame, state: str, valueColumn: str, key: str) -> None:
    """Render imagery with transparent result overlays and an explicit offline alternative."""
    background = st.segmented_control("Map background", ["Satellite imagery", "County outlines"],
                                       default="Satellite imagery", key=f"{key}Background") or "Satellite imagery"
    st.plotly_chart(resultMap(table, state, valueColumn, satellite=background == "Satellite imagery"),
                    width="stretch", key=key, config={"displayModeBar": False})
    st.caption("Imagery: U.S. Geological Survey. Imagery needs internet access and is geographic context, "
               "not a predicted future image. Choose County outlines for an offline map. Grey counties have no estimate.")
