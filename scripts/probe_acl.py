from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]


def database_url() -> str:
    for line in (ROOT / ".env.local").read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("missing")


with psycopg.connect(database_url()) as conn:
    print(conn.execute("select current_user, session_user").fetchone())
    print(conn.execute("select relname, relowner::regrole, relacl from pg_class where relname in ('seasons','teams','notebook_user','saved_pick')").fetchall())
    print("select seasons", conn.execute("select count(*) from seasons").fetchone())
