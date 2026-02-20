import streamlit as st
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import re
import os

# 確保 Streamlit 雲端有安裝瀏覽器
os.system("playwright install chromium")

st.set_page_config(page_title="HKTVmall 精準抓取面板", layout="wide")
st.title("🎯 終極極速版：直連專屬網址抓取")

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
    st.error("⚠️ 尚未設定 Streamlit Secrets 帳號密碼！")

# 📅 日期選擇器：自動計算今明後三天
now = datetime.utcnow() + timedelta(hours=8)
today_str = now.strftime("%Y-%m-%d")
tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")   # 21號
day_after_str = (now + timedelta(days=2)).strftime("%Y-%m-%d") # 22號

# 預設選在 21 號
test_date_option = st.radio(
    "📅 請選擇你要測試的入倉日期：", 
    [f"今日訂單 ({today_str})", f"明日訂單 ({tomorrow_str})", f"後天訂單 ({day_after_str})"],
    index=1 
)

if st.button("🚀 開始極速抓取！"):
    if not USERNAME or not PASSWORD:
        st.warning("請先設定 Secrets！")
    else:
        # 決定目標日期
        if "今日" in test_date_option:
            target_date_str = today_str
        elif "明日" in test_date_option:
            target_date_str = tomorrow_str
        else:
            target_date_str = day_after_str
            
        with st.status(f"⚡ 任意門啟動！直接跳躍抓取 {target_date_str} 的資料...", expanded=True) as status:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
                    page = context.new_page()
                    
                    # --- 1. 登入 ---
                    st.write("⏳ 正在登入 HKTVmall...")
                    page.goto("https://merchant.shoalter.com/login")
                    page.locator('#account').fill(USERNAME)
                    page.locator('#password').fill(PASSWORD)
                    page.locator('button[data-testid="繼續"]').click()
                    page.wait_for_timeout(5000)
                    
                    # 定義要抓取的 4 個狀態
                    statuses = [("CONFIRMED", "已建立"), ("ACKNOWLEDGED", "已確認"), ("PACKED", "已包裝"), ("PICKED", "已出貨")]
                    date_data = {"date": target_date_str}
                    
                    st.markdown("### 📸 機器人視角監視器")
                    
                    # --- 2. 迴圈：直接透過網址拿資料 ---
                    for status_val, status_name in statuses:
                        st.write(f"✈️ 正在直飛 **{status_name}** 專屬網址...")
                        
                        # 這是你給我的終極網址，我把日期和狀態變成變數！
                        target_url = (
                            f"https://merchant.shoalter.com/zh/order-management/orders/toship"
                            f"?bu=HKTV&deliveryType=STANDARD_DELIVERY&productReadyMethod=SAME_DAY_IN_HUB"
                            f"&searchType=ORDER_ID&storefrontCodes=H0956004%2CH0956006%2CH0956007%2CH0956008%2CH0956010%2CH0956012"
                            f"&dateType=PICK_UP_DATE&startDate={target_date_str}&endDate={target_date_str}"
                            f"&waybillStatuses={status_val}&pageSize=20&pageNumber=1&sortColumn=orderDate"
                        )
                        
                        # 直接跳到這個網址
                        page.goto(target_url)
                        
                        # 強制等待 6 秒，讓頁面把表格和數字仔細渲染出來
                        page.wait_for_timeout(6000)
                        
                        # 拍照存證
                        st.image(page.screenshot(), caption=f"成功抵達：{status_name} 的專屬畫面", use_container_width=True)
                        
                        # 抓取數字
                        try:
                            # 尋找結果數字
                            result_text = page.locator('span:has-text("結果")').last.inner_text(timeout=3000)
                            count = extract_total_count(result_text)
                            date_data[status_val] = count
                            st.write(f"👉 **{status_name}** 抓取成功： **{count}** 筆")
                        except Exception:
                            # 如果沒有結果標籤，通常代表 0 筆
                            date_data[status_val] = "0"
                            st.write(f"👉 **{status_name}** 抓取結果： **0** 筆 (無資料)")
                            
                    browser.close()
                    status.update(label="🎉 極速抓取任務完美結束！", state="complete", expanded=False)
                    
            except Exception as e:
                status.update(label="❌ 任務發生錯誤", state="error", expanded=True)
                st.error(f"錯誤詳情：{e}")
                date_data = {}

        # --- 3. 顯示結果面板 ---
        if date_data:
            st.markdown("---")
            st.subheader(f"📦 機器人回報的 {date_data.get('date')} 訂單總結")
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("已建立 (CONFIRMED)", date_data.get('CONFIRMED', '--'))
            with col2: st.metric("已確認 (ACKNOWLEDGED)", date_data.get('ACKNOWLEDGED', '--'))
            with col3: st.metric("已包裝 (PACKED)", date_data.get('PACKED', '--'))
            with col4: st.metric("已出貨 (PICKED)", date_data.get('PICKED', '--'))
