import { formatMetric, num, ordinal, type FormatKind, type Row } from "@/lib/format";

export type Better = "high" | "low" | "none";

export type Metric = {
  key: string;
  label: string;
  format: FormatKind;
  better: Better;
  note?: string;
  min?: { key: string; value: number };
};

export type Section = {
  title: string;
  groups: string[];
  volume: { key: string; value: number };
  metrics: Metric[];
};

const sackNote = "Sacks divided by opponent dropbacks. One play is counted once.";
const pressureNote =
  "Share of dropbacks on which the quarterback was hurried, hit, or sacked. Defender pressure credits are not used, because two rushers can be credited on the same play.";
const blitzNote =
  "Share of charted dropbacks with at least one blitzer. This is a tendency, not a quality ranking.";

export const teamSections: Section[] = [
  {
    title: "Offense",
    groups: [],
    volume: { key: "plays", value: 1 },
    metrics: [
      { key: "epa_per_play", label: "EPA per play", format: "epa", better: "high" },
      { key: "success_rate", label: "Success rate", format: "pct", better: "high" },
      { key: "yards_per_attempt", label: "Yards per pass", format: "yards", better: "high" },
      { key: "yards_per_carry", label: "Yards per carry", format: "yards", better: "high" },
      { key: "pass_epa_per_dropback", label: "Pass EPA per dropback", format: "epa", better: "high" },
      { key: "rush_epa_per_carry", label: "Rush EPA per carry", format: "epa", better: "high" },
      {
        key: "proe",
        label: "Pass rate over expected",
        format: "pct",
        better: "none",
        note: "Neutral-down pass rate minus the expected pass rate. Positive means more pass-heavy than the situation suggests.",
      },
      {
        key: "expl_pass_rate",
        label: "Explosive pass rate",
        format: "pct",
        better: "high",
        note: "Passes of 20 or more yards, excluding sacks.",
      },
      {
        key: "expl_rush_rate",
        label: "Explosive rush rate",
        format: "pct",
        better: "high",
        note: "Rushes of 10 or more yards.",
      },
      { key: "early_success_rate", label: "Early-down success", format: "pct", better: "high" },
      { key: "third_down_rate", label: "Third-down rate", format: "pct", better: "high" },
      { key: "fourth_down_rate", label: "Fourth-down rate", format: "pct", better: "high" },
      { key: "rz_td_rate", label: "Red-zone TD rate", format: "pct", better: "high" },
      { key: "play_action_rate", label: "Play-action rate", format: "pct", better: "none" },
      { key: "motion_rate", label: "Motion rate", format: "pct", better: "none" },
      {
        key: "sack_rate_allowed",
        label: "Sack rate allowed",
        format: "pct",
        better: "low",
        note: "Sacks taken divided by dropbacks.",
      },
      {
        key: "pressure_rate_allowed",
        label: "Pressure rate allowed",
        format: "pct",
        better: "low",
        note: pressureNote,
      },
      {
        key: "start_yardline",
        label: "Average start",
        format: "yards",
        better: "high",
        note: "Average yards from the offense's own goal line at the start of a drive.",
      },
      { key: "ybc_per_carry", label: "Yards before contact", format: "yards", better: "high" },
    ],
  },
  {
    title: "Defense",
    groups: [],
    volume: { key: "plays", value: 1 },
    metrics: [
      { key: "epa_per_play_allowed", label: "EPA per play allowed", format: "epa", better: "low" },
      { key: "success_rate_allowed", label: "Success rate allowed", format: "pct", better: "low" },
      { key: "sack_rate", label: "Sack rate", format: "pct", better: "high", note: sackNote },
      { key: "pressure_rate", label: "Pressure rate", format: "pct", better: "high", note: pressureNote },
      {
        key: "qb_hit_rate",
        label: "QB hit rate",
        format: "pct",
        better: "high",
        note: "Plays flagged as a quarterback hit, divided by dropbacks. Sacks are often flagged too.",
      },
      { key: "blitz_rate", label: "Blitz rate", format: "pct", better: "none", note: blitzNote },
      {
        key: "five_plus_rusher_rate",
        label: "Five-plus rusher rate",
        format: "pct",
        better: "none",
        note: "Charted dropbacks with five or more pass rushers. This is separate from the blitz rate.",
      },
      { key: "stuff_rate", label: "Stuff rate", format: "pct", better: "high", note: "Rushes stopped at the line or for a loss." },
      { key: "takeaways", label: "Takeaways", format: "int", better: "high" },
      { key: "missed_tackles", label: "Missed tackles", format: "int", better: "low" },
    ],
  },
  {
    title: "Special teams",
    groups: [],
    volume: { key: "plays", value: 1 },
    metrics: [
      { key: "fg_pct", label: "Field-goal percentage", format: "pct", better: "high" },
      { key: "net_punt", label: "Net yards per punt", format: "yards", better: "high" },
      { key: "punt_inside_20_rate", label: "Punts inside the 20", format: "pct", better: "high" },
      { key: "penalties", label: "Penalties", format: "int", better: "low" },
      { key: "penalty_yards", label: "Penalty yards", format: "int", better: "low" },
    ],
  },
];

