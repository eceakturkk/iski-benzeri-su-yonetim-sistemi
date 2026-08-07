"""
İSKİ Benzeri Akıllı Su Yönetim Sistemi
Anomali Tespit Scripti

Bu script:
- Veri ambarındaki (iski_dw) tüketim verisini okur
- Her abone için ortalama ve standart sapma hesaplar (kendi geçmişine göre)
- Z-skoru yöntemiyle normalin dışına çıkan okumaları "anomali" olarak işaretler
- Sonuçları anomali_kayitlari tablosuna yazar
"""

import pandas as pd
from sqlalchemy import create_engine

# ---------------------------------------------------------
# 1. VERİTABANI BAĞLANTISI
# ---------------------------------------------------------
DB_USER = "iski"
DB_PASS = "iski123"
DB_HOST = "localhost"
DB_PORT = "5432"

engine_dw = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/iski_dw")

# Anomali eşiği: kaç standart sapma uzaktaki değerler "anomali" sayılsın
Z_ESIGI = 2.0

print("Anomali tespit süreci başlıyor...\n")

# ---------------------------------------------------------
# 2. VERİYİ ÇEK
# ---------------------------------------------------------
df = pd.read_sql("""
    SELECT 
        f.okuma_id,
        f.abone_id,
        f.mahalle_id,
        f.tarih_id,
        f.tuketim_miktari
    FROM fact_su_tuketimi f
""", engine_dw)

print(f"{len(df)} tüketim kaydı okundu.")

# ---------------------------------------------------------
# 3. ABONE BAZLI ORTALAMA VE STANDART SAPMA HESAPLA
# ---------------------------------------------------------
abone_istatistik = df.groupby("abone_id")["tuketim_miktari"].agg(
    abone_ortalama="mean",
    abone_std_sapma="std"
).reset_index()

# Bazı abonelerin std sapması NaN çıkabilir (çok az okuma varsa) - bunları 0 yapıyoruz
abone_istatistik["abone_std_sapma"] = abone_istatistik["abone_std_sapma"].fillna(0)

df = df.merge(abone_istatistik, on="abone_id", how="left")

# ---------------------------------------------------------
# 4. Z-SKORU HESAPLA
# ---------------------------------------------------------
# std_sapma 0 olan aboneler için z-skoru hesaplanamaz (bölme hatası), bunları ayrı ele alıyoruz
df["z_skoru"] = 0.0
gecerli_mask = df["abone_std_sapma"] > 0
df.loc[gecerli_mask, "z_skoru"] = (
    (df.loc[gecerli_mask, "tuketim_miktari"] - df.loc[gecerli_mask, "abone_ortalama"])
    / df.loc[gecerli_mask, "abone_std_sapma"]
)

# ---------------------------------------------------------
# 5. ANOMALİLERİ FİLTRELE
# ---------------------------------------------------------
df_anomali = df[df["z_skoru"].abs() >= Z_ESIGI].copy()

df_anomali["anomali_tipi"] = df_anomali["z_skoru"].apply(
    lambda z: "Yüksek Tüketim" if z > 0 else "Düşük Tüketim"
)

print(f"{len(df_anomali)} anomali tespit edildi (z-skoru >= {Z_ESIGI}).")

# ---------------------------------------------------------
# 6. YÜKLE — anomali_kayitlari tablosuna yaz
# ---------------------------------------------------------
df_anomali_final = df_anomali[[
    "okuma_id", "abone_id", "mahalle_id", "tarih_id",
    "tuketim_miktari", "abone_ortalama", "abone_std_sapma",
    "z_skoru", "anomali_tipi"
]].round(2)

if len(df_anomali_final) > 0:
    df_anomali_final.to_sql("anomali_kayitlari", engine_dw, if_exists="append", index=False)
    print(f"\n✅ {len(df_anomali_final)} anomali kaydı 'anomali_kayitlari' tablosuna yazıldı.")
else:
    print("\nHiç anomali bulunamadı.")

# ---------------------------------------------------------
# 7. ÖZET RAPOR (terminalde göster)
# ---------------------------------------------------------
if len(df_anomali_final) > 0:
    print("\n--- En belirgin 5 anomali ---")
    en_belirgin = df_anomali_final.reindex(
        df_anomali_final["z_skoru"].abs().sort_values(ascending=False).index
    ).head(5)
    print(en_belirgin.to_string(index=False))
