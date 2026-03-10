import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- ページの設定 ---
st.set_page_config(page_title="現状確認ダッシュボード", layout="wide")
st.title("📌 現状確認ダッシュボード")

# --- 秘密鍵のエラーとTypeErrorを同時に解決する接続処理 ---
def get_connection():
    # Secretsから設定をコピー
    s = st.secrets["connections"]["gsheets"]
    creds = {k: v for k, v in s.items()}
    
    # 秘密鍵の改行コード（\\n）や余計な空白を徹底的に掃除
    if "private_key" in creds:
        creds["private_key"] = creds["private_key"].replace("\\n", "\n").strip()
    
    # st.connectionを使わず、クラスを直接呼び出すことで 'type' の衝突を防ぐ
    return GSheetsConnection(connection_name="gsheets", **creds)

# 接続の実行
try:
    conn = get_connection()
except Exception as e:
    st.error(f"接続設定に問題があります。エラー内容: {e}")
    st.exception(e) # これで詳細な裏側の動きが表示されます
    st.stop()

GENRES = ["ベネッセ", "体育局", "福田ゼミ", "趣味"]

def load_data(genre):
    try:
        return conn.read(worksheet=genre)
    except:
        return pd.DataFrame({
            "進捗": [False], "優先度": ["中"], "プロジェクト": ["新規入力"],
            "タスク": ["内容を入力"], "期日": [str(date.today())], "関連リンク": [""], "備考": [""]
        })

# --- メイン処理 ---
tabs = st.tabs(GENRES)

for i, genre in enumerate(GENRES):
    with tabs[i]:
        df = load_data(genre)
        today = date.today()

        # データ型を整える
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
                "残り日数": st.column_config.NumberColumn("残り", disabled=True),
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
            st.success("保存しました！")
            st.rerun()