export const teamChartMetrics: Metric[] = [
  { key: "epa_per_play", label: "Offense EPA per play", format: "epa", better: "high" },
  { key: "epa_per_play_allowed", label: "Defense EPA per play allowed", format: "epa", better: "low" },
  { key: "success_rate", label: "Offense success rate", format: "pct", better: "high" },
  { key: "success_rate_allowed", label: "Defense success rate allowed", format: "pct", better: "low" },
  { key: "points_per_game", label: "Points per game", format: "one", better: "high" },
  { key: "sack_rate", label: "Sack rate", format: "pct", better: "high", note: sackNote },
  { key: "pressure_rate", label: "Pressure rate", format: "pct", better: "high", note: pressureNote },
  { key: "blitz_rate", label: "Blitz rate", format: "pct", better: "none", note: blitzNote },
  { key: "sack_rate_allowed", label: "Sack rate allowed", format: "pct", better: "low" },
  { key: "pressure_rate_allowed", label: "Pressure rate allowed", format: "pct", better: "low", note: pressureNote },
  {
    key: "proe",
    label: "Pass rate over expected",
    format: "pct",
    better: "none",
    note: "Neutral-down pass rate minus the expected pass rate.",
  },
  { key: "expl_pass_rate", label: "Explosive pass rate", format: "pct", better: "high", note: "Passes of 20 or more yards, excluding sacks." },
  { key: "expl_rush_rate", label: "Explosive rush rate", format: "pct", better: "high", note: "Rushes of 10 or more yards." },
  { key: "third_down_rate", label: "Third-down rate", format: "pct", better: "high" },
  { key: "rz_td_rate", label: "Red-zone TD rate", format: "pct", better: "high" },
  { key: "stuff_rate", label: "Stuff rate", format: "pct", better: "high" },
  { key: "net_punt", label: "Net yards per punt", format: "yards", better: "high" },
  {
    key: "start_yardline",
    label: "Average starting field position",
    format: "yards",
    better: "high",
    note: "Yards from the offense's own goal line. Higher means better field position.",
  },
];

const countNote =
  "This is a season count. Public data does not include pass-rush snaps, so a rate would not be comparable.";

