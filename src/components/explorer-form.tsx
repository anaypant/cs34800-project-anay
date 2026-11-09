"use client";

import { useTransition, type ReactNode } from "react";
import { useRouter } from "next/navigation";

type Option = { value: string; label: string };
type Group = { label: string; options: Option[] };

export function ExplorerForm({
  season,
  team,
  player,
  teamMetric,
  playerMetric,
  seasons,
  teams,
  playerGroups,
  teamMetrics,
  playerMetrics,
}: {
  season: string;
  team: string;
  player: string;
  teamMetric: string;
  playerMetric: string;
  seasons: Option[];
  teams: Option[];
  playerGroups: Group[];
  teamMetrics: Option[];
  playerMetrics: Option[];
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  function go(patch: Partial<Record<"season" | "team" | "player" | "teamMetric" | "playerMetric", string>>) {
    const next = { season, team, player, teamMetric, playerMetric, ...patch };
    if (patch.season != null && patch.season !== season) {
      next.team = "";
      next.player = "";
    }
    if (patch.team != null && patch.team !== team) {
      next.player = "";
    }
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(next)) {
      if (value) params.set(key, value);
    }
    const queryString = params.toString();
    startTransition(() => {
      router.push(queryString ? `/?${queryString}` : "/");
    });
  }

  return (
    <form
      className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5"
      aria-busy={pending}
      onSubmit={(event) => event.preventDefault()}
    >
      <Field label="Season">
        <select
          value={season}
          disabled={pending}
          onChange={(event) => go({ season: event.target.value })}
        >
          {seasons.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Team">
        <select value={team} disabled={pending} onChange={(event) => go({ team: event.target.value })}>
          <option value="">Select a team</option>
          {teams.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Player">
        <select
          value={player}
          disabled={pending || !team}
          onChange={(event) => go({ player: event.target.value })}
        >
          <option value="">{team ? "Select a player" : "Select a team first"}</option>
          {playerGroups.map((group) => (
            <optgroup key={group.label} label={group.label}>
              {group.options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </Field>
      <Field label="Team chart">
        <select
          value={teamMetric}
          disabled={pending}
          onChange={(event) => go({ teamMetric: event.target.value })}
        >
          {teamMetrics.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Player chart">
        <select
          value={playerMetric}
          disabled={pending || playerMetrics.length === 0}
          onChange={(event) => go({ playerMetric: event.target.value })}
        >
          {playerMetrics.length === 0 ? <option value="">Select a player</option> : null}
          {playerMetrics.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </Field>
    </form>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block text-xs font-medium tracking-wide text-zinc-400 uppercase">
      {label}
      <span className="mt-1 block [&_select]:w-full [&_select]:rounded-md [&_select]:border [&_select]:border-zinc-700 [&_select]:bg-zinc-950 [&_select]:px-3 [&_select]:py-2 [&_select]:text-sm [&_select]:font-normal [&_select]:normal-case [&_select]:tracking-normal [&_select]:text-zinc-100 [&_select]:disabled:opacity-50">
        {children}
      </span>
    </label>
  );
}
