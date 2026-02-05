import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="台股精選 100 偵測器", page_icon="📈", layout="wide")

# --- 2. 側邊欄：台指期監控 (移除美股) ---
st.sidebar.header("🇹🇼 台股盤勢")
def get_market_data():
    try:
        # 只保留台指期 (WTX&F)，移除納斯達克與費半
        data = yf.Ticker("WTX&F").history(period="2d")
        if len(data) >= 2:
            change = (data.iloc[-1]['Close'] - data.iloc[-2]['Close']) / data.iloc[-2]['Close'] * 100
            st.sidebar.metric("台指期 (近月)", f"{data.iloc[-1]['Close']:,.0f}", f"{change:.2f}%")
    except:
        st.sidebar.caption("盤後資料讀取中...")
get_market_data()

st.sidebar.markdown("---")

# --- 3. 側邊欄：篩選條件 ---
st.sidebar.header("⚙️ 篩選條件")
min_increase = st.sidebar.slider("今日漲幅大於 (%)", 0.0, 10.0, 2.0, 0.5)
vol_multiplier = st.sidebar.slider("成交量放大倍數 (倍)", 1.0, 5.0, 1.2, 0.1)

st.sidebar.markdown("---")
st.sidebar.header("📊 技術指標")
check_ma60 = st.sidebar.checkbox("站上季線 (60MA)", value=True)
check_kd_cross = st.sidebar.checkbox("KD 黃金交叉", value=False)
check_macd_bull = st.sidebar.checkbox("MACD 多頭翻紅", value=False)

# --- 4. 主程式 ---
st.title("📈 台股百大熱門股選股器")
st.write(f"數據日期：{datetime.now().strftime('%Y-%m-%d %H:%M')}")

# 內建 100 檔熱門清單 (已人工校對補齊)
@st.cache_data
def get_tw_stock_list():
    top_stocks = [
        # 1. 半導體與晶圓代工 (20檔)
        {"代號": "2330", "名稱": "台積電"}, {"代號": "2454", "名稱": "聯發科"}, {"代號": "2303", "名稱": "聯電"},
        {"代號": "3711", "名稱": "日月光"}, {"代號": "3034", "名稱": "聯詠"}, {"代號": "2379", "名稱": "瑞昱"},
        {"代號": "3443", "名稱": "創意"}, {"代號": "3661", "名稱": "世芯-KY"}, {"代號": "3035", "名稱": "智原"},
        {"代號": "3006", "名稱": "晶豪科"}, {"代號": "8150", "名稱": "南茂"}, {"代號": "2408", "名稱": "南亞科"},
        {"代號": "2344", "名稱": "華邦電"}, {"代號": "5347", "名稱": "世界"}, {"代號": "6488", "名稱": "環球晶"},
        {"代號": "5483", "名稱": "中美晶"}, {"代號": "6147", "名稱": "頎邦"}, {"代號": "6239", "名稱": "力成"},
        {"代號": "8299", "名稱": "群聯"}, {"代號": "3105", "名稱": "穩懋"},
        
        # 2. AI 伺服器與電腦周邊 (15檔)
        {"代號": "2317", "名稱": "鴻海"}, {"代號": "2382", "名稱": "廣達"}, {"代號": "3231", "名稱": "緯創"},
        {"代號": "6669", "名稱": "緯穎"}, {"代號": "2376", "名稱": "技嘉"}, {"代號": "2356", "名稱": "英業達"},
        {"代號": "2324", "名稱": "仁寶"}, {"代號": "2357", "名稱": "華碩"}, {"代號": "4938", "名稱": "和碩"},
        {"代號": "2353", "名稱": "宏碁"}, {"代號": "3017", "名稱": "奇鋐"}, {"代號": "3324", "名稱": "雙鴻"},
        {"代號": "2421", "名稱": "建準"}, {"代號": "3653", "名稱": "健策"}, {"代號": "6230", "名稱": "超眾"},

        # 3. 網通、PCB 與低軌衛星 (15檔)
        {"代號": "3037", "名稱": "欣興"}, {"代號": "2368", "名稱": "金像電"}, {"代號": "2383", "名稱": "台光電"},
        {"代號": "6274", "名稱": "台燿"}, {"代號": "8046", "名稱": "南電"}, {"代號": "3189", "名稱": "景碩"},
        {"代號": "2313", "名稱": "華通"}, {"代號": "2345", "名稱": "智邦"}, {"代號": "6285", "名稱": "啟碁"},
        {"代號": "5388", "名稱": "中磊"}, {"代號": "3491", "名稱": "昇達科"}, {"代號": "2314", "名稱": "台揚"},
        {"代號": "3163", "名稱": "波若威"}, {"代號": "3363", "名稱": "上詮"}, {"代號": "4979", "名稱": "華星光"},

        # 4. 金融股 (15檔)
        {"代號": "2881", "名稱": "富邦金"}, {"代號": "2882", "名稱": "國泰金"}, {"代號": "2891", "名稱": "中信金"},
        {"代號": "2886", "名稱": "兆豐金"}, {"代號": "2884", "名稱": "玉山金"}, {"代號": "2885", "名稱": "元大金"},
        {"代號": "5880", "名稱": "合庫金"}, {"代號": "2892", "名稱": "第一金"}, {"代號": "2880", "名稱": "華南金"},
        {"代號": "2883", "名稱": "開發金"}, {"代號": "2887", "名稱": "台新金"}, {"代號": "2890", "名稱": "永豐金"},
        {"代號": "5871", "名稱": "中租-KY"}, {"代號": "5876", "名稱": "上海商銀"}, {"代號": "2801", "名稱": "彰銀"},

        # 5. 傳產龍頭 (塑化、水泥、食品、紡織) (12檔)
        {"代號": "1101", "名稱": "台泥"}, {"代號": "1102", "名稱": "亞泥"}, {"代號": "1216", "名稱": "統一"},
        {"代號": "2912", "名稱": "統一超"}, {"代號": "2002", "名稱": "中鋼"}, {"代號": "6505", "名稱": "台塑化"},
        {"代號": "1301", "名稱": "台塑"}, {"代號": "1303", "名稱": "南亞"}, {"代號": "1326", "名稱": "台化"},
        {"代號": "9910", "名稱": "豐泰"}, {"代號": "9904", "名稱": "寶成"}, {"代號": "1476", "名稱": "儒鴻"},

        # 6. 重電、綠能與航運 (10檔)
        {"代號": "1513", "名稱": "中興電"}, {"代號": "1519", "名稱": "華城"}, {"代號": "1503", "名稱": "士電"},
        {"代號": "1504", "名稱": "東元"}, {"代號": "1605", "名稱": "華新"}, {"代號": "2603", "名稱": "長榮"},
        {"代號": "2609", "名稱": "陽明"}, {"代號": "2615", "名稱": "萬海"}, {"代號": "2618", "名稱": "長榮航"},
        {"代號": "2610", "名稱": "華航"},

        # 7. 其他熱門指標 (13檔)
        {"代號": "2308", "名稱": "台達電"}, {"代號": "3008", "名稱": "大立光"}, {"代號": "2207", "名稱": "和泰車"},
        {"代號": "2412", "名稱": "中華電"}, {"代號": "3045", "名稱": "台灣大"}, {"代號": "4904", "名稱": "遠傳"},
        {"代號": "9921", "名稱": "巨大"}, {"代號": "2206", "名稱": "三陽工業"}, {"代號": "3293", "名稱": "鈊象"},
        {"代號": "8069", "名稱": "元太"}, {"代號": "2409", "名稱": "友達"}, {"代號": "3481", "名稱": "群創"},
        {"代號": "6415", "名稱": "矽力-KY"}
    ]
    return pd.DataFrame(top_stocks)

