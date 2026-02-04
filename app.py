import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="台股/美股/期貨全方位掃描", page_icon="📈", layout="wide")

# --- 2. 側邊欄：即時盤勢資訊 ---
st.sidebar.header("🌍 全球盤勢即時監控")

def get_market_data():
    # 定義要抓取的全球指數
    indices = {
        "^IXIC": "納斯達克 (Nasdaq)",
        "^SOX": "費半指數 (SOX)",
        "^DJI": "道瓊工業 (DJI)",
        "WTX&F": "台指期 (近月)" # Yahoo Finance 的台指期代碼
    }
    
    for symbol, name in indices.items():
        try:
            data = yf.Ticker(symbol).history(period="2d")
            if not data.empty:
                price = data.iloc[-1]['Close']
                change = data.iloc[-1]['Close'] - data.iloc[-2]['Close']
                pct_change = (change / data.iloc[-2]['Close']) * 100
                
                # 決定顏色 (美股與台股不同，這裡統一用顏色箭頭)
                color = "green" if pct_change >= 0 else "red"
                sign = "+" if pct_change >= 0 else ""
                
                st.sidebar.metric(label=name, value=f"{price:,.0f}", delta=f"{sign}{pct_change:.2f}%")
        except:
            st.sidebar.caption(f"暫時無法取得 {name} 資料")

get_market_data()

st.sidebar.markdown("---")

# --- 3. 側邊欄：進階篩選條件 ---
st.sidebar.header("⚙️ 1. 基礎漲幅與量能")
min_increase = st.sidebar.slider("最低漲幅限制 (%)", 0.0, 10.0, 2.0, 0.5)
vol_multiplier = st.sidebar.slider("成交量放大倍數 (倍)", 1.0, 5.0, 1.2, 0.1)

st.sidebar.markdown("---")
st.sidebar.header("📐 2. 均線過濾 (可多選)")
check_ma5 = st.sidebar.checkbox("站上 5日線 (短線攻擊)", value=True)
check_ma10 = st.sidebar.checkbox("站上 10日線 (雙週)", value=False)
check_ma20 = st.sidebar.checkbox("站上 20日線 (月線)", value=True)
check_ma60 = st.sidebar.checkbox("站上 60日線 (季線)", value=True)

# --- 4. 主畫面內容 ---
st.title("📈 台股全方位偵測器 (美股/期貨同步版)")
st.write(f"數據分析日期：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- 5. 穩定版：內建 100 檔熱門股票清單 ---
@st.cache_data
def get_tw_stock_list():
    top_stocks = [
        # --- 核心權值 & 金融 ---
        {"代號": "2330", "名稱": "台積電"}, {"代號": "2317", "名稱": "鴻海"}, {"代號": "2454", "名稱": "聯發科"}, 
        {"代號": "2308", "名稱": "台達電"}, {"代號": "2303", "名稱": "聯電"}, {"代號": "2881", "名稱": "富邦金"}, 
        {"代號": "2882", "名稱": "國泰金"}, {"代號": "2891", "名稱": "中信金"}, {"代號": "2886", "名稱": "兆豐金"}, 
        # --- AI 相關 ---
        {"代號": "2382", "名稱": "廣達"}, {"代號": "3231", "名稱": "緯創"}, {"代號": "6669", "名稱": "緯穎"}, 
        {"代號": "2376", "名稱": "技嘉"}, {"代號": "3017", "名稱": "奇鋐"}, {"代號": "3324", "名稱": "雙鴻"}, 
        {"代號": "3661", "名稱": "世芯-KY"}, {"代號": "3443", "名稱": "創意"}, {"代號": "3035", "名稱": "智原"},
        {"代號": "2383", "名稱": "台光電"}, {"代號": "6274", "名稱": "台燿"}, {"代號": "3037", "名稱": "欣興"},
        # --- 低軌衛星 & 網通 ---
        {"代號": "3491", "名稱": "昇達科"}, {"代號": "6285", "名稱": "啟碁"}, {"代號": "2313", "名稱": "華通"}, 
        {"代號": "2345", "名稱": "智邦"}, {"代號": "3163", "名稱": "波若威"}, {"代號": "3363", "名稱": "上詮"},
        # --- 半導體 & IC 設計 ---
        {"代號": "3006", "名稱": "晶豪科"}, {"代號": "8150", "名稱": "南茂"}, {"代號": "2379", "名稱": "瑞昱"}, 
        {"代號": "3034", "名稱": "聯詠"}, {"代號": "5269", "名稱": "祥碩"}, {"代號": "6415", "名稱": "矽力-KY"},
        # --- 航運 & 重電 ---
        {"代號": "2603", "名稱": "長榮"}, {"代號": "2609", "名稱": "陽明"}, {"代號": "1513", "名稱": "中興電"}, 
        {"代號": "1519", "名稱": "華城"}, {"代號": "1503", "名稱": "士電"}
        # (清單縮減為精華版以加速，可依需求再補齊至 100 檔)
    ]
    return pd.DataFrame(top_stocks)

# --- 6. 執行掃描邏輯 ---
if st.button("🚀 開始全市場掃描", type="primary"):
    stock_df = get_tw_stock_list()
    st.info(f"✅ 已載入 {len(stock_df)} 檔指標股，開始掃描...")
    
    results = []
    progress_bar = st.progress(0)
    
    for i, row in stock_df.iterrows():
        try:
            code, name = row['代號'], row['名稱']
            data = yf.Ticker(code + ".TW").history(period="3mo")
            if len(data) >= 60:
                today = data.iloc[-1]
                yesterday = data.iloc[-2]
                price = today['Close']
                change_pct = (price - yesterday['Close']) / yesterday['Close'] * 100
                vol_ratio = today['Volume'] / data['Volume'].tail(5).mean()
                
                ma5, ma10, ma20, ma60 = data['Close'].tail(5).mean(), data['Close'].tail(10).mean(), data['Close'].tail(20).mean(), data['Close'].tail(60).mean()
                
                pass_ma = True
                if check_ma5 and price < ma5: pass_ma = False
                if check_ma10 and price < ma10: pass_ma = False
                if check_ma20 and price < ma20: pass_ma = False
                if check_ma60 and price < ma60: pass_ma = False

                if change_pct >= min_increase and vol_ratio >= vol_multiplier and pass_ma:
                    results.append({"代號": code, "名稱": name, "價錢": f"{price:.1f}", "漲幅": f"{change_pct:.1f}%", "量比": f"{vol_ratio:.1f}倍"})
        except: continue
        progress_bar.progress((i + 1) / len(stock_df))

    if results:
        st.success(f"發現 {len(results)} 檔符合條件標的！")
        st.table(pd.DataFrame(results))
    else:
        st.warning("目前無符合標的。")
