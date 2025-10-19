"""Helper to invoke the pgvector verification SQL in a cross-platform way."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit, urlunsplit


def _load_env_from_file(env_path: Path) -> None:
    """Populate os.environ with values from `.env` if they are not already set."""
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key = key.strip()
        if not key or key in os.environ:
            continue
        cleaned = value.strip()
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (
            cleaned.startswith("'") and cleaned.endswith("'")
        ):
            cleaned = cleaned[1:-1]
        os.environ[key] = cleaned


def main() -> int:
    _load_env_from_file(Path(".env"))

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set. Export it before running db.verify.", file=sys.stderr)
        return 1

    sql_path = Path("scripts/verify_pgvector.sql")
    if not sql_path.exists():
        print("scripts/verify_pgvector.sql not found.", file=sys.stderr)
        return 1

    dimension = os.environ.get("PGVECTOR_DIMENSION", "3072")
    lists = os.environ.get("PGVECTOR_LISTS", "100")
    probes = os.environ.get("PGVECTOR_PROBES", "4")
    sql_template = sql_path.read_text(encoding="utf-8")
    sql_rendered = (
        sql_template.replace(":expected_pgvector_dimension", dimension)
        .replace(":expected_pgvector_lists", lists)
        .replace(":expected_pgvector_probes", probes)
    )

    with NamedTemporaryFile("w", encoding="utf-8", suffix=".sql", delete=False) as tmp_file:
        tmp_file.write(sql_rendered)
        tmp_path = Path(tmp_file.name)

    extra_cleanup: list[list[str]] = [["rm", "-f", str(tmp_path)]]

    psql_path = shutil.which("psql")
    docker_path = shutil.which("docker")
    docker_compose_path = shutil.which("docker-compose")

    compose_base: list[str] | None = None

    adjusted_database_url = database_url

    if psql_path:
        command_prefix: list[str] = [psql_path]
        sql_arg = str(tmp_path)
    else:
        if docker_path:
            compose_base = [docker_path, "compose"]
        elif docker_compose_path:
            compose_base = [docker_compose_path]
        else:
            print(
                "psql is required but not found on PATH, and docker compose is unavailable for fallback execution.",
                file=sys.stderr,
            )
            return 1

        command_prefix = [*compose_base, "exec", "-T", "postgres", "psql"]
        remote_path = "/tmp/verify_pgvector.sql"
        copy_cmd = [*compose_base, "cp", str(tmp_path), f"postgres:{remote_path}"]
        subprocess.run(copy_cmd, check=True)
        sql_arg = remote_path
        extra_cleanup.append([*compose_base, "exec", "-T", "postgres", "rm", "-f", remote_path])

        parsed = urlsplit(database_url)
        host_port = os.environ.get("POSTGRES_PORT")
        try:
            host_port_int = int(host_port) if host_port else None
        except ValueError:
            host_port_int = None

        if parsed.hostname in {"localhost", "127.0.0.1"} and host_port_int is not None:
            if parsed.port == host_port_int:
                userinfo = ""
                if parsed.username:
                    userinfo = parsed.username
                    if parsed.password:
                        userinfo = f"{userinfo}:{parsed.password}"
                    userinfo = f"{userinfo}@"
                netloc = f"{userinfo}{parsed.hostname}:5432"
                adjusted_database_url = urlunsplit(parsed._replace(netloc=netloc))

    cmd: list[str] = [
        *command_prefix,
        "--dbname",
        adjusted_database_url,
        "-v",
        f"expected_pgvector_dimension={dimension}",
        "-v",
        f"expected_pgvector_lists={lists}",
        "-v",
        f"expected_pgvector_probes={probes}",
        "-f",
        sql_arg,
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    finally:
        for cleanup_cmd in extra_cleanup:
            try:
                if cleanup_cmd[0] == "rm":
                    Path(cleanup_cmd[-1]).unlink(missing_ok=True)
                else:
                    subprocess.run(cleanup_cmd, check=False)
            except Exception:
                pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
