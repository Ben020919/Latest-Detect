import streamlit as st
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import re
import os

# 確保 Streamlit 雲端有安裝瀏覽器
os.system("playwright install chromium")

st.set_page_config(page_title="HKTVmall 訂單深度核對", layout="wide")
st.title("🎯 數據對齊測試：直連 100 筆分頁網址")

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

# 固定測試日期為 21 號
target_date_str = "2026-02-21"

if st.button(f"🚀 開始抓取 {target_date_str} 的訂單詳情"):
    if not USERNAME or not PASSWORD:
        st.warning("請先設定 Secrets！")
    else:
        with st.status(f"⚡ 正在掃描 {target_date_str} 的數據與單號...", expanded=True) as status:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(viewport={'width': 1920, 'height': 2000}) # 加高視窗以便抓取更多列表
                    page = context.new_page()
                    
                    # --- 1. 登入 ---
                    st.write("⏳ 正在登入 HKTVmall...")
                    page.goto("https://merchant.shoalter.com/login")
                    page.locator('#account').fill(USERNAME)
                    page.locator('#password').fill(PASSWORD)
                    page.locator('button[data-testid="繼續"]').click()
                    page.wait_for_timeout(5000)
                    
                    statuses = [("CONFIRMED", "已建立"), ("ACKNOWLEDGED", "已確認"), ("PACKED", "已包裝"), ("PICKED", "已出貨")]
                    all_results = {}
                    
                    for status_val, status_name in statuses:
                        st.write(f"🔍 正在檢查 **{status_name}** ...")
                        
                        # 這是你指定的 100 筆分頁網址
                        target_url = (
                            f"https://merchant.shoalter.com/zh/order-management/orders/toship"
                            f"?bu=HKTV&deliveryType=STANDARD_DELIVERY&productReadyMethod=SAME_DAY_IN_HUB"
                            f"&searchType=ORDER_ID&storefrontCodes=H0956004%2CH0956006%2CH0956007%2CH0956008%2CH0956010%2CH0956012"
                            f"&dateType=PICK_UP_DATE&startDate={target_date_str}&endDate={target_date_str}"
                            f"&waybillStatuses={status_val}&pageSize=100&pageNumber=1&sortColumn=orderDate"
                        )
                        
                        page.goto(target_url)
                        page.wait_for_timeout(8000) # 給予充足時間加載 100 筆數據
                        
                        # 1. 抓取統計文字
                        try:
                            result_text = page.locator('span:has-text("結果")').last.inner_text(timeout=5000)
                            count = extract_total_count(result_text)
                        except:
                            result_text = "未找到結果文字"
                            count = "0"
                            
                        # 2. 抓取頁面上的訂單編號 (單號通常是 10-12 位數字)
                        # 嘗試抓取表格中所有可能的訂單號碼位置
                        order_ids = []
                        try:
                            # HKTVmall 單號通常在特定的 cell 或 button 裡
                            potential_ids = page.locator('td, button').all_inner_texts()
                            # 過濾出純數字且長度大於 9 的字串
                            order_ids = [str(x).strip() for x in potential_ids if str(x).strip().isdigit() and len(str(x).strip()) >= 10]
                            order_ids = sorted(list(set(order_ids))) # 去重
                        except:
                            pass
                            
                        all_results[status_name] = {
                            "count": count,
                            "raw_text": result_text,
                            "order_ids": order_ids,
                            "screenshot": page.screenshot()
                        }
                        
                    browser.close()
                    status.update(label="🎉 掃描完成！", state="complete", expanded=False)
                    
            except Exception as e:
                status.update(label="❌ 任務發生錯誤", state="error", expanded=True)
                st.error(f"錯誤詳情：{e}")
                all_results = {}

        # --- 顯示結果與核對清單 ---
        if all_results:
            st.markdown("---")
            for name, res in all_results.items():
                with st.expander(f"📊 {name} 詳情 (總數: {res['count']})", expanded=(res['count'] != "0")):
                    st.write(f"**網頁原始文字:** `{res['raw_text']}`")
                    st.write(f"**本頁偵測到的訂單單號 (前 20 筆):**")
                    if res['order_ids']:
                        st.write(", ".join(res['order_ids'][:20]))
                    else:
                        st.write("未能自動提取單號")
                    
                    st.image(res['screenshot'], caption=f"{name} 頁面截圖")
