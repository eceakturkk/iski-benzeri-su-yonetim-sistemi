-- ============================================
-- TALEP TAHMİNİ TABLOSU (iski_dw veritabanında çalıştırılmalı)
-- Hem hareketli ortalama (scripts/tahmin.py) hem de Prophet
-- (scripts/prophet_tahmin.py) sonuçları bu tabloya, "yontem" sütunuyla
-- ayrıştırılarak yazılır.
-- ============================================

CREATE TABLE fact_tahmin (
    tahmin_id         SERIAL PRIMARY KEY,
    mahalle_id        INTEGER NOT NULL REFERENCES dim_mahalle(mahalle_id),
    tahmin_yil         INTEGER NOT NULL,
    tahmin_ay          INTEGER NOT NULL,
    tahmini_tuketim     NUMERIC(10,2) NOT NULL,
    yontem              VARCHAR(50) NOT NULL,
    olusturma_tarihi    TIMESTAMP DEFAULT NOW()
);
