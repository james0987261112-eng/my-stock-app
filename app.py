import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="台股優質起漲掃描", page_icon="💎")
st.title("💎 台股優質起漲偵測器 (Pro版)")
st.write(f"今天是：{datetime.now().strftime('%Y-%m-%d')}")

# --- 2. 側邊欄：讓您用手機就能調整條件 ---
st.sidebar.header("⚙️ 篩選條件設定")
st.sidebar.write("調整下方滑桿，即時改變策略：")

min_increase = st.sidebar.slider("最低漲幅限制 (%)", 0.0, 10.0, 3.0, 0.5)
vol_multiplier = st.sidebar.slider("成交量放大倍數 (倍)", 1.0, 5.0, 1.5, 0.1)
check_ma60 = st.sidebar.checkbox("必須站上季線 (60MA - 生命線)", value=True, help="勾選後，只會顯示長期趨勢向上的股票，安全性較高。")

st.sidebar.markdown("---")
st.sidebar.info("💡 **小撇步**：\n勾選「站上季線」可以過濾掉很多只是反彈的爛股票，找出真正的優質股。")

# --- 3. 自動取得台股清單 ---
@st.cache_data
def get_tw_stock_list():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'big5'
        res = pd.read_html(response.text)[0]
        res.columns = res.iloc[0]
        res = res.iloc[1:]
        res['代號'] = res['有價證券代號及名稱'].str.split('　').str[0]
        res['名稱'] = res['有價證券代號及名稱'].str.split('　').str[1]
        
        # 只選股票代號為 4 碼的
        stock_data = res[res['代號'].str.len() == 4][['代號', '名稱']]
        return stock_data
    except Exception as e:
        # 備用清單
        return pd.DataFrame({
            '代號': ["2330", "2317", "2454", "3006", "3231", "2603", "5269", "6415", "8150"],
            '名稱': ["台積電", "鴻海", "聯發科", "晶豪科", "緯創", "長榮", "祥碩", "矽力", "南茂"]
        })

# --- 4. 執行掃描邏輯 ---
if st.button("🚀 開始掃描優質起漲股", type="primary"):
    st.write("🔍 AI 正在分析均線與成交量，請稍候...")
    
    stock_df = get_tw_stock_list()
    # 為了速度，我們先掃描前 200 檔熱門股
    scan_list = stock_df.head(200)
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, row in scan_list.iterrows():
        code = row['代號']
        name = row['名稱']
        
        try:
            ticker_code = code + ".TW"
            # 抓取 3 個月資料 (因為要計算 60MA 季線)
            data = yf.Ticker(ticker_code).history(period="3mo")
            
            if len(data) >= 60: # 確保資料夠長
                today = data.iloc[-1]
                yesterday = data.iloc[-2]
                
                # --- 計算技術指標 ---
                price = today['Close']
                # 漲幅
                change_pct = (price - yesterday['Close']) / yesterday['Close'] * 100
                
                # 均線 (5日, 20日, 60日)
                ma5 = data['Close'].tail(5).mean()
                ma20 = data['Close'].tail(20).mean()
                ma60 = data['Close'].tail(60).mean()
                
                # 成交量 (與過去 5 天均量相比，比較客觀)
                vol_ma5 = data['Volume'].tail(5).mean()
                vol_ratio = today['Volume'] / vol_ma5 if vol_ma5 > 0 else 0
                
                # --- 篩選條件判斷 ---
                # 1. 基礎條件：漲幅達標 + 爆量
                cond_basic = change_pct >= min_increase and vol_ratio >= vol_multiplier
                
                # 2. 優質條件：站上季線 (如果使用者有勾選)
                cond_quality = True
                if check_ma60:
                    cond_quality = price > ma60
                
                # 3. 趨勢條件：均線多頭排列 (股價 > 月線)
                cond_trend = price > ma20

                if cond_basic and cond_quality and cond_trend:
                    results.append({
                        "代號": code,
                        "名稱": name,
                        "股價": f"{price:.2f}",
                        "漲幅": f"🔥 {change_pct:.1f}%",
                        "量能倍數": f"{vol_ratio:.1f}倍",
                        "季線狀態": "✅ 站上" if price > ma60 else "⚠️ 跌破"
                    })
        except:
            continue
        
        # 更新進度
        current_progress = (i + 1) / len(scan_list)
        progress_bar.progress(current_progress)
        status_text.text(f"掃描進度: {int(current_progress*100)}% - 正在分析 {name} ({code})")

    # --- 5. 顯示結果 ---
    status_text.empty() # 清空進度文字
    if results:
        st.success(f"掃描完畢！共發現 {len(results)} 檔優質潛力股")
        # 將資料轉為表格並顯示
        df_results = pd.DataFrame(results)
        st.dataframe(df_results, use_container_width=True)
        
        st.markdown("### 📊 結果分析")
        st.write("這些股票不僅今日**爆量起漲**，且股價站穩**月線**之上，屬於強勢格局。")
    else:
        st.warning(f"目前條件下（漲幅>{min_increase}%、量增>{vol_multiplier}倍），沒有發現符合的股票。")
        st.info("💡 試著在左側選單把條件放寬一點看看？")

st.markdown("---")
st.caption("資料來源：證交所、Yahoo Finance | 本工具為量化分析輔助，不構成投資建議")
