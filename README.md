# İSKİ Benzeri Akıllı Su Yönetim Sistemi

İSKİ Veri Yönetimi ve Sistemleri Şefliği stajı sırasında gözlemlenen **veritabanı → orta katman (ETL) → veri ambarı** mimarisinden esinlenerek geliştirilmiş, uçtan uca bir su yönetim veri sistemi prototipidir.

Sistem; sahte ama gerçekçi abone, sayaç okuma ve arıza verisi üretir, bunları işlemsel bir veritabanında tutar, ETL süreciyle analiz odaklı bir veri ambarına aktarır ve son olarak bir BI aracıyla görselleştirir.

## Mimari

```mermaid
flowchart LR
    A[Python<br/>Veri Üretimi] -->|INSERT| B[(PostgreSQL<br/>iski_oltp<br/>OLTP)]
    B -->|Extract| C[Python ETL<br/>Orta Katman]
    C -->|Transform| C
    C -->|Load| D[(PostgreSQL<br/>iski_dw<br/>Veri Ambarı)]
    D --> E[Metabase<br/>Dashboard]
```

Bu üç katman, İSKİ'deki **Veritabanı, Orta Katman ve Veri Ambarı** birimlerinin küçük ölçekli bir yansımasıdır.

| Katman | Rol | Teknoloji |
|---|---|---|
| Veritabanı (OLTP) | Ham, işlemsel veri | PostgreSQL |
| Orta Katman | Veri çekme, temizleme, dönüştürme | Python (pandas, SQLAlchemy) |
| Veri Ambarı (OLAP) | Analiz odaklı, star schema | PostgreSQL |
| Görselleştirme | Dashboard, raporlama | Metabase |

## Veri Modeli

### OLTP Şeması (iski_oltp)
- `mahalle` — mahalle/ilçe bilgisi
- `abone` — abone bilgisi (mahalleye bağlı)
- `sayac` — su sayaçları (aboneye bağlı)
- `sayac_okuma` — periyodik tüketim okumaları
- `ariza` — arıza/kesinti kayıtları (mahalleye bağlı)

### Veri Ambarı Şeması (iski_dw) — Star Schema
**Dimension tablolar:**
- `dim_zaman` — yıl, ay, çeyrek, mevsim
- `dim_mahalle` — mahalle, ilçe
- `dim_abone` — abone, tarife tipi, abonelik yılı

**Fact tablolar:**
- `fact_su_tuketimi` — tüketim miktarı (tarih, abone, mahalle ile ilişkili)
- `fact_ariza` — arıza süresi ve tipi (tarih, mahalle ile ilişkili)

**Analiz tablosu:**
- `anomali_kayitlari` — z-skoru yöntemiyle tespit edilen anormal tüketim kayıtları

## Dashboard

Metabase üzerinde aşağıdaki analizler oluşturuldu:

1. **Mahalle Bazlı Toplam Tüketim** — hangi mahallede su tüketimi en yüksek
2. **Aylık Tüketim Trendi** — zaman içinde tüketim değişimi, mevsimsellik
3. **İlçe Bazlı Arıza Sıklığı** — hangi ilçede arıza yoğunluğu fazla
4. **Tarife Tipine Göre Ortalama Tüketim** — konut/ticari/resmi karşılaştırması
5. **Mevsime Göre Ortalama Tüketim** — yaz/kış tüketim farkı

## Kurulum

### Gereksinimler
- Docker Desktop
- Python 3.10+
- pgAdmin (opsiyonel, veritabanı yönetimi için)

## Kullanılan Analiz Sorguları

Tüm SQL analiz sorguları `sql/03_analiz_sorgulari.sql` dosyasında yer almaktadır.

## Anomali Tespiti

`scripts/anomali_tespit.py`, her abonenin **kendi geçmiş tüketim ortalaması ve standart sapmasına** göre z-skoru hesaplayarak, normalin dışına çıkan (|z| ≥ 2) okumaları **anomali** olarak işaretler. Bu, olası su kaçağı, sayaç arızası veya anormal kullanım gibi durumları erken yakalamayı amaçlar.

## Not

Bu proje, İSKİ Veri Yönetimi ve Sistemleri Şefliği stajı sırasında edinilen gözlemlerden ilham alınarak, tamamen sahte/simüle veriyle, öğrenme amacıyla geliştirilmiştir. Gerçek İSKİ verisi veya sistemleriyle hiçbir bağlantısı yoktur.

## Kullanılan Teknolojiler

- PostgreSQL 16
- Python (pandas, SQLAlchemy, Faker)
- Docker
- Metabase
- pgAdmin
