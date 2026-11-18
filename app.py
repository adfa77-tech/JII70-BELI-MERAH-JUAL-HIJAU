import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import json
import feedparser
from datetime import datetime
import pytz
import urllib.parse

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="BELI SAHAM MERAH JUAL HIJAU",
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

# --- KAMUS PROFIL EMITEN BAHASA INDONESIA (70 EMITEN JII70) ---
PROFIL_INDONESIA = {
    "AADI": ("Energi & Pertambangan Batu Bara", "Pertambangan Batu Bara Termal", "PT Adaro Andalan Indonesia Tbk bergerak di bidang pertambangan batu bara termal terintegrasi, logistik batu bara, pengelolaan pelabuhan, serta pembangkit listrik pendukung operasional industri di Indonesia."),
    "ACES": ("Barang Konsumen Non-Primer", "Ritel Perbaikan Rumah & Gaya Hidup", "PT Aspirasi Hidup Indonesia Tbk (sebelumnya Ace Hardware Indonesia) mengelola jaringan ritel perlengkapan rumah tangga, perkakas, dan gaya hidup modern di berbagai kota besar di Indonesia."),
    "ADMR": ("Barang Baku", "Pertambangan Batu Bara Metalurgi & Aluminium", "PT Adaro Minerals Indonesia Tbk berfokus pada pertambangan batu bara kokas (metalurgi) untuk bahan baku baja serta pengembangan smelter pengolahan aluminium hijau di Kalimantan Utara."),
    "ADRO": ("Energi", "Pertambangan Batu Bara & Energi Terbarukan", "PT Alamtri Resources Indonesia Tbk merupakan perusahaan energi terintegrasi yang menjalankan bisnis pertambangan batu bara, jasa pertambangan, logistik, serta investasi energi baru dan terbarukan."),
    "AKRA": ("Energi", "Distribusi BBM, Kimia Dasar & Kawasan Industri", "PT AKR Corporindo Tbk bergerak di bidang distribusi bahan bakar minyak (BBM) dan bahan kimia dasar, jasa logistik tangki penyimpanan, serta pengelola kawasan industri terintegrasi JIIPE di Gresik."),
    "ANTM": ("Barang Baku", "Pertambangan Emas, Nikel & Logam Mulia", "PT Aneka Tambang Tbk (ANTAM) adalah perusahaan pertambangan terdiversifikasi milik negara (BUMN) yang memproduksi dan memurnikan emas logam mulia, bijih nikel, feronikel, bauksit, dan alumina."),
    "ARCI": ("Barang Baku", "Pertambangan Emas & Perak", "PT Archi Indonesia Tbk merupakan salah satu produsen emas murni terkemuka di Indonesia yang mengoperasikan Tambang Emas Toka Tindung di Sulawesi Utara."),
    "AVIA": ("Barang Baku", "Industri Cat & Bahan Bangunan", "PT Avia Avian Tbk adalah produsen cat dekoratif dan pelapis pelindung terkemuka di Indonesia dengan jaringan distribusi logistik mandiri di seluruh nusantara."),
    "BKSL": ("Properti & Real Estat", "Pengembangan Kota Mandiri", "PT Sentul City Tbk bergerak dalam bidang pengembangan properti dan kota mandiri terpadu di kawasan Sentul, Bogor, meliputi hunian, area komersial, dan fasilitas rekreasi."),
    "BRIS": ("Keuangan Syariah", "Perbankan Syariah", "PT Bank Syariah Indonesia Tbk (BSI) merupakan bank syariah terbesar di Indonesia hasil penggabungan bank syariah BUMN yang menyediakan layanan perbankan ritel, UMKM, dan korporasi sesuai prinsip syariah."),
    "BRMS": ("Barang Baku", "Pertambangan Emas, Tembaga & Seng", "PT Bumi Resources Minerals Tbk mengelola berbagai konsesi pertambangan mineral non-batu bara, terutama produksi emas di Poboya (Palu) serta proyek tembaga dan seng."),
    "BSDE": ("Properti & Real Estat", "Pengembangan Properti & Kota Mandiri", "PT Bumi Serpong Damai Tbk merupakan pengembang properti terkemuka di bawah grup Sinar Mas Land yang mengembangkan kota mandiri BSD City serta berbagai proyek residensial dan komersial."),
    "BTPS": ("Keuangan Syariah", "Perbankan Syariah Pembiayaan Produktif", "PT Bank BTPN Syariah Tbk berfokus pada layanan perbankan syariah bagi segmen prasejahtera produktif dan pemberdayaan pelaku usaha mikro perempuan di seluruh Indonesia."),
    "BUMI": ("Energi", "Pertambangan Batu Bara", "PT Bumi Resources Tbk adalah salah satu eksportir batu bara termal terbesar di dunia dengan wilayah operasi utama di Kalimantan Timur dan Kalimantan Selatan."),
    "CMRY": ("Barang Konsumen Primer", "Produk Olahan Susu & Makanan Konsumen", "PT Cisarua Mountain Dairy Tbk (Cimory) memproduksi dan mendistribusikan produk olahan susu seperti yogurt dan susu UHT serta makanan olahan siap masak."),
    "CPIN": ("Barang Konsumen Primer", "Pakan Ternak & Peternakan Unggas Terpadu", "PT Charoen Pokphand Indonesia Tbk merupakan pemimpin pasar dalam industri pakan ternak, pembibitan ayam usia sehari (DOC), dan produk makanan olahan berbasis daging ayam."),
    "CTRA": ("Properti & Real Estat", "Pengembangan Residensial, Komersial & Rumah Sakit", "PT Ciputra Development Tbk mengembangkan proyek perumahan berskala kota, pusat perbelanjaan, hotel, serta jaringan layanan kesehatan di puluhan kota di Indonesia."),
    "DEWA": ("Energi", "Jasa Kontraktor Pertambangan", "PT Darma Henwa Tbk menyediakan jasa kontraktor pertambangan terpadu, meliputi pengupasan lapisan tanah penutup, penggalian batu bara, dan pemeliharaan alat berat."),
    "DKFT": ("Barang Baku", "Pertambangan Bijih Nikel", "PT Central Omega Resources Tbk bergerak di bidang pertambangan dan pengolahan bijih nikel dengan wilayah operasional utama di Sulawesi Tengah."),
    "DSNG": ("Barang Konsumen Primer", "Perkebunan Kelapa Sawit & Produk Kayu", "PT Dharma Satya Nusantara Tbk menjalankan usaha perkebunan kelapa sawit dan pabrik pengolahan CPO di Kalimantan serta industri panel dan lantai kayu berkualitas ekspor."),
    "ELSA": ("Energi", "Jasa Hulu Migas & Distribusi Energi", "PT Elnusa Tbk merupakan anak usaha Pertamina yang menyediakan jasa survei seismik, pengeboran, pemeliharaan sumur minyak dan gas, serta distribusi energi."),
    "ENRG": ("Energi", "Eksplorasi & Produksi Minyak dan Gas Bumi", "PT Energi Mega Persada Tbk bergerak di bidang eksplorasi, pengembangan, dan produksi minyak mentah serta gas bumi di berbagai blok migas di Indonesia."),
    "ERAA": ("Barang Konsumen Non-Primer", "Ritel & Distribusi Perangkat Elektronik", "PT Erajaya Swasembada Tbk adalah importir, distributor, dan peritel terbesar perangkat telekomunikasi seluler, aksesoris, serta produk gaya hidup pintar di Indonesia."),
    "ESSA": ("Barang Baku", "Industri Amonia & Kilang LPG", "PT ESSA Industries Indonesia Tbk mengoperasikan kilang pemurnian LPG swasta dan pabrik produksi amonia berkapasitas besar di Sulawesi Tengah."),
    "EXCL": ("Infrastruktur", "Operator Telekomunikasi Seluler & Data", "PT XL Axiata Tbk merupakan penyedia layanan telekomunikasi seluler, jaringan data broadband berkecepatan tinggi, dan solusi digital terkemuka di Indonesia."),
    "HEAL": ("Kesehatan", "Jaringan Rumah Sakit Umum & Ibu Anak", "PT Medikaloka Hermina Tbk mengelola jaringan rumah sakit Hermina yang tersebar luas di Indonesia dengan keunggulan pada layanan spesialis ibu, anak, dan rumah sakit umum."),
    "HRTA": ("Barang Konsumen Non-Primer", "Manufaktur & Perdagangan Perhiasan Emas", "PT Hartadinata Abadi Tbk bergerak dalam industri manufaktur perhiasan emas, emas batangan, serta jaringan toko emas ritel dan gadai emas."),
    "HRUM": ("Energi & Barang Baku", "Pertambangan Batu Bara & Hilirisasi Nikel", "PT Harum Energy Tbk menjalankan usaha pertambangan batu bara di Kalimantan Timur serta memperluas bisnis secara agresif ke rantai pasok pengolahan dan pemurnian nikel."),
    "ICBP": ("Barang Konsumen Primer", "Industri Makanan & Minuman Olahan", "PT Indofood CBP Sukses Makmur Tbk merupakan produsen berbagai produk konsumen bermerek terkemuka, termasuk mi instan (Indomie), susu, makanan ringan, dan bumbu masak."),
    "IMPC": ("Perindustrian", "Manufaktur Bahan Bangunan Polimer", "PT Impack Pratama Industri Tbk memproduksi dan mendistribusikan bahan bangunan berbahan dasar plastik/polimer seperti atap polikarbonat, pipa, dan panel komposit."),
    "INDF": ("Barang Konsumen Primer", "Perusahaan Total Food Solutions", "PT Indofood Sukses Makmur Tbk memiliki operasional bisnis yang mencakup seluruh tahapan produksi makanan, mulai dari agribisnis, pengolahan tepung terigu (Bogasari), hingga distribusi produk konsumen."),
    "INDY": ("Energi", "Energi Terintegrasi & Kendaraan Listrik", "PT Indika Energy Tbk merupakan perusahaan investasi energi terdiversifikasi yang mencakup pertambangan batu bara, jasa energi, logistik, hingga ekosistem kendaraan listrik (ALVA)."),
    "INKP": ("Barang Baku", "Industri Pulp, Kertas & Kemasan", "PT Indah Kiat Pulp & Paper Tbk merupakan salah satu produsen pulp, kertas budaya, dan kertas kemasan industri terbesar di Asia yang berada di bawah grup APP Sinar Mas."),
    "INTP": ("Barang Baku", "Industri Semen & Bahan Bangunan", "PT Indocement Tunggal Prakarsa Tbk memproduksi dan memasarkan semen bermerek Tiga Roda serta beton siap pakai dengan pabrik utama di Citeureup, Cirebon, dan Tarjun."),
    "ISAT": ("Infrastruktur", "Telekomunikasi & Solusi Digital", "PT Indosat Tbk (Indosat Ooredoo Hutchison) merupakan operator telekomunikasi seluler, konektivitas tetap, dan layanan pusat data digital utama di Indonesia."),
    "ITMG": ("Energi", "Pertambangan & Perdagangan Batu Bara", "PT Indo Tambangraya Megah Tbk adalah produsen batu bara berkalori tinggi terkemuka di Kalimantan yang dikenal memiliki efisiensi operasional dan rasio dividen tinggi."),
    "JPFA": ("Barang Konsumen Primer", "Agribisnis & Peternakan Unggas", "PT Japfa Comfeed Indonesia Tbk bergerak di bidang produksi pakan ternak, pembibitan ayam, peternakan komersial, budidaya perairan, dan pengolahan produk protein hewani."),
    "JSMR": ("Infrastruktur", "Pengembang & Operator Jalan Tol", "PT Jasa Marga (Persero) Tbk adalah pengembang dan operator jalan tol utama di Indonesia yang mengelola jaringan tol strategis di Pulau Jawa dan luar Jawa."),
    "KIJA": ("Properti & Real Estat", "Pengembangan Kawasan Industri", "PT Kawasan Industri Jababeka Tbk merupakan pengembang kawasan industri terpadu pertama yang tercatat di BEI dengan kawasan utama di Cikarang, Kendal, dan Tanjung Lesung."),
    "KLBF": ("Kesehatan", "Farmasi, Nutrisi & Distribusi Kesehatan", "PT Kalbe Farma Tbk merupakan perusahaan farmasi terbesar di Asia Tenggara yang memproduksi obat resep, obat bebas, produk nutrisi kesehatan, serta jaringan distribusi alat kesehatan."),
    "KPIG": ("Properti & Real Estat", "Properti, Perhotelan & Kawasan Wisata", "PT MNC Land Tbk mengembangkan proyek properti komersial, gedung perkantoran, hotel berbintang, serta kawasan pariwisata terpadu Lido City."),
    "LSIP": ("Barang Konsumen Primer", "Perkebunan Kelapa Sawit & Karet", "PT PP London Sumatra Indonesia Tbk (Lonsum) mengelola perkebunan kelapa sawit, karet, dan benih bibit unggul di Sumatra, Kalimantan, dan Sulawesi."),
    "MAPA": ("Barang Konsumen Non-Primer", "Ritel Produk Olahraga & Gaya Hidup Aktif", "PT Map Aktif Adiperkasa Tbk adalah pemimpin pasar ritel perlengkapan olahraga, sepatu atletik, dan pakaian aktif yang mengelola puluhan merek global di Asia Tenggara."),
    "MAPI": ("Barang Konsumen Non-Primer", "Ritel Gaya Hidup, Fesyen & F&B", "PT Mitra Adiperkasa Tbk merupakan peritel gaya hidup terkemuka di Indonesia yang mengoperasikan ratusan gerai department store, fesyen, olahraga, dan makanan minuman."),
    "MARK": ("Perindustrian", "Manufaktur Cetakan Sarung Tangan", "PT Mark Dynamics Indonesia Tbk adalah produsen cetakan sarung tangan (hand former) berbahan porselen terbesar di dunia yang memasok pabrik sarung tangan medis global."),
    "MBMA": ("Barang Baku", "Pertambangan & Hilirisasi Nikel", "PT Merdeka Battery Materials Tbk mengintegrasikan rantai pasok mineral bahan baku baterai kendaraan listrik mulai dari tambang nikel Konawe hingga fasilitas smelter HPAL dan RKEF."),
    "MDKA": ("Barang Baku", "Pertambangan Emas, Tembaga & Nikel", "PT Merdeka Copper Gold Tbk adalah perusahaan pertambangan logam nasional yang mengoperasikan tambang emas Tujuh Bukit, tambang tembaga Wetar, serta proyek nikel."),
    "MEDC": ("Energi", "Minyak & Gas Bumi serta Pembangkit Listrik", "PT Medco Energi Internasional Tbk merupakan perusahaan energi swasta terkemuka di Asia Tenggara dengan portofolio eksplorasi migas, pertambangan tembaga-emas, dan ketenagalistrikan."),
    "MIKA": ("Kesehatan", "Jaringan Rumah Sakit Swasta", "PT Mitra Keluarga Karyasehat Tbk mengoperasikan jaringan rumah sakit Mitra Keluarga yang berfokus pada pelayanan kesehatan komprehensif bagi segmen menengah ke atas."),
    "MTEL": ("Infrastruktur", "Penyewaan Menara Telekomunikasi", "PT Dayamitra Telekomunikasi Tbk (Mitratel) adalah pemilik dan pengelola menara telekomunikasi terbesar di Asia Tenggara dengan puluhan ribu menara di seluruh Indonesia."),
    "MYOR": ("Barang Konsumen Primer", "Industri Makanan & Minuman Konsumen", "PT Mayora Indah Tbk memproduksi biskuit, permen, wafer, cokelat, dan kopi instan (seperti Kopiko dan Torabika) yang dipasarkan secara luas di pasar domestik maupun ekspor."),
    "PGAS": ("Energi", "Transmisi & Distribusi Gas Bumi", "PT Perusahaan Gas Negara Tbk (PGN) merupakan subholding gas Pertamina yang mengelola jaringan pipa transmisi dan distribusi gas bumi bagi industri, komersial, dan rumah tangga."),
    "PTBA": ("Energi", "Pertambangan Batu Bara BUMN", "PT Bukit Asam Tbk adalah perusahaan pertambangan batu bara milik negara yang berpusat di Tanjung Enim, Sumatra Selatan, dengan cadangan batu bara besar dan ekspansi energi bersih."),
    "RAJA": ("Energi", "Infrastruktur Gas Bumi & Energi", "PT Rukun Raharja Tbk bergerak di bidang penyediaan infrastruktur gas bumi terintegrasi, pipa transmisi gas, perdagangan gas, dan investasi hulu migas."),
    "RATU": ("Energi", "Eksplorasi & Produksi Minyak dan Gas", "PT Raharja Energi Cepu Tbk bergerak pada bidang investasi dan pengelolaan partisipasi wilayah kerja minyak dan gas bumi di Indonesia."),
    "SIDO": ("Kesehatan", "Industri Herbal & Farmasi Tradisional", "PT Industri Jamu Dan Farmasi Sido Muncul Tbk merupakan produsen obat herbal modern dan minuman kesehatan terkemuka di Indonesia dengan produk unggulan Tolak Angin."),
    "SMGR": ("Barang Baku", "Industri Semen & Solusi Bahan Bangunan", "PT Semen Indonesia (Persero) Tbk (SIG) adalah produsen semen terbesar di Indonesia dan Asia Tenggara dengan jaringan pabrik terintegrasi dari Sumatra hingga Papua."),
    "SMRA": ("Properti & Real Estat", "Pengembangan Kota Terpadu & Pusat Belanja", "PT Summarecon Agung Tbk mengembangkan kawasan kota terpadu bernilai tinggi (Kelapa Gading, Serpong, Bekasi, Bandung) serta mengelola pusat perbelanjaan Summarecon Mall."),
    "SRTG": ("Keuangan & Investasi", "Perusahaan Investasi Aktif", "PT Saratoga Investama Sedaya Tbk merupakan perusahaan investasi aktif terkemuka di Indonesia yang berfokus pada sektor sumber daya alam, infrastruktur, dan produk konsumen."),
    "SSIA": ("Infrastruktur & Properti", "Konstruksi, Kawasan Industri & Perhotelan", "PT Surya Semesta Internusa Tbk menjalankan bisnis jasa konstruksi (Nusa Raya Cipta), pengembangan kawasan industri Suryacipta dan Subang Smartpolitan, serta perhotelan."),
    "TAPG": ("Barang Konsumen Primer", "Perkebunan Kelapa Sawit", "PT Triputra Agro Persada Tbk mengelola perkebunan kelapa sawit produktif dan pabrik pengolahan minyak kelapa sawit (CPO) dengan usia tanaman prima di Kalimantan dan Sumatra."),
    "TCPI": ("Energi", "Jasa Logistik & Angkutan Laut Energi", "PT Transcoal Pacific Tbk menyediakan jasa transportasi laut dan logistik terintegrasi untuk pengangkutan batu bara, nikel, dan komoditas curah di perairan Indonesia."),
    "TINS": ("Barang Baku", "Pertambangan & Peleburan Timah", "PT Timah Tbk merupakan salah satu produsen dan eksportir logam timah terbesar di dunia yang beroperasi di wilayah Provinsi Kepulauan Bangka Belitung."),
    "TKIM": ("Barang Baku", "Industri Kertas & Produk Kemasan", "PT Pabrik Kertas Tjiwi Kimia Tbk merupakan produsen kertas budaya, alat tulis kantor, dan kemasan industri terkemuka di bawah grup APP Sinar Mas."),
    "TLKM": ("Infrastruktur", "Telekomunikasi & Ekosistem Digital BUMN", "PT Telkom Indonesia (Persero) Tbk adalah penyedia layanan telekomunikasi, jaringan internet fiber optik (IndiHome), layanan seluler (Telkomsel), dan pusat data terbesar di Indonesia."),
    "TOBA": ("Energi", "Energi Terbarukan, Kendaraan Listrik & Batu Bara", "PT TBS Energi Utama Tbk bertransformasi dari pertambangan batu bara menuju energi hijau, pembangkit listrik terbarukan, pengelolaan limbah medis, dan motor listrik Electrum."),
    "TPIA": ("Barang Baku", "Industri Petrokimia & Infrastruktur", "PT Chandra Asri Pacific Tbk merupakan produsen petrokimia terintegrasi terbesar di Indonesia yang memasok bahan baku plastik olefin dan poliolefin untuk industri nasional."),
    "UNTR": ("Perindustrian", "Alat Berat, Kontraktor Tambang & Energi", "PT United Tractors Tbk adalah distributor alat berat Komatsu terbesar di Indonesia sekaligus operator kontraktor pertambangan (PAMA), tambang emas, dan energi terbarukan."),
    "UNVR": ("Barang Konsumen Primer", "Produk Kebutuhan Rumah Tangga & Perawatan Diri", "PT Unilever Indonesia Tbk memproduksi dan memasarkan puluhan merek kebutuhan sehari-hari (Pepsodent, Lifebuoy, Rinso, Royco, Bango) yang menjangkau seluruh lapisan masyarakat."),
    "WIFI": ("Teknologi & Infrastruktur", "Jaringan Internet Fiber Optik & Konektivitas", "PT Solusi Sinergi Digital Tbk (Surge) mengembangkan infrastruktur jaringan serat optik berkapasitas tinggi di sepanjang jalur kereta api Pulau Jawa dan layanan internet terjangkau.")
}

