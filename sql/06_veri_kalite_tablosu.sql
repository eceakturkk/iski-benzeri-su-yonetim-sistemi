-- ============================================
-- VERİ KALİTESİ RAPORU TABLOSU (iski_dw veritabanında çalıştırılmalı)
-- ============================================

CREATE TABLE data_kalite_raporu (
    kontrol_id      SERIAL PRIMARY KEY,
    kontrol_adi     VARCHAR(150) NOT NULL,
    kategori        VARCHAR(50) NOT NULL,
    durum           VARCHAR(20) NOT NULL,
    etkilenen_kayit INTEGER NOT NULL,
    detay           TEXT,
    kontrol_tarihi  TIMESTAMP DEFAULT NOW()
);
