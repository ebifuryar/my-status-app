import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import json

# --- ページの設定 ---
st.set_page_config(page_title="現状確認ダッシュボード", layout="wide")
st.title("📌 現状確認ダッシュボード")

# --- 秘密鍵の自動お掃除・接続設定 ---
def get_connection():
    # Secretsから設定を読み込む
    creds = dict(st.secrets["connections"]["gsheets"])
    
    if "private_key" in creds:
        # 【重要】鍵の中の \n を本物の改行に変え、余計なスペースを徹底的に取り除く
        clean_key = creds["private_key"].replace("\\n", "\n").strip()
        # 万が一、前後に余計な改行や空白があっても除去
        creds["private_key"] = clean_key
    
    # 掃除した設定を使って接続
    return st.connection("gsheets", type=GSheetsConnection, **creds)

conn = get_connection()

GENRES = ["ベネッセ", "体育局", "福田ゼミ", "趣味"]

def load_data(genre):
    try:
        return conn.read(worksheet=genre)
    except:
        return pd.DataFrame({
            "進捗": [False], "優先度": ["中"], "プロジェクト": ["新規"],
            "タスク": ["新規内容"], "期日": [str(date.today())], "関連リンク": [""], "備考": [""]
        })

# --- メイン処理 ---
tabs = st.tabs(GENRES)

for i, genre in enumerate(GENRES):
    with tabs[i]:
        df = load_data(genre)
        today = date.today()

        df['期日'] = pd.to_datetime(df['期日']).dt.date
        df['関連リンク'] = df['関連リンク'].fillna("").astype(str)
        df['残り日数'] = df['期日'].apply(lambda x: (x - today).days if pd.notna(x) else 0)
        
        done_count = df["進捗"].sum()
        total_count = len(df)
        progress = done_count / total_count if total_count > 0 else 0
        st.progress(progress, text=f"達成率: {int(progress * 100)}%")

        edited_df = st.data_editor(
            df,
            column_config={
                "進捗": st.column_config.CheckboxColumn("完了"),
                "優先度": st.column_config.SelectboxColumn("優先度", options=["高", "中", "低"]),
                "期日": st.column_config.DateColumn("期日"),
                "残り日数": st.column_config.NumberColumn("残り(日)", disabled=True),
                "関連リンク": st.column_config.LinkColumn("URL"),
            },
            num_rows="dynamic",
            key=f"editor_{genre}",
            use_container_width=True
        )

        if st.button(f"💾 {genre} を保存", key=f"save_{genre}"):
            save_df = edited_df.drop(columns=["残り日数"])
            save_df['期日'] = save_df['期日'].astype(str)
            conn.update(worksheet=genre, data=save_df)
            st.success("保存完了！")
            st.rerun()
