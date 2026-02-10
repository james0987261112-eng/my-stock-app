import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
from FinMind.data import DataLoader  # 引入真實籌碼資料庫

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="台股 200 強戰情室", page_icon="📈", layout="wide")
st.title("📈 台股 200 強戰情室 (V13.0 真實籌碼版)")
st.write(f"系統執行時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("註：本版本串接 FinMind 真實法人數據。因需聯網查詢，掃描速度較慢，請耐心等候。")

# --- 2. 側邊欄：策略控制台 ---
st.sidebar.header("🎯 請選擇操盤策略")
strategy = st.sidebar.radio(
    "您今天想找什麼股票？",
    ("🔥 強勢噴出 (追高動能)", "🛡️ 波段多頭 (穩健趨勢)", "🎣 低檔轉折 (抄底反彈)")
)

st.sidebar.markdown("---")
ai_filter = st.sidebar.checkbox("只顯示 AI 供應鏈", value=False)
if ai_filter:
    st.sidebar.caption("✅ 已開啟濾鏡：將從 200 檔中篩選出 AI、散熱、機器人等核心族群。")

vol_threshold = st.sidebar.slider("量能過濾 (今日量/5日均量)", 0.5, 3.0, 1.0, 0.1)

# --- 3. 籌碼數據引擎 (FinMind) ---
@st.cache_data(ttl=3600) # 設定快取 1 小時，避免重複抓取
def get_chip_data(stock_id):
    try:
        api = DataLoader()
        # 抓取最近 5 天的數據
        start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        
        # 抓取三大法人買賣超
        df_inst = api.taiwan_stock_institutional_investors(
            stock_id=stock_id, 
            start_date=start_date
        )
        
        if df_inst.empty:
            return 0, 0, "無數據"

        # 取最近一天的數據
        latest = df_inst[df_inst['date'] == df_inst['date'].max()]
        if latest.empty:
            return 0, 0, "無數據"

        # 計算外資與投信買賣超 (Foreign_Investor, Investment_Trust)
        # FinMind 欄位名稱可能為 'Foreign_Investor_Diff' 等
        foreign_buy = latest[latest['name'] == 'Foreign_Investor']['buy'].sum() - latest[latest['name'] == 'Foreign_Investor']['sell'].sum()
        trust_buy = latest[latest['name'] == 'Investment_Trust']['buy'].sum() - latest[latest['name'] == 'Investment_Trust']['sell'].sum()
        
        return foreign_buy, trust_buy, "有數據"
    except Exception as e:
        return 0, 0, "連線失敗"

# --- 4. 內建熱門清單 ---
@st.cache_data
def get_tw_stock_list():
    top_stocks = [
        # === 💎 半導體權值 ===
        {"代號": "2330", "名稱": "台積電", "Tag": "AI-半導體"}, {"代號": "2454", "名稱": "聯發科", "Tag": "AI-IC設計"},
        {"代號": "2317", "名稱": "鴻海", "Tag": "AI-伺服器"}, {"代號": "2308", "名稱": "台達電", "Tag": "AI-電源"},
        {"代號": "2303", "名稱": "聯電", "Tag": "AI-半導體"}, {"代號": "3711", "名稱": "日月光", "Tag": "AI-封測"},
        {"代號": "3034", "名稱": "聯詠", "Tag": "AI-IC設計"}, {"代號": "2379", "名稱": "瑞昱", "Tag": "AI-IC設計"},
        {"代號": "3035", "名稱": "智原", "Tag": "AI-IP矽智財"}, {"代號": "3443", "名稱": "創意", "Tag": "AI-IP矽智財"},
        {"代號": "3661", "名稱": "世芯-KY", "Tag": "AI-IP矽智財"}, {"代號": "6643", "名稱": "M31", "Tag": "AI-IP矽智財"},
        {"代號": "6531", "名稱": "愛普*", "Tag": "AI-IP矽智財"}, {"代號": "3529", "名稱": "力旺", "Tag": "AI-IP矽智財"},
        {"代號": "6488", "名稱": "環球晶", "Tag": "AI-半導體"}, {"代號": "5483", "名稱": "中美晶", "Tag": "AI-半導體"},
        {"代號": "6147", "名稱": "頎邦", "Tag": "AI-封測"}, {"代號": "6239", "名稱": "力成", "Tag": "AI-封測"},
        {"代號": "8299", "名稱": "群聯", "Tag": "AI-IC設計"}, {"代號": "3105", "名稱": "穩懋", "Tag": "AI-PA功率"},
        {"代號": "2408", "名稱": "南亞科", "Tag": "AI-記憶體"}, {"代號": "2344", "名稱": "華邦電", "Tag": "AI-記憶體"},
        {"代號": "5347", "名稱": "世界", "Tag": "AI-半導體"}, {"代號": "6770", "名稱": "力積電", "Tag": "AI-半導體"},
        {"代號": "3227", "名稱": "原相", "Tag": "AI-IC設計"}, {"代號": "4961", "名稱": "天鈺", "Tag": "AI-IC設計"},
        {"代號": "4966", "名稱": "譜瑞-KY", "Tag": "AI-IC設計"}, {"代號": "6415", "名稱": "矽力-KY", "Tag": "AI-IC設計"},
        {"代號": "8016", "名稱": "矽創", "Tag": "AI-IC設計"}, {"代號": "8081", "名稱": "致新", "Tag": "AI-IC設計"},
        # === 🧠 AI 伺服器 / 組裝 ===
        {"代號": "2382", "名稱": "廣達", "Tag": "AI-伺服器"}, {"代號": "3231", "名稱": "緯創", "Tag": "AI-伺服器"},
        {"代號": "6669", "名稱": "緯穎", "Tag": "AI-伺服器"}, {"代號": "2376", "名稱": "技嘉", "Tag": "AI-伺服器"},
        {"代號": "2356", "名稱": "英業達", "Tag": "AI-伺服器"}, {"代號": "2301", "名稱": "光寶科", "Tag": "AI-電源"},
        {"代號": "2357", "名稱": "華碩", "Tag": "AI-PC"}, {"代號": "2353", "名稱": "宏碁", "Tag": "AI-PC"},
        {"代號": "4938", "名稱": "和碩", "Tag": "AI-組裝"}, {"代號": "2324", "名稱": "仁寶", "Tag": "AI-PC"},
        {"代號": "3706", "名稱": "神達", "Tag": "AI-伺服器"}, {"代號": "8112", "名稱": "至上", "Tag": "AI-通路"},
        {"代號": "8210", "名稱": "勤誠", "Tag": "AI-機殼"}, {"代號": "3013", "名稱": "晟銘電", "Tag": "AI-機殼"},
        {"代號": "6117", "名稱": "迎廣", "Tag": "AI-機殼"}, {"代號": "3515", "名稱": "華擎", "Tag": "AI-板卡"},
        {"代號": "2395", "名稱": "研華", "Tag": "AI-工業電腦"}, {"代號": "6214", "名稱": "精誠", "Tag": "AI-軟體"},
        {"代號": "2423", "名稱": "固緯", "Tag": "AI-儀器"}, {"代號": "5269", "名稱": "祥碩", "Tag": "AI-高速傳輸"},
        {"代號": "6271", "名稱": "同欣電", "Tag": "AI-封測"}, {"代號": "2449", "名稱": "京元電子", "Tag": "AI-封測"},
        {"代號": "3014", "名稱": "聯陽", "Tag": "AI-IC設計"}, {"代號": "6139", "名稱": "亞翔", "Tag": "AI-設備"},
        {"代號": "2480", "名稱": "敦陽科", "Tag": "AI-軟體"},
        # === 🤖 機器人 / 自動化 ===
        {"代號": "2359", "名稱": "所羅門", "Tag": "AI-機器人"}, {"代號": "2365", "名稱": "昆盈", "Tag": "AI-機器人"},
        {"代號": "4562", "名稱": "穎漢", "Tag": "AI-機器人"}, {"代號": "8374", "名稱": "羅昇", "Tag": "AI-機器人"},
        {"代號": "6125", "名稱": "廣運", "Tag": "AI-機器人"}, {"代號": "2049", "名稱": "上銀", "Tag": "AI-機器人"},
        {"代號": "1590", "名稱": "亞德客", "Tag": "AI-機器人"}, {"代號": "8367", "名稱": "建達", "Tag": "AI-機器人"},
        {"代號": "6188", "名稱": "廣明", "Tag": "AI-機器人"}, {"代號": "2059", "名稱": "川湖", "Tag": "AI-滑軌"},
        {"代號": "4569", "名稱": "六方科", "Tag": "AI-機器人"}, {"代號": "4526", "名稱": "東台", "Tag": "AI-機器人"},
        {"代號": "6640", "名稱": "均華", "Tag": "AI-設備"}, {"代號": "6438", "名稱": "迅得", "Tag": "AI-設備"},
        {"代號": "4532", "名稱": "瑞智", "Tag": "AI-機器人"},
        # === 🔥 散熱 / CoWoS / 矽光子 ===
        {"代號": "3017", "名稱": "奇鋐", "Tag": "AI-散熱"}, {"代號": "3324", "名稱": "雙鴻", "Tag": "AI-散熱"},
        {"代號": "2421", "名稱": "建準", "Tag": "AI-散熱"}, {"代號": "3653", "名稱": "健策", "Tag": "AI-散熱"},
        {"代號": "6230", "名稱": "超眾", "Tag": "AI-散熱"}, {"代號": "8996", "名稱": "高力", "Tag": "AI-散熱"},
        {"代號": "3483", "名稱": "力致", "Tag": "AI-散熱"}, {"代號": "3338", "名稱": "泰碩", "Tag": "AI-散熱"},
        {"代號": "2486", "名稱": "一詮", "Tag": "AI-散熱"}, {"代號": "5215", "名稱": "科嘉-KY", "Tag": "AI-散熱"},
        {"代號": "3131", "名稱": "弘塑", "Tag": "AI-CoWoS"}, {"代號": "3583", "名稱": "辛耘", "Tag": "AI-CoWoS"},
        {"代號": "6187", "名稱": "萬潤", "Tag": "AI-CoWoS"}, {"代號": "5443", "名稱": "均豪", "Tag": "AI-CoWoS"},
        {"代號": "3450", "名稱": "聯鈞", "Tag": "AI-矽光子"}, {"代號": "3163", "名稱": "波若威", "Tag": "AI-矽光子"},
        {"代號": "3363", "名稱": "上詮", "Tag": "AI-矽光子"}, {"代號": "4979", "名稱": "華星光", "Tag": "AI-矽光子"},
        {"代號": "6442", "名稱": "光聖", "Tag": "AI-矽光子"}, {"代號": "4977", "名稱": "眾達-KY", "Tag": "AI-矽光子"},
        {"代號": "3234", "名稱": "光環", "Tag": "AI-矽光子"}, {"代號": "3081", "名稱": "聯亞", "Tag": "AI-矽光子"},
        {"代號": "4908", "名稱": "前鼎", "Tag": "AI-矽光子"}, {"代號": "6451", "名稱": "訊芯-KY", "Tag": "AI-CPO"},
        {"代號": "6196", "名稱": "帆宣", "Tag": "AI-設備"},
        # === ⚡ 網通 / PCB / 重電 ===
        {"代號": "2345", "名稱": "智邦", "Tag": "AI-網通"}, {"代號": "6285", "名稱": "啟碁", "Tag": "AI-網通"},
        {"代號": "5388", "名稱": "中磊", "Tag": "AI-網通"}, {"代號": "3704", "名稱": "合勤控", "Tag": "AI-網通"},
        {"代號": "2314", "名稱": "台揚", "Tag": "AI-網通"}, {"代號": "3491", "名稱": "昇達科", "Tag": "AI-低軌衛星"},
        {"代號": "8011", "名稱": "台通", "Tag": "AI-網通"}, {"代號": "3037", "名稱": "欣興", "Tag": "AI-載板"},
        {"代號": "8046", "名稱": "南電", "Tag": "AI-載板"}, {"代號": "3189", "名稱": "景碩", "Tag": "AI-載板"},
        {"代號": "2368", "名稱": "金像電", "Tag": "AI-PCB"}, {"代號": "2383", "名稱": "台光電", "Tag": "AI-CCL"},
        {"代號": "6274", "名稱": "台燿", "Tag": "AI-CCL"}, {"代號": "6213", "名稱": "聯茂", "Tag": "AI-CCL"},
        {"代號": "2313", "名稱": "華通", "Tag": "AI-PCB"}, {"代號": "3044", "名稱": "健鼎", "Tag": "AI-PCB"},
        {"代號": "4958", "名稱": "臻鼎-KY", "Tag": "AI-PCB"}, {"代號": "1513", "名稱": "中興電", "Tag": "重電綠能"},
        {"代號": "1519", "名稱": "華城", "Tag": "重電綠能"}, {"代號": "1503", "名稱": "士電", "Tag": "重電綠能"},
        {"代號": "1514", "名稱": "亞力", "Tag": "重電綠能"}, {"代號": "1504", "名稱": "東元", "Tag": "重電綠能"},
        {"代號": "1605", "名稱": "華新", "Tag": "重電綠能"}, {"代號": "1609", "名稱": "大亞", "Tag": "重電綠能"},
        {"代號": "6806", "名稱": "森崴能源", "Tag": "重電綠能"}, {"代號": "9958", "名稱": "世紀鋼", "Tag": "重電綠能"},
        {"代號": "3708", "名稱": "上緯投控", "Tag": "重電綠能"}, {"代號": "6443", "名稱": "元晶", "Tag": "重電綠能"},
        {"代號": "1515", "名稱": "力山", "Tag": "重電綠能"}, {"代號": "2305", "名稱": "全友", "Tag": "重電綠能"},
        # === 🚢 航運 / 金融 / 傳產 ===
        {"代號": "2603", "名稱": "長榮", "Tag": "航運"}, {"代號": "2609", "名稱": "陽明", "Tag": "航運"},
        {"代號": "2615", "名稱": "萬海", "Tag": "航運"}, {"代號": "2618", "名稱": "長榮航", "Tag": "航運"},
        {"代號": "2610", "名稱": "華航", "Tag": "航運"}, {"代號": "2637", "名稱": "慧洋-KY", "Tag": "航運"},
        {"代號": "2606", "名稱": "裕民", "Tag": "航運"}, {"代號": "2634", "名稱": "漢翔", "Tag": "航運"},
        {"代號": "2881", "名稱": "富邦金", "Tag": "金融"}, {"代號": "2882", "名稱": "國泰金", "Tag": "金融"},
        {"代號": "2891", "名稱": "中信金", "Tag": "金融"}, {"代號": "2886", "名稱": "兆豐金", "Tag": "金融"},
        {"代號": "2884", "名稱": "玉山金", "Tag": "金融"}, {"代號": "2885", "名稱": "元大金", "Tag": "金融"},
        {"代號": "5880", "名稱": "合庫金", "Tag": "金融"}, {"代號": "2892", "名稱": "第一金", "Tag": "金融"},
        {"代號": "2880", "名稱": "華南金", "Tag": "金融"}, {"代號": "2883", "名稱": "開發金", "Tag": "金融"},
        {"代號": "2887", "名稱": "台新金", "Tag": "金融"}, {"代號": "2890", "名稱": "永豐金", "Tag": "金融"},
        {"代號": "2888", "名稱": "新光金", "Tag": "金融"}, {"代號": "5871", "名稱": "中租-KY", "Tag": "金融"},
        {"代號": "1101", "名稱": "台泥", "Tag": "傳產"}, {"代號": "2002", "名稱": "中鋼", "Tag": "傳產"},
        {"代號": "1301", "名稱": "台塑", "Tag": "傳產"}, {"代號": "6505", "名稱": "台塑化", "Tag": "傳產"},
        {"代號": "2207", "名稱": "和泰車", "Tag": "汽車"}, {"代號": "2201", "名稱": "裕隆", "Tag": "汽車"},
        {"代號": "2204", "名稱": "中華", "Tag": "汽車"}, {"代號": "1476", "名稱": "儒鴻", "Tag": "紡織"},
        {"代號": "1402", "名稱": "遠東新", "Tag": "紡織"}, {"代號": "2105", "名稱": "正新", "Tag": "傳產"},
        {"代號": "2014", "名稱": "中鴻", "Tag": "鋼鐵"}, {"代號": "1722", "名稱": "台肥", "Tag": "傳產"},
        {"代號": "1216", "名稱": "統一", "Tag": "傳產"},
        # === 💎 其他熱門指標 ===
        {"代號": "1795", "名稱": "美時", "Tag": "生技"}, {"代號": "6472", "名稱": "保瑞", "Tag": "生技"},
        {"代號": "4147", "名稱": "中裕", "Tag": "生技"}, {"代號": "1760", "名稱": "寶齡富錦", "Tag": "生技"},
        {"代號": "3293", "名稱": "鈊象", "Tag": "遊戲"}, {"代號": "5478", "名稱": "智冠", "Tag": "遊戲"},
        {"代號": "8069", "名稱": "元太", "Tag": "電子紙"}, {"代號": "3008", "名稱": "大立光", "Tag": "光學"},
        {"代號": "3406", "名稱": "玉晶光", "Tag": "光學"}, {"代號": "2409", "名稱": "友達", "Tag": "面板"},
        {"代號": "3481", "名稱": "群創", "Tag": "面板"}, {"代號": "6116", "名稱": "彩晶", "Tag": "面板"},
        {"代號": "2412", "名稱": "中華電", "Tag": "電信"}, {"代號": "3045", "名稱": "台灣大", "Tag": "電信"},
        {"代號": "4904", "名稱": "遠傳", "Tag": "電信"}, {"代號": "9921", "名稱": "巨大", "Tag": "自行車"},
        {"代號": "9914", "名稱": "美利達", "Tag": "自行車"}, {"代號": "4763", "名稱": "材料-KY", "Tag": "傳產"},
        {"代號": "6176", "名稱": "瑞儀", "Tag": "光電"}, {"代號": "6269", "名稱": "台郡", "Tag": "PCB"},
        {"代號": "2360", "名稱": "致茂", "Tag": "儀器"}, {"代號": "2912", "名稱": "統一超", "Tag": "零售"},
        {"代號": "2707", "名稱": "晶華", "Tag": "觀光"}, {"代號": "2731", "名稱": "雄獅", "Tag": "觀光"},
        {"代號": "2727", "名稱": "王品", "Tag": "觀光"}, {"代號": "2498", "名稱": "宏達電", "Tag": "VR"},
        {"代號": "5522", "名稱": "遠雄", "Tag": "營建"}, {"代號": "2542", "名稱": "興富發", "Tag": "營建"},
        {"代號": "2501", "名稱": "國建", "Tag": "營建"}, {"代號": "2515", "名稱": "中工", "Tag": "營建"},
        {"代號": "9945", "名稱": "潤泰新", "Tag": "營建"}, {"代號": "2548", "名稱": "華固", "Tag": "營建"},
        {"代號": "3023", "名稱": "信邦", "Tag": "電子"}, {"代號": "6282", "名稱": "康舒", "Tag": "電源"},
        {"代號": "6182", "名稱": "合晶", "Tag": "半導體"}, {"代號": "6257", "名稱": "矽格", "Tag": "封測"},
        {"代號": "3006", "名稱": "晶豪科", "Tag": "記憶體"}, {"代號": "8150", "名稱": "南茂", "Tag": "封測"},
        {"代號": "6223", "名稱": "旺矽", "Tag": "探針卡"}, {"代號": "6414", "名稱": "樺漢", "Tag": "IPC"}
    ]
    return pd.DataFrame(top_stocks)

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

# --- 🎯 V13.0 核心：真實籌碼判讀引擎 (FinMind 整合) ---
def get_chip_analysis(strategy, change_pct, vol_ratio, price, ma5, ma60, foreign_buy, trust_buy):
    
    # 基本籌碼判斷邏輯
    is_foreign_buy = foreign_buy > 0
    is_trust_buy = trust_buy > 0
    is_foreign_sell = foreign_buy < 0
    is_trust_sell = trust_buy < 0
    
    # 策略 1: 強勢噴出
    if strategy == "🔥 強勢噴出 (追高動能)":
        if is_foreign_buy and is_trust_buy:
            return "🚀 雙主力鎖籌 (土洋合擊)"
        if is_trust_buy:
            return "🚀 投信點火 (作帳行情)"
        if is_foreign_buy:
            return "📈 外資回補 (波段買盤)"
        return "📈 帶量攻擊 (主力動能)"

    # 策略 2: 波段多頭
    elif strategy == "🛡️ 波段多頭 (穩健趨勢)":
        if change_pct < 0 and is_trust_buy and is_foreign_sell:
            return "📉 法人換手 (外資丟、投信撿)"
        if change_pct < 0 and is_foreign_buy:
            return "🛡️ 外資護盤 (低接買盤)"
        if is_trust_buy:
            return "💎 投信認養 (波段持有)"
        if is_foreign_sell and is_trust_sell:
            return "⚠️ 法人雙賣 (短線修正)"
        return "🛡️ 多頭排列 (穩健續強)"

    # 策略 3: 低檔轉折
    elif strategy == "🎣 低檔轉折 (抄底反彈)":
        if is_trust_buy:
            return "✨ 投信抄底 (低檔佈局)"
        if is_foreign_buy:
            return "✨ 外資低接 (跌深反彈)"
        if is_foreign_sell and is_trust_sell:
            return "⚠️ 散戶接盤 (法人未進場)"
        return "✨ 技術面反彈 (觀望籌碼)"
    
    return "符合策略條件"

# 🚀 執行主程式
if st.button("🚀 執行操盤手完整掃描", type="primary"):
    stock_df = get_tw_stock_list()
    
    if ai_filter:
        working_df = stock_df[stock_df['Tag'].str.contains("AI", na=False)].copy()
        st.info(f"🤖 AI 聚焦模式：正在分析 {len(working_df)} 檔核心供應鏈...")
    else:
        working_df = stock_df.copy()
        st.info(f"📊 全市場模式：正在掃描 200 檔指標股 (含 FinMind 真實籌碼)...")

    working_df = working_df.reset_index(drop=True)
    total = len(working_df)
    
    if total == 0:
        st.warning("⚠️ 沒有符合條件的股票。")
    else:
        status_text = st.empty()
        progress_bar = st.progress(0)
        results = []
        
        for i, row in working_df.iterrows():
            code, name, tag = row['代號'], row['名稱'], row['Tag']
            status_text.text(f"🔍 掃描中 ({i+1}/{total})：[{code} {name}] - 查詢籌碼中...")
            
            try:
                # 1. 抓價量 (Yahoo)
                ticker = yf.Ticker(f"{code}.TW")
                data = ticker.history(period="6mo")
                
                # 2. 抓籌碼 (FinMind) -> 這裡會比較慢
                foreign_buy, trust_buy, chip_status = get_chip_data(code)

                if not data.empty and len(data) >= 60:
                    data = calculate_indicators(data)
                    
                    price_now = data['Close'].iloc[-1]
                    price_yesterday = data['Close'].iloc[-2]
                    change_pct = (price_now - price_yesterday) / price_yesterday * 100
                    
                    vol_avg = data['Volume'].iloc[-7:-2].mean()
                    vol_ratio = data['Volume'].iloc[-1] / vol_avg if vol_avg > 0 else 0
                    
                    ma5 = data['Close'].tail(5).mean()
                    ma60 = data['Close'].tail(60).mean()
                    kd_cross = data['K'].iloc[-1] > data['D'].iloc[-1] and data['K'].iloc[-2] < data['D'].iloc[-2]
                    macd_red = data['MACD_Hist'].iloc[-1] > 0
                    
                    is_match = False
                    
                    # === 策略核心判斷 (含滑桿限制) ===
                    if strategy == "🔥 強勢噴出 (追高動能)":
                        if change_pct > 1.0 and price_now > ma5 and vol_ratio >= vol_threshold:
                            is_match = True
                    elif strategy == "🛡️ 波段多頭 (穩健趨勢)":
                        if price_now > ma60 and macd_red and vol_ratio >= vol_threshold:
                            is_match = True
                    elif strategy == "🎣 低檔轉折 (抄底反彈)":
                        if kd_cross and vol_ratio >= vol_threshold:
                            is_match = True

                    if is_match:
                        # 呼叫 V13.0 真實籌碼解讀引擎
                        chip_reason = get_chip_analysis(strategy, change_pct, vol_ratio, price_now, ma5, ma60, foreign_buy, trust_buy)
                        
                        display_tag = tag.replace("AI-", "🔥 ") if "AI-" in tag else (tag if tag else "一般")
                        
                        # 格式化籌碼顯示
                        f_str = f"外資:{int(foreign_buy/1000)}k" if abs(foreign_buy) > 0 else "外資:-"
                        t_str = f"投信:{int(trust_buy/1000)}k" if abs(trust_buy) > 0 else "投信:-"
                        
                        results.append({
                            "代號": code, "名稱": name, "屬性": display_tag, 
                            "籌碼戰況": f"{f_str} / {t_str}",
                            "即時價格": f"{price_now:.2f}", 
                            "今日漲幅": f"{change_pct:.1f}%", 
                            "量比": f"{vol_ratio:.1f}倍", 
                            "原因": chip_reason # 顯示真實籌碼解讀
                        })
                
                # 這裡不需要 sleep 太多，因為 FinMind 請求本身就會耗時
                time.sleep(0.01) 
            except Exception as e:
                pass 

            progress_bar.progress((i + 1) / total)

        status_text.text("✅ 全數掃描完畢！")
        if results:
            df_res = pd.DataFrame(results).sort_values(by="今日漲幅", ascending=False, key=lambda x: x.str.strip('%').astype(float))
            st.success(f"🎊 發現 {len(results)} 檔符合策略標的！")
            st.dataframe(df_res[["代號", "名稱", "屬性", "籌碼戰況", "即時價格", "今日漲幅", "量比", "原因"]], use_container_width=True)
        else:
            st.warning(f"目前市場符合條件標的較少 (設定量比門檻：{vol_threshold}倍)。")
