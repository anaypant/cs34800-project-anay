"""Write db/schema.sql from the warehouse column lists."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "db" / "schema.sql"

TEAM_GAME = """
game_id season week game_type gameday team_abbr opponent_abbr is_home plays
pass_attempts completions pass_yards pass_tds interceptions_thrown rush_attempts
rush_yards rush_tds epa success_plays shotgun_plays third_conv third_fail
fourth_conv fourth_fail drives early_success early_plays neutral_plays
neutral_passes neutral_xpass neutral_xpass_plays expl_pass_plays expl_pass_15
expl_pass_20 expl_rush_plays expl_rush rz_plays rz_tds rz_epa fumbles_lost
dropbacks sacks_taken pass_epa rush_epa charted_dropbacks_off play_action_dropbacks
rpo_dropbacks epa_vs_blitz blitz_faced motion_charted motion_plays no_huddle_plays
start_drives start_yardline_sum run_left epa_left run_mid epa_mid run_right
epa_right dropbacks_faced sacks qb_hits interceptions charted_dropbacks
blitz_dropbacks rushers_4 rushers_5plus stuffs rushes_faced penalties penalty_yards
fg_made fg_att pat_made pat_att punts pt_yards pt_net_yards pt_inside_20
punt_returns punt_return_yards kick_returns kickoff_return_yards times_pressured
times_hurried times_hit ybc yac_contact missed_tackles tackle_credits
pressure_credits hurry_credits
""".split()

PLAYER_GAME = """
player_id full_name position game_id team_abbr opponent_abbr completions
pass_attempts pass_yards pass_tds interceptions_thrown sacks_taken air_yards
pass_yac passing_epa cpoe carries rush_yards rush_tds rushing_epa targets
receptions rec_yards rec_tds rec_air_yards rec_yac receiving_epa tackles_solo
tackle_assists tackles_for_loss sacks qb_hits interceptions passes_defended
fg_made fg_att fg_long fg_0_19 fg_20_29 fg_30_39 pat_made pat_att punts
punt_yards punt_net_yards punts_inside_20 fg_made_0_39 fg_made_40_49 fg_made_50
pbp_dropbacks deep_att deep_cmp play_action_dropbacks blitz_faced play_action_epa
blitz_epa rush_success rush_explosive stuffed short_att short_conv scramble_carries
designed_carries light_carries light_yards stacked_carries stacked_yards
scramble_yards contested_targets contested_catches rec_explosive rz_targets
rz_receptions rz_tds times_pressured qb_hurries qb_hits_taken qb_times_blitzed
passing_bad_throws ybc yac_contact broken_tackles drops cov_targets
cov_completions cov_yards cov_tds cov_ints missed_tackles pfr_tackles pressures
hurries pfr_qb_hits pfr_sacks times_blitzed qbr_total qb_plays
""".split()


def sql_type(name: str) -> str:
    if name in {
        "game_id",
        "team_abbr",
        "opponent_abbr",
        "player_id",
        "full_name",
        "position",
        "game_type",
    }:
        return "text"
    if name in {"season", "week"}:
        return "integer"
    if name == "gameday":
        return "date"
    if name == "is_home":
        return "boolean"
    return "double precision"


def fact_table(name: str, columns: list[str], pk: str, fks: list[str], required: set[str]) -> str:
    lines = []
    for column in columns:
        null = " not null" if column in required else ""
        lines.append(f"  {column} {sql_type(column)}{null}")
    body = ",\n".join(lines + [pk, *fks])
    return f"create table {name} (\n{body}\n);\n"


VIEWS = r"""
create or replace function passer_rating(
  attempts double precision,
  completions double precision,
  yards double precision,
  touchdowns double precision,
  interceptions double precision
) returns double precision
language sql
immutable
set search_path = public
as $$
  select case
    when attempts is null or attempts <= 0 then null
    else (
      least(greatest((completions / attempts - 0.3) * 5, 0), 2.375)
      + least(greatest((yards / attempts - 3) * 0.25, 0), 2.375)
      + least(greatest((touchdowns / attempts) * 20, 0), 2.375)
      + least(greatest(2.375 - (interceptions / attempts) * 25, 0), 2.375)
    ) / 6.0 * 100
  end;
