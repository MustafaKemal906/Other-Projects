# Çoklu Drone Telemetri Sistemi

Bu proje, birden fazla dronedan **MAVSDK kullanarak telemetri verisi toplamak** ve bu verileri HTTP üzerinden bir sunucuya göndermek için geliştirilmiştir.

Mevcut yapıda iki drone ayrı UDP portlarından bağlanır ve telemetri bilgileri yaklaşık **1 saniyede bir** sunucuya gönderilir.

---

## Genel Akış

```text
Drone 1 ──┐
          ├── MAVSDK
Drone 2 ──┘
      ↓
Telemetri Verileri
      ↓
HTTP POST
      ↓
Sunucu
```

---

## Drone Bağlantıları

Program iki drone için ayrı bağlantı oluşturur:

```text
Drone 1 → udp://:14541
Drone 2 → udp://:14542
```

Her drone bağımsız olarak işlenir.

---

## Toplanan Telemetri Verileri

Program aşağıdaki bilgileri toplar:

- Batarya yüzdesi
- GPS bilgisi
- Uydu sayısı
- GPS fix tipi
- Drone havada mı bilgisi
- Enlem
- Boylam
- Mutlak irtifa
- Bağıl irtifa

Örnek veri:

```json
{
  "drone_name": "Drone 1",
  "telemetry": {
    "battery": 0.82,
    "gps_info": {
      "num_satellites": 14,
      "fix_type": 3
    },
    "in_air": true,
    "position": {
      "latitude_deg": 39.0,
      "longitude_deg": 32.0,
      "absolute_altitude_m": 1020.4,
      "relative_altitude_m": 43.8
    }
  }
}
```

---

## Kullanılan Teknolojiler

- Python 3
- MAVSDK
- asyncio
- aiohttp
- JSON
- HTTP REST API

---

## Kurulum

Gerekli Python paketleri:

```bash
pip install mavsdk aiohttp
```

---

## Çalışma Mantığı

Her drone için bir MAVSDK bağlantısı oluşturulur:

```python
drone1 = System()
await drone1.connect(system_address="udp://:14541")

drone2 = System()
await drone2.connect(system_address="udp://:14542")
```

Daha sonra her drone için telemetri fonksiyonları ayrı ayrı çalıştırılır.

---

## Batarya Bilgisi

Batarya verisi:

```python
drone.telemetry.battery()
```

üzerinden alınır.

Kaydedilen temel değer:

```text
battery.remaining_percent
```

---

## GPS Bilgisi

GPS bilgisi:

```python
drone.telemetry.gps_info()
```

üzerinden alınır.

Kaydedilen bilgiler:

```text
num_satellites
fix_type
```

---

## Havada Olma Bilgisi

Drone'un uçuş durumu:

```python
drone.telemetry.in_air()
```

üzerinden kontrol edilir.

Sonuç:

```text
True  → Drone havada
False → Drone yerde
```

---

## Konum Bilgisi

Konum verisi:

```python
drone.telemetry.position()
```

üzerinden alınır.

Kaydedilen bilgiler:

```text
latitude_deg
longitude_deg
absolute_altitude_m
relative_altitude_m
```

---

## Sunucuya Veri Gönderme

Toplanan bilgiler aşağıdaki yapıda hazırlanır:

```python
payload = {
    "drone_name": drone_name,
    "telemetry": telemetry_data
}
```

Daha sonra HTTP POST isteği ile sunucuya gönderilir:

```python
async with session.post(
    server_address,
    json=payload
) as response:
    ...
```

Gönderim yaklaşık olarak:

```text
1 Hz
```

hızında yapılır.

---

## Sunucu Adresi

Kodda kullanılan varsayılan endpoint:

```text
http://0.0.0.0:5000/api/telemetri_gonder
```

Eğer sunucu aynı bilgisayarda çalışıyorsa genellikle şu adres kullanılabilir:

```text
http://127.0.0.1:5000/api/telemetri_gonder
```

Sunucu başka bir bilgisayarda ise o bilgisayarın IP adresi kullanılmalıdır.

---

## Örnek Kayıt Yapısı

Sunucu tarafında veriler drone adı ve zaman bilgisine göre tutulabilir:

```json
{
  "Drone 1": {
    "2025-03-12T16:48:39.547125": {},
    "2025-03-12T16:48:40.549860": {},
    "2025-03-12T16:48:41.553649": {}
  }
}
```

Telemetri bilgileri de timestamp altında saklanabilir.

---

## Çalıştırma

MAVSDK / PX4 / SITL veya gerçek drone bağlantıları hazırlandıktan sonra:

```bash
python3 telemetry_sender.py
```

komutu ile program çalıştırılabilir.

Program sürekli çalışmaya devam eder.

Durdurmak için:

```text
Ctrl + C
```

---

## Çoklu Drone Yapısı

```text
Drone 1
   ↓
MAVSDK
   ↓
Telemetri
   ↓
HTTP POST
   ↓
Sunucu


Drone 2
   ↓
MAVSDK
   ↓
Telemetri
   ↓
HTTP POST
   ↓
Sunucu
```

Her drone farklı bir UDP portu kullanır.

Bu yapı yeni drone bağlantıları eklenerek genişletilebilir.

---

## Sunucu Cevapları

Sunucu başarılı cevap verirse:

```text
HTTP 200
```

döner.

Başarılı durumda sunucu cevabı terminale yazdırılır.

Hata durumunda:

```text
Status code
Error content
```

bilgileri gösterilir.

Bağlantı hataları da `aiohttp` tarafından yakalanır.

---

## Önemli Not

Kodda aşağıdaki fonksiyon `async` olarak tanımlanmıştır:

```python
async def print_and_store_data(data_type, data):
    telemetry_data[data_type] = data
```

Ancak çağrıldığı yerde `await` kullanılmamaktadır.

Daha doğru kullanım:

```python
await print_and_store_data(
    "battery",
    battery.remaining_percent
)
```

veya bu fonksiyon normal bir fonksiyon yapılabilir:

```python
def print_and_store_data(data_type, data):
    telemetry_data[data_type] = data
    print(f"{drone_name} {data_type}: {data}")
```

Bu işlem içinde beklenen bir asenkron işlem olmadığı için normal fonksiyon kullanmak daha basit olabilir.

---

## Projenin Amacı

Bu projenin amacı birden fazla dronedan gelen telemetri bilgilerini tek bir sunucuda toplamak ve izlenebilir hale getirmektir.

Temel sistem:

```text
Drone
  ↓
MAVSDK
  ↓
Telemetri Toplama
  ↓
HTTP Gönderimi
  ↓
Merkezi Sunucu
```

Bu yapı;

- çoklu drone izleme,
- yer kontrol sistemi,
- telemetri kaydı,
- drone takip paneli,
- sürü drone çalışmaları

için temel oluşturabilir.
