import importlib
import ast
from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


class ScoreQuery:
    def __init__(self):
        self.upsert_rows = None
        self.on_conflict = None
        self.delete_called = False

    def delete(self):
        self.delete_called = True
        return self

    def upsert(self, rows, on_conflict):
        self.upsert_rows = rows
        self.on_conflict = on_conflict
        return self

    def execute(self):
        return object()


class SupabaseStub:
    def __init__(self):
        self.scores = ScoreQuery()

    def table(self, name):
        assert name == "scores"
        return self.scores


class SessionStateStub(dict):
    def __getattr__(self, name):
        return self[name]


def test_save_scores_upserts_without_deleting_existing_rows(monkeypatch):
    score_entry = importlib.import_module("score_entry")
    supabase = SupabaseStub()
    monkeypatch.setattr(score_entry, "get_supabase_client", lambda: supabase)
    monkeypatch.setattr(
        score_entry.st,
        "session_state",
        SessionStateStub({
            "competitions": pd.DataFrame(
                [{"competition_id": 7, "date": "2026-07-18", "course": "Test Course"}]
            )
        }),
    )

    saved = score_entry.save_scores(
        7,
        {
            10: {
                "out_score": 40,
                "in_score": 41,
                "handicap": 10,
                "net_score": 71,
            }
        },
        pd.DataFrame(),
    )

    assert saved is True
    assert supabase.scores.delete_called is False
    assert supabase.scores.on_conflict == "competition_id,player_id"
    assert supabase.scores.upsert_rows[0]["competition_id"] == 7
    assert supabase.scores.upsert_rows[0]["player_id"] == 10


def test_initial_schema_uses_competition_id_consistently():
    sql = (PROJECT_ROOT / "migrations" / "0001_initial_schema.sql").read_text(encoding="utf-8")
    assert "competition_id SERIAL PRIMARY KEY" in sql
    assert "REFERENCES competitions(competition_id)" in sql
    assert "REFERENCES competitions(id)" not in sql


def test_atomic_restore_is_restricted_to_service_role():
    sql = (PROJECT_ROOT / "migrations" / "0002_atomic_restore.sql").read_text(encoding="utf-8")
    assert "CREATE OR REPLACE FUNCTION restore_golf_database" in sql
    assert "ALTER TABLE competitions RENAME COLUMN id TO competition_id" in sql
    assert "SECURITY DEFINER" in sql
    assert "REVOKE ALL ON FUNCTION restore_golf_database(JSONB) FROM PUBLIC" in sql
    assert "GRANT EXECUTE ON FUNCTION restore_golf_database(JSONB) TO service_role" in sql


def test_application_does_not_contain_default_passwords_or_secret_output():
    app_source = (APP_DIR / "app.py").read_text(encoding="utf-8")
    score_source = (APP_DIR / "score_entry.py").read_text(encoding="utf-8")
    combined = app_source + score_source
    assert 'or "admin88"' not in combined
    assert 'or "88"' not in combined
    assert 'st.write("DEBUG: from secrets' not in app_source
    assert 'st.write("DEBUG: from env' not in app_source
    assert 'supabase.rpc("restore_golf_database"' in app_source


def test_deployment_environment_variables_take_precedence_over_local_dotenv():
    app_source = (APP_DIR / "app.py").read_text(encoding="utf-8-sig")
    assert "load_dotenv(dotenv_path=dotenv_path, override=False)" in app_source


def test_member_dashboard_has_direct_scorecard_import_route():
    app_source = (APP_DIR / "app.py").read_text(encoding="utf-8-sig")
    assert "📷  スコアカード画像を読み込む" in app_source
    assert '_navigate("scorecard_import")' in app_source
    assert 'elif page == "scorecard_import":' in app_source
    assert "score_entry_tab(score_entry_client)" in app_source


def test_winner_count_includes_ranked_history_without_score_details():
    app_path = APP_DIR / "app.py"
    module = ast.parse(app_path.read_text(encoding="utf-8-sig"))
    function = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "get_winner_count_ranking"
    )
    namespace = {"pd": pd}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(app_path), "exec"), namespace)

    scores = pd.DataFrame(
        [
            {"競技ID": 1, "順位": 1, "プレイヤー名": "荒巻　典芳", "アウトスコア": 0, "インスコア": 0},
            {"競技ID": 40, "順位": 1, "プレイヤー名": "荒巻　典芳", "アウトスコア": 49, "インスコア": 50},
            {"競技ID": 41, "順位": 1, "プレイヤー名": "荒巻　典芳", "アウトスコア": 40, "インスコア": 40},
        ]
    )

    result = namespace["get_winner_count_ranking"](scores)
    assert result.to_dict("records") == [{"プレイヤー名": "荒巻　典芳", "優勝回数": 2}]


def test_dashboard_score_filter_requires_detailed_regular_competition_scores():
    app_path = APP_DIR / "app.py"
    module = ast.parse(app_path.read_text(encoding="utf-8-sig"))
    function = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "_valid_dashboard_scores"
    )
    namespace = {"pd": pd}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(app_path), "exec"), namespace)
    scores = pd.DataFrame(
        [
            {"競技ID": 10, "アウトスコア": 40, "インスコア": 42, "合計スコア": 82, "プレイヤー名": "A"},
            {"競技ID": 11, "アウトスコア": 0, "インスコア": 0, "合計スコア": None, "プレイヤー名": "B"},
            {"競技ID": 100, "アウトスコア": 40, "インスコア": 42, "合計スコア": 82, "プレイヤー名": "C"},
        ]
    )
    result = namespace["_valid_dashboard_scores"](scores)
    assert result["プレイヤー名"].tolist() == ["A"]
