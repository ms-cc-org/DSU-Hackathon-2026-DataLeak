"""Shared Streamlit presentation helpers: design tokens, labels, the shared CSS, the Story hero,
and asset loading with fallbacks."""

from pathlib import Path

import pandas as pd
import streamlit as st


ASSET_DIR = Path(__file__).resolve().parent / "assets"
MEDIA_DIR = ASSET_DIR / "media"

# ---------------------------------------------------------------------------
# Design tokens ("dusk field"). The same values are in .streamlit/config.toml and viewer.html.
# ---------------------------------------------------------------------------

GROUND, PANEL, LINE = "#0E1318", "#151C23", "#26313B"
TEXT, TEXT_2, MUTED = "#E8E4DA", "#B9C0C7", "#8E9AA5"
AMBER = "#F2A33A"

# The master's max_drought_severity is shifted by one: 0 = none, 1 = D0, ..., 5 = D4.
# The ramp is used only for data. "None" (no drought) is not in the D0-D4 ramp, so it gets a muted sage.
DROUGHT_LABELS = ["None", "D0", "D1", "D2", "D3", "D4"]
DROUGHT_WORDS = ["no drought", "abnormally dry", "moderate", "severe", "extreme", "exceptional"]
DROUGHT_COLORS = ["#5E7F6B", "#E8D26B", "#E3B04B", "#D9843A", "#C2553A", "#8C2F2F"]
NO_DATA_COLOR = "#2A333C"

LOSS_LABEL = "estimated crop-value loss, not a relief payment"
CROP_NAMES = {"CORN": "Corn", "SOYBEANS": "Soybeans", "WHEAT": "Winter wheat", "SORGHUM": "Sorghum"}
# Assumed prices ($/bushel) until a cited source is added; every page labels them as assumptions.
DEFAULT_PRICE = {"CORN": 4.00, "SOYBEANS": 10.00, "WHEAT": 5.50, "SORGHUM": 4.00}


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
    """A clear "Not available yet" state for a result that does not exist. Never shows invented numbers."""
    st.html(f'<div class="drPending"><span class="drMono">NOT AVAILABLE YET</span>'
            f'<div>{featureName}: no calculated results yet.</div></div>')


def eyebrow(text: str) -> None:
    """Small mono label above a headline."""
    st.html(f'<div class="drEyebrow">{text}</div>')


def priceInput(crop: str = "CORN", key: str = "price", where=None) -> float:
    """One editable price assumption, clearly labeled."""
    where = where or st
    return where.number_input(
        f"{CROP_NAMES.get(crop, crop.title())} price ($ per bushel) - assumption",
        min_value=0.0, value=DEFAULT_PRICE.get(crop, 4.00), step=0.25, key=f"{key}_{crop}",
        help="An editable assumption, not a cited market price.",
    )


# ---------------------------------------------------------------------------
# Shared CSS: injected once per run from app.py so it reaches every page.
# All motion is decorative and switched off for visitors who ask their system to reduce motion.
# ---------------------------------------------------------------------------

