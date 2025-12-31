import re

# app.pyの内容を読み込み
with open('app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. インポート部分を有効化
old_imports = '''# 他のモジュールをインポート
from announcement_management import announcement_management_tab
# プレースホルダーとして他の管理モジュールもインポート
# from player_management import player_management_tab
# from competition_management import competition_management_tab
# from score_entry import score_entry_tab'''

new_imports = '''# 他のモジュールをインポート
from announcement_management import announcement_management_tab
# プレースホルダーとして他の管理モジュールもインポート
from player_management import player_management_tab
from competition_management import competition_management_tab
from score_entry import score_entry_page as score_entry_tab'''

# 2. 管理者機能のタブを有効化
old_admin_tabs = '''    with tabs[1]:
        st.subheader("プレイヤー管理")
        st.write("（この機能は現在開発中です）")
        # player_management_tab(supabase_admin)

    with tabs[2]:
        st.subheader("コンペ設定")
        st.write("（この機能は現在開発中です）")
        # competition_management_tab(supabase_admin)

    with tabs[3]:
        st.subheader("スコア入力")
        st.write("（この機能は現在開発中です）")
        # score_entry_tab(supabase_admin)'''

new_admin_tabs = '''    with tabs[1]:
        player_management_tab(supabase_admin)

    with tabs[2]:
        competition_management_tab(supabase_admin)

    with tabs[3]:
        score_entry_tab()'''

# 置き換えを実行
content = content.replace(old_imports, new_imports)
content = content.replace(old_admin_tabs, new_admin_tabs)

# 修正した内容をファイルに書き込み
with open('app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ app.pyの管理者機能を有効化しました")
print("- プレイヤー管理：有効化")
print("- コンペ設定：有効化")  
print("- スコア入力：有効化")