$$;

create or replace view v_team_reg
with (security_invoker = true) as
with reg as (
  select t.*
  from team_game t
  join games g on g.game_id = t.game_id
  where g.game_type = 'REG'
),
record as (
  select
    g.season,
    t.team_abbr,
    count(*)::integer as games,
    sum(case
      when g.home_score = g.away_score then 0
      when t.is_home and g.home_score > g.away_score then 1
      when not t.is_home and g.away_score > g.home_score then 1
      else 0
    end)::integer as wins,
    sum(case when g.home_score = g.away_score then 1 else 0 end)::integer as ties,
    sum(case when t.is_home then g.home_score else g.away_score end)::integer as points_for,
    sum(case when t.is_home then g.away_score else g.home_score end)::integer as points_against
  from team_game t
  join games g on g.game_id = t.game_id
  where g.game_type = 'REG'
  group by g.season, t.team_abbr
),
winpct as (
  select
    season,
    team_abbr,
    ((wins + 0.5 * ties) / nullif(games, 0))::double precision as win_pct
  from record
),
offense as (
  select
    season,
    team_abbr,
    sum(plays) as plays,
    sum(epa) as epa,
    sum(epa) / nullif(sum(plays), 0) as epa_per_play,
    sum(success_plays) / nullif(sum(plays), 0) as success_rate,
    sum(pass_yards) as pass_yards,
    sum(rush_yards) as rush_yards,
    sum(pass_yards) / nullif(sum(pass_attempts), 0) as yards_per_attempt,
    sum(rush_yards) / nullif(sum(rush_attempts), 0) as yards_per_carry,
    sum(pass_epa) / nullif(sum(dropbacks), 0) as pass_epa_per_dropback,
    sum(rush_epa) / nullif(sum(rush_attempts), 0) as rush_epa_per_carry,
    sum(neutral_passes) / nullif(sum(neutral_plays), 0)
      - sum(neutral_xpass) / nullif(sum(neutral_xpass_plays), 0) as proe,
    sum(expl_pass_20) / nullif(sum(expl_pass_plays), 0) as expl_pass_rate,
    sum(expl_rush) / nullif(sum(expl_rush_plays), 0) as expl_rush_rate,
    sum(early_success) / nullif(sum(early_plays), 0) as early_success_rate,
    sum(third_conv) / nullif(sum(third_conv) + sum(third_fail), 0) as third_down_rate,
    sum(fourth_conv) / nullif(sum(fourth_conv) + sum(fourth_fail), 0) as fourth_down_rate,
    sum(rz_tds) / nullif(sum(rz_plays), 0) as rz_td_rate,
    sum(shotgun_plays) / nullif(sum(plays), 0) as shotgun_rate,
    sum(sacks_taken) / nullif(sum(dropbacks), 0) as sack_rate_allowed,
    sum(times_pressured) / nullif(sum(dropbacks), 0) as pressure_rate_allowed,
    sum(play_action_dropbacks) / nullif(sum(charted_dropbacks_off), 0) as play_action_rate,
    sum(rpo_dropbacks) / nullif(sum(charted_dropbacks_off), 0) as rpo_rate,
    sum(motion_plays) / nullif(sum(motion_charted), 0) as motion_rate,
    sum(no_huddle_plays) / nullif(sum(motion_charted), 0) as no_huddle_rate,
    sum(start_yardline_sum) / nullif(sum(start_drives), 0) as start_yardline,
    sum(ybc) / nullif(sum(rush_attempts), 0) as ybc_per_carry,
    sum(fg_made) / nullif(sum(fg_att), 0) as fg_pct,
    sum(pt_net_yards) / nullif(sum(punts), 0) as net_punt,
    sum(pt_inside_20) / nullif(sum(punts), 0) as punt_inside_20_rate,
    sum(penalties) as penalties,
    sum(penalty_yards) as penalty_yards
  from reg
  group by season, team_abbr
),
defense as (
  select
    me.season,
    me.team_abbr,
    sum(opp.epa) / nullif(sum(opp.plays), 0) as epa_per_play_allowed,
    sum(opp.success_plays) / nullif(sum(opp.plays), 0) as success_rate_allowed,
    sum(opp.pass_yards) as pass_yards_allowed,
    sum(opp.rush_yards) as rush_yards_allowed,
    sum(me.sacks) / nullif(sum(me.dropbacks_faced), 0) as sack_rate,
    sum(me.qb_hits) / nullif(sum(me.dropbacks_faced), 0) as qb_hit_rate,
    sum(me.blitz_dropbacks) / nullif(sum(me.charted_dropbacks), 0) as blitz_rate,
    sum(me.rushers_5plus) / nullif(sum(me.charted_dropbacks), 0) as five_plus_rusher_rate,
    sum(opp.times_pressured) / nullif(sum(opp.dropbacks), 0) as pressure_rate,
    sum(me.stuffs) / nullif(sum(me.rushes_faced), 0) as stuff_rate,
    sum(me.interceptions) + sum(opp.fumbles_lost) as takeaways,
    sum(me.missed_tackles) as missed_tackles
  from reg me
  join reg opp
    on opp.game_id = me.game_id
   and opp.team_abbr = me.opponent_abbr
  group by me.season, me.team_abbr
),
sos as (
  select
    me.season,
    me.team_abbr,
    avg(w.win_pct) as sos
  from reg me
  join winpct w
    on w.season = me.season
   and w.team_abbr = me.opponent_abbr
  group by me.season, me.team_abbr
)
select
  o.season,
  o.team_abbr,
  tm.team_name,
  tm.team_conf,
  tm.team_division,
  tm.team_color,
  tm.team_logo_espn,
  r.games,
  r.wins,
  (r.games - r.wins - r.ties) as losses,
  r.ties,
  ((r.wins + 0.5 * r.ties) / nullif(r.games, 0))::double precision as win_pct,
  r.points_for,
  r.points_against,
  (r.points_for - r.points_against) as point_diff,
  r.points_for::double precision / nullif(r.games, 0) as points_per_game,
  s.sos,
  o.plays,
  o.epa,
  o.epa_per_play,
  o.success_rate,
  o.pass_yards,
  o.rush_yards,
  o.yards_per_attempt,
  o.yards_per_carry,
  o.pass_epa_per_dropback,
  o.rush_epa_per_carry,
  o.proe,
  o.expl_pass_rate,
  o.expl_rush_rate,
  o.early_success_rate,
  o.third_down_rate,
  o.fourth_down_rate,
  o.rz_td_rate,
  o.shotgun_rate,
  o.sack_rate_allowed,
  o.pressure_rate_allowed,
  o.play_action_rate,
  o.rpo_rate,
  o.motion_rate,
  o.no_huddle_rate,
  o.start_yardline,
  o.ybc_per_carry,
  o.fg_pct,
  o.net_punt,
  o.punt_inside_20_rate,
  o.penalties,
  o.penalty_yards,
  d.epa_per_play_allowed,
  d.success_rate_allowed,
  d.pass_yards_allowed,
  d.rush_yards_allowed,
  d.sack_rate,
  d.qb_hit_rate,
  d.blitz_rate,
  d.five_plus_rusher_rate,
  d.pressure_rate,
  d.stuff_rate,
  d.takeaways,
  d.missed_tackles
