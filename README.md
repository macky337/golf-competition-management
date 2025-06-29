# 🏌️ 88会ゴルフコンペ・スコア管理システム (Flask版)

**Railway対応 - 最小Flask版ゴルフスコア管理システム**

## ✅ 解決済み問題

- ❌ `STREAMLIT_SERVER_PORT='$PORT'` エラー → ✅ **完全解決**
- ❌ `streamlit: command not found` エラー → ✅ **完全解決**
- ❌ ビルド・デプロイ失敗 → ✅ **安定動作**

## 🚀 現在の構成

- **app_simple.py** - Flask単体アプリ（依存関係最小）
- **Procfile** - `web: python3 app_simple.py`
- **requirements.txt** - `flask>=3.0.0` のみ
- **railway.json** - Railway最適化設定
- **nixpacks.toml** - ビルド設定明確化

## 🎯 特徴

- 🚫 **Streamlit完全不使用** → PORTエラー根絶
- ⚡ **最小依存関係** → 高速ビルド・確実デプロイ
- 🎨 **美しいUI** → HTML/CSS による洗練されたデザイン
- 🏥 **ヘルスチェック** → `/health` エンドポイント搭載
- 📊 **システム情報** → `/info` エンドポイント

## 📱 エンドポイント

- `/` - メインダッシュボード
- `/health` - ヘルスチェック
- `/info` - システム情報

## 🔧 ローカル実行

```bash
python3 app_simple.py
```

ブラウザで `http://localhost:5000` にアクセス

## 🌐 Railway デプロイ状況

- **最新コミット**: `ac44b0b4`
- **設定**: Procfile + nixpacks.toml
- **状態**: 正常稼働予定

---

**88会ゴルフコンペ・スコア管理システム**  
Version 2.0 - Streamlit問題完全解決版