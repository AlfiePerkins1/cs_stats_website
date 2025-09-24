# leetify_api.py
from __future__ import annotations

import requests
from typing import Any, Dict, Tuple, Optional

from dotenv import load_dotenv

load_dotenv("keys.env")

LEETIFY_URL = "https://api-public.cs-prod.leetify.com/v3/profile"

class LeetifyError(Exception):
    """Base error for Leetify API failures."""

class LeetifyNotFound(LeetifyError):
    """Profile not found for given steam64_id."""

class LeetifyBadResponse(LeetifyError):
    """Non-JSON or unexpected structure returned."""

def _build_url(steam64_id: str) -> str:
    steam64_id = (steam64_id or "").strip()
    if not steam64_id.isdigit():
        # Leetify expects a 17-digit steam64; we don't hard-enforce length here
        # but we do require numeric to avoid accidental input.
        raise ValueError("steam64_id must be numeric.")
    return f"{LEETIFY_URL}?steam64_id={steam64_id}"

def get_profile(
    steam64_id: str,
    *,
    timeout: int = 10,
    session: Optional[requests.Session] = None,
) -> Dict[str, Any]:
    """
    Fetch the full Leetify profile JSON for a given Steam64 ID.

    Raises:
        LeetifyNotFound: if Leetify returns 404.
        LeetifyError:    for other HTTP errors.
        LeetifyBadResponse: if the body isn't valid JSON.
        ValueError:      if steam64_id is not numeric.
    """
    url = _build_url(steam64_id)
    s = session or requests
    try:
        resp = s.get(url, timeout=timeout, headers={"User-Agent": "cs2-stats-app/1.0"})
    except requests.exceptions.RequestException as e:
        raise LeetifyError(f"Network error calling Leetify: {e}") from e

    if resp.status_code == 404:
        raise LeetifyNotFound(f"No Leetify profile for Steam64 '{steam64_id}'.")
    if not (200 <= resp.status_code < 300):
        raise LeetifyError(f"Leetify HTTP {resp.status_code}: {resp.text[:200]}")

    try:
        return resp.json()
    except ValueError as e:
        raise LeetifyBadResponse("Leetify returned non-JSON response.") from e

def extract_sections(profile: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Given a Leetify profile JSON, return (ranks_dict, rating_dict, stats_dict)
    with the exact keys your UI expects.
    """
    ranks = profile.get("ranks", {}) or {}
    rating = profile.get("rating", {}) or {}
    stats  = profile.get("stats", {})  or {}

    ranks_dict = {
        "leetify":    ranks.get("leetify"),
        "premier":    ranks.get("premier"),
        "faceit":     ranks.get("faceit"),
        "faceit_elo": ranks.get("faceit_elo"),
        "wingman":    ranks.get("wingman"),
        "renown":     ranks.get("renown"),
    }

    rating_dict = {
        "aim":         rating.get("aim"),
        "positioning": rating.get("positioning"),
        "utility":     rating.get("utility"),
    }

    stats_dict = {
        "accuracy_enemy_spotted":            stats.get("accuracy_enemy_spotted"),
        "counter_strafing_good_shots_ratio": stats.get("counter_strafing_good_shots_ratio"),
    }

    return ranks_dict, rating_dict, stats_dict

def get_leetify_sections(
    steam64_id: str,
    *,
    timeout: int = 10,
    session: Optional[requests.Session] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Convenience one-shot: fetch profile and return
    (ranks_dict, rating_dict, stats_dict, raw_profile).
    """
    profile = get_profile(steam64_id, timeout=timeout, session=session)
    ranks_dict, rating_dict, stats_dict = extract_sections(profile)
    return ranks_dict, rating_dict, stats_dict, profile
