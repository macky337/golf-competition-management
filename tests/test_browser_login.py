"""Browser smoke tests that never load local Supabase credentials.

The Streamlit process is started with APP_TEST_MODE=1.  In that mode the
application deliberately clears Supabase configuration and uses only the
fictional E2E login credentials defined below.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

import pytest
from playwright.sync_api import expect, sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = PROJECT_ROOT / "test-results" / "playwright"
FAKE_MEMBER_PASSWORD = "e2e-member-password"


def _available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _wait_for_server(url: str, process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Streamlit exited before the browser test could start.")
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.25)
    raise TimeoutError("Timed out waiting for the local Streamlit server.")


@pytest.fixture(scope="module")
def streamlit_url():
    """Start a local, DB-disabled Streamlit process for browser tests."""
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    port = _available_port()
    url = f"http://127.0.0.1:{port}"
    environment = os.environ.copy()
    for name in (
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "DATABASE_URL",
        "USER_PASSWORD",
        "ADMIN_PASSWORD",
    ):
        environment.pop(name, None)
    environment.update(
        {
            "APP_TEST_MODE": "1",
            "E2E_USER_PASSWORD": FAKE_MEMBER_PASSWORD,
            "E2E_ADMIN_PASSWORD": "e2e-admin-password",
            "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
            "PYTHONUNBUFFERED": "1",
        }
    )

    log_path = ARTIFACT_DIR / "streamlit.log"
    with log_path.open("wb") as log_file:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app/app.py",
                "--server.address=127.0.0.1",
                f"--server.port={port}",
                "--server.headless=true",
            ],
            cwd=PROJECT_ROOT,
            env=environment,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        try:
            _wait_for_server(url, process)
            yield url
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)


@pytest.mark.parametrize(
    ("name", "viewport"),
    [
        ("desktop", {"width": 1280, "height": 900}),
        ("mobile", {"width": 390, "height": 844}),
    ],
)
def test_login_screen_renders_without_supabase_requests(streamlit_url, name, viewport):
    """Confirm both viewports render the login form without external DB traffic."""
    external_requests: list[str] = []
    page_errors: list[str] = []
    console_errors: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport=viewport)
        page = context.new_page()

        def record_request(request) -> None:
            host = urlparse(request.url).hostname
            if host not in {"127.0.0.1", "localhost", None}:
                external_requests.append(request.url)

        page.on("request", record_request)
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.on(
            "console",
            lambda message: console_errors.append(message.text) if message.type == "error" else None,
        )

        response = page.goto(streamlit_url, wait_until="domcontentloaded")
        assert response is not None and response.ok
        expect(page.get_by_text("会員ログイン", exact=True)).to_be_visible(timeout=20_000)
        password_input = page.get_by_label("パスワード", exact=True)
        password_input.fill(FAKE_MEMBER_PASSWORD)
        expect(password_input).to_have_value(FAKE_MEMBER_PASSWORD)
        page.screenshot(path=str(ARTIFACT_DIR / f"login-{name}.png"), full_page=True)

        context.close()
        browser.close()

    assert not external_requests, f"Unexpected external request(s): {external_requests}"
    assert not page_errors, f"JavaScript page error(s): {page_errors}"
    assert not console_errors, f"JavaScript console error(s): {console_errors}"