export const playerSections: Section[] = [
  {
    title: "Passing",
    groups: ["QB"],
    volume: { key: "pass_attempts", value: 20 },
    metrics: [
      { key: "pass_attempts", label: "Attempts", format: "int", better: "none" },
      { key: "pass_yards", label: "Yards", format: "int", better: "none" },
      { key: "pass_tds", label: "Touchdowns", format: "int", better: "high" },
      { key: "interceptions_thrown", label: "Interceptions", format: "int", better: "low" },
      { key: "passer_rating", label: "Passer rating", format: "rating", better: "high", min: { key: "pass_attempts", value: 80 } },
      { key: "epa_per_dropback", label: "EPA per dropback", format: "epa", better: "high", min: { key: "pass_attempts", value: 80 } },
      {
        key: "cpoe",
        label: "Completion % over expected",
        format: "signed",
        better: "high",
        min: { key: "pass_attempts", value: 80 },
        note: "Attempt-weighted completion percentage over expected.",
      },
      {
        key: "qbr",
        label: "ESPN QBR",
        format: "rating",
        better: "high",
        min: { key: "pass_attempts", value: 80 },
        note: "Play-weighted ESPN Total QBR.",
      },
      { key: "sack_rate", label: "Sack rate faced", format: "pct", better: "low", min: { key: "pass_attempts", value: 80 } },
      { key: "pressure_rate", label: "Pressure rate faced", format: "pct", better: "low", min: { key: "pass_attempts", value: 80 }, note: pressureNote },
      { key: "bad_throw_rate", label: "Bad-throw rate", format: "pct", better: "low", min: { key: "pass_attempts", value: 80 } },
      { key: "deep_completion_rate", label: "Deep completion rate", format: "pct", better: "high", min: { key: "deep_att", value: 15 }, note: "Completions on throws of 20 or more air yards." },
      { key: "play_action_epa", label: "EPA per play-action dropback", format: "epa", better: "high", min: { key: "pass_attempts", value: 80 } },
      { key: "blitz_epa", label: "EPA per blitz faced", format: "epa", better: "high", min: { key: "pass_attempts", value: 80 } },
    ],
  },
  {
    title: "Rushing",
    groups: ["RB", "QB"],
    volume: { key: "carries", value: 15 },
    metrics: [
      { key: "carries", label: "Carries", format: "int", better: "none" },
      { key: "rush_yards", label: "Yards", format: "int", better: "none" },
      { key: "rush_tds", label: "Touchdowns", format: "int", better: "high" },
      { key: "yards_per_carry", label: "Yards per carry", format: "yards", better: "high", min: { key: "carries", value: 40 } },
      { key: "rush_epa_per_carry", label: "EPA per carry", format: "epa", better: "high", min: { key: "carries", value: 40 } },
      { key: "rush_success_rate", label: "Success rate", format: "pct", better: "high", min: { key: "carries", value: 40 } },
      { key: "explosive_rush_rate", label: "Explosive rate", format: "pct", better: "high", min: { key: "carries", value: 40 }, note: "Rushes of 10 or more yards." },
      { key: "stuff_rate", label: "Stuff rate", format: "pct", better: "low", min: { key: "carries", value: 40 } },
      { key: "ybc_per_carry", label: "Yards before contact", format: "yards", better: "high", min: { key: "carries", value: 40 } },
      { key: "yac_per_carry", label: "Yards after contact", format: "yards", better: "high", min: { key: "carries", value: 40 } },
      { key: "broken_tackles", label: "Broken tackles", format: "int", better: "high", min: { key: "carries", value: 40 } },
      { key: "light_box_ypc", label: "Yards per carry vs light box", format: "yards", better: "high", min: { key: "carries", value: 40 }, note: "Designed rushes against six or fewer defenders in the box." },
      { key: "stacked_box_ypc", label: "Yards per carry vs stacked box", format: "yards", better: "high", min: { key: "carries", value: 40 }, note: "Designed rushes against eight or more defenders in the box." },
      { key: "short_yardage_rate", label: "Short-yardage conversion", format: "pct", better: "high", min: { key: "carries", value: 40 } },
    ],
  },
  {
    title: "Receiving",
    groups: ["WR", "TE", "RB"],
    volume: { key: "targets", value: 10 },
    metrics: [
      { key: "targets", label: "Targets", format: "int", better: "none" },
      { key: "receptions", label: "Receptions", format: "int", better: "none" },
      { key: "rec_yards", label: "Yards", format: "int", better: "none" },
      { key: "rec_tds", label: "Touchdowns", format: "int", better: "high" },
      { key: "yards_per_target", label: "Yards per target", format: "yards", better: "high", min: { key: "targets", value: 25 } },
      { key: "rec_epa_per_target", label: "EPA per target", format: "epa", better: "high", min: { key: "targets", value: 25 } },
      { key: "catch_rate", label: "Catch rate", format: "pct", better: "high", min: { key: "targets", value: 25 } },
      { key: "yac_per_reception", label: "Yards after catch", format: "yards", better: "high", min: { key: "targets", value: 25 } },
      { key: "drop_rate", label: "Drop rate", format: "pct", better: "low", min: { key: "targets", value: 25 } },
      { key: "explosive_rec_rate", label: "Explosive catch rate", format: "pct", better: "high", min: { key: "targets", value: 25 }, note: "Receptions of 20 or more yards, divided by targets." },
      { key: "contested_catch_rate", label: "Contested-catch rate", format: "pct", better: "high", min: { key: "targets", value: 25 } },
      { key: "rz_td_rate", label: "Red-zone TD rate", format: "pct", better: "high", min: { key: "targets", value: 25 } },
    ],
  },
  {
    title: "Defense",
    groups: ["DL", "LB", "DB"],
    volume: { key: "tackles", value: 8 },
    metrics: [
      { key: "tackles", label: "Tackles", format: "int", better: "none" },
      { key: "tackles_for_loss", label: "Tackles for loss", format: "one", better: "high", min: { key: "games", value: 4 } },
      { key: "sacks", label: "Sacks", format: "one", better: "high", min: { key: "games", value: 4 }, note: countNote },
      { key: "qb_hits", label: "QB hits", format: "int", better: "high", min: { key: "games", value: 4 } },
      { key: "pressures", label: "Pressures", format: "one", better: "high", min: { key: "games", value: 4 }, note: countNote },
      { key: "hurries", label: "Hurries", format: "one", better: "high", min: { key: "games", value: 4 }, note: countNote },
      { key: "interceptions", label: "Interceptions", format: "int", better: "high", min: { key: "games", value: 4 } },
      { key: "passes_defended", label: "Passes defended", format: "int", better: "high", min: { key: "games", value: 4 } },
      { key: "missed_tackles", label: "Missed tackles", format: "int", better: "low", min: { key: "games", value: 4 } },
      {
        key: "completion_rate_allowed",
        label: "Completion rate allowed",
        format: "pct",
        better: "low",
        min: { key: "cov_targets", value: 20 },
      },
      {
        key: "yards_per_target_allowed",
        label: "Yards per target allowed",
        format: "yards",
        better: "low",
        min: { key: "cov_targets", value: 20 },
      },
      {
        key: "passer_rating_allowed",
        label: "Passer rating allowed",
        format: "rating",
        better: "low",
        min: { key: "cov_targets", value: 20 },
        note: "Passer rating of the throws charted against this defender.",
      },
    ],
  },
  {
    title: "Kicking",
    groups: ["K"],
    volume: { key: "fg_att", value: 1 },
    metrics: [
      { key: "fg_made", label: "Field goals made", format: "int", better: "none" },
      { key: "fg_att", label: "Field goals attempted", format: "int", better: "none" },
      { key: "fg_pct", label: "Field-goal percentage", format: "pct", better: "high", min: { key: "fg_att", value: 8 } },
      { key: "fg_long", label: "Long", format: "int", better: "high", min: { key: "fg_att", value: 8 } },
      { key: "fg_made_0_39", label: "Makes inside 40", format: "int", better: "none" },
      { key: "fg_made_40_49", label: "Makes from 40–49", format: "int", better: "none" },
      { key: "fg_made_50", label: "Makes from 50+", format: "int", better: "high" },
      { key: "pat_pct", label: "Extra-point percentage", format: "pct", better: "high", min: { key: "fg_att", value: 8 } },
    ],
  },
  {
    title: "Punting",
    groups: ["P"],
    volume: { key: "punts", value: 1 },
    metrics: [
      { key: "punts", label: "Punts", format: "int", better: "none" },
      { key: "net_punt", label: "Net yards per punt", format: "yards", better: "high", min: { key: "punts", value: 15 } },
      { key: "inside_20_rate", label: "Inside-20 rate", format: "pct", better: "high", min: { key: "punts", value: 15 } },
    ],
  },
];

