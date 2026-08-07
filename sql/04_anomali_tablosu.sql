-- ============================================
-- ANOMALİ KAYITLARI TABLOSU (iski_dw veritabanında çalıştırılmalı)
-- ============================================

CREATE TABLE anomali_kayitlari (
    anomali_id        SERIAL PRIMARY KEY,
    okuma_id          INTEGER NOT NULL,          -- OLTP'deki okuma_id referansı
    abone_id          INTEGER NOT NULL REFERENCES dim_abone(abone_id),
    mahalle_id        INTEGER NOT NULL REFERENCES dim_mahalle(mahalle_id),
    tarih_id          INTEGER NOT NULL REFERENCES dim_zaman(tarih_id),
    tuketim_miktari    NUMERIC(10,2) NOT NULL,
    abone_ortalama     NUMERIC(10,2) NOT NULL,   -- abonenin ortalama tüketimi
    abone_std_sapma    NUMERIC(10,2) NOT NULL,   -- abonenin standart sapması
    z_skoru             NUMERIC(10,2) NOT NULL,   -- kaç standart sapma uzakta
    anomali_tipi        VARCHAR(30) NOT NULL,     -- 'Yüksek Tüketim' veya 'Düşük Tüketim'
    tespit_tarihi       TIMESTAMP DEFAULT NOW()
);
