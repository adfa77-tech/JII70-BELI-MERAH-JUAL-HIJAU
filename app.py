import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import feedparser
from datetime import datetime
import pytz
import urllib.parse

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="JII70 Pro Screener & Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS (TEMA: HIJAU EMERALD, KUNING EMAS, PUTIH & GELAP ESTETIK) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #061a14 0%, #092e22 50%, #0f172a 100%) !important;
        color: #ffffff !important;
    }

    .glass-card {
        background: rgba(15, 35, 25, 0.85) !important;
        border: 1.5px solid rgba(74, 222, 128, 0.3) !important;
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 10px 25px 0 rgba(0, 0, 0, 0.5);
    }

    .header-box {
        background: linear-gradient(135deg, #065f46 0%, #047857 50%, #059669 100%);
        color: #ffffff !important;
        padding: 20px 24px;
        border-radius: 20px;
        margin-bottom: 24px;
        box-shadow: 0 12px 35px rgba(5, 150, 105, 0.4);
        border: 2px solid rgba(250, 204, 21, 0.4);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
    }
    .header-box h2, .header-box p, .header-box span, .header-box h3 {
        color: #ffffff !important;
    }

    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, .stMetric label, .stMetric div {
        color: #f8fafc !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        padding: 8px;
        border-radius: 16px;
        border: 1.5px solid rgba(74, 222, 128, 0.3);
        background: rgba(10, 25, 18, 0.9);
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 10px 18px;
        font-weight: 700;
        background-color: transparent !important;
        color: #f8fafc !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
        border: 1px solid #facc15;
    }
    .stTabs [aria-selected="true"] div p {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# --- DAFTAR 70 EMITEN JII70 ---
JII70_RAW = [
    'AADI', 'ACES', 'ADMR', 'ADRO', 'AKRA', 'ANTM', 'ARCI', 'AVIA', 'BKSL', 'BRIS', 
    'BRMS', 'BSDE', 'BTPS', 'BUMI', 'CMRY', 'CPIN', 'CTRA', 'DEWA', 'DKFT', 'DSNG', 
    'ELSA', 'ENRG', 'ERAA', 'ESSA', 'EXCL', 'HEAL', 'HRTA', 'HRUM', 'ICBP', 'IMPC', 
    'INDF', 'INDY', 'INKP', 'INTP', 'ISAT', 'ITMG', 'JPFA', 'JSMR', 'KIJA', 'KLBF', 
    'KPIG', 'LSIP', 'MAPA', 'MAPI', 'MARK', 'MBMA', 'MDKA', 'MEDC', 'MIKA', 'MTEL', 
    'MYOR', 'PGAS', 'PTBA', 'RAJA', 'RATU', 'SIDO', 'SMGR', 'SMRA', 'SRTG', 'SSIA', 
    'TAPG', 'TCPI', 'TINS', 'TKIM', 'TLKM', 'TOBA', 'TPIA', 'UNTR', 'UNVR', 'WIFI'
]
JII70_TICKERS = [f"{t}.JK" for t in JII70_RAW]

# --- INISIALISASI SESSION STATE ---
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["ADRO.JK", "ANTM.JK", "BRIS.JK", "ICBP.JK", "TLKM.JK"]

# --- FUNGSI FORMAT ANGKA INDONESIA ---
def fmt_id(val, prefix=""):
    if pd.isna(val) or val is None:
        return "-"
    return f"{prefix}{int(round(val)):,}".replace(",", ".")

def fmt_pct(val):
    if pd.isna(val) or val is None:
        return "-"
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.2f}%".replace(".", ",")

# --- WAKTU WIB REAL-TIME ---
def get_wib_time():
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz)
    hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][now.weekday()]
    return f"{hari}, {now.strftime('%d-%m-%Y | %H:%M:%S')} WIB"

