import streamlit as st
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import re
import os

os.system("playwright install chromium")

st.set_page_config(page_title="HKTVmall 除錯診斷", layout="wide")
st.title("🔎 終極診斷模式：追蹤 21 號「已建立」 (JS 強制點擊版)")

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

if st.button("🐛 開始單步診斷 (測 21 號的 CONFIRMED)"):
    if not USERNAME or not PASSWORD:
        st.warning("請先設定 Secrets！")
    else:
        now = datetime.utcnow() + timedelta(hours=8)
        target_date_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        
        with st.status(f"🕵️ 偵探模式啟動，正在抓取 {target_date_str} 的資料...", expanded=True) as status:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
                    page = context.new_page()
                    
                    # --- 1. 登入 ---
                    page.goto("https://merchant.shoalter.com/login")
                    page.locator('#account').fill(USERNAME)
                    page.locator('#password').fill(PASSWORD)
                    page.locator('button[data-testid="繼續"]').click()
                    page.wait_for_timeout(5000)
                    
                    # --- 2. 導航 ---
                    target_url = (
                        f"https://merchant.shoalter.com/zh/order-management/orders/toship"
                        f"?bu=HKTV&deliveryType=STANDARD_DELIVERY&productReadyMethod=SAME_DAY_IN_HUB"
                        f"&searchType=ORDER_ID&storefrontCodes=H0956004%2CH0956006%2CH0956007%2CH0956008%2CH0956010%2CH0956012"
                        f"&dateType=PICK_UP_DATE&startDate={target_date_str}&endDate={target_date_str}"
                        f"&pageSize=20&pageNumber=1&sortColumn=orderDate&waybillStatuses="
                    )
                    page.goto(target_url)
                    page.wait_for_timeout(6000)
                    
                    st.markdown(f"### 📸 {target_date_str} 動作監視紀錄")
                    st.image(page.screenshot(), caption="動作 A：剛進入 21 號 8小時送貨頁面", use_container_width=True)
                    
                    # --- 3. 展開選單 ---
                    try:
                        page.locator('div.ant-select-selector:has-text("運單狀態")').click(force=True)
                        page.wait_for_timeout(2000)
                        st.image(page.screenshot(), caption="動作 B：已點擊「運單狀態」展開選單", use_container_width=True)
                    except Exception as e:
                        st.error(f"打開選單失敗：{e}")
                    
                    # --- 4. 點擊清除全部 ---
                    try:
                        page.locator('button[data-testid="清除全部"]').click(timeout=2000, force=True)
                        page.wait_for_timeout(2000)
                        st.image(page.screenshot(), caption="動作 C：已點擊「清除全部」", use_container_width=True)
                    except Exception as e:
                        st.error(f"點擊清除全部失敗：{e}")
                    
                    # --- 5. 🎯 終極修正：用 JavaScript 強制觸發底層 input 打勾 ---
                    try:
                        # 這行指令會直接命令瀏覽器核心，對 value="CONFIRMED" 的元素執行 click()，無視所有障礙物！
                        page.locator('input[value="CONFIRMED"]').evaluate("node => node.click()")
                        page.wait_for_timeout(2000)
                        st.image(page.screenshot(), caption="動作 D：JS 強制打勾「CONFIRMED」 (請確認是否出現藍勾勾)", use_container_width=True)
                    except Exception as e:
                        st.error(f"JS 強制打勾 失敗：{e}")
                        
                    # --- 6. 點擊套用 ---
                    try:
                        page.locator('button[data-testid="套用"]').click(force=True)
                        page.wait_for_timeout(6000) # 等待 6 秒讓 API 回傳
                        st.image(page.screenshot(), caption="動作 E：點擊「套用」後的最終結果", use_container_width=True)
                    except Exception as e:
                        st.error(f"點擊套用失敗：{e}")
                    
                    # --- 7. 最終抓取 ---
                    try:
                        result_text = page.locator('span:has-text("結果")').last.inner_text(timeout=3000)
                        count = extract_total_count(result_text)
                        st.success(f"🎯 最終機器人抓到的數字為： **{count}**")
                    except Exception:
                        st.error("找不到結果標籤！")

                    browser.close()
                    status.update(label="診斷完畢！請檢視上方的截圖。", state="complete", expanded=False)
                    
            except Exception as e:
                status.update(label="❌ 任務發生錯誤", state="error", expanded=True)
                st.error(f"錯誤詳情：{e}")
