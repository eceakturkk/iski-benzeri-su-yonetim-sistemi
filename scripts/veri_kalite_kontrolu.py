"""
İSKİ Benzeri Akıllı Su Yönetim Sistemi
Veri Kalitesi Kontrol Scripti

Bu script, OLTP ve veri ambarındaki veriyi belirli kalite kurallarına
karşı test eder ve sonuçları data_kalite_raporu tablosuna yazar.

Kontrol edilen boyutlar:
- Bütünlük (Completeness): zorunlu alanlar boş mu
- Geçerlilik (Validity): değerler mantıklı aralıkta mı
- Teklik (Uniqueness): mükerrer kayıt var mı
- Tutarlılık (Consistency): kayıtlar birbiriyle çelişiyor mu
- Referans bütünlüğü: yetim (orphan) kayıt var mı
"""

import pandas as pd
from sqlalchemy import create_engine

DB_USER = "eticaret"
DB_PASS = "eticaret123"
DB_HOST = "localhost"
DB_PORT = "5432"

engine_oltp = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/iski_oltp")
engine_dw = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/iski_dw")

sonuclar = []


def kontrol_ekle(kontrol_adi, kategori, etkilenen_kayit, detay=""):
    """Bir kontrol sonucunu listeye ekler. etkilenen_kayit 0 ise BAŞARILI, değilse BAŞARISIZ sayılır."""
    durum = "BAŞARILI" if etkilenen_kayit == 0 else "BAŞARISIZ"
    sonuclar.append({
        "kontrol_adi": kontrol_adi,
        "kategori": kategori,
        "durum": durum,
        "etkilenen_kayit": int(etkilenen_kayit),
        "detay": detay,
    })
    isaret = "✅" if durum == "BAŞARILI" else "❌"
    print(f"{isaret} {kontrol_adi}: {etkilenen_kayit} sorunlu kayıt")


print("Veri kalitesi kontrolleri başlıyor...\n")

# ---------------------------------------------------------
# 1. BÜTÜNLÜK — zorunlu alanlar boş mu
# ---------------------------------------------------------
df_abone = pd.read_sql("SELECT * FROM abone", engine_oltp)
eksik_ad = df_abone["ad_soyad"].isna().sum()
kontrol_ekle("Abone ad_soyad alanı boş olmamalı", "Bütünlük", eksik_ad)

eksik_tarife = df_abone["tarife_tipi"].isna().sum()
kontrol_ekle("Abone tarife_tipi alanı boş olmamalı", "Bütünlük", eksik_tarife)

# ---------------------------------------------------------
# 2. GEÇERLİLİK — değerler mantıklı aralıkta mı
# ---------------------------------------------------------
df_okuma = pd.read_sql("SELECT * FROM sayac_okuma", engine_oltp)
negatif_tuketim = (df_okuma["tuketim_miktari"] < 0).sum()
kontrol_ekle("Tüketim miktarı negatif olmamalı", "Geçerlilik", negatif_tuketim)

asiri_yuksek_tuketim = (df_okuma["tuketim_miktari"] > 100).sum()
kontrol_ekle(
    "Tüketim miktarı 100 m³'ü aşan aylık okuma sayısı (aşırı yüksek şüphesi)",
    "Geçerlilik", asiri_yuksek_tuketim,
    detay="Bu bir hata olmayabilir (bkz. anomali tespiti), ama gözden geçirilmeli"
)

df_ariza = pd.read_sql("SELECT * FROM ariza", engine_oltp)
gecersiz_ariza_tarihi = (
    (df_ariza["bitis_tarihi"].notna()) &
    (df_ariza["bitis_tarihi"] < df_ariza["baslangic_tarihi"])
).sum()
kontrol_ekle("Arıza bitiş tarihi, başlangıçtan önce olmamalı", "Tutarlılık", gecersiz_ariza_tarihi)

# ---------------------------------------------------------
# 3. TEKLİK — mükerrer kayıt var mı
# ---------------------------------------------------------
mukerrer_okuma = df_okuma.duplicated(subset=["sayac_id", "okuma_tarihi"]).sum()
kontrol_ekle("Aynı sayaç için aynı tarihte mükerrer okuma olmamalı", "Teklik", mukerrer_okuma)

# ---------------------------------------------------------
# 4. TUTARLILIK — sayaç okuması, kurulum tarihinden önce olmamalı
# ---------------------------------------------------------
df_sayac = pd.read_sql("SELECT sayac_id, kurulum_tarihi FROM sayac", engine_oltp)
df_okuma_merged = df_okuma.merge(df_sayac, on="sayac_id", how="left")
df_okuma_merged["okuma_tarihi"] = pd.to_datetime(df_okuma_merged["okuma_tarihi"])
df_okuma_merged["kurulum_tarihi"] = pd.to_datetime(df_okuma_merged["kurulum_tarihi"])

erken_okuma = (df_okuma_merged["okuma_tarihi"] < df_okuma_merged["kurulum_tarihi"]).sum()
kontrol_ekle("Sayaç okuması, kurulum tarihinden önce olmamalı", "Tutarlılık", erken_okuma)

# ---------------------------------------------------------
# 5. REFERANS BÜTÜNLÜĞÜ — yetim kayıt var mı
# (Not: FK kısıtları veritabanı seviyesinde zaten bunu engelliyor,
#  bu kontrol ekstra bir güvence katmanı olarak ekleniyor)
# ---------------------------------------------------------
df_mahalle_ids = pd.read_sql("SELECT mahalle_id FROM mahalle", engine_oltp)["mahalle_id"]
yetim_abone = (~df_abone["mahalle_id"].isin(df_mahalle_ids)).sum()
kontrol_ekle("Her abone geçerli bir mahalleye bağlı olmalı", "Referans Bütünlüğü", yetim_abone)

df_abone_ids = pd.read_sql("SELECT abone_id FROM abone", engine_oltp)["abone_id"]
df_sayac_full = pd.read_sql("SELECT abone_id FROM sayac", engine_oltp)
yetim_sayac = (~df_sayac_full["abone_id"].isin(df_abone_ids)).sum()
kontrol_ekle("Her sayaç geçerli bir aboneye bağlı olmalı", "Referans Bütünlüğü", yetim_sayac)

# ---------------------------------------------------------
# SONUÇLARI KAYDET
# ---------------------------------------------------------
df_sonuc = pd.DataFrame(sonuclar)
df_sonuc.to_sql("data_kalite_raporu", engine_dw, if_exists="append", index=False)

basarili = (df_sonuc["durum"] == "BAŞARILI").sum()
basarisiz = (df_sonuc["durum"] == "BAŞARISIZ").sum()

print(f"\n{'='*50}")
print(f"TOPLAM: {len(df_sonuc)} kontrol çalıştırıldı")
print(f"✅ Başarılı: {basarili}   ❌ Başarısız: {basarisiz}")
print(f"{'='*50}")
print(f"\n✅ Sonuçlar 'data_kalite_raporu' tablosuna yazıldı.")
