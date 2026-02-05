import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="台股 AI 趨勢操盤手", page_icon="🤖", layout="wide")
st.title("🤖 台股 AI 趨勢操盤手 (V6.0)")
st.write(f"趨勢分析日期：{datetime.now().strftime('%Y-%m-%d')}")

# --- 2. 側邊欄：策略與篩選 ---
st.sidebar.header("🎯 策略控制台")

# 2.1 產業篩選 (新增功能)
industry_filter = st.sidebar.selectbox(
    "📊 鎖定產業板塊",
    ("全部顯示", "🤖 AI 伺服器/組裝", "🔥 散熱與機殼", "⚡ 重電與綠能", "🚢 航運與傳產", "💎 半導體與 IC 設計")
)

st.sidebar.markdown("---")

# 2.2 策略選擇
strategy = st.sidebar.radio(
    "📈 選擇操盤策略",
    ("🔥 強勢噴出 (追高動能)", "🛡️ 波段多頭 (穩健趨勢)", "🎣 低檔轉折 (抄底反彈)")
)

vol_threshold = st.sidebar.slider("量能過濾 (今日量/5日均量)", 0.5, 3.0, 1.0, 0.1)

# --- 3. 智慧清單 (含產業標籤) ---
@st.cache_data
def get_tw_stock_list():
    # 這裡示範如何將股票加上「產業」標籤，讓篩選更精準
    data = [
        # AI 伺服器/組裝
        {"代號": "2317", "名稱": "鴻海", "產業": "🤖 AI 伺服器/組裝"},
        {"代號": "2382", "名稱": "廣達", "產業": "🤖 AI 伺服器/組裝"},
        {"代號": "3231", "名稱": "緯創", "產業": "🤖 AI 伺服器/組裝"},
        {"代號": "6669", "名稱": "緯穎", "產業": "🤖 AI 伺服器/組裝"},
        {"代號": "2376", "名稱": "技嘉", "產業": "🤖 AI 伺服器/組裝"},
        {"代號": "2356", "名稱": "英業達", "產業": "🤖 AI 伺服器/組裝"},
        {"代號": "2357", "名稱": "華碩", "產業": "🤖 AI 伺服器/組裝"},
        {"代號": "2301", "名稱": "光寶科", "產業": "🤖 AI 伺服器/組裝"},
        
        # 散熱與機殼 (AI 關鍵)
        {"代號": "3017", "名稱": "奇鋐", "產業": "🔥 散熱與機殼"},
        {"代號": "3324", "名稱": "雙鴻", "產業": "🔥 散熱與機殼"},
        {"代號": "2421", "名稱": "建準", "產業": "🔥 散熱與機殼"},
        {"代號": "3653", "名稱": "健策", "產業": "🔥 散熱與機殼"},
        {"代號": "6230", "名稱": "超眾", "產業": "🔥 散熱與機殼"},
        {"代號": "3013", "名稱": "晟銘電", "產業": "🔥 散熱與機殼"},
        {"代號": "8996", "名稱": "高力", "產業": "🔥 散熱與機殼"},

        # 半導體/IC設計 (AI 上游)
        {"代號": "2330", "名稱": "台積電", "產業": "💎 半導體與 IC 設計"},
        {"代號": "2454", "名稱": "聯發科", "產業": "💎 半導體與 IC 設計"},
        {"代號": "3443", "名稱": "創意", "產業": "💎 半導體與 IC 設計"},
        {"代號": "3661", "名稱": "世芯-KY", "產業": "💎 半導體與 IC 設計"},
        {"代號": "3035", "名稱": "智原", "產業": "💎 半導體與 IC 設計"},
        {"代號": "2303", "名稱": "聯電", "產業": "💎 半導體與 IC 設計"},
        {"代號": "3711", "名稱": "日月光", "產業": "💎 半導體與 IC 設計"},
        {"代號": "3034", "名稱": "聯詠", "產業": "💎 半導體與 IC 設計"},
        {"代號": "2379", "名稱": "瑞昱", "產業": "💎 半導體與 IC 設計"},

        # 重電與綠能 (缺電題材)
        {"代號": "1513", "名稱": "中興電", "產業": "⚡ 重電與綠能"},
        {"代號": "1519", "名稱": "華城", "產業": "⚡ 重電與綠能"},
        {"代號": "1503", "名稱": "士電", "產業": "⚡ 重電與綠能"},
        {"代號": "1504", "名稱": "東元", "產業": "⚡ 重電與綠能"},
        {"代號": "1605", "名稱": "華新", "產業": "⚡ 重電與綠能"},
        {"代號": "1514", "名稱": "亞力", "產業": "⚡ 重電與綠能"},

        # 航運與傳產
        {"代號": "2603", "名稱": "長榮", "產業": "🚢 航運與傳產"},
        {"代號": "2609", "名稱": "陽明", "產業": "🚢 航運與傳產"},
        {"代號": "2615", "名稱": "萬海", "產業": "🚢 航運與傳產"},
        {"代號": "2618", "名稱": "長榮航", "產業": "🚢 航運與傳產"},
        {"代號": "2610", "名稱": "華航", "產業": "🚢 航運與傳產"},
        
        # 為了示範，若您有更多股票，請依照格式補在下面，"產業" 欄位可以自己定義
        {"代號": "2368", "名稱": "金像電", "產業": "🤖 AI 伺服器/組裝"}, # PCB 歸類於此方便觀察
        {"代號": "3037", "名稱": "欣興", "產業": "💎 半導體與 IC 設計"}, # 載板
        {"代號": "2383", "名稱": "台光電", "產業": "🤖 AI 伺服器/組裝"}, # CCL
        {"代號": "2881", "名稱": "富邦金", "產業": "💰 金融與其他"},
        {"代號": "2882", "名稱": "國泰金", "產業": "💰 金融與其他"}
    ]
    # 補滿至 100~200 檔的邏輯 (略)，這裡先用精選示範
    return pd.DataFrame(data)

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

