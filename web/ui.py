"""Shared Streamlit presentation helpers: labels, styling and motion, and asset loading with fallbacks."""

import random
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
    """Label an unimplemented feature without showing fabricated results."""
    st.info(f"{featureName}: planned; no calculated results yet.")


def priceInput(crop: str = "CORN", key: str = "price") -> float:
    """One editable price assumption, clearly labeled, shared through session state."""
    return st.sidebar.number_input(
        f"{CROP_NAMES.get(crop, crop.title())} price ($/bushel) - assumed price, replace with a cited source",
        min_value=0.0, value=DEFAULT_PRICE.get(crop, 4.00), step=0.25, key=f"{key}_{crop}",
    )


# ---------------------------------------------------------------------------
# Styling and motion
# ---------------------------------------------------------------------------

# Injected once per run from app.py, so it reaches every page. All motion is decorative and is
# switched off for visitors who ask their system to reduce motion.
GLOBAL_CSS = """
<style>
@keyframes drFadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
@keyframes drPop { 0% { opacity: 0; transform: scale(.94); } 60% { opacity: 1; transform: scale(1.03); } 100% { transform: none; } }
@keyframes drShine { from { background-position: 0% 50%; } to { background-position: 200% 50%; } }
@keyframes drGlow { 0%, 100% { box-shadow: 0 0 0 0 rgba(240,180,41,.0); } 50% { box-shadow: 0 0 0 6px rgba(240,180,41,.22); } }

.block-container { padding-top: 2.4rem; }

/* Page content rises in, one block after another */
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > * { animation: drFadeUp .6s cubic-bezier(.2,.7,.2,1) both; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(2) { animation-delay: .05s; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(3) { animation-delay: .10s; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(4) { animation-delay: .15s; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(5) { animation-delay: .20s; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(6) { animation-delay: .25s; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > *:nth-child(n+7) { animation-delay: .30s; }

/* Page titles: a slow amber shine */
[data-testid="stHeading"] h1 {
  background: linear-gradient(90deg, #f0b429, #e8743b, #f6d365, #f0b429);
  background-size: 200% auto; -webkit-background-clip: text; background-clip: text; color: transparent;
  animation: drShine 8s linear infinite;
}
[data-testid="stHeading"] h3 { border-left: 3px solid #f0b429; padding-left: .55rem; }

/* County cards (containers keyed "card..."): lift on hover */
[class*="st-key-card"] { transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease; border-radius: .7rem; }
[class*="st-key-card"]:hover { transform: translateY(-4px); box-shadow: 0 12px 28px rgba(0,0,0,.35); border-color: rgba(240,180,41,.55) !important; }
[data-testid="stMetricValue"] { animation: drPop .7s ease both; font-size: 1.5rem; }

/* Primary buttons breathe softly; navigation links slide on hover */
[data-testid="stBaseButton-primary"] { animation: drGlow 2.6s ease-in-out infinite; transition: transform .15s; }
[data-testid="stBaseButton-primary"]:hover { transform: translateY(-1px); }
[data-testid="stSidebarNavLink"] { transition: transform .2s ease, background .2s ease; }
[data-testid="stSidebarNavLink"]:hover { transform: translateX(4px); }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
</style>
"""


def applyStyle() -> None:
    """Shared CSS and motion. Style-only st.html takes no space on the page."""
    st.html(GLOBAL_CSS)


