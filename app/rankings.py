"""スコアデータから自動集計するランキング画面。"""

from __future__ import annotations

from typing import Callable

import pandas as pd
import streamlit as st


EXCLUDED_COMPETITION_IDS = {41}
MIN_SAMPLES_FOR_AVERAGE = 3


def _empty(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def prepare_ranking_scores(scores_df: pd.DataFrame) -> pd.DataFrame:
    """集計に使う型を揃え、通常コンペの記録だけを返す。"""
    required = {"競技ID", "プレイヤー名", "日付"}
    if scores_df.empty or not required.issubset(scores_df.columns):
        return pd.DataFrame()

    scores = scores_df.copy()
    scores["_competition_id"] = pd.to_numeric(scores["競技ID"], errors="coerce")
    scores["_rank"] = pd.to_numeric(scores.get("順位"), errors="coerce")
    scores["_out"] = pd.to_numeric(scores.get("アウトスコア"), errors="coerce")
    scores["_in"] = pd.to_numeric(scores.get("インスコア"), errors="coerce")
    scores["_gross"] = pd.to_numeric(scores.get("合計スコア"), errors="coerce")
    scores["_net"] = pd.to_numeric(scores.get("ネットスコア"), errors="coerce")
    scores["_handicap"] = pd.to_numeric(scores.get("ハンディキャップ"), errors="coerce")
    scores["_date"] = pd.to_datetime(scores["日付"], errors="coerce")

    return scores[
        (scores["_competition_id"] > 0)
        & (scores["_competition_id"] < 100)
        & ~scores["_competition_id"].isin(EXCLUDED_COMPETITION_IDS)
        & scores["プレイヤー名"].notna()
        & scores["_date"].notna()
    ].copy()


def _ranked_scores(scores: pd.DataFrame) -> pd.DataFrame:
    return scores[scores["_rank"] > 0].copy()


def _detailed_scores(scores: pd.DataFrame) -> pd.DataFrame:
    return scores[
        (scores["_out"] > 0)
        & (scores["_in"] > 0)
        & (scores["_gross"] > 0)
    ].copy()


def _count_ranking(rows: pd.DataFrame, condition: pd.Series, column: str) -> pd.DataFrame:
    filtered = rows[condition].copy()
    if filtered.empty:
        return _empty(["プレイヤー名", column])
    return (
        filtered.groupby("プレイヤー名")
        .size()
        .reset_index(name=column)
        .sort_values([column, "プレイヤー名"], ascending=[False, True])
        .reset_index(drop=True)
    )


def winner_count_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    ranked = _ranked_scores(scores)
    return _count_ranking(ranked, ranked["_rank"] == 1, "優勝回数")


def podium_count_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    ranked = _ranked_scores(scores)
    return _count_ranking(ranked, ranked["_rank"].between(1, 3), "入賞回数")


def best_gross_count_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    detailed = _detailed_scores(scores)
    if detailed.empty:
        return _empty(["プレイヤー名", "ベスグロ回数"])
    competition_best = detailed.groupby("_competition_id")["_gross"].transform("min")
    return _count_ranking(detailed, detailed["_gross"] == competition_best, "ベスグロ回数")


def average_ranking(scores: pd.DataFrame, value_column: str, title: str, ascending: bool = True) -> pd.DataFrame:
    detailed = _detailed_scores(scores)
    valid = detailed[detailed[value_column].notna()]
    if value_column == "_net":
        valid = valid[valid[value_column] > 0]
    if valid.empty:
        return _empty(["プレイヤー名", "記録数", title])
    result = valid.groupby("プレイヤー名")[value_column].agg(["count", "mean"]).reset_index()
    result.columns = ["プレイヤー名", "記録数", title]
    result = result[result["記録数"] >= MIN_SAMPLES_FOR_AVERAGE]
    return result.sort_values([title, "プレイヤー名"], ascending=[ascending, True]).reset_index(drop=True)


def average_rank_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    ranked = _ranked_scores(scores)
    if ranked.empty:
        return _empty(["プレイヤー名", "順位登録回数", "平均順位"])
    result = ranked.groupby("プレイヤー名")["_rank"].agg(["count", "mean"]).reset_index()
    result.columns = ["プレイヤー名", "順位登録回数", "平均順位"]
    return result.sort_values(["平均順位", "プレイヤー名"]).reset_index(drop=True)


def top3_rate_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    ranked = _ranked_scores(scores)
    if ranked.empty:
        return _empty(["プレイヤー名", "順位登録回数", "トップ3回数", "トップ3率"])
    result = ranked.groupby("プレイヤー名")["_rank"].agg(
        順位登録回数="count", トップ3回数=lambda ranks: int(ranks.between(1, 3).sum())
    ).reset_index()
    result["トップ3率"] = result["トップ3回数"] / result["順位登録回数"] * 100
    return result.sort_values(["トップ3率", "トップ3回数", "プレイヤー名"], ascending=[False, False, True]).reset_index(drop=True)


def _longest_streak(scores: pd.DataFrame, predicate: Callable[[float], bool]) -> pd.DataFrame:
    ranked = _ranked_scores(scores).sort_values(["プレイヤー名", "_date", "_competition_id"])
    records: list[dict[str, object]] = []
    for player, rows in ranked.groupby("プレイヤー名", sort=False):
        best = current = 0
        for rank in rows["_rank"]:
            if predicate(float(rank)):
                current += 1
                best = max(best, current)
            else:
                current = 0
        if best:
            records.append({"プレイヤー名": player, "最長連続回数": best})
    if not records:
        return _empty(["プレイヤー名", "最長連続回数"])
    return pd.DataFrame(records).sort_values(["最長連続回数", "プレイヤー名"], ascending=[False, True]).reset_index(drop=True)


def win_streak_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    result = _longest_streak(scores, lambda rank: rank == 1)
    return result.rename(columns={"最長連続回数": "連続優勝"})


def podium_streak_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    result = _longest_streak(scores, lambda rank: 1 <= rank <= 3)
    return result.rename(columns={"最長連続回数": "連続入賞"})


def score_stddev_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    detailed = _detailed_scores(scores)
    if detailed.empty:
        return _empty(["プレイヤー名", "記録数", "グロス標準偏差"])
    result = detailed.groupby("プレイヤー名")["_gross"].agg(["count", "std"]).reset_index()
    result.columns = ["プレイヤー名", "記録数", "グロス標準偏差"]
    result = result[result["記録数"] >= MIN_SAMPLES_FOR_AVERAGE]
    return result.sort_values(["グロス標準偏差", "プレイヤー名"]).reset_index(drop=True)


def personal_best_update_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    detailed = _detailed_scores(scores).sort_values(["プレイヤー名", "_date", "_competition_id"])
    records: list[dict[str, object]] = []
    for player, rows in detailed.groupby("プレイヤー名", sort=False):
        previous_best: float | None = None
        updates = 0
        for gross in rows["_gross"]:
            if previous_best is not None and gross < previous_best:
                updates += 1
            previous_best = gross if previous_best is None else min(previous_best, gross)
        records.append({"プレイヤー名": player, "自己ベスト更新回数": updates})
    if not records:
        return _empty(["プレイヤー名", "自己ベスト更新回数"])
    return pd.DataFrame(records).sort_values(["自己ベスト更新回数", "プレイヤー名"], ascending=[False, True]).reset_index(drop=True)


def personal_best_gross_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    detailed = _detailed_scores(scores)
    if detailed.empty:
        return _empty(["プレイヤー名", "ベストグロス"])
    result = detailed.groupby("プレイヤー名")["_gross"].min().reset_index(name="ベストグロス")
    return result.sort_values(["ベストグロス", "プレイヤー名"]).reset_index(drop=True)


def handicap_change_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    detailed = _detailed_scores(scores).dropna(subset=["_handicap"]).sort_values(["プレイヤー名", "_date", "_competition_id"])
    records: list[dict[str, object]] = []
    for player, rows in detailed.groupby("プレイヤー名", sort=False):
        changes = rows["_handicap"].diff().abs().dropna()
        if not changes.empty:
            records.append({"プレイヤー名": player, "最大ハンデ変動": changes.max()})
    if not records:
        return _empty(["プレイヤー名", "最大ハンデ変動"])
    return pd.DataFrame(records).sort_values(["最大ハンデ変動", "プレイヤー名"], ascending=[False, True]).reset_index(drop=True)


def booby_count_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    ranked = _ranked_scores(scores)
    winners: list[pd.DataFrame] = []
    for _, rows in ranked.groupby("_competition_id"):
        ordered = rows.sort_values("_rank")
        if len(ordered) >= 3:
            # 順位が一意に付く現在の保存方式に合わせ、下から2番目をブービーとする。
            winners.append(ordered.iloc[[-2]])
    if not winners:
        return _empty(["プレイヤー名", "ブービー賞回数"])
    booby_rows = pd.concat(winners, ignore_index=True)
    return _count_ranking(booby_rows, pd.Series(True, index=booby_rows.index), "ブービー賞回数")


def _show_table(df: pd.DataFrame, empty_message: str, decimals: dict[str, int] | None = None) -> None:
    if df.empty:
        st.info(empty_message)
        return
    display = df.copy()
    for column, digits in (decimals or {}).items():
        if column in display.columns:
            display[column] = display[column].map(lambda value: f"{value:.{digits}f}" if pd.notna(value) else "－")
    display.index = range(1, len(display) + 1)
    display.index.name = "順位"
    st.dataframe(display, width="stretch")


def rankings_page(scores_df: pd.DataFrame) -> None:
    """会員向けの自動更新ランキングページを表示する。"""
    st.title("🏅 88会ランキング")
    st.caption("スコアを保存すると、次回の表示時に自動で集計へ反映されます。通常コンペ（第1〜99回・第41回を除く）を対象にしています。")

    scores = prepare_ranking_scores(scores_df)
    if scores.empty:
        st.warning("ランキングを集計できるスコアデータがありません。")
    else:
        ability_tab, stability_tab, records_tab = st.tabs(["実力", "安定感", "記録・特別賞"])
        with ability_tab:
            st.subheader("実力系ランキング")
            _show_table(winner_count_ranking(scores), "優勝記録がありません。")
            st.subheader("ベスグロ回数")
            _show_table(best_gross_count_ranking(scores), "有効なグロススコアがありません。")
            st.subheader("平均グロス")
            _show_table(average_ranking(scores, "_gross", "平均グロス"), "3回以上の有効スコアが必要です。", {"平均グロス": 1})
            st.subheader("平均ネット")
            _show_table(average_ranking(scores, "_net", "平均ネット"), "3回以上の有効ネットスコアが必要です。", {"平均ネット": 1})
            st.subheader("入賞回数（3位以内）")
            _show_table(podium_count_ranking(scores), "入賞記録がありません。")

        with stability_tab:
            st.subheader("平均順位")
            _show_table(average_rank_ranking(scores), "順位記録がありません。", {"平均順位": 2})
            st.subheader("トップ3率")
            _show_table(top3_rate_ranking(scores), "順位記録がありません。", {"トップ3率": 1})
            st.subheader("連続優勝記録")
            _show_table(win_streak_ranking(scores), "連続優勝記録がありません。")
            st.subheader("連続入賞記録")
            _show_table(podium_streak_ranking(scores), "連続入賞記録がありません。")
            st.subheader("スコアのばらつき（グロス標準偏差）")
            _show_table(score_stddev_ranking(scores), "3回以上の有効スコアが必要です。", {"グロス標準偏差": 2})
            st.caption("数値が小さいほど、グロススコアが安定しています。")

        with records_tab:
            st.subheader("自己ベスト更新回数")
            _show_table(personal_best_update_ranking(scores), "有効なグロススコアがありません。")
            st.subheader("ベストグロス")
            _show_table(personal_best_gross_ranking(scores), "有効なグロススコアがありません。")
            st.subheader("最大ハンデ変動")
            _show_table(handicap_change_ranking(scores), "比較できるハンデ記録がありません。", {"最大ハンデ変動": 1})
            st.caption("各プレイヤーの記録間で最も大きく変わったハンデの絶対値です。")
            st.subheader("ブービー賞受賞回数")
            _show_table(booby_count_ranking(scores), "ブービー賞の対象となる競技がありません。")
            st.caption("順位登録済みの参加者が3名以上の競技で、下から2番目をブービー賞として集計しています。")

    if st.button("← メイン画面へ", key="back_to_main_from_rankings"):
        st.session_state.page = "main"
        st.rerun()