# --- INISIALISASI SESSION STATE ---
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

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

# --- SINKRONISASI DATA HARGA REAL-TIME TRADINGVIEW SCANNER ---
@st.cache_data(ttl=60)
def fetch_tradingview_realtime(raw_codes):
    """Mengambil harga & perubahan % real-time langsung dari TradingView Scanner API untuk bursa IDX"""
    tv_map = {}
    try:
        url = "https://scanner.tradingview.com/indonesia/scan"
        symbols = ["IDX:COMPOSITE"] + [f"IDX:{code}" for code in raw_codes]
        payload = {
            "symbols": {
                "tickers": symbols,
                "query": {"types": []}
            },
            "columns": ["name", "close", "change", "open", "high", "low", "volume"]
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json"
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=8)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            for item in data:
                sym = item.get("s", "")
                d = item.get("d", [])
                if len(d) >= 7 and d[1] is not None:
                    code = sym.replace("IDX:", "")
                    tv_map[code] = {
                        "close": float(d[1]),
                        "change_pct": float(d[2]) if d[2] is not None else 0.0,
                        "open": float(d[3]) if d[3] is not None else float(d[1]),
                        "high": float(d[4]) if d[4] is not None else float(d[1]),
                        "low": float(d[5]) if d[5] is not None else float(d[1]),
                        "volume": float(d[6]) if d[6] is not None else 0.0
                    }
    except Exception:
        pass
    return tv_map

