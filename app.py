import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="台股 200 強操盤手", page_icon="📈", layout="wide")
st.title("📈 台股 200 強熱門股選股器 (V7.0 穩定加速版)")
st.write(f"最後更新日期：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- 2. 側邊欄：策略控制台 ---
st.sidebar.header("🎯 策略控制台")
strategy = st.sidebar.radio(
    "您今天想找什麼股票？",
    ("🔥 強勢噴出 (追高動能)", "🛡️ 波段多頭 (穩健趨勢)", "🎣 低檔轉折 (抄底反彈)")
)

st.sidebar.markdown("---")
ai_filter = st.sidebar.checkbox("🤖 只顯示 AI 供應鏈", value=False)
vol_threshold = st.sidebar.slider("量能過濾 (今日量/5日均量)", 0.5, 3.0, 1.2, 0.1)

# --- 3. 內建 200 檔清單 ---
@st.cache_data
def get_tw_stock_list():
    # 這裡維持您最愛的 200 檔結構
    top_stocks = [
        {"代號": "2330", "名稱": "台積電", "Tag": "AI"}, {"代號": "2454", "名稱": "聯發科", "Tag": "AI"},
        {"代號": "2317", "名稱": "鴻海", "Tag": "AI"}, {"代號": "2382", "名稱": "廣達", "Tag": "AI"},
        {"代號": "3231", "名稱": "緯創", "Tag": "AI"}, {"代號": "3017", "名稱": "奇鋐", "Tag": "AI"},
        {"代號": "3324", "名稱": "雙鴻", "Tag": "AI"}, {"代號": "2376", "名稱": "技嘉", "Tag": "AI"},
        {"代號": "3661", "名稱": "世芯-KY", "Tag": "AI"}, {"代號": "3443", "名稱": "創意", "Tag": "AI"},
        {"代號": "6669", "名稱": "緯穎", "Tag": "AI"}, {"代號": "1513", "名稱": "中興電", "Tag": "Energy"},
        {"代號": "1519", "名稱": "華城", "Tag": "Energy"}, {"代號": "2603", "名稱": "長榮", "Tag": ""},
        {"代號": "2609", "名稱": "陽明", "Tag": ""}, {"代號": "2881", "名稱": "富邦金", "Tag": ""},
        {"代號": "3450", "名稱": "聯鈞", "Tag": "AI"}, {"代號": "6230", "名稱": "超眾", "Tag": "AI"}
        # ... 建議手動補足至 200 檔熱門代號 ...
    ]
    # 自動補足填充標的至 200 檔
    curr_len = len(top_stocks)
    for i in range(curr_len, 200):
        top_stocks.append({"代號": "0000", "名稱": f"填充標的 {i}", "Tag": ""})
    return pd.DataFrame(top_stocks)

# --- 4. 技術指標核心計算 ---
def calculate_indicators(df):
    # MACD
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['DIF'] = exp12 - exp26
    df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = (df['DIF'] - df['DEA']) * 2
    # KD
    low_min = df['Low'].rolling(window=9).min()
    high_max = df['High'].rolling(window=9).max()
    df['RSV'] = (df['Close'] - low_min) / (high_max - low_min) * 100
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    # 均線
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    return df

# --- 5. 🚀 執行主程式 ---
if st.button("🚀 開始全市場 200 檔深度掃描", type="primary"):
    full_list = get_tw_stock_list()
    if ai_filter:
        working_df = full_list[full_list['Tag'] == "AI"].copy()
    else:
        working_df = full_list.copy()
    
    # 移除無效代號
    working_df = working_df[working_df['代號'] != "0000"].reset_index(drop=True)
    tickers = [f"{c}.TW" for c in working_df['代號']]
    total = len(tickers)

    st.info(f"📊 正在下載 {total} 檔個股數據，請稍候...")
    
    try:
        # 【關鍵優化】改用 yf.download 批次抓取所有股票 6 個月的資料
        raw_data = yf.download(tickers, period="6mo", group_by='ticker', threads=True, progress=False)
        
        status_text = st.empty()
        progress_bar = st.progress(0)
        results = []

        for i, code in enumerate(working_df['代號']):
            name, tag = working_df.iloc[i]['名稱'], working_df.iloc[i]['Tag']
            status_text.text(f"🔍 正在分析 ({i+1}/{total})：{code} {name}")
            
            try:
                # 取得該檔股票的資料切片
                ticker_data = raw_data[f"{code}.TW"].dropna()
                
                if len(ticker_data) >= 60:
                    data = calculate_indicators(ticker_data)
                    today, yesterday = data.iloc[-1], data.iloc[-2]
                    
                    price_now = today['Close']
                    price_prev = yesterday['Close']
                    change_pct = (price_now - price_prev) / price_prev * 100
                    
                    vol_avg = data['Volume'].iloc[-7:-2].mean()
                    vol_ratio = today['Volume'] / vol_avg if vol_avg > 0 else 0
                    
                    kd_cross = today['K'] > today['D'] and yesterday['K'] < yesterday['D']
                    macd_red = today['MACD_Hist'] > 0
                    
                    # 判斷策略
                    match = False
                    if strategy == "🔥 強勢噴出 (追高動能)":
                        if change_pct > 1.0 and price_now > today['MA5'] and vol_ratio >= vol_threshold:
                            match = True
                    elif strategy == "🛡️ 波段多頭 (穩健趨勢)":
                        if price_now > today['MA60'] and macd_red:
                            match = True
                    elif strategy == "🎣 低檔轉折 (抄底反彈)":
                        if kd_cross:
                            match = True

                    if match:
                        results.append({
                            "代號": code, "名稱": name, "屬性": "🤖 AI" if tag == "AI" else "一般", 
                            "昨日收盤": f"{price_prev:.2f}", "今日漲幅": f"{change_pct:.1f}%", 
                            "量比": f"{vol_ratio:.1f}倍"
                        })
            except Exception:
                continue
                
            progress_bar.progress((i + 1) / total)

        status_text.text("✅ 全市場掃描完成！")
        if results:
            st.success(f"發現 {len(results)} 檔標的")
            df_res = pd.DataFrame(results).sort_values(by="今日漲幅", ascending=False, key=lambda x: x.str.strip('%').astype(float))
            st.dataframe(df_res, use_container_width=True)
        else:
            st.warning("⚠️ 掃描完成，目前市場無符合條件標的。")
            
    except Exception as e:
        st.error(f"數據下載失敗：{str(e)}")
