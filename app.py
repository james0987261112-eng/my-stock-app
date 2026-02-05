import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="台股 AI 趨勢監控", page_icon="🤖", layout="wide")
st.title("🤖 台股 AI 趨勢監控 (即時價格版)")
st.write(f"系統更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- 2. 側邊欄設定 ---
st.sidebar.header("🎯 策略控制台")
industry_filter = st.sidebar.selectbox(
    "📊 鎖定產業板塊",
    ("全部顯示", "🤖 AI 伺服器/組裝", "🔥 散熱與機殼", "⚡ 重電與綠能", "🚢 航運與傳產", "💎 半導體與 IC 設計")
)
st.sidebar.markdown("---")
strategy = st.sidebar.radio(
    "📈 選擇操盤策略",
    ("🔥 強勢噴出 (追高動能)", "🛡️ 波段多頭 (穩健趨勢)", "🎣 低檔轉折 (抄底反彈)")
)
vol_threshold = st.sidebar.slider("量能過濾 (今日量/5日均量)", 0.5, 3.0, 1.0, 0.1)

# --- 3. 股票清單與產業分類 ---
@st.cache_data
def get_tw_stock_list():
    data = [
        # AI 伺服器/組裝
        {"代號": "2317", "名稱": "鴻海", "產業": "🤖 AI 伺服器/組裝"},
        {"代號": "2382", "名稱": "廣達", "產業": "🤖 AI 伺服器/組裝"},
        {"代號": "3231", "名稱": "緯創", "產業": "🤖 AI 伺服器/組裝"},
        {"代號": "6669", "名稱": "緯穎", "產業": "🤖 AI 伺服器/組裝"},
        {"代號": "2376", "名稱": "技嘉", "產業": "🤖 AI 伺服器/組裝"},
        {"代號": "2356", "名稱": "英業達", "產業": "🤖 AI 伺服器/組裝"},
        {"代號": "2368", "名稱": "金像電", "產業": "🤖 AI 伺服器/組裝"},
        {"代號": "2383", "名稱": "台光電", "產業": "🤖 AI 伺服器/組裝"},
        
        # 散熱與機殼
        {"代號": "3017", "名稱": "奇鋐", "產業": "🔥 散熱與機殼"},
        {"代號": "3324", "名稱": "雙鴻", "產業": "🔥 散熱與機殼"},
        {"代號": "2421", "名稱": "建準", "產業": "🔥 散熱與機殼"},
        {"代號": "3013", "名稱": "晟銘電", "產業": "🔥 散熱與機殼"},
        {"代號": "8996", "名稱": "高力", "產業": "🔥 散熱與機殼"},

        # 半導體/IC設計
        {"代號": "2330", "名稱": "台積電", "產業": "💎 半導體與 IC 設計"},
        {"代號": "2454", "名稱": "聯發科", "產業": "💎 半導體與 IC 設計"},
        {"代號": "3443", "名稱": "創意", "產業": "💎 半導體與 IC 設計"},
        {"代號": "3661", "名稱": "世芯-KY", "產業": "💎 半導體與 IC 設計"},
        {"代號": "3035", "名稱": "智原", "產業": "💎 半導體與 IC 設計"},

        # 重電與綠能
        {"代號": "1513", "名稱": "中興電", "產業": "⚡ 重電與綠能"},
        {"代號": "1519", "名稱": "華城", "產業": "⚡ 重電與綠能"},
        {"代號": "1503", "名稱": "士電", "產業": "⚡ 重電與綠能"},

        # 航運與傳產
        {"代號": "2603", "名稱": "長榮", "產業": "🚢 航運與傳產"},
        {"代號": "2609", "名稱": "陽明", "產業": "🚢 航運與傳產"},
        {"代號": "2618", "名稱": "長榮航", "產業": "🚢 航運與傳產"}
    ]
    # 此處可繼續增加至 100-200 檔
    return pd.DataFrame(data)

def calculate_indicators(df):
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_Hist'] = (exp12 - exp26 - (exp12 - exp26).ewm(span=9, adjust=False).mean()) * 2
    low_min, high_max = df['Low'].rolling(9).min(), df['High'].rolling(9).max()
    df['K'] = ((df['Close'] - low_min) / (high_max - low_min) * 100).ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df

def plot_candlestick(df, title):
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線')])
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'].rolling(20).mean(), mode='lines', name='月線(20MA)', line=dict(color='orange', width=1.5)))
    fig.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0), template="plotly_dark")
    return fig

# --- 4. 執行掃描 ---
if st.button("🚀 執行即時趨勢掃描", type="primary"):
    df_list = get_tw_stock_list()
    if industry_filter != "全部顯示":
        df_list = df_list[df_list['產業'] == industry_filter]
    
    st.info(f"🔍 正在同步最新價格，掃描 **{industry_filter}** 板塊...")
    
    status_text = st.empty()
    progress_bar = st.progress(0)
    results = []
    
    for i, row in df_list.iterrows():
        code, name, industry = row['代號'], row['名稱'], row['產業']
        status_text.text(f"分析中：[{code} {name}] ({i+1}/{len(df_list)})")
        
        try:
            # 獲取 6 個月歷史數據
            data = yf.Ticker(code + ".TW").history(period="6mo")
            if len(data) >= 60:
                data = calculate_indicators(data)
                today, yesterday = data.iloc[-1], data.iloc[-2]
                
                # --- 價格資訊 ---
                price_prev = yesterday['Close']  # 昨日收盤
                price_now = today['Close']      # 最新價格 (即時或今日收盤)
                change_pct = (price_now - price_prev) / price_prev * 100
                
                vol_ratio = today['Volume'] / data['Volume'].iloc[-7:-2].mean()
                ma5, ma60 = data['Close'].tail(5).mean(), data['Close'].tail(60).mean()
                kd_cross = today['K'] > today['D'] and yesterday['K'] < yesterday['D']
                macd_red = today['MACD_Hist'] > 0
                
                match, reason = False, ""
                if strategy == "🔥 強勢噴出 (追高動能)":
                    if change_pct > 0.5 and price_now > ma5 and vol_ratio >= vol_threshold:
                        match, reason = True, "強勢動能/爆量起漲"
                elif strategy == "🛡️ 波段多頭 (穩健趨勢)":
                    if price_now > ma60 and macd_red:
                        match, reason = True, "波段向上/站穩季線"
                elif strategy == "🎣 低檔轉折 (抄底反彈)":
                    if kd_cross: match, reason = True, "低檔金叉/起漲轉折"

                if match:
                    results.append({
                        "代號": code, "名稱": name, "產業": industry,
                        "昨日收盤": f"{price_prev:.2f}",
                        "最新價格": f"{price_now:.2f}", # 新增最新價格
                        "今日漲幅": f"{change_pct:.1f}%",
                        "量比": f"{vol_ratio:.1f}倍",
                        "AI簡評": reason, "raw_data": data
                    })
        except: pass
        progress_bar.progress((i + 1) / len(df_list))
    
    status_text.empty()
    if results:
        st.success(f"✅ 發現 {len(results)} 檔標的")
        # 將結果轉換為 DataFrame 並顯示
        df_display = pd.DataFrame(results).drop(columns=['raw_data'])
        st.dataframe(df_display, use_container_width=True)
        
        # 顯示詳細 K 線
        for item in results:
            with st.expander(f"📊 {item['代號']} {item['名稱']} | 最新：{item['最新價格']} ({item['今日漲幅']})"):
                st.plotly_chart(plot_candlestick(item['raw_data'], f"{item['名稱']} 即時趨勢圖"), use_container_width=True)
    else:
        st.warning("目前市場狀況無符合標的。")
