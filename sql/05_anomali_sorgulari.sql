-- ============================================
-- ANOMALİ ANALİZ SORGULARI (iski_dw veritabanında çalıştırılır)
-- Anomali tespit scriptinin (scripts/anomali_tespit.py) ürettiği
-- anomali_kayitlari tablosu üzerinden çalışır
-- ============================================

-- 1. Anomali Tespit Raporu (detaylı liste)
SELECT 
    a.anomali_id,
    m.mahalle_adi,
    m.ilce,
    z.tarih,
    ab.ad_soyad,
    a.tuketim_miktari,
    a.abone_ortalama,
    a.z_skoru,
    a.anomali_tipi
FROM anomali_kayitlari a
JOIN dim_mahalle m ON a.mahalle_id = m.mahalle_id
JOIN dim_zaman z ON a.tarih_id = z.tarih_id
JOIN dim_abone ab ON a.abone_id = ab.abone_id
ORDER BY a.z_skoru DESC;

-- 2. Mahalle Bazlı Anomali Yoğunluğu
SELECT 
    m.mahalle_adi,
    COUNT(*) AS anomali_sayisi
FROM anomali_kayitlari a
JOIN dim_mahalle m ON a.mahalle_id = m.mahalle_id
GROUP BY m.mahalle_adi
ORDER BY anomali_sayisi DESC;