# 繪製 K 線圖函數
def plot_candlestick(df, title):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name='K線')])
    # 加一條 20日均線
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'].rolling(window=20).mean(), 
                             mode='lines', name='月線(20MA)', line=dict(color='orange', width=1.5)))
    fig.update_layout(title=title, xaxis_title='日期', yaxis_title='股價', height=350, margin=dict(l=0, r=0, t=30, b=0))
    return fig

# 🚀 執行主程式
if st.button("🚀 AI 趨勢掃描啟動", type="primary"):
    df_list = get_tw_stock_list()
    
    # 1. 先根據使用者選擇的產業進行過濾
    if industry_filter != "全部顯示":
        df_list = df_list[df_list['產業'] == industry_filter]
    
    st.info(f"🔍 正在掃描 **{industry_filter}** 板塊，共 {len(df_list)} 檔標的...")
    
    status_text = st.empty()
    progress_bar = st.progress(0)
    results = []
    
    for i, row in df_list.iterrows():
        code, name, industry = row['代號'], row['名稱'], row['產業']
        status_text.text(f"分析中：[{code} {name}] ({i+1}/{len(df_list)})")
        
        try:
            data = yf.Ticker(code + ".TW").history(period="6mo")
            if len(data) >= 60:
                data = calculate_indicators(data)
                today, yesterday = data.iloc[-1], data.iloc[-2]
                price_now, price_prev = today['Close'], yesterday['Close']
                change_pct = (price_now - price_prev) / price_prev * 100
                vol_avg = data['Volume'].iloc[-7:-2].mean()
                vol_ratio = today['Volume'] / vol_avg if vol_avg > 0 else 0
                
                ma5, ma20, ma60 = data['Close'].tail(5).mean(), data['Close'].tail(20).mean(), data['Close'].tail(60).mean()
                kd_cross = today['K'] > today['D'] and yesterday['K'] < yesterday['D']
                macd_red = today['MACD_Hist'] > 0
                
                match, reason = False, ""
                
                # 策略邏輯
                if strategy == "🔥 強勢噴出 (追高動能)":
                    if change_pct > 0.5 and price_now > ma5 and vol_ratio >= vol_threshold:
                        match, reason = True, "AI 動能轉強/站穩短均"
                elif strategy == "🛡️ 波段多頭 (穩健趨勢)":
                    if price_now > ma60 and macd_red:
                        match, reason = True, "長線保護短線/趨勢向上"
                elif strategy == "🎣 低檔轉折 (抄底反彈)":
                    if kd_cross: match, reason = True, "低檔黃金交叉/乖離修正"

                if match:
                    results.append({
                        "代號": code, "名稱": name, "產業": industry,
                        "股價": f"{price_now:.2f}", "漲幅": f"{change_pct:.1f}%",
                        "量比": f"{vol_ratio:.1f}倍", "AI簡評": reason,
                        "raw_data": data # 暫存數據給畫圖用
                    })
        except: pass
        progress_bar.progress((i + 1) / len(df_list))
    
    status_text.empty()
    
    if results:
        st.success(f"✅ 掃描完成！在 **{industry_filter}** 中發現 {len(results)} 檔機會股")
        
        # 顯示結果，並加入展開畫圖功能
        for item in results:
            with st.expander(f"📊 {item['代號']} {item['名稱']} ({item['漲幅']}) - {item['AI簡評']}"):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write(f"**產業**：{item['產業']}")
                    st.write(f"**收盤價**：{item['股價']}")
                    st.write(f"**成交量倍數**：{item['量比']}")
                    st.caption("AI 訊號解讀：" + item['AI簡評'])
                with col2:
                    st.plotly_chart(plot_candlestick(item['raw_data'], f"{item['名稱']} K線圖"), use_container_width=True)
    else:
        st.warning("目前條件下無符合標的，建議切換產業或策略。")
