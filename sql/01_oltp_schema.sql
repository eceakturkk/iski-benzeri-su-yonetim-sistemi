
-- OLTP ŞEMASI 

-- 1. MAHALLE tablosu
CREATE TABLE mahalle (
    mahalle_id      SERIAL PRIMARY KEY,
    mahalle_adi     VARCHAR(100) NOT NULL,
    ilce            VARCHAR(100) NOT NULL
);

-- 2. ABONE tablosu
CREATE TABLE abone (
    abone_id        SERIAL PRIMARY KEY,
    ad_soyad        VARCHAR(150) NOT NULL,
    adres           VARCHAR(255),
    mahalle_id      INTEGER NOT NULL REFERENCES mahalle(mahalle_id),
    tarife_tipi     VARCHAR(50) NOT NULL,   -- örn: 'Konut', 'Ticari', 'Resmi'
    abonelik_tarihi DATE NOT NULL,
    telefon         VARCHAR(50)
);

-- 3. SAYAC tablosu
CREATE TABLE sayac (
    sayac_id        SERIAL PRIMARY KEY,
    abone_id        INTEGER NOT NULL REFERENCES abone(abone_id),
    sayac_tipi      VARCHAR(50),            -- örn: 'Mekanik', 'Akıllı'
    kurulum_tarihi  DATE NOT NULL
);

-- 4. SAYAC_OKUMA tablosu
CREATE TABLE sayac_okuma (
    okuma_id        SERIAL PRIMARY KEY,
    sayac_id        INTEGER NOT NULL REFERENCES sayac(sayac_id),
    okuma_tarihi    DATE NOT NULL,
    okuma_degeri    NUMERIC(10,2) NOT NULL,   -- kümülatif sayaç değeri (m³)
    tuketim_miktari NUMERIC(10,2)             -- bir önceki okumaya göre fark (m³)
);

-- 5. ARIZA tablosu
CREATE TABLE ariza (
    ariza_id          SERIAL PRIMARY KEY,
    mahalle_id        INTEGER NOT NULL REFERENCES mahalle(mahalle_id),
    ariza_tipi        VARCHAR(100),          -- örn: 'Boru Patlağı', 'Su Kesintisi'
    baslangic_tarihi  TIMESTAMP NOT NULL,
    bitis_tarihi      TIMESTAMP,
    durum             VARCHAR(30) DEFAULT 'Açık',  -- 'Açık', 'Kapalı', 'Devam Ediyor'
    aciklama          TEXT
);
