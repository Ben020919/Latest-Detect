import streamlit as st
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import re
import os

os.system("playwright install chromium")

st.set_page_config(page_title="HKTVmall 數據對齊工具", layout="wide")
st.title("🎯 數據對齊模式：抓取數字 + 訂單編號")

def extract_total_count(text):
    if not text: return "0"
    numbers = re.findall(r'\d+', text)
    return numbers[-1] if numbers else "0"

try:
    USERNAME = st.secrets["HKTV_USERNAME"]
    PASSWORD = st.secrets["HKTV_PASSWORD"]
except KeyError:
    USERNAME = ""
    PASSWORD = ""
    st.error("⚠️ 尚未設定 Streamlit Secrets！")

now = datetime.utcnow() + timedelta(hours=8)
target_date_str = (now + timedelta(days=1)).strftime("%Y-%m-%d") # 測試 21 號

if st.button(f"🚀 抓取 {target_date_str} 並列出單號"):
    with st.status(f"🕵️ 正在比對 {target_date_str} 的數據...", expanded=True) as status:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(viewport={'width': 1920, 'height': 1080})
                page = context.new_page()
                
                # 1. 登入
                page.goto("https://merchant.shoalter.com/login")
                page.locator('#account').fill(USERNAME)
                page.locator('#password').fill(PASSWORD)
                page.locator('button[data-testid="繼續"]').click()
                page.wait_for_timeout(5000)
                
                # 2. 準備狀態
                statuses = [("CONFIRMED", "已建立")] # 先精準診斷這一個
                
                for status_val, status_name in statuses:
                    # 使用你提供的 SAME_DAY_IN_HUB 網址
                    target_url = (
                        f"https://merchant.shoalter.com/zh/order-management/orders/toship"
                        f"?bu=HKTV&deliveryType=STANDARD_DELIVERY&productReadyMethod=SAME_DAY_IN_HUB"
                        f"&searchType=ORDER_ID&storefrontCodes=H0956004%2CH0956006%2CH0956007%2CH0956008%2CH0956010%2CH0956012"
                        f"&dateType=PICK_UP_DATE&startDate={target_date_str}&endDate={target_date_str}"
                        f"&waybillStatuses={status_val}&pageSize=20&pageNumber=1&sortColumn=orderDate"
                    )
                    
                    page.goto(target_url)
                    page.wait_for_timeout(7000) # 延長等待確保數字跳完
                    
                    # 抓取「結果」那行字
                    result_raw = page.locator('span:has-text("結果")').last.inner_text()
                    total_count = extract_total_count(result_raw)
                    
                    st.write(f"📊 機器人看到的原始文字：`{result_raw}`")
                    st.write(f"🎯 提取出的總數：**{total_count}**")
                    
                    # --- 💡 新增：抓取前 5 筆訂單編號 ---
                    st.write("📋 該頁面顯示的前 5 筆訂單編號：")
                    # 假設單號在表格中，通常 HKTVmall 單號包含特定前綴或在特定 class 裡
                    # 這裡先抓取頁面上看起來像單號的文字 (數字組合)
                    orders = page.locator('button[type="button"]:has-text("單號")').all_inner_texts()
                    if not orders:
                        # 備案：嘗試抓取連結或特定單元格
                        orders = page.locator('td').filter(has_text=re.compile(r'^\d{10,}$')).all_inner_texts()
                    
                    for i, order_id in enumerate(orders[:5]):
                        st.code(f"第 {i+1} 筆：{order_id}")
                    
                    # 拍照確認
                    st.image(page.screenshot(), caption=f"{status_name} 頁面截圖")
                    
                browser.close()
                status.update(label="診斷完畢！", state="complete")
        except Exception as e:
            st.error(f"錯誤：{e}")
