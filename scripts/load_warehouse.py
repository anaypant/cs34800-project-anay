"""Apply db/schema.sql and copy the local warehouse into Postgres."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import psycopg
import pyarrow.parquet as pq
from psycopg.pq import ExecStatus

ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = ROOT / "data" / "warehouse"
RAW = ROOT / "data" / "raw"


def database_url() -> str:
    for line in (ROOT / ".env.local").read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("DATABASE_URL is missing from .env.local")


def apply_script(conn: psycopg.Connection, path: Path) -> None:
    result = conn.pgconn.exec_(path.read_bytes())
    if result.status not in (ExecStatus.COMMAND_OK, ExecStatus.TUPLES_OK):
        message = result.error_message.decode() if result.error_message else "schema failed"
        raise SystemExit(message)


def column_types(conn: psycopg.Connection, table: str) -> list[tuple[str, str]]:
    rows = conn.execute(
        """
        select column_name, data_type
        from information_schema.columns
        where table_schema = 'public' and table_name = %s
        order by ordinal_position
        """,
        (table,),
    ).fetchall()
    return [(row[0], row[1]) for row in rows]


def blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return bool(pd.isna(value))


def csv_value(value: object, kind: str) -> str | None:
    if blank(value):
        return None
    if kind == "boolean":
        return "true" if bool(value) else "false"
    if kind == "date":
        return pd.Timestamp(value).strftime("%Y-%m-%d")
    if kind in {"integer", "bigint", "smallint"}:
        return str(int(value))
    if kind == "double precision":
        return f"{float(value):.10g}"
    return str(value)


def copy_frame(conn: psycopg.Connection, table: str, frame: pd.DataFrame) -> None:
    types = column_types(conn, table)
    missing = [name for name, _kind in types if name not in frame.columns]
    if missing:
        raise SystemExit(f"{table} is missing {missing}")
    columns = [name for name, _kind in types]
    kind_of = dict(types)
    buffer = []
    for record in frame[columns].itertuples(index=False, name=None):
        cells = []
        for name, value in zip(columns, record):
            text = csv_value(value, kind_of[name])
            if text is None:
                cells.append("\\N")
            else:
                escaped = text.replace("\\", "\\\\").replace("\n", " ").replace("\r", " ")
                if any(character in escaped for character in [",", '"']):
                    escaped = '"' + escaped.replace('"', '""') + '"'
                cells.append(escaped)
        buffer.append(",".join(cells))
    payload = ("\n".join(buffer) + "\n").encode()
    column_list = ", ".join(columns)
    with conn.cursor() as cur:
        with cur.copy(
            f"copy {table} ({column_list}) from stdin with (format csv, null '\\N')"
        ) as copy:
            copy.write(payload)
    print(table, len(frame))


def force_read_only(conn: psycopg.Connection) -> None:
    tables = [
        "seasons",
        "data_source",
        "teams",
        "players",
        "games",
        "roster",
        "team_game",
        "player_game",
        "team_season_summary",
    ]
    for table in tables:
        conn.execute(f"alter table {table} force row level security")
    conn.execute(
        "revoke insert, update, delete, truncate on all tables in schema public from nfl_app"
    )
    conn.execute("revoke create on schema public from nfl_app")
    conn.execute("revoke all on procedure refresh_team_season_summary() from nfl_app")


def main() -> None:
    with psycopg.connect(database_url()) as conn:
        if conn.execute("select to_regclass('public.team_game')").fetchone()[0] is None:
            apply_script(conn, ROOT / "db" / "schema.sql")
            conn.commit()
            print("schema applied")
        loaded = conn.execute("select count(*) from team_game").fetchone()[0]
        if loaded == 0:
            teams = pq.read_table(RAW / "teams.parquet").to_pandas()
            copy_frame(
                conn,
                "teams",
                teams[
                    [
                        "team_abbr",
                        "team_name",
                        "team_nick",
                        "team_conf",
                        "team_division",
                        "team_color",
                        "team_color2",
                        "team_logo_espn",
                    ]
                ],
            )
            copy_frame(conn, "players", pq.read_table(WAREHOUSE / "players.parquet").to_pandas())
            copy_frame(conn, "games", pq.read_table(WAREHOUSE / "games.parquet").to_pandas())
            copy_frame(conn, "roster", pq.read_table(WAREHOUSE / "roster.parquet").to_pandas())
            copy_frame(conn, "team_game", pq.read_table(WAREHOUSE / "team_game.parquet").to_pandas())
            copy_frame(conn, "player_game", pq.read_table(WAREHOUSE / "player_game.parquet").to_pandas())
            conn.commit()
        conn.execute("call refresh_team_season_summary()")
        force_read_only(conn)
        conn.commit()
        summary = conn.execute(
            """
            select season,
                   count(*) as teams,
                   round(avg(sack_rate)::numeric, 3) as sack_rate,
                   round(avg(blitz_rate)::numeric, 3) as blitz_rate,
                   round(avg(start_yardline)::numeric, 1) as start_yardline
            from v_team_reg
            group by season
            order by season
            """
        ).fetchall()
        print("team seasons", summary)
        players = conn.execute("select count(*) from v_player_reg").fetchone()[0]
        print("player season rows", players)
        class WriteProbe(Exception):
            def __init__(self, blocked: bool, sqlstate: str | None = None) -> None:
                self.blocked = blocked
                self.sqlstate = sqlstate

        try:
            with conn.transaction():
                try:
                    conn.execute(
                        "insert into data_source (name, coverage) values ('should fail', 'no')"
                    )
                except psycopg.Error as exc:
                    raise WriteProbe(True, exc.sqlstate) from exc
                raise WriteProbe(False)
        except WriteProbe as probe:
            if not probe.blocked:
                raise SystemExit("writes were not blocked")
            print("writes blocked", probe.sqlstate)


if __name__ == "__main__":
    main()
