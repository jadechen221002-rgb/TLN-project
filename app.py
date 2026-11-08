import io

import pandas as pd
import requests
import streamlit as st
import urllib3

# 因為使用 verify=False，關閉 SSL 警告訊息
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_URL = "https://mopsfin.twse.com.tw/opendata/t187ap46_O_1.csv"  # 換連結

st.set_page_config(page_title="公開資料 CSV 檢視器", page_icon="📊", layout="wide")


@st.cache_data(ttl=3600, show_spinner="資料下載中...")
def load_data(url: str) -> pd.DataFrame:
    """下載 CSV 並轉成 DataFrame（快取 1 小時）"""
    response = requests.get(url, verify=False, timeout=30)
    response.raise_for_status()
    # utf-8-sig 可正確處理繁體中文與 BOM
    return pd.read_csv(io.BytesIO(response.content), encoding="utf-8-sig")


st.title("📊 公開資料 CSV 檢視器")

# ---------------- 側邊欄 ----------------
with st.sidebar:
    st.header("設定")
    url = st.text_input("CSV 連結", value=DEFAULT_URL)
    drop_na = st.checkbox("移除含有空值的列 (dropna)", value=True)
    keyword = st.text_input("關鍵字搜尋", placeholder="輸入文字過濾所有欄位")
    if st.button("🔄 重新載入資料"):
        st.cache_data.clear()
        st.rerun()

# ---------------- 載入資料 ----------------
try:
    df = load_data(url)
except requests.exceptions.RequestException as e:
    st.error(f"下載資料失敗：{e}")
    st.stop()
except Exception as e:
    st.error(f"資料解析失敗：{e}")
    st.stop()

if drop_na:
    df = df.dropna()

if keyword:
    mask = df.astype(str).apply(
        lambda col: col.str.contains(keyword, case=False, na=False, regex=False)
    ).any(axis=1)
    df = df[mask]

# ---------------- 顯示結果 ----------------
col1, col2 = st.columns(2)
col1.metric("資料筆數", f"{len(df):,}")
col2.metric("欄位數", f"{df.shape[1]:,}")

st.dataframe(df, use_container_width=True, hide_index=True)

st.download_button(
    label="⬇️ 下載 CSV",
    data=df.to_csv(index=False).encode("utf-8-sig"),
    file_name="data01.csv",
    mime="text/csv",
)
