import streamlit as st
from playwright.sync_api import sync_playwright
import os

# 確保 Streamlit 雲端有安裝瀏覽器
os.system("playwright install chromium")

st.set_page_config(page_title="HKTVmall 爬蟲開發", layout="centered")
st.title("🛠️ 第一關：測試登入")

# 👉 改用 st.secrets 來讀取帳號密碼 (絕對安全，不會外洩到 GitHub)
try:
    USERNAME = st.secrets["HKTV_USERNAME"]
    PASSWORD = st.secrets["HKTV_PASSWORD"]
except KeyError:
    USERNAME = ""
    PASSWORD = ""
    st.error("⚠️ 尚未設定 Streamlit Secrets 帳號密碼！")

if st.button("🚀 執行登入測試"):
    if not USERNAME or not PASSWORD:
        st.warning("請先到 Streamlit Cloud 後台設定 Secrets！")
    else:
        with st.spinner("🤖 正在啟動隱形瀏覽器並嘗試登入..."):
            try:
                with sync_playwright() as p:
                    # 設定 1920x1080 視窗，確保網頁不會變形
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
                    page = context.new_page()
                    
                    # 1. 前往登入頁面
                    page.goto("https://merchant.shoalter.com/login")
                    
                    # 2. 輸入帳號密碼並點擊繼續
                    page.locator('#account').fill(USERNAME)
                    page.locator('#password').fill(PASSWORD)
                    page.locator('button[data-testid="繼續"]').click()
                    
                    # 3. 等待 5 秒讓系統載入跳轉
                    page.wait_for_timeout(5000) 
                    
                    # 4. 驗證是否登入成功 (抓取當下網址)
                    current_url = page.url
                    page_title = page.title()
                    
                    st.success("✅ 登入動作執行完畢！")
                    st.write(f"**登入後的網頁標題:** `{page_title}`")
                    st.write(f"**目前的網址:** `{current_url}`")
                    
                    # 判斷網址有沒有離開 login 頁面
                    if "login" not in current_url:
                        st.balloons()
                        st.info("🎉 完美！我們成功登入並跳轉到後台了！")
                    else:
                        st.error("❌ 網址還是停留在 login，可能是密碼錯誤，或是遇到了機器人驗證碼。")
                        
                    browser.close()
            except Exception as e:
                st.error(f"❌ 發生錯誤：{e}")
