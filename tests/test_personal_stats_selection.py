"""Empty personal-stat pages remain navigable without connecting to a database."""

import ast
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest


@pytest.mark.parametrize(
    ("scores", "message"),
    [
        (pd.DataFrame(), "個人成績データを取得できません。"),
        (pd.DataFrame({"プレイヤー名": [None]}), "表示できるプレイヤーがいません。"),
    ],
)
def test_empty_stats_allow_return_to_main(scores, message):
    source = (Path(__file__).resolve().parents[1] / "app" / "app.py").read_text(encoding="utf-8-sig")
    functions = [
        ast.get_source_segment(source, node)
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name in {"_navigate", "personal_stats_page"}
    ]
    script = "import streamlit as st\n" + "\n\n".join(functions)
    script += '\n\ndef fetch_scores():\n    return st.session_state["scores"]\n'
    script += '\nif st.session_state.get("page") == "main":\n    st.title("メイン画面")\nelse:\n    personal_stats_page()\n'
    app = AppTest.from_string(script)
    app.session_state["scores"] = scores
    app.run()
    assert not app.exception
    assert message in [element.value for element in list(app.warning) + list(app.info)]
    assert not app.selectbox
    app.button(key="back_to_main_from_stats_modern").click().run()
    assert not app.exception
    assert app.title[0].value == "メイン画面"
