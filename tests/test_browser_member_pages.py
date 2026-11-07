"""Member-page browser journeys using only APP_TEST_MODE fictional data."""

from __future__ import annotations

from urllib.parse import urlparse

import pytest
from playwright.sync_api import expect, sync_playwright

from test_browser_login import ARTIFACT_DIR, FAKE_MEMBER_PASSWORD, streamlit_url


def _assert_no_streamlit_exception(page) -> None:
    assert page.locator('[data-testid="stException"]').count() == 0
    assert page.locator("text=Traceback").count() == 0


@pytest.mark.parametrize(
    ("name", "viewport"),
    [
        ("desktop", {"width": 1280, "height": 900}),
        ("mobile", {"width": 390, "height": 844}),
    ],
)
def test_member_pages_render_with_fictional_data(streamlit_url, name, viewport):
    """Log in, visit every member page, and log out without external traffic."""
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
        page.get_by_label("パスワード", exact=True).fill(FAKE_MEMBER_PASSWORD)
        page.get_by_role("button", name="ログイン", exact=True).click()

        expect(page.get_by_role("button", name="個人成績を見る", exact=True)).to_be_visible(timeout=20_000)
        _assert_no_streamlit_exception(page)
        page.screenshot(path=str(ARTIFACT_DIR / f"member-{name}-dashboard.png"), full_page=True)

        page.get_by_role("button", name="個人成績を見る", exact=True).click()
        expect(page.get_by_text("テスト 太郎 さんのゴルフノート", exact=True)).to_be_visible(timeout=20_000)
        _assert_no_streamlit_exception(page)
        page.screenshot(path=str(ARTIFACT_DIR / f"member-{name}-stats.png"), full_page=True)
        page.get_by_role("button", name="← メイン画面へ", exact=True).click()
        expect(page.get_by_role("button", name="個人成績を見る", exact=True)).to_be_visible(timeout=20_000)

        page.get_by_role("button", name="競技結果を見る", exact=True).click()
        expect(page.locator(".dashboard-section-label", has_text="完全順位表")).to_be_visible(timeout=20_000)
        expect(page.get_by_role("heading", name="第55回 競技結果", exact=True)).to_be_visible(timeout=20_000)
        expect(page.locator("p", has_text="モックレイクGC")).to_be_visible(timeout=20_000)
        _assert_no_streamlit_exception(page)
        page.screenshot(path=str(ARTIFACT_DIR / f"member-{name}-results.png"), full_page=True)
        page.get_by_role("button", name="← メイン画面へ", exact=True).click()
        expect(page.get_by_role("button", name="個人成績を見る", exact=True)).to_be_visible(timeout=20_000)

        page.get_by_role("button", name="ランキング", exact=True).click()
        expect(page.get_by_text("実力系ランキング", exact=True)).to_be_visible(timeout=20_000)
        expect(page.get_by_text("テスト 太郎", exact=True).first).to_be_visible(timeout=20_000)
        _assert_no_streamlit_exception(page)
        page.screenshot(path=str(ARTIFACT_DIR / f"member-{name}-rankings.png"), full_page=True)
        page.get_by_role("button", name="← メイン画面へ", exact=True).click()
        expect(page.get_by_role("button", name="個人成績を見る", exact=True)).to_be_visible(timeout=20_000)

        page.get_by_role("button", name="↗ ログアウト", exact=True).click()
        expect(page.get_by_text("会員ログイン", exact=True)).to_be_visible(timeout=20_000)
        _assert_no_streamlit_exception(page)
        page.screenshot(path=str(ARTIFACT_DIR / f"member-{name}-logout.png"), full_page=True)

        context.close()
        browser.close()

    assert not external_requests, f"Unexpected external request(s): {external_requests}"
    assert not page_errors, f"JavaScript page error(s): {page_errors}"
    assert not console_errors, f"JavaScript console error(s): {console_errors}"
