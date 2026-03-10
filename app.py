import streamlit as st
import pandas as pd
from datetime import date
from google.oauth2.service_account import Credentials
import gspread

# --- ページの設定 ---
st.set_page_config(page_title="現状確認ダッシュボード", layout="wide")
st.title("📌 現状確認ダッシュボード")

# 1. お手元のJSONファイルの内容をここに転記してください
# ※ GitHubで保存する際、また「Allow Secret」が出ますが、前回同様「許可」してください。
info = {
    "type": "service_account",
    "project_id": "norse-augury-489809-k8",
    "private_key_id": "8fedf2ed6623fccc1a256e30d809b71b45ec7f8c",
    "private_key": "-----BEGIN PRIVATE KEY-----\n（★ここにあなたの長い秘密鍵を貼り付け★）\n-----END PRIVATE KEY-----\n",
    "client_email": "viewer@norse-augury-489809-k8.iam.gserviceaccount.com",
    "client_id": "101378109863753583492",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/viewer%40norse-augury-489809-k8.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# あなたのスプレッドシートID（URLの /d/ と /edit の間の英数字）
SPREADSHEET_ID = "1xS3x9SO5Ev7KZOu-UU6RRx5OGldDWbI_rmcAQjXAHCY"

# --- 接続処理（直通版） ---
@st.cache_resource
def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # 秘密鍵の改行を補正
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)

try:
    client = get_gspread_client()
    sh = client.open_by_key(SPREADSHEET_ID)
except Exception as e:
    st.error(f"スプレッドシートへの接続に失敗しました: {e}")
    st.stop()

GENRES = ["ベネッセ", "体育局", "福田ゼミ", "趣味"]

def load_data(genre):
    try:
        worksheet = sh.worksheet(genre)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
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
        
        # データ整形
        if not df.empty:
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
                worksheet = sh.worksheet(genre)
                save_df = edited_df.drop(columns=["残り日数"])
                save_df['期日'] = save_df['期_'] = save_df['期日'].astype(str)
                # 書き込み（一度クリアして全件上書き）
                worksheet.clear()
                worksheet.update([save_df.columns.values.tolist()] + save_df.values.tolist())
                st.success("保存完了！")
                st.rerun()
