"""Pull 2024 and 2025 source files into data/raw. 2026 is already there."""

import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
BASE = "https://github.com/nflverse/nflverse-data/releases/download"
UA = {"User-Agent": "cs348-metric-check"}
FILES = []
for year in (2024, 2025):
    FILES.extend(
        [
            f"pbp/play_by_play_{year}.parquet",
            f"ftn_charting/ftn_charting_{year}.parquet",
            f"stats_team/stats_team_week_{year}.parquet",
            f"stats_player/stats_player_week_{year}.parquet",
            f"pfr_advstats/advstats_week_def_{year}.parquet",
            f"pfr_advstats/advstats_week_pass_{year}.parquet",
            f"pfr_advstats/advstats_week_rush_{year}.parquet",
            f"pfr_advstats/advstats_week_rec_{year}.parquet",
            f"snap_counts/snap_counts_{year}.parquet",
            f"rosters/roster_{year}.parquet",
        ]
    )

for relative in FILES:
    dest = RAW / relative.replace("/", "__")
    if dest.exists() and dest.stat().st_size > 1000:
        print("have", dest.name)
        continue
    print("get", relative)
    request = urllib.request.Request(f"{BASE}/{relative}", headers=UA)
    with urllib.request.urlopen(request) as response, dest.open("wb") as out:
        out.write(response.read())
    print(" ", dest.stat().st_size)
