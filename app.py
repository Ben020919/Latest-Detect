import streamlit as st
from playwright.sync_api import sync_playwright
import os, re, time

os.system("playwright install chromium")

st.set_page_config(page_title="HKTVmall 真相調查", layout="wide")
st.title("🕵️ 數據真相調查：真人模擬模式")

try:
    USERNAME = st.secrets["HKTV_USERNAME"]
    PASSWORD = st.secrets["HKTV_PASSWORD"]
except:
    st.error("請設定 Secrets")

if st.button("🔍 開始真人模擬抓取 (驗證數據真假)"):
    with st.status("🤖 模擬真人操作中...", expanded=True) as status:
        try:
            with sync_playwright() as p:
                # 💡 關鍵：加入 user_agent 偽裝成真實瀏覽器，避開部分防爬偵測
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()
                
                # 1. 登入
                page.goto("https://merchant.shoalter.com/login")
                page.locator('#account').fill(USERNAME)
                page.locator('#password').fill(PASSWORD)
                page.locator('button[data-testid="繼續"]').click()
                page.wait_for_timeout(7000)
                
                # 2. 手動導航到訂單頁 (不靠網址參數)
                st.write("📍 正在進入訂單管理頁面...")
                page.goto("https://merchant.shoalter.com/zh/order-management/orders/toship")
                page.wait_for_timeout(5000)

                # 3. 診斷：截圖看現在預設是什麼數字
                st.image(page.screenshot(), caption="診斷 1：剛進入頁面的原始狀態 (看日期/店鋪是否正確)")

                # 4. 點擊「商戶8小時送貨」並等待
                st.write("👆 點擊「商戶8小時送貨」...")
                page.get_by_text("商戶8小時送貨").first.click()
                page.wait_for_timeout(3000)

                # 5. 抓取「已建立」
                st.write("🔍 正在嘗試過濾「已建立」...")
                page.locator('div.ant-select-selector:has-text("運單狀態")').click()
                page.wait_for_timeout(1000)
                page.locator('button:has-text("清除全部")').click()
                page.wait_for_timeout(1000)
                
                # 用文字精確定位
                page.locator('.ant-select-item-option-content').filter(has_text="已建立").click()
                page.locator('button:has-text("套用")').click()
                
                # 🚀 關鍵等待：等待網頁的 Loading 消失
                page.wait_for_timeout(8000) 
                
                # 6. 最終抓取並顯示真相
                result_text = page.locator('span:has-text("結果")').last.inner_text()
                st.image(page.screenshot(), caption="最終結果截圖")
                
                st.success(f"🎯 機器人最終抓到的文字：{result_text}")
                
                browser.close()
        except Exception as e:
            st.error(f"錯誤：{e}")
