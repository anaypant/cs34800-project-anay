import { CompareChart } from "@/components/compare-chart";
import { ExplorerForm } from "@/components/explorer-form";
import { Notebook } from "@/components/notebook";
import { StatList } from "@/components/stat-list";
import { query } from "@/lib/db";
import { notebookFor, viewerId } from "@/lib/notebook";
import { num, shortName, teamColor, type Row } from "@/lib/format";
import {
  chartPoints,
  groupLabels,
  groupOrder,
  metricByKey,
  playerChartMetrics,
  rankLabel,
  standing,
  statLine,
  teamChartMetrics,
  teamSections,
  visibleSections,
} from "@/lib/metrics";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const rosterSql = `select *
  from v_player_reg
  where season = $1 and team_abbr = $2
  order by (
    pass_attempts + carries + targets + tackles
    + coalesce(fg_att, 0) + coalesce(punts, 0)
    + coalesce(sacks, 0) + coalesce(pressures, 0)
  ) desc, full_name`;

const minimumLabel: Record<string, string> = {
  pass_attempts: "attempts",
  carries: "carries",
  targets: "targets",
  deep_att: "deep attempts",
  games: "games",
  cov_targets: "targets in coverage",
  fg_att: "field-goal attempts",
  punts: "punts",
};

function one(value: string | string[] | undefined): string {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
}

function safeMessage(error: unknown): string {
  const text = error instanceof Error ? error.message : "The database query failed.";
  return text.replace(/postgres(?:ql)?:\/\/\S+/gi, "postgresql://***");
}

function whole(value: unknown): string {
  const parsed = num(value);
  return parsed == null ? "—" : Math.round(parsed).toLocaleString("en-US");
}

function recordOf(row: Row): string {
  const ties = num(row.ties) ?? 0;
  const base = `${whole(row.wins)}-${whole(row.losses)}`;
  return ties > 0 ? `${base}-${whole(ties)}` : base;
}

function playerSummary(row: Row, group: string | null): string {
  if (group === "QB") {
    return `${whole(row.pass_attempts)} att · ${whole(row.pass_yards)} yds · ${whole(row.pass_tds)} TD · ${whole(row.interceptions_thrown)} INT`;
  }
  if (group === "RB") {
    return `${whole(row.carries)} car · ${whole(row.rush_yards)} yds · ${whole(row.rush_tds)} TD`;
  }
  if (group === "WR" || group === "TE") {
    return `${whole(row.targets)} tgt · ${whole(row.receptions)} rec · ${whole(row.rec_yards)} yds · ${whole(row.rec_tds)} TD`;
  }
  if (group === "DL" || group === "LB" || group === "DB") {
    return `${whole(row.tackles)} tkl · ${whole(row.sacks)} sacks · ${whole(row.pressures)} pressures`;
  }
  if (group === "K") return `${whole(row.fg_made)}/${whole(row.fg_att)} field goals`;
  if (group === "P") {
    const net = num(row.net_punt);
    return `${whole(row.punts)} punts${net == null ? "" : ` · ${net.toFixed(1)} net`}`;
  }
  return `${whole(row.games)} games`;
}

