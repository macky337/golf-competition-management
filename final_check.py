#!/usr/bin/env python3
"""
Railway最終診断スクリプト
環境変数とポート設定を最終確認
"""

import os
import sys
import subprocess

def check_environment():
    """環境変数の最終確認"""
    print("=" * 60)
    print("RAILWAY 最終環境診断")
    print("=" * 60)
    
    # 基本環境情報
    print("\n【基本環境情報】")
    print(f"Python実行ファイル: {sys.executable}")
    print(f"Pythonバージョン: {sys.version}")
    print(f"作業ディレクトリ: {os.getcwd()}")
    
    # ポート関連
    print("\n【ポート設定確認】")
    port_env = os.environ.get('PORT', 'NOT_SET')
    print(f"PORT環境変数: {port_env}")
    print(f"PORTの型: {type(port_env)}")
    
    if port_env != 'NOT_SET':
        try:
            port_int = int(port_env)
            print(f"PORTを整数変換: {port_int} ✓")
        except ValueError as e:
            print(f"PORT整数変換エラー: {e} ✗")
    
    # Supabase環境変数
    print("\n【Supabase設定確認】")
    supabase_url = os.environ.get('SUPABASE_URL', 'NOT_SET')
    supabase_key = os.environ.get('SUPABASE_KEY', 'NOT_SET')
    
    print(f"SUPABASE_URL: {'✓ 設定済み' if supabase_url != 'NOT_SET' else '✗ 未設定'}")
    print(f"SUPABASE_KEY: {'✓ 設定済み' if supabase_key != 'NOT_SET' else '✗ 未設定'}")
    
    if supabase_url != 'NOT_SET':
        print(f"SUPABASE_URL長さ: {len(supabase_url)}")
    if supabase_key != 'NOT_SET':
        print(f"SUPABASE_KEY長さ: {len(supabase_key)}")
    
    # 環境変数一覧（Railway関連のみ）
    print("\n【Railway関連環境変数】")
    railway_vars = [k for k in os.environ.keys() if 'RAILWAY' in k.upper()]
    for var in sorted(railway_vars):
        print(f"{var}: {os.environ[var]}")
    
    # Dockerfileの確認
    print("\n【Dockerfile確認】")
    try:
        with open('Dockerfile', 'r') as f:
            lines = f.readlines()
            cmd_line = [line for line in lines if line.strip().startswith('CMD')]
            if cmd_line:
                print(f"CMD行: {cmd_line[0].strip()}")
            else:
                print("CMD行が見つかりません")
    except FileNotFoundError:
        print("Dockerfileが見つかりません")
    
    # Streamlit設定確認
    print("\n【Streamlit設定確認】")
    config_path = '/app/.streamlit/config.toml'
    if os.path.exists(config_path):
        print("Streamlit設定ファイル存在: ✓")
        try:
            with open(config_path, 'r') as f:
                print("設定内容:")
                print(f.read())
        except Exception as e:
            print(f"設定ファイル読み取りエラー: {e}")
    else:
        print("Streamlit設定ファイル存在: ✗")
    
    print("\n" + "=" * 60)
    print("診断完了")
    print("=" * 60)

if __name__ == "__main__":
    check_environment()
