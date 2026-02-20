import streamlit as st

# 設定網頁標題與寬版顯示
st.set_page_config(page_title="HKTVmall 庫存與訂單系統", layout="wide")

# 顯示標題
st.title("📦 庫存與訂單查詢系統 (測試中)")
st.success("✅ 網頁地基建立成功！GitHub 同步正常！")

# 建立一個簡單的輸入框，為之後的搜尋做準備
user_input = st.text_input("請輸入測試關鍵字：", placeholder="例如：SKU 或 Barcode")

if user_input:
    st.write(f"你輸入了：**{user_input}**")
    st.info("下一步我們將在這裡串接真實的資料！")
