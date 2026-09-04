"""
Generates a real skill radar chart from GitHub language stats
(bytes of code per language, aggregated across all public repos).

Run locally:
    GITHUB_TOKEN=xxx USERNAME=SakshamShandilya01 python3 skill_radar.py

In CI (GitHub Actions) GITHUB_TOKEN and USERNAME are read from env vars
automatically (see .github/workflows/skill-radar.yml).
"""

import os
import sys
import requests
import numpy as np
import matplotlib.pyplot as plt

USERNAME = os.environ.get("USERNAME", "SakshamShandilya01")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "assets/skill-radar.svg")
MAX_LANGUAGES = 8  # keep the radar readable

HEADERS = {"Accept": "application/vnd.github+json"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def get_repos(username):
    repos = []
    page = 1
    while True:
        resp = requests.get(
            f"https://api.github.com/users/{username}/repos",
            params={"per_page": 100, "page": page, "type": "owner"},
            headers=HEADERS,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    # skip forks — they inflate your language stats with someone else's code
    return [r for r in repos if not r.get("fork")]


def get_language_bytes(username, repo_name):
    resp = requests.get(
        f"https://api.github.com/repos/{username}/{repo_name}/languages",
        headers=HEADERS,
    )
    if resp.status_code != 200:
        return {}
    return resp.json()


def aggregate_languages(username):
    totals = {}
    for repo in get_repos(username):
        langs = get_language_bytes(username, repo["name"])
        for lang, byte_count in langs.items():
            totals[lang] = totals.get(lang, 0) + byte_count
    return totals


def render_radar(totals, output_path):
    if not totals:
        print("No language data found — skipping radar generation.")
        sys.exit(0)

    # keep top N languages by bytes, normalize to 0-100
    top = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:MAX_LANGUAGES]
    labels = [name for name, _ in top]
    values = [count for _, count in top]
    max_val = max(values)
    scaled = [v / max_val * 100 for v in values]

    # close the loop for the polygon
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    scaled += scaled[:1]
    angles += angles[:1]

    fig = plt.figure(figsize=(6, 6), facecolor="#0D1117")
    ax = fig.add_subplot(111, polar=True, facecolor="#0D1117")

    ax.plot(angles, scaled, color="#FF61D8", linewidth=2)
    ax.fill(angles, scaled, color="#B983FF", alpha=0.35)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, color="#c9d1d9", fontsize=12, fontfamily="monospace")
    ax.set_yticks([])
    ax.spines["polar"].set_color("#30363d")
    ax.grid(color="#30363d", linewidth=0.6)

    ax.set_title(
        f"{USERNAME} — language mix",
        color="#FF61D8",
        fontsize=13,
        fontfamily="monospace",
        pad=20,
    )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    plt.savefig(output_path, format="svg", facecolor="#0D1117", bbox_inches="tight")
    print(f"Saved radar to {output_path}")
    print("Languages plotted:", labels)


if __name__ == "__main__":
    totals = aggregate_languages(USERNAME)
    render_radar(totals, OUTPUT_PATH)
