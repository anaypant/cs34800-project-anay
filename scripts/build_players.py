"""Build player-game facts and the player / roster dimensions."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from build_warehouse import SEASONS, attach_ftn, load_ftn, load_games, load_pbp, season_path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "warehouse"
GROUPS = {
    "QB": "QB",
    "RB": "RB",
    "FB": "RB",
    "HB": "RB",
    "WR": "WR",
    "TE": "TE",
    "DE": "DL",
    "DT": "DL",
    "NT": "DL",
    "DL": "DL",
    "EDGE": "DL",
    "LB": "LB",
    "ILB": "LB",
    "OLB": "LB",
    "MLB": "LB",
    "CB": "DB",
    "DB": "DB",
    "S": "DB",
    "FS": "DB",
    "SS": "DB",
    "SAF": "DB",
    "K": "K",
    "P": "P",
}


def group_of(position: object) -> str | None:
    if not isinstance(position, str) or position == "":
        return None
    return GROUPS.get(position.split("/")[0].upper())


def pbp_player_facts(plays: pd.DataFrame) -> pd.DataFrame:
    plays = plays.copy()
    plays["deep"] = plays.air_yards.ge(20) & (plays.pass_attempt == 1)
    plays["deep_cmp"] = plays.deep & (plays.complete_pass == 1)
    plays["contested_catch"] = plays.is_contested_ball & (plays.complete_pass == 1)
    plays["rz"] = plays.yardline_100.le(20)
    plays["short"] = plays.ydstogo.le(2) & (plays.rush_attempt == 1)
    plays["short_conv"] = plays.short & (plays.yards_gained >= plays.ydstogo)

    passer = plays[(plays.qb_dropback == 1) & plays.passer_player_id.notna()]
    passer_agg = passer.groupby(["game_id", "passer_player_id"], as_index=False).agg(
        pbp_dropbacks=("play_id", "size"),
        deep_att=("deep", "sum"),
        deep_cmp=("deep_cmp", "sum"),
        play_action_dropbacks=("is_play_action", "sum"),
        blitz_faced=("is_blitz", "sum"),
    )
    pa = passer[passer.is_play_action].groupby(["game_id", "passer_player_id"], as_index=False).agg(play_action_epa=("epa", "sum"))
    blitz = passer[passer.is_blitz].groupby(["game_id", "passer_player_id"], as_index=False).agg(blitz_epa=("epa", "sum"))
    passer_agg = passer_agg.merge(pa, on=["game_id", "passer_player_id"], how="left").merge(blitz, on=["game_id", "passer_player_id"], how="left")
    passer_agg = passer_agg.rename(columns={"passer_player_id": "player_id"})

    rushes = plays[(plays.rush_attempt == 1) & plays.rusher_player_id.notna()].copy()
    rushes["designed"] = rushes.qb_scramble != 1
    rush_agg = rushes.groupby(["game_id", "rusher_player_id"], as_index=False).agg(
        rush_success=("success", "sum"),
        rush_explosive=("yards_gained", lambda series: int(series.ge(10).sum())),
        stuffed=("yards_gained", lambda series: int(series.le(0).sum())),
        short_att=("short", "sum"),
        short_conv=("short_conv", "sum"),
        scramble_carries=("qb_scramble", "sum"),
    )
    designed = rushes[rushes.designed]
    designed_agg = designed.groupby(["game_id", "rusher_player_id"], as_index=False).agg(designed_carries=("play_id", "size"))
    light = designed[designed.light_box].groupby(["game_id", "rusher_player_id"], as_index=False).agg(light_carries=("play_id", "size"), light_yards=("yards_gained", "sum"))
    stacked = designed[designed.stacked_box].groupby(["game_id", "rusher_player_id"], as_index=False).agg(stacked_carries=("play_id", "size"), stacked_yards=("yards_gained", "sum"))
    scramble = rushes[rushes.qb_scramble == 1].groupby(["game_id", "rusher_player_id"], as_index=False).agg(scramble_yards=("yards_gained", "sum"))
    rush_agg = rush_agg.merge(designed_agg, on=["game_id", "rusher_player_id"], how="left")
    rush_agg = rush_agg.merge(light, on=["game_id", "rusher_player_id"], how="left")
    rush_agg = rush_agg.merge(stacked, on=["game_id", "rusher_player_id"], how="left")
    rush_agg = rush_agg.merge(scramble, on=["game_id", "rusher_player_id"], how="left")
    rush_agg = rush_agg.rename(columns={"rusher_player_id": "player_id"})

    targets = plays[(plays.pass_attempt == 1) & plays.receiver_player_id.notna()]
    rec_agg = targets.groupby(["game_id", "receiver_player_id"], as_index=False).agg(
        contested_targets=("is_contested_ball", "sum"),
        contested_catches=("contested_catch", "sum"),
        rec_explosive=("yards_gained", lambda series: int(series.ge(20).sum())),
    )
    rz = targets[targets.rz]
    rz_agg = rz.groupby(["game_id", "receiver_player_id"], as_index=False).agg(
        rz_targets=("play_id", "size"),
        rz_receptions=("complete_pass", "sum"),
        rz_tds=("pass_touchdown", "sum"),
    )
    rec_agg = rec_agg.merge(rz_agg, on=["game_id", "receiver_player_id"], how="left")
    rec_agg = rec_agg.rename(columns={"receiver_player_id": "player_id"})

    facts = passer_agg.merge(rush_agg, on=["game_id", "player_id"], how="outer").merge(rec_agg, on=["game_id", "player_id"], how="outer")
    return facts


def weekly_box(year: int, game_ids: set[str]) -> pd.DataFrame:
    frame = pq.read_table(season_path("player", year)).to_pandas()
    frame = frame[frame.game_id.isin(game_ids)].copy()
    keep = {
        "player_id": "player_id",
        "player_display_name": "full_name",
        "position": "position",
        "game_id": "game_id",
        "team": "team_abbr",
        "opponent_team": "opponent_abbr",
        "completions": "completions",
        "attempts": "pass_attempts",
        "passing_yards": "pass_yards",
        "passing_tds": "pass_tds",
        "passing_interceptions": "interceptions_thrown",
        "sacks_suffered": "sacks_taken",
        "passing_air_yards": "air_yards",
        "passing_yards_after_catch": "pass_yac",
        "passing_epa": "passing_epa",
        "passing_cpoe": "cpoe",
        "carries": "carries",
        "rushing_yards": "rush_yards",
        "rushing_tds": "rush_tds",
        "rushing_epa": "rushing_epa",
        "targets": "targets",
        "receptions": "receptions",
        "receiving_yards": "rec_yards",
        "receiving_tds": "rec_tds",
        "receiving_air_yards": "rec_air_yards",
        "receiving_yards_after_catch": "rec_yac",
        "receiving_epa": "receiving_epa",
        "def_tackles_solo": "tackles_solo",
        "def_tackle_assists": "tackle_assists",
        "def_tackles_for_loss": "tackles_for_loss",
        "def_sacks": "sacks",
        "def_qb_hits": "qb_hits",
        "def_interceptions": "interceptions",
        "def_pass_defended": "passes_defended",
        "fg_made": "fg_made",
        "fg_att": "fg_att",
        "fg_long": "fg_long",
        "fg_made_0_19": "fg_0_19",
        "fg_made_20_29": "fg_20_29",
        "fg_made_30_39": "fg_30_39",
        "fg_att_0_19": "fg_att_0_19",
        "pat_made": "pat_made",
        "pat_att": "pat_att",
        "pt_att": "punts",
        "pt_yards": "punt_yards",
        "pt_net_yards": "punt_net_yards",
        "pt_inside_20": "punts_inside_20",
    }
    # Attempt buckets are not separate columns. Made-by-distance is enough for makes;
    # attempts by distance are not in this file, so the UI uses overall fg_att.
    present = {source: target for source, target in keep.items() if source in frame.columns}
    out = frame[list(present)].rename(columns=present)
    out["fg_made_0_39"] = sum(pd.to_numeric(out[column], errors="coerce").fillna(0) for column in ("fg_0_19", "fg_20_29", "fg_30_39") if column in out.columns)
    out["fg_made_40_49"] = pd.to_numeric(frame["fg_made_40_49"], errors="coerce").fillna(0) if "fg_made_40_49" in frame.columns else 0
    out["fg_made_50"] = 0
    for column in ("fg_made_50_59", "fg_made_60_"):
        if column in frame.columns:
            out["fg_made_50"] = out["fg_made_50"] + pd.to_numeric(frame[column], errors="coerce").fillna(0)
    return out


def pfr_player_facts(year: int, roster_map: pd.DataFrame) -> pd.DataFrame:
    pieces = []
    passing = pq.read_table(season_path("pass", year)).to_pandas()
    pieces.append(passing.rename(columns={"pfr_player_id": "pfr_id", "team": "team_abbr"})[
        ["game_id", "pfr_id", "team_abbr", "times_pressured", "times_hurried", "times_hit", "times_blitzed", "passing_bad_throws"]
    ].rename(columns={"times_blitzed": "qb_times_blitzed", "times_hurried": "qb_hurries", "times_hit": "qb_hits_taken"}))
    rushing = pq.read_table(season_path("rush", year)).to_pandas()
    pieces.append(rushing.rename(columns={"pfr_player_id": "pfr_id", "team": "team_abbr"})[
        ["game_id", "pfr_id", "rushing_yards_before_contact", "rushing_yards_after_contact", "rushing_broken_tackles"]
    ].rename(columns={"rushing_yards_before_contact": "ybc", "rushing_yards_after_contact": "yac_contact", "rushing_broken_tackles": "broken_tackles"}))
    receiving = pq.read_table(season_path("rec", year)).to_pandas()
    pieces.append(receiving.rename(columns={"pfr_player_id": "pfr_id"})[
        ["game_id", "pfr_id", "receiving_drop"]
    ].rename(columns={"receiving_drop": "drops"}))
    defense = pq.read_table(season_path("def", year)).to_pandas()
    pieces.append(defense.rename(columns={"pfr_player_id": "pfr_id"})[
        ["game_id", "pfr_id", "def_targets", "def_completions_allowed", "def_yards_allowed", "def_receiving_td_allowed", "def_ints", "def_missed_tackles", "def_tackles_combined", "def_pressures", "def_times_hurried", "def_times_hitqb", "def_sacks", "def_times_blitzed"]
    ].rename(columns={
        "def_targets": "cov_targets",
        "def_completions_allowed": "cov_completions",
        "def_yards_allowed": "cov_yards",
        "def_receiving_td_allowed": "cov_tds",
        "def_ints": "cov_ints",
        "def_missed_tackles": "missed_tackles",
        "def_tackles_combined": "pfr_tackles",
        "def_pressures": "pressures",
        "def_times_hurried": "hurries",
        "def_times_hitqb": "pfr_qb_hits",
        "def_sacks": "pfr_sacks",
        "def_times_blitzed": "times_blitzed",
    }))
    merged = pieces[0]
    for piece in pieces[1:]:
        merged = merged.merge(piece, on=["game_id", "pfr_id"], how="outer")
    merged = merged.merge(roster_map, on="pfr_id", how="left")
    mapped = merged.dropna(subset=["player_id"])
    print(year, "pfr player rows", len(merged), "mapped", len(mapped), f"{len(mapped) / max(len(merged), 1):.3f}")
    return mapped.drop(columns=["pfr_id"])


def roster_map(year: int) -> pd.DataFrame:
    roster = pq.read_table(season_path("roster", year), columns=["gsis_id", "pfr_id", "team", "position", "full_name"]).to_pandas()
    roster = roster.dropna(subset=["gsis_id"])
    mapping = roster.dropna(subset=["pfr_id"])[["pfr_id", "gsis_id"]].drop_duplicates("pfr_id").rename(columns={"gsis_id": "player_id"})
    people = roster.sort_values("full_name").groupby("gsis_id", as_index=False).tail(1)
    people = people.rename(columns={"gsis_id": "player_id"})
    assignments = roster.groupby(["gsis_id", "team"], as_index=False).tail(1)
    assignments = assignments.rename(columns={"gsis_id": "player_id", "team": "team_abbr"})
    assignments["season"] = year
    return mapping, people, assignments[["season", "player_id", "team_abbr", "position"]]


def main() -> None:
    games = load_games()
    boxes = []
    facts = []
    pfrs = []
    people = []
    assignments = []
    for year in SEASONS:
        ids = set(games.loc[games.season == year, "game_id"])
        plays = attach_ftn(load_pbp(year, ids), load_ftn(year))
        facts.append(pbp_player_facts(plays))
        boxes.append(weekly_box(year, ids))
        mapping, persons, assigned = roster_map(year)
        people.append(persons)
        assignments.append(assigned)
        pfrs.append(pfr_player_facts(year, mapping))
        print(year, "weekly", len(boxes[-1]), "pbp players", len(facts[-1]))

    box = pd.concat(boxes, ignore_index=True)
    fact = pd.concat(facts, ignore_index=True)
    pfr = pd.concat(pfrs, ignore_index=True)
    pfr = pfr.groupby(["game_id", "player_id"], as_index=False).sum(numeric_only=True)
    player_game = box.merge(fact, on=["game_id", "player_id"], how="outer").merge(pfr, on=["game_id", "player_id"], how="left")
    player_game = player_game.dropna(subset=["player_id", "game_id"])
    player_game = player_game.drop_duplicates(["game_id", "player_id"])
    text_columns = {"player_id", "full_name", "position", "game_id", "team_abbr", "opponent_abbr"}
    for column in player_game.columns:
        if column not in text_columns:
            player_game[column] = pd.to_numeric(player_game[column], errors="coerce")
    player_game.to_parquet(OUT / "player_game.parquet", index=False)

    persons = pd.concat(people, ignore_index=True).drop_duplicates("player_id")
    named = box.dropna(subset=["full_name"]).drop_duplicates("player_id")[["player_id", "full_name", "position"]]
    persons = named.merge(persons[["player_id", "position"]], on="player_id", how="outer", suffixes=("", "_roster"))
    persons["position"] = persons.position.fillna(persons.position_roster)
    persons["position_group"] = persons.position.map(group_of)
    persons["full_name"] = persons.full_name.fillna(persons.player_id)
    persons[["player_id", "full_name", "position", "position_group"]].to_parquet(OUT / "players.parquet", index=False)

    roster = pd.concat(assignments, ignore_index=True).dropna(subset=["player_id", "team_abbr"])
    roster = roster.drop_duplicates(["season", "player_id", "team_abbr"])
    roster.to_parquet(OUT / "roster.parquet", index=False)
    print("player_game", len(player_game), "players", len(persons), "roster", len(roster))


if __name__ == "__main__":
    main()
