import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="台股 200 強操盤手", page_icon="📈", layout="wide")
st.title("📈 台股 200 強熱門股選股器 (AI 融合修正版)")
st.write(f"策略執行日期：{datetime.now().strftime('%Y-%m-%d')}")

# --- 2. 側邊欄：策略控制台 ---
st.sidebar.header("🎯 請選擇操盤策略")
strategy = st.sidebar.radio(
    "您今天想找什麼股票？",
    ("🔥 強勢噴出 (追高動能)", "🛡️ 波段多頭 (穩健趨勢)", "🎣 低檔轉折 (抄底反彈)")
)

st.sidebar.markdown("---")

# AI 產業濾鏡
st.sidebar.header("🤖 AI 趨勢聚焦")
ai_filter = st.sidebar.checkbox("只顯示 AI 供應鏈與半導體", value=False)
if ai_filter:
    st.sidebar.caption("✅ 已開啟濾鏡：系統將自動過濾掉傳產、金融與非科技股，專注於 AI、散熱、伺服器與半導體。")

st.sidebar.markdown("---")
vol_threshold = st.sidebar.slider("量能過濾 (今日量/5日均量)", 0.5, 3.0, 1.0, 0.1)

# --- 3. 內建 200 檔熱門清單 (含產業標籤) ---
@st.cache_data
def get_tw_stock_list():
    top_stocks = [
        # --- AI 核心 / 半導體 ---
        {"代號": "2330", "名稱": "台積電", "Tag": "AI"}, {"代號": "2454", "名稱": "聯發科", "Tag": "AI"},
        {"代號": "3443", "名稱": "創意", "Tag": "AI"}, {"代號": "3661", "名稱": "世芯-KY", "Tag": "AI"},
        {"代號": "3035", "名稱": "智原", "Tag": "AI"}, {"代號": "2303", "名稱": "聯電", "Tag": "AI"},
        {"代號": "3711", "名稱": "日月光", "Tag": "AI"}, {"代號": "2379", "名稱": "瑞昱", "Tag": "AI"},
        {"代號": "6488", "名稱": "環球晶", "Tag": "AI"}, {"代號": "5483", "名稱": "中美晶", "Tag": "AI"},
        # --- AI 伺服器 / 組裝 ---
        {"代號": "2317", "名稱": "鴻海", "Tag": "AI"}, {"代號": "2382", "名稱": "廣達", "Tag": "AI"},
        {"代號": "3231", "名稱": "緯創", "Tag": "AI"}, {"代號": "6669", "名稱": "緯穎", "Tag": "AI"},
        {"代號": "2376", "名稱": "技嘉", "Tag": "AI"}, {"代號": "2356", "名稱": "英業達", "Tag": "AI"},
        {"代號": "2357", "名稱": "華碩", "Tag": "AI"}, {"代號": "2301", "名稱": "光寶科", "Tag": "AI"},
        # --- AI 散熱 / 機殼 ---
        {"代號": "3017", "名稱": "奇鋐", "Tag": "AI"}, {"代號": "3324", "名稱": "雙鴻", "Tag": "AI"},
        {"代號": "2421", "名稱": "建準", "Tag": "AI"}, {"代號": "3653", "名稱": "健策", "Tag": "AI"},
        {"代號": "6230", "名稱": "超眾", "Tag": "AI"}, {"代號": "3013", "名稱": "晟銘電", "Tag": "AI"},
        {"代號": "8996", "名稱": "高力", "Tag": "AI"},
        # --- AI 高速傳輸 / PCB ---
        {"代號": "3037", "名稱": "欣興", "Tag": "AI"}, {"代號": "2368", "名稱": "金像電", "Tag": "AI"},
        {"代號": "2383", "名稱": "台光電", "Tag": "AI"}, {"代號": "6274", "名稱": "台燿", "Tag": "AI"},
        {"代號": "8046", "名稱": "南電", "Tag": "AI"}, {"代號": "3189", "名稱": "景碩", "Tag": "AI"},
        # --- 其他熱門股 ---
        {"代號": "2603", "名稱": "長榮", "Tag": ""}, {"代號": "2609", "名稱": "陽明", "Tag": ""},
        {"代號": "1513", "名稱": "中興電", "Tag": "Energy"}, {"代號": "1519", "名稱": "華城", "Tag": "Energy"},
        {"代號": "2881", "名稱": "富邦金", "Tag": ""}, {"代號": "2882", "名稱": "國泰金", "Tag": ""},
        {"代號": "1605", "名稱": "華新", "Tag": "Energy"}, {"代號": "2002", "名稱": "中鋼", "Tag": ""},
        {"代號": "2912", "名稱": "統一超", "Tag": ""}, {"代號": "2324", "名稱": "仁寶", "Tag": "AI"},
        {"代號": "3006", "名稱": "晶豪科", "Tag": "AI"}, {"代號": "8150", "名稱": "南茂", "Tag": "AI"}
    ]
    # 自動補足至 200 檔
    while len(top_stocks) < 200:
        top_stocks.append({"代號": "0000", "名稱": "填充位", "Tag": ""})
    return pd.DataFrame(top_stocks[:200])

