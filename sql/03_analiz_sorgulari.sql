
-- ANALİZ SORGULARI
-- Metabase dashboard'undaki 5 grafiğin kaynağı

-- 1. Mahalle bazlı toplam tüketim
SELECT 
    m.mahalle_adi,
    m.ilce,
    ROUND(SUM(f.tuketim_miktari), 2) AS toplam_tuketim
FROM fact_su_tuketimi f
JOIN dim_mahalle m ON f.mahalle_id = m.mahalle_id
GROUP BY m.mahalle_adi, m.ilce
ORDER BY toplam_tuketim DESC;

-- 2. Aylık tüketim trendi
SELECT 
    z.yil || '-' || LPAD(z.ay::text, 2, '0') AS yil_ay,
    ROUND(SUM(f.tuketim_miktari), 2) AS toplam_tuketim
FROM fact_su_tuketimi f
JOIN dim_zaman z ON f.tarih_id = z.tarih_id
GROUP BY z.yil, z.ay
ORDER BY z.yil, z.ay;

-- 3. İlçe bazlı arıza sıklığı
SELECT 
    m.ilce,
    COUNT(*) AS ariza_sayisi,
    ROUND(AVG(f.ariza_suresi_saat), 2) AS ortalama_sure_saat
FROM fact_ariza f
JOIN dim_mahalle m ON f.mahalle_id = m.mahalle_id
GROUP BY m.ilce
ORDER BY ariza_sayisi DESC;

-- 4. Tarife tipine göre ortalama tüketim
SELECT 
    a.tarife_tipi,
    ROUND(AVG(f.tuketim_miktari), 2) AS ortalama_tuketim,
    COUNT(*) AS okuma_sayisi
FROM fact_su_tuketimi f
JOIN dim_abone a ON f.abone_id = a.abone_id
GROUP BY a.tarife_tipi
ORDER BY ortalama_tuketim DESC;

-- 5. Mevsime göre ortalama tüketim
SELECT 
    z.mevsim,
    ROUND(AVG(f.tuketim_miktari), 2) AS ortalama_tuketim
FROM fact_su_tuketimi f
JOIN dim_zaman z ON f.tarih_id = z.tarih_id
GROUP BY z.mevsim
ORDER BY ortalama_tuketim DESC;
