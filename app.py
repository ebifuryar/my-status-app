import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- ページの設定 ---
st.set_page_config(page_title="現状確認ダッシュボード", layout="wide")
st.title("📌 現状確認ダッシュボード")

GENRES = ["ベネッセ", "体育局", "福田ゼミ", "趣味"]

# --- スプレッドシートへの接続設定 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(genre):
    try:
        # 指定したワークシートを読み込む
        return conn.read(worksheet=genre)
    except:
        # シートが空、または読み込めない場合の初期データ
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

        # データ型を整える（エラー防止）
        df['期日'] = pd.to_datetime(df['期日']).dt.date
        df['関連リンク'] = df['関連リンク'].fillna("").astype(str)

        # 残り日数の計算
        df['残り日数'] = df['期日'].apply(lambda x: (x - today).days if pd.notna(x) else 0)
        
        # 進捗率
        done_count = df["進捗"].sum()
        total_count = len(df)
        progress = done_count / total_count if total_count > 0 else 0
        st.progress(progress, text=f"達成率: {int(progress * 100)}%")

        # データエディタ
        edited_df = st.data_editor(
            df,
            column_config={
                "進捗": st.column_config.CheckboxColumn("完了"),
                "優先度": st.column_config.SelectboxColumn("優先度", options=["高", "中", "低"]),
                "期日": st.column_config.DateColumn("期日"),
                "残り日数": st.column_config.NumberColumn("残り", disabled=True),
                "関連リンク": st.column_config.LinkColumn("URL"),
            },
            num_rows="dynamic",
            key=f"editor_{genre}",
            use_container_width=True
        )

        # 保存ボタン
        if st.button(f"💾 {genre} を保存", key=f"save_{genre}"):
            save_df = edited_df.drop(columns=["残り日数"])
            # 日付を文字列に直して保存（スプレッドシート用）
            save_df['期日'] = save_df['期日'].astype(str)
            conn.update(worksheet=genre, data=save_df)
            st.success("スプレッドシートに保存しました！")
            st.rerun()
