# STM Stajı – Pytest Web Test Otomasyonu

Bu proje, **STM stajı kapsamında test geliştirme çalışması** olarak hazırlanmış bir web test otomasyonu projesidir.

Projede belirlenen yazılım gereksinimleri, manuel test prosedürlerine dönüştürülmüş ve ardından **Python + pytest** kullanılarak otomatik test senaryoları halinde çalıştırılmıştır.

Test ortamı olarak **Automation Exercise** web uygulaması kullanılmıştır.

---

## Projenin Amacı

Çalışmanın temel amacı, bir web uygulamasındaki kullanıcı işlemlerinin gereksinimlere uygun şekilde çalışıp çalışmadığını otomatik olarak doğrulamaktır.

Proje kapsamında özellikle aşağıdaki süreçler test edilmiştir:

- Giriş işlemleri
- Negatif giriş senaryoları
- Kullanıcı kayıt işlemleri
- Pozitif giriş işlemleri
- Ürün ve alışveriş işlemleri
- Sepet işlemleri
- Sipariş verme
- Ürün filtreleme
- Ürün yorumlama
- İletişim formu
- Sayfa davranışları

---

## Genel Test Akışı

```text
Yazılım Gereksinimleri
        ↓
Test Senaryolarının Belirlenmesi
        ↓
Test Prosedürlerinin Hazırlanması
        ↓
Pytest Testlerinin Yazılması
        ↓
Tarayıcı Üzerinde Otomatik Çalıştırma
        ↓
Beklenen Sonuçların Kontrolü
        ↓
PASS / FAIL
```

Her test senaryosunda kullanıcı davranışı otomatik olarak gerçekleştirilir ve oluşan sonuç, gereksinimde tanımlanan beklenen davranış ile karşılaştırılır.

---

## Kullanılan Teknolojiler

- Python
- pytest
- Web browser automation
- Google Chrome
- HTML / Web UI testleri

> Staj sunumunda kullanılan tarayıcı otomasyon kütüphanesinin adı ayrıca belirtilmemiştir. Projenin test çalıştırma ve raporlama yapısı `pytest` tabanlıdır.

---

## Test Edilen Sistem

Testler aşağıdaki uygulama üzerinde gerçekleştirilmiştir:

```text
https://automationexercise.com
```

Automation Exercise, web otomasyon testleri için hazırlanmış örnek bir e-ticaret uygulamasıdır.

---

# Yazılım Gereksinimleri

Projeye başlamadan önce test edilecek fonksiyonlar gereksinimlere ayrılmıştır.

## 1. Giriş İşlemleri

Test edilen başlıca gereksinimler:

- Ana ekrandan `Signup / Login` ekranına erişilebilmesi
- Kullanıcının sisteme kayıt olabilmesi
- Kayıtlı kullanıcı ile sisteme giriş yapılabilmesi
- Boş e-mail alanında uygun uyarının gösterilmesi
- Geçersiz e-mail formatında uygun uyarının gösterilmesi
- `@` karakterinden sonra alan girilmediğinde uyarı verilmesi
- Şifre alanı boş bırakıldığında uyarı verilmesi
- Yanlış kullanıcı bilgileriyle giriş yapıldığında hata mesajı gösterilmesi

---

## 2. Alışveriş İşlemleri

Test edilen alışveriş gereksinimleri:

- Ürün üzerine gelindiğinde ürün modalının görüntülenmesi
- Ürünün sepete eklenebilmesi
- Birden fazla ürünün sepete eklenebilmesi
- Sepete eklenen ürünlerle sipariş sürecinin başlatılabilmesi
- Sipariş bilgilerinin girilebilmesi
- Satın alma işleminin tamamlanabilmesi

---

## 3. Filtreleme İşlemleri

Ürün listeleme ekranında:

- Arama alanı üzerinden ürün aranabilmesi
- Birden fazla ürün için arama yapılabilmesi
- `CATEGORY` alanının çalışması
- `BRANDS` alanının çalışması

kontrol edilmiştir.

---

## 4. Ürün İşlemleri

Ürün detaylarıyla ilgili olarak:

- Ürün detay sayfasına erişim
- Ürün bilgilerinin görüntülenmesi
- Ürüne yorum yapılması
- İletişim sayfası üzerinden mesaj gönderilmesi

senaryoları test edilmiştir.

---

## 5. Sayfa Özellikleri

Arayüz davranışları da test kapsamına alınmıştır.

Örneğin:

- Sayfa aşağı kaydırıldığında yukarı çıkma ikonunun görünmesi
- İkona basıldığında sayfanın başlangıcına dönülmesi

---

# Test Senaryoları

## Test 1 – Negatif Giriş Testi

