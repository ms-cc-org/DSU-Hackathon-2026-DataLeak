"""Shared Streamlit presentation helpers: labels, styling, and asset loading with fallbacks."""

from pathlib import Path

import pandas as pd
import streamlit as st


ASSET_DIR = Path(__file__).resolve().parent / "assets"
MEDIA_DIR = ASSET_DIR / "media"

# The master's max_drought_severity is shifted by one: 0 = none, 1 = D0, ..., 5 = D4.
DROUGHT_LABELS = ["None", "D0", "D1", "D2", "D3", "D4"]
DROUGHT_WORDS = ["no drought", "abnormally dry", "moderate", "severe", "extreme", "exceptional"]
DROUGHT_COLORS = ["#8fbf8f", "#ffff00", "#fcd37f", "#ffaa00", "#e60000", "#730000"]  # U.S. Drought Monitor style
LOSS_LABEL = "estimated crop loss, not program payout"


def droughtLabel(severity) -> str:
    """Shifted master scale (0-5) to a label: 4 -> "D3". Missing stays "No data"."""
    return "No data" if severity is None or pd.isna(severity) else DROUGHT_LABELS[int(severity)]


def droughtText(severity) -> str:
    """Label plus words: 4 -> "D3 (extreme)"."""
    if severity is None or pd.isna(severity):
        return "No data"
    return f"{DROUGHT_LABELS[int(severity)]} ({DROUGHT_WORDS[int(severity)]})"


def money(value) -> str:
    return "No data" if value is None or pd.isna(value) else f"${value:,.0f}"


def markdownSafe(text: str) -> str:
    """Escape $ so Streamlit markdown does not read "$...$" as a math formula."""
    return text.replace("$", "\\$")


def showPending(featureName: str) -> None:
    """Label an unimplemented feature without showing fabricated results."""
    st.info(f"{featureName}: planned; no calculated results yet.")


def applyStyle() -> None:
    """Small shared CSS: card borders and tighter page top. Call once per page run."""
    st.markdown(
        """<style>
        .block-container {padding-top: 2.6rem;}
        div[data-testid="stMetricValue"] {font-size: 1.5rem;}
        </style>""",
        unsafe_allow_html=True,
    )


def priceInput(crop: str = "CORN", key: str = "price") -> float:
    """One editable price assumption, clearly labeled, shared through session state."""
    default = {"CORN": 4.00, "SOYBEANS": 10.00}[crop]
    return st.sidebar.number_input(
        f"{crop.title()} price ($/bushel) - assumed price, replace with a cited source",
        min_value=0.0, value=default, step=0.25, key=f"{key}_{crop}",
    )


# ---------------------------------------------------------------------------
# Assets: every asset is optional. A missing file never breaks a page.
# ---------------------------------------------------------------------------

def assetPath(name: str) -> Path | None:
    """Path to a media file in web/assets/media/, or None if it is missing or empty."""
    path = MEDIA_DIR / name
    return path if path.is_file() and path.stat().st_size > 0 else None


def showImage(name: str, caption: str | None = None) -> bool:
    """Show a decorative image if it exists. Returns False (and shows nothing) if missing."""
    path = assetPath(name)
    if path is None:
        return False
    try:
        st.image(str(path), caption=caption, width="stretch")
        return True
    except Exception:
        return False


def showVideo(name: str, caption: str | None = None) -> bool:
    """Show a decorative muted, looping video if it exists. Returns False if missing."""
    path = assetPath(name)
    if path is None:
        return False
    try:
        st.video(str(path), autoplay=True, muted=True, loop=True)
        if caption:
            st.caption(caption)
        return True
    except Exception:
        return False
