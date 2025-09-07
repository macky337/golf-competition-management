#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
88会ゴルフコンペ・スコア管理システム - エントリーポイント
このファイルは、Streamlitクラウドのデプロイに必要なエントリーポイントです。
実際のアプリケーションロジックはapp/app.pyに実装されています。
"""

import sys
import os
import importlib.util

# app/app.pyを直接読み込む方法に変更
app_path = os.path.join(os.path.dirname(__file__), 'app', 'app.py')

# モジュール名
module_name = "app_module"

# app.pyファイルをモジュールとして読み込む
spec = importlib.util.spec_from_file_location(module_name, app_path)
app_module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = app_module
spec.loader.exec_module(app_module)

# モジュールの全ての変数をグローバル名前空間にインポート
for name in dir(app_module):
    if not name.startswith("_"):  # プライベート変数以外をインポート
        globals()[name] = getattr(app_module, name)