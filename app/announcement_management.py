# -*- coding: utf-8 -*-
"""
お知らせ・ブログ管理機能
管理者が簡単にコンテンツを投稿・編集できる機能
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
from supabase import Client
from typing import Optional

# Supabaseクライアントをグローバル変数として宣言（ただし、初期化は後で行う）
supabase: Optional[Client] = None

def init_announcement_management(supabase_client: Client):
    """このモジュールで使用するSupabaseクライアントを初期化"""
    global supabase
    supabase = supabase_client

def fetch_announcements(is_active_only=True):
    """お知らせ一覧を取得"""
    if not supabase:
        st.error("Supabaseクライアントが初期化されていません。")
        return []
    try:
        query = supabase.table("announcements").select("*")
        if is_active_only:
            query = query.eq("is_active", True)
        
        response = query.order("display_order", desc=True).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"お知らせの取得に失敗しました: {e}")
        return []

def create_announcement(title, content, image_url=None, tournament_info=None, display_order=0):
    """お知らせを作成"""
    if not supabase:
        return False, "Supabaseクライアントが初期化されていません。"
    try:
        data = {
            "title": title,
            "content": content,
            "display_order": display_order,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        if image_url:
            data["image_url"] = image_url
        
        if tournament_info:
            data["tournament_info"] = tournament_info
        
        response = supabase.table("announcements").insert(data).execute()
        return True, "お知らせを作成しました"
    except Exception as e:
        return False, f"エラー: {e}"

def update_announcement(announcement_id, title=None, content=None, image_url=None, tournament_info=None, display_order=None, is_active=None):
    """お知らせを更新"""
    if not supabase:
        return False, "Supabaseクライアントが初期化されていません。"
    try:
        data = {}
        if title is not None:
            data["title"] = title
        if content is not None:
            data["content"] = content
        if image_url is not None:
            data["image_url"] = image_url
        if tournament_info is not None:
            data["tournament_info"] = tournament_info
        if display_order is not None:
            data["display_order"] = display_order
        if is_active is not None:
            data["is_active"] = is_active
        
        response = supabase.table("announcements").update(data).eq("id", announcement_id).execute()
        return True, "お知らせを更新しました"
    except Exception as e:
        return False, f"エラー: {e}"

def delete_announcement(announcement_id):
    """お知らせを削除（論理削除）"""
    if not supabase:
        return False, "Supabaseクライアントが初期化されていません。"
    try:
        response = supabase.table("announcements").update({"is_active": False}).eq("id", announcement_id).execute()
        return True, "お知らせを非表示にしました"
    except Exception as e:
        return False, f"エラー: {e}"

def _legacy_announcement_management_tab(supabase_client: Client):
    """お知らせ管理タブのUI"""
    init_announcement_management(supabase_client)
    st.subheader("📢 お知らせ・大会案内管理")
    
    # サブタブで「一覧」「新規作成」「編集」に分ける
    sub_tabs = st.tabs(["お知らせ一覧", "新規作成", "編集"])
    
    with sub_tabs[0]:
        st.write("### 現在のお知らせ一覧")
        
        # 全て表示するか有効なもののみ表示するか
        show_all = st.checkbox("非表示のお知らせも表示", value=False)
        announcements = fetch_announcements(is_active_only=not show_all)
        
        if announcements:
            for ann in announcements:
                status = "✅ 表示中" if ann.get("is_active") else "❌ 非表示"
                with st.expander(f"{status} {ann.get('title', '無題')} (表示順: {ann.get('display_order', 0)})"):
                    st.write(f"**内容:** {ann.get('content', '')}")
                    
                    if ann.get('image_url'):
                        st.write(f"**画像URL:** {ann.get('image_url')}")
                        try:
                            st.image(ann.get('image_url'), width=300)
                        except:
                            st.warning("画像の読み込みに失敗しました")
                    
                    if ann.get('tournament_info'):
                        st.write("**大会情報:**")
                        info = ann.get('tournament_info')
                        if isinstance(info, str):
                            info = json.loads(info)
                        st.json(info)
                    
                    st.write(f"**作成日:** {ann.get('created_at', '')}")
                    st.write(f"**更新日:** {ann.get('updated_at', '')}")
        else:
            st.info("お知らせはまだありません")
    
    with sub_tabs[1]:
        st.write("### 新しいお知らせを作成")
        
        with st.form("create_announcement_form"):
            title = st.text_input("タイトル", placeholder="第52回88会ゴルフコンペのご案内")
            content = st.text_area("本文", placeholder="次回の開催場所は...", height=100)
            image_url = st.text_input("画像URL（オプション）", placeholder="https://example.com/image.jpg")
            display_order = st.number_input("表示順序（大きいほど上に表示）", min_value=0, value=0)
            
            st.write("#### 大会情報（オプション）")
            with_tournament_info = st.checkbox("大会情報を追加")
            
            tournament_info = None
            if with_tournament_info:
                col1, col2 = st.columns(2)
                with col1:
                    tournament_number = st.number_input("大会回数", min_value=1, value=52)
                    tournament_date = st.date_input("開催日")
                    start_time = st.time_input("スタート時間")
                    course_name = st.text_input("コース名", value="本千葉カントリークラブ")
                    course_url = st.text_input("コースURL", value="https://www.honchiba-cc.co.jp/")
                
                with col2:
                    address = st.text_input("住所", value="千葉市緑区大金沢町311")
                    phone = st.text_input("電話番号", value="043-292-0191")
                    groups = st.number_input("組数", min_value=1, value=3)
                    meeting_time = st.time_input("集合時間")
                    fee = st.text_input("費用", value="18,000+昼食")
                    organizers = st.text_input("幹事", value="吉井.福澤")
                
                tournament_info = {
                    "tournament_number": tournament_number,
                    "date": str(tournament_date),
                    "start_time": str(start_time),
                    "course_name": course_name,
                    "course_url": course_url,
                    "address": address,
                    "phone": phone,
                    "groups": groups,
                    "meeting_time": str(meeting_time),
                    "fee": fee,
                    "organizers": organizers
                }
            
            submitted = st.form_submit_button("作成")
            if submitted:
                if not title or not content:
                    st.error("タイトルと本文は必須です")
                else:
                    success, message = create_announcement(
                        title=title,
                        content=content,
                        image_url=image_url if image_url else None,
                        tournament_info=tournament_info,
                        display_order=display_order
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    with sub_tabs[2]:
        st.write("### お知らせを編集")
        
        announcements = fetch_announcements(is_active_only=False)
        if announcements:
            # 編集するお知らせを選択
            options = {f"{ann.get('title')} (ID: {ann.get('id')})": ann for ann in announcements}
            selected_title = st.selectbox("編集するお知らせを選択", options.keys())
            
            if selected_title:
                selected_ann = options[selected_title]
                
                with st.form("edit_announcement_form"):
                    new_title = st.text_input("タイトル", value=selected_ann.get('title', ''))
                    new_content = st.text_area("本文", value=selected_ann.get('content', ''), height=100)
                    new_image_url = st.text_input("画像URL", value=selected_ann.get('image_url', '') or '')
                    new_display_order = st.number_input("表示順序", value=selected_ann.get('display_order', 0))
                    new_is_active = st.checkbox("表示する", value=selected_ann.get('is_active', True))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_button = st.form_submit_button("更新")
                    with col2:
                        delete_button = st.form_submit_button("削除（非表示）", type="secondary")
                    
                    if update_button:
                        success, message = update_announcement(
                            announcement_id=selected_ann.get('id'),
                            title=new_title,
                            content=new_content,
                            image_url=new_image_url if new_image_url else None,
                            display_order=new_display_order,
                            is_active=new_is_active
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    if delete_button:
                        success, message = delete_announcement(selected_ann.get('id'))
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        else:
            st.info("編集できるお知らせがありません")


def announcement_management_tab(supabase_client: Client):
    """公開状態が分かる、お知らせ・大会案内の管理画面。"""
    init_announcement_management(supabase_client)
    st.subheader("📢 お知らせ・大会案内管理")
    st.info("ホームには「表示する」が有効な案内のうち、表示順が最も大きい1件だけが表示されます。同じ表示順の場合は、新しく作成した案内が優先されます。")

    active_announcements = fetch_announcements(is_active_only=True)
    all_announcements = fetch_announcements(is_active_only=False)
    tabs = st.tabs(["公開状況", "新しい案内を作る", "編集・公開設定"])

    with tabs[0]:
        st.write("### 現在ホームに表示される案内")
        if active_announcements:
            primary = active_announcements[0]
            st.success(f"現在表示中: 「{primary.get('title', '無題')}」")
            st.caption(f"表示順 {primary.get('display_order', 0)} ・ 作成日 {primary.get('created_at', '')}")
            st.write(primary.get("content", ""))
            if primary.get("image_url"):
                try:
                    st.image(primary["image_url"], width=360)
                except Exception:
                    st.warning("画像を読み込めませんでした。URLを確認してください。")
            if len(active_announcements) > 1:
                st.warning(f"公開設定の案内が他に {len(active_announcements) - 1} 件あります。ホームに表示されるのは最上位の1件です。")
        else:
            st.warning("現在ホームに表示する案内がありません。新しい案内を作成するか、既存の案内を「表示する」に変更してください。")

        st.write("### すべての案内")
        if all_announcements:
            primary_id = active_announcements[0].get("id") if active_announcements else None
            rows = []
            for announcement in all_announcements:
                rows.append({
                    "ホーム表示": "表示中" if announcement.get("id") == primary_id else ("公開候補" if announcement.get("is_active") else "非表示"),
                    "タイトル": announcement.get("title", "無題"),
                    "表示順": announcement.get("display_order", 0),
                    "作成日": announcement.get("created_at", ""),
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        else:
            st.info("作成済みの案内はありません。")

    with tabs[1]:
        st.write("### 新しい案内を作る")
        st.caption("作成直後はホームに表示されます。表示したくない場合は、作成後に「編集・公開設定」で非表示にしてください。")
        with st.form("create_announcement_form"):
            title = st.text_input("タイトル", placeholder="第55回88会ゴルフコンペのご案内")
            content = st.text_area("本文", placeholder="次回の開催場所は...", height=120)
            image_url = st.text_input("画像URL（任意）", placeholder="https://example.com/image.jpg")
            display_order = st.number_input("ホームでの優先順位（大きいほど優先）", min_value=0, value=10)
            with_tournament_info = st.checkbox("大会情報も登録する")

            tournament_info = None
            if with_tournament_info:
                col1, col2 = st.columns(2)
                with col1:
                    tournament_number = st.number_input("大会回数", min_value=1, value=55)
                    tournament_date = st.date_input("開催日")
                    start_time = st.time_input("スタート時間")
                    course_name = st.text_input("コース名")
                with col2:
                    meeting_time = st.time_input("集合時間")
                    groups = st.number_input("組数", min_value=1, value=3)
                    fee = st.text_input("費用")
                    organizers = st.text_input("幹事")
                tournament_info = {
                    "tournament_number": tournament_number,
                    "date": str(tournament_date),
                    "start_time": str(start_time),
                    "course_name": course_name,
                    "groups": groups,
                    "meeting_time": str(meeting_time),
                    "fee": fee,
                    "organizers": organizers,
                }

            if st.form_submit_button("作成してホームに表示する", type="primary"):
                if not title.strip() or not content.strip():
                    st.error("タイトルと本文は必須です。")
                else:
                    success, message = create_announcement(title.strip(), content.strip(), image_url or None, tournament_info, display_order)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    with tabs[2]:
        st.write("### 編集・公開設定")
        if not all_announcements:
            st.info("編集できる案内はありません。")
        else:
            options = {
                f"{'表示中' if ann.get('is_active') else '非表示'} ｜ {ann.get('title', '無題')} （表示順 {ann.get('display_order', 0)}）": ann
                for ann in all_announcements
            }
            selected_label = st.selectbox("編集する案内を選択", list(options.keys()), key="announcement_edit_selector")
            selected = options[selected_label]
            with st.form("edit_announcement_form"):
                new_title = st.text_input("タイトル", value=selected.get("title", ""))
                new_content = st.text_area("本文", value=selected.get("content", ""), height=120)
                new_image_url = st.text_input("画像URL（任意）", value=selected.get("image_url", "") or "")
                new_display_order = st.number_input("ホームでの優先順位（大きいほど優先）", min_value=0, value=int(selected.get("display_order", 0)))
                new_is_active = st.checkbox("ホームに表示する", value=bool(selected.get("is_active", True)))
                if st.form_submit_button("変更を保存", type="primary"):
                    if not new_title.strip() or not new_content.strip():
                        st.error("タイトルと本文は必須です。")
                    else:
                        success, message = update_announcement(
                            selected.get("id"), new_title.strip(), new_content.strip(), new_image_url or None,
                            display_order=new_display_order, is_active=new_is_active,
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

            st.markdown("---")
            st.caption("削除はデータを消さず、ホームから非表示にする操作です。")
            if selected.get("is_active"):
                if st.button("この案内をホームから非表示にする", type="secondary", key=f"hide_announcement_{selected.get('id')}"):
                    success, message = delete_announcement(selected.get("id"))
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.info("この案内は現在非表示です。チェックボックスを「ホームに表示する」にして保存すると再公開できます。")
