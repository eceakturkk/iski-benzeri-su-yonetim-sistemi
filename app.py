"""
İSKİ Benzeri Akıllı Su Yönetim Sistemi
Streamlit Dashboard Uygulaması

Bu, Metabase'e alternatif olarak tamamen Python ile yazılmış,
çalıştırılabilir, interaktif bir web uygulamasıdır.

Çalıştırmak için:
    streamlit run app.py
"""

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

# ---------------------------------------------------------
# SAYFA AYARLARI
# ---------------------------------------------------------
st.set_page_config(
    page_title="İSKİ Benzeri Su Yönetim Sistemi",
    page_icon="💧",
    layout="wide",
)

# ---------------------------------------------------------
# VERİTABANI BAĞLANTISI (cache'lenir, her etkileşimde tekrar kurulmaz)
# ---------------------------------------------------------
DB_USER = "eticaret"
DB_PASS = "eticaret123"
DB_HOST = "localhost"
DB_PORT = "5432"


@st.cache_resource
def get_engine():
    return create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/iski_dw")


@st.cache_data(ttl=300)  # 5 dakika cache'le, tekrar tekrar sorgu atmasın
def veri_cek(sorgu):
    return pd.read_sql(sorgu, get_engine())


# ---------------------------------------------------------
# BAŞLIK
# ---------------------------------------------------------
st.title("💧 İSKİ Benzeri Akıllı Su Yönetim Sistemi")
st.caption("Veri ambarından canlı olarak beslenen interaktif kontrol paneli")

# ---------------------------------------------------------
# ÜST ÖZET KUTULARI (KPI'lar)
# ---------------------------------------------------------
toplam_tuketim = veri_cek("SELECT ROUND(SUM(tuketim_miktari)::numeric, 0) AS v FROM fact_su_tuketimi")["v"][0]
toplam_abone = veri_cek("SELECT COUNT(*) AS v FROM dim_abone")["v"][0]
toplam_ariza = veri_cek("SELECT COUNT(*) AS v FROM fact_ariza")["v"][0]
toplam_anomali = veri_cek("SELECT COUNT(*) AS v FROM anomali_kayitlari")["v"][0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Toplam Tüketim (m³)", f"{toplam_tuketim:,.0f}")
col2.metric("Toplam Abone", f"{toplam_abone:,.0f}")
col3.metric("Toplam Arıza Kaydı", f"{toplam_ariza:,.0f}")
col4.metric("Tespit Edilen Anomali", f"{toplam_anomali:,.0f}", delta_color="inverse")

st.divider()

# ---------------------------------------------------------
# SEKME (TAB) YAPISI
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Tüketim Analizi", "🔧 Arıza Analizi", "🚨 Anomali Raporu", "📈 Talep Tahmini"
])

