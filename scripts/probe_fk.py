from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]


def database_url() -> str:
    for line in (ROOT / ".env.local").read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("missing")


with psycopg.connect(database_url()) as conn:
    conn.execute("grant update on seasons to nfl_app")
    try:
        print(
            conn.execute(
                "select 1 from only public.seasons x where season = 2026 for key share of x"
            ).fetchall()
        )
    except psycopg.Error as error:
        print("still denied", error.sqlstate, str(error).splitlines()[0])
    conn.rollback()
