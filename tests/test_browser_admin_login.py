"""Admin authentication uses only fictional local credentials, never a database."""

from urllib.parse import urlparse

import pytest
from playwright.sync_api import expect, sync_playwright

from test_browser_login import ARTIFACT_DIR, FAKE_MEMBER_PASSWORD, streamlit_url


def watch_local_page(page, external_requests, errors):
    def guard(route):
        if urlparse(route.request.url).hostname not in {"localhost", "127.0.0.1"}:
            external_requests.append(route.request.url)
            route.abort()
        else:
            route.continue_()
    page.route("**/*", guard)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)


@pytest.mark.parametrize("engine", ["chromium", "webkit"])
@pytest.mark.parametrize("width", [390, 1280])
def test_admin_login_from_dashboard(streamlit_url, engine, width):
    external_requests, errors = [], []
    with sync_playwright() as playwright:
        browser = getattr(playwright, engine).launch()
        context = browser.new_context(viewport={"width": width, "height": 900})
        page = context.new_page()

        watch_local_page(page, external_requests, errors)
        page.goto(streamlit_url)
        page.get_by_label("パスワード", exact=True).fill(FAKE_MEMBER_PASSWORD)
        page.get_by_role("button", name="ログイン", exact=True).click()
        page.get_by_role("button", name="⚙️ 管理メニュー", exact=True).click()
        expect(page.get_by_role("heading", name="管理者ログイン", exact=True)).to_be_visible()
        password = page.get_by_label("管理者パスワードを入力してください", exact=True)
        expect(password).to_be_visible()
        expect(password).to_be_in_viewport()
        page.screenshot(path=str(ARTIFACT_DIR / f"admin-login-{engine}-{width}.png"), full_page=True)
        password.fill("incorrect-fictional-password")
        page.get_by_role("button", name="ログイン", exact=True).click()
        expect(page.get_by_text("パスワードが間違っています", exact=True)).to_be_visible()
        password.fill("e2e-admin-password")
        password.press("Enter")
        expect(page.get_by_role("heading", name="88会 運営メニュー", exact=True)).to_be_visible()
        # In test mode the authenticated admin DB client remains disabled.
        expect(page.get_by_text("管理者用クライアントの初期化に失敗しました。設定を確認してください。", exact=True)).to_be_visible()
        expect(page.locator('[data-testid="stException"]')).to_have_count(0)
        page.screenshot(path=str(ARTIFACT_DIR / f"admin-{engine}-{width}.png"), full_page=True)
        context.close()
        browser.close()
    assert not external_requests
    assert not errors


@pytest.mark.parametrize("engine", ["chromium", "webkit"])
def test_direct_admin_entry_requires_authentication(streamlit_url, engine):
    external_requests, errors = [], []
    with sync_playwright() as playwright:
        browser = getattr(playwright, engine).launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        watch_local_page(page, external_requests, errors)
        page.goto(streamlit_url + "?view=admin")
        expect(page.get_by_role("heading", name="管理者ログイン", exact=True)).to_be_visible()
        expect(page.get_by_label("管理者パスワードを入力してください", exact=True)).to_be_in_viewport()
        expect(page.get_by_role("heading", name="88会 運営メニュー", exact=True)).to_have_count(0)
        page.screenshot(path=str(ARTIFACT_DIR / f"admin-direct-{engine}.png"), full_page=True)
        page.get_by_role("button", name="会員ログインへ", exact=True).click()
        expect(page.get_by_text("会員ログイン", exact=True)).to_be_visible()
        expect(page.locator('[data-testid="stException"]')).to_have_count(0)
        browser.close()
    assert not external_requests
    assert not errors