from offense o
join defense d on d.season = o.season and d.team_abbr = o.team_abbr
join record r on r.season = o.season and r.team_abbr = o.team_abbr
join sos s on s.season = o.season and s.team_abbr = o.team_abbr
join teams tm on tm.team_abbr = o.team_abbr;

create or replace view v_player_reg
with (security_invoker = true) as
select
  g.season,
  pg.team_abbr,
  pg.player_id,
  p.full_name,
  p.position,
  p.position_group,
  count(*)::integer as games,
  sum(coalesce(pg.pass_attempts, 0)) as pass_attempts,
  sum(coalesce(pg.completions, 0)) as completions,
  sum(coalesce(pg.pass_yards, 0)) as pass_yards,
  sum(coalesce(pg.pass_tds, 0)) as pass_tds,
  sum(coalesce(pg.interceptions_thrown, 0)) as interceptions_thrown,
  passer_rating(
    sum(coalesce(pg.pass_attempts, 0)),
    sum(coalesce(pg.completions, 0)),
    sum(coalesce(pg.pass_yards, 0)),
    sum(coalesce(pg.pass_tds, 0)),
    sum(coalesce(pg.interceptions_thrown, 0))
  ) as passer_rating,
  sum(pg.passing_epa) as passing_epa,
  sum(pg.passing_epa) / nullif(sum(pg.pbp_dropbacks), 0) as epa_per_dropback,
  sum(pg.cpoe * pg.pass_attempts) filter (where pg.cpoe is not null)
    / nullif(sum(pg.pass_attempts) filter (where pg.cpoe is not null), 0) as cpoe,
  sum(pg.qbr_total * pg.qb_plays) filter (where pg.qbr_total is not null)
    / nullif(sum(pg.qb_plays) filter (where pg.qbr_total is not null), 0) as qbr,
  sum(coalesce(pg.sacks_taken, 0)) / nullif(sum(pg.pbp_dropbacks), 0) as sack_rate,
  sum(pg.times_pressured) / nullif(sum(pg.pbp_dropbacks), 0) as pressure_rate,
  sum(pg.passing_bad_throws) / nullif(sum(pg.pass_attempts), 0) as bad_throw_rate,
  sum(pg.deep_cmp) / nullif(sum(pg.deep_att), 0) as deep_completion_rate,
  sum(pg.deep_att) as deep_att,
  sum(pg.play_action_epa) / nullif(sum(pg.play_action_dropbacks), 0) as play_action_epa,
  sum(pg.blitz_epa) / nullif(sum(pg.blitz_faced), 0) as blitz_epa,
  sum(coalesce(pg.carries, 0)) as carries,
  sum(coalesce(pg.rush_yards, 0)) as rush_yards,
  sum(coalesce(pg.rush_tds, 0)) as rush_tds,
  sum(pg.rushing_epa) as rushing_epa,
  sum(pg.rushing_epa) / nullif(sum(pg.carries), 0) as rush_epa_per_carry,
  sum(pg.rush_yards) / nullif(sum(pg.carries), 0) as yards_per_carry,
  sum(pg.rush_success) / nullif(sum(coalesce(pg.designed_carries, 0) + coalesce(pg.scramble_carries, 0)), 0) as rush_success_rate,
  sum(pg.rush_explosive) / nullif(sum(coalesce(pg.designed_carries, 0) + coalesce(pg.scramble_carries, 0)), 0) as explosive_rush_rate,
  sum(pg.stuffed) / nullif(sum(coalesce(pg.designed_carries, 0) + coalesce(pg.scramble_carries, 0)), 0) as stuff_rate,
  sum(pg.ybc) / nullif(sum(pg.carries), 0) as ybc_per_carry,
  sum(pg.yac_contact) / nullif(sum(pg.carries), 0) as yac_per_carry,
  sum(pg.broken_tackles) as broken_tackles,
  sum(pg.scramble_carries) as scramble_carries,
  sum(pg.scramble_yards) as scramble_yards,
  sum(pg.light_yards) / nullif(sum(pg.light_carries), 0) as light_box_ypc,
  sum(pg.stacked_yards) / nullif(sum(pg.stacked_carries), 0) as stacked_box_ypc,
  sum(pg.short_conv) / nullif(sum(pg.short_att), 0) as short_yardage_rate,
  sum(coalesce(pg.targets, 0)) as targets,
  sum(coalesce(pg.receptions, 0)) as receptions,
  sum(coalesce(pg.rec_yards, 0)) as rec_yards,
  sum(coalesce(pg.rec_tds, 0)) as rec_tds,
  sum(pg.receiving_epa) as receiving_epa,
  sum(pg.receiving_epa) / nullif(sum(pg.targets), 0) as rec_epa_per_target,
  sum(pg.rec_yards) / nullif(sum(pg.targets), 0) as yards_per_target,
  sum(pg.receptions) / nullif(sum(pg.targets), 0) as catch_rate,
  sum(pg.rec_yac) / nullif(sum(pg.receptions), 0) as yac_per_reception,
  sum(pg.drops) / nullif(sum(pg.targets), 0) as drop_rate,
  sum(pg.contested_catches) / nullif(sum(pg.contested_targets), 0) as contested_catch_rate,
  sum(pg.rec_explosive) / nullif(sum(pg.targets), 0) as explosive_rec_rate,
  sum(pg.rz_tds) / nullif(sum(pg.rz_targets), 0) as rz_td_rate,
  sum(coalesce(pg.tackles_solo, 0) + coalesce(pg.tackle_assists, 0)) as tackles,
  sum(pg.tackles_for_loss) as tackles_for_loss,
  sum(pg.sacks) as sacks,
  sum(pg.qb_hits) as qb_hits,
  sum(pg.interceptions) as interceptions,
  sum(pg.passes_defended) as passes_defended,
  sum(pg.missed_tackles) as missed_tackles,
  sum(pg.pressures) as pressures,
  sum(pg.hurries) as hurries,
  sum(pg.cov_targets) as cov_targets,
  sum(pg.cov_completions) / nullif(sum(pg.cov_targets), 0) as completion_rate_allowed,
  sum(pg.cov_yards) / nullif(sum(pg.cov_targets), 0) as yards_per_target_allowed,
  passer_rating(
    sum(pg.cov_targets),
    sum(pg.cov_completions),
    sum(pg.cov_yards),
    sum(pg.cov_tds),
    sum(pg.cov_ints)
  ) as passer_rating_allowed,
  sum(pg.fg_made) as fg_made,
  sum(pg.fg_att) as fg_att,
  sum(pg.fg_made) / nullif(sum(pg.fg_att), 0) as fg_pct,
  max(pg.fg_long) as fg_long,
  sum(pg.fg_made_0_39) as fg_made_0_39,
  sum(pg.fg_made_40_49) as fg_made_40_49,
  sum(pg.fg_made_50) as fg_made_50,
  sum(pg.pat_made) / nullif(sum(pg.pat_att), 0) as pat_pct,
  sum(pg.punts) as punts,
  sum(pg.punt_net_yards) / nullif(sum(pg.punts), 0) as net_punt,
  sum(pg.punts_inside_20) / nullif(sum(pg.punts), 0) as inside_20_rate
