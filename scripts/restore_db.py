import argparse
import os
import shutil
import subprocess
from urllib.parse import urlparse


def parse_args():
    parser = argparse.ArgumentParser(description="Restore Postgres from SQL via docker compose.")
    parser.add_argument("backup_file", help="Path to .sql file")
    parser.add_argument("--db", default="garden_records", help="Database name")
    parser.add_argument("--user", default="postgres", help="Database user")
    parser.add_argument("--host", default="db", help="Database host (direct mode)")
    parser.add_argument("--port", default="5432", help="Database port (direct mode)")
    return parser.parse_args()


def main():
    args = parse_args()
    if not os.path.exists(args.backup_file):
        raise SystemExit(f"Backup file not found: {args.backup_file}")

    use_docker = shutil.which("docker") or shutil.which("docker.exe")
    env = os.environ.copy()
    if not use_docker:
        db_url = env.get("DATABASE_URL")
        if db_url:
            parsed = urlparse(db_url)
            if parsed.scheme.startswith("postgres"):
                if args.db == "garden_records" and parsed.path:
                    args.db = parsed.path.lstrip("/")
                if args.user == "postgres" and parsed.username:
                    args.user = parsed.username
                if args.host == "db" and parsed.hostname:
                    args.host = parsed.hostname
                if args.port == "5432" and parsed.port:
                    args.port = str(parsed.port)
                if parsed.password:
                    env["PGPASSWORD"] = parsed.password
    if use_docker:
        drop_cmd = [
            "docker",
            "compose",
            "exec",
            "-T",
            "db",
            "psql",
            "-U",
            args.user,
            "-d",
            args.db,
            "-c",
            "DROP SCHEMA public CASCADE; CREATE SCHEMA public;",
        ]
    else:
        drop_cmd = [
            "psql",
            "-h",
            args.host,
            "-p",
            str(args.port),
            "-U",
            args.user,
            "-d",
            args.db,
            "-c",
            "DROP SCHEMA public CASCADE; CREATE SCHEMA public;",
        ]
    print("Reset schema...")
    if subprocess.run(drop_cmd, check=False, env=env).returncode != 0:
        raise SystemExit("Schema reset failed.")

    if use_docker:
        restore_cmd = [
            "docker",
            "compose",
            "exec",
            "-T",
            "db",
            "psql",
            "-U",
            args.user,
            "-d",
            args.db,
        ]
    else:
        restore_cmd = [
            "psql",
            "-h",
            args.host,
            "-p",
            str(args.port),
            "-U",
            args.user,
            "-d",
            args.db,
        ]

    print(f"Restoring from {args.backup_file}")
    with open(args.backup_file, "rb") as in_file:
        proc = subprocess.run(restore_cmd, stdin=in_file, check=False, env=env)
    if proc.returncode != 0:
        raise SystemExit("Restore failed.")
    print("Done.")


if __name__ == "__main__":
    main()