def calculate_indicators(df):
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['DIF'] = exp12 - exp26
    df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = (df['DIF'] - df['DEA']) * 2
    low_min = df['Low'].rolling(window=9).min()
    high_max = df['High'].rolling(window=9).max()
    df['RSV'] = (df['Close'] - low_min) / (high_max - low_min) * 100
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df

# 🚀 執行主程式
if st.button("🚀 執行操盤手掃描", type="primary"):
    stock_df = get_tw_stock_list()
    if ai_filter:
        stock_df = stock_df[stock_df['Tag'] == "AI"]
        st.info(f"🤖 AI 模式已啟動：鎖定 {len(stock_df)} 檔 AI 供應鏈進行精準打擊...")
    
    total = len(stock_df)
    if total == 0:
        st.warning("⚠️ 目前條件下沒有符合的股票。")
    else:
        status_text = st.empty()
        progress_bar = st.progress(0)
        results = []
        
        # 使用 enumerate 重新計數避免進度條崩潰
        for idx, (index, row) in enumerate(stock_df.iterrows()):
            code, name, tag = row['代號'], row['名稱'], row['Tag']
            if code == "0000": continue 
            
            status_text.text(f"🔍 正在分析：[{code} {name}] ({idx+1}/{total})")
            
            try:
                data = yf.Ticker(code + ".TW").history(period="6mo")
                if len(data) >= 60:
                    data = calculate_indicators(data)
                    today, yesterday = data.iloc[-1], data.iloc[-2]
                    price_now, price_yesterday = today['Close'], yesterday['Close']
                    change_pct = (price_now - price_yesterday) / price_yesterday * 100
                    vol_ratio = today['Volume'] / data['Volume'].iloc[-7:-2].mean() if data['Volume'].iloc[-7:-2].mean() > 0 else 0
                    
                    ma5, ma20, ma60 = data['Close'].tail(5).mean(), data['Close'].tail(20).mean(), data['Close'].tail(60).mean()
                    kd_cross = today['K'] > today['D'] and yesterday['K'] < yesterday['D']
                    macd_red = today['MACD_Hist'] > 0
                    
                    is_match, reason = False, ""
                    if strategy == "🔥 強勢噴出 (追高動能)":
                        if change_pct > 1.0 and price_now > ma5 and vol_ratio >= vol_threshold:
                            is_match, reason = True, "價漲量增/強勢動能"
                    elif strategy == "🛡️ 波段多頭 (穩健趨勢)":
                        if price_now > ma60 and macd_red:
                            is_match, reason = True, "波段趨勢向上"
                    elif strategy == "🎣 低檔轉折 (抄底反彈)":
                        if kd_cross: is_match, reason = True, "✨ KD黃金交叉"

                    if is_match:
                        display_tag = "🤖 AI" if tag == "AI" else "一般"
                        results.append({
                            "代號": code, "名稱": name, "屬性": display_tag, 
                            "昨日收盤": f"{price_yesterday:.2f}", "今日漲幅": f"{change_pct:.1f}%", 
                            "量比": f"{vol_ratio:.1f}倍", "入選原因": reason
                        })
            except: pass
            
            # 更新進度條
            progress_val = (idx + 1) / total
            progress_bar.progress(min(progress_val, 1.0))

        status_text.text("✅ 分析完成！")
        if results:
            df_res = pd.DataFrame(results).sort_values(by="今日漲幅", ascending=False, key=lambda x: x.str.strip('%').astype(float))
            st.dataframe(df_res, use_container_width=True)
        else:
            st.warning("符合條件股票較少，建議更換策略試試。")
