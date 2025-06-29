#!/usr/bin/env python3
"""
Railway環境変数設定確認ツール
"""
import os
import sys

def main():
    print("=" * 50)
    print("Railway環境変数設定確認")
    print("=" * 50)
    
    # 必須変数をチェック
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: 設定済み ({len(value)} 文字)")
            if var == 'SUPABASE_URL':
                print(f"   プレビュー: {value[:30]}...")
            elif var == 'SUPABASE_KEY':
                print(f"   プレビュー: {value[:30]}...")
        else:
            print(f"❌ {var}: 未設定")
            missing_vars.append(var)
    
    # Railway固有の変数をチェック
    print(f"\n🚂 Railway環境: {os.getenv('RAILWAY_ENVIRONMENT_NAME', '未検出')}")
    print(f"📦 プロジェクト: {os.getenv('RAILWAY_PROJECT_NAME', '未検出')}")
    print(f"🔧 サービス: {os.getenv('RAILWAY_SERVICE_NAME', '未検出')}")
    
    if missing_vars:
        print(f"\n⚠️ 設定が必要な変数: {', '.join(missing_vars)}")
        print("\n🔧 設定方法:")
        print("1. Railway Dashboard → プロジェクト選択")
        print("2. 'Variables' タブをクリック")
        print("3. 'New Variable' で以下を追加:")
        for var in missing_vars:
            if var == 'SUPABASE_URL':
                print(f"   {var} = https://your-project-ref.supabase.co")
            elif var == 'SUPABASE_KEY':
                print(f"   {var} = eyJhbGciOiJIUzI1NiI...")
        return 1
    else:
        print("\n✅ すべての必須環境変数が設定されています")
        return 0

if __name__ == "__main__":
    sys.exit(main())
