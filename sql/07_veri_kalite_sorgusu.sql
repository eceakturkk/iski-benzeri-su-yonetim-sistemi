-- ============================================
-- VERİ KALİTESİ RAPORU SORGUSU
-- Analiz scriptinin (scripts/veri_kalite_kontrolu.py) ürettiği
-- data_kalite_raporu tablosu üzerinden çalışır

SELECT 
    kontrol_adi,
    kategori,
    durum,
    etkilenen_kayit,
    kontrol_tarihi
FROM data_kalite_raporu
ORDER BY kontrol_tarihi DESC, kategori;
