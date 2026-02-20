import streamlit as st
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import re
import os

# 確保 Streamlit 雲端有安裝瀏覽器
os.system("playwright install chromium")

st.set_page_config(page_title="HKTVmall 爬蟲開發", layout="wide")
st.title("🛠️ 第三關：精準抓取數字測試 (極速防疊加版)")

# --- 輔助函數：提取數字 ---
def extract_total_count(text):
    if not text: return "0"
    numbers = re.findall(r'\d+', text)
    return numbers[-1] if numbers else "0"

# --- 讀取密碼 ---
try:
    USERNAME = st.secrets["HKTV_USERNAME"]
    PASSWORD = st.secrets["HKTV_PASSWORD"]
except KeyError:
    USERNAME = ""
    PASSWORD = ""
    st.error("⚠️ 尚未設定 Streamlit Secrets 帳號密碼！")

# 📅 讓你可以自由選擇要測試哪一天！
now = datetime.utcnow() + timedelta(hours=8)
today_str = now.strftime("%Y-%m-%d")
tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

test_date_option = st.radio(
    "📅 請選擇你要測試的日期：", 
    [f"今日訂單 ({today_str})", f"明日訂單 ({tomorrow_str})"]
)

if st.button("🚀 執行精準抓取測試"):
    if not USERNAME or not PASSWORD:
        st.warning("請先設定 Secrets！")
    else:
        # 決定目標日期字串
        target_date_str = today_str if "今日" in test_date_option else tomorrow_str
        
        with st.status(f"🤖 機器人工作中，正在抓取 {target_date_str} 的資料...", expanded=True) as status:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
                    page = context.new_page()
                    
                    # 1. 登入
                    st.write("⏳ 正在登入 HKTVmall...")
                    page.goto("https://merchant.shoalter.com/login")
                    page.locator('#account').fill(USERNAME)
                    page.locator('#password').fill(PASSWORD)
                    page.locator('button[data-testid="繼續"]').click()
                    page.wait_for_timeout(5000)
                    
                    # 2. 組合目標網址並前往
                    target_url = (
                        f"https://merchant.shoalter.com/zh/order-management/orders/toship"
                        f"?bu=HKTV&deliveryType=STANDARD_DELIVERY&productReadyMethod=STANDARD_DELIVERY_ALL"
                        f"&searchType=ORDER_ID&storefrontCodes=H0956004%2CH0956006%2CH0956007%2CH0956008%2CH0956010%2CH0956012"
                        f"&dateType=PICK_UP_DATE&startDate={target_date_str}&endDate={target_date_str}"
                        f"&pageSize=20&pageNumber=1&sortColumn=orderDate&waybillStatuses="
                    )
                    page.goto(target_url)
                    page.wait_for_timeout(5000) 
                    
                    # 3. 點擊商戶8小時送貨 (只需點一次)
                    try:
                        eight_hour_tab = page.get_by_text("商戶8小時送貨").first
                        eight_hour_tab.click(force=True)
                        page.wait_for_timeout(3000)
                        st.write("✅ 已切換至「商戶8小時送貨」")
                    except Exception:
                        pass
                    
                    # 4. 開始輪流抓取 4 個狀態
                    statuses = [("CONFIRMED", "已建立"), ("ACKNOWLEDGED", "已確認"), ("PACKED", "已包裝"), ("PICKED", "已出貨")]
                    date_data = {"date": target_date_str}
                    
                    for status_val, status_name in statuses:
                        st.write(f"🔍 正在過濾並抓取：**{status_name}** ...")
                        
                        # 展開選單
                        page.locator('div.ant-select-selector:has-text("運單狀態")').click(force=True)
                        page.wait_for_timeout(1000)
                        
                        # 嘗試點擊清除全部
                        try:
                            page.locator('button[data-testid="清除全部"]').click(timeout=1000, force=True)
                            page.wait_for_timeout(500)
                        except:
                            pass
                        
                        # 🚀 終極防呆：手動把「不是我們要的狀態」通通取消打勾！
                        for other_val, _ in statuses:
                            if other_val != status_val:
                                try:
                                    page.locator(f'input[value="{other_val}"]').uncheck(force=True)
                                except:
                                    pass
                        
                        # 勾選目標狀態
                        page.locator(f'input[value="{status_val}"]').check(force=True) 
                        page.wait_for_timeout(800)
                        
                        # 點擊套用
                        page.locator('button[data-testid="套用"]').click(force=True)
                        
                        # 🛑 核心關鍵：等待 6 秒讓 API 回傳並更新畫面數字
                        page.wait_for_timeout(6000) 
                        
                        # 抓取數字
                        try:
                            result_text = page.locator('span:has-text("結果")').last.inner_text(timeout=3000)
                            count = extract_total_count(result_text)
                            date_data[status_val] = count
                            st.write(f"👉 {status_name} 抓取成功： **{count}** 筆")
                        except Exception as e:
                            # 如果數字是 0，找不到「結果」就會跳到這裡
                            date_data[status_val] = "0"
                            st.write(f"👉 {status_name} 抓取結果為： **0** 筆 (無資料)")
                            
                    browser.close()
                    status.update(label="🎉 抓取任務完美結束！", state="complete", expanded=False)
                    
            except Exception as e:
                status.update(label="❌ 任務發生錯誤", state="error", expanded=True)
                st.error(f"錯誤詳情：{e}")
                date_data = {}

        # 5. 顯示漂亮的結果面板
        if date_data:
            st.markdown("---")
            st.subheader(f"📦 機器人回報的測試結果 ({date_data.get('date')})")
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("已建立 (CONFIRMED)", date_data.get('CONFIRMED', '--'))
            with col2: st.metric("已確認 (ACKNOWLEDGED)", date_data.get('ACKNOWLEDGED', '--'))
            with col3: st.metric("已包裝 (PACKED)", date_data.get('PACKED', '--'))
            with col4: st.metric("已出貨 (PICKED)", date_data.get('PICKED', '--'))
