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

# --- CUSTOM CSS (GLASSMORPHISM & MOBILE FRIENDLY) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Latar Belakang Utama */
    .stApp {
        background: linear-gradient(135deg, #f0f4ff 0%, #e6f0fa 50%, #f5f0ff 100%);
    }

    /* Glassmorphism Card */
    .glass-card {
        background: rgba(255, 255, 255, 0.78);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.9);
        padding: 18px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        margin-bottom: 16px;
    }

    /* Header Banner */
    .header-box {
        background: linear-gradient(90deg, #1e3a8a 0%, #2563eb 50%, #0d9488 100%);
        color: white;
        padding: 18px 24px;
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px rgba(37, 99, 235, 0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
    }

    /* Navigasi Tab Atas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(255, 255, 255, 0.65);
        padding: 8px;
        border-radius: 14px;
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 8px 16px;
        font-weight: 700;
        color: #1e293b;
        background-color: transparent;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #2563eb, #0284c7) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }

    /* Badge Status */
    .badge-buy { background-color: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 8px; font-weight: 700; font-size: 0.85rem; }
    .badge-sell { background-color: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 8px; font-weight: 700; font-size: 0.85rem; }
    .badge-wait { background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 8px; font-weight: 700; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# --- DAFTAR EMITEN JII70 (REPRESENTATIF UTAMA) ---
JII70_TICKERS = [
    "ADRO.JK", "AKRA.JK", "AMMN.JK", "ANTM.JK", "ASII.JK", "BRIS.JK", "BRPT.JK",
    "CPIN.JK", "CTRA.JK", "DSNG.JK", "ELSA.JK", "EMTK.JK", "ENRG.JK", "ERAA.JK",
    "EXCL.JK", "HEAL.JK", "HRUM.JK", "ICBP.JK", "INCO.JK", "INDF.JK", "INDY.JK",
    "INKP.JK", "INTP.JK", "ISAT.JK", "ITMG.JK", "JPFA.JK", "JSMR.JK", "KLBF.JK",
    "MAPI.JK", "MBMA.JK", "MDKA.JK", "MEDC.JK", "MIKA.JK", "MNCN.JK", "MTEL.JK",
    "MYOR.JK", "NCKL.JK", "PGAS.JK", "PGEO.JK", "PTBA.JK", "PTPP.JK", "PWON.JK",
    "RAJA.JK", "SCMA.JK", "SIDO.JK", "SILO.JK", "SMGR.JK", "SMRA.JK", "TAPG.JK",
    "TINS.JK", "TLKM.JK", "TPIA.JK", "UNTR.JK", "UNVR.JK", "WIKA.JK"
]

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

# --- MESIN ANALISIS KUANTITATIF & TEKNIKAL ---
@st.cache_data(ttl=300)
def fetch_and_analyze_market(tickers):
    # Ambil data IHSG 1 tahun untuk perbandingan RS Rating
    ihsg = yf.download("^JKSE", period="1y", interval="1d", progress=False)
    if isinstance(ihsg.columns, pd.MultiIndex):
        ihsg.columns = ihsg.columns.get_level_values(0)
    ihsg_ret_3m = (ihsg['Close'].iloc[-1] / ihsg['Close'].iloc[-63] - 1) * 100 if len(ihsg) >= 63 else 0

    # Ambil data seluruh saham sekaligus
    raw_data = yf.download(tickers, period="1y", interval="1d", group_by='ticker', progress=False)
    results = []

    for t in tickers:
        try:
            df = raw_data[t].dropna()
            if len(df) < 150:
                continue

            close = df['Close']
            high = df['High']
            low = df['Low']
            volume = df['Volume']

            curr_price = close.iloc[-1]
            prev_price = close.iloc[-2]
            chg_pct = ((curr_price - prev_price) / prev_price) * 100

            # Moving Averages
            ema9 = close.ewm(span=9, adjust=False).mean().iloc[-1]
            ma20 = close.rolling(20).mean().iloc[-1]
            ma50 = close.rolling(50).mean().iloc[-1]
            ma150 = close.rolling(150).mean().iloc[-1]
            ma200 = close.rolling(200).mean().iloc[-1] if len(df) >= 200 else ma150

            # RSI (14)
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = (100 - (100 / (1 + rs))).iloc[-1]

            # Relative Strength vs IHSG (3 Bulan)
            ret_3m = (curr_price / close.iloc[-63] - 1) * 100
            rs_score = round(50 + (ret_3m - ihsg_ret_3m), 1)
            rs_score = max(1, min(99, rs_score))

            # Volume Ratio & VCP (Kontraksi Volatilitas)
            vol_ma20 = volume.rolling(20).mean().iloc[-1]
            vol_ratio = volume.iloc[-1] / vol_ma20 if vol_ma20 > 0 else 1.0
            atr_10 = (high - low).rolling(10).mean().iloc[-1]
            atr_50 = (high - low).rolling(50).mean().iloc[-1]
            is_vcp = atr_10 < (0.75 * atr_50)

            # Support & Resistance 20 Hari
            support_20 = low.tail(20).min()
            resist_20 = high.tail(20).max()

            # --- LOGIKA REKOMENDASI & ALASAN ---
            sinyal = "WAIT / PANTAU"
            strategi = "Konsolidasi"
            alasan = []
            waktu_eksekusi = "Tunggu konfirmasi penutupan sesi 2 (15:50 WIB)"

            # 1. Strategi Buy on Weakness (Merah/Koreksi di Uptrend Kuat)
            if curr_price > ma150 and chg_pct < 0 and (abs(curr_price - ma20)/ma20 <= 0.03 or abs(curr_price - ma50)/ma50 <= 0.03) and vol_ratio < 0.9:
                sinyal = "STRONG BUY (BOW)"
                strategi = "Buy on Weakness (Pantulan Support)"
                alasan.append("Harga terkoreksi sehat ke area support kuat MA20/MA50 dengan volume mengecil (tidak ada distribusi besar).")
                alasan.append("Tren utama jangka panjang masih bullish di atas MA150.")
                waktu_eksekusi = "Sesi 2 (15:30 - 15:55 WIB) jika muncul ekor bawah / pantulan"

            # 2. Strategi Breakout VCP / Momentum
            elif curr_price > ma20 and ma20 > ma50 and vol_ratio > 1.3 and chg_pct > 1.0:
                sinyal = "STRONG BUY (BREAKOUT)"
                strategi = "Momentum & Breakout"
                alasan.append(f"Lonjakan volume {vol_ratio:.1f}x rata-rata harian disertai penguatan harga.")
                if is_vcp:
                    alasan.append("Terdeteksi pola penyempitan volatilitas (VCP) sebelum ledakan harga.")
                waktu_eksekusi = "Sesi 1 (09:30 - 10:30 WIB) atau saat menembus resistance"

            # 3. Strategi BSJP (Beli Sore Jual Pagi)
            elif curr_price > ema9 and chg_pct > 1.5 and rsi < 72 and vol_ratio > 1.1:
                sinyal = "BUY (BSJP / SWING)"
                strategi = "Beli Sore Jual Pagi / Swing Pendek"
                alasan.append("Harga ditutup kuat di atas EMA 9 dengan momentum RSI sehat.")
                waktu_eksekusi = "Pre-closing (15:50 WIB), target jual pagi besok (09:05 - 09:45 WIB)"

            # 4. Sinyal Jual / Take Profit / Cut Loss
            elif rsi > 78 or (curr_price < ma20 and chg_pct < -2.5 and vol_ratio > 1.2):
                sinyal = "SELL / TAKE PROFIT"
                strategi = "Amankan Profit / Hindari"
                if rsi > 78:
                    alasan.append(f"RSI sudah jenuh beli ({rsi:.1f}), rawan koreksi jangka pendek.")
                else:
                    alasan.append("Harga jebol ke bawah MA20 disertai lonjakan volume jual.")
                waktu_eksekusi = "Segera pada pembukaan pasar (09:00 - 09:30 WIB)"
            else:
                alasan.append("Harga masih bergerak di area tengah tanpa konfirmasi volume breakout maupun diskon support.")

            # Penentuan Harga Entry, Target Profit, dan Stop Loss
            buy_low = support_20 if "BOW" in sinyal else curr_price * 0.99
            buy_high = curr_price * 1.005
            target_1 = resist_20 if resist_20 > curr_price * 1.04 else curr_price * 1.06
            target_2 = curr_price * 1.12
            stop_loss = min(support_20 * 0.98, curr_price * 0.95)

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

    return pd.DataFrame(results), ihsg

# --- FUNGSI GRAFIK CANDLESTICK 1 TAHUN ---
def plot_candlestick_1y(ticker, title_name):
    df = yf.download(ticker, period="1y", interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.dropna()

    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA150'] = df['Close'].rolling(150).mean()

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.05, row_heights=[0.75, 0.25]
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name="Harga",
        increasing_line_color='#16a34a', decreasing_line_color='#dc2626'
    ), row=1, col=1)

    # Moving Averages
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#2563eb', width=1.5), name='MA 20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], line=dict(color='#f59e0b', width=1.5), name='MA 50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA150'], line=dict(color='#7c3aed', width=1.8), name='MA 150'), row=1, col=1)

    # Volume Bar
    colors = ['#16a34a' if c >= o else '#dc2626' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume'), row=2, col=1)

    fig.update_layout(
        title=dict(text=f"Grafik Candlestick 1 Tahun: {title_name}", font=dict(size=16, color="#1e293b")),
        xaxis_rangeslider_visible=False,
        height=520,
        margin=dict(l=10, r=10, t=45, b=10),
        paper_bgcolor='rgba(255,255,255,0.85)',
        plot_bgcolor='rgba(248,250,252,0.9)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# --- FUNGSI BERITA TERKINI (GOOGLE NEWS RSS) ---
@st.cache_data(ttl=600)
def fetch_stock_news(query="saham JII70 IHSG bursa efek"):
    encoded_q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl=id&gl=ID&ceid=ID:id"
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:12]:
        articles.append({
            "judul": entry.title,
            "link": entry.link,
            "sumber": entry.source.title if hasattr(entry, 'source') else "Berita Pasar Modal",
            "waktu": entry.published if hasattr(entry, 'published') else ""
        })
    return articles

# --- HEADER APLIKASI ---
st.markdown(f"""
<div class="header-box">
    <div>
        <h2 style="margin:0; font-weight:800; letter-spacing:-0.5px;">📊 JII70 QUANTUM SCREENER PRO</h2>
        <p style="margin:4px 0 0 0; font-size:0.9rem; opacity:0.9;">Real-Time Yahoo Finance • Analisis RS Rating, VCP & Buy on Weakness</p>
    </div>
    <div style="text-align:right;">
        <span style="background:rgba(255,255,255,0.2); padding:6px 12px; border-radius:10px; font-weight:600; font-size:0.85rem;">
            🕒 {get_wib_time()}
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# Tombol Refresh Data
col_ref1, col_ref2 = st.columns([1, 5])
with col_ref1:
    if st.button("🔄 Refresh Data Live", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with st.spinner("Mengambil data pasar real-time dari Yahoo Finance..."):
    df_screener, df_ihsg = fetch_and_analyze_market(JII70_TICKERS)

# --- NAVIGASI UTAMA ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔍 Screener & Sinyal",
    "🕯️ Chart 1 Tahun (Saham & IHSG)",
    "🏢 Profil Perusahaan",
    "⭐ Watchlist Pilihan",
    "🧮 Kalkulator Trading",
    "📰 Berita Saham Terkini"
])

# ==============================================================================
# TAB 1: SCREENER & REKOMENDASI BUY/SELL
# ==============================================================================
with tab1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Emiten Terpantau", f"{len(df_screener)} Saham")
    c2.metric("Sinyal Strong Buy", f"{len(df_screener[df_screener['Sinyal'].str.contains('STRONG BUY')])} Saham")
    c3.metric("Peluang Buy on Weakness", f"{len(df_screener[df_screener['Sinyal'].str.contains('BOW')])} Saham")
    ihsg_last = df_ihsg['Close'].iloc[-1]
    ihsg_chg = ((ihsg_last - df_ihsg['Close'].iloc[-2]) / df_ihsg['Close'].iloc[-2]) * 100
    c4.metric("IHSG Terkini", fmt_id(ihsg_last), fmt_pct(ihsg_chg))
    st.markdown('</div>', unsafe_allow_html=True)

    # Filter Screener
    f_col1, f_col2, f_col3 = st.columns([2, 2, 2])
    with f_col1:
        filter_sinyal = st.selectbox("Filter Sinyal Trading:", [
            "Semua Saham", "STRONG BUY (Semua)", "STRONG BUY (BOW)", "STRONG BUY (BREAKOUT)", "BUY (BSJP / SWING)", "SELL / TAKE PROFIT"
        ])
    with f_col2:
        min_rs = st.slider("Minimal RS Rating (Kekuatan vs IHSG):", 1, 99, 50)
    with f_col3:
        kondisi_harga = st.selectbox("Kondisi Harga Hari Ini:", ["Semua Kondisi", "Saham Merah (Koreksi)", "Saham Hijau (Naik)"])

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

    # Tampilkan Tabel Berwarna
    st.markdown("### 📋 Hasil Pemindaian & Rekomendasi Eksekusi")
    if df_filtered.empty:
        st.info("Tidak ada saham yang memenuhi kriteria filter saat ini. Coba turunkan batas RS Rating atau ubah filter sinyal.")
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
            # Warna kolom Kode & Sinyal
            styles[0] = 'background-color: #e0f2fe; font-weight: bold; color: #0369a1;'
            if "BUY" in str(row["Sinyal"]):
                styles[3] = 'background-color: #dcfce7; color: #166534; font-weight: bold;'
            elif "SELL" in str(row["Sinyal"]):
                styles[3] = 'background-color: #fee2e2; color: #991b1b; font-weight: bold;'
            else:
                styles[3] = 'background-color: #fef3c7; color: #92400e;'
            # Warna Perubahan %
            if "+" in str(row["Perubahan (%)"]):
                styles[2] = 'color: #16a34a; font-weight: bold;'
            elif "-" in str(row["Perubahan (%)"]):
                styles[2] = 'color: #dc2626; font-weight: bold;'
            return styles

        st.dataframe(
            display_df.style.apply(style_table, axis=1),
            use_container_width=True,
            hide_index=True
        )

        # Detail Alasan & Waktu Eksekusi per Saham
        st.markdown("### 🎯 Detail Rencana Trading & Alasan Buy/Sell")
        pilih_detail = st.selectbox("Pilih Kode Saham untuk Melihat Alasan & Waktu Eksekusi:", df_filtered["Kode"].tolist())
        row_det = df_filtered[df_filtered["Kode"] == pilih_detail].iloc[0]

        st.markdown(f"""
        <div class="glass-card">
            <h4 style="margin-top:0; color:#1e3a8a;">{row_det['Kode']} — <span class="badge-buy">{row_det['Sinyal']}</span></h4>
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
# TAB 2: CHART CANDLESTICK 1 TAHUN (SAHAM & IHSG)
# ==============================================================================
with tab2:
    col_ch1, col_ch2 = st.columns(2)
    with col_ch1:
        saham_chart = st.selectbox("Pilih Saham JII70:", [t.replace(".JK", "") for t in JII70_TICKERS], index=0)
        fig_saham = plot_candlestick_1y(f"{saham_chart}.JK", f"Saham {saham_chart}")
        st.plotly_chart(fig_saham, use_container_width=True)

    with col_ch2:
        st.markdown("<div style='height: 42px;'></div>", unsafe_allow_html=True)
        fig_ihsg = plot_candlestick_1y("^JKSE", "Indeks Harga Saham Gabungan (IHSG)")
        st.plotly_chart(fig_ihsg, use_container_width=True)

# ==============================================================================
# TAB 3: PROFIL PERUSAHAAN
# ==============================================================================
with tab3:
    saham_profil = st.selectbox("Pilih Emiten untuk Melihat Profil Resmi:", [t.replace(".JK", "") for t in JII70_TICKERS], key="prof_sel")
    ticker_obj = yf.Ticker(f"{saham_profil}.JK")
    info = ticker_obj.info

    st.markdown(f"""
    <div class="glass-card">
        <h3 style="margin-top:0; color:#1e3a8a;">🏢 {info.get('longName', saham_profil)} ({saham_profil})</h3>
        <p><b>Sektor:</b> {info.get('sector', '-')} | <b>Industri:</b> {info.get('industry', '-')}</p>
        <p><b>Situs Web Resmi:</b> <a href="{info.get('website', '#')}" target="_blank">{info.get('website', '-')}</a></p>
        <hr>
        <p style="text-align:justify; line-height:1.6;">{info.get('longBusinessSummary', 'Deskripsi profil perusahaan sedang tidak tersedia dari penyedia data.')}</p>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Kapitalisasi Pasar", fmt_id(info.get('marketCap'), "Rp "))
    m2.metric("PER (Trailing)", f"{info.get('trailingPE', 0):.2f}x" if info.get('trailingPE') else "-")
    m3.metric("PBV (Price to Book)", f"{info.get('priceToBook', 0):.2f}x" if info.get('priceToBook') else "-")
    m4.metric("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "-")

# ==============================================================================
# TAB 4: WATCHLIST SAHAM PILIHAN
# ==============================================================================
with tab4:
    st.markdown("### ⭐ Daftar Pantauan (Watchlist) Anda")
    c_wl1, c_wl2 = st.columns([3, 1])
    with c_wl1:
        tambah_wl = st.selectbox("Tambah Saham ke Watchlist:", [t.replace(".JK", "") for t in JII70_TICKERS], key="add_wl")
    with c_wl2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("Tambah ke Daftar", use_container_width=True):
            if f"{tambah_wl}.JK" not in st.session_state.watchlist:
                st.session_state.watchlist.append(f"{tambah_wl}.JK")
                st.rerun()

    df_wl = df_screener[df_screener["Ticker"].isin(st.session_state.watchlist)].copy()
    if df_wl.empty:
        st.info("Watchlist masih kosong.")
    else:
        for _, r in df_wl.iterrows():
            col_w1, col_w2, col_w3, col_w4, col_w5 = st.columns([2, 2, 3, 3, 1])
            col_w1.markdown(f"**{r['Kode']}** ({fmt_id(r['Harga'], 'Rp ')})")
            col_w2.markdown(f"Perubahan: **{fmt_pct(r['Perubahan (%)'])}**")
            col_w3.markdown(f"Sinyal: **{r['Sinyal']}**")
            col_w4.markdown(f"Target Jual: **{fmt_id(r['Target Jual 1'], 'Rp ')}** | SL: **{fmt_id(r['Stop Loss'], 'Rp ')}**")
            if col_w5.button("🗑️", key=f"del_{r['Kode']}"):
                st.session_state.watchlist.remove(r['Ticker'])
                st.rerun()
            st.divider()

# ==============================================================================
# TAB 5: KALKULATOR TRADING SAHAM (BUY, SELL, FEE, PROFIT)
# ==============================================================================
with tab5:
    st.markdown("### 🧮 Kalkulator Profit & Fee Transaksi Saham")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    with k1:
        harga_beli = st.number_input("Harga Beli (Rp per lembar):", min_value=1, value=1000, step=5)
        jumlah_lot = st.number_input("Jumlah Lot (1 Lot = 100 lembar):", min_value=1, value=10, step=1)
    with k2:
        harga_jual = st.number_input("Target Harga Jual (Rp per lembar):", min_value=1, value=1100, step=5)
        fee_beli_pct = st.number_input("Fee Beli Sekuritas (%):", min_value=0.0, value=0.15, step=0.01, format="%.2f")
    with k3:
        fee_jual_pct = st.number_input("Fee Jual Sekuritas + Pajak (%):", min_value=0.0, value=0.25, step=0.01, format="%.2f")

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

    st.divider()
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Total Modal Beli (+Fee)", fmt_id(total_modal_keluar, "Rp "))
    r2.metric("Total Hasil Jual (-Fee)", fmt_id(total_dana_diterima, "Rp "))
    r3.metric("Total Fee Transaksi", fmt_id(total_fee, "Rp "))
    r4.metric("Profit / Rugi Bersih", fmt_id(profit_bersih, "Rp "), fmt_pct(roi_bersih))
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# TAB 6: BERITA TERKINI TERKAIT SAHAM
# ==============================================================================
with tab6:
    st.markdown("### 📰 Berita Pasar Modal & Emiten Terkini")
    topik_berita = st.text_input("Cari Berita Emiten atau Topik Pasar (misal: ADRO, ANTM, IHSG, dividen):", value="saham syariah JII70 IHSG")
    daftar_berita = fetch_stock_news(topik_berita)

    if not daftar_berita:
        st.warning("Belum ada berita terbaru yang ditemukan untuk kata kunci tersebut.")
    else:
        for b in daftar_berita:
            st.markdown(f"""
            <div class="glass-card" style="padding:14px;">
                <a href="{b['link']}" target="_blank" style="text-decoration:none; color:#1d4ed8; font-weight:700; font-size:1.05rem;">
                    {b['judul']}
                </a>
                <p style="margin:6px 0 0 0; font-size:0.82rem; color:#475569;">
                    Sumber: <b>{b['sumber']}</b> • {b['waktu']}
                </p>
            </div>
            """, unsafe_allow_html=True)
