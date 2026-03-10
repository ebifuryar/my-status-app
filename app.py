import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import json

# --- ページの設定 ---
st.set_page_config(page_title="現状確認ダッシュボード", layout="wide")
st.title("📌 現状確認ダッシュボード")

# --- 設定情報を直接コードに書く（Secretsを使わない方法） ---
# お手元のJSONファイルの中身を、下のシングルクォート (''' ''') の間に貼り付けてください
json_data = '''
{
  "type": "service_account",
  "project_id": "norse-augury-489809-k8",
  "private_key_id": "8fedf2ed6623fccc1a256e30d809b71b45ec7f8c",
  "private_key": "-----BEGIN PRIVATE KEY-----\n（ここに長い秘密鍵が続きます）\n-----END PRIVATE KEY-----\n",
  "client_email": "viewer@norse-augury-489809-k8.iam.gserviceaccount.com",
  "client_id": "101378109863753583492",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/viewer%40norse-augury-489809-k8.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
'''

# 接続に使用するURL（あなたのスプレッドシートURL）
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1xS3x9SO5Ev7KZOu-UU6RRx5OGldDWbI_rmcAQjXAHCY/edit"

# --- 接続処理 ---
@st.cache_resource
def get_connection():
    creds = json.loads(json_data)
    return GSheetsConnection(connection_name="gsheets", service_account_info=creds)

conn = get_connection()

GENRES = ["ベネッセ", "体育局", "福田ゼミ", "趣味"]

def load_data(genre):
    try:
        return conn.read(spreadsheet=SPREADSHEET_URL, worksheet=genre)
    except:
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
        
        st.progress(df["進捗"].sum() / len(df) if len(df) > 0 else 0)

        edited_df = st.data_editor(
            df,
            column_config={
                "進捗": st.column_config.CheckboxColumn("完了"),
                "優先度": st.column_config.SelectboxColumn("優先度", options=["高", "中", "低"]),
                "期日": st.column_config.DateColumn("期日"),
                "残り日数": st.column_config.NumberColumn("残り", disabled=True),
            },
            num_rows="dynamic", key=f"editor_{genre}", use_container_width=True
        )

        if st.button(f"💾 {genre} を保存", key=f"save_{genre}"):
            save_df = edited_df.drop(columns=["残り日数"])
            save_df['期日'] = save_df['期日'].astype(str)
            conn.update(spreadsheet=SPREADSHEET_URL, worksheet=genre, data=save_df)
            st.success("保存完了！")
            st.rerun()