export const groupLabels: Record<string, string> = {
  QB: "Quarterbacks",
  RB: "Running backs",
  WR: "Wide receivers",
  TE: "Tight ends",
  DL: "Defensive line",
  LB: "Linebackers",
  DB: "Defensive backs",
  K: "Kickers",
  P: "Punters",
};

export const groupOrder = ["QB", "RB", "WR", "TE", "DL", "LB", "DB", "K", "P"];

export function metricByKey(metrics: Metric[], key: string | undefined): Metric {
  return metrics.find((metric) => metric.key === key) ?? metrics[0];
}

export function playerChartMetrics(group: string | null): Metric[] {
  if (group === "QB") {
    return playerSections[0].metrics.filter((metric) =>
      ["epa_per_dropback", "cpoe", "passer_rating", "qbr", "sack_rate", "pressure_rate", "bad_throw_rate", "deep_completion_rate"].includes(metric.key),
    );
  }
  if (group === "RB") {
    return playerSections[1].metrics.filter((metric) =>
      ["yards_per_carry", "rush_epa_per_carry", "rush_success_rate", "explosive_rush_rate", "stuff_rate", "ybc_per_carry"].includes(metric.key),
    );
  }
  if (group === "WR" || group === "TE") {
    return playerSections[2].metrics.filter((metric) =>
      ["yards_per_target", "rec_epa_per_target", "catch_rate", "yac_per_reception", "drop_rate", "explosive_rec_rate"].includes(metric.key),
    );
  }
  if (group === "DL" || group === "LB") {
    return playerSections[3].metrics.filter((metric) =>
      ["sacks", "pressures", "tackles_for_loss", "qb_hits", "missed_tackles"].includes(metric.key),
    );
  }
  if (group === "DB") {
    return playerSections[3].metrics.filter((metric) =>
      ["passer_rating_allowed", "completion_rate_allowed", "yards_per_target_allowed", "interceptions", "passes_defended", "missed_tackles"].includes(metric.key),
    );
  }
  if (group === "K") {
    return playerSections[4].metrics.filter((metric) => ["fg_pct", "pat_pct", "fg_long"].includes(metric.key));
  }
  if (group === "P") {
    return playerSections[5].metrics.filter((metric) => ["net_punt", "inside_20_rate"].includes(metric.key));
  }
  return [];
}

