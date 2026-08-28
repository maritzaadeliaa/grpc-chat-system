# Implementasi Real-Time Chat Berbasis gRPC & MQTT v5

Sistem ini adalah implementasi **Real-Time Chat** modern yang menggabungkan **gRPC** (untuk manajemen User & Room) dan **MQTT v5** (sebagai engine pesan Chat utama) dengan arsitektur **Microservices**. Dilengkapi dengan antarmuka **Web UI (FastAPI Proxy)** yang responsif dan fitur-fitur canggih protokol MQTT v5.

---

## Demo

[![TypeSense Demo](https://img.youtube.com/vi/WRqGBEfifrk/maxresdefault.jpg)](https://youtu.be/WRqGBEfifrk)

## 🏗️ Arsitektur Sistem Baru (MQTT Integration)

Sistem telah bermigrasi dari gRPC Bidirectional Streaming menjadi model **Publish/Subscribe** menggunakan broker **Eclipse Mosquitto**.

```
┌─────────────────────────────────────────────────┐
│         Web Browser / Client (WebSocket)        │
└────────────────┬────────────────────────────────┘
                 │
      ┌──────────▼────────────┐
      │  Web Proxy (FastAPI)   │  <- port 8000
      │  MQTT Bridge (Client)  │
      └──┬──────┬─────────┬────┘
         │      │         │
    gRPC │ gRPC │         │ MQTT (Pub/Sub)
         │      │         │
┌────────▼┐ ┌───▼───┐ ┌───▼────────────┐
│  User   │ │  Room  │ │ MQTT Broker    │
│ Service │ │ Service│ │ (Mosquitto)    │
│ :50052  │ │ :50053  │ │ :1883 / :9001  │
└─────────┘ └────────┘ └───┬────────────┘
                           │
                 ┌─────────▼───────────┐
                 │  Chat Worker        │
                 │  (MQTT Daemon)      │
                 └─────────────────────┘
```

---

## 🛠️ Pembagian Tugas & Fitur MQTT v5

Proyek ini mendemonstrasikan fitur-fitur utama **MQTT v5** yang dibagi menjadi 3 peran:

### 🧑‍💻 Orang 1: Fondasi MQTT & Proxy Bridge
*   **MQTT Broker Setup**: Menggunakan Eclipse Mosquitto via Docker.
*   **Web Proxy MQTT Bridge**: Menghubungkan WebSocket browser ke MQTT Broker secara asinkron.
*   **Topic Alias**: Menghemat bandwidth dengan mengganti string topik yang panjang dengan ID numerik.
*   **User Properties**: Memindahkan metadata (`username`, `msg_type`) dari payload JSON ke header MQTT v5.

### 🧑‍💻 Orang 2: Worker, Routing & Retained Messages
*   **Chat Worker (Daemon)**: Mengubah Chat Service menjadi background worker murni berbasis MQTT.
*   **Wildcard & Shared Subscription**: Menggunakan `$share/chat_workers/chat/room/#` agar banyak worker bisa memproses pesan secara load-balanced.
*   **QoS (Quality of Service)**: Implementasi pilihan QoS 0, 1, dan 2 di UI untuk jaminan pengiriman pesan.
*   **Retained Messages (Pin Message)**: Fitur untuk "menyematkan" pesan di room. User yang baru bergabung akan langsung menerima pesan terakhir yang di-retain.

### 🧑‍💻 Orang 3: Reliability, Expiry & Bot Interaction
*   **Last Will Testament (LWT)**: Pesan otomatis *"🚨 Proxy Server Terputus!"* jika server proxy mati mendadak.
*   **Message Expiry**: Fitur "Ephemeral Message" di mana pesan akan otomatis dihapus oleh broker jika tidak tersampaikan dalam waktu X detik.
*   **Request-Response Pattern**: Fitur **Chat Bot** interaktif. Proxy mengirim request ke `chat/request/bot` dengan `ResponseTopic` unik, dan Worker membalas langsung ke user tersebut.
*   **Flow Control**: Mengatur `ReceiveMaximum` pada Worker untuk menangani beban trafik tinggi (*backpressure*).

---

## 🎮 Panduan Demo Fitur

Berikut adalah cara menguji fitur-fitur yang telah diimplementasikan:

| Fitur | Perintah / Cara Uji | Hasil yang Diharapkan |
| :--- | :--- | :--- |
| **Chat Dasar** | Login & Kirim pesan antar tab browser | Pesan terkirim secara real-time via MQTT. |
| **Pin Message** | Centang **"Pin Message"** lalu kirim | Muncul badge `📌 PINNED`. User baru yang masuk room langsung melihat pesan ini. |
| **Private Bot** | Ketik `/bot ping` atau `/bot time` | Bot membalas secara privat hanya ke Anda (Request-Response). |
| **QoS 2** | Pilih **QoS 2** di dropdown lalu kirim | Jaminan pengiriman "Exactly Once" (Tepat satu kali). |
| **Expiry** | Pilih **Expiry 10 detik** lalu kirim | Jika penerima offline > 10 detik, pesan otomatis hangus/tidak diterima. |
| **LWT** | Matikan paksa `run_all.py` | Muncul notifikasi merah *"Proxy Server Terputus"* di browser. |

---

## 💻 Komando Utama (Cheat Sheet)

### 1. Menjalankan Infrastruktur (Docker)
```bash
docker-compose up -d
```

### 2. Menjalankan Seluruh Sistem Chat
```bash
python run_all.py
```

### 3. Menghentikan Sistem (Windows)
```powershell
taskkill /f /im python.exe
docker-compose down
```

---

## 📂 Struktur Proyek Terkini
```
grpc-chat-system/
├── mosquitto/          # Konfigurasi & Data MQTT Broker
├── server/
│   ├── chat_service/   # MQTT Worker (Daemon)
│   ├── user_service/   # gRPC User Service
│   └── room_service/   # gRPC Room Service
├── web/                # Frontend UI (HTML/JS/CSS)
├── web_proxy.py        # Bridge WebSocket <-> MQTT v5
├── run_all.py          # Launcher Sistem Terpadu
└── requirements.txt    # Library: fastapi, paho-mqtt, grpcio, dll.
```

---
**Kelompok INSIS - Migrasi gRPC ke MQTT v5**
