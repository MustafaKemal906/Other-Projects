# ROS Tarımsal Sıra Tespiti

Bu proje, ROS ve OpenCV kullanarak kamera görüntüsünden **tarım sıralarını ve yeşil bitki bölgelerini tespit etmek** için geliştirilmiştir.

Sistem ROS üzerinden gelen kamera görüntüsünü alır, görüntü işleme adımları uygular ve farklı yöntemlerle bitki sıralarının yönünü bulmaya çalışır.

---

## Genel Akış

```text
ROS Kamera Görüntüsü
        ↓
CvBridge
        ↓
Görüntü İşleme
        ↓
Bitki Bölgesini Ayırma
        ↓
Sıra Noktalarını Bulma
        ↓
Hough Transform
        ↓
Tarım Sıralarını Gösterme
```

Projede ayrıca farklı deneme yöntemleri de bulunmaktadır:

```text
HSV Yeşil Maske
   ├── Kütle Merkezi
   ├── Kontur Tespiti
   └── Convex Hull
```

---

## ROS Kamera Girdisi

Kodlar aşağıdaki ROS görüntü topic'ine abone olur:

```text
/atom/zed2/left/image_rect_color
```

ROS'tan gelen `sensor_msgs/Image` mesajları `CvBridge` ile OpenCV görüntüsüne çevrilir.

---

## Kullanılan Teknolojiler

- ROS 1
- Python 3
- OpenCV
- NumPy
- rospy
- sensor_msgs
- cv_bridge

---

## Proje Dosyaları

```text
.
├── ekinoks.py
├── main.py
├── detection.py
├── detection_main.py
├── center_detection.py
└── 763ef48f-1564-4ab0-9626-d6a59be3a664.py
```

---

## `ekinoks.py`

Temel tarım sırası tespit algoritmasıdır.

İşlem sırası:

```text
Kamera Görüntüsü
        ↓
2G - R - B
        ↓
Otsu Threshold
        ↓
Yatay Şeritlere Bölme
        ↓
Dikey Piksel Toplamı
        ↓
Geçiş Noktalarını Bulma
        ↓
Sıra Merkez Noktaları
        ↓
Hough Transform
        ↓
Tarım Sırası Çizgileri
```

Bitki bölgelerini belirginleştirmek için:

```python
2 * G - R - B
```

ifadesi kullanılır.

Daha sonra görüntü Otsu yöntemi ile siyah-beyaz hale getirilir.

---

## Şerit Tabanlı Algoritma

Görüntü yatay şeritlere bölünür.

Varsayılan değerler:

```python
NUMBER_OF_STRIPS = 10
SUM_THRESH = 2
DIFF_NOISE_THRESH = 8
```

Her şerit için görüntünün sütunlarındaki bitki piksel miktarı hesaplanır.

```text
Sütun
  ↓
Bitki Piksel Toplamı
  ↓
Threshold
  ↓
Bitki Var / Yok
```

Bitkinin başladığı ve bittiği noktalar bulunur.

Yeterince geniş bir bitki bölgesinin orta noktası, tarım sırası için aday nokta olarak kaydedilir.

Bu noktalar daha sonra Hough Transform'a gönderilir.

---

## Hough Transform

Aday noktalar kullanılarak tarım sıralarının doğrusal yapısı bulunur.

Kullanılan temel parametreler:

```python
HOUGH_RHO = 5
HOUGH_ANGLE = pi / 180
HOUGH_THRESH = 6
```

Çok eğimli yanlış çizgileri elemek için:

```python
ANGLE_THRESH = 30°
```

değeri kullanılır.

---

## `detection.py`

Bu dosyada kontur tabanlı farklı bir yöntem denenmiştir.

Akış:

```text
Binary Görüntü
      ↓
Gaussian Blur
      ↓
Adaptive Threshold
      ↓
Morphological Closing
      ↓
Contour Detection
      ↓
Alan Filtreleme
```

Küçük konturlar elenir ve kalan bölgeler bitki veya tarım sırası adayı olarak gösterilir.

---

## `detection_main.py`

Kontur tabanlı yöntemin başka bir deneme sürümüdür.

Kullanılan işlemler:

- Grayscale dönüşümü
- Gaussian Blur
- Adaptive Threshold
- Morphological Closing
- Contour Detection
- Alan filtresi

Kod içinde test için şu görüntü kullanılır:

```text
./img/2_image_bin_2.jpg
```

---

## `center_detection.py`

Yeşil alanın merkezini bulmak için kullanılan deneme yöntemidir.

Öncelikle görüntü HSV renk uzayına çevrilir.

Yeşil renk aralığı:

```python
lower_green = [35, 50, 50]
upper_green = [85, 255, 255]
```

Daha sonra görüntü momentleri kullanılarak yeşil alanın kütle merkezi hesaplanır.

```text
RGB Görüntü
    ↓
HSV
    ↓
Yeşil Maske
    ↓
Image Moments
    ↓
Kütle Merkezi
    ↓
Referans Çizgisi
```

---

## `main.py`

Bu dosyada yeşil bitki bölgeleri geometrik olarak analiz edilir.

İşlem sırası:

```text
Kamera Görüntüsü
        ↓
HSV Yeşil Maske
        ↓
Konturlar
        ↓
Sol / Sağ Ayrımı
        ↓
Convex Hull
        ↓
Yön Hesabı
        ↓
Tarım Sırası Geometrisi
```

Kontur noktaları görüntünün sol ve sağ tarafı olarak iki gruba ayrılır.

Her taraf için:

1. Kontur noktaları alınır.
2. Convex Hull hesaplanır.
3. Merkez bulunur.
4. Üst ve alt noktalar bulunur.
5. Yön vektörü hesaplanır.
6. Görüntü üzerine yön çizgisi çizilir.

---

## Alternatif Convex Hull Dosyası

`763ef48f-1564-4ab0-9626-d6a59be3a664.py` dosyası `main.py` içerisindeki Convex Hull yaklaşımının alternatif bir sürümüdür.

Bu yöntemde:

- Yeşil alanlar ayrılır.
- Noktalar sol ve sağ olarak ikiye bölünür.
- Convex Hull hesaplanır.
- Yön vektörü bulunur.
- Sonuç kamera görüntüsü üzerine çizilir.

---

## Yeşil Bitki Tespiti

Bazı yöntemlerde `2G - R - B` yerine HSV renk filtresi kullanılır.

Kullanılan yeşil aralığı:

```python
lower_green = np.array([35, 50, 50])
upper_green = np.array([85, 255, 255])
```

Bu değerler aşağıdaki şartlara göre değiştirilebilir:

- Işık miktarı
- Kamera ayarları
- Bitki türü
- Toprak rengi
- Hava koşulları

---

## Kaydedilen Ara Görüntüler

Debug amacıyla bazı görüntüler kaydedilir.

Örnek dosyalar:

```text
0_image_in
1_image_gray
2_image_bin
8_crop_points
9_image_hough
nihai
```

Kaydedilecek frame numaraları:

```python
images_to_save = [2, 3, 4, 5]
```

---

## Çalıştırma

Öncelikle ROS ve kamera sistemi çalışıyor olmalıdır.

Ardından workspace aktif edilir:

```bash
source ~/catkin_ws/devel/setup.bash
```

Temel algoritmayı çalıştırmak için:

```bash
python3 ekinoks.py
```

Geometrik yöntemi çalıştırmak için:

```bash
python3 main.py
```

Kontur tabanlı yöntemi çalıştırmak için:

```bash
python3 detection.py
```

Merkez tespitini çalıştırmak için:

```bash
python3 center_detection.py
```

---

## Önemli Notlar

Bazı dosyalarda bilgisayara özel sabit klasör yolları bulunmaktadır:

```text
/home/mustafa/catkin_ws/src/atom/script/img
/home/mustafa/catkin_ws/src/atom/script2/img
```

Başka bir bilgisayarda çalıştırmadan önce bu yollar değiştirilmelidir.

Bazı deneysel kodlar ayrıca sabit test görüntüleri kullanır:

```text
./img/green_2.jpg
./img/2_image_bin_2.jpg
```

---

## Algoritma Özeti

```text
                    ROS Kamera
                        ↓
                 OpenCV / CvBridge
                        ↓
          ┌─────────────┴─────────────┐
          ↓                           ↓
      2G - R - B                HSV Yeşil Maske
          ↓                           ↓
    Otsu Threshold          ┌─────────┼─────────┐
          ↓                 ↓         ↓         ↓
    Şerit İşleme        Merkez     Kontur   Convex Hull
          ↓
    Aday Noktalar
          ↓
   Hough Transform
          ↓
 Tarım Sırası Çizgileri
```

---

## Projenin Amacı

Bu projenin amacı, tarım alanında kamera görüntülerinden bitki sıralarını otomatik olarak tespit etmek için farklı görüntü işleme yöntemlerini denemektir.

Projede kullanılan başlıca yöntemler:

- `2G - R - B` bitki belirginleştirme
- Otsu threshold
- Şerit tabanlı sıra tespiti
- Hough Transform
- Adaptive Threshold
- Kontur tespiti
- HSV yeşil renk filtresi
- Kütle merkezi hesabı
- Convex Hull analizi