def heroBanner(title: str, subtitle: str) -> None:
    """Animated banner drawn in CSS and SVG: a corn field cycles from wet to drought and back.
    Purely decorative (labeled as such); no data is shown in it."""
    rand = random.Random(4)
    stalks = []
    for row, (y, scale, opacity) in enumerate([(150, 0.55, 0.55), (165, 0.75, 0.75), (182, 1.0, 1.0)]):
        for k in range(26):
            x = k * 40 + rand.uniform(-8, 8) + (row % 2) * 20
            delay = rand.uniform(0, 3)
            stalks.append(
                f'<g class="stalk" transform="translate({x:.0f},{y}) scale({scale})" opacity="{opacity}" '
                f'style="animation-delay:-{delay:.2f}s">'
                f'<path d="M0 0 C 1 -20 -1 -40 0 -62"/>'
                f'<path d="M0 -22 C 10 -26 18 -22 24 -16"/><path d="M0 -34 C -10 -38 -18 -34 -24 -28"/>'
                f'<path d="M0 -46 C 9 -50 15 -48 20 -42"/></g>'
            )
    # Rendered in its own frame: st.html sanitizes SVG away, an iframe keeps it.
    st.iframe(f"""<!doctype html><html><head><meta charset="utf-8">
<style>html, body {{ margin: 0; background: transparent; font-family: "Source Sans Pro", system-ui, sans-serif; overflow: hidden; }}</style>
</head><body>
<div class="drHero">
  <div class="drSky"></div><div class="drSun"></div>
  <div class="drCloud c1"></div><div class="drCloud c2"></div><div class="drCloud c3"></div>
  <svg class="drField" viewBox="0 0 1040 200" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
    <rect class="drGround" x="0" y="150" width="1040" height="50"/>
    <g class="drCracks"><path d="M60 175 l30 8 l25 -6 l20 10"/><path d="M300 185 l22 -7 l30 9"/>
      <path d="M520 172 l26 10 l18 -8 l28 6"/><path d="M760 186 l24 -9 l26 8"/><path d="M930 176 l28 7 l22 -5"/></g>
    {''.join(stalks)}
  </svg>
  <div class="drText"><div class="drTitle">{title}</div><div class="drSub">{subtitle}</div></div>
  <div class="drTag">Illustrative animation, not data</div>
</div>
<style>
.drHero {{ position: relative; height: 230px; border-radius: 14px; overflow: hidden; margin: 2px 2px 0;
  border: 1px solid rgba(255,255,255,.08); box-shadow: 0 10px 30px rgba(0,0,0,.35); }}
.drSky {{ position: absolute; inset: 0; background: linear-gradient(180deg, #5aa7e6, #bfe0f5);
  animation: drSkyCycle 16s ease-in-out infinite; }}
@keyframes drSkyCycle {{ 0%,100% {{ filter: none; }} 45%,60% {{ filter: sepia(.9) saturate(1.6) hue-rotate(-12deg) brightness(.92); }} }}
.drSun {{ position: absolute; top: 28px; right: 12%; width: 54px; height: 54px; border-radius: 50%;
  background: radial-gradient(circle, #fff6c8, #ffd25e 60%, rgba(255,210,94,0) 72%);
  animation: drSunCycle 16s ease-in-out infinite; }}
@keyframes drSunCycle {{ 0%,100% {{ transform: scale(1); }} 50% {{ transform: scale(1.35); filter: hue-rotate(-20deg) saturate(1.8); }} }}
.drCloud {{ position: absolute; height: 26px; border-radius: 20px; background: rgba(255,255,255,.85);
  box-shadow: 18px -10px 0 4px rgba(255,255,255,.85), 40px 0 0 0 rgba(255,255,255,.85);
  animation: drDrift 40s linear infinite, drCloudCycle 16s ease-in-out infinite; }}
.drCloud.c1 {{ top: 40px; width: 70px; left: -120px; }}
.drCloud.c2 {{ top: 70px; width: 90px; left: -120px; animation-delay: -14s, 0s; }}
.drCloud.c3 {{ top: 30px; width: 60px; left: -120px; animation-delay: -27s, 0s; }}
@keyframes drDrift {{ to {{ transform: translateX(calc(100vw + 240px)); }} }}
@keyframes drCloudCycle {{ 0%,100% {{ opacity: 1; }} 45%,60% {{ opacity: 0; }} }}
.drField {{ position: absolute; left: 0; right: 0; bottom: 0; width: 100%; height: 200px; }}
.drGround {{ fill: #5b4030; animation: drGroundCycle 16s ease-in-out infinite; }}
@keyframes drGroundCycle {{ 0%,100% {{ fill: #5b4030; }} 50% {{ fill: #8a6a45; }} }}
.drCracks path {{ fill: none; stroke: #2b1d12; stroke-width: 2; opacity: 0; animation: drCrackCycle 16s ease-in-out infinite; }}
@keyframes drCrackCycle {{ 0%,30%,80%,100% {{ opacity: 0; }} 50%,62% {{ opacity: .9; }} }}
.stalk path {{ fill: none; stroke: #3f8f2f; stroke-width: 3; stroke-linecap: round; animation: drStalkColor 16s ease-in-out infinite; }}
.stalk {{ transform-box: fill-box; transform-origin: bottom center; animation: drSway 3.2s ease-in-out infinite; }}
@keyframes drSway {{ 0%,100% {{ rotate: -3deg; }} 50% {{ rotate: 3deg; }} }}
@keyframes drStalkColor {{ 0%,100% {{ stroke: #3f8f2f; }} 40% {{ stroke: #c9b23a; }} 55% {{ stroke: #8a6436; }} 70% {{ stroke: #c9b23a; }} }}
.drText {{ position: absolute; left: 28px; top: 26px; max-width: 70%; }}
.drTitle {{ font-size: 2.1rem; font-weight: 750; color: #fff; text-shadow: 0 2px 12px rgba(0,0,0,.45); line-height: 1.15;
  animation: drTitleIn .9s cubic-bezier(.2,.7,.2,1) both; }}
.drSub {{ margin-top: .4rem; color: #f5f7fa; font-size: 1.02rem; text-shadow: 0 1px 8px rgba(0,0,0,.5);
  animation: drTitleIn .9s .15s cubic-bezier(.2,.7,.2,1) both; }}
@keyframes drTitleIn {{ from {{ opacity: 0; transform: translateY(16px); }} to {{ opacity: 1; transform: none; }} }}
.drTag {{ position: absolute; right: 10px; bottom: 8px; font-size: 11px; color: #f5f7fa; background: rgba(0,0,0,.35);
  padding: 2px 8px; border-radius: 6px; }}
@media (prefers-reduced-motion: reduce) {{ .drHero * {{ animation: none !important; }} }}
</style>
</body></html>""", height=250)


def animatedStats(stats: list[tuple[str, float, str]]) -> None:
    """A row of numbers that count up when the page opens. stats: (label, value, suffix).
    The values are real; only the counting is animation."""
    cells = "".join(
        f'<div class="drStat"><div class="drNum" data-target="{value}">{value:,.0f}{suffix}</div>'
        f'<div class="drLab">{label}</div></div>'
        for label, value, suffix in stats
    )
    st.html(f"""
<div class="drStats">{cells}</div>
<style>
.drStats {{ display: grid; grid-template-columns: repeat({len(stats)}, 1fr); gap: 12px; margin: .3rem 0 1rem; }}
.drStat {{ background: #151c26; border: 1px solid rgba(255,255,255,.08); border-radius: 12px; padding: 14px 16px;
  transition: transform .25s ease, border-color .25s ease; }}
.drStat:hover {{ transform: translateY(-3px); border-color: rgba(240,180,41,.5); }}
.drNum {{ font-size: 1.9rem; font-weight: 750; color: #f0b429; font-variant-numeric: tabular-nums; }}
.drLab {{ color: #a3adb8; font-size: .9rem; }}
@media (max-width: 640px) {{ .drStats {{ grid-template-columns: repeat(2, 1fr); }} }}
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