export default async function Page({ searchParams }: PageProps<"/">) {
  const params = await searchParams;
  const requestedSeason = Number(one(params.season));
  const requestedTeam = one(params.team).toUpperCase();
  const safeTeam = /^[A-Z]{2,3}$/.test(requestedTeam) ? requestedTeam : "";
  const requestedPlayer = one(params.player);
  const safePlayer = /^[A-Za-z0-9-]{1,40}$/.test(requestedPlayer) ? requestedPlayer : "";

  let seasons: Row[] = [];
  let teams: Row[] = [];
  let roster: Row[] = [];
  let season = 2026;
  try {
    seasons = await query<Row>("select season, label from seasons order by season desc");
    const seasonNumbers = seasons.map((row) => Number(row.season));
    season = seasonNumbers.includes(requestedSeason) ? requestedSeason : (seasonNumbers[0] ?? 2026);
    [teams, roster] = await Promise.all([
      query<Row>("select * from v_team_reg where season = $1 order by team_abbr", [season]),
      safeTeam ? query<Row>(rosterSql, [season, safeTeam]) : Promise.resolve([]),
    ]);
  } catch (error) {
    return (
      <main className="flex-1 bg-zinc-950 px-6 py-16 text-zinc-200">
        <h1 className="text-2xl font-semibold">cs34800 project anay</h1>
        <p className="mt-3 max-w-xl text-sm text-zinc-400">{safeMessage(error)}</p>
      </main>
    );
  }
  const seasonLabel = String(seasons.find((row) => Number(row.season) === season)?.label ?? season);
  const showingRequested = Number.isInteger(requestedSeason) && requestedSeason === season;
  const team = teams.some((row) => row.team_abbr === safeTeam) ? safeTeam : "";
  const teamRow = teams.find((row) => row.team_abbr === team);
  const players = team ? roster.filter((row) => row.team_abbr === team) : [];
  const playerRow = players.find((row) => row.player_id === safePlayer);
  const player = playerRow ? safePlayer : "";
  const group = typeof playerRow?.position_group === "string" ? playerRow.position_group : null;
  const chartMetrics = playerChartMetrics(group);
  const teamMetric = metricByKey(teamChartMetrics, one(params.teamMetric));
  const playerMetric = chartMetrics.length ? metricByKey(chartMetrics, one(params.playerMetric)) : null;

  let peers: Row[] = [];
  if (playerRow && group) {
    try {
      peers = await query<Row>(
        "select * from v_player_reg where season = $1 and position_group = $2",
        [season, group],
      );
    } catch (error) {
      return (
        <main className="flex-1 bg-zinc-950 px-6 py-16 text-zinc-200">
          <h1 className="text-2xl font-semibold">cs34800 project anay</h1>
          <p className="mt-3 max-w-xl text-sm text-zinc-400">{safeMessage(error)}</p>
        </main>
      );
    }
  }

  const teamPoints = chartPoints(
    teams,
    teamMetric,
    team,
    "team_abbr",
    (row) => String(row.team_abbr),
    40,
  );
  const teamPlace = teamRow ? standing(teams, teamMetric, teamRow, "team_abbr") : null;
  const playerPoints =
    playerRow && playerMetric
      ? chartPoints(peers, playerMetric, player, "player_id", (row) => shortName(row.full_name), 24)
      : [];
  const playerPlace =
    playerRow && playerMetric ? standing(peers, playerMetric, playerRow, "player_id") : null;
  const color = teamColor(teamRow?.team_color);
  const userId = await viewerId();
  const [teamNotebook, playerNotebook] = await Promise.all([
    teamRow ? notebookFor(season, "team", team, userId) : Promise.resolve(null),
    playerRow ? notebookFor(season, "player", player, userId) : Promise.resolve(null),
  ]);
  const playerGroups = [
    ...groupOrder.flatMap((positionGroup) => {
      const options = players
        .filter((row) => row.position_group === positionGroup)
        .map((row) => ({
          value: String(row.player_id),
          label: `${row.full_name} · ${row.position ?? positionGroup}`,
        }));
      return options.length ? [{ label: groupLabels[positionGroup], options }] : [];
    }),
    ...(() => {
      const options = players
        .filter((row) => typeof row.position_group !== "string" || !groupOrder.includes(row.position_group))
        .map((row) => ({
          value: String(row.player_id),
          label: `${row.full_name} · ${row.position ?? "Other"}`,
        }));
      return options.length ? [{ label: "Other", options }] : [];
    })(),
  ];

  return (
    <main className="flex-1 bg-zinc-950 text-zinc-100">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 sm:px-6">
        <header className="flex flex-col gap-1">
          <p className="text-xs font-medium tracking-[0.18em] text-zinc-500 uppercase">
            cs34800 project anay
          </p>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">NFL season explorer</h1>
          <p className="max-w-3xl text-sm text-zinc-400">
            {seasonLabel}. Open one team, then one player on that team. Like either of them and leave a note.
            Those likes and notes are the rows this app inserts, updates, and deletes. The season stats stay
            read-only.
          </p>
        </header>

        <ExplorerForm
          season={String(season)}
          team={team}
          player={player}
          teamMetric={teamMetric.key}
          playerMetric={playerMetric?.key ?? ""}
          seasons={seasons.map((row) => ({ value: String(row.season), label: String(row.label) }))}
          teams={teams.map((row) => ({
            value: String(row.team_abbr),
            label: `${row.team_abbr} · ${row.team_name} · ${recordOf(row)}`,
          }))}
          playerGroups={playerGroups}
          teamMetrics={teamChartMetrics.map((metric) => ({ value: metric.key, label: metric.label }))}
          playerMetrics={chartMetrics.map((metric) => ({ value: metric.key, label: metric.label }))}
        />

        {!showingRequested && one(params.season) ? (
          <p className="text-sm text-zinc-500">That season is not in the warehouse, so this is {seasonLabel}.</p>
        ) : null}

        <CompareChart
          title={teamMetric.label}
          caption={
            teamPlace
              ? `${teamRow?.team_name ?? team} is ${rankLabel(teamPlace, teamMetric.better)}.`
              : `${teams.length} teams. Select one to highlight it and open the season sheet.`
          }
          note={teamMetric.note}
          points={teamPoints}
          color={team ? color : "#a1a1aa"}
          format={teamMetric.format}
        />

        {teamRow ? (
          <section className="flex flex-col gap-4" style={{ borderColor: color }}>
            <div className="flex items-center gap-4 rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
              <span className="h-14 w-1.5 rounded-full" style={{ background: color }} aria-hidden />
              {typeof teamRow.team_logo_espn === "string" && teamRow.team_logo_espn.startsWith("https://") ? (
                // Team logos are remote ESPN assets, used as content rather than layout.
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={teamRow.team_logo_espn}
                  alt=""
                  width={56}
                  height={56}
                  className="h-14 w-14 object-contain"
                />
              ) : null}
              <div>
                <h2 className="text-xl font-semibold">
                  {String(teamRow.team_name)}{" "}
                  <span className="text-zinc-500">{team}</span>
                </h2>
                <p className="text-sm text-zinc-300 tabular-nums">
                  {recordOf(teamRow)} · {whole(teamRow.points_for)}–{whole(teamRow.points_against)} ·{" "}
                  {rankLabel(standing(teams, { key: "win_pct", label: "", format: "pct", better: "high" }, teamRow, "team_abbr"), "high")}{" "}
                  by win percentage
                </p>
                <p className="text-xs text-zinc-500">
                  {String(teamRow.team_conf ?? "")} {String(teamRow.team_division ?? "")} · strength of schedule{" "}
                  {((num(teamRow.sos) ?? 0) * 100).toFixed(1)}%
                </p>
              </div>
            </div>
            {teamNotebook ? (
              <Notebook
                title={`Notes on ${String(teamRow.team_name)}`}
                season={season}
                targetKind="team"
                targetId={team}
                state={teamNotebook}
              />
            ) : null}
            <div className="grid gap-4 lg:grid-cols-3">
              {teamSections.map((section) => (
                <StatList
                  key={section.title}
                  title={section.title}
                  rows={section.metrics.flatMap((metric) => {
                    const line = statLine(metric, teamRow, teams, "team_abbr");
                    return line ? [line] : [];
                  })}
                />
              ))}
            </div>
          </section>
        ) : null}

        {playerRow && playerMetric ? (
          <section className="flex flex-col gap-4">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
              <h2 className="text-xl font-semibold">{String(playerRow.full_name)}</h2>
              <p className="text-sm text-zinc-400">
                {String(playerRow.position ?? group)} · {team} · {whole(playerRow.games)} games ·{" "}
                {playerSummary(playerRow, group)}
              </p>
            </div>
            {playerNotebook ? (
              <Notebook
                title={`Notes on ${String(playerRow.full_name)}`}
                season={season}
                targetKind="player"
                targetId={player}
                state={playerNotebook}
              />
            ) : null}
            <div className="grid gap-4 lg:grid-cols-2">
              {visibleSections(group, playerRow).map((section) => (
                <StatList
                  key={section.title}
                  title={section.title}
                  rows={section.metrics.flatMap((metric) => {
                    const line = statLine(metric, playerRow, peers.length ? peers : [playerRow], "player_id");
                    return line ? [line] : [];
                  })}
                />
              ))}
            </div>
            <CompareChart
              title={`${playerMetric.label} · ${groupLabels[group ?? ""] ?? "players"}`}
              caption={[
                playerPlace ? `${playerRow.full_name} is ${rankLabel(playerPlace, playerMetric.better)}.` : "",
                playerPlace && playerPoints.length < playerPlace.total
                  ? `The chart shows ${playerPoints.length} of ${playerPlace.total}.`
                  : "",
                playerMetric.min
                  ? `The comparison keeps players with at least ${playerMetric.min.value} ${minimumLabel[playerMetric.min.key] ?? "chances"}.`
                  : "",
              ]
                .filter(Boolean)
                .join(" ")}
              note={playerMetric.note}
              points={playerPoints}
              color={color}
              format={playerMetric.format}
            />
          </section>
        ) : playerRow ? (
          <section className="flex flex-col gap-4">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
            <h2 className="text-xl font-semibold">{String(playerRow.full_name)}</h2>
            <p className="mt-2 max-w-2xl text-sm text-zinc-400">
              {String(playerRow.position ?? "This player")} does not have a position group with a public snap
              denominator, so there is no peer chart. Offensive line play is represented by the team sack rate
              and pressure rate allowed.
            </p>
            </div>
            {playerNotebook ? (
              <Notebook
                title={`Notes on ${String(playerRow.full_name)}`}
                season={season}
                targetKind="player"
                targetId={player}
                state={playerNotebook}
              />
            ) : null}
            <div className="grid gap-4 lg:grid-cols-2">
              {visibleSections(group, playerRow).map((section) => (
                <StatList
                  key={section.title}
                  title={section.title}
                  rows={section.metrics.flatMap((metric) => {
                    const line = statLine(metric, playerRow, [playerRow], "player_id");
                    return line ? [line] : [];
                  })}
                />
              ))}
            </div>
          </section>
        ) : null}
      </div>
    </main>
  );
}
