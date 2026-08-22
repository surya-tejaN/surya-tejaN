#!/usr/bin/env python3
"""
fetch_contributions.py
Scrapes the public (no-token) contribution calendar fragment GitHub serves at
https://github.com/users/<username>/contributions and writes data/contributions.json
with the raw daily counts plus a few derived stats used by the info card / heatmap.
"""
import json
import os
import re
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME", "surya-tejaN")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")


def fetch_html(username: str) -> str:
    resp = requests.get(
        f"https://github.com/users/{username}/contributions",
        headers={"User-Agent": "profile-readme-bot"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.text


def parse(html: str):
    soup = BeautifulSoup(html, "html.parser")

    total_match = re.search(r"([\d,]+)\s*\n?\s*contributions?\s+in the last year", html)
    total = int(total_match.group(1).replace(",", "")) if total_match else None

    days = []
    for td in soup.select("td[data-date]"):
        date_str = td.get("data-date")
        level = int(td.get("data-level", 0))
        tooltip_id = td.get("id")
        count = 0
        if tooltip_id:
            tip = soup.select_one(f'[for="{tooltip_id}"]')
            if tip:
                text = tip.get_text(strip=True)
                m = re.match(r"([\d,]+)\s+contributions?", text)
                if m:
                    count = int(m.group(1).replace(",", ""))
                elif text.lower().startswith("no contributions"):
                    count = 0
        days.append({"date": date_str, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])
    return total, days


def derive_stats(days):
    counts = [d["count"] for d in days]
    total = sum(counts)

    # current streak (walking back from most recent day with data)
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    # longest streak
    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    best_day = max(days, key=lambda d: d["count"]) if days else None

    active_days = sum(1 for d in days if d["count"] > 0)

    monthly = {}
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly[month_key] = monthly.get(month_key, 0) + d["count"]

    return {
        "total_computed": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "active_days": active_days,
        "monthly": monthly,
    }


def main():
    username = USERNAME
    print(f"Fetching contributions for {username}...")
    html = fetch_html(username)
    total, days = parse(html)
    stats = derive_stats(days)

    payload = {
        "username": username,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_from_page": total,
        "days": days,
        "stats": stats,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {OUT_PATH}: {len(days)} days, total={total}, "
          f"current_streak={stats['current_streak']}, longest_streak={stats['longest_streak']}")


if __name__ == "__main__":
    sys.exit(main())
