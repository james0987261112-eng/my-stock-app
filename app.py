import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="我的台股起漲偵測器", page_icon="📈")
st.title("🇹🇼 台股全市場起漲偵測器")
st.write(f"今天是：{datetime.now().strftime('%Y-%m-%d')}")

# --- 2. 自動取得台股清單的功能 (含偽裝瀏覽器) ---
@st.cache_data
def get_tw_stock_list():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'big5'
        # 解析網頁表格
        res = pd.read_html(response.text)[0]
        res.columns = res.iloc[0]
        res = res.iloc[1:]
        # 過濾出 4 碼的股票代號
        res['代號'] = res['有價證券代號及名稱'].str.split('　').str[0]
        list_tw = res[res['代號'].str.len() == 4]['代號'].tolist()
        return list_tw
    except Exception as e:
        # 如果失敗，回傳一組基本的觀察清單 (包含您關注的股票)
        return ["3006", "2330", "2317", "2454", "3231", "2603", "5269", "6415", "8150"]

# --- 3. 執行掃描邏輯 ---
if st.button("🚀 開始全市場掃描 (每日一次)", type="primary"):
    st.write("🔍 正在抓取全市場資料，請耐心稍候...")
    
    all_stocks = get_tw_stock_list()
    # 為了執行速度與穩定性，我們優先掃描前 200 檔標的
    # 您可以把 [:200] 刪掉來掃描全市場，但會跑非常久
    scan_list = all_stocks[:200] 
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, code in enumerate(scan_list):
        try:
            ticker_code = code + ".TW"
            # 抓取最近 10 天資料
            data = yf.Ticker(ticker_code).history(period="10d")
            
            if len(data) >= 2:
                today = data.iloc[-1]
                yesterday = data.iloc[-2]
                
                # 起漲判斷條件
                price = today['Close']
                change_pct = (price - yesterday['Close']) / yesterday['Close'] * 100
                vol_ratio = today['Volume'] / yesterday['Volume'] if yesterday['Volume'] > 0 else 0
                
                # 條件：漲幅 > 3% 且 成交量是昨天 1.5 倍以上
                if change_pct > 3 and vol_ratio > 1.5:
                    results.append({
                        "股票代號": code,
                        "目前股價": f"{price:.2f}",
                        "今日漲幅": f"{change_pct:.1f}%",
                        "成交量增": f"{vol_ratio:.1f}倍",
                        "狀態": "🔥 訊號觸發"
                    })
        except:
            continue
        
        # 更新進度條
        progress_bar.progress((i + 1) / len(scan_list))
        status_text.text(f"掃描進度: {i+1}/{len(scan_list)} (正在分析 {code})")

    # --- 4. 顯示結果 ---
    if results:
        st.success(f"掃描完畢！共發現 {len(results)} 檔符合條件標的")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.warning("今日掃描範圍內暫無符合「爆量起漲」條件的股票。")

st.markdown("---")
st.caption("資料來源：證交所、Yahoo Finance | 免責聲明：本工具僅供參考，不構成投資建議。")
