#!/usr/bin/env python3
"""
Railway環境変数診断・修正スクリプト
"""
import os

print("🔍 Railway環境変数診断開始")
print("=" * 50)

# 全環境変数をチェック
port_related = {}
streamlit_related = {}
railway_related = {}

for key, value in os.environ.items():
    if 'PORT' in key.upper():
        port_related[key] = value
    elif key.startswith('STREAMLIT_'):
        streamlit_related[key] = value
    elif key.startswith('RAILWAY_'):
        railway_related[key] = value

print("📍 PORT関連環境変数:")
for k, v in port_related.items():
    print(f"  {k} = '{v}'")

print("\n🎛️ STREAMLIT関連環境変数:")
for k, v in streamlit_related.items():
    print(f"  {k} = '{v}'")

print("\n🚂 RAILWAY関連環境変数:")
for k, v in railway_related.items():
    print(f"  {k} = '{v}'")

print("\n" + "=" * 50)

# 問題の診断
issues = []
if os.getenv('STREAMLIT_SERVER_PORT') == '$PORT':
    issues.append("STREAMLIT_SERVER_PORT が '$PORT' (文字列)")

port_val = os.getenv('PORT', '8501')
if port_val == '$PORT':
    issues.append("PORT が '$PORT' (文字列)")

if issues:
    print("🚨 検出された問題:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("✅ 環境変数に明らかな問題は見つかりませんでした")

print("\n🔧 推奨対策:")
print("1. Railwayダッシュボードで STREAMLIT_SERVER_PORT 環境変数を削除")
print("2. PORT は Railway が自動設定するため手動設定不要")
print("3. 現在のスクリプトが環境変数をクリアして安全な値を使用")

print("\n" + "=" * 50)
