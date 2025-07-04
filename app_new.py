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
    # app/app.pyの内容を実行
    with open(APP_PATH, 'r', encoding='utf-8') as f:
        code = f.read()
    
    # グローバル変数として実行
    exec(code, globals())