
import pandas as pd
from sqlalchemy import create_engine

# ---------------------------------------------------------
# 1. VERİTABANI BAĞLANTILARI
# ---------------------------------------------------------
DB_USER = "eticaret"
DB_PASS = "eticaret123"
DB_HOST = "localhost"
DB_PORT = "5432"

engine_oltp = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/iski_oltp")
engine_dw = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/iski_dw")

MEVSIM_MAP = {
    12: "Kış", 1: "Kış", 2: "Kış",
    3: "İlkbahar", 4: "İlkbahar", 5: "İlkbahar",
    6: "Yaz", 7: "Yaz", 8: "Yaz",
    9: "Sonbahar", 10: "Sonbahar", 11: "Sonbahar",
}

AY_ADLARI = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
    7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık",
}

print("ETL süreci başlıyor...\n")

# ---------------------------------------------------------
# 2. EXTRACT — OLTP'den ham veriyi çek
# ---------------------------------------------------------
df_mahalle_src = pd.read_sql("SELECT * FROM mahalle", engine_oltp)
df_abone_src = pd.read_sql("SELECT * FROM abone", engine_oltp)
df_okuma_src = pd.read_sql("SELECT * FROM sayac_okuma", engine_oltp)
df_sayac_src = pd.read_sql("SELECT * FROM sayac", engine_oltp)
df_ariza_src = pd.read_sql("SELECT * FROM ariza", engine_oltp)

print("Extract tamamlandı: OLTP'den veriler çekildi.")

# ---------------------------------------------------------
# 3. TRANSFORM + LOAD — dim_mahalle
# ---------------------------------------------------------
df_dim_mahalle = df_mahalle_src[["mahalle_id", "mahalle_adi", "ilce"]].copy()
df_dim_mahalle.to_sql("dim_mahalle", engine_dw, if_exists="append", index=False)
print(f"dim_mahalle yüklendi: {len(df_dim_mahalle)} kayıt.")

# ---------------------------------------------------------
# 4. TRANSFORM + LOAD — dim_abone
# ---------------------------------------------------------
df_dim_abone = df_abone_src[["abone_id", "ad_soyad", "tarife_tipi", "mahalle_id"]].copy()
df_dim_abone["abonelik_yili"] = pd.to_datetime(df_abone_src["abonelik_tarihi"]).dt.year
df_dim_abone.to_sql("dim_abone", engine_dw, if_exists="append", index=False)
print(f"dim_abone yüklendi: {len(df_dim_abone)} kayıt.")

# ---------------------------------------------------------
# 5. TRANSFORM + LOAD — dim_zaman
# ---------------------------------------------------------
# sayaç okuma ve arıza tarihlerinin tamamını birleştirip, tekil tarihlerden dim_zaman kuruyoruz
tarihler_okuma = pd.to_datetime(df_okuma_src["okuma_tarihi"]).dt.date
tarihler_ariza = pd.to_datetime(df_ariza_src["baslangic_tarihi"]).dt.date

tum_tarihler = pd.Series(pd.concat([tarihler_okuma, tarihler_ariza]).unique())
tum_tarihler = pd.to_datetime(tum_tarihler).sort_values().reset_index(drop=True)

df_dim_zaman = pd.DataFrame({"tarih": tum_tarihler})
df_dim_zaman["yil"] = df_dim_zaman["tarih"].dt.year
df_dim_zaman["ay"] = df_dim_zaman["tarih"].dt.month
df_dim_zaman["ay_adi"] = df_dim_zaman["ay"].map(AY_ADLARI)
df_dim_zaman["ceyrek"] = df_dim_zaman["tarih"].dt.quarter
df_dim_zaman["mevsim"] = df_dim_zaman["ay"].map(MEVSIM_MAP)

df_dim_zaman.to_sql("dim_zaman", engine_dw, if_exists="append", index=False)
print(f"dim_zaman yüklendi: {len(df_dim_zaman)} kayıt.")

# dim_zaman'ı geri oku (tarih -> tarih_id eşlemesi için, SERIAL id'ler DB tarafında atandı)
df_dim_zaman_db = pd.read_sql("SELECT tarih_id, tarih FROM dim_zaman", engine_dw)
df_dim_zaman_db["tarih"] = pd.to_datetime(df_dim_zaman_db["tarih"])
tarih_to_id = dict(zip(df_dim_zaman_db["tarih"], df_dim_zaman_db["tarih_id"]))

# ---------------------------------------------------------
# 6. TRANSFORM + LOAD — fact_su_tuketimi
# ---------------------------------------------------------
# sayac_okuma -> sayac -> abone -> mahalle_id zincirini kurmamız lazım
df_okuma_merged = df_okuma_src.merge(
    df_sayac_src[["sayac_id", "abone_id"]], on="sayac_id", how="left"
).merge(
    df_abone_src[["abone_id", "mahalle_id"]], on="abone_id", how="left"
)

df_okuma_merged["okuma_tarihi"] = pd.to_datetime(df_okuma_merged["okuma_tarihi"])
df_okuma_merged["tarih_id"] = df_okuma_merged["okuma_tarihi"].map(tarih_to_id)

df_fact_tuketim = df_okuma_merged[[
    "okuma_id", "tarih_id", "abone_id", "mahalle_id", "tuketim_miktari"
]].copy()

df_fact_tuketim.to_sql("fact_su_tuketimi", engine_dw, if_exists="append", index=False)
print(f"fact_su_tuketimi yüklendi: {len(df_fact_tuketim)} kayıt.")

# ---------------------------------------------------------
# 7. TRANSFORM + LOAD — fact_ariza
# ---------------------------------------------------------
df_ariza_src["baslangic_tarihi"] = pd.to_datetime(df_ariza_src["baslangic_tarihi"])
df_ariza_src["bitis_tarihi"] = pd.to_datetime(df_ariza_src["bitis_tarihi"])

df_ariza_src["ariza_suresi_saat"] = (
    (df_ariza_src["bitis_tarihi"] - df_ariza_src["baslangic_tarihi"]).dt.total_seconds() / 3600
)

# tarih_id eşlemesi için sadece tarih kısmını (saat olmadan) kullanıyoruz
df_ariza_src["tarih_only"] = df_ariza_src["baslangic_tarihi"].dt.normalize()
df_ariza_src["tarih_id"] = df_ariza_src["tarih_only"].map(tarih_to_id)

df_fact_ariza = df_ariza_src[[
    "ariza_id", "tarih_id", "mahalle_id", "ariza_tipi", "ariza_suresi_saat"
]].copy()

df_fact_ariza.to_sql("fact_ariza", engine_dw, if_exists="append", index=False)
print(f"fact_ariza yüklendi: {len(df_fact_ariza)} kayıt.")

print("\n ETL süreci başarıyla tamamlandı! Veri ambarı dolduruldu.")
