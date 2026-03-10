import streamlit as st
import pandas as pd
from datetime import date
import os

# --- ページの設定 ---
st.set_page_config(page_title="現状確認ダッシュボード", layout="wide")
st.title("📌 現状確認ダッシュボード")

# ボードの名前
GENRES = ["ベネッセ", "体育局", "福田ゼミ", "趣味"]

# --- データの読み込み関数 ---
def load_data(genre):
    file_path = f"data_{genre}.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        # 空文字対策
        if "関連リンク" in df.columns:
            df["関連リンク"] = df["関連リンク"].fillna("").astype(str)
        if "備考" in df.columns:
            df["備考"] = df["備考"].fillna("").astype(str)
        
        df['期日'] = pd.to_datetime(df['期日']).dt.date
        return df
    else:
        return pd.DataFrame({
            "進捗": [False], "優先度": ["中"], "プロジェクト": ["例：イベント"],
            "タスク": ["例：書類作成"], "期日": [date.today()], "関連リンク": [""], "備考": [""]
        })

def save_data(df, genre):
    df.to_csv(f"data_{genre}.csv", index=False)

# --- メイン処理 ---
tabs = st.tabs(GENRES)

for i, genre in enumerate(GENRES):
    with tabs[i]:
        df = load_data(genre)
        today = date.today()

        # 残り日数の計算
        def calculate_days(target_date):
            if pd.isna(target_date):
                return 0
            return (target_date - today).days

        df['残り日数'] = df['期日'].apply(calculate_days)
        
        # 進捗率
        done_count = df["進捗"].sum()
        total_count = len(df)
        progress = done_count / total_count if total_count > 0 else 0
        st.progress(progress, text=f"達成率: {int(progress * 100)}%")

        # データエディタ（カッコの閉じに注意して作成）
        edited_df = st.data_editor(
            df,
            column_config={
                "進捗": st.column_config.CheckboxColumn("完了"),
                "優先度": st.column_config.SelectboxColumn("優先度", options=["高", "中", "低"]),
                "期日": st.column_config.DateColumn("期日", required=True),
                "残り日数": st.column_config.NumberColumn("残り(日)", disabled=True, format="%d 日"),
                "関連リンク": st.column_config.LinkColumn("関連URL"),
            },
            num_rows="dynamic",
            key=f"editor_{genre}",
            use_container_width=True
        )

        # 保存ボタン
        if st.button(f"💾 {genre} のデータを保存", key=f"save_{genre}"):
            save_df = edited_df.drop(columns=["残り日数"]).dropna(subset=["期日"])
            save_data(save_df, genre)
            st.success(f"{genre} のデータを保存しました！")
            st.rerun()

# サイドバー
with st.sidebar:
    st.info(f"今日は {today} です。")
    st.write("【操作ガイド】")
    st.write("1. 表の下の「+」でタスク追加")
    st.write("2. 日付を選んで保存")
    st.write("3. 「残り」が自動計算されます")