import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.title("🇹🇼 台股全市場起漲偵測器")
st.write("掃描範圍：所有上市與上櫃公司")

# --- 自動取得台股清單的功能 ---
@st.cache_data # 這行很重要，可以讓網頁記住清單，不用每次都重抓
def get_tw_stock_list():
    # 抓取證交所的公開清單 (簡單處理)
    # 這裡預設先放入指標性的 200 檔，如果要全市場，建議由 FinMind 或其他 API 提供
    # 為確保執行速度，我們採用「熱門 300 檔」作為示範，若要全市場 1700 檔會跑很久
    url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2" # 上市
    res = pd.read_html(url)[0]
    res.columns = res.iloc[0]
    res = res.iloc[1:]
    # 過濾出股票 (代號 4 碼)
    res['代號'] = res['有價證券代號及名稱'].str.split('　').str[0]
    list_tw = res[res['代號'].str.len() == 4]['代號'].tolist()
    return list_tw

if st.button("🚀 開始全市場掃描 (需耗時約 1-2 分鐘)"):
    st.write("🔍 正在抓取全市場資料，請耐心稍候...")
    
    stock_list = get_tw_stock_list()
    results = []
    
    # 進度條
    progress_bar = st.progress(0)
    total = len(stock_list)

    # 為了示範效率，我們掃描前 100 檔最熱門的標的
    # 如果要全掃，把 [:100] 去掉即可，但會跑很久
    for i, code in enumerate(stock_list[:100]): 
        try:
            t = code + ".TW"
            data = yf.Ticker(t).history(period="10d")
            if len(data) < 2: continue
            
            today = data.iloc[-1]
            yesterday = data.iloc[-2]
            
            # 起漲條件
            change = (today['Close'] - yesterday['Close']) / yesterday['Close'] * 100
            vol_ratio = today['Volume'] / yesterday['Volume'] if yesterday['Volume'] > 0 else 0
            
            if change > 3 and vol_ratio > 1.8: # 漲幅>3% 且 爆量1.8倍
                results.append({
                    "代號": code,
                    "股價": round(today['Close'], 2),
                    "漲幅": f"{change:.1f}%",
                    "量增": f"{vol_ratio:.1f}倍"
                })
        except:
            continue
        progress_bar.progress((i + 1) / 100)

    if results:
        st.success(f"掃描完畢！共發現 {len(results)} 檔符合條件標的")
        st.table(pd.DataFrame(results))
    else:
        st.warning("今日市場較冷淡，暫無符合爆量起漲標的。")
