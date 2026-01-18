import argparse
import os
import shutil
import subprocess
from datetime import datetime
from urllib.parse import urlparse


def parse_args():
    parser = argparse.ArgumentParser(description="Backup Postgres to SQL via docker compose.")
    parser.add_argument(
        "--output",
        help="Output SQL file path (default: backups/garden_records_YYYYMMDD-HHMMSS.sql)",
    )
    parser.add_argument("--db", default="garden_records", help="Database name")
    parser.add_argument("--user", default="postgres", help="Database user")
    parser.add_argument("--host", default="db", help="Database host (direct mode)")
    parser.add_argument("--port", default="5432", help="Database port (direct mode)")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.output:
        out_path = args.output
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backups_dir = os.path.join(os.path.dirname(__file__), "..", "backups")
        os.makedirs(backups_dir, exist_ok=True)
        out_path = os.path.join(backups_dir, f"garden_records_{stamp}.sql")

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
        cmd = [
            "docker",
            "compose",
            "exec",
            "-T",
            "db",
            "pg_dump",
            "-U",
            args.user,
            "-d",
            args.db,
            "-F",
            "p",
        ]
    else:
        cmd = [
            "pg_dump",
            "-h",
            args.host,
            "-p",
            str(args.port),
            "-U",
            args.user,
            "-d",
            args.db,
            "-F",
            "p",
        ]

    print(f"Backup to {out_path}")
    with open(out_path, "wb") as out_file:
        proc = subprocess.run(cmd, stdout=out_file, check=False, env=env)
    if proc.returncode != 0:
        raise SystemExit("Backup failed.")
    print("Done.")


if __name__ == "__main__":
    main()
