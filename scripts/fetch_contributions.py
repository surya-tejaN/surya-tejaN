#!/usr/bin/env python3
"""
fetch_contributions.py
Fetches contribution calendar data for the profile heatmap.

Uses GitHub GraphQL (viewer) when GH_TOKEN / GITHUB_TOKEN is set — includes
private + org contributions. Falls back to the public contributions page scrape.
"""
import json
import os
import re
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME", "surya-tejaN")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")
GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
query {
  viewer {
    login
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def fetch_graphql(token: str, username: str):
    resp = requests.post(
        GRAPHQL_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"query": QUERY},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])

    viewer = payload["data"]["viewer"]
    if viewer["login"].lower() != username.lower():
        raise RuntimeError(
            f"Token user {viewer['login']} does not match GH_USERNAME {username}"
        )

    calendar = viewer["contributionsCollection"]["contributionCalendar"]
    total = calendar["totalContributions"]
    days = []
    for week in calendar["weeks"]:
        for day in week["contributionDays"]:
            count = day["contributionCount"]
            days.append(
                {
                    "date": day["date"],
                    "count": count,
                    "level": min(4, count) if count else 0,
                }
            )

    days.sort(key=lambda d: d["date"])
    return total, days, "graphql_private"


def fetch_html(username: str) -> str:
    resp = requests.get(
        f"https://github.com/users/{username}/contributions",
        headers={"User-Agent": "profile-readme-bot"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.text


def parse_public(html: str):
    total_match = re.search(r"([\d,]+)\s*\n?\s*contributions?\s+in the last year", html)
    total = int(total_match.group(1).replace(",", "")) if total_match else None

    soup = BeautifulSoup(html, "html.parser")
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
    return total, days, "public_scrape"


def derive_stats(days):
    counts = [d["count"] for d in days]
    total = sum(counts)

    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

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
        month_key = d["date"][:7]
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
    pat = os.environ.get("GH_CONTRIBUTIONS_PAT")
    source = "public_scrape"

    print(f"Fetching contributions for {username}...")
    if pat:
        try:
            total, days, source = fetch_graphql(pat, username)
            print(f"GraphQL via PAT (private included): {total} contributions")
        except Exception as exc:
            print(f"GraphQL with GH_CONTRIBUTIONS_PAT failed ({exc}), falling back to public scrape")
            html = fetch_html(username)
            total, days, source = parse_public(html)
    else:
        print("GH_CONTRIBUTIONS_PAT not set — using public scrape only")
        html = fetch_html(username)
        total, days, source = parse_public(html)

    stats = derive_stats(days)
    payload = {
        "username": username,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source": source,
        "total_from_page": total,
        "days": days,
        "stats": stats,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print(
        f"Wrote {OUT_PATH}: {len(days)} days, total={total}, "
        f"current_streak={stats['current_streak']}, longest_streak={stats['longest_streak']}"
    )


if __name__ == "__main__":
    sys.exit(main())
