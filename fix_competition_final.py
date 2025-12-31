import re

# competition_management.pyの内容を読み込み
with open('app/competition_management.py', 'r', encoding='utf-8') as f:
    content = f.read()

# デバッグ情報を削除し、よりシンプルな表示に変更
old_debug_code = '''        if competitions:
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

new_simple_code = '''        if competitions:
            df = pd.DataFrame(competitions)
            
            # 安全なカラム表示（存在するカラムのみ使用）
            display_df = df.copy()
            
            # 日付カラムの処理（存在する場合）
            if 'date' in df.columns:
                try:
                    display_df['date'] = pd.to_datetime(display_df['date'])
                    display_df = display_df.sort_values('date', ascending=False)
                    display_df['開催日'] = display_df['date'].dt.strftime('%Y-%m-%d')
                except:
                    pass
            
            # カラム名を日本語に変換（存在する場合のみ）
            column_rename = {
                'name': 'コンペ名',
                'title': 'コンペ名', 
                'location': '開催地',
                'course': 'コース',
                'status': 'ステータス',
                'description': '説明',
                'id': 'ID'
            }
            
            # 存在するカラムのみリネーム
            for old_name, new_name in column_rename.items():
                if old_name in display_df.columns:
                    display_df = display_df.rename(columns={old_name: new_name})
            
            # 不要なカラムを除外（内部カラムやタイムスタンプなど）
            exclude_cols = ['created_at', 'updated_at', 'date']
            display_columns = [col for col in display_df.columns if col not in exclude_cols]
            
            if display_columns:
                st.dataframe(display_df[display_columns], use_container_width=True)
            else:
                st.dataframe(display_df, use_container_width=True)'''

# 置き換えを実行
content = content.replace(old_debug_code, new_simple_code)

# 修正した内容をファイルに書き込み
with open('app/competition_management.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ より安全で洗練されたカラム表示に修正しました")
print("- デバッグ情報を削除")
print("- 動的なカラム処理")
print("- 日本語カラム名への変換")
