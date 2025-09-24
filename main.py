import streamlit as st
import pandas as pd
import numpy as np
import requests

from leetify_api import get_leetify_sections, LeetifyError, LeetifyNotFound
from faceit_api import get_faceit_player_by_steam, get_faceit_stats


st.set_page_config(
    page_title="CS2 Stats",
    page_icon="📊️",
    layout="wide",
)

st.title("CS2 Stats Dashboard")


def safe_round(value, ndigits=2, fallback="N/A"):
    try:
        f = float(value)
        return round(f, ndigits)
    except (TypeError, ValueError):
        return fallback

def _to_float(x):
    try:
        return float(str(x).replace("%", "").strip())
    except Exception:
        return None

# Input form
with st.form("lookup_form"):
    steamID = st.text_input("SteamID64", "76561198259409483")
    submitted = st.form_submit_button("Fetch stats")

if not submitted:
    st.stop()

# Fetch data
try:
    ranks_dict, rating_dict, stats_dict, leetify_profile = get_leetify_sections(steamID)
except LeetifyNotFound:
    st.error("No Leetify profile found for this SteamID.")
    st.stop()
except LeetifyError as e:
    st.error(f"Leetify error: {e}")
    st.stop()

# Faceit integration
try:
    faceit_player = get_faceit_player_by_steam(steamID)
    faceit_stats = get_faceit_stats(faceit_player["player_id"])


    def extract_faceit_lifetime(stats: dict):
        lt = (stats or {}).get("lifetime", {}) or {}
        return {
            "Average K/D Ratio": _to_float(lt.get("Average K/D Ratio")),
            "ADR": _to_float(lt.get("ADR")),
            "Win Rate %": _to_float(lt.get("Win Rate %")),
            "Matches": int(float(lt.get("Matches"))) if lt.get("Matches") is not None else None,
        }


    # Build a clean dict can pass to st.metric
    faceit_life = extract_faceit_lifetime(faceit_stats)
except Exception as e:
    faceit_player, faceit_stats = None, None
    st.warning(f"Faceit data not available: {e}")

#Layout
col1, col2, col3 = st.columns(3)

with col1:
    st.header("Faceit")
    faceit_elo = ranks_dict.get("faceit_elo")
    faceit_lvl = ranks_dict.get("faceit")
    st.metric("Elo", faceit_elo if faceit_elo is not None else "N/A")
    st.caption(f"Level {faceit_lvl if faceit_lvl else 'N/A'}")

    v = faceit_life["Average K/D Ratio"]
    st.metric("Average K/D Ratio", f"{v:.2f}" if v is not None else "N/A")

    v = faceit_life["ADR"]
    st.metric("ADR", f"{v:.2f}" if v is not None else "N/A")

    v = faceit_life["Win Rate %"]
    st.metric("Win Rate %", f"{v:.1f}%" if v is not None else "N/A")

    v = faceit_life["Matches"]
    st.metric("Matches (GO & 2)", f"{v:,}" if v is not None else "N/A")

with col2:
    st.header("Premier")
    st.metric("Premier", ranks_dict.get("premier", "N/A"))

with col3:
    st.header("Leetify Stats")

    aim_rating = safe_round(rating_dict.get("aim"),2)
    st.metric("Aim Rating", aim_rating)

    leetify_rating = safe_round(ranks_dict.get("leetify"), 2)
    st.metric("Leetify Rating", leetify_rating)

    utility_rating = safe_round(rating_dict.get("utility"), 2)
    st.metric("Utility Rating", utility_rating)
