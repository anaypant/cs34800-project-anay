"""Download public NFL files and report which chart metrics they can support through 2026 week 8."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
BASE = "https://github.com/nflverse/nflverse-data/releases/download"
UA = {"User-Agent": "cs348-metric-check"}


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        return
    print(f"get {dest.name}")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req) as response, dest.open("wb") as out:
        out.write(response.read())


def asset_sizes() -> None:
    req = urllib.request.Request(
        "https://api.github.com/repos/nflverse/nflverse-data/releases?per_page=100",
        headers=UA,
    )
    with urllib.request.urlopen(req) as response:
        releases = json.load(response)
    interesting = (
        "play_by_play_",
        "ftn_charting_",
        "stats_team_week_",
        "stats_player_week_",
        "advstats_week_",
        "ngs_",
        "snap_counts_",
        "roster_",
        "games.parquet",
        "qbr_week",
    )
    print("=== asset sizes ===")
    for release in releases:
        for asset in release["assets"]:
            name = asset["name"]
            if not any(token in name for token in interesting):
                continue
            if not any(year in name for year in ("2024", "2025", "2026", "games", "qbr")):
                continue
            if name.endswith((".parquet", ".csv.gz")):
                print(f"{asset['size']:10}  {release['tag_name']}/{name}")


def week_span(frame: pd.DataFrame, week_col: str, season_col: str = "season") -> str:
    if frame.empty:
        return "empty"
    seasons = sorted(frame[season_col].dropna().unique())
    bits = []
    for season in seasons:
        weeks = sorted(frame.loc[frame[season_col] == season, week_col].dropna().unique())
        if not weeks:
            continue
        bits.append(f"{int(season)} w{int(weeks[0])}-{int(weeks[-1])} n={len(weeks)}")
    return "; ".join(bits)


def main() -> None:
    asset_sizes()
    files = {
        "pbp_2026": f"{BASE}/pbp/play_by_play_2026.parquet",
        "ftn_2026": f"{BASE}/ftn_charting/ftn_charting_2026.parquet",
        "team_2026": f"{BASE}/stats_team/stats_team_week_2026.parquet",
        "player_2026": f"{BASE}/stats_player/stats_player_week_2026.parquet",
        "pfr_def_2026": f"{BASE}/pfr_advstats/advstats_week_def_2026.parquet",
        "pfr_pass_2026": f"{BASE}/pfr_advstats/advstats_week_pass_2026.parquet",
        "pfr_rush_2026": f"{BASE}/pfr_advstats/advstats_week_rush_2026.parquet",
        "pfr_rec_2026": f"{BASE}/pfr_advstats/advstats_week_rec_2026.parquet",
        "snap_2026": f"{BASE}/snap_counts/snap_counts_2026.parquet",
        "games": f"{BASE}/schedules/games.parquet",
        "qbr": f"{BASE}/espn_data/qbr_week_level.parquet",
    }
    paths = {}
    for key, url in files.items():
        dest = RAW / f"{key}.parquet"
        download(url, dest)
        paths[key] = dest

    pbp = pq.read_table(
        paths["pbp_2026"],
        columns=[
            "season",
            "week",
            "season_type",
            "game_id",
            "play_id",
            "posteam",
            "defteam",
            "play",
            "pass",
            "rush",
            "qb_dropback",
            "sack",
            "qb_hit",
            "xpass",
            "shotgun",
            "epa",
            "success",
            "down",
            "ydstogo",
            "yardline_100",
            "yards_gained",
            "run_location",
            "air_yards",
            "complete_pass",
            "passer_player_id",
            "rusher_player_id",
            "receiver_player_id",
            "wp",
            "drive",
            "fixed_drive",
            "third_down_converted",
            "fourth_down_converted",
        ],
    ).to_pandas()
    print("PBP 2026", week_span(pbp, "week"), "rows", len(pbp))
    reg = pbp[pbp.season_type == "REG"]
    print("  xpass nonnull", reg.xpass.notna().mean())
    print("  shotgun nonnull on plays", reg.loc[reg.play == 1, "shotgun"].notna().mean())
    print("  epa nonnull on plays", reg.loc[reg.play == 1, "epa"].notna().mean())
    print("  run_location on rushes", reg.loc[reg.rush == 1, "run_location"].notna().mean())

    ftn = pq.read_table(paths["ftn_2026"]).to_pandas()
    print("FTN 2026", week_span(ftn, "week"), "rows", len(ftn))
    drops = reg[reg.qb_dropback == 1][["game_id", "play_id", "week"]]
    merged = drops.merge(
        ftn,
        left_on=["game_id", "play_id"],
        right_on=["nflverse_game_id", "nflverse_play_id"],
        how="left",
    )
    print("  dropback chart rate", merged.n_blitzers.notna().mean())
    week8 = merged[merged.week_x <= 8]
    print("  through week 8 chart rate", week8.n_blitzers.notna().mean(), "dropbacks", len(week8))

    for key, week_col in (
        ("team_2026", "week"),
        ("player_2026", "week"),
        ("pfr_def_2026", "week"),
        ("pfr_pass_2026", "week"),
        ("pfr_rush_2026", "week"),
        ("pfr_rec_2026", "week"),
        ("snap_2026", "week"),
    ):
        frame = pq.read_table(paths[key]).to_pandas()
        print(key, week_span(frame, week_col), "rows", len(frame), "cols", len(frame.columns))

    games = pq.read_table(paths["games"]).to_pandas()
    g26 = games[(games.season == 2026) & (games.game_type == "REG")]
    played = g26[g26.home_score.notna()]
    print("GAMES 2026 REG played", week_span(played, "week"), "rows", len(played))

    qbr = pq.read_table(paths["qbr"]).to_pandas()
    q26 = qbr[qbr.season == 2026]
    print("QBR", week_span(q26, "game_week"), "rows", len(q26))

    players = pq.read_table(paths["player_2026"]).to_pandas()
    print("player cpoe nonnull among passers", players.loc[players.attempts.fillna(0) > 0, "passing_cpoe"].notna().mean())
    print("player target_share nonnull among targets", players.loc[players.targets.fillna(0) > 0, "target_share"].notna().mean())


if __name__ == "__main__":
    main()
