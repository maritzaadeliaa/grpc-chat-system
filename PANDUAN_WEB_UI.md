# Panduan Menjalankan Web Chat MQTT v5

Dokumen ini berisi panduan lengkap untuk menjalankan **Web UI Realtime Chat** yang telah dimigrasi dari gRPC streaming ke **MQTT v5**.

---

## 🏗️ Gambaran Arsitektur Baru

Sistem ini menggunakan kombinasi **gRPC** untuk layanan manajemen (User & Room) dan **MQTT v5** untuk pengiriman pesan chat real-time.

1.  **Frontend (Browser)**: Berkomunikasi via WebSocket ke Proxy.
2.  **Web Proxy (FastAPI)**: Menjembatani WebSocket ke MQTT Broker (Mosquitto) dan layanan gRPC.
3.  **Chat Worker (MQTT Daemon)**: Memproses pesan secara background menggunakan *Shared Subscriptions*.
4.  **MQTT Broker (Mosquitto)**: Router pesan utama yang mendukung fitur MQTT v5.

---

## 🛠️ Prasyarat

- **Python 3.8+**
- **Docker Desktop** (Wajib untuk menjalankan MQTT Broker)
- **pip install -r requirements.txt**

---

## 🚀 Cara Menjalankan (3 Langkah Mudah)

### 1. Jalankan MQTT Broker
Buka terminal dan jalankan Mosquitto menggunakan Docker Compose:
```bash
docker-compose up -d
```

### 2. Jalankan Seluruh Sistem (Layanan & Worker)
Jalankan launcher otomatis yang akan menyalakan User Service, Room Service, Chat Worker, dan Web Proxy:
```bash
python run_all.py
```

### 3. Akses Web UI
Buka browser dan akses: **http://localhost:8000**

---

## 🕹️ Fitur & Cara Demo

### A. Fitur Chat Dasar
- Login dengan username apa saja.
- Masukkan nama room (misal: `tech`).
- Chat berjalan secara real-time via MQTT.

### B. MQTT v5 - Fitur Lanjutan (Orang 2 & 3)

| Fitur | Cara Menggunakan | Kegunaan |
| :--- | :--- | :--- |
| **QoS (0, 1, 2)** | Pilih dari dropdown sebelum kirim pesan. | Mengatur tingkat jaminan pengiriman pesan. |
| **Pin Message** | Centang **"Pin Message"** sebelum kirim. | Pesan akan "menempel" (Retain) di room untuk user baru. |
| **Expiry** | Pilih **10 Detik** atau **1 Menit**. | Pesan otomatis terhapus dari broker jika lewat waktu. |
| **Chat Bot** | Ketik `/bot ping` atau `/bot time`. | Bot membalas secara private (Request-Response). |
| **LWT Alert** | Matikan paksa server `web_proxy.py`. | Muncul alert merah otomatis di semua browser user. |

---

## 💡 Troubleshooting

### Pesan tidak terkirim?
Pastikan Docker Mosquitto sudah `Up` (cek dengan `docker ps`). Jika port 1883 bentrok, pastikan tidak ada broker MQTT lain yang berjalan di komputer Anda.

### Error `paho-mqtt`?
Pastikan Anda menggunakan versi terbaru:
```bash
pip install --upgrade paho-mqtt
```

### Cara Mematikan Semua Layanan (Windows)
```powershell
taskkill /f /im python.exe
docker-compose stop
```

---
**Tim Pengembang - Kelompok 3 INSIS**