# 輔助：計算技術指標
def calculate_indicators(df):
    # MACD
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['DIF'] = exp12 - exp26
    df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = (df['DIF'] - df['DEA']) * 2
    
    # KD (9,3,3)
    low_min = df['Low'].rolling(window=9).min()
    high_max = df['High'].rolling(window=9).max()
    df['RSV'] = (df['Close'] - low_min) / (high_max - low_min) * 100
    df['K'] = df['RSV'].ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df

# 執行按鈕
if st.button("🚀 開始分析 100 檔熱門股", type="primary"):
    stock_df = get_tw_stock_list()
    st.info(f"✅ 已載入 {len(stock_df)} 檔全台熱門標的，正在計算技術指標...")
    
    results = []
    progress_bar = st.progress(0)
    
    for i, row in stock_df.iterrows():
        try:
            code, name = row['代號'], row['名稱']
            # 抓取 6 個月資料以確保技術指標準確
            data = yf.Ticker(code + ".TW").history(period="6mo")
            
            if len(data) >= 60:
                data = calculate_indicators(data)
                today = data.iloc[-1]
                yesterday = data.iloc[-2]
                
                # 價格數據
                price_yesterday = yesterday['Close']
                price_now = today['Close']
                change_pct = (price_now - price_yesterday) / price_yesterday * 100
                
                # 成交量 (與過去 5 天均量相比)
                vol_avg_5 = data['Volume'].iloc[-7:-2].mean()
                vol_ratio = today['Volume'] / vol_avg_5 if vol_avg_5 > 0 else 0
                
                # 技術訊號
                ma60 = data['Close'].tail(60).mean()
                kd_gold = today['K'] > today['D'] and yesterday['K'] < yesterday['D']
                macd_bull = today['MACD_Hist'] > 0 and today['DIF'] > today['DEA']

                # 篩選邏輯
                # 1. 漲幅與量能
                cond_1 = change_pct >= min_increase and vol_ratio >= vol_multiplier
                # 2. 季線 (勾選才檢查)
                cond_2 = price_now > ma60 if check_ma60 else True
                # 3. KD (勾選才檢查)
                cond_3 = kd_gold if check_kd_cross else True
                # 4. MACD (勾選才檢查)
                cond_4 = macd_bull if check_macd_bull else True

                if cond_1 and cond_2 and cond_3 and cond_4:
                    sigs = []
                    if kd_gold: sigs.append("KD金叉")
                    if macd_bull: sigs.append("MACD多頭")
                    if price_now > ma60: sigs.append("站上季線")
                    
                    results.append({
                        "代號": code,
                        "名稱": name,
                        "昨日收盤": f"{price_yesterday:.2f}",
                        "今日漲幅": f"{change_pct:.1f}%",
                        "量比": f"{vol_ratio:.1f}倍",
                        "技術訊號": " | ".join(sigs)
                    })
        except: pass
        progress_bar.progress((i + 1) / len(stock_df))

    if results:
        st.success(f"篩選完畢！共發現 {len(results)} 檔符合條件：")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.warning("⚠️ 目前條件下無符合股票。")
