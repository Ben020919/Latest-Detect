import streamlit as st
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import os

# 確保 Streamlit 雲端有安裝瀏覽器
os.system("playwright install chromium")

st.set_page_config(page_title="HKTVmall 爬蟲開發", layout="wide")
st.title("🛠️ 第二關：導航與視覺確認")

try:
    USERNAME = st.secrets["HKTV_USERNAME"]
    PASSWORD = st.secrets["HKTV_PASSWORD"]
except KeyError:
    USERNAME = ""
    PASSWORD = ""
    st.error("⚠️ 尚未設定 Streamlit Secrets 帳號密碼！")

if st.button("🚀 執行第二關測試 (登入 + 前往訂單頁 + 截圖)"):
    if not USERNAME or not PASSWORD:
        st.warning("請先到 Streamlit Cloud 後台設定 Secrets！")
    else:
        with st.spinner("🤖 機器人正在登入並前往訂單頁面，請稍候約 15 秒..."):
            try:
                with sync_playwright() as p:
                    # 設定大螢幕尺寸，確保截圖完整
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
                    page = context.new_page()
                    
                    # 1. 登入
                    st.toast("正在登入中...")
                    page.goto("https://merchant.shoalter.com/login")
                    page.locator('#account').fill(USERNAME)
                    page.locator('#password').fill(PASSWORD)
                    page.locator('button[data-testid="繼續"]').click()
                    page.wait_for_timeout(5000) 
                    
                    # 2. 計算今天的日期 (香港時間)
                    now = datetime.utcnow() + timedelta(hours=8)
                    today_str = now.strftime("%Y-%m-%d")
                    st.toast(f"準備前往 {today_str} 的訂單頁面...")
                    
                    # 3. 組合目標網址 (請確認 storefrontCodes 是否正確)
                    target_url = (
                        f"https://merchant.shoalter.com/zh/order-management/orders/toship"
                        f"?bu=HKTV&deliveryType=STANDARD_DELIVERY&productReadyMethod=STANDARD_DELIVERY_ALL"
                        f"&searchType=ORDER_ID&storefrontCodes=H0956004%2CH0956006%2CH0956007%2CH0956008%2CH0956010%2CH0956012"
                        f"&dateType=PICK_UP_DATE&startDate={today_str}&endDate={today_str}"
                        f"&pageSize=20&pageNumber=1&sortColumn=orderDate&waybillStatuses="
                    )
                    
                    # 4. 直接跳轉到訂單頁面
                    page.goto(target_url)
                    
                    # 💡 給網頁 8 秒鐘的時間，讓那些轉圈圈的數字和表格徹底載入完畢
                    page.wait_for_timeout(8000)
                    
                    # 5. 拍下機器人看到的畫面！
                    screenshot_bytes = page.screenshot()
                    
                    st.success("✅ 導航成功！請查看下方機器人拍到的真實畫面：")
                    st.write(f"**目前網址:** `{page.url}`")
                    
                    # 把截圖顯示在 Streamlit 網頁上
                    st.image(screenshot_bytes, caption=f"機器人視角：{today_str} 待出貨訂單", use_container_width=True)
                    
                    browser.close()
            except Exception as e:
                st.error(f"❌ 發生錯誤：{e}")
