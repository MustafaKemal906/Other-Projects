# Half-Moon Sensör MTF Analizi

Bu proje, iki farklı yönde çekilmiş **half-moon hedef görüntülerini** kullanarak bir görüntüleme sensörünün **X ve Y yönündeki MTF değerlerini** hesaplamak için geliştirilmiştir.

Program iki `.mat` dosyasını ayrı ayrı analiz eder ve bulunan kenarın yönüne göre sonucu otomatik olarak `MTF_X` veya `MTF_Y` olarak sınıflandırır.

---

## Genel Akış

```text
Half-Moon Görüntüsü
        ↓
Kenar Tespiti
        ↓
Düz Kenarın Bulunması
        ↓
ESF
        ↓
LSF
        ↓
FFT
        ↓
MTF
        ↓
MTF_X / MTF_Y
```

---

## MTF Nasıl Hesaplanıyor?

Öncelikle hedef üzerindeki düz kenar bulunur.

Bu kenardan **Edge Spread Function (ESF)** elde edilir.

ESF'nin türevi alınarak **Line Spread Function (LSF)** hesaplanır:

\[
LSF(x)=\frac{d}{dx}ESF(x)
\]

Daha sonra LSF'nin Fourier dönüşümü alınır:

\[
MTF(f)=|\mathcal{F}\{LSF(x)\}|
\]

Sonuç normalize edilir:

\[
MTF(0)=1
\]

---

## Sensör Bilgisi

Projede kullanılan piksel boyutu:

```python
PIXEL_PITCH_MM = 0.017
```

Yani:

```text
Piksel boyutu = 0.017 mm = 17 µm
```

Sensörün Nyquist frekansı yaklaşık olarak:

```text
29.41 lp/mm
```

---

## Girdi Dosyaları

Program iki adet MATLAB `.mat` dosyası alır.

Örnek:

```text
capture_01.mat
capture_02.mat
```

Varsayılan MATLAB değişkeni:

```text
img_final
```

---

## Kullanım

```bash
python main.py first_capture.mat second_capture.mat
```

Örnek:

```bash
python main.py data/capture_01.mat data/capture_02.mat
```

Dosyaların sırası önemli değildir. Program kenarın yönüne göre hangi görüntünün `MTF_X`, hangisinin `MTF_Y` olduğunu otomatik belirler.

---

## Komut Seçenekleri

Farklı MAT değişkeni kullanmak için:

```bash
python main.py first.mat second.mat --mat-key image
```

Grafikleri göstermeden çalıştırmak için:

```bash
python main.py first.mat second.mat --no-graphs
```

MATLAB HDF5 transpose işlemini kapatmak için:

```bash
python main.py first.mat second.mat --no-hdf5-transpose
```

---

## Proje Yapısı

```text
project/
│
├── main.py
│
└── src/
    ├── variables.py
    ├── mtf_pipeline.py
    ├── graph.py
    └── ...
```

### `variables.py`

Görüntü dosyası ve sensör bilgilerini tutar.

### `mtf_pipeline.py`

MTF hesaplama işlemlerini gerçekleştirir.

### `graph.py`

ESF, LSF ve MTF grafiklerini oluşturur.

### `main.py`

Programın çalıştırıldığı ana dosyadır.

---

## Neden İki Görüntü Kullanılıyor?

Tek bir düz kenar ölçümü yalnızca kenara dik yöndeki MTF bilgisini verir.

Bu nedenle hedef iki farklı yönde çekilir.

```text
Görüntü 1
   ↓
Kenar yönü
   ↓
MTF_X veya MTF_Y

Görüntü 2
   ↓
Kenar yönü
   ↓
Diğer MTF yönü
```

Böylece sensörün hem yatay hem dikey yöndeki görüntü performansı ölçülebilir.

---

## Neden Half-Moon Hedef?

Half-moon hedef üzerinde kullanılabilecek düz bir kenar bulunur.

Bu kenar sayesinde klasik:

```text
ESF
 ↓
LSF
 ↓
FFT
 ↓
MTF
```

yöntemi uygulanabilir.

---

## Grafikler

Program her iki yön için ayrı ayrı:

```text
ESF
LSF
MTF
```

grafiklerini oluşturabilir.

Ayrıca `MTF_X` ve `MTF_Y` karşılaştırması da gösterilebilir.

---

## Dikkat Edilmesi Gerekenler

MTF sonucunu etkileyebilecek bazı durumlar:

- Kenarın yeterince düz olmaması
- Yüksek görüntü gürültüsü
- Hedef çevresinde halo oluşması
- Arka planın düzgün olmaması
- Yanlış piksel boyutu kullanılması
- Doygunluk
- Yetersiz örnekleme

Bu nedenle yalnızca son MTF eğrisine değil, ESF ve LSF gibi ara sonuçlara da bakılmalıdır.

---

## Örnek İşlem Akışı

```text
1. İki half-moon görüntüsü alınır
                ↓
2. MAT dosyaları okunur
                ↓
3. Hedef bulunur
                ↓
4. Düz kenar tespit edilir
                ↓
5. Kenarın yönü belirlenir
                ↓
6. X veya Y yönü atanır
                ↓
7. ESF oluşturulur
                ↓
8. ESF'nin türevi alınır
                ↓
9. LSF elde edilir
                ↓
10. FFT uygulanır
                ↓
11. MTF hesaplanır
                ↓
12. Sonuç lp/mm olarak gösterilir
```

---

## Örnek Komut

```bash
python main.py \
    data/halfmoon_horizontal.mat \
    data/halfmoon_vertical.mat
```

Grafiksiz çalıştırmak için:

```bash
python main.py \
    data/halfmoon_horizontal.mat \
    data/halfmoon_vertical.mat \
    --no-graphs
```

---

## Projenin Amacı

Bu projenin amacı, bir görüntüleme sensörünün iki farklı yöndeki görüntü kalitesini MTF kullanarak ölçmektir.

Program sonunda:

```text
MTF_X
MTF_Y
```

değerleri elde edilir.

Uzaysal frekans birimi:

```text
lp/mm
```

olarak kullanılır.

---

## Kaynak

Glenn D. Boreman  
*Modulation Transfer Function in Optical and Electro-Optical Systems*  
SPIE Press, 2021