from player_game pg
join games g on g.game_id = pg.game_id
join players p on p.player_id = pg.player_id
where g.game_type = 'REG'
group by g.season, pg.team_abbr, pg.player_id, p.full_name, p.position, p.position_group;

create or replace procedure refresh_team_season_summary()
language plpgsql
set search_path = public
as $$
begin
  delete from team_season_summary;
  insert into team_season_summary (
    season, team_abbr, games, wins, losses, ties,
    points_for, points_against, sos,
    epa_per_play, epa_per_play_allowed,
    sack_rate, blitz_rate, pressure_rate, refreshed_at
  )
  select
    season, team_abbr, games, wins, losses, ties,
    points_for, points_against, sos,
    epa_per_play, epa_per_play_allowed,
    sack_rate, blitz_rate, pressure_rate, now()
  from v_team_reg;
end;
$$;
"""

POLICIES = """
alter table seasons enable row level security;
alter table data_source enable row level security;
alter table teams enable row level security;
alter table players enable row level security;
alter table games enable row level security;
alter table roster enable row level security;
alter table team_game enable row level security;
alter table player_game enable row level security;
alter table team_season_summary enable row level security;

create policy seasons_public_read on seasons for select to anon, authenticated using (true);
create policy data_source_public_read on data_source for select to anon, authenticated using (true);
create policy teams_public_read on teams for select to anon, authenticated using (true);
create policy players_public_read on players for select to anon, authenticated using (true);
create policy games_public_read on games for select to anon, authenticated using (true);
create policy roster_public_read on roster for select to anon, authenticated using (true);
create policy team_game_public_read on team_game for select to anon, authenticated using (true);
create policy player_game_public_read on player_game for select to anon, authenticated using (true);
create policy team_season_summary_public_read on team_season_summary for select to anon, authenticated using (true);

