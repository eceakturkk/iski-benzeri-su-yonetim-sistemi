-- ============================================
-- VERİ AMBARI ŞEMASI - STAR SCHEMA (iski_dw veritabanında çalıştırılmalı)
-- ============================================

-- ============================================
-- DIMENSION TABLOLARI
-- ============================================

-- 1. dim_zaman
CREATE TABLE dim_zaman (
    tarih_id        SERIAL PRIMARY KEY,
    tarih           DATE NOT NULL UNIQUE,
    yil             INTEGER NOT NULL,
    ay              INTEGER NOT NULL,
    ay_adi          VARCHAR(20) NOT NULL,
    ceyrek          INTEGER NOT NULL,
    mevsim          VARCHAR(20) NOT NULL
);

-- 2. dim_mahalle
CREATE TABLE dim_mahalle (
    mahalle_id      INTEGER PRIMARY KEY,   -- OLTP'deki mahalle_id ile aynı tutuyoruz
    mahalle_adi     VARCHAR(100) NOT NULL,
    ilce            VARCHAR(100) NOT NULL
);

-- 3. dim_abone
CREATE TABLE dim_abone (
    abone_id        INTEGER PRIMARY KEY,   -- OLTP'deki abone_id ile aynı
    ad_soyad        VARCHAR(150),
    tarife_tipi     VARCHAR(50),
    mahalle_id      INTEGER NOT NULL REFERENCES dim_mahalle(mahalle_id),
    abonelik_yili   INTEGER
);

-- ============================================
-- FACT TABLOLARI
-- ============================================

-- 4. fact_su_tuketimi
CREATE TABLE fact_su_tuketimi (
    fact_id           SERIAL PRIMARY KEY,
    okuma_id          INTEGER NOT NULL,     -- OLTP'deki okuma_id referansı (kaynak izlenebilirliği için)
    tarih_id          INTEGER NOT NULL REFERENCES dim_zaman(tarih_id),
    abone_id          INTEGER NOT NULL REFERENCES dim_abone(abone_id),
    mahalle_id        INTEGER NOT NULL REFERENCES dim_mahalle(mahalle_id),
    tuketim_miktari   NUMERIC(10,2) NOT NULL
);

-- 5. fact_ariza
CREATE TABLE fact_ariza (
    fact_id           SERIAL PRIMARY KEY,
    ariza_id          INTEGER NOT NULL,     -- OLTP'deki ariza_id referansı
    tarih_id          INTEGER NOT NULL REFERENCES dim_zaman(tarih_id),
    mahalle_id        INTEGER NOT NULL REFERENCES dim_mahalle(mahalle_id),
    ariza_tipi        VARCHAR(100),
    ariza_suresi_saat NUMERIC(10,2)         -- başlangıç-bitiş farkı, saat cinsinden
);
