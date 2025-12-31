import re

# competition_management.pyの内容を読み込み
with open('app/competition_management.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 問題のある表示部分を修正版に置き換え
old_display_code = '''        if competitions:
            df = pd.DataFrame(competitions)
            # 日付順でソート
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date', ascending=False)
            
            # 表示用に日付フォーマットを調整
            df['date_display'] = df['date'].dt.strftime('%Y-%m-%d')
            display_df = df[['name', 'date_display', 'location', 'course', 'status']].copy()
            display_df.columns = ['コンペ名', '開催日', '開催地', 'コース', 'ステータス']
            
            st.dataframe(display_df, use_container_width=True)'''

new_display_code = '''        if competitions:
            df = pd.DataFrame(competitions)
            
            # 実際に存在するカラムを確認してから処理
            st.write("**デバッグ情報（カラム名）:**", list(df.columns))
            
            # 必要なカラムの存在確認と安全な処理
            display_columns = []
            column_mapping = {}
            
            # 基本的なカラムの確認
            if 'name' in df.columns:
                display_columns.append('name')
                column_mapping['name'] = 'コンペ名'
            elif 'title' in df.columns:
                display_columns.append('title')
                column_mapping['title'] = 'コンペ名'
            
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date', ascending=False)
                df['date_display'] = df['date'].dt.strftime('%Y-%m-%d')
                display_columns.append('date_display')
                column_mapping['date_display'] = '開催日'
            
            if 'location' in df.columns:
                display_columns.append('location')
                column_mapping['location'] = '開催地'
            
            if 'course' in df.columns:
                display_columns.append('course')
                column_mapping['course'] = 'コース'
            
            if 'status' in df.columns:
                display_columns.append('status')
                column_mapping['status'] = 'ステータス'
            
            # 安全にDataFrameを作成
            if display_columns:
                display_df = df[display_columns].copy()
                display_df.columns = [column_mapping.get(col, col) for col in display_columns]
                st.dataframe(display_df, use_container_width=True)
            else:
                # カラム名が異なる場合は、全データを表示
                st.write("**データ構造が想定と異なります。全データを表示します:**")
                st.dataframe(df, use_container_width=True)'''

# 置き換えを実行
content = content.replace(old_display_code, new_display_code)

# 修正した内容をファイルに書き込み
with open('app/competition_management.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ competition_management.pyのカラム参照エラーを修正しました")
print("- 安全なカラム参照に変更")
print("- デバッグ情報を追加")
print("- 存在しないカラムのフォールバック処理")
