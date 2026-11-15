from pathlib import Path

from streamlit.testing.v1 import AppTest


def make_app(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "app"))
    monkeypatch.setenv("APP_TEST_MODE", "1")
    monkeypatch.setenv("E2E_USER_PASSWORD", "fictional-member-password")
    monkeypatch.setenv("E2E_ADMIN_PASSWORD", "fictional-admin-password")
    app = AppTest.from_file(str(root / "app" / "app.py"), default_timeout=20)
    app.run()
    app.session_state.page = "admin"
    app.run()
    assert not app.exception
    return app


def test_admin_login_rejects_wrong_password(monkeypatch):
    app = make_app(monkeypatch)
    app.button(key="FormSubmitter:admin_login_form-ログイン").click().run()
    assert not app.session_state.admin_logged_in
    app.text_input(key="admin_password_input").input("incorrect-fictional").run()
    app.button(key="FormSubmitter:admin_login_form-ログイン").click().run()
    assert not app.session_state.admin_logged_in
    assert any(error.value == "パスワードが間違っています" for error in app.error)


def test_admin_login_accepts_correct_password(monkeypatch):
    app = make_app(monkeypatch)
    app.text_input(key="admin_password_input").input("fictional-admin-password").run()
    app.button(key="FormSubmitter:admin_login_form-ログイン").click().run()
    assert app.session_state.admin_logged_in
    assert not app.exception


def test_admin_login_has_return_to_member_login(monkeypatch):
    app = make_app(monkeypatch)
    app.button(key="admin_login_back").click().run()
    assert app.session_state.page == "login"
    assert not app.session_state.admin_logged_in
    assert not app.exception