Bu testte sistemin hatalı veya eksik giriş verilerine doğru tepki verip vermediği kontrol edilir.

### Amaç

Kullanıcının geçersiz giriş bilgileriyle sisteme giriş yapamaması ve uygun hata mesajlarının gösterilmesi.

### Kontrol Edilen Durumlar

```text
Boş e-mail + boş şifre
        ↓
Uyarı mesajı

Geçersiz e-mail formatı
        ↓
E-mail format uyarısı

Eksik domain bilgisi
        ↓
E-mail doğrulama uyarısı

Boş şifre
        ↓
Şifre alanı uyarısı

Yanlış e-mail / şifre
        ↓
Login hata mesajı
```

Örnek beklenen mesajlar:

```text
Lütfen bu alanı doldurun.
Email adresi @ içermeli.
Lütfen @ işaretinden sonra bir bölüm girin.
Şifre veya email hatalı!
```

Test başarılı olduğunda ilgili doğrulama adımı `PASS` olarak değerlendirilir.

---

## Test 2 – Kayıt Olma Testi

Yeni bir kullanıcının sisteme başarıyla kayıt olabildiği doğrulanır.

### Test Akışı

```text
Ana Sayfa
   ↓
Signup / Login
   ↓
New User Signup
   ↓
İsim Gir
   ↓
E-mail Gir
   ↓
Signup
   ↓
Account Information
   ↓
Kullanıcı Bilgilerini Gir
   ↓
Kayıt İşlemini Tamamla
```

Test sırasında kayıt ekranına erişim ve kullanıcı bilgilerinin ilgili alanlara doğru şekilde aktarılması kontrol edilir.

---

## Test 3 – Pozitif Giriş Testi

Daha önce kayıt edilmiş geçerli kullanıcı bilgileri kullanılarak sisteme başarılı şekilde giriş yapılması doğrulanır.

Örnek pytest çıktısı:

```text
3_pozitif_giris_test.py::Test_Login::test_login

Giriş ekranına giriliyor...
Email giriliyor...
Şifre giriliyor...
Giriş yapılıyor...

GİRİŞ İŞLEMİ BAŞARILI
PASSED
```

Bu testte amaç yalnızca sayfanın açılması değil, giriş işleminin gerçekten başarılı olduğunun doğrulanmasıdır.

---

## Test 4 – Alışveriş Testi

Kullanıcının giriş yaptıktan sonra ürünleri seçebilmesi ve sepet işlemlerini gerçekleştirebilmesi test edilir.

Örnek test sınıfı:

```text
4_alisveris_test.py
Test_Shopping
test_shopping
```

Temel akış:

```text
Login
  ↓
Ürünleri Görüntüle
  ↓
Ürün Seç
  ↓
Sepete Ekle
  ↓
Sepeti Kontrol Et
```

pytest testi başarıyla tamamlandığında terminal çıktısında:

```text
PASSED
```

sonucu alınır.

---

## Test 5 – Sipariş Verme Testi

Bu test, alışveriş senaryosunun devamı olarak ürünlerin sepete eklenmesi ve sipariş sürecinin ilerletilmesini kontrol eder.

Sunumdaki test akışı:

```text
Giriş işlemi
      ↓
Ürün-1 sepete ekleniyor
      ↓
Ürün-2 sepete ekleniyor
      ↓
Sepete gidiliyor
      ↓
Ürünler kontrol ediliyor
      ↓
Sipariş süreci
```

Örnek pytest testi:

```text
5_siparis_verme_test.py::Test_Order::test_order
```

Başarılı test çıktısı:

```text
Ürünler sepete başarılı bir şekilde eklendi!
PASSED
```

---

## Ürün Yorumlama Testi

Bir ürünün detay sayfasına gidilerek kullanıcı bilgilerinin ve yorum içeriğinin girilmesi test edilir.

Örnek test:

```text
8_ürün_yorumlama_test.py::Test_Comment::test_comment
```

Akış:

```text
Ürün bölümüne git
        ↓
Ürün seç
        ↓
Yorum bilgilerini gir
        ↓
Yorumu gönder
        ↓
Gönderim sonucunu doğrula
```

Örnek terminal çıktısı:

```text
Ürün bölümüne gidiyor...
Bilgiler giriliyor...
Yorum gönderiliyor...
Yorum gönderildi.
PASSED
```

---

## İletişim Testi

Web sitesindeki iletişim formunun çalışması otomatik olarak kontrol edilir.

Örnek test:

```text
9_iletişim_test.py::Test_Communication::test_communication
```

Akış:

```text
İletişim sayfasına git
        ↓
İletişim bilgilerini gir
        ↓
Mesajı gönder
        ↓
Uyarıyı onayla
        ↓
Başarılı gönderimi doğrula
```