GLOBAL_CSS = f"""
<style>
:root {{ --ground: {GROUND}; --panel: {PANEL}; --line: {LINE}; --text: {TEXT}; --text2: {TEXT_2};
  --muted: {MUTED}; --amber: {AMBER}; --mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
  --display: "Bricolage Grotesque", "DM Sans", system-ui, sans-serif; }}
@keyframes drFadeUp {{ from {{ opacity: 0; transform: translateY(14px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes drShine {{ from {{ background-position: 0% 50%; }} to {{ background-position: 200% 50%; }} }}
@keyframes drGlow {{ 0%, 100% {{ box-shadow: 0 0 0 0 rgba(242,163,58,0); }} 50% {{ box-shadow: 0 0 0 6px rgba(242,163,58,.22); }} }}

/* No sidebar: navigation lives in the top bar */
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"] {{ display: none !important; }}

/* Top bar: brand on the left and page tabs */
[data-testid="stHeader"] {{ background: var(--ground); border-bottom: 1px solid var(--line); }}
[data-testid="stHeaderLogo"] {{ height: 34px; width: 34px; }}
div:has(> [data-testid="stHeaderLogo"]), a:has(> [data-testid="stHeaderLogo"]), button:has(> [data-testid="stHeaderLogo"]) {{ display: flex; align-items: center; gap: 10px; text-decoration: none; }}
div:has(> [data-testid="stHeaderLogo"])::after, a:has(> [data-testid="stHeaderLogo"])::after,
button:has(> [data-testid="stHeaderLogo"])::after {{ content: "Drought Relief Planner"; font-family: var(--display);
  font-weight: 700; font-size: 1.05rem; color: var(--text); white-space: nowrap; }}
[data-testid="stTopNavLink"] {{ border-radius: 999px; border: 1px solid var(--line); min-height: 44px; padding: 0 18px;
  display: inline-flex; align-items: center; transition: background .2s ease, color .2s ease; }}
[data-testid="stTopNavLink"] p {{ font-weight: 500; }}
[data-testid="stTopNavLink"]:hover {{ border-color: var(--amber); }}
[data-testid="stTopNavLink"][aria-current="page"] {{ background: var(--amber); border-color: var(--amber); }}
[data-testid="stTopNavLink"][aria-current="page"] p {{ color: var(--ground); font-weight: 700; }}
@media (max-width: 760px) {{ div:has(> [data-testid="stHeaderLogo"])::after,
  a:has(> [data-testid="stHeaderLogo"])::after, button:has(> [data-testid="stHeaderLogo"])::after {{ display: none; }} }}

/* Page */
.block-container {{ padding-top: 4.2rem; max-width: 1440px; }}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > * {{ animation: drFadeUp .6s cubic-bezier(.2,.7,.2,1) both; }}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(2) {{ animation-delay: .05s; }}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(3) {{ animation-delay: .10s; }}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(4) {{ animation-delay: .15s; }}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(n+5) {{ animation-delay: .20s; }}
[data-testid="stHeading"] h1 {{
  background: linear-gradient(90deg, {AMBER}, #C2553A, #E8D26B, {AMBER}); background-size: 200% auto;
  -webkit-background-clip: text; background-clip: text; color: transparent; animation: drShine 8s linear infinite; }}
.drEyebrow, .drMono {{ font-family: var(--mono); font-size: .74rem; letter-spacing: .14em; text-transform: uppercase; color: var(--amber); }}
.drMuted {{ color: var(--muted); }}

/* Cards: containers keyed "card..." and the pending state */
[class*="st-key-card"] {{ background: var(--panel); border: 1px solid var(--line) !important; border-radius: 22px;
  padding: 18px 20px; transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease; }}
[class*="st-key-cardhover"]:hover {{ transform: translateY(-4px); box-shadow: 0 12px 28px rgba(0,0,0,.4); border-color: rgba(242,163,58,.55) !important; }}
.drPending {{ background: var(--panel); border: 1px dashed var(--line); border-radius: 20px; padding: 16px 18px; color: var(--text2); }}
.drPending .drMono {{ display: block; margin-bottom: 4px; }}
[data-testid="stMetricValue"] {{ font-family: var(--mono); color: var(--amber); }}
[data-testid="stButtonGroup"] button {{ border-color: var(--line); }}
[data-testid="stButtonGroup"] button[aria-checked="true"] {{ background: var(--amber) !important; border-color: var(--amber) !important; }}
[data-testid="stButtonGroup"] button[aria-checked="true"] p {{ color: var(--ground) !important; font-weight: 700; }}

/* Buttons, links, segmented controls: pills, 44px targets, amber with dark text */
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondary"], [data-testid="stPageLink-NavLink"],
[data-testid="stButtonGroup"] button, [data-testid="stDownloadButton"] button {{ min-height: 44px; border-radius: 999px !important; }}
[data-testid="stBaseButton-primary"] {{ background: var(--amber); border-color: var(--amber); color: var(--ground);
  animation: drGlow 2.6s ease-in-out infinite; }}
[data-testid="stBaseButton-primary"] p {{ color: var(--ground); font-weight: 700; }}
[data-testid="stBaseButton-secondary"] {{ border: 1px solid var(--line); background: transparent; }}
[data-testid="stPageLink-NavLink"] {{ border: 1px solid var(--line); padding: 0 20px; display: inline-flex; align-items: center; }}
[class*="st-key-ctaprimary"] [data-testid="stPageLink-NavLink"] {{ background: var(--amber); border-color: var(--amber); }}
[class*="st-key-ctaprimary"] [data-testid="stPageLink-NavLink"] p {{ color: var(--ground); font-weight: 700; }}
[data-testid="stPageLink-NavLink"] p {{ font-weight: 500; }}
:focus-visible, [data-testid="stTopNavLink"]:focus-visible {{ outline: 2px solid var(--amber) !important; outline-offset: 2px; }}

/* Plain blocks */
hr {{ border-color: var(--line); }}
.drFooter {{ border-top: 1px solid var(--line); margin-top: 2rem; padding-top: 1rem; color: var(--muted);
  font-family: var(--mono); font-size: .76rem; letter-spacing: .04em; }}

@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation: none !important; transition: none !important; }}
}}
</style>
"""


