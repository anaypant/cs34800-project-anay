"""Apply db/002_notebook.sql with SQL, then show that the new tables exist."""

from pathlib import Path

import psycopg
from psycopg.pq import ExecStatus

ROOT = Path(__file__).resolve().parents[1]


def database_url() -> str:
    for line in (ROOT / ".env.local").read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("DATABASE_URL is missing from .env.local")


def main() -> None:
    path = ROOT / "db" / "002_notebook.sql"
    with psycopg.connect(database_url()) as conn:
        result = conn.pgconn.exec_(path.read_bytes())
        if result.status not in (ExecStatus.COMMAND_OK, ExecStatus.TUPLES_OK):
            message = result.error_message.decode() if result.error_message else "notebook sql failed"
            raise SystemExit(message)
        rows = conn.execute(
            """
            select c.relname, c.relrowsecurity, c.relforcerowsecurity
            from pg_class c
            join pg_namespace n on n.oid = c.relnamespace
            where n.nspname = 'public'
              and c.relname in ('notebook_user', 'saved_pick', 'note')
            order by c.relname
            """
        ).fetchall()
        grants = conn.execute(
            """
            select table_name, grantee, privilege_type
            from information_schema.role_table_grants
            where table_schema = 'public'
              and table_name in ('notebook_user', 'saved_pick', 'note')
            order by table_name, grantee, privilege_type
            """
        ).fetchall()
    print("tables", rows)
    print("grants", grants)


if __name__ == "__main__":
    main()
