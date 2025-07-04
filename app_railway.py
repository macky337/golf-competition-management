#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
88会ゴルフコンペ・スコア管理システム - Railway PostgreSQL版
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

# SQLAlchemyとpsycopg2のインポート（オプション）
try:
    from sqlalchemy import create_engine
    import psycopg2
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    st.warning("⚠️ データベースライブラリが未インストール（本番環境では自動インストールされます）")

# ページ設定
st.set_page_config(
    page_title="88会ゴルフコンペ・スコア管理システム", 
    page_icon="🏌️",
    layout="wide"
)

# 日本語フォント設定
plt.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'MS Gothic']

@st.cache_resource
def init_connection():
    """Railway PostgreSQLデータベース接続"""
    if not DB_AVAILABLE:
        return None
        
    try:
        # Railway環境変数からDB接続情報を取得
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            # SQLAlchemy用のエンジンを作成
            engine = create_engine(database_url)
            return engine
        else:
            # 環境変数がない場合はローカルのサンプルデータを使用
            return None
    except Exception as e:
        st.error(f"データベース接続エラー: {e}")
        return None

def create_tables(engine):
    """データベーステーブル作成"""
    if not engine:
        return False
        
    try:
        with engine.connect() as conn:
            # プレイヤーテーブル
            conn.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 大会テーブル
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tournaments (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    date DATE NOT NULL,
                    course VARCHAR(200),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # スコアテーブル
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id SERIAL PRIMARY KEY,
                    tournament_id INTEGER REFERENCES tournaments(id),
                    player_id INTEGER REFERENCES players(id),
                    gross_score INTEGER NOT NULL,
                    handicap INTEGER DEFAULT 0,
                    net_score INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            return True
    except Exception as e:
        st.error(f"テーブル作成エラー: {e}")
        return False

def load_data_from_db(engine):
    """データベースからデータを読み込み"""
    if not engine:
        return pd.DataFrame()
        
    try:
        query = """
        SELECT 
            p.name as player_name,
            s.gross_score as score,
            s.handicap as hdcp,
            s.net_score as net_score,
            t.date::text as date,
            t.course as course
        FROM scores s
        JOIN players p ON s.player_id = p.id
        JOIN tournaments t ON s.tournament_id = t.id
        ORDER BY t.date DESC, s.net_score ASC
        """
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return pd.DataFrame()

def load_sample_data():
    """サンプルデータを生成（DB接続がない場合）"""
    sample_data = {
        'player_name': ['田中太郎', '佐藤花子', '山田次郎', '鈴木美咲', '高橋健一', '渡辺良子'],
        'score': [82, 76, 88, 79, 84, 81],
        'hdcp': [12, 8, 16, 10, 14, 11],
        'net_score': [70, 68, 72, 69, 70, 70],
        'date': ['2025-06-15', '2025-06-15', '2025-06-15', '2025-06-15', '2025-06-15', '2025-06-15'],
        'course': ['〇〇ゴルフクラブ', '〇〇ゴルフクラブ', '〇〇ゴルフクラブ', '〇〇ゴルフクラブ', '〇〇ゴルフクラブ', '〇〇ゴルフクラブ']
    }
    return pd.DataFrame(sample_data)

def insert_sample_data(engine):
    """初回起動時にサンプルデータをDBに挿入"""
    if not engine:
        return False
        
    try:
        with engine.connect() as conn:
            # プレイヤー挿入
            players = ['田中太郎', '佐藤花子', '山田次郎', '鈴木美咲', '高橋健一', '渡辺良子']
            for player in players:
                conn.execute(
                    "INSERT INTO players (name) VALUES (%s) ON CONFLICT DO NOTHING",
                    (player,)
                )
            
            # 大会挿入
            conn.execute("""
                INSERT INTO tournaments (name, date, course) 
                VALUES ('第1回88会ゴルフコンペ', '2025-06-15', '〇〇ゴルフクラブ')
                ON CONFLICT DO NOTHING
            """)
            
            # スコア挿入
            scores_data = [
                (1, 1, 82, 12, 70),  # 田中太郎
                (1, 2, 76, 8, 68),   # 佐藤花子
                (1, 3, 88, 16, 72),  # 山田次郎
                (1, 4, 79, 10, 69),  # 鈴木美咲
                (1, 5, 84, 14, 70),  # 高橋健一
                (1, 6, 81, 11, 70),  # 渡辺良子
            ]
            
            for score in scores_data:
                conn.execute("""
                    INSERT INTO scores (tournament_id, player_id, gross_score, handicap, net_score)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, score)
            
            conn.commit()
            return True
    except Exception as e:
        st.error(f"サンプルデータ挿入エラー: {e}")
        return False

def main():
    st.title("🏌️ 88会ゴルフコンペ・スコア管理システム")
    st.markdown("### 📊 Railway PostgreSQL版")
    
    # データベース接続
    engine = init_connection()
    
    # サイドバー
    st.sidebar.title("📋 メニュー")
    page = st.sidebar.selectbox("ページを選択", ["スコア一覧", "ランキング", "統計情報", "システム情報"])
    
    # データ読み込み
    if engine:
        # DBテーブル作成
        if create_tables(engine):
            st.sidebar.success("✅ データベース接続完了")
            
            # 初回データ確認・挿入
            df = load_data_from_db(engine)
            if df.empty:
                if insert_sample_data(engine):
                    df = load_data_from_db(engine)
                    st.sidebar.info("📝 サンプルデータを挿入しました")
        else:
            st.sidebar.error("❌ データベース初期化失敗")
            df = load_sample_data()
    else:
        st.sidebar.warning("⚠️ DB未接続 - サンプルデータ使用")
        df = load_sample_data()
    
    if page == "スコア一覧":
        st.header("📊 最新スコア一覧")
        st.dataframe(df, use_container_width=True)
        
        # 基本統計
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("参加者数", len(df))
        with col2:
            st.metric("平均スコア", f"{df['score'].mean():.1f}")
        with col3:
            st.metric("ベストスコア", df['score'].min())
        with col4:
            st.metric("平均ネット", f"{df['net_score'].mean():.1f}")
    
    elif page == "ランキング":
        st.header("🏆 ランキング")
        
        # ネットスコアランキング
        st.subheader("ネットスコアランキング")
        ranking_df = df.sort_values('net_score').reset_index(drop=True)
        ranking_df.index += 1
        
        # 順位列を追加
        ranking_display = ranking_df[['player_name', 'score', 'hdcp', 'net_score']].copy()
        ranking_display.columns = ['プレイヤー名', 'グロススコア', 'ハンディキャップ', 'ネットスコア']
        
        st.dataframe(ranking_display, use_container_width=True)
        
        # 上位3位表彰
        st.subheader("🥇 表彰台")
        if len(ranking_df) >= 3:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("### 🥇 1位")
                st.write(f"**{ranking_df.iloc[0]['player_name']}**")
                st.write(f"ネット: {ranking_df.iloc[0]['net_score']}")
            with col2:
                st.markdown("### 🥈 2位")
                st.write(f"**{ranking_df.iloc[1]['player_name']}**")
                st.write(f"ネット: {ranking_df.iloc[1]['net_score']}")
            with col3:
                st.markdown("### 🥉 3位")
                st.write(f"**{ranking_df.iloc[2]['player_name']}**")
                st.write(f"ネット: {ranking_df.iloc[2]['net_score']}")
    
    elif page == "統計情報":
        st.header("📈 統計情報")
        
        # スコア分布グラフ
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # グロススコア分布
        ax1.hist(df['score'], bins=8, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.set_title('グロススコア分布')
        ax1.set_xlabel('スコア')
        ax1.set_ylabel('人数')
        ax1.grid(True, alpha=0.3)
        
        # ネットスコア分布
        ax2.hist(df['net_score'], bins=8, alpha=0.7, color='lightgreen', edgecolor='black')
        ax2.set_title('ネットスコア分布')
        ax2.set_xlabel('ネットスコア')
        ax2.set_ylabel('人数')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # スコア比較
        st.subheader("📊 スコア比較")
        comparison_df = df[['player_name', 'score', 'net_score']].copy()
        comparison_df.columns = ['プレイヤー名', 'グロス', 'ネット']
        
        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.arange(len(comparison_df))
        width = 0.35
        
        ax.bar(x - width/2, comparison_df['グロス'], width, label='グロススコア', alpha=0.8)
        ax.bar(x + width/2, comparison_df['ネット'], width, label='ネットスコア', alpha=0.8)
        
        ax.set_xlabel('プレイヤー')
        ax.set_ylabel('スコア')
        ax.set_title('グロス vs ネットスコア比較')
        ax.set_xticks(x)
        ax.set_xticklabels(comparison_df['プレイヤー名'], rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig)
    
    elif page == "システム情報":
        st.header("🔧 システム情報")
        
        # デプロイ環境情報
        st.subheader("📱 デプロイメント情報")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**環境:**")
            platform = "Railway" if os.getenv('RAILWAY_ENVIRONMENT') else "ローカル"
            st.write(f"- プラットフォーム: {platform}")
            st.write(f"- ポート: {os.getenv('PORT', '8502')}")
            st.write(f"- Python: 利用可能")
            st.write(f"- Streamlit: 利用可能")
        
        with col2:
            st.write("**データベース:**")
            if engine:
                st.write("- タイプ: PostgreSQL (Railway)")
                st.write("- 状態: ✅ 接続済み")
                st.write("- URL: 設定済み")
                st.write("- エラー: なし")
            else:
                st.write("- タイプ: インメモリ（サンプル）")
                st.write("- 状態: ⚠️ DB未接続")
                st.write("- 外部依存: なし")
                st.write("- モード: ローカル開発")
        
        # 機能状況
        st.subheader("⚙️ 機能状況")
        features = {
            "スコア表示": "✅ 正常",
            "ランキング表示": "✅ 正常", 
            "統計グラフ": "✅ 正常",
            "日本語表示": "✅ 正常",
            "レスポンシブデザイン": "✅ 正常",
            "データベース": "✅ 正常" if engine else "⚠️ 未接続",
            "DBライブラリ": "✅ 利用可能" if DB_AVAILABLE else "⚠️ 未インストール"
        }
        
        for feature, status in features.items():
            st.write(f"- {feature}: {status}")
        
        # 成功メッセージ
        if engine:
            st.success("🎉 Railway PostgreSQLに接続成功！本格的なデータベースで動作中です。")
        else:
            st.info("ℹ️ ローカル環境ではサンプルデータで動作しています。Railwayデプロイ時にPostgreSQLが利用されます。")
        
        # デバッグ情報
        with st.expander("🔍 詳細情報"):
            st.write("**環境変数:**")
            env_vars = {k: v for k, v in os.environ.items() 
                       if any(keyword in k.upper() for keyword in ['RAILWAY', 'PORT', 'DATABASE', 'PYTHON'])}
            for key, value in env_vars.items():
                if 'DATABASE' in key:
                    st.write(f"- {key}: ***設定済み***")
                else:
                    st.write(f"- {key}: {value}")
            
            st.write("**システム:**")
            st.write(f"- 作業ディレクトリ: {os.getcwd()}")
            st.write(f"- データフレーム行数: {len(df)}")
            st.write(f"- 最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"- DBライブラリ: {'利用可能' if DB_AVAILABLE else '未インストール'}")

if __name__ == "__main__":
    main()