def applyStyle() -> None:
    """Shared CSS and motion. Style-only st.html takes no space on the page."""
    st.html(GLOBAL_CSS)


# Fonts for self-contained frames (hero, 3D viewer): served by Streamlit from static/fonts/.
FRAME_FONTS = """
@font-face { font-family: "Bricolage Grotesque"; font-weight: 700; src: url("/app/static/fonts/bricolage-grotesque-latin-700-normal.woff2") format("woff2"); }
@font-face { font-family: "DM Sans"; font-weight: 400; src: url("/app/static/fonts/dm-sans-latin-400-normal.woff2") format("woff2"); }
@font-face { font-family: "DM Sans"; font-weight: 500; src: url("/app/static/fonts/dm-sans-latin-500-normal.woff2") format("woff2"); }
@font-face { font-family: "DM Sans"; font-weight: 700; src: url("/app/static/fonts/dm-sans-latin-700-normal.woff2") format("woff2"); }
@font-face { font-family: "JetBrains Mono"; font-weight: 400; src: url("/app/static/fonts/jetbrains-mono-latin-400-normal.woff2") format("woff2"); }
@font-face { font-family: "JetBrains Mono"; font-weight: 500; src: url("/app/static/fonts/jetbrains-mono-latin-500-normal.woff2") format("woff2"); }
"""


# ---------------------------------------------------------------------------
# Story hero: a dusk landscape drawn in SVG. It sits in its own frame because st.html strips SVG.
# ---------------------------------------------------------------------------

def duskHero(eyebrowText: str, headline: str, sentence: str, height: int = 620) -> None:
    """Full-bleed dusk landscape with an overlay. Decorative only (labeled); the CTAs are real Streamlit
    page links placed over its lower part by the page (see heroCtas in 1_overview.py)."""
    rows = []
    for i in range(-22, 23):  # crop rows converging on the horizon
        xBottom, xTop = 720 + i * 96, 720 + i * 7
        rows.append(f'<line x1="{xBottom}" y1="640" x2="{xTop}" y2="452" />')
    st.iframe(f"""<!doctype html><html><head><meta charset="utf-8">
<style>
{FRAME_FONTS}
html, body {{ margin: 0; height: 100%; background: {GROUND}; overflow: hidden; }}
.hero {{ position: relative; height: 100%; border-radius: 24px; overflow: hidden; border: 1px solid {LINE}; }}
svg {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
.sunGlow {{ animation: breathe 7s ease-in-out infinite; transform-origin: 1040px 450px; }}
@keyframes breathe {{ 0%,100% {{ opacity: .85; transform: scale(1); }} 50% {{ opacity: 1; transform: scale(1.06); }} }}
.rows line {{ stroke: url(#rowFade); stroke-width: 1.4; }}
.rows {{ animation: shimmer 9s ease-in-out infinite; }}
@keyframes shimmer {{ 0%,100% {{ opacity: .55; }} 50% {{ opacity: .8; }} }}
.copy {{ position: absolute; left: clamp(20px, 5vw, 64px); top: clamp(36px, 9vh, 88px); max-width: min(680px, 86%); }}
.eyebrow {{ font: 500 12px/1.4 "JetBrains Mono", ui-monospace, monospace; letter-spacing: .16em; color: {AMBER};
  text-transform: uppercase; animation: rise .8s cubic-bezier(.2,.7,.2,1) both; }}
h1 {{ margin: 14px 0 12px; font: 700 clamp(36px, 6vw, 72px)/1.02 "Bricolage Grotesque", "DM Sans", system-ui, sans-serif;
  color: {TEXT}; letter-spacing: -.01em; animation: rise .9s .08s cubic-bezier(.2,.7,.2,1) both; }}
p {{ margin: 0; font: 400 clamp(16px, 1.6vw, 20px)/1.5 "DM Sans", system-ui, sans-serif; color: {TEXT};
  max-width: 560px; animation: rise .9s .16s cubic-bezier(.2,.7,.2,1) both; }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(16px); }} to {{ opacity: 1; transform: none; }} }}
.tag {{ position: absolute; right: 14px; bottom: 12px; font: 500 11px "JetBrains Mono", monospace; color: {TEXT_2};
  background: rgba(14,19,24,.6); padding: 3px 9px; border-radius: 999px; }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style></head><body>
<div class="hero">
  <svg viewBox="0 0 1440 620" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
    <defs>
      <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="{GROUND}"/><stop offset=".42" stop-color="#2B2430"/>
        <stop offset=".66" stop-color="#C2553A"/><stop offset=".78" stop-color="{AMBER}"/>
      </linearGradient>
      <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">
        <stop offset="0" stop-color="#FFD58A" stop-opacity=".95"/><stop offset=".35" stop-color="{AMBER}" stop-opacity=".55"/>
        <stop offset="1" stop-color="{AMBER}" stop-opacity="0"/>
      </radialGradient>
      <linearGradient id="rowFade" x1="0" y1="1" x2="0" y2="0">
        <stop offset="0" stop-color="#5a3a2a"/><stop offset="1" stop-color="{AMBER}" stop-opacity=".2"/>
      </linearGradient>
    </defs>
    <rect width="1440" height="620" fill="url(#sky)"/>
    <g class="sunGlow"><circle cx="1040" cy="450" r="250" fill="url(#glow)"/><circle cx="1040" cy="452" r="46" fill="#FBD58C"/></g>
    <path d="M0 418 C 180 370 320 400 470 380 C 640 356 760 402 930 386 C 1090 372 1250 398 1440 372 L1440 470 L0 470 Z" fill="#4A2E33" opacity=".85"/>
    <path d="M0 446 C 160 428 300 446 460 432 C 640 416 820 452 1000 438 C 1180 424 1320 446 1440 434 L1440 470 L0 470 Z" fill="#241C22"/>
    <rect x="0" y="452" width="1440" height="168" fill="#14171B"/>
    <g class="rows">{''.join(rows)}</g>
  </svg>
  <div class="copy"><div class="eyebrow">{eyebrowText}</div><h1>{headline}</h1><p>{sentence}</p></div>
  <div class="tag">Illustration, not data</div>
</div>
</body></html>""", height=height)