# --- KONEKSI YFINANCE & ANALISIS (VERSI PERTAMA YANG AKURAT) ---
@st.cache_data(ttl=300)
def fetch_and_analyze_market(tickers):
    try:
        ihsg = yf.download("^JKSE", period="6m", interval="1d", progress=False)
        if isinstance(ihsg.columns, pd.MultiIndex):
            ihsg.columns = ihsg.columns.get_level_values(0)
        ihsg_last = float(ihsg['Close'].iloc[-1])
        ihsg_prev = float(ihsg['Close'].iloc[-2]) if len(ihsg) > 1 else ihsg_last
        ihsg_ret = (ihsg_last / float(ihsg['Close'].iloc[0]) - 1) * 100 if len(ihsg) >= 20 else 0
    except Exception:
        ihsg = pd.DataFrame({'Close': [7000, 7000]})
        ihsg_last = 7000.0
        ihsg_prev = 7000.0
        ihsg_ret = 0

    results = []
    for t in tickers:
        try:
            df = yf.download(t, period="6m", interval="1d", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna()
            if len(df) < 30:
                continue

            close = df['Close']
            high = df['High']
            low = df['Low']
            volume = df['Volume']

            curr_price = float(close.iloc[-1])
            prev_price = float(close.iloc[-2])
            chg_pct = ((curr_price - prev_price) / prev_price) * 100

            ma20 = float(close.rolling(20).mean().iloc[-1])
            ma50 = float(close.rolling(50).mean().iloc[-1] if len(df) >= 50 else ma20)
            ma150 = float(close.rolling(min(len(df), 150)).mean().iloc[-1])

            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = float((100 - (100 / (1 + rs))).iloc[-1])

            ret_stock = (curr_price / float(close.iloc[0]) - 1) * 100
            rs_score = round(50 + (ret_stock - ihsg_ret), 1)
            rs_score = max(1, min(99, rs_score))

            vol_ma20 = float(volume.rolling(20).mean().iloc[-1])
            vol_ratio = float(volume.iloc[-1] / vol_ma20) if vol_ma20 > 0 else 1.0
            
            support_20 = float(low.tail(20).min())
            resist_20 = float(high.tail(20).max())

            # --- STRATEGI DISIPLIN ---
            sinyal = "WAIT / PANTAU"
            strategi = "Konsolidasi Sehat"
            alasan = []
            waktu_eksekusi = "Pantau saat pembukaan atau sesi sore"

            if chg_pct < 0 and curr_price >= (ma50 * 0.93) and rs_score >= 40:
                sinyal = "STRONG BUY (BOW)"
                strategi = "Buy on Weakness (Diskon di Dekat Support)"
                alasan.append(f"Harga terkoreksi {chg_pct:.2f}% namun bertahan di area support MA50.")
                alasan.append(f"RS Rating solid di angka {rs_score}.")
                waktu_eksekusi = "Sesi 2 (14:30 - 15:50 WIB) saat harga melandai"
            elif chg_pct > 1.0 and vol_ratio > 1.2 and curr_price > ma20:
                sinyal = "STRONG BUY (MOMENTUM)"
                strategi = "Breakout Volume Tinggi"
                alasan.append(f"Kenaikan harga {chg_pct:.2f}% didukung lonjakan volume (Ratio: {vol_ratio:.2f}x).")
                waktu_eksekusi = "Sesi 1 (09:30 - 11:00 WIB)"
            elif chg_pct > 0.3 and vol_ratio > 1.05 and rsi < 75:
                sinyal = "BUY (DAYTRADE)"
                strategi = "Scalping Intraday Cepat"
                alasan.append("Volatilitas dan volume mendukung untuk trading harian.")
                waktu_eksekusi = "Sesi 1 / Awal Sesi 2"
            elif rsi < 60 and curr_price >= ma20:
                sinyal = "BUY (SWING TRADING)"
                strategi = "Pantulan Sehat di atas MA20"
                alasan.append("Harga di atas MA20 dengan RSI tidak jenuh beli.")
                waktu_eksekusi = "Menjelang penutupan pasar"
            elif rsi > 80 or (curr_price < ma20 and chg_pct < -2.5):
                sinyal = "SELL / TAKE PROFIT"
                strategi = "Amankan Profit / Batasi Risiko"
                alasan.append(f"RSI jenuh beli tinggi ({rsi:.1f}) atau breakdown MA20.")
                waktu_eksekusi = "Sesi pagi (09:00 - 09:30 WIB)"
            else:
                alasan.append("Pergerakan konsolidasi dalam kisaran normal.")

            buy_low = support_20 if "BOW" in sinyal else curr_price * 0.985
            buy_high = curr_price * 1.005
            target_1 = resist_20 if resist_20 > curr_price * 1.03 else curr_price * 1.05
            target_2 = curr_price * 1.10
            stop_loss = min(support_20 * 0.98, curr_price * 0.94)

            results.append({
                "Kode": t.replace(".JK", ""),
                "Ticker": t,
                "Harga": curr_price,
                "Perubahan (%)": chg_pct,
                "Sinyal": sinyal,
                "Strategi": strategi,
                "RS Rating": rs_score,
                "RSI (14)": round(rsi, 1),
                "Vol Ratio": round(vol_ratio, 2),
                "MA20": ma20,
                "MA50": ma50,
                "MA150": ma150,
                "Area Beli": f"{fmt_id(buy_low)} - {fmt_id(buy_high)}",
                "Target Jual 1": target_1,
                "Target Jual 2": target_2,
                "Stop Loss": stop_loss,
                "Waktu Eksekusi": waktu_eksekusi,
                "Alasan": " ".join(alasan)
            })
        except Exception:
            continue

    df_res = pd.DataFrame(results)
    return df_res, ihsg, ihsg_last, ihsg_prev

# --- FUNGSI GRAFIK CANDLESTICK 6 BULAN (LAYAR PENUH) ---
def plot_candlestick_6m(ticker, title_name):
    df = yf.download(ticker, period="6m", interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.dropna()

    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA150'] = df['Close'].rolling(min(len(df), 150)).mean()

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.05, row_heights=[0.75, 0.25]
    )

    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name="Harga",
        increasing_line_color='#22c55e', decreasing_line_color='#ef4444'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#38bdf8', width=1.5), name='MA 20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], line=dict(color='#facc15', width=1.5), name='MA 50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA150'], line=dict(color='#a855f7', width=1.8), name='MA 150'), row=1, col=1)

    colors = ['#22c55e' if c >= o else '#ef4444' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume'), row=2, col=1)

    fig.update_layout(
        title=dict(text=f"Grafik Candlestick 6 Bulan: {title_name}", font=dict(size=16, color="#ffffff")),
        xaxis_rangeslider_visible=False,
        height=600,
        paper_bgcolor='rgba(10, 25, 18, 0.9)',
        plot_bgcolor='rgba(10, 25, 18, 0.9)',
        font=dict(color="#ffffff"),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# --- BERITA TERKINI ---
@st.cache_data(ttl=600)
def fetch_stock_news(query="saham syariah JII70 IHSG"):
    encoded_q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl=id&gl=ID&ceid=ID:id"
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:12]:
        articles.append({
            "judul": entry.title,
            "link": entry.link,
            "sumber": entry.source.title if hasattr(entry, 'source') else "Berita Pasar",
            "waktu": entry.published if hasattr(entry, 'published') else ""
        })
    return articles

# --- AMBIL DATA PASAR ---
with st.spinner("Memindai 70 emiten JII70 dari Yahoo Finance..."):
    df_screener, df_ihsg, ihsg_last, ihsg_prev = fetch_and_analyze_market(JII70_TICKERS)

# --- HEADER UTAMA ---
ihsg_chg = ((ihsg_last - ihsg_prev) / ihsg_prev) * 100 if ihsg_prev > 0 else 0
chg_color = "#4ade80" if ihsg_chg >= 0 else "#f87171"
chg_sign = "+" if ihsg_chg >= 0 else ""
ihsg_str = f"{ihsg_last:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.markdown(f"""
<div class="header-box">
    <div>
        <h2 style="margin:0; font-weight:800; color:#ffffff !important;">📊 JII70 QUANTUM SCREENER PRO</h2>
        <p style="margin:4px 0 0 0; font-size:0.88rem; color:#facc15 !important;">Yahoo Finance Official Data • 70 Emiten Syariah JII70</p>
    </div>
    <div style="text-align: right;">
        <p style="margin:0; font-size:0.75rem; color:#facc15; font-weight:700;">IHSG TERKINI</p>
        <h3 style="margin:2px 0; font-size:1.3rem; color:#ffffff !important;">{ihsg_str} <span style="font-size:0.9rem; color:{chg_color};">({chg_sign}{ihsg_chg:.2f}%)</span></h3>
    </div>
</div>
""", unsafe_allow_html=True)

col_ref1, col_ref2 = st.columns([1, 5])
with col_ref1:
    if st.button("🔄 Refresh Data Live", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- NAVIGASI TAB ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔍 Screener & Sinyal",
    "🕯️ Chart Candlestick 6 Bulan",
    "🏢 Profil Perusahaan",
    "⭐ Watchlist Pilihan",
    "🧮 Kalkulator Trading",
    "📰 Berita Saham Terkini"
])

# ==============================================================================
# TAB 1: SCREENER & REKOMENDASI
# ==============================================================================
with tab1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    
    total_emiten = len(df_screener) if 'Sinyal' in df_screener.columns else 0
    strong_buy_cnt = len(df_screener[df_screener['Sinyal'].str.contains('STRONG BUY')]) if 'Sinyal' in df_screener.columns else 0
    bow_cnt = len(df_screener[df_screener['Sinyal'].str.contains('BOW')]) if 'Sinyal' in df_screener.columns else 0
    
    c1.metric("Total Emiten Terpantau", f"{total_emiten} Saham")
    c2.metric("Sinyal Strong Buy", f"{strong_buy_cnt} Saham")
    c3.metric("Peluang Buy on Weakness", f"{bow_cnt} Saham")
    c4.metric("Waktu Pemindaian", get_wib_time())
    st.markdown('</div>', unsafe_allow_html=True)

    f_col1, f_col2, f_col3 = st.columns([2, 2, 2])
    with f_col1:
        filter_sinyal = st.selectbox("Filter Sinyal Trading:", [
            "Semua Saham", "STRONG BUY (Semua)", "STRONG BUY (BOW)", "STRONG BUY (MOMENTUM)", "BUY (DAYTRADE)", "BUY (SWING TRADING)", "SELL / TAKE PROFIT"
        ])
    with f_col2:
        min_rs = st.slider("Minimal RS Rating (Kekuatan vs IHSG):", 1, 99, 25)
    with f_col3:
        kondisi_harga = st.selectbox("Kondisi Harga Hari Ini:", ["Semua Kondisi", "Saham Merah (Koreksi)", "Saham Hijau (Naik)"])

    if 'Sinyal' in df_screener.columns:
        df_filtered = df_screener[df_screener['RS Rating'] >= min_rs].copy()
        if filter_sinyal == "STRONG BUY (Semua)":
            df_filtered = df_filtered[df_filtered['Sinyal'].str.contains("STRONG BUY")]
        elif filter_sinyal != "Semua Saham":
            df_filtered = df_filtered[df_filtered['Sinyal'] == filter_sinyal]

        if kondisi_harga == "Saham Merah (Koreksi)":
            df_filtered = df_filtered[df_filtered['Perubahan (%)'] < 0]
        elif kondisi_harga == "Saham Hijau (Naik)":
            df_filtered = df_filtered[df_filtered['Perubahan (%)'] > 0]

        df_filtered = df_filtered.sort_values(by="RS Rating", ascending=False)
    else:
        df_filtered = pd.DataFrame()

    st.markdown("### 📋 Hasil Pemindaian & Rekomendasi Eksekusi")
    if df_filtered.empty:
        st.info("Tidak ada saham yang memenuhi kriteria filter saat ini.")
    else:
        display_df = df_filtered[[
            "Kode", "Harga", "Perubahan (%)", "Sinyal", "Strategi",
            "RS Rating", "RSI (14)", "Vol Ratio", "Area Beli", "Target Jual 1", "Stop Loss"
        ]].copy()

        display_df["Harga"] = display_df["Harga"].apply(fmt_id)
        display_df["Target Jual 1"] = display_df["Target Jual 1"].apply(fmt_id)
        display_df["Stop Loss"] = display_df["Stop Loss"].apply(fmt_id)
        display_df["Perubahan (%)"] = display_df["Perubahan (%)"].apply(fmt_pct)

        def style_table(row):
            styles = [''] * len(row)
            styles[0] = 'background-color: #064e3b; font-weight: bold; color: #facc15;'
            if "BUY" in str(row["Sinyal"]):
                styles[3] = 'background-color: #022c22; color: #4ade80; font-weight: bold;'
            elif "SELL" in str(row["Sinyal"]):
                styles[3] = 'background-color: #450a0a; color: #f87171; font-weight: bold;'
            else:
                styles[3] = 'background-color: #422006; color: #facc15;'
            if "+" in str(row["Perubahan (%)"]):
                styles[2] = 'color: #4ade80; font-weight: bold;'
            elif "-" in str(row["Perubahan (%)"]):
                styles[2] = 'color: #f87171; font-weight: bold;'
            return styles

        st.dataframe(
            display_df.style.apply(style_table, axis=1),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### 🎯 Detail Rencana Trading & Alasan Buy/Sell")
        pilih_detail = st.selectbox("Pilih Kode Saham:", df_filtered["Kode"].tolist())
        row_det = df_filtered[df_filtered["Kode"] == pilih_detail].iloc[0]

        st.markdown(f"""
        <div class="glass-card">
            <h4 style="margin-top:0; color:#facc15;">{row_det['Kode']} — <span style="background:#064e3b; color:#4ade80; padding:4px 8px; border-radius:6px;">{row_det['Sinyal']}</span></h4>
            <p><b>Strategi Utama:</b> {row_det['Strategi']}</p>
            <p><b>Alasan Teknis & Kuantitatif:</b> {row_det['Alasan']}</p>
            <ul>
                <li><b>Zona Harga Beli Ideal:</b> Rp {row_det['Area Beli']}</li>
                <li><b>Target Jual 1 (Konservatif):</b> {fmt_id(row_det['Target Jual 1'], 'Rp ')}</li>
                <li><b>Target Jual 2 (Optimis):</b> {fmt_id(row_det['Target Jual 2'], 'Rp ')}</li>
                <li><b>Batas Stop Loss Ketat:</b> {fmt_id(row_det['Stop Loss'], 'Rp ')}</li>
                <li><b>Rekomendasi Waktu Eksekusi:</b> {row_det['Waktu Eksekusi']}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"➕ Tambahkan {pilih_detail} ke Watchlist"):
            ticker_full = f"{pilih_detail}.JK"
            if ticker_full not in st.session_state.watchlist:
                st.session_state.watchlist.append(ticker_full)
                st.success(f"{pilih_detail} berhasil ditambahkan ke Watchlist!")
            else:
                st.warning(f"{pilih_detail} sudah ada di Watchlist.")

# ==============================================================================
# TAB 2: CHART CANDLESTICK 6 BULAN (LAYAR PENUH)
# ==============================================================================
with tab2:
    st.markdown("### 🕯️ Grafik Candlestick & Indikator Teknikal (6 Bulan)")
    saham_chart = st.selectbox("Pilih Emiten untuk Dilihat Chart-nya:", JII70_RAW, index=0)
    fig_saham = plot_candlestick_6m(f"{saham_chart}.JK", f"Saham {saham_chart}")
    st.plotly_chart(fig_saham, use_container_width=True)

# ==============================================================================
# TAB 3: PROFIL PERUSAHAAN
# ==============================================================================
with tab3:
    saham_profil = st.selectbox("Pilih Emiten:", JII70_RAW, key="prof_sel")
    ticker_obj = yf.Ticker(f"{saham_profil}.JK")
    info = ticker_obj.info

    raw_summary = info.get('longBusinessSummary', 'Deskripsi profil perusahaan sedang tidak tersedia.')
    id_summary = raw_summary
    if "engaged in" in raw_summary or "operates as" in raw_summary or "provides" in raw_summary:
        id_summary = f"{info.get('longName', saham_profil)} merupakan emiten syariah terdaftar di Bursa Efek Indonesia dalam sektor {info.get('sector', '-')} (industri {info.get('industry', '-')}). Ringkasan operasional berdasarkan referensi pasar: {raw_summary}"

    st.markdown(f"""
    <div class="glass-card">
        <h3 style="margin-top:0; color:#facc15;">🏢 {info.get('longName', saham_profil)} ({saham_profil})</h3>
        <p><b>Sektor:</b> {info.get('sector', '-')} | <b>Industri:</b> {info.get('industry', '-')}</p>
        <p><b>Situs Web Resmi:</b> <a href="{info.get('website', '#')}" target="_blank" style="color:#4ade80;">{info.get('website', '-')}</a></p>
        <hr style="border-color: rgba(74,222,128,0.2);">
        <p style="text-align:justify; line-height:1.6; color:#f8fafc;">{id_summary}</p>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Kapitalisasi Pasar", fmt_id(info.get('marketCap'), "Rp "))
    m2.metric("PER (Trailing)", f"{info.get('trailingPE', 0):.2f}x" if info.get('trailingPE') else "-")
    m3.metric("PBV", f"{info.get('priceToBook', 0):.2f}x" if info.get('priceToBook') else "-")
    m4.metric("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "-")

# ==============================================================================
# TAB 4: WATCHLIST
# ==============================================================================
with tab4:
    st.markdown("### ⭐ Daftar Pantauan (Watchlist) Anda")
    c_wl1, c_wl2 = st.columns([3, 1])
    with c_wl1:
        tambah_wl = st.selectbox("Tambah Saham ke Watchlist:", JII70_RAW, key="add_wl")
    with c_wl2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("Tambah", use_container_width=True):
            if f"{tambah_wl}.JK" not in st.session_state.watchlist:
                st.session_state.watchlist.append(f"{tambah_wl}.JK")
                st.rerun()

    if 'Ticker' in df_screener.columns:
        df_wl = df_screener[df_screener["Ticker"].isin(st.session_state.watchlist)].copy()
    else:
        df_wl = pd.DataFrame()

    if df_wl.empty:
        st.info("Watchlist masih kosong.")
    else:
        for _, r in df_wl.iterrows():
            col_w1, col_w2, col_w3, col_w4, col_w5 = st.columns([2, 2, 3, 3, 1])
            col_w1.markdown(f"**{r['Kode']}** ({fmt_id(r['Harga'], 'Rp ')})")
            col_w2.markdown(f"Perubahan: **{fmt_pct(r['Perubahan (%)'])}**")
            col_w3.markdown(f"Sinyal: **{r['Sinyal']}**")
            col_w4.markdown(f"Target: **{fmt_id(r['Target Jual 1'], 'Rp ')}** | SL: **{fmt_id(r['Stop Loss'], 'Rp ')}**")
            if col_w5.button("🗑️", key=f"del_{r['Kode']}"):
                st.session_state.watchlist.remove(r['Ticker'])
                st.rerun()
            st.divider()

# ==============================================================================
# TAB 5: KALKULATOR TRADING SAHAM
# ==============================================================================
with tab5:
    st.markdown("### 🧮 Kalkulator Profit & Fee Transaksi Saham")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    nama_saham_manual = st.text_input("Nama atau Kode Saham (Isi Manual):", value="ADRO")
    
    k1, k2, k3 = st.columns(3)
    with k1:
        harga_beli = st.number_input("Harga Beli (Rp):", min_value=1, value=1000, step=5)
        jumlah_lot = st.number_input("Jumlah Lot:", min_value=1, value=10, step=1)
    with k2:
        harga_jual = st.number_input("Target Harga Jual (Rp):", min_value=1, value=1100, step=5)
        fee_beli_pct = st.number_input("Fee Beli (%):", min_value=0.0, value=0.15, step=0.01, format="%.2f")
    with k3:
        fee_jual_pct = st.number_input("Fee Jual + Pajak (%):", min_value=0.0, value=0.25, step=0.01, format="%.2f")

    total_lembar = jumlah_lot * 100
    nilai_beli_kotor = harga_beli * total_lembar
    biaya_fee_beli = nilai_beli_kotor * (fee_beli_pct / 100)
    total_modal_keluar = nilai_beli_kotor + biaya_fee_beli

    nilai_jual_kotor = harga_jual * total_lembar
    biaya_fee_jual = nilai_jual_kotor * (fee_jual_pct / 100)
    total_dana_diterima = nilai_jual_kotor - biaya_fee_jual

    profit_bersih = total_dana_diterima - total_modal_keluar
    roi_bersih = (profit_bersih / total_modal_keluar) * 100 if total_modal_keluar > 0 else 0
    total_fee = biaya_fee_beli + biaya_fee_jual

    st.markdown("<hr style='border-color: rgba(74,222,128,0.3);'>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='color:#facc15;'>Simulasi Perhitungan untuk Saham: {nama_saham_manual.upper()}</h4>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#cbd5e1;'>Jumlah Lot: <b>{jumlah_lot}</b> ({total_lembar:,} Lembar)</p>".replace(",", "."), unsafe_allow_html=True)
    
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Total Modal Beli", fmt_id(total_modal_keluar, "Rp "))
    r2.metric("Total Hasil Jual", fmt_id(total_dana_diterima, "Rp "))
    r3.metric("Total Fee Transaksi", fmt_id(total_fee, "Rp "))
    r4.metric("Profit Bersih", fmt_id(profit_bersih, "Rp "), fmt_pct(roi_bersih))
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# TAB 6: BERITA TERKINI
# ==============================================================================
with tab6:
    st.markdown("### 📰 Berita Pasar Modal & Emiten Terkini")
    topik_berita = st.text_input("Cari Berita Emiten:", value="saham syariah IHSG")
    daftar_berita = fetch_stock_news(topik_berita)

    if not daftar_berita:
        st.warning("Belum ada berita terbaru.")
    else:
        for b in daftar_berita:
            st.markdown(f"""
            <div class="glass-card" style="padding:14px;">
                <a href="{b['link']}" target="_blank" style="text-decoration:none; color:#facc15; font-weight:700; font-size:1.02rem;">
                    {b['judul']}
                </a>
                <p style="margin:6px 0 0 0; font-size:0.8rem; color:#cbd5e1;">
                    Sumber: <b>{b['sumber']}</b> • {b['waktu']}
                </p>
            </div>
            """, unsafe_allow_html=True)
    
