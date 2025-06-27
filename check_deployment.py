#!/usr/bin/env python3
"""
Railway環境変数設定後の確認スクリプト
"""
import os
import time
import sys

def check_deployment_status():
    """デプロイ状況をリアルタイムで確認"""
    
    print("🚀 Railway環境変数設定後の確認")
    print("=" * 50)
    
    # 基本情報
    print(f"⏰ 確認時刻: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🚂 Railway環境: {os.getenv('RAILWAY_ENVIRONMENT_NAME', '不明')}")
    print(f"📦 プロジェクト: {os.getenv('RAILWAY_PROJECT_NAME', '不明')}")
    print(f"🔧 サービス: {os.getenv('RAILWAY_SERVICE_NAME', '不明')}")
    print(f"🌐 URL: {os.getenv('RAILWAY_PUBLIC_DOMAIN', '不明')}")
    
    print("\n🔍 環境変数確認:")
    
    # SUPABASE_URL確認
    supabase_url = os.getenv('SUPABASE_URL')
    if supabase_url:
        print(f"✅ SUPABASE_URL: 設定済み ({len(supabase_url)} 文字)")
        print(f"   プレビュー: {supabase_url[:30]}...")
        
        # URLの妥当性チェック
        if supabase_url.startswith('https://') and '.supabase.co' in supabase_url:
            print("   ✅ URL形式: 正常")
        else:
            print("   ⚠️ URL形式: 要確認（https://で始まり.supabase.coを含むべき）")
    else:
        print("❌ SUPABASE_URL: 未設定")
    
    # SUPABASE_KEY確認
    supabase_key = os.getenv('SUPABASE_KEY')
    if supabase_key:
        print(f"✅ SUPABASE_KEY: 設定済み ({len(supabase_key)} 文字)")
        print(f"   プレビュー: {supabase_key[:30]}...")
        
        # KEYの妥当性チェック
        if supabase_key.startswith('eyJ'):
            print("   ✅ KEY形式: 正常（JWT形式）")
        else:
            print("   ⚠️ KEY形式: 要確認（通常eyJで始まるJWT形式）")
    else:
        print("❌ SUPABASE_KEY: 未設定")
    
    # 設定状況の判定
    if supabase_url and supabase_key:
        print("\n🎉 環境変数設定完了！")
        print("✅ Supabase接続情報が正常に設定されています")
        
        # 接続テストの実行
        print("\n🔗 Supabase接続テスト実行中...")
        try:
            import requests
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            test_url = f"{supabase_url}/rest/v1/"
            response = requests.get(test_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print("✅ Supabase接続テスト成功！")
                print("🚀 アプリケーションは完全に動作可能です")
            else:
                print(f"⚠️ 接続テスト警告: ステータス {response.status_code}")
                print("   APIキーやURL設定を再確認してください")
                
        except Exception as e:
            print(f"⚠️ 接続テストエラー: {e}")
            print("   ネットワークまたは設定に問題がある可能性があります")
            
    elif supabase_url or supabase_key:
        print("\n⚠️ 部分的設定")
        print("一部の環境変数のみ設定されています。両方とも設定してください。")
        
    else:
        print("\n❌ 環境変数未設定")
        print("まだ環境変数が反映されていません。")
        print("Railway再デプロイの完了をお待ちください。")
    
    # デプロイ情報
    deployment_id = os.getenv('RAILWAY_DEPLOYMENT_ID')
    if deployment_id:
        print(f"\n📋 現在のデプロイID: {deployment_id}")
    
    return supabase_url and supabase_key

def main():
    """メイン実行"""
    try:
        status = check_deployment_status()
        
        if status:
            print("\n🎯 次のステップ:")
            print("1. ブラウザでアプリケーションにアクセス")
            print("2. Supabase接続エラーが解消されていることを確認")
            print("3. ログイン機能が正常に動作することを確認")
            print("4. データベース機能を活用してください！")
        else:
            print("\n⏳ 待機推奨:")
            print("1. Railway環境変数設定を再確認")
            print("2. 数分待ってから再デプロイを確認")
            print("3. 必要に応じて手動再デプロイを実行")
            
        print(f"\n🔄 再確認したい場合は、このスクリプトを再実行してください")
        return 0 if status else 1
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