# --- KONEKSI DATA REAL-TIME TRADINGVIEW + HISTORIS TEKNIKAL ---
@st.cache_data(ttl=120)
def fetch_and_analyze_market(tickers):
    tv_realtime = fetch_tradingview_realtime(JII70_RAW)

    try:
        tk_ihsg = yf.Ticker("^JKSE")
        ihsg = tk_ihsg.history(period="6mo", interval="1d")
        if isinstance(ihsg.columns, pd.MultiIndex):
            ihsg.columns = ihsg.columns.get_level_values(0)
        ihsg = ihsg.dropna()
        ihsg_last = float(ihsg['Close'].iloc[-1])
        ihsg_prev = float(ihsg['Close'].iloc[-2]) if len(ihsg) > 1 else ihsg_last
        ihsg_chg_pct = ((ihsg_last - ihsg_prev) / ihsg_prev) * 100 if ihsg_prev > 0 else 0.0
        ihsg_ret = (ihsg_last / float(ihsg['Close'].iloc[0]) - 1) * 100 if len(ihsg) >= 20 else 0.0
    except Exception:
        ihsg = pd.DataFrame({'Close': [7200.0, 7200.0], 'Open': [7200, 7200], 'High': [7200, 7200], 'Low': [7200, 7200], 'Volume': [1000, 1000]})
        ihsg_last = 7200.0
        ihsg_prev = 7200.0
        ihsg_chg_pct = 0.0
        ihsg_ret = 0.0

    # Override IHSG dengan feed real-time TradingView jika tersedia
    if "COMPOSITE" in tv_realtime:
        ihsg_last = tv_realtime["COMPOSITE"]["close"]
        ihsg_chg_pct = tv_realtime["COMPOSITE"]["change_pct"]

    results = []
    for t in tickers:
        try:
            kode = t.replace(".JK", "")
            tk = yf.Ticker(t)
            df = tk.history(period="6mo", interval="1d")
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna()
            if len(df) < 30:
                continue

            close = df['Close'].copy()
            high = df['High'].copy()
            low = df['Low'].copy()
            volume = df['Volume'].copy()

            # Sinkronkan bar terakhir dengan harga real-time TradingView
            if kode in tv_realtime:
                rt = tv_realtime[kode]
                curr_price = rt["close"]
                chg_pct = rt["change_pct"]
                curr_high = max(float(high.iloc[-1]), rt["high"], curr_price)
                curr_low = min(float(low.iloc[-1]), rt["low"], curr_price) if rt["low"] > 0 else float(low.iloc[-1])
                curr_vol = rt["volume"] if rt["volume"] > 0 else float(volume.iloc[-1])
                close.iloc[-1] = curr_price
                high.iloc[-1] = curr_high
                low.iloc[-1] = curr_low
                volume.iloc[-1] = curr_vol
            else:
                curr_price = float(close.iloc[-1])
                prev_price = float(close.iloc[-2])
                chg_pct = ((curr_price - prev_price) / prev_price) * 100

            # Moving Average 20, 50, 200
            ma20 = float(close.rolling(20).mean().iloc[-1])
            ma50 = float(close.rolling(50).mean().iloc[-1]) if len(df) >= 50 else ma20
            ma200 = float(close.rolling(min(len(df), 200)).mean().iloc[-1])

            # RSI 14
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = float((100 - (100 / (1 + rs))).iloc[-1])

            # Bollinger Bands (20, 2)
            bb_std = float(close.rolling(20).std().iloc[-1])
            bb_lower = ma20 - (2 * bb_std)
            bb_upper = ma20 + (2 * bb_std)

            # Stochastic %K (14)
            low_14 = float(low.rolling(14).min().iloc[-1])
            high_14 = float(high.rolling(14).max().iloc[-1])
            stoch_k = ((curr_price - low_14) / (high_14 - low_14) * 100) if (high_14 - low_14) > 0 else 50.0

            # RS Rating vs IHSG
            ret_stock = (curr_price / float(close.iloc[0]) - 1) * 100
            rs_score = round(50 + (ret_stock - ihsg_ret), 1)
            rs_score = max(1, min(99, rs_score))

            vol_ma20 = float(volume.rolling(20).mean().iloc[-1])
            vol_ratio = float(volume.iloc[-1] / vol_ma20) if vol_ma20 > 0 else 1.0
            
            support_20 = float(low.tail(20).min())
            resist_20 = float(high.tail(20).max())

            # --- PENYEMPURNAAN RUMUS "BELI SAHAM MERAH JUAL HIJAU" ---
            sinyal = "WAIT / PANTAU"
            strategi = "Konsolidasi Sehat"
            alasan = []
            waktu_eksekusi = "Pantau saat pembukaan atau menjelang penutupan"

            # 1. BELI MERAH UTAMA (Diskon di Zona Support Kuat / Oversold pada Uptrend)
            if chg_pct <= -0.5 and (curr_price <= bb_lower * 1.015 or rsi <= 38 or stoch_k <= 25) and curr_price >= ma200 * 0.92:
                sinyal = "STRONG BUY MERAH (DISKON)"
                strategi = "Beli Merah Ekstrem (Oversold di Support)"
                alasan.append(f"Harga terkoreksi merah ({chg_pct:.2f}%) menyentuh area jenuh jual (RSI {rsi:.1f}, Stoch {stoch_k:.0f}) namun tren jangka panjang MA200 terjaga.")
                waktu_eksekusi = "Sesi 2 (14:45 - 15:50 WIB) saat tekanan jual mereda"

            # 2. BELI MERAH PULLBACK (Koreksi Wajar di Atas MA20 / MA50)
            elif chg_pct < 0 and (curr_price >= ma20 * 0.985 or curr_price >= ma50 * 0.98) and rsi < 62 and rs_score >= 45:
                sinyal = "BUY MERAH (PULLBACK)"
                strategi = "Beli Merah Pullback MA20 / MA50"
                alasan.append(f"Saham memerah sehat ({chg_pct:.2f}%) tepat di atas area pantulan MA20/MA50 dengan kekuatan relatif RS {rs_score}.")
                waktu_eksekusi = "Sesi 2 (14:30 - 15:50 WIB) untuk tangkap pantulan"

            # 3. JUAL HIJAU UTAMA (Take Profit Optimal saat Hijau Tinggi / Overbought)
            elif chg_pct >= 2.0 and (rsi >= 70 or curr_price >= bb_upper * 0.99 or stoch_k >= 82):
                sinyal = "STRONG SELL HIJAU (TAKE PROFIT)"
                strategi = "Jual Hijau Optimal (Overbought / Resistensi)"
                alasan.append(f"Harga melonjak hijau (+{chg_pct:.2f}%) menembus Upper Bollinger / RSI jenuh beli ({rsi:.1f}). Saat ideal merealisasikan keuntungan.")
                waktu_eksekusi = "Sesi 1 (09:05 - 10:30 WIB) saat antrean bid tebal"

            # 4. JUAL HIJAU BERTAHAP (Trailing Profit saat Hijau Menguat)
            elif chg_pct >= 1.5 and curr_price >= resist_20 * 0.985:
                sinyal = "SELL HIJAU (TRAILING PROFIT)"
                strategi = "Jual Hijau Bertahap di Area Resistensi"
                alasan.append(f"Harga menguat hijau (+{chg_pct:.2f}%) mendekati puncak resistensi 20 hari ({fmt_id(resist_20)}). Amankan sebagian profit.")
                waktu_eksekusi = "Sesi 1 atau saat harga menyentuh resistensi"

            # 5. CUT LOSS / WASPADA BREAKDOWN
            elif chg_pct <= -3.0 and curr_price < ma50 and vol_ratio > 1.3:
                sinyal = "CUT LOSS / HINDARI"
                strategi = "Breakdown Support dengan Volume Besar"
                alasan.append(f"Penurunan tajam ({chg_pct:.2f}%) menembus MA50 disertai lonjakan volume distribusi ({vol_ratio:.2f}x).")
                waktu_eksekusi = "Segera batasi risiko jika menembus batas Stop Loss"

            else:
                if chg_pct < 0:
                    alasan.append(f"Harga memerah ({chg_pct:.2f}%), menunggu konfirmasi pantulan di dekat support {fmt_id(support_20)}.")
                else:
                    alasan.append(f"Harga menghijau (+{chg_pct:.2f}%), masih dalam rentang akumulasi wajar di bawah resistensi {fmt_id(resist_20)}.")

            # Kalkulasi Zona Beli Merah & Target Jual Hijau
            if "MERAH" in sinyal:
                buy_low = min(curr_price * 0.985, support_20)
                buy_high = curr_price
            else:
                buy_low = max(support_20, ma20 * 0.98)
                buy_high = min(curr_price * 0.995, ma20 * 1.005)

            target_1 = max(resist_20, curr_price * 1.04)
            target_2 = max(bb_upper, curr_price * 1.08)
            stop_loss = min(support_20 * 0.975, curr_price * 0.94)

            results.append({
                "Kode": kode,
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
                "MA200": ma200,
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
    return df_res, ihsg, ihsg_last, ihsg_chg_pct

# --- WIDGET CHART CANDLESTICK TRADINGVIEW DENGAN MA 20, MA 50, MA 200 ---
def render_tradingview_widget(kode_saham, height=640):
    tv_symbol = "IDX:COMPOSITE" if kode_saham == "IHSG" else f"IDX:{kode_saham}"
    widget_html = f"""
    <div class="tradingview-widget-container" style="height:{height}px;width:100%;border-radius:16px;overflow:hidden;border:1.5px solid rgba(74, 222, 128, 0.35);box-shadow:0 10px 25px rgba(0,0,0,0.45);">
      <div id="tv_chart_jii70" style="height:calc(100% - 30px);width:100%;"></div>
      <div style="background:#081713;color:#94a3b8;font-family:'Plus Jakarta Sans',sans-serif;font-size:11px;padding:6px 14px;display:flex;justify-content:space-between;align-items:center;">
        <span>Indikator Aktif: <b>MA 20</b> (Biru) • <b>MA 50</b> (Kuning) • <b>MA 200</b> (Ungu)</span>
        <span>Sumber Real-Time: <a href="https://id.tradingview.com/" target="_blank" style="color:#4ade80;text-decoration:none;font-weight:700;">TradingView ({tv_symbol})</a></span>
      </div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "{tv_symbol}",
        "interval": "D",
        "timezone": "Asia/Jakarta",
        "theme": "dark",
        "style": "1",
        "locale": "id",
        "toolbar_bg": "#081713",
        "backgroundColor": "#071813",
        "gridColor": "rgba(74, 222, 128, 0.08)",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "hide_side_toolbar": false,
        "save_image": true,
        "studies": [
          {{
            "id": "MASimple@tv-basicstudies",
            "inputs": {{ "length": 20 }}
          }},
          {{
            "id": "MASimple@tv-basicstudies",
            "inputs": {{ "length": 50 }}
          }},
          {{
            "id": "MASimple@tv-basicstudies",
            "inputs": {{ "length": 200 }}
          }}
        ],
        "studies_overrides": {{
          "moving average.ma.color": "#38bdf8",
          "moving average.ma.linewidth": 2
        }},
        "container_id": "tv_chart_jii70"
      }});
      </script>
    </div>
    """
    components.html(widget_html, height=height + 8)

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

# --- AMBIL DATA PASAR REAL-TIME ---
with st.spinner("Menyinkronkan data harga real-time TradingView untuk 70 emiten JII70..."):
    df_screener, df_ihsg, ihsg_last, ihsg_chg = fetch_and_analyze_market(JII70_TICKERS)

# --- HEADER UTAMA ---
chg_color = "#4ade80" if ihsg_chg >= 0 else "#f87171"
chg_sign = "+" if ihsg_chg >= 0 else ""
ihsg_str = f"{ihsg_last:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.markdown(f"""
<div class="header-box">
    <div>
        <h2 style="margin:0; font-weight:800; color:#ffffff !important;">📊 BELI SAHAM MERAH JUAL HIJAU</h2>
        <p style="margin:4px 0 0 0; font-size:0.88rem; color:#facc15 !important;">TradingView Real-Time Price Sync • 70 Emiten Syariah JII70</p>
    </div>
    <div style="text-align: right;">
        <p style="margin:0; font-size:0.75rem; color:#facc15; font-weight:700;">IHSG REAL-TIME</p>
        <h3 style="margin:2px 0; font-size:1.3rem; color:#ffffff !important;">{ihsg_str} <span style="font-size:0.9rem; color:{chg_color};">({chg_sign}{ihsg_chg:.2f}%)</span></h3>
    </div>
</div>
""", unsafe_allow_html=True)

col_ref1, col_ref2 = st.columns([1, 5])
with col_ref1:
    if st.button("🔄 Refresh Harga Live", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- NAVIGASI TAB ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔍 Screener Beli Merah Jual Hijau",
    "🕯️ Chart TradingView (MA 20/50/200)",
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
    beli_merah_cnt = len(df_screener[df_screener['Sinyal'].str.contains('BUY MERAH')]) if 'Sinyal' in df_screener.columns else 0
    jual_hijau_cnt = len(df_screener[df_screener['Sinyal'].str.contains('SELL HIJAU')]) if 'Sinyal' in df_screener.columns else 0
    
    c1.metric("Total Emiten Terpantau", f"{total_emiten} Saham")
    c2.metric("Sinyal Beli Merah (Diskon)", f"{beli_merah_cnt} Saham")
    c3.metric("Sinyal Jual Hijau (Profit)", f"{jual_hijau_cnt} Saham")
    c4.metric("Waktu Pemindaian", get_wib_time())
    st.markdown('</div>', unsafe_allow_html=True)

    f_col1, f_col2, f_col3 = st.columns([2, 2, 2])
    with f_col1:
        filter_sinyal = st.selectbox("Filter Sinyal Trading:", [
            "Semua Saham",
            "Semua Beli Merah (Diskon & Pullback)",
            "STRONG BUY MERAH (DISKON)",
            "BUY MERAH (PULLBACK)",
            "Semua Jual Hijau (Take Profit)",
            "STRONG SELL HIJAU (TAKE PROFIT)",
            "SELL HIJAU (TRAILING PROFIT)",
            "CUT LOSS / HINDARI"
        ])
    with f_col2:
        min_rs = st.slider("Minimal RS Rating (Kekuatan vs IHSG):", 1, 99, 25)
    with f_col3:
        kondisi_harga = st.selectbox("Kondisi Harga Hari Ini:", ["Semua Kondisi", "Saham Merah (Koreksi)", "Saham Hijau (Naik)"])

    if 'Sinyal' in df_screener.columns:
        df_filtered = df_screener[df_screener['RS Rating'] >= min_rs].copy()
        if filter_sinyal == "Semua Beli Merah (Diskon & Pullback)":
            df_filtered = df_filtered[df_filtered['Sinyal'].str.contains("BUY MERAH")]
        elif filter_sinyal == "Semua Jual Hijau (Take Profit)":
            df_filtered = df_filtered[df_filtered['Sinyal'].str.contains("SELL HIJAU")]
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
            if "BUY MERAH" in str(row["Sinyal"]):
                styles[3] = 'background-color: #022c22; color: #4ade80; font-weight: bold;'
            elif "SELL HIJAU" in str(row["Sinyal"]):
                styles[3] = 'background-color: #1e3a8a; color: #93c5fd; font-weight: bold;'
            elif "CUT LOSS" in str(row["Sinyal"]):
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
                <li><b>Zona Harga Beli Merah Ideal:</b> Rp {row_det['Area Beli']}</li>
                <li><b>Target Jual Hijau 1 (Konservatif):</b> {fmt_id(row_det['Target Jual 1'], 'Rp ')}</li>
                <li><b>Target Jual Hijau 2 (Optimis):</b> {fmt_id(row_det['Target Jual 2'], 'Rp ')}</li>
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
# TAB 2: CHART CANDLESTICK TRADINGVIEW (MA 20, MA 50, MA 200)
# ==============================================================================
with tab2:
    st.markdown("### 🕯️ Grafik Candlestick Real-Time TradingView (MA 20, MA 50 & MA 200)")
    col_ch1, col_ch2 = st.columns([2, 4])
    with col_ch1:
        saham_chart = st.selectbox("Pilih Emiten / Indeks:", ["IHSG"] + JII70_RAW, index=1)
    with col_ch2:
        if saham_chart != "IHSG" and 'Kode' in df_screener.columns and saham_chart in df_screener['Kode'].values:
            r_ch = df_screener[df_screener['Kode'] == saham_chart].iloc[0]
            st.markdown(f"""
            <div style="background:rgba(15,35,25,0.85); border:1px solid rgba(74,222,128,0.3); border-radius:12px; padding:10px 16px; margin-top:22px; display:flex; gap:20px; flex-wrap:wrap;">
                <span><b>Harga Live:</b> {fmt_id(r_ch['Harga'], 'Rp ')} ({fmt_pct(r_ch['Perubahan (%)'])})</span>
                <span><b>MA20:</b> {fmt_id(r_ch['MA20'])}</span>
                <span><b>MA50:</b> {fmt_id(r_ch['MA50'])}</span>
                <span><b>MA200:</b> {fmt_id(r_ch['MA200'])}</span>
                <span><b>Sinyal:</b> <span style="color:#facc15;font-weight:700;">{r_ch['Sinyal']}</span></span>
            </div>
            """, unsafe_allow_html=True)

    render_tradingview_widget(saham_chart, height=640)

# ==============================================================================
# TAB 3: PROFIL PERUSAHAAN (BAHASA INDONESIA)
# ==============================================================================
with tab3:
    saham_profil = st.selectbox("Pilih Emiten:", JII70_RAW, key="prof_sel")
    ticker_obj = yf.Ticker(f"{saham_profil}.JK")
    info = ticker_obj.info

    sektor_id, industri_id, ringkasan_id = PROFIL_INDONESIA.get(
        saham_profil,
        (
            info.get('sector', '-'),
            info.get('industry', '-'),
            f"{info.get('longName', saham_profil)} merupakan emiten syariah yang tercatat di Bursa Efek Indonesia dan tergabung dalam indeks Jakarta Islamic Index 70 (JII70)."
        )
    )

    st.markdown(f"""
    <div class="glass-card">
        <h3 style="margin-top:0; color:#facc15;">🏢 {info.get('longName', saham_profil)} ({saham_profil})</h3>
        <p><b>Sektor Usaha:</b> {sektor_id} &nbsp;|&nbsp; <b>Sub-Industri:</b> {industri_id}</p>
        <p><b>Situs Web Resmi:</b> <a href="{info.get('website', '#')}" target="_blank" style="color:#4ade80;">{info.get('website', '-')}</a></p>
        <hr style="border-color: rgba(74,222,128,0.2);">
        <p style="text-align:justify; line-height:1.7; color:#f8fafc; font-size:0.98rem;">{ringkasan_id}</p>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Kapitalisasi Pasar", fmt_id(info.get('marketCap'), "Rp "))
    m2.metric("PER (Rasio Harga/Laba)", f"{info.get('trailingPE', 0):.2f}x" if info.get('trailingPE') else "-")
    m3.metric("PBV (Rasio Harga/Nilai Buku)", f"{info.get('priceToBook', 0):.2f}x" if info.get('priceToBook') else "-")
    m4.metric("Imbal Hasil Dividen", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "-")

# ==============================================================================
# TAB 4: WATCHLIST
# ==============================================================================
with tab4:
    st.markdown("### ⭐ Daftar Pantauan (Watchlist) Anda")
    c_wl1, c_wl2 = st.columns([3, 1])
    with c_wl1:
        tambah_wl = st.selectbox("Pilih Saham untuk Dipantau:", ["— Pilih Kode Saham —"] + JII70_RAW, key="add_wl")
    with c_wl2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("Tambah ke Watchlist", use_container_width=True):
            if tambah_wl != "— Pilih Kode Saham —":
                if f"{tambah_wl}.JK" not in st.session_state.watchlist:
                    st.session_state.watchlist.append(f"{tambah_wl}.JK")
                    st.rerun()

    if 'Ticker' in df_screener.columns and st.session_state.watchlist:
        df_wl = df_screener[df_screener["Ticker"].isin(st.session_state.watchlist)].copy()
    else:
        df_wl = pd.DataFrame()

    if df_wl.empty:
        st.info("Watchlist masih kosong. Pilih kode saham di atas lalu klik **Tambah ke Watchlist** untuk mulai memantau.")
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
# TAB 5: KALKULATOR TRADING SAHAM
# ==============================================================================
with tab5:
    st.markdown("### 🧮 Kalkulator Profit & Fee Transaksi Saham")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    c_saham1, c_saham2 = st.columns([1, 2])
    with c_saham1:
        pilih_kode_calc = st.selectbox("Pilih Emiten JII70:", ["Input Manual"] + JII70_RAW, index=1)
    with c_saham2:
        default_nama = "BBCA" if pilih_kode_calc == "Input Manual" else pilih_kode_calc
        nama_saham_manual = st.text_input("Nama / Kode Saham:", value=default_nama).strip().upper() or "-"
    
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
    st.markdown(f"<h4 style='color:#facc15;'>Simulasi Perhitungan untuk Saham: {nama_saham_manual}</h4>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#cbd5e1;'>Jumlah Lot: <b>{jumlah_lot}</b> ({total_lembar:,} Lembar)</p>".replace(",", "."), unsafe_allow_html=True)
    
    roi_color = "#4ade80" if profit_bersih >= 0 else "#f87171"
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f"""
        <div style="background:rgba(10,25,18,0.85); border:1px solid rgba(74,222,128,0.25); border-radius:12px; padding:12px 14px;">
            <div style="font-size:0.8rem; color:#cbd5e1;">Total Modal Beli ({nama_saham_manual})</div>
            <div style="font-size:1.05rem; font-weight:800; color:#ffffff; margin-top:4px; word-break:break-word;">{fmt_id(total_modal_keluar, "Rp ")}</div>
        </div>
        """, unsafe_allow_html=True)
    with r2:
        st.markdown(f"""
        <div style="background:rgba(10,25,18,0.85); border:1px solid rgba(74,222,128,0.25); border-radius:12px; padding:12px 14px;">
            <div style="font-size:0.8rem; color:#cbd5e1;">Total Hasil Jual</div>
            <div style="font-size:1.05rem; font-weight:800; color:#ffffff; margin-top:4px; word-break:break-word;">{fmt_id(total_dana_diterima, "Rp ")}</div>
        </div>
        """, unsafe_allow_html=True)
    with r3:
        st.markdown(f"""
        <div style="background:rgba(10,25,18,0.85); border:1px solid rgba(74,222,128,0.25); border-radius:12px; padding:12px 14px;">
            <div style="font-size:0.8rem; color:#cbd5e1;">Total Fee Transaksi</div>
            <div style="font-size:1.05rem; font-weight:800; color:#facc15; margin-top:4px; word-break:break-word;">{fmt_id(total_fee, "Rp ")}</div>
        </div>
        """, unsafe_allow_html=True)
    with r4:
        st.markdown(f"""
        <div style="background:rgba(10,25,18,0.85); border:1px solid rgba(74,222,128,0.25); border-radius:12px; padding:12px 14px;">
            <div style="font-size:0.8rem; color:#cbd5e1;">Profit / Loss Bersih</div>
            <div style="font-size:1.05rem; font-weight:800; color:{roi_color}; margin-top:4px; word-break:break-word;">{fmt_id(profit_bersih, "Rp ")} ({fmt_pct(roi_bersih)})</div>
        </div>
        """, unsafe_allow_html=True)
    
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
