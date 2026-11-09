from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]


def database_url() -> str:
    for line in (ROOT / ".env.local").read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("missing")


with psycopg.connect(database_url()) as conn:
    conn.execute(
        "create policy notebook_user_delete on notebook_user for delete to nfl_app using (true)"
    )
    removed = conn.execute("delete from notebook_user where display_name = 'probe'").rowcount
    left = conn.execute(
        "select (select count(*) from notebook_user), (select count(*) from saved_pick), (select count(*) from note)"
    ).fetchone()
    conn.commit()
print("removed", removed, "left", left)
