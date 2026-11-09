"""Build game-level NFL facts for 2024-2026 from the local nflverse files.

Regular-season rates are computed later in SQL. This script only stores counts
and sums so a rate is always a ratio of those columns.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "warehouse"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://github.com/nflverse/nflverse-data/releases/download"
SEASONS = (2024, 2025, 2026)
GAME_TYPES = {"REG", "WC", "DIV", "CON", "SB"}


def download(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 1000:
        return
    print("get", dest.name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "cs348-warehouse"})
    with urllib.request.urlopen(request) as response, dest.open("wb") as handle:
        handle.write(response.read())


def season_path(kind: str, year: int) -> Path:
    names = {
        "pbp": [RAW / f"pbp__play_by_play_{year}.parquet", RAW / f"pbp_{year}.parquet"],
        "ftn": [RAW / f"ftn_charting__ftn_charting_{year}.parquet", RAW / f"ftn_{year}.parquet"],
        "team": [RAW / f"stats_team__stats_team_week_{year}.parquet", RAW / f"team_{year}.parquet"],
        "player": [RAW / f"stats_player__stats_player_week_{year}.parquet", RAW / f"player_{year}.parquet"],
        "def": [RAW / f"pfr_advstats__advstats_week_def_{year}.parquet", RAW / f"pfr_def_{year}.parquet"],
        "pass": [RAW / f"pfr_advstats__advstats_week_pass_{year}.parquet", RAW / f"pfr_pass_{year}.parquet"],
        "rush": [RAW / f"pfr_advstats__advstats_week_rush_{year}.parquet", RAW / f"pfr_rush_{year}.parquet"],
        "rec": [RAW / f"pfr_advstats__advstats_week_rec_{year}.parquet", RAW / f"pfr_rec_{year}.parquet"],
        "roster": [RAW / f"rosters__roster_{year}.parquet", RAW / f"roster_{year}.parquet"],
    }
    for path in names[kind]:
        if path.exists():
            return path
    raise FileNotFoundError(kind + " " + str(year))


def own_yardline(value: object, posteam: object) -> float | None:
    if not isinstance(value, str) or not isinstance(posteam, str):
        return None
    parts = value.split()
    if len(parts) != 2:
        return None
    side, yards_text = parts
    try:
        yards = int(yards_text)
    except ValueError:
        return None
    if side == "50":
        return 50
    if side == posteam:
        return yards
    return 100 - yards


def num(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(0, index=frame.index, dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce").fillna(0)


def ensure_sources() -> None:
    download(f"{BASE}/teams/teams_colors_logos.parquet", RAW / "teams.parquet")
    download(f"{BASE}/rosters/roster_2026.parquet", RAW / "rosters__roster_2026.parquet")
    download(f"{BASE}/schedules/games.parquet", RAW / "games.parquet")
    download(f"{BASE}/espn_data/qbr_week_level.parquet", RAW / "qbr.parquet")


def load_games() -> pd.DataFrame:
    games = pq.read_table(
        RAW / "games.parquet",
        columns=["game_id", "season", "game_type", "week", "gameday", "home_team", "away_team", "home_score", "away_score"],
    ).to_pandas()
    games = games[games.season.isin(SEASONS) & games.game_type.isin(GAME_TYPES)]
    games = games[games.home_score.notna() & games.away_score.notna()].copy()
    games["week"] = games.week.astype(int)
    games["season"] = games.season.astype(int)
    games["gameday"] = pd.to_datetime(games.gameday).dt.date
    for column in ("home_score", "away_score"):
        games[column] = games[column].astype(int)
    return games


def load_pbp(year: int, game_ids: set[str]) -> pd.DataFrame:
    columns = [
        "game_id", "play_id", "season", "week", "season_type", "posteam", "defteam",
        "play", "pass", "rush", "qb_dropback", "sack", "qb_hit", "qb_scramble",
        "pass_attempt", "complete_pass", "rush_attempt", "interception",
        "passing_yards", "rushing_yards", "yards_gained", "epa", "success",
        "down", "ydstogo", "yardline_100", "air_yards", "xpass", "shotgun",
        "wp", "touchdown", "run_location", "fixed_drive", "drive_start_yard_line",
        "third_down_converted", "third_down_failed", "fourth_down_converted", "fourth_down_failed",
        "fumble_lost", "fumbled_1_team", "passer_player_id", "rusher_player_id",
        "receiver_player_id", "pass_touchdown", "rush_touchdown",
    ]
    frame = pq.read_table(season_path("pbp", year), columns=columns).to_pandas()
    frame = frame[frame.game_id.isin(game_ids)].copy()
    frame["play_id"] = pd.to_numeric(frame.play_id, errors="coerce")
    return frame


def load_ftn(year: int) -> pd.DataFrame:
    columns = [
        "nflverse_game_id", "nflverse_play_id", "n_blitzers", "n_pass_rushers",
        "is_play_action", "is_motion", "is_rpo", "is_no_huddle", "is_contested_ball", "n_defense_box",
    ]
    frame = pq.read_table(season_path("ftn", year), columns=columns).to_pandas()
    frame["nflverse_play_id"] = pd.to_numeric(frame.nflverse_play_id, errors="coerce")
    return frame


def attach_ftn(pbp: pd.DataFrame, ftn: pd.DataFrame) -> pd.DataFrame:
    merged = pbp.merge(
        ftn,
        left_on=["game_id", "play_id"],
        right_on=["nflverse_game_id", "nflverse_play_id"],
        how="left",
    )
    merged["charted"] = merged.n_blitzers.notna()
    merged["is_blitz"] = merged.n_blitzers.fillna(-1).gt(0)
    merged["rushers_4"] = merged.n_pass_rushers.eq(4)
    merged["rushers_5plus"] = merged.n_pass_rushers.ge(5)
    merged["light_box"] = merged.n_defense_box.le(6) & merged.n_defense_box.notna()
    merged["stacked_box"] = merged.n_defense_box.ge(8)
    for column in ("is_play_action", "is_motion", "is_rpo", "is_no_huddle", "is_contested_ball"):
        merged[column] = merged[column].fillna(False).astype(bool)
    return merged


def team_offense(plays: pd.DataFrame) -> pd.DataFrame:
    offense = plays[plays.posteam.notna() & (plays.play == 1)].copy()
    offense["early"] = offense["down"].isin([1, 2])
    offense["neutral"] = offense.wp.between(0.2, 0.8) & offense.early
    offense["explosive_pass_play"] = (offense["pass"] == 1) & (offense.sack != 1)
    offense["rz"] = offense.yardline_100.le(20)
    grouped = offense.groupby(["game_id", "posteam"], as_index=False).agg(
        plays=("play", "size"),
        pass_attempts=("pass_attempt", "sum"),
        completions=("complete_pass", "sum"),
        pass_yards=("passing_yards", "sum"),
        pass_tds=("pass_touchdown", "sum"),
        interceptions_thrown=("interception", "sum"),
        rush_attempts=("rush_attempt", "sum"),
        rush_yards=("rushing_yards", "sum"),
        rush_tds=("rush_touchdown", "sum"),
        epa=("epa", "sum"),
        success_plays=("success", "sum"),
        shotgun_plays=("shotgun", "sum"),
        third_conv=("third_down_converted", "sum"),
        third_fail=("third_down_failed", "sum"),
        fourth_conv=("fourth_down_converted", "sum"),
        fourth_fail=("fourth_down_failed", "sum"),
        rz_plays=("rz", "sum"),
        drives=("fixed_drive", "nunique"),
    )
    # The early_success lambda above is intentionally replaced below.
    early = offense[offense.early].groupby(["game_id", "posteam"], as_index=False).agg(early_success=("success", "sum"), early_plays=("play", "size"))
    neutral = offense[offense.neutral]
    neutral_agg = neutral.groupby(["game_id", "posteam"], as_index=False).agg(
        neutral_plays=("play", "size"),
        neutral_passes=("pass_attempt", "sum"),
        neutral_xpass=("xpass", "sum"),
        neutral_xpass_plays=("xpass", lambda series: series.notna().sum()),
    )
    expl = offense[offense.explosive_pass_play].groupby(["game_id", "posteam"], as_index=False).agg(
        expl_pass_plays=("play", "size"),
        expl_pass_15=("yards_gained", lambda series: series.ge(15).sum()),
        expl_pass_20=("yards_gained", lambda series: series.ge(20).sum()),
    )
    rush = offense[offense.rush_attempt == 1]
    expl_rush = rush.groupby(["game_id", "posteam"], as_index=False).agg(
        expl_rush_plays=("play", "size"),
        expl_rush=("yards_gained", lambda series: series.ge(10).sum()),
    )
    directions = []
    for label, side in (("left", "left"), ("mid", "middle"), ("right", "right")):
        side_plays = rush[rush.run_location == side]
        part = side_plays.groupby(["game_id", "posteam"], as_index=False).agg(
            **{f"run_{label}": ("play", "size"), f"epa_{label}": ("epa", "sum")}
        )
        directions.append(part)
    rz = offense[offense.rz]
    rz_agg = rz.groupby(["game_id", "posteam"], as_index=False).agg(
        rz_plays=("play", "size"),
        rz_tds=("touchdown", "sum"),
        rz_epa=("epa", "sum"),
    )
    fumbles = offense[(offense.fumble_lost == 1) & (offense.fumbled_1_team == offense.posteam)]
    fum = fumbles.groupby(["game_id", "posteam"], as_index=False).agg(fumbles_lost=("play", "size"))
    drops = plays[(plays.qb_dropback == 1) & plays.posteam.notna()]
    drop_agg = drops.groupby(["game_id", "posteam"], as_index=False).agg(
        dropbacks=("qb_dropback", "size"),
        sacks_taken=("sack", "sum"),
        pass_epa=("epa", "sum"),
    )
    rush_epa = offense[offense.rush_attempt == 1].groupby(["game_id", "posteam"], as_index=False).agg(rush_epa=("epa", "sum"))
    charted = drops[drops.charted]
    chart_agg = charted.groupby(["game_id", "posteam"], as_index=False).agg(
        charted_dropbacks_off=("play_id", "size"),
        play_action_dropbacks=("is_play_action", "sum"),
        rpo_dropbacks=("is_rpo", "sum"),
    )
    # epa vs blitz computed directly
    blitz = charted[charted.is_blitz]
    blitz_epa = blitz.groupby(["game_id", "posteam"], as_index=False).agg(epa_vs_blitz=("epa", "sum"), blitz_faced=("play_id", "size"))
    motion_base = offense[offense.charted]
    motion = motion_base.groupby(["game_id", "posteam"], as_index=False).agg(
        motion_charted=("play_id", "size"),
        motion_plays=("is_motion", "sum"),
        no_huddle_plays=("is_no_huddle", "sum"),
    )
    offense["own_start"] = [
        own_yardline(value, team) for value, team in zip(offense.drive_start_yard_line, offense.posteam)
    ]
    starts = offense.dropna(subset=["fixed_drive"]).groupby(["game_id", "posteam", "fixed_drive"], as_index=False)["own_start"].first()
    start_agg = starts.groupby(["game_id", "posteam"], as_index=False).agg(
        start_drives=("fixed_drive", "size"),
        start_yardline_sum=("own_start", "sum"),
    )
    pieces = [grouped.drop(columns=["rz_plays"]), early, neutral_agg, expl, expl_rush, rz_agg, fum, drop_agg, rush_epa, chart_agg, blitz_epa, motion, start_agg]
    pieces.extend(directions)
    out = pieces[0]
    for piece in pieces[1:]:
        out = out.merge(piece, on=["game_id", "posteam"], how="left")
    return out


def team_defense(plays: pd.DataFrame) -> pd.DataFrame:
    drops = plays[(plays.qb_dropback == 1) & plays.defteam.notna()]
    defense = drops.groupby(["game_id", "defteam"], as_index=False).agg(
        dropbacks_faced=("qb_dropback", "size"),
        sacks=("sack", "sum"),
        qb_hits=("qb_hit", "sum"),
        interceptions=("interception", "sum"),
        charted_dropbacks=("charted", "sum"),
        blitz_dropbacks=("is_blitz", "sum"),
        rushers_4=("rushers_4", "sum"),
        rushers_5plus=("rushers_5plus", "sum"),
    )
    rushes = plays[(plays.rush_attempt == 1) & plays.defteam.notna()]
    stuffs = rushes[rushes.yards_gained <= 0].groupby(["game_id", "defteam"], as_index=False).agg(stuffs=("play_id", "size"))
    rush_faced = rushes.groupby(["game_id", "defteam"], as_index=False).agg(rushes_faced=("play_id", "size"))
    out = defense.merge(stuffs, on=["game_id", "defteam"], how="left").merge(rush_faced, on=["game_id", "defteam"], how="left")
    return out


def build_team_games(games: pd.DataFrame) -> pd.DataFrame:
    frames = []
    xpass_on_rushes = []
    for year in SEASONS:
        ids = set(games.loc[games.season == year, "game_id"])
        plays = attach_ftn(load_pbp(year, ids), load_ftn(year))
        rushes = plays[(plays.rush_attempt == 1)]
        xpass_on_rushes.append(rushes.xpass.notna().mean() if len(rushes) else 0)
        offense = team_offense(plays).rename(columns={"posteam": "team_abbr"})
        defense = team_defense(plays).rename(columns={"defteam": "team_abbr"})
        both = offense.merge(defense, on=["game_id", "team_abbr"], how="outer")
        frames.append(both)
        print(year, "team rows", len(both), "rush xpass coverage", round(xpass_on_rushes[-1], 3))
    facts = pd.concat(frames, ignore_index=True)
    home = games.rename(columns={"home_team": "team_abbr", "away_team": "opponent_abbr"})
    home["is_home"] = True
    away = games.rename(columns={"away_team": "team_abbr", "home_team": "opponent_abbr"})
    away["is_home"] = False
    skeleton = pd.concat([
        home[["game_id", "season", "week", "game_type", "gameday", "team_abbr", "opponent_abbr", "is_home"]],
        away[["game_id", "season", "week", "game_type", "gameday", "team_abbr", "opponent_abbr", "is_home"]],
    ], ignore_index=True)
    out = skeleton.merge(facts, on=["game_id", "team_abbr"], how="left")
    return out


def add_team_supplements(team_games: pd.DataFrame) -> pd.DataFrame:
    weekly = []
    pfr_pass = []
    pfr_rush = []
    pfr_def = []
    for year in SEASONS:
        week = pq.read_table(season_path("team", year)).to_pandas()
        week = week[week.game_id.isin(team_games.game_id)]
        weekly.append(week[["game_id", "team", "penalties", "penalty_yards", "fg_made", "fg_att", "pat_made", "pat_att", "pt_att", "pt_yards", "pt_net_yards", "pt_inside_20", "punt_returns", "punt_return_yards", "kickoff_returns", "kickoff_return_yards"]].rename(columns={"team": "team_abbr", "pt_att": "punts", "punt_returns": "punt_returns", "kickoff_returns": "kick_returns"}))
        passed = pq.read_table(season_path("pass", year)).to_pandas()
        pfr_pass.append(passed.groupby(["game_id", "team"], as_index=False)[["times_pressured", "times_hurried", "times_hit"]].sum().rename(columns={"team": "team_abbr"}))
        rushed = pq.read_table(season_path("rush", year)).to_pandas()
        pfr_rush.append(rushed.groupby(["game_id", "team"], as_index=False)[["rushing_yards_before_contact", "rushing_yards_after_contact"]].sum().rename(columns={"team": "team_abbr", "rushing_yards_before_contact": "ybc", "rushing_yards_after_contact": "yac_contact"}))
        defended = pq.read_table(season_path("def", year)).to_pandas()
        pfr_def.append(defended.groupby(["game_id", "team"], as_index=False)[["def_missed_tackles", "def_tackles_combined", "def_pressures", "def_times_hurried"]].sum().rename(columns={"team": "team_abbr", "def_missed_tackles": "missed_tackles", "def_tackles_combined": "tackle_credits", "def_pressures": "pressure_credits", "def_times_hurried": "hurry_credits"}))
    supplements = pd.concat(weekly, ignore_index=True)
    for frame in (pd.concat(pfr_pass, ignore_index=True), pd.concat(pfr_rush, ignore_index=True), pd.concat(pfr_def, ignore_index=True)):
        supplements = supplements.merge(frame, on=["game_id", "team_abbr"], how="outer")
    out = team_games.merge(supplements, on=["game_id", "team_abbr"], how="left")
    count_columns = [column for column in out.columns if column not in {"game_id", "season", "week", "game_type", "gameday", "team_abbr", "opponent_abbr", "is_home"}]
    for column in count_columns:
        out[column] = pd.to_numeric(out[column], errors="coerce").fillna(0)
    return out


def main() -> None:
    ensure_sources()
    games = load_games()
    print("games", len(games), "2026 reg", ((games.season == 2026) & (games.game_type == "REG")).sum())
    team_games = add_team_supplements(build_team_games(games))
    print(team_games.head(2).to_string())
    print("team_game", len(team_games), "cols", len(team_games.columns))
    reg = team_games[team_games.game_type == "REG"]
    for year in SEASONS:
        part = reg[reg.season == year]
        drops = part.dropbacks_faced.sum()
        sacks = part.sacks.sum()
        blitz = part.blitz_dropbacks.sum()
        charted = part.charted_dropbacks.sum()
        print(year, "sack", round(sacks / drops, 3) if drops else None, "blitz", round(blitz / charted, 3) if charted else None, "teams", part.team_abbr.nunique(), "dropbacks", int(drops))
    team_games.to_parquet(OUT / "team_game.parquet", index=False)
    games.to_parquet(OUT / "games.parquet", index=False)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
