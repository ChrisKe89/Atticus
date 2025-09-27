"""E2E smoke checks for Atticus API and UI make targets."""

from __future__ import annotations

import contextlib
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import requests

HOST = os.environ.get("ATTICUS_E2E_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("ATTICUS_API_PORT", "8000"))
UI_PORT = int(os.environ.get("ATTICUS_UI_PORT", "8081"))
ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"


class ManagedProcess:
    """Launch a long-running command and surface logs if checks fail."""

    def __init__(self, name: str, args: list[str], cwd: Path) -> None:
        self.name = name
        self.args = args
        self.cwd = cwd
        self.proc: subprocess.Popen | None = None
        self.stdout: str = ""
        self.stderr: str = ""
        self._should_dump = False

    def __enter__(self) -> ManagedProcess:
        self.proc = subprocess.Popen(
            self.args,
            cwd=self.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._should_dump = exc_type is not None
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
        if self.proc:
            try:
                out, err = self.proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                out, err = self.proc.communicate()
            self.stdout = out or ""
            self.stderr = err or ""
            if self._should_dump:
                if self.stdout.strip():
                    print(f"[{self.name} stdout]\n{self.stdout}")
                if self.stderr.strip():
                    print(f"[{self.name} stderr]\n{self.stderr}", file=sys.stderr)
        return False


def wait_for_port(host: str, port: int, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(1.0)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for {host}:{port}")


def request_with_retry(url: str, *, attempts: int = 5, delay: float = 0.5) -> requests.Response:
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(delay)
    raise RuntimeError(f"Failed to GET {url}") from last_error


def check_api(host: str, port: int) -> None:
    base = f"http://{host}:{port}"
    health = request_with_retry(f"{base}/health")
    payload = health.json()
    if payload.get("status") != "ok":
        raise RuntimeError("API health check did not return status 'ok'")

    root_page = request_with_retry(f"{base}/")
    lower_html = root_page.text.lower()
    if "<html" not in lower_html or "atticus" not in lower_html:
        raise RuntimeError("API root did not render an Atticus UI shell")
    if "/static/" not in lower_html:
        raise RuntimeError("API root is missing static asset references")

    static_asset = request_with_retry(f"{base}/static/js/script.js")
    if not static_asset.text.strip():
        raise RuntimeError("API static assets are empty or missing")


def check_ui(host: str, port: int) -> None:
    base = f"http://{host}:{port}"
    ui_page = request_with_retry(f"{base}/templates/index.html")
    lower_html = ui_page.text.lower()
    if "<html" not in lower_html or "atticus" not in lower_html:
        raise RuntimeError("Standalone UI did not include Atticus branding")
    if "/static/" not in lower_html:
        raise RuntimeError("Standalone UI page is missing static asset references")

    ui_script = request_with_retry(f"{base}/static/js/script.js")
    if not ui_script.text.strip():
        raise RuntimeError("Standalone UI cannot serve static JavaScript")


def main() -> None:
    if not WEB_DIR.exists():
        raise RuntimeError(f"Expected UI directory at {WEB_DIR}")

    api_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "api.main:app",
        "--port",
        str(API_PORT),
    ]
    ui_cmd = [
        sys.executable,
        "-m",
        "http.server",
        str(UI_PORT),
        "--directory",
        str(WEB_DIR),
    ]

    with ManagedProcess("api", api_cmd, ROOT):
        wait_for_port(HOST, API_PORT)
        check_api(HOST, API_PORT)
        print(f"API smoke passed on {HOST}:{API_PORT}")

        with ManagedProcess("ui", ui_cmd, ROOT):
            wait_for_port(HOST, UI_PORT)
            check_ui(HOST, UI_PORT)
            print(f"UI static smoke passed on {HOST}:{UI_PORT}")

    print("E2E API/UI checks completed.")


if __name__ == "__main__":
    main()