grant select on seasons, data_source, teams, players, games, roster, team_game, player_game, team_season_summary, v_team_reg, v_player_reg to anon, authenticated;
grant execute on function passer_rating(double precision, double precision, double precision, double precision, double precision) to anon, authenticated;
revoke all on procedure refresh_team_season_summary() from public, anon, authenticated;

insert into seasons (season, label, through_week) values
  (2024, '2024 regular season', 18),
  (2025, '2025 regular season', 18),
  (2026, '2026 through week 8', 8);

insert into data_source (name, coverage) values
  ('nflverse play-by-play', 'EPA, success rate, explosives, dropbacks, sacks, starting field position'),
  ('nflverse FTN charting', 'Blitz, extra rushers, play action, motion, no-huddle, box count, contested catches'),
  ('Pro Football Reference advanced', 'Quarterback pressure, yards before contact, drops, coverage allowed'),
  ('nflverse player and team week', 'Box score, kicking, and punting'),
  ('ESPN QBR', 'Weekly QBR joined through ESPN player and game ids');
"""


def main() -> None:
    team = fact_table(
        "team_game",
        TEAM_GAME,
        "  primary key (game_id, team_abbr)",
        [
            "  foreign key (game_id) references games (game_id)",
            "  foreign key (season) references seasons (season)",
            "  foreign key (team_abbr) references teams (team_abbr)",
            "  foreign key (opponent_abbr) references teams (team_abbr)",
        ],
        {"game_id", "season", "week", "game_type", "team_abbr", "opponent_abbr", "is_home"},
    )
    player = fact_table(
        "player_game",
        PLAYER_GAME,
        "  primary key (game_id, player_id)",
        [
            "  foreign key (game_id) references games (game_id)",
            "  foreign key (player_id) references players (player_id)",
            "  foreign key (team_abbr) references teams (team_abbr)",
            "  foreign key (opponent_abbr) references teams (team_abbr)",
        ],
        {"player_id", "game_id", "team_abbr"},
    )
    sql = f"""-- NFL warehouse for the 2024, 2025, and 2026 seasons.