export function visibleSections(group: string | null, row: Row): Section[] {
  return playerSections.filter((section) => {
    const inGroup = group != null && section.groups.includes(group);
    const enough = (num(row[section.volume.key]) ?? 0) >= section.volume.value;
    return inGroup || enough;
  });
}

export type Standing = { rank: number; total: number; pool: Row[] };

export function standing(population: Row[], metric: Metric, subject: Row, idKey: string): Standing | null {
  const subjectId = String(subject[idKey] ?? "");
  const pool = population.filter((row) => {
    if (num(row[metric.key]) == null) return false;
    if (!metric.min) return true;
    return (num(row[metric.min.key]) ?? 0) >= metric.min.value;
  });
  if (!pool.some((row) => String(row[idKey]) === subjectId) && num(subject[metric.key]) != null) {
    pool.push(subject);
  }
  const direction = metric.better === "low" ? 1 : -1;
  pool.sort((left, right) => direction * ((num(left[metric.key]) ?? 0) - (num(right[metric.key]) ?? 0)));
  const index = pool.findIndex((row) => String(row[idKey]) === subjectId);
  if (index < 0) return null;
  const subjectValue = num(pool[index][metric.key]);
  let rank = index + 1;
  for (let cursor = index - 1; cursor >= 0; cursor -= 1) {
    if (num(pool[cursor][metric.key]) !== subjectValue) break;
    rank = cursor + 1;
  }
  return { rank, total: pool.length, pool };
}

export function chartPoints(
  population: Row[],
  metric: Metric,
  subjectId: string,
  idKey: string,
  label: (row: Row) => string,
  limit = 32,
): { name: string; value: number; selected: boolean }[] {
  if (population.length === 0) return [];
  const subject = population.find((row) => String(row[idKey]) === subjectId) ?? population[0];
  const ranked = standing(population, metric, subject, idKey);
  if (!ranked) return [];
  let rows = ranked.pool.slice(0, limit);
  const selected = ranked.pool.find((row) => String(row[idKey]) === subjectId);
  if (selected && !rows.some((row) => String(row[idKey]) === subjectId)) {
    rows = [...rows.slice(0, Math.max(limit - 1, 0)), selected];
    const direction = metric.better === "low" ? 1 : -1;
    rows.sort((left, right) => direction * ((num(left[metric.key]) ?? 0) - (num(right[metric.key]) ?? 0)));
  }
  const names = rows.map((row) => label(row));
  const repeated = new Set(names.filter((name, index) => names.indexOf(name) !== index));
  return rows.flatMap((row) => {
    const value = num(row[metric.key]);
    if (value == null) return [];
    const base = label(row);
    const team = typeof row.team_abbr === "string" ? row.team_abbr : "";
    const name = repeated.has(base) && team ? `${base} (${team})` : base;
    return [{ name, value, selected: String(row[idKey]) === subjectId }];
  });
}

export function rankLabel(place: Standing | null, better: Better): string | null {
  if (!place) return null;
  if (better === "none") return `${ordinal(place.rank)}-highest of ${place.total}`;
  return `${ordinal(place.rank)}-best of ${place.total}`;
}

export function statLine(metric: Metric, row: Row, population: Row[], idKey: string) {
  const value = num(row[metric.key]);
  if (value == null) return null;
  const place = standing(population, metric, row, idKey);
  return {
    label: metric.label,
    value: formatMetric(value, metric.format),
    rank: place && metric.better !== "none" && place.total > 1 ? `${place.rank}/${place.total}` : null,
  };
}
