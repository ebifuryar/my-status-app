import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- ページの設定 ---
st.set_page_config(page_title="現状確認ダッシュボード", layout="wide")
st.title("📌 現状確認ダッシュボード")

# --- 接続処理（すべての重複エラーを回避する版） ---
def get_connection():
    # Secretsから設定を取得
    s = st.secrets["connections"]["gsheets"]
    creds = {k: v for k, v in s.items()}
    
    # 1. 秘密鍵の汚れ（改行やスペース）を掃除
    if "private_key" in creds:
        creds["private_key"] = creds["private_key"].replace("\\n", "\n").strip()
    
    # 2. 【重要】接続の邪魔になる項目をすべて取り出す
    creds.pop("spreadsheet", None)
    creds.pop("type", None) # 今回のエラー（unexpected keyword argument 'type'）を解決
    
    # 3. 接続を実行
    return GSheetsConnection(connection_name="gsheets", **creds)

try:
    conn = get_connection()
    # 共通で使用するURLを取得
    target_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
except Exception as e:
    # 万が一エラーが出た場合に詳細を表示
    st.error(f"接続設定に問題があります。エラー内容: {e}")
    st.exception(e)
    st.stop()

GENRES = ["ベネッセ", "体育局", "福田ゼミ", "趣味"]

def load_data(genre):
    try:
        return conn.read(spreadsheet=target_url, worksheet=genre)
    except Exception as e:
        return pd.DataFrame({
            "進捗": [False], "優先度": ["中"], "プロジェクト": ["新規"],
            "タスク": ["内容を入力"], "期日": [str(date.today())], "関連リンク": [""], "備考": [""]
        })

# --- メイン画面表示 ---
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
            conn.update(spreadsheet=target_url, worksheet=genre, data=save_df)
            st.success(f"{genre} のデータを更新しました！")
            st.rerun()
