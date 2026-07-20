#!/usr/bin/env python3
"""Fetch public GitHub contribution data for the configured profile.

The generated JSON is consumed by ``render_heatmap_svg.py``. The script uses
GitHub's public contribution-calendar HTML and deliberately fails instead of
publishing fabricated fallback statistics when the remote markup is unavailable.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_USERNAME = "Deekshith06"
USERNAME = os.environ.get("GH_PROFILE_USER", DEFAULT_USERNAME).strip() or DEFAULT_USERNAME
URL = f"https://github.com/users/{quote(USERNAME, safe='')}/contributions"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "contributions.json"
USER_AGENT = "Deekshith06-profile-readme/2.0"


def build_session() -> requests.Session:
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        }
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def contribution_count(cell: Any, soup: BeautifulSoup) -> int:
    """Extract a contribution count from a calendar cell and its tooltip."""
    cell_id = cell.get("id")
    tooltip = soup.find("tool-tip", attrs={"for": cell_id}) if cell_id else None
    text = tooltip.get_text(" ", strip=True) if tooltip else ""

    if re.search(r"\bno contributions?\b", text, re.IGNORECASE):
        return 0

    match = re.search(r"([\d,]+)\s+contributions?\b", text, re.IGNORECASE)
    if match:
        return int(match.group(1).replace(",", ""))

    # GitHub occasionally exposes a count directly in accessible markup.
    for attribute in ("data-count", "aria-label"):
        raw = cell.get(attribute)
        if not raw:
            continue
        direct_match = re.search(r"([\d,]+)", str(raw))
        if direct_match:
            return int(direct_match.group(1).replace(",", ""))

    return 0


def fetch_days() -> list[dict[str, int | str]]:
    response = build_session().get(URL, timeout=(10, 30))
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day[data-date]")
    if not cells:
        raise RuntimeError("GitHub contribution calendar cells were not found")

    by_date: dict[str, int] = {}
    for cell in cells:
        date_text = cell.get("data-date")
        if not date_text:
            continue
        try:
            dt.date.fromisoformat(date_text)
        except ValueError:
            continue
        by_date[date_text] = contribution_count(cell, soup)

    if not by_date:
        raise RuntimeError("GitHub returned a calendar with no valid dated cells")

    return [{"date": day, "count": by_date[day]} for day in sorted(by_date)]


def compute_current_streak(days: list[dict[str, int | str]]) -> tuple[int, str | None, str | None]:
    if not days:
        return 0, None, None

    index = len(days) - 1
    today = dt.datetime.now(dt.timezone.utc).date()
    last_date = dt.date.fromisoformat(str(days[index]["date"]))

    # A stale snapshot cannot represent a current streak.
    if last_date < today - dt.timedelta(days=1):
        return 0, None, None

    # A zero for the still-in-progress UTC day should not break yesterday's streak.
    if int(days[index]["count"]) == 0 and last_date >= today:
        index -= 1

    if index < 0 or int(days[index]["count"]) == 0:
        return 0, None, None

    end_index = index
    streak = 0
    expected = dt.date.fromisoformat(str(days[index]["date"]))
    while index >= 0:
        current_date = dt.date.fromisoformat(str(days[index]["date"]))
        if current_date != expected or int(days[index]["count"]) <= 0:
            break
        streak += 1
        expected -= dt.timedelta(days=1)
        index -= 1

    start_index = index + 1
    return streak, str(days[start_index]["date"]), str(days[end_index]["date"])


def compute_longest_streak(days: list[dict[str, int | str]]) -> tuple[int, str | None, str | None]:
    longest = run = 0
    longest_start = longest_end = None
    run_start = None
    previous_date: dt.date | None = None

    for item in days:
        current_date = dt.date.fromisoformat(str(item["date"]))
        is_consecutive = previous_date is None or current_date == previous_date + dt.timedelta(days=1)

        if int(item["count"]) > 0:
            if run == 0 or not is_consecutive:
                run = 1
                run_start = str(item["date"])
            else:
                run += 1
            if run > longest:
                longest = run
                longest_start = run_start
                longest_end = str(item["date"])
        else:
            run = 0
            run_start = None

        previous_date = current_date

    return longest, longest_start, longest_end


def build_data(days: list[dict[str, int | str]]) -> dict[str, Any]:
    if not days:
        raise ValueError("Cannot build contribution statistics without days")

    total = sum(int(item["count"]) for item in days)
    active_days = sum(1 for item in days if int(item["count"]) > 0)
    best = max(days, key=lambda item: int(item["count"]))
    current_length, current_start, current_end = compute_current_streak(days)
    longest_length, longest_start, longest_end = compute_longest_streak(days)

    monthly: dict[str, int] = {}
    for item in days:
        month = str(item["date"])[:7]
        monthly[month] = monthly.get(month, 0) + int(item["count"])

    return {
        "username": USERNAME,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active_days,
        "avg_per_active_day": round(total / active_days, 1) if active_days else 0,
        "current_streak": {
            "length": current_length,
            "start": current_start,
            "end": current_end,
        },
        "longest_streak": {
            "length": longest_length,
            "start": longest_start,
            "end": longest_end,
        },
        "best_day": {"date": best["date"], "count": int(best["count"])},
        "monthly": [{"month": month, "total": value} for month, value in sorted(monthly.items())],
        "days": days,
    }


def main() -> int:
    try:
        days = fetch_days()
        data = build_data(days)
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        print(f"error: could not refresh contributions for {USERNAME}: {exc}", file=sys.stderr)
        return 1

    print(
        f"wrote {OUT_PATH}: {data['total_contributions']} contributions, "
        f"current streak {data['current_streak']['length']}, "
        f"longest streak {data['longest_streak']['length']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