# ---------------------------------------------------------
# TAB 1 — TÜKETİM ANALİZİ
# ---------------------------------------------------------
with tab1:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Mahalle Bazlı Toplam Tüketim")
        df_mahalle = veri_cek("""
            SELECT m.mahalle_adi, ROUND(SUM(f.tuketim_miktari)::numeric, 2) AS toplam_tuketim
            FROM fact_su_tuketimi f
            JOIN dim_mahalle m ON f.mahalle_id = m.mahalle_id
            GROUP BY m.mahalle_adi
            ORDER BY toplam_tuketim DESC
        """)
        st.bar_chart(df_mahalle.set_index("mahalle_adi"))

    with col_b:
        st.subheader("Aylık Tüketim Trendi")
        df_aylik = veri_cek("""
            SELECT z.yil || '-' || LPAD(z.ay::text, 2, '0') AS yil_ay,
                   ROUND(SUM(f.tuketim_miktari)::numeric, 2) AS toplam_tuketim
            FROM fact_su_tuketimi f
            JOIN dim_zaman z ON f.tarih_id = z.tarih_id
            GROUP BY z.yil, z.ay
            ORDER BY z.yil, z.ay
        """)
        st.line_chart(df_aylik.set_index("yil_ay"))

    st.subheader("Tarife Tipine Göre Ortalama Tüketim")
    df_tarife = veri_cek("""
        SELECT a.tarife_tipi, ROUND(AVG(f.tuketim_miktari)::numeric, 2) AS ortalama_tuketim
        FROM fact_su_tuketimi f
        JOIN dim_abone a ON f.abone_id = a.abone_id
        GROUP BY a.tarife_tipi
        ORDER BY ortalama_tuketim DESC
    """)
    st.dataframe(df_tarife, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# TAB 2 — ARIZA ANALİZİ
# ---------------------------------------------------------
with tab2:
    st.subheader("İlçe Bazlı Arıza Sıklığı")
    df_ariza = veri_cek("""
        SELECT m.ilce, COUNT(*) AS ariza_sayisi,
               ROUND(AVG(f.ariza_suresi_saat)::numeric, 2) AS ortalama_sure_saat
        FROM fact_ariza f
        JOIN dim_mahalle m ON f.mahalle_id = m.mahalle_id
        GROUP BY m.ilce
        ORDER BY ariza_sayisi DESC
    """)
    col_c, col_d = st.columns([1, 1])
    with col_c:
        st.bar_chart(df_ariza.set_index("ilce")["ariza_sayisi"])
    with col_d:
        st.dataframe(df_ariza, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# TAB 3 — ANOMALİ RAPORU
# ---------------------------------------------------------
with tab3:
    st.subheader("Tespit Edilen Anomaliler (Olası Su Kaçağı / Sayaç Arızası)")
    st.caption(
        "Z-skoru yöntemiyle, abonenin kendi ortalamasından anlamlı şekilde sapan "
        "okumalar burada listelenir (|z| ≥ 2)."
    )

    df_anomali = veri_cek("""
        SELECT m.mahalle_adi, ab.ad_soyad, z.tarih, a.tuketim_miktari,
               a.abone_ortalama, a.z_skoru, a.anomali_tipi
        FROM anomali_kayitlari a
        JOIN dim_mahalle m ON a.mahalle_id = m.mahalle_id
        JOIN dim_abone ab ON a.abone_id = ab.abone_id
        JOIN dim_zaman z ON a.tarih_id = z.tarih_id
        ORDER BY a.z_skoru DESC
    """)

    # En kritik anomalileri kırmızı ile vurgula (basit koşullu biçimlendirme)
    st.dataframe(
        df_anomali.style.background_gradient(subset=["z_skoru"], cmap="Reds"),
        use_container_width=True, hide_index=True,
    )

# ---------------------------------------------------------
# TAB 4 — TALEP TAHMİNİ
# ---------------------------------------------------------
with tab4:
    st.subheader("Gelecek Ay Tahmini Tüketim (Yöntem Karşılaştırmalı)")
    st.caption(
        "Hareketli ortalama (basit yöntem) ile Prophet (Facebook/Meta'nın "
        "zaman serisi modeli) tahminleri yan yana karşılaştırılıyor."
    )

    df_tahmin = veri_cek("""
        SELECT m.mahalle_adi, t.tahmin_yil, t.tahmin_ay, t.yontem, t.tahmini_tuketim
        FROM fact_tahmin t
        JOIN dim_mahalle m ON t.mahalle_id = m.mahalle_id
        ORDER BY m.mahalle_adi, t.tahmin_yil, t.tahmin_ay, t.yontem
    """)

    secilen_mahalle = st.selectbox("Mahalle seç", df_tahmin["mahalle_adi"].unique())
    df_filtreli = df_tahmin[df_tahmin["mahalle_adi"] == secilen_mahalle].copy()

    # tahmin_yil ve tahmin_ay'ı tek bir okunabilir etikete birleştiriyoruz
    # (st.bar_chart çoklu index ile çalışamadığı için düz bir index gerekiyor)
    df_filtreli["yil_ay"] = (
        df_filtreli["tahmin_yil"].astype(str) + "-" +
        df_filtreli["tahmin_ay"].astype(str).str.zfill(2)
    )

    df_pivot = df_filtreli.pivot_table(
        index="yil_ay", columns="yontem", values="tahmini_tuketim"
    )
    st.bar_chart(df_pivot)
    st.dataframe(df_filtreli.drop(columns=["yil_ay"]), use_container_width=True, hide_index=True)

st.divider()
st.caption("İSKİ Veri Yönetimi ve Sistemleri Şefliği stajından ilham alınarak geliştirilmiştir.")