def animatedStats(stats: list[tuple[str, float, str]]) -> None:
    """A slim row of numbers that count up when the page opens. stats: (label, value, suffix).
    The values are real; only the counting is animation."""
    cells = "".join(
        f'<div class="drStat"><div class="drNum" data-target="{value}">{value:,.0f}{suffix}</div>'
        f'<div class="drLab">{label}</div></div>'
        for label, value, suffix in stats
    )
    st.html(f"""
<div class="drStats">{cells}</div>
<style>
.drStats {{ display: grid; grid-template-columns: repeat({len(stats)}, 1fr); gap: 12px; margin: .4rem 0 1.2rem; }}
.drStat {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 999px; padding: 8px 18px; min-width: 0;
  display: flex; align-items: baseline; gap: 10px; transition: transform .25s ease, border-color .25s ease; }}
.drStat:hover {{ transform: translateY(-3px); border-color: rgba(242,163,58,.5); }}
.drNum {{ font: 500 1.3rem "JetBrains Mono", ui-monospace, monospace; color: {AMBER}; font-variant-numeric: tabular-nums; }}
.drLab {{ color: {TEXT_2}; font-size: .85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
@media (max-width: 640px) {{ .drStats {{ grid-template-columns: repeat(2, 1fr); }} .drStat {{ border-radius: 18px; }}
  .drLab {{ white-space: normal; overflow: visible; text-overflow: clip; }} }}
</style>
<script>
(function () {{
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.drNum[data-target]').forEach((el) => {{
    if (el.dataset.done) return;
    el.dataset.done = '1';
    const target = Number(el.dataset.target), suffix = el.textContent.replace(/[0-9,.]/g, '');
    if (reduce) return;
    const start = performance.now(), duration = 1300;
    const step = (now) => {{
      const k = Math.min(1, (now - start) / duration), eased = 1 - Math.pow(1 - k, 3);
      el.textContent = Math.round(target * eased).toLocaleString('en-US') + suffix;
      if (k < 1) requestAnimationFrame(step);
    }};
    requestAnimationFrame(step);
  }});
}})();
</script>
""", unsafe_allow_javascript=True)


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
