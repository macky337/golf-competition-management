import streamlit as st
import platform
import sys
import subprocess

def get_git_revision():
    """現在のGitリビジョン（コミットハッシュ）を取得する"""
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "N/A"

def display_debug_info():
    """デバッグ情報を表示する"""
    st.subheader("デバッグ情報")
    st.write(f"**Pythonバージョン:** {sys.version}")
    st.write(f"**Streamlitバージョン:** {st.__version__}")
    st.write(f"**OS:** {platform.system()} {platform.release()}")
    st.write(f"**Gitリビジョン:** {get_git_revision()}")
