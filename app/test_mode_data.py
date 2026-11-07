"""Read-only fictional data used only by APP_TEST_MODE browser tests."""

from __future__ import annotations

import pandas as pd


MOCK_PLAYERS = (
    {"id": 901, "name": "テスト 太郎", "initial_handicap": 10.0, "affiliation": "モック支部"},
    {"id": 902, "name": "テスト 花子", "initial_handicap": 5.0, "affiliation": "モック支部"},
    {"id": 903, "name": "青空 次郎", "initial_handicap": 14.0, "affiliation": "モック支部"},
    {"id": 904, "name": "緑野 さくら", "initial_handicap": 12.0, "affiliation": "モック支部"},
)

MOCK_COMPETITIONS = (
    {
        "competition_id": 54,
        "name": "テスト春季コンペ",
        "date": "2026-04-12",
        "course": "テストヒルズGC",
        "description": "ブラウザテスト用の架空大会です。",
        "status": "completed",
    },
    {
        "competition_id": 55,
        "name": "テスト初夏コンペ",
        "date": "2026-06-14",
        "course": "モックレイクGC",
        "description": "ブラウザテスト用の架空大会です。",
        "status": "completed",
    },
)

MOCK_SCORES = (
    {"competition_id": 54, "player_id": 901, "out_score": 42, "in_score": 40, "handicap": 10.0, "net_score": 72.0, "ranking": 2},
    {"competition_id": 54, "player_id": 902, "out_score": 40, "in_score": 39, "handicap": 5.0, "net_score": 74.0, "ranking": 3},
    {"competition_id": 54, "player_id": 903, "out_score": 44, "in_score": 41, "handicap": 14.0, "net_score": 71.0, "ranking": 1},
    {"competition_id": 54, "player_id": 904, "out_score": 45, "in_score": 43, "handicap": 12.0, "net_score": 76.0, "ranking": 4},
    {"competition_id": 55, "player_id": 901, "out_score": 41, "in_score": 39, "handicap": 10.0, "net_score": 70.0, "ranking": 2},
    {"competition_id": 55, "player_id": 902, "out_score": 43, "in_score": 40, "handicap": 5.0, "net_score": 78.0, "ranking": 4},
    {"competition_id": 55, "player_id": 903, "out_score": 41, "in_score": 41, "handicap": 13.0, "net_score": 69.0, "ranking": 1},
    {"competition_id": 55, "player_id": 904, "out_score": 44, "in_score": 40, "handicap": 12.0, "net_score": 72.0, "ranking": 3},
)


def mock_players_dataframe() -> pd.DataFrame:
    return pd.DataFrame(MOCK_PLAYERS).copy()


def mock_competitions_dataframe() -> pd.DataFrame:
    return pd.DataFrame(MOCK_COMPETITIONS).copy()


def mock_scores_dataframe() -> pd.DataFrame:
    players = {row["id"]: row["name"] for row in MOCK_PLAYERS}
    competitions = {row["competition_id"]: row for row in MOCK_COMPETITIONS}
    rows = []
    for score in MOCK_SCORES:
        competition = competitions[score["competition_id"]]
        out_score = score["out_score"]
        in_score = score["in_score"]
        rows.append(
            {
                "競技ID": score["competition_id"],
                "日付": competition["date"],
                "コース": competition["course"],
                "プレイヤー名": players[score["player_id"]],
                "アウトスコア": out_score,
                "インスコア": in_score,
                "合計スコア": out_score + in_score,
                "ハンディキャップ": score["handicap"],
                "ネットスコア": score["net_score"],
                "順位": score["ranking"],
            }
        )
    return pd.DataFrame(rows)


def mock_announcement() -> dict[str, object]:
    return {
        "title": "テスト用のお知らせ",
        "content": "この案内はブラウザテストでのみ表示される架空データです。",
        "tournament_info": {"tournament_number": 56, "course_name": "モックレイクGC"},
    }
