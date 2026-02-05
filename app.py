import streamlit as st
import pandas as pd
import pandas_datareader as pdr
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 設定頁面資訊
st.set_page_config(page_title="AI 趨勢選股戰情室", layout="wide")

st.title("🚀 台股 AI 庫存監控與籌碼分析")
st.write("目前專注指標：法人籌碼集中度、20日乖離率")

# 1. 庫存清單與參數設定
my_stocks = ['00635U.TW', '2409.TW', '3450.TW', '6187.TW', '6230.TW']
target_stock = st.sidebar.selectbox("切換追蹤標的", my_stocks, index=2) # 預設聯鈞
start_date = datetime.now() - timedelta(days=120)

# 2. 抓取數據 (以 yfinance 為例)
@st.cache_data
def get_stock_data(ticker):
    data = yf.download(ticker, start=start_date)
    return data

df = get_stock_data(target_stock)

# 3. 計算核心指標：乖離率 (BIAS)
def calculate_metrics(df):
    # 計算 20MA
    df['MA20'] = df['Close'].rolling(window=20).mean()
    # 計算 20日乖離率
    df['BIAS_20'] = ((df['Close'] - df['MA20']) / df['MA20']) * 100
    return df

df = calculate_metrics(df)
current_bias = df['BIAS_20'].iloc[-1]

# 4. 側邊欄警示燈號 (根據乖離率)
st.sidebar.metric("當前 20日乖離率", f"{current_bias:.2f}%")
if current_bias > 10:
    st.sidebar.error("⚠️ 指標過熱：注意回檔風險")
elif current_bias < -10:
    st.sidebar.success("✅ 超跌訊號：考慮逢低布局")
else:
    st.sidebar.info("📊 走勢平穩")

# 5. 主視覺圖表：K線與均線
fig = go.Figure(data=[
    go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"),
    go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=2), name="20日均線")
])
fig.update_layout(title=f"{target_stock} 股價走勢圖", xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

# 6. 法人籌碼模擬區 (註：實務上需串接 FinMind API)
st.subheader("🕵️ 法人籌碼動態 (模擬數據)")
col1, col2 = st.columns(2)

with col1:
    st.write("最近 5 日法人買賣超趨勢")
    # 這裡建議未來串接 API 獲取實際買賣超張數
    mock_data = pd.DataFrame({
        '日期': df.index[-5:],
        '法人買賣超': [500, -200, 1200, 800, -100]
    })
    st.bar_chart(mock_data.set_index('日期'))

with col2:
    concentration = 12.5 # 假設數值
    st.metric("5日籌碼集中度", f"{concentration}%")
    st.write("註：集中度 > 10% 代表大人正在吃貨。")

# 7. 庫存檢查表
st.divider()
st.subheader("📋 庫存操作筆記")
st.table(pd.DataFrame({
    "股票代碼": my_stocks,
    "核心題材": ["黃金避險", "面板循環", "矽光子/CPO", "CoWoS設備", "AI散熱"],
    "操作策略": ["持股對沖", "逢高調節", "強勢續抱", "拉回加碼", "嚴設停損"]
}))
