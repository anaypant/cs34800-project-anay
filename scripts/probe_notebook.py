"""Prove notebook writes succeed and NFL fact tables still reject writes."""

from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]


def database_url() -> str:
    for line in (ROOT / ".env.local").read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("DATABASE_URL is missing from .env.local")


def main() -> None:
    with psycopg.connect(database_url()) as conn:
        with conn.transaction():
            user_id = conn.execute(
                "insert into notebook_user (display_name) values (%s) returning user_id",
                ("probe",),
            ).fetchone()[0]
            conn.execute(
                """
                insert into saved_pick (user_id, season, target_kind, target_id)
                values (%s, 2026, 'team', 'BUF')
                """,
                (user_id,),
            )
            conn.execute(
                """
                insert into note (user_id, season, target_kind, target_id, body)
                values (%s, 2026, 'player', '00-0037248', 'probe note')
                """,
                (user_id,),
            )
            conn.execute(
                """
                update note set body = 'probe note edited', updated_at = now()
                where user_id = %s
                """,
                (user_id,),
            )
            blocked_target = False
            try:
                with conn.transaction():
                    conn.execute(
                        """
                        insert into saved_pick (user_id, season, target_kind, target_id)
                        values (%s, 2026, 'team', 'ZZZ')
                        """,
                        (user_id,),
                    )
            except psycopg.Error as error:
                blocked_target = "did not play" in str(error)
            fact_blocked = False
            try:
                with conn.transaction():
                    conn.execute("insert into data_source (name, coverage) values ('probe', 'probe')")
            except psycopg.Error as error:
                fact_blocked = error.sqlstate == "42501"
            conn.execute("delete from notebook_user where user_id = %s", (user_id,))
            left = conn.execute("select count(*) from notebook_user").fetchone()[0]
    print("blocked_target", blocked_target)
    print("fact_blocked", fact_blocked)
    print("users_left", left)


if __name__ == "__main__":
    main()
