#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
リダイレクトファイル - app_new.py から app/app.py へ
このファイルは、Railwayが app_new.py を参照している問題を解決するための一時的な対策です。
"""

import os
import sys

# 正しいメインアプリケーションファイルのパスを設定
APP_PATH = os.path.join(os.path.dirname(__file__), 'app', 'app.py')

# app/app.pyを実行
if __name__ == "__main__":
    # app/app.pyの内容を実行（BOM文字を適切に処理）
    with open(APP_PATH, 'r', encoding='utf-8-sig') as f:
        code = f.read()
    
    # BOM文字が残っている場合は除去
    if code.startswith('\ufeff'):
        code = code[1:]
    
    # 実行環境を設定（__file__を正しく設定）
    exec_globals = {
        '__file__': APP_PATH,
        '__name__': '__main__',
        '__package__': None,
        '__doc__': None,
        '__builtins__': __builtins__,
    }
    
    # グローバル変数として実行
    exec(code, exec_globals)