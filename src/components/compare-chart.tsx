"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatMetric, type FormatKind } from "@/lib/format";

export type ChartPoint = {
  name: string;
  value: number;
  selected: boolean;
};

export function CompareChart({
  title,
  caption,
  note,
  points,
  color,
  format,
}: {
  title: string;
  caption: string;
  note?: string;
  points: ChartPoint[];
  color: string;
  format: FormatKind;
}) {
  const height = Math.max(280, points.length * 24 + 36);
  const ordered = points;
  return (
    <section className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4" aria-label={title}>
      <h3 className="text-sm font-medium text-zinc-100">{title}</h3>
      <p className="mt-1 text-sm text-zinc-400">{caption}</p>
      {note ? <p className="mt-1 text-xs leading-5 text-zinc-500">{note}</p> : null}
      <div className="mt-3" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={ordered}
            layout="vertical"
            margin={{ top: 4, right: 20, left: 4, bottom: 4 }}
          >
            <CartesianGrid horizontal={false} stroke="#27272a" />
            <XAxis
              type="number"
              tick={{ fill: "#a1a1aa", fontSize: 11 }}
              axisLine={{ stroke: "#3f3f46" }}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={118}
              interval={0}
              tick={{ fill: "#e4e4e7", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            {points.some((point) => point.value < 0) ? (
              <ReferenceLine x={0} stroke="#52525b" />
            ) : null}
            <Tooltip
              cursor={{ fill: "rgba(255,255,255,0.04)" }}
              content={({ active, payload }) => {
                const item = payload?.[0];
                if (!active || !item || typeof item.value !== "number") return null;
                const name = item.payload && typeof item.payload === "object" && "name" in item.payload
                  ? String(item.payload.name)
                  : "";
                return (
                  <div className="rounded-md bg-zinc-950 px-2 py-1 text-xs text-zinc-100 ring-1 ring-zinc-700">
                    {name}: {formatMetric(item.value, format)}
                  </div>
                );
              }}
            />
            <Bar dataKey="value" radius={2} isAnimationActive={false}>
              {ordered.map((point) => (
                <Cell key={point.name} fill={point.selected ? color : "#52525b"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