Örnek çıktı:

```text
İletişim bilgileri giriliyor...
Gönderiliyor...
Uyarı geçiliyor...
Gönderildi.
PASSED
```

---

# Pytest Yapısı

Testler pytest'in test keşif yapısına uygun şekilde dosya, sınıf ve test fonksiyonlarına ayrılmıştır.

Örnek:

```python
class Test_Login:

    def test_login(self):
        ...
```

Test dosyaları fonksiyonel senaryolara göre ayrılmıştır.

Örnek yapı:

```text
tests/
│
├── negatif_giris_test.py
├── kayit_olma_test.py
├── 3_pozitif_giris_test.py
├── 4_alisveris_test.py
├── 5_siparis_verme_test.py
├── ...
├── 8_ürün_yorumlama_test.py
└── 9_iletişim_test.py
```

Bu yapı sayesinde her kullanıcı senaryosu bağımsız olarak çalıştırılabilir.

---

# Testlerin Çalıştırılması

Tüm pytest testlerini çalıştırmak için:

```bash
pytest
```

Daha detaylı çıktı için:

```bash
pytest -v
```

Tek bir test dosyasını çalıştırmak için:

```bash
pytest -v 4_alisveris_test.py
```

Belirli bir test fonksiyonunu çalıştırmak için:

```bash
pytest -v 4_alisveris_test.py::Test_Shopping::test_shopping
```

---

# Test Otomasyonunun Çalışma Mantığı

Projede test otomasyonu temelde üç adımdan oluşur:

```text
ACTION
   ↓
Kullanıcı işlemini gerçekleştir

ASSERT / CONTROL
   ↓
Sistemin verdiği sonucu kontrol et

RESULT
   ↓
PASS veya FAIL
```

Örneğin bir giriş testi için:

```text
Login sayfasına git
        ↓
E-mail alanını doldur
        ↓
Şifre alanını doldur
        ↓
Login butonuna bas
        ↓
Giriş sonucunu kontrol et
        ↓
PASS / FAIL
```

Bu yöntem manuel olarak tekrar tekrar gerçekleştirilecek işlemlerin kod tarafından tekrarlanmasını sağlar.

---

# Gereksinim – Test İlişkisi

Testler yalnızca sayfa üzerinde işlem yapmak için değil, tanımlanan yazılım gereksinimlerini doğrulamak için hazırlanmıştır.

Örneğin:

```text
Gereksinim 1.8

Yanlış şifre veya e-mail girilirse
"Şifre veya email hatalı!" uyarısı görünmelidir.
```

Test otomasyonu:

```text
Geçersiz kullanıcı bilgilerini gir
             ↓
Login işlemini gerçekleştir
             ↓
Hata mesajını oku
             ↓
Beklenen mesaj ile karşılaştır
             ↓
PASS / FAIL
```

Bu sayede gereksinim ile test sonucu arasında doğrudan ilişki kurulmuştur.

---

# Test Prosedürü Yaklaşımı

Her test için temel olarak aşağıdaki bilgiler belirlenmiştir:

| Alan | Açıklama |
|---|---|
| Test No | Test adımının numarası |
| Test Adımı | Gerçekleştirilecek kullanıcı işlemi |
| Beklenen Sonuç | Sistemden beklenen davranış |
| Karşılanan Gereksinim | Testin doğruladığı gereksinim |

Bu yaklaşım sayesinde manuel test prosedürleri ile otomasyon testleri aynı gereksinim tabanı üzerinden takip edilebilir.

---

# Projenin Kazandırdıkları

Bu çalışma sırasında:

- yazılım gereksinimlerinin analiz edilmesi,
- gereksinimlerden test senaryosu çıkarılması,
- pozitif ve negatif test durumlarının oluşturulması,
- web arayüzlerinin otomatik test edilmesi,
- pytest ile test organizasyonu,
- test sonuçlarının `PASS / FAIL` olarak değerlendirilmesi,
- tekrar eden manuel testlerin otomatikleştirilmesi

konularında çalışma yapılmıştır.

---

# Sonuç

STM stajında gerçekleştirilen bu çalışma ile bir e-ticaret web uygulaması için uçtan uca çalışan bir test otomasyon yaklaşımı oluşturulmuştur.

Proje akışı:

```text
Gereksinim
    ↓
Test Prosedürü
    ↓
Pytest Test Senaryosu
    ↓
Otomatik Tarayıcı İşlemleri
    ↓
Doğrulama
    ↓
PASS / FAIL
```

şeklinde tasarlanmıştır.

Böylece kullanıcı kayıt, giriş, alışveriş, sipariş, ürün yorumlama ve iletişim gibi temel web uygulaması fonksiyonları otomatik olarak test edilebilir hale getirilmiştir.
