# 🏌️ Railway PostgreSQL移行ガイド

## 📋 作成されたファイル

### Railway PostgreSQL版
- `app_railway.py` - PostgreSQL対応版アプリ
- `requirements_railway.txt` - PostgreSQL依存関係
- `start_railway.sh` - Railway用起動スクリプト
- `Procfile_railway` - Railway用Procfile
- `railway_postgres.json` - Railway設定

## 🚀 Railwayでの設定手順

### 1. PostgreSQLデータベース追加
1. Railwayダッシュボードでプロジェクトを開く
2. 「Add Service」→「Database」→「PostgreSQL」を選択
3. 自動でPostgreSQLサービスが作成されます

### 2. 環境変数設定
Railwayが自動で以下の環境変数を設定します：
- `DATABASE_URL` - PostgreSQL接続URL

### 3. デプロイファイル入れ替え
以下のファイルを既存のものと入れ替えてデプロイ：

```bash
# Railway版に切り替え
mv Procfile_railway Procfile
mv requirements_railway.txt requirements.txt
mv railway_postgres.json railway.json
```

### 4. アプリファイル変更
- `app.py` → `app_railway.py` を使用
- または `app_railway.py` の内容を `app.py` にコピー

## 🔧 機能

### PostgreSQL対応機能
- **プレイヤー管理** - players テーブル
- **大会管理** - tournaments テーブル  
- **スコア管理** - scores テーブル
- **自動テーブル作成** - 初回起動時
- **サンプルデータ挿入** - 初回起動時

### フォールバック機能
- DB接続失敗時は自動でサンプルデータ使用
- ローカル開発でも動作可能

## 📊 データベース構造

```sql
-- プレイヤーテーブル
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 大会テーブル
CREATE TABLE tournaments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    date DATE NOT NULL,
    course VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- スコアテーブル
CREATE TABLE scores (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id),
    player_id INTEGER REFERENCES players(id),
    gross_score INTEGER NOT NULL,
    handicap INTEGER DEFAULT 0,
    net_score INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## ✅ 利点

1. **永続データ** - データがPostgreSQLに保存される
2. **スケーラブル** - 大量データ対応
3. **リレーショナル** - 正規化されたデータ構造
4. **バックアップ** - Railway自動バックアップ
5. **フォールバック** - DB接続失敗時もサンプルデータで動作

---

**Status: Railway PostgreSQL版準備完了 🚀**
