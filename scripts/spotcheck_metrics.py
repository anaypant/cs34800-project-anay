"""Spot-check columns that decide whether a chart metric stays."""

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

pbp = pq.read_table(
    RAW / "pbp_2026.parquet",
    columns=[
        "season_type",
        "week",
        "qb_dropback",
        "xpass",
        "pass",
        "rush",
        "air_yards",
        "receiver_player_id",
        "drive_start_yard_line",
        "fixed_drive",
        "posteam",
    ],
).to_pandas()
reg = pbp[pbp.season_type == "REG"]
drops = reg[reg.qb_dropback == 1]
print("xpass on dropbacks", drops.xpass.notna().mean(), "n", len(drops))
print("drive start nonnull", reg.drive_start_yard_line.notna().mean())
print("air yards on pass attempts", reg.loc[reg["pass"] == 1, "air_yards"].notna().mean())

ftn = pq.read_table(
    RAW / "ftn_2026.parquet",
    columns=["nflverse_game_id", "nflverse_play_id", "is_contested_ball", "is_play_action", "is_motion", "is_rpo", "n_defense_box", "n_blitzers"],
).to_pandas()
print("ftn contested nonnull", ftn.is_contested_ball.notna().mean())
print("ftn play action nonnull", ftn.is_play_action.notna().mean())
print("ftn box nonnull", ftn.n_defense_box.notna().mean())

pfr_pass = pq.read_table(RAW / "pfr_pass_2026.parquet").to_pandas()
print("pfr pass rows", len(pfr_pass), "pressured null", pfr_pass.times_pressured.isna().mean(), "sum pressured", pfr_pass.times_pressured.sum())
print("bad throw null", pfr_pass.passing_bad_throw_pct.isna().mean())

pfr_def = pq.read_table(RAW / "pfr_def_2026.parquet").to_pandas()
print("def pressures null", pfr_def.def_pressures.isna().mean(), "missed tackle null", pfr_def.def_missed_tackles.isna().mean())
print("def targets null", pfr_def.def_targets.isna().mean(), "rating null", pfr_def.def_passer_rating_allowed.isna().mean())

players = pq.read_table(RAW / "player_2026.parquet").to_pandas()
print("fg rows", (players.fg_att.fillna(0) > 0).sum(), "punt rows", (players.pt_att.fillna(0) > 0).sum())
print("has pt_net", "pt_net_yards" in players.columns, "has passing_air", "passing_air_yards" in players.columns)
