"""Responsive dashboard layout checks using only APP_TEST_MODE fictional data."""

from __future__ import annotations

from urllib.parse import urlparse

import pytest
from playwright.sync_api import expect, sync_playwright

from test_browser_login import ARTIFACT_DIR, FAKE_MEMBER_PASSWORD, streamlit_url


VIEWPORTS = (
    ("iphone-375", {"width": 375, "height": 844}),
    ("iphone-390", {"width": 390, "height": 844}),
    ("iphone-402", {"width": 402, "height": 874}),
    ("iphone-430", {"width": 430, "height": 932}),
    ("desktop-1280", {"width": 1280, "height": 900}),
)


def _layout_measurements(page) -> dict[str, object]:
    """Return viewport, key component, and visible overflow measurements."""
    return page.evaluate(
        """
        () => {
          const box = (selector) => {
            const node = document.querySelector(selector);
            if (!node) return null;
            const rect = node.getBoundingClientRect();
            return {
              left: Math.round(rect.left), right: Math.round(rect.right),
              top: Math.round(rect.top), bottom: Math.round(rect.bottom),
              width: Math.round(rect.width), height: Math.round(rect.height),
            };
          };
          const horizontalOverflow = [...document.querySelectorAll('body *')]
            .filter((node) => {
              const style = window.getComputedStyle(node);
              const rect = node.getBoundingClientRect();
              return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0
                && (rect.left < -1 || rect.right > window.innerWidth + 1);
            })
            .map((node) => {
              const rect = node.getBoundingClientRect();
              return {
                tag: node.tagName,
                className: typeof node.className === 'string' ? node.className : '',
                testId: node.getAttribute('data-testid'),
                left: Math.round(rect.left), right: Math.round(rect.right), width: Math.round(rect.width),
              };
            })
            .slice(0, 20);
          const buttonClipping = [...document.querySelectorAll('[data-testid="stButton"] > button')]
            .filter((button) => button.getClientRects().length > 0)
            .map((button) => ({
              text: button.innerText.trim(),
              clientWidth: button.clientWidth,
              scrollWidth: button.scrollWidth,
            }))
            .filter((button) => button.scrollWidth > button.clientWidth + 1);
          return {
            innerWidth: window.innerWidth,
            scrollWidth: document.documentElement.scrollWidth,
            hero: box('.dashboard-hero'),
            notice: box('.dashboard-notice'),
            firstButton: box('[data-testid="stButton"] > button'),
            horizontalOverflow,
            buttonClipping,
          };
        }
        """
    )


def _assert_inside_viewport(name: str, box: dict[str, int] | None, width: int) -> None:
    assert box is not None, f"{name} was not rendered"
    assert box["left"] >= -1, f"{name} extends left of the viewport: {box}"
    assert box["right"] <= width + 1, f"{name} extends right of the viewport: {box}"


@pytest.mark.parametrize(("name", "viewport"), VIEWPORTS)
def test_dashboard_has_no_horizontal_overflow(streamlit_url, name, viewport) -> None:
    """Keep the member dashboard inside the viewport at phone and desktop widths."""
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
        expect(page.locator(".dashboard-hero")).to_be_visible(timeout=20_000)
        expect(page.locator(".dashboard-notice")).to_be_visible(timeout=20_000)
        expect(page.get_by_role("button", name="個人成績を見る", exact=True)).to_be_visible(timeout=20_000)

        measurements = _layout_measurements(page)
        assert measurements["innerWidth"] == viewport["width"]
        assert measurements["scrollWidth"] <= measurements["innerWidth"] + 1, measurements
        assert not measurements["horizontalOverflow"], measurements
        assert not measurements["buttonClipping"], measurements
        _assert_inside_viewport("hero", measurements["hero"], viewport["width"])
        _assert_inside_viewport("notice", measurements["notice"], viewport["width"])
        _assert_inside_viewport("first dashboard button", measurements["firstButton"], viewport["width"])

        page.screenshot(path=str(ARTIFACT_DIR / f"dashboard-layout-{name}.png"), full_page=True)
        context.close()
        browser.close()

    assert not external_requests, f"Unexpected external request(s): {external_requests}"
    assert not page_errors, f"JavaScript page error(s): {page_errors}"
    assert not console_errors, f"JavaScript console error(s): {console_errors}"
