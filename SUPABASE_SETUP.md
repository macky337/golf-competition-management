# Supabase接続設定ガイド

## 概要
このアプリケーションはSupabaseをデータベースとして使用します。アプリケーションを正常に動作させるには、Supabase接続情報の設定が必要です。

## 設定方法

### 1. Supabaseプロジェクトの準備

1. [Supabase](https://app.supabase.com) にログインし、新しいプロジェクトを作成
2. プロジェクトの設定画面から以下の情報を取得：
   - **Project URL**: `https://your-project-ref.supabase.co`
   - **anon/public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### 2. 環境別の設定

#### A. ローカル開発環境

プロジェクトルートに `.env` ファイルを作成し、以下の内容を記述：

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### B. Streamlit Cloud

2つの方法があります：

**方法1: secrets.tomlファイル**
`.streamlit/secrets.toml` ファイルを作成し、以下の内容を記述：

```toml
[supabase]
url = "https://your-project-ref.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**方法2: Streamlit Cloud設定画面**
1. Streamlit Cloudのアプリ設定画面を開く
2. "Secrets" セクションに上記と同じ内容を入力

#### C. その他のデプロイ環境（Heroku、Docker等）

環境変数として以下を設定：
- `SUPABASE_URL`
- `SUPABASE_KEY`

## セキュリティ注意事項

⚠️ **重要**: 接続情報は機密情報です。以下の点にご注意ください：

- `.env` ファイルや `.streamlit/secrets.toml` ファイルは絶対にGitにコミットしないでください
- これらのファイルは既に `.gitignore` に含まれています
- APIキーは他人と共有しないでください
- 本番環境ではRLS（Row Level Security）を有効にしてください

## データベーススキーマ

アプリケーションは以下のテーブルを使用します：

```sql
-- プレイヤー情報
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    handicap REAL DEFAULT 0,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- コンペ情報
CREATE TABLE competitions (
    competition_id SERIAL PRIMARY KEY,
    date TEXT NOT NULL,
    course TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 参加者情報
CREATE TABLE participants (
    id SERIAL PRIMARY KEY,
    competition_id INTEGER REFERENCES competitions(competition_id),
    player_id INTEGER REFERENCES players(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- スコア情報
CREATE TABLE scores (
    id SERIAL PRIMARY KEY,
    competition_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    course TEXT NOT NULL,
    out_score REAL DEFAULT 0,
    in_score REAL DEFAULT 0,
    handicap REAL DEFAULT 0,
    net_score REAL DEFAULT 0,
    ranking INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- バックアップ情報（オプション）
CREATE TABLE backups (
    id SERIAL PRIMARY KEY,
    backup_id TEXT NOT NULL,
    backup_date TEXT NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## トラブルシューティング

### 接続エラーが発生する場合

1. **設定値の確認**
   - URLとAPIキーが正しく設定されているか確認
   - スペースや改行文字が含まれていないか確認

2. **Supabaseプロジェクトの状態確認**
   - プロジェクトが一時停止されていないか確認
   - 課金制限に達していないか確認

3. **ネットワーク接続の確認**
   - インターネット接続が正常か確認
   - ファイアウォール設定を確認

### データベースが空の場合

1. アプリケーション内の「管理画面」からサンプルデータをインポート
2. または `data/migrate_sqlite_to_supabase.py` スクリプトを使用してデータ移行

### RLS（Row Level Security）の設定

本番環境では以下のポリシーを設定することを推奨：

```sql
-- RLSを有効化
ALTER TABLE players ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE scores ENABLE ROW LEVEL SECURITY;

-- 読み取り専用ポリシー（カスタマイズ可能）
CREATE POLICY "誰でも読み取り可能" ON players FOR SELECT USING (true);
CREATE POLICY "誰でも読み取り可能" ON competitions FOR SELECT USING (true);
CREATE POLICY "誰でも読み取り可能" ON participants FOR SELECT USING (true);
CREATE POLICY "誰でも読み取り可能" ON scores FOR SELECT USING (true);
```

## サポート

設定でご不明な点がございましたら、プロジェクト管理者までお問い合わせください。
