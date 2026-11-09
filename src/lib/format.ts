export type Row = Record<string, unknown>;

export type FormatKind =
  | "pct"
  | "epa"
  | "one"
  | "signed"
  | "int"
  | "yards"
  | "rating";

export function num(value: unknown): number | null {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function formatMetric(value: number | null, kind: FormatKind): string {
  if (value == null) return "—";
  if (kind === "pct") return `${(value * 100).toFixed(1)}%`;
  if (kind === "epa") return `${value > 0 ? "+" : ""}${value.toFixed(3)}`;
  if (kind === "signed") return `${value > 0 ? "+" : ""}${value.toFixed(1)}`;
  if (kind === "one") return value.toFixed(1);
  if (kind === "yards") return value.toFixed(1);
  if (kind === "rating") return value.toFixed(1);
  return Math.round(value).toLocaleString("en-US");
}

export function ordinal(value: number): string {
  const mod100 = value % 100;
  if (mod100 >= 11 && mod100 <= 13) return `${value}th`;
  if (value % 10 === 1) return `${value}st`;
  if (value % 10 === 2) return `${value}nd`;
  if (value % 10 === 3) return `${value}rd`;
  return `${value}th`;
}

export function shortName(value: unknown): string {
  if (typeof value !== "string") return "Player";
  const parts = value.replace(/\s+/g, " ").trim().split(" ");
  if (parts.length === 0 || parts[0] === "") return "Player";
  if (parts.length === 1) return parts[0];
  return `${parts[0][0]}. ${parts.slice(1).join(" ")}`;
}

export function teamColor(value: unknown): string {
  return typeof value === "string" && /^#[0-9a-fA-F]{6}$/.test(value)
    ? value
    : "#e4e4e7";
}
