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


def booby_maker_count_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    """順位登録済みの最下位（ブービーメーカー）回数を返す。"""
    ranked = _ranked_scores(scores)
    last_place_rows: list[pd.DataFrame] = []
    for _, rows in ranked.groupby("_competition_id"):
        ordered = rows.sort_values("_rank")
        if len(ordered) >= 2:
            last_place_rows.append(ordered.iloc[[-1]])
    if not last_place_rows:
        return _empty(["プレイヤー名", "ブービーメーカー回数"])
    last_place = pd.concat(last_place_rows, ignore_index=True)
    return _count_ranking(last_place, pd.Series(True, index=last_place.index), "ブービーメーカー回数")


def participation_count_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    """登録済みスコアを参加として数える。"""
    if scores.empty:
        return _empty(["プレイヤー名", "参加回数"])
    result = scores.groupby("プレイヤー名")["_competition_id"].nunique().reset_index(name="参加回数")
    return result.sort_values(["参加回数", "プレイヤー名"], ascending=[False, True]).reset_index(drop=True)


def registered_participation_streak_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    """登録済みスコアのあるコンペだけを母集団にした最長連続参加。"""
    if scores.empty:
        return _empty(["プレイヤー名", "最長連続参加"])
    competitions = (
        scores[["_competition_id", "_date"]]
        .drop_duplicates()
        .sort_values(["_date", "_competition_id"])["_competition_id"]
        .tolist()
    )
    records: list[dict[str, object]] = []
    for player, rows in scores.groupby("プレイヤー名"):
        attended = set(rows["_competition_id"])
        best = current = 0
        for competition_id in competitions:
            if competition_id in attended:
                current += 1
                best = max(best, current)
            else:
                current = 0
        records.append({"プレイヤー名": player, "最長連続参加": best})
    return pd.DataFrame(records).sort_values(["最長連続参加", "プレイヤー名"], ascending=[False, True]).reset_index(drop=True)


def out_in_gap_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    detailed = _detailed_scores(scores).copy()
    if detailed.empty:
        return _empty(["プレイヤー名", "最大前後半差"])
    detailed["_gap"] = (detailed["_out"] - detailed["_in"]).abs()
    result = detailed.groupby("プレイヤー名")["_gap"].max().reset_index(name="最大前後半差")
    return result.sort_values(["最大前後半差", "プレイヤー名"], ascending=[False, True]).reset_index(drop=True)


def near_miss_count_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    """各コンペの優勝者ネットより1打多い記録を数える。"""
    detailed = _detailed_scores(scores)
    detailed = detailed[detailed["_net"] > 0]
    rows_to_count: list[pd.DataFrame] = []
    for _, rows in detailed.groupby("_competition_id"):
        winner_rows = rows[rows["_rank"] == 1]
        if winner_rows.empty:
            continue
        winner_net = winner_rows["_net"].min()
        rows_to_count.append(rows[(rows["_rank"] != 1) & (rows["_net"] == winner_net + 1)])
    if not rows_to_count:
        return _empty(["プレイヤー名", "惜しいで賞回数"])
    near_miss_rows = pd.concat(rows_to_count, ignore_index=True)
    return _count_ranking(near_miss_rows, pd.Series(True, index=near_miss_rows.index), "惜しいで賞回数")


def miracle_win_count_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    """ネット優勝者が同コンペの最少グロスではない回数を数える。"""
    detailed = _detailed_scores(scores)
    winners: list[pd.DataFrame] = []
    for _, rows in detailed.groupby("_competition_id"):
        winner_rows = rows[rows["_rank"] == 1]
        if winner_rows.empty:
            continue
        gross_best = rows["_gross"].min()
        winners.append(winner_rows[winner_rows["_gross"] > gross_best])
    if not winners:
        return _empty(["プレイヤー名", "ミラクル優勝回数"])
    miracle_rows = pd.concat(winners, ignore_index=True)
    return _count_ranking(miracle_rows, pd.Series(True, index=miracle_rows.index), "ミラクル優勝回数")


def monthly_win_ranking(scores: pd.DataFrame) -> pd.DataFrame:
    winners = _ranked_scores(scores)
    winners = winners[winners["_rank"] == 1].copy()
    if winners.empty:
        return _empty(["プレイヤー名", "優勝回数"])
    winners["月"] = winners["_date"].dt.month
    result = pd.crosstab(winners["プレイヤー名"], winners["月"])
    result = result.reindex(columns=range(1, 13), fill_value=0)
    result.columns = [f"{month}月" for month in result.columns]
    result["優勝回数"] = result.sum(axis=1)
    return result.reset_index().sort_values(["優勝回数", "プレイヤー名"], ascending=[False, True]).reset_index(drop=True)


def course_win_rate_ranking(scores: pd.DataFrame, course: str) -> pd.DataFrame:
    ranked = _ranked_scores(scores)
    ranked = ranked[ranked["コース"].fillna("") == course]
    if ranked.empty:
        return _empty(["プレイヤー名", "順位登録回数", "優勝回数", "勝率"])
    result = ranked.groupby("プレイヤー名")["_rank"].agg(
        順位登録回数="count", 優勝回数=lambda ranks: int((ranks == 1).sum())
    ).reset_index()
    result["勝率"] = result["優勝回数"] / result["順位登録回数"] * 100
    return result.sort_values(["勝率", "優勝回数", "プレイヤー名"], ascending=[False, False, True]).reset_index(drop=True)


def course_statistics(scores: pd.DataFrame, player: str) -> pd.DataFrame:
    player_scores = scores[scores["プレイヤー名"] == player].copy()
    if player_scores.empty:
        return _empty(["コース", "参加回数", "平均グロス", "平均ネット", "平均順位", "優勝回数", "勝率"])
    player_scores["コース"] = player_scores["コース"].fillna("コース未登録")
    records: list[dict[str, object]] = []
    for course, rows in player_scores.groupby("コース"):
        detailed = _detailed_scores(rows)
        ranked = _ranked_scores(rows)
        participation_count = rows["_competition_id"].nunique()
        ranked_count = len(ranked)
        wins = int((ranked["_rank"] == 1).sum())
        records.append({
            "コース": course,
            "参加回数": participation_count,
            "平均グロス": detailed["_gross"].mean() if not detailed.empty else float("nan"),
            "平均ネット": detailed.loc[detailed["_net"] > 0, "_net"].mean() if not detailed.empty else float("nan"),
            "平均順位": ranked["_rank"].mean() if not ranked.empty else float("nan"),
            "優勝回数": wins,
            "勝率": wins / ranked_count * 100 if ranked_count else float("nan"),
        })
    return pd.DataFrame(records).sort_values(["参加回数", "コース"], ascending=[False, True]).reset_index(drop=True)


def seasonal_average_scores(scores: pd.DataFrame, player: str) -> pd.DataFrame:
    detailed = _detailed_scores(scores)
    detailed = detailed[detailed["プレイヤー名"] == player].copy()
    if detailed.empty:
        return _empty(["季節", "記録数", "平均グロス", "平均ネット"])
    month = detailed["_date"].dt.month
    detailed["季節"] = pd.Series("", index=detailed.index)
    detailed.loc[month.isin([3, 4, 5]), "季節"] = "春（3〜5月）"
    detailed.loc[month.isin([6, 7, 8]), "季節"] = "夏（6〜8月）"
    detailed.loc[month.isin([9, 10, 11]), "季節"] = "秋（9〜11月）"
    detailed.loc[month.isin([12, 1, 2]), "季節"] = "冬（12〜2月）"
    result = detailed.groupby("季節").agg(
        記録数=("_gross", "count"), 平均グロス=("_gross", "mean"), 平均ネット=("_net", "mean")
    ).reset_index()
    order = {"春（3〜5月）": 0, "夏（6〜8月）": 1, "秋（9〜11月）": 2, "冬（12〜2月）": 3}
    return result.sort_values("季節", key=lambda values: values.map(order)).reset_index(drop=True)


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
    st.info("集計に使うのは登録済みのスコア・順位だけです。未登録のスコアや順位は、各ランキングの分母・連続記録へ含めません。")

    with st.expander("ランキング・賞の集計条件を見る"):
        st.markdown(
            """
            - **優勝・入賞・平均順位・トップ3率**：登録済みの順位を使用します。トップ3率の分母は、順位が登録された参加回数です。
            - **ベスグロ・平均グロス・平均ネット・標準偏差・自己ベスト**：OUT/INとグロスが揃った有効スコアだけを使用します。平均値と標準偏差は3回以上の記録が必要です。
            - **ベスグロ回数**：各コンペの最少グロスを出した回数です。同スコアがあれば、該当者全員を1回として数えます。
            - **連続優勝・連続入賞**：そのプレイヤーに登録されている順位記録を日付順に並べて集計します。未登録回がある過去データでは、実際の連続記録と異なる場合があります。
            - **参加回数・連続参加**：スコア登録があるコンペを参加として数えます。連続参加は、登録済みスコアがあるコンペの範囲での参考記録です。
            - **自己ベスト更新回数**：初回の有効スコアは基準値とし、その後に自己最少グロスを更新した回数です。同スコアは更新に数えません。
            - **最大ハンデ変動**：同一プレイヤーの連続する登録ハンデの差の絶対値で、最も大きい値です。良化・悪化は区別しません。
            - **ブービー賞**：順位登録済みの参加者が3名以上のコンペで、下から2番目の順位を受賞者とします。
            - **ブービーメーカー**：順位登録済みの参加者が2名以上のコンペで、最下位を受賞者とします。
            - **大波賞**：1ラウンド内のOUTとINの差の絶対値が最も大きい記録です。
            - **惜しいで賞**：優勝者のネットスコアより1打多い記録の回数です。
            - **ミラクル優勝**：ネット順位1位だが、そのコンペの最少グロスではなかった優勝回数です。
            """
        )

    scores = prepare_ranking_scores(scores_df)
    if scores.empty:
        st.warning("ランキングを集計できるスコアデータがありません。")
    else:
        available_years = sorted(scores["_date"].dt.year.dropna().astype(int).unique(), reverse=True)
        selected_year = st.selectbox("集計対象", ["全期間"] + [str(year) for year in available_years], key="ranking_year_filter")
        display_scores = scores if selected_year == "全期間" else scores[scores["_date"].dt.year == int(selected_year)].copy()
        st.caption(f"対象期間：{selected_year}。フィルターを変更すると、すべてのランキング・賞・コース別成績へ反映されます。")

        ability_tab, stability_tab, records_tab, course_tab, yearly_tab = st.tabs(["実力", "安定感", "記録・特別賞", "コース・季節", "年度別"])
        with ability_tab:
            st.subheader("実力系ランキング")
            _show_table(winner_count_ranking(display_scores), "優勝記録がありません。")
            st.caption("順位1位の回数です。順位のみ登録された過去記録も対象です。")
            st.subheader("ベスグロ回数")
            _show_table(best_gross_count_ranking(display_scores), "有効なグロススコアがありません。")
            st.caption("各コンペの最少グロスを出した回数です。同スコアは全員を数えます。")
            st.subheader("平均グロス")
            _show_table(average_ranking(display_scores, "_gross", "平均グロス"), "3回以上の有効スコアが必要です。", {"平均グロス": 1})
            st.caption("OUT・IN・グロスが揃った記録を3回以上登録したプレイヤーが対象です。数値が小さいほど上位です。")
            st.subheader("平均ネット")
            _show_table(average_ranking(display_scores, "_net", "平均ネット"), "3回以上の有効ネットスコアが必要です。", {"平均ネット": 1})
            st.caption("有効なネットスコアを3回以上登録したプレイヤーが対象です。数値が小さいほど上位です。")
            st.subheader("入賞回数（3位以内）")
            _show_table(podium_count_ranking(display_scores), "入賞記録がありません。")
            st.caption("順位1位〜3位に入った回数です。")

        with stability_tab:
            st.subheader("平均順位")
            _show_table(average_rank_ranking(display_scores), "順位記録がありません。", {"平均順位": 2})
            st.caption("順位が登録された回だけで算出します。数値が小さいほど上位です。")
            st.subheader("トップ3率")
            _show_table(top3_rate_ranking(display_scores), "順位記録がありません。", {"トップ3率": 1})
            st.caption("順位1位〜3位の回数 ÷ 順位登録回数です。")
            st.subheader("連続優勝記録")
            _show_table(win_streak_ranking(display_scores), "連続優勝記録がありません。")
            st.caption("登録済みの順位記録を日付順に並べた最長連続優勝です。未登録回がある過去データでは、実際の連続記録と異なる場合があります。")
            st.subheader("連続入賞記録")
            _show_table(podium_streak_ranking(display_scores), "連続入賞記録がありません。")
            st.caption("登録済みの順位記録を日付順に並べた最長連続入賞（3位以内）です。未登録回がある過去データでは、実際の連続記録と異なる場合があります。")
            st.subheader("スコアのばらつき（グロス標準偏差）")
            _show_table(score_stddev_ranking(display_scores), "3回以上の有効スコアが必要です。", {"グロス標準偏差": 2})
            st.caption("数値が小さいほど、グロススコアが安定しています。")
            st.subheader("参加賞の帝王（参加回数）")
            _show_table(participation_count_ranking(display_scores), "登録済みスコアがありません。")
            st.caption("スコア登録のあるユニークなコンペ数です。実際の参加者名簿ではなく、登録済みデータを基準にします。")
            st.subheader("最多連続参加（登録スコアベース）")
            _show_table(registered_participation_streak_ranking(display_scores), "登録済みスコアがありません。")
            st.caption("登録済みスコアがあるコンペだけを時系列に並べた参考記録です。未登録の過去コンペは判定できません。")

        with records_tab:
            st.subheader("自己ベスト更新回数")
            _show_table(personal_best_update_ranking(display_scores), "有効なグロススコアがありません。")
            st.caption("初回の有効スコアは基準値とし、その後に自己最少グロスを更新した回数です。同スコアは更新に数えません。")
            st.subheader("ベストグロス")
            _show_table(personal_best_gross_ranking(display_scores), "有効なグロススコアがありません。")
            st.caption("登録済みの有効スコアにおける、生涯最少グロスです。")
            st.subheader("最大ハンデ変動")
            _show_table(handicap_change_ranking(display_scores), "比較できるハンデ記録がありません。", {"最大ハンデ変動": 1})
            st.caption("各プレイヤーの記録間で最も大きく変わったハンデの絶対値です。")
            st.subheader("ブービー賞受賞回数")
            _show_table(booby_count_ranking(display_scores), "ブービー賞の対象となる競技がありません。")
            st.caption("順位登録済みの参加者が3名以上の競技で、下から2番目をブービー賞として集計しています。")
            st.subheader("ブービーメーカー回数")
            _show_table(booby_maker_count_ranking(display_scores), "ブービーメーカーの対象となる競技がありません。")
            st.caption("順位登録済みの参加者が2名以上の競技で、最下位をブービーメーカーとして集計しています。")
            st.subheader("大波賞（最大前後半差）")
            _show_table(out_in_gap_ranking(display_scores), "有効なOUT・INスコアがありません。")
            st.caption("1ラウンド内のOUTとINの差の絶対値が最も大きい記録です。数値が大きいほど前後半の差が大きくなります。")
            st.subheader("惜しいで賞")
            _show_table(near_miss_count_ranking(display_scores), "惜しいで賞の対象となる記録がありません。")
            st.caption("優勝者のネットスコアより1打多かった回数です。")
            st.subheader("ミラクル優勝")
            _show_table(miracle_win_count_ranking(display_scores), "ミラクル優勝の対象となる記録がありません。")
            st.caption("ネット順位1位だが、そのコンペの最少グロスではなかった優勝回数です。ハンデによる逆転優勝の参考記録です。")

        with course_tab:
            players = sorted(display_scores["プレイヤー名"].dropna().astype(str).unique())
            if players:
                selected_player = st.selectbox("プレイヤー", players, key="ranking_course_player")
                st.subheader(f"{selected_player} さんのコース別成績")
                _show_table(
                    course_statistics(display_scores, selected_player),
                    "コース別に集計できる記録がありません。",
                    {"平均グロス": 1, "平均ネット": 1, "平均順位": 2, "勝率": 1},
                )
                st.caption("参加回数は登録済みスコアのあるコンペ数です。平均スコアは有効なOUT・INスコア、勝率は順位登録回数を分母にします。")
                st.subheader("季節別平均スコア")
                _show_table(
                    seasonal_average_scores(display_scores, selected_player),
                    "季節別に集計できる有効スコアがありません。",
                    {"平均グロス": 1, "平均ネット": 1},
                )
                st.caption("春（3〜5月）・夏（6〜8月）・秋（9〜11月）・冬（12〜2月）に分け、登録済みの有効スコアを平均しています。")
            courses = sorted(display_scores["コース"].dropna().astype(str).unique())
            if courses:
                selected_course = st.selectbox("コース別勝率を表示するコース", courses, key="ranking_win_rate_course")
                st.subheader(f"{selected_course} の勝率")
                _show_table(course_win_rate_ranking(display_scores, selected_course), "順位記録がありません。", {"勝率": 1})
                st.caption("優勝回数 ÷ 順位登録回数です。スコア未登録・順位未登録の回は分母に含めません。")

        with yearly_tab:
            st.subheader("年度別ランキング")
            st.caption("上部の「集計対象」で年度を選ぶと、全ページがその年度の記録に切り替わります。ここでは年度内の代表指標をまとめて表示します。")
            st.subheader("年間優勝回数")
            _show_table(winner_count_ranking(display_scores), "優勝記録がありません。")
            st.subheader("年間ベスグロ")
            _show_table(personal_best_gross_ranking(display_scores), "有効なグロススコアがありません。")
            st.subheader("年間平均順位")
            _show_table(average_rank_ranking(display_scores), "順位記録がありません。", {"平均順位": 2})
            st.subheader("月別優勝数")
            _show_table(monthly_win_ranking(display_scores), "優勝記録がありません。")
            st.caption("選択した対象期間における、月ごとの優勝回数です。")

    if st.button("← メイン画面へ", key="back_to_main_from_rankings"):
        st.session_state.page = "main"
        st.rerun()
