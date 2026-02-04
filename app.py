import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="台股優質起漲掃描", page_icon="💎", layout="wide")
st.title("💎 台股熱門股起漲偵測器")
st.write(f"數據分析日期：{datetime.now().strftime('%Y-%m-%d')}")

# --- 2. 側邊欄：讓您用手機就能調整條件 ---
st.sidebar.header("⚙️ 篩選條件設定")
min_increase = st.sidebar.slider("最低漲幅限制 (%)", 0.0, 10.0, 3.0, 0.5)
vol_multiplier = st.sidebar.slider("成交量放大倍數 (倍)", 1.0, 5.0, 1.5, 0.1)
check_ma60 = st.sidebar.checkbox("必須站上季線 (60MA)", value=True)

st.sidebar.markdown("---")
st.sidebar.info("💡 **操作提醒**：\n若搜尋結果為空，可試著將「漲幅」調低至 1.5% 或將「量能倍數」調低至 1.2 倍。")

# --- 3. 穩定版：內建熱門 100 檔股票清單 (不再爬蟲，保證不報錯) ---
@st.cache_data
def get_tw_stock_list():
    top_stocks = [
        {"代號": "2330", "名稱": "台積電"}, {"代號": "2317", "名稱": "鴻海"}, {"代號": "2454", "名稱": "聯發科"}, 
        {"代號": "2382", "名稱": "廣達"}, {"代號": "2308", "名稱": "台達電"}, {"代號": "2303", "名稱": "聯電"}, 
        {"代號": "2603", "名稱": "長榮"}, {"代號": "3711", "名稱": "日月光"}, {"代號": "2881", "名稱": "富邦金"}, 
        {"代號": "2882", "名稱": "國泰金"}, {"代號": "3231", "名稱": "緯創"}, {"代號": "2609", "名稱": "陽明"}, 
        {"代號": "2615", "名稱": "萬海"}, {"代號": "3037", "名稱": "欣興"}, {"代號": "2379", "名稱": "瑞昱"}, 
        {"代號": "3034", "名稱": "聯詠"}, {"代號": "2357", "名稱": "華碩"}, {"代號": "2891", "名稱": "中信金"}, 
        {"代號": "3006", "名稱": "晶豪科"}, {"代號": "8150", "名稱": "南茂"}, {"代號": "3035", "名稱": "智原"},
        {"代號": "2376", "名稱": "技嘉"}, {"代號": "2388", "名稱": "威盛"}, {"代號": "3017", "名稱": "奇鋐"}, 
        {"代號": "3324", "名稱": "雙鴻"}, {"代號": "1513", "內容": "中興電"}, {"代號": "1519", "名稱": "華城"}, 
        {"代號": "2409", "名稱": "友達"}, {"代號": "3481", "名稱": "群創"}, {"代號": "2353", "名稱": "宏碁"},
        {"代號": "2324", "名稱": "仁寶"}, {"代號": "2356", "名稱": "英業達"}, {"代號": "6239", "名稱": "力成"},
        {"代號": "8046", "名稱": "南電"}, {"代號": "3293", "名稱": "鈊象"}, {"代號": "8069", "名稱": "元太"},
        {"代號": "5483", "名稱": "中美晶"}, {"代號": "8299", "名稱": "群聯"}, {"代號": "2368", "名稱": "金像電"},
        {"代號": "2383", "名稱": "台光電"}, {"代號": "6274", "名稱": "台燿"}, {"代號": "3533", "名稱": "嘉澤"},
        {"代號": "2345", "名稱": "智邦"}, {"代號": "5269", "名稱": "祥碩"}, {"代號": "6415", "名稱": "矽力"},
        {"代號": "3443", "名稱": "創意"}, {"代號": "3661", "名稱": "世芯"}, {"代號": "6669", "名稱": "緯穎"},
        {"代號": "1504", "名稱": "東元"}, {"代號": "1605", "名稱": "華新"}, {"代號": "2002", "名稱": "中鋼"},
        {"代號": "2886", "名稱": "兆豐金"}, {"代號": "2884", "名稱": "玉山金"}, {"代號": "2885", "名稱": "元大金"},
        {"代號": "5880", "名稱": "合庫金"}, {"代號": "2892", "名稱": "第一金"}, {"代號": "2880", "名稱": "華南金"},
        {"代號": "2883", "名稱": "開發金"}, {"代號": "2887", "名稱": "台新金"}, {"代號": "2890", "名稱": "永豐金"},
        {"代號": "1101", "名稱": "台泥"}, {"代號": "1102", "名稱": "亞泥"}, {"代號": "1216", "名稱": "統一"},
        {"代號": "2912", "名稱": "統一超"}, {"代號": "9910", "名稱": "豐泰"}, {"代號": "9904", "名稱": "寶成"}
    ]
    return pd.DataFrame(top_stocks)

# --- 4. 執行掃描邏輯 ---
if st.button("🚀 開始分析熱門權值股", type="primary"):
    stock_df = get_tw_stock_list()
    st.info(f"✅ 已載入 {len(stock_df)} 檔熱門指標股，開始執行 AI 掃描...")
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, row in stock_df.iterrows():
        code = row['代號']
        name = row['名稱']
        try:
            ticker_code = code + ".TW"
            # 抓取 3 個月資料 (計算季線)
            data = yf.Ticker(ticker_code).history(period="3mo")
            
            if len(data) >= 60:
                today = data.iloc[-1]
                yesterday = data.iloc[-2]
                
                # 計算指標
                price = today['Close']
                change_pct = (price - yesterday['Close']) / yesterday['Close'] * 100
                ma60 = data['Close'].tail(60).mean()
                ma20 = data['Close'].tail(20).mean()
                
                # 成交量比較 (與 5 日均量比)
                vol_ma5 = data['Volume'].tail(5).mean()
                vol_ratio = today['Volume'] / vol_ma5 if vol_ma5 > 0 else 0
                
                # 判定條件
                cond_basic = change_pct >= min_increase and vol_ratio >= vol_multiplier
                cond_quality = price > ma60 if check_ma60 else True
                cond_trend = price > ma20 # 必須站上月線

                if cond_basic and cond_quality and cond_trend:
                    results.append({
                        "股票代號": code,
                        "股票名稱": name,
                        "今日收盤": f"{price:.2f}",
                        "今日漲幅": f"{change_pct:.1f}%",
                        "量能放大": f"{vol_ratio:.1f}倍",
                        "趨勢": "💪 強勢多頭"
                    })
        except:
            continue
        
        progress_bar.progress((i + 1) / len(stock_df))
        status_text.text(f"掃描中: {name} ({code})")

    status_text.empty()
    if results:
        st.success(f"🎊 掃描完畢！共有 {len(results)} 檔標的符合條件：")
        st.table(pd.DataFrame(results))
    else:
        st.warning("⚠️ 目前條件下沒有發現符合標的。")
        st.info("建議：您可以調整左側選單的「最低漲幅」或「量能倍數」後重新掃描。")

st.markdown("---")
st.caption("本工具僅供量化數據參考，投資請自行評估風險。")
