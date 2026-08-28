-- ============================================
-- TALEP TAHMİNİ SORGUSU (iski_dw veritabanında çalıştırılır)
-- fact_tahmin tablosu hem hareketli ortalama (scripts/tahmin.py) hem de
-- Prophet (scripts/prophet_tahmin.py) sonuçlarını "yontem" sütunuyla
-- ayrıştırılmış şekilde tutar - bu sorgu ikisini karşılaştırmalı gösterir.
-- ============================================

SELECT 
    m.mahalle_adi,
    t.tahmin_yil,
    t.tahmin_ay,
    t.yontem,
    t.tahmini_tuketim
FROM fact_tahmin t
JOIN dim_mahalle m ON t.mahalle_id = m.mahalle_id
ORDER BY m.mahalle_adi, t.tahmin_yil, t.tahmin_ay, t.yontem;
