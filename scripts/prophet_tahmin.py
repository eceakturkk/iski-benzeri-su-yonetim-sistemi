"""
Gelişmiş Talep Tahmini (Prophet)

Bu script, basit hareketli ortalama yönteminin (tahmin.py) yerine/yanına
Facebook/Meta'nın geliştirdiği Prophet kütüphanesiyle gerçek bir zaman
serisi modeli kurar.
"""

import logging
import pandas as pd
from sqlalchemy import create_engine
from prophet import Prophet

# Prophet/cmdstanpy'nin ayrıntılı loglarını sustur (terminali kirletmesin)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
logging.getLogger("prophet").setLevel(logging.WARNING)

DB_USER = "eticaret"
DB_PASS = "eticaret123"
DB_HOST = "localhost"
DB_PORT = "5432"

engine_dw = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/iski_dw")

TAHMIN_AY_SAYISI = 3   # gelecek kaç ayı tahmin edeceğiz
YONTEM_ADI = "Prophet (Facebook/Meta)"

print("Prophet ile talep tahmini başlıyor...\n")

# ---------------------------------------------------------
# 1. VERİYİ ÇEK — mahalle + ay bazında toplam tüketim

df = pd.read_sql("""
    SELECT 
        f.mahalle_id,
        z.yil,
        z.ay,
        SUM(f.tuketim_miktari) AS aylik_tuketim
    FROM fact_su_tuketimi f
    JOIN dim_zaman z ON f.tarih_id = z.tarih_id
    GROUP BY f.mahalle_id, z.yil, z.ay
    ORDER BY f.mahalle_id, z.yil, z.ay
""", engine_dw)

df["ds"] = pd.to_datetime(dict(year=df["yil"], month=df["ay"], day=1))

print(f"{len(df)} mahalle-ay satırı okundu.")
print(f"{df['mahalle_id'].nunique()} mahalle için model kurulacak.\n")

# ---------------------------------------------------------
# 2. HER MAHALLE İÇİN AYRI PROPHET MODELİ KUR

tahmin_kayitlari = []

for mahalle_id, grup in df.groupby("mahalle_id"):
    grup_prophet = grup[["ds", "aylik_tuketim"]].rename(columns={"aylik_tuketim": "y"})
    grup_prophet = grup_prophet.sort_values("ds")

    if len(grup_prophet) < 4:
        # Prophet için çok az veri varsa bu mahalleyi atla
        print(f" Mahalle {mahalle_id}: yetersiz veri, atlanıyor.")
        continue

    # Sadece 1 yıllık veri olduğu için yıllık/haftalık mevsimselliği kapatıyoruz
    # (yeterli tekrar olmadan mevsimsellik güvenilir öğrenilemez)
    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
        interval_width=0.80,  # %80 güven aralığı
    )
    model.fit(grup_prophet)

    # Gelecek TAHMIN_AY_SAYISI ayı için tarih iskeleti oluştur
    gelecek = model.make_future_dataframe(periods=TAHMIN_AY_SAYISI, freq="MS")
    tahmin = model.predict(gelecek)

    # Sadece GERÇEKTEN gelecekteki (geçmişte olmayan) satırları al
    son_gecmis_tarih = grup_prophet["ds"].max()
    gelecek_tahminler = tahmin[tahmin["ds"] > son_gecmis_tarih]

    for _, satir in gelecek_tahminler.iterrows():
        tahmin_kayitlari.append({
            "mahalle_id": mahalle_id,
            "tahmin_yil": satir["ds"].year,
            "tahmin_ay": satir["ds"].month,
            "tahmini_tuketim": round(max(satir["yhat"], 0), 2),  # negatif tahmin olmasın
            "yontem": YONTEM_ADI,
        })

    print(f" Mahalle {mahalle_id}: {TAHMIN_AY_SAYISI} aylık tahmin üretildi.")

df_tahmin = pd.DataFrame(tahmin_kayitlari)

# ---------------------------------------------------------
# 3. YÜKLE — fact_tahmin tablosuna yaz (hareketli ortalama ile aynı tablo,
#    farklı "yontem" değeriyle - böylece dashboard'da iki yöntemi karşılaştırabiliriz)

df_tahmin.to_sql("fact_tahmin", engine_dw, if_exists="append", index=False)

print(f"\n{'='*50}")
print(f" {len(df_tahmin)} Prophet tahmini 'fact_tahmin' tablosuna yazıldı.")
print(f"{'='*50}")
print("\n--- Örnek tahminler (ilk 10) ---")
print(df_tahmin.head(10).to_string(index=False))
