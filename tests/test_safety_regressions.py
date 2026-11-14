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
        self.existing_rows = []
        self.insert_rows = None
        self.updated_rows = []
        self.filters = []

    def select(self, columns):
        self.selected_columns = columns
        self.mode = "select"
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def delete(self):
        self.delete_called = True
        return self

    def upsert(self, rows, on_conflict):
        self.upsert_rows = rows
        self.on_conflict = on_conflict
        return self

    def insert(self, rows):
        self.insert_rows = rows
        self.mode = "insert"
        return self

    def update(self, row):
        self.mode = "update"
        self.updated_rows.append((row, list(self.filters)))
        self.filters.clear()
        return self

    def execute(self):
        data = self.existing_rows if getattr(self, "mode", "select") == "select" else []
        if getattr(self, "mode", "select") == "select":
            self.filters.clear()
        return type("Response", (), {"data": data})()


class SupabaseStub:
    def __init__(self):
        self.scores = ScoreQuery()

    def table(self, name):
        assert name == "scores"
        return self.scores


class SessionStateStub(dict):
    def __getattr__(self, name):
        return self[name]


def test_save_scores_inserts_and_updates_without_on_conflict(monkeypatch):
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
    assert supabase.scores.upsert_rows is None
    assert supabase.scores.insert_rows[0]["competition_id"] == 7
    assert supabase.scores.insert_rows[0]["player_id"] == 10

    supabase.scores.existing_rows = [{"id": 55, "player_id": 10}]
    assert score_entry.save_scores(
        7, {10: {"out_score": 40, "in_score": 41, "net_score": 71}},
        pd.DataFrame(), supabase,
    ) is True
    updated_record, filters = supabase.scores.updated_rows[-1]
    assert updated_record["competition_id"] == 7
    assert filters == [("id", 55), ("competition_id", 7), ("player_id", 10)]
    assert supabase.scores.upsert_rows is None

    supabase.scores.existing_rows = [
        {"id": 55, "player_id": 10}, {"id": 56, "player_id": 10}
    ]
    assert score_entry.save_scores(
        7, {10: {"out_score": 40, "in_score": 41, "net_score": 71}},
        pd.DataFrame(), supabase,
    ) is False
    assert supabase.scores.upsert_rows is None
    assert len(supabase.scores.updated_rows) == 1

    supabase.scores.existing_rows = []
    supabase.scores.insert_rows = None
    assert score_entry.save_scores(
        7, {10: {"out_score": 40, "in_score": 41, "net_score": 71},
            11: {"out_score": 0, "in_score": 0, "net_score": 0}},
        pd.DataFrame(), supabase,
    ) is False
    assert supabase.scores.upsert_rows is None


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