-- Game rows keep postseason games. The regular-season views are what the site reads.
-- Rates are computed here from summed counts, not averaged from weekly rates.

create table seasons (
  season integer primary key,
  label text not null,
  through_week integer not null
);

create table data_source (
  source_id integer generated always as identity primary key,
  name text not null,
  coverage text not null
);

create table teams (
  team_abbr text primary key,
  team_name text not null,
  team_nick text not null,
  team_conf text,
  team_division text,
  team_color text,
  team_color2 text,
  team_logo_espn text
);

create table players (
  player_id text primary key,
  full_name text not null,
  position text,
  position_group text
);

create table games (
  game_id text primary key,
  season integer not null references seasons (season),
  game_type text not null,
  week integer not null,
  gameday date,
  home_team text not null references teams (team_abbr),
  away_team text not null references teams (team_abbr),
  home_score integer,
  away_score integer
);

create table roster (
  season integer not null references seasons (season),
  player_id text not null references players (player_id),
  team_abbr text not null references teams (team_abbr),
  position text,
  primary key (season, player_id, team_abbr)
);

{team}
{player}
create table team_season_summary (
  season integer not null references seasons (season),
  team_abbr text not null references teams (team_abbr),
  games integer,
  wins integer,
  losses integer,
  ties integer,
  points_for integer,
  points_against integer,
  sos double precision,
  epa_per_play double precision,
  epa_per_play_allowed double precision,
  sack_rate double precision,
  blitz_rate double precision,
  pressure_rate double precision,
  refreshed_at timestamptz not null default now(),
  primary key (season, team_abbr)
);

create index games_season_type_idx on games (season, game_type);
create index games_home_team_idx on games (home_team);
create index games_away_team_idx on games (away_team);
create index roster_player_idx on roster (player_id);
create index roster_team_idx on roster (team_abbr);
create index roster_season_team_idx on roster (season, team_abbr);
create index team_game_team_idx on team_game (team_abbr);
create index team_game_opponent_idx on team_game (opponent_abbr);
create index team_game_season_team_idx on team_game (season, team_abbr);
create index player_game_player_idx on player_game (player_id);
create index player_game_team_idx on player_game (team_abbr);
create index player_game_opponent_idx on player_game (opponent_abbr);
create index players_group_idx on players (position_group);
create index team_season_summary_team_idx on team_season_summary (team_abbr);

{VIEWS}
{POLICIES}
"""
    OUT.write_text(sql, encoding="utf-8")
    print(f"wrote {OUT} ({len(sql)} chars)")


if __name__ == "__main__":
    main()
