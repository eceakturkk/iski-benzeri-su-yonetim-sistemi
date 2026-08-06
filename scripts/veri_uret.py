
import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker
from sqlalchemy import create_engine

# ---------------------------------------------------------
# 1. VERİTABANI BAĞLANTISI
# ---------------------------------------------------------
DB_USER = "iski"
DB_PASS = "iski123"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "iski_oltp"

engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

fake = Faker("tr_TR")
random.seed(42)

# ---------------------------------------------------------
# 2. MAHALLE VERİSİ
# ---------------------------------------------------------
mahalleler = [
    ("Levent", "Beşiktaş"),
    ("Etiler", "Beşiktaş"),
    ("Kadıköy Merkez", "Kadıköy"),
    ("Moda", "Kadıköy"),
    ("Bakırköy Merkez", "Bakırköy"),
    ("Ataköy", "Bakırköy"),
    ("Maltepe Merkez", "Maltepe"),
    ("Üsküdar Merkez", "Üsküdar"),
    ("Beylikdüzü Merkez", "Beylikdüzü"),
    ("Kartal Merkez", "Kartal"),
    ("Şişli Merkez", "Şişli"),
    ("Bahçelievler Merkez", "Bahçelievler"),
]

df_mahalle = pd.DataFrame(mahalleler, columns=["mahalle_adi", "ilce"])
df_mahalle.to_sql("mahalle", engine, if_exists="append", index=False)
print(f"{len(df_mahalle)} mahalle eklendi.")

# Veritabanından mahalle_id'leri geri çekelim (SERIAL otomatik atandığı için)
mahalle_ids = pd.read_sql("SELECT mahalle_id FROM mahalle", engine)["mahalle_id"].tolist()

# ---------------------------------------------------------
# 3. ABONE VERİSİ
# ---------------------------------------------------------
tarife_tipleri = ["Konut", "Ticari", "Resmi"]
n_abone = 100

abone_kayitlari = []
for _ in range(n_abone):
    abone_kayitlari.append({
        "ad_soyad": fake.name(),
        "adres": fake.street_address(),
        "mahalle_id": random.choice(mahalle_ids),
        "tarife_tipi": random.choices(tarife_tipleri, weights=[0.75, 0.20, 0.05])[0],
        "abonelik_tarihi": fake.date_between(start_date="-5y", end_date="-1y"),
        "telefon": fake.phone_number(),
    })

df_abone = pd.DataFrame(abone_kayitlari)
df_abone.to_sql("abone", engine, if_exists="append", index=False)
print(f"{len(df_abone)} abone eklendi.")

abone_ids = pd.read_sql("SELECT abone_id FROM abone", engine)["abone_id"].tolist()

# ---------------------------------------------------------
# 4. SAYAÇ VERİSİ (her abonenin 1 sayacı var)
# ---------------------------------------------------------
sayac_tipleri = ["Mekanik", "Akıllı"]

sayac_kayitlari = []
for abone_id in abone_ids:
    sayac_kayitlari.append({
        "abone_id": abone_id,
        "sayac_tipi": random.choices(sayac_tipleri, weights=[0.6, 0.4])[0],
        "kurulum_tarihi": fake.date_between(start_date="-5y", end_date="-1y"),
    })

df_sayac = pd.DataFrame(sayac_kayitlari)
df_sayac.to_sql("sayac", engine, if_exists="append", index=False)
print(f"{len(df_sayac)} sayaç eklendi.")

sayac_ids = pd.read_sql("SELECT sayac_id FROM sayac", engine)["sayac_id"].tolist()

# ---------------------------------------------------------
# 5. SAYAÇ OKUMA VERİSİ (son 12 ay, mevsimsel dalgalanmalı)
# ---------------------------------------------------------
# Yaz aylarında (Haziran-Ağustos) tüketim daha yüksek olacak şekilde kurgulanıyor
mevsim_carpani = {
    1: 0.8, 2: 0.8, 3: 0.9, 4: 1.0, 5: 1.1,
    6: 1.4, 7: 1.6, 8: 1.5, 9: 1.2, 10: 1.0,
    11: 0.9, 12: 0.85
}

bugun = date.today()
okuma_kayitlari = []

for sayac_id in sayac_ids:
    kumulatif_deger = random.uniform(100, 500)  # başlangıç sayaç değeri
    for ay_gerisi in range(12, 0, -1):
        okuma_tarihi = bugun.replace(day=1) - timedelta(days=30 * ay_gerisi)
        ay = okuma_tarihi.month

        temel_tuketim = random.uniform(8, 20)  # aylık ortalama m³
        tuketim = round(temel_tuketim * mevsim_carpani[ay] * random.uniform(0.85, 1.15), 2)

        kumulatif_deger += tuketim

        okuma_kayitlari.append({
            "sayac_id": sayac_id,
            "okuma_tarihi": okuma_tarihi,
            "okuma_degeri": round(kumulatif_deger, 2),
            "tuketim_miktari": tuketim,
        })

df_okuma = pd.DataFrame(okuma_kayitlari)
df_okuma.to_sql("sayac_okuma", engine, if_exists="append", index=False)
print(f"{len(df_okuma)} sayaç okuma kaydı eklendi.")

# ---------------------------------------------------------
# 6. ARIZA VERİSİ
# ---------------------------------------------------------
ariza_tipleri = ["Boru Patlağı", "Su Kesintisi", "Vana Arızası", "Basınç Düşüklüğü", "Sızıntı"]
durumlar = ["Kapalı", "Kapalı", "Kapalı", "Devam Ediyor"]  # çoğu kapalı olsun ki analiz zengin olsun

n_ariza = 60
ariza_kayitlari = []

for _ in range(n_ariza):
    mahalle_id = random.choice(mahalle_ids)
    baslangic = fake.date_time_between(start_date="-1y", end_date="now")
    durum = random.choice(durumlar)

    if durum == "Kapalı":
        bitis = baslangic + timedelta(hours=random.randint(1, 48))
    else:
        bitis = None

    ariza_kayitlari.append({
        "mahalle_id": mahalle_id,
        "ariza_tipi": random.choice(ariza_tipleri),
        "baslangic_tarihi": baslangic,
        "bitis_tarihi": bitis,
        "durum": durum,
        "aciklama": fake.sentence(nb_words=8),
    })

df_ariza = pd.DataFrame(ariza_kayitlari)
df_ariza.to_sql("ariza", engine, if_exists="append", index=False)
print(f"{len(df_ariza)} arıza kaydı eklendi.")

print("\n Tüm örnek veriler başarıyla yüklendi!")
