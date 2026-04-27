# Implementasi Real-Time Chat Berbasis gRPC

Sistem ini adalah implementasi **Real-Time Chat** berbasis **gRPC** dengan arsitektur **Client-Server** yang mendukung **Multi-Client**, dirancang untuk efisiensi koneksi tinggi tanpa kompromi. Dilengkapi pula dengan antarmuka **Web UI (FastAPI Proxy)** yang modern!

---

## 🚀 Penyempurnaan Sistem (Week 9)
Proyek ini telah diperbarui untuk memenuhi seluruh **Fitur Wajib** tugas Week 9 mengenai integrasi sistem:

### 1. Implementasi WebSocket (Core Requirement)
*   **Tugas**: Wajib menghubungkan fitur Streaming gRPC yang sudah ada ke WebSocket. Data yang mengalir di gRPC stream harus ditampilkan secara otomatis di Web UI.
*   **Implementasi**: Terletak di `web_proxy.py` pada fungsi `websocket_chat`. Proxy menjembatani `ChatStream` gRPC langsung ke koneksi WebSocket browser secara real-time.

### 2. Event-Driven UI
*   **Tugas**: Minimal terdapat 3 komponen di UI yang berubah secara dinamis berdasarkan pesan dari WebSocket.
*   **Implementasi**: 
    *   **Grafik Server Monitor**: Bar CPU & Memory yang update tiap 5 detik.
    *   **Activity Log**: Konsol log sistem di bagian atas chat yang mencatat event server.
    *   **Status Indicators**: Indikator "Live" dan jumlah koneksi aktif yang berubah otomatis.

### 3. Server-Initiated Events
*   **Tugas**: Server harus bisa mendorong data secara proaktif ke browser tanpa ada permintaan dari klien (contoh: alert sistem, notifikasi otomatis).
*   **Implementasi**: Background task `server_metrics_broadcaster` di `web_proxy.py` yang mengirimkan data kesehatan server dan pesan broadcast otomatis secara proaktif.

### 4. Command & Control Bridge
*   **Tugas**: Browser harus mampu mengirim instruksi via WebSocket yang secara otomatis memicu pemanggilan fungsi gRPC di layanan back-end.
*   **Implementasi**: User dapat menggunakan prefix `/cmd` (contoh: `/cmd ping_services`) yang akan diproses oleh Proxy dan diteruskan ke backend gRPC.

---

## 📖 Deskripsi Proyek Original

### Masalah & Solusi
* **Masalah:** Komunikasi HTTP konvensional lambat dan mengharuskan *refresh* halaman untuk melihat pesan terbaru.
* **Solusi & Tujuan:** Menggunakan gRPC untuk mendapatkan performa realtime tanpa *delay*, membangun backend yang efisien untuk banyak koneksi sekaligus.

### Mengapa gRPC?
- **PROTOBUF:** Data diserialisasi sehingga ukurannya menjadi jauh lebih kecil & lebih cepat dibandingkan format teks seperti JSON.
- **BIDIRECTIONAL STREAMING:** Memungkinkan server dan client mengirimkan data secara terus-menerus melalui satu koneksi abadi.

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────┐
│         Web Browser / CLI Client                │
│         (WebSocket / gRPC)                      │
└────────────────┬────────────────────────────────┘
                 │
     ┌───────────▼────────────┐
     │  Web Proxy (FastAPI)   │  <- port 8000
     │  HTTP + WebSocket      │
     └──┬──────┬──────┬───────┘
        │      │      │
   gRPC │ gRPC │ gRPC │
        │      │      │
┌───────▼┐ ┌───▼───┐ ┌▼──────────┐
│  User  │ │  Room │ │   Chat    │
│Service │ │Service│ │  Service  │
│:50052  │ │:50053 │ │  :50054   │
└────────┘ └───────┘ └───────────┘
```

---

## 🛠️ Pembagian Microservices

Untuk menjaga agar backend tetap rapi dan terstruktur, sistem dibagi menjadi tiga servis utama:

### 1. User Service (Unary RPC) - Port 50052
- **Fungsi:** Mengelola data pengguna, seperti proses login, registrasi, dan pencatatan status online/offline.
- **Implementasi Kode:** `server/user_service/user_server.py` dan `proto/user.proto`

### 2. Room Service (Unary RPC) - Port 50053
- **Fungsi:** Mengatur ruang obrolan, termasuk pembuatan grup dan pengelolaan keanggotaan pengguna.
- **Implementasi Kode:** `server/room_service/room_server.py` dan `proto/room.proto`

### 3. Chat Service (Bidirectional Streaming) - Port 50054
- **Fungsi:** Layanan inti yang bertugas menerima pesan masuk dan melakukan broadcast ke penerima yang tepat secara real-time.
- **Implementasi Kode:** `server/chat_service/chat_server.py` dan `proto/chat.proto`
- *Catatan: Port dipindahkan ke 50054 untuk menghindari konflik sistem.*

---

## 🛡️ State Management & Error Handling

Sistem dibangun agar tahan banting dengan fitur **State Management (Multi-Client)** dan **Penanganan Error** yang modern:

- **In-Memory Storage & Connection Tracking:** Menyimpan daftar user aktif dan mencatat koneksi tiap user secara dinamis menggunakan dictionary pool antrean utas di memori sistem.
- **Targeted Broadcasting:** Pesan otomatis difilter sehingga hanya dikirim kepada user yang berada dalam Room yang sama.
- **Cleanup Process:** Menghapus overhead secara mulus pada server ketika terputus untuk menjaga System Stability.

> **Catatan:** Sistem ini menggunakan penyimpanan **In-Memory (RAM)** — data pesan, user, dan room tidak disimpan ke database. Ini adalah desain yang disengaja untuk menjaga sistem tetap ringan dan fokus pada demonstrasi gRPC Streaming.

---

## 💻 Cara Menjalankan Project

1.  **Install requirements**: `pip install -r requirements.txt`
2.  **Jalankan Sistem**: `python run_all.py` (Menyalakan 4 service sekaligus).
3.  **Akses Web UI**: **http://localhost:8000**
4.  **Panduan Detail**: **[PANDUAN_WEB_UI.md](PANDUAN_WEB_UI.md)**

---

## 📂 Struktur Proyek
```
grpc-chat-system/
├── proto/              # Definisi Protokol gRPC
├── server/             # Backend Services
│   ├── user_service/   # Port 50052
│   ├── room_service/   # Port 50053
│   └── chat_service/   # Port 50054
├── client/             # CLI Client
├── web/                # Frontend Web
├── web_proxy.py        # Bridge WebSocket <-> gRPC
├── run_all.py          # Launcher Otomatis
└── requirements.txt    # Library Dependencies
```

---

**Oryza Qiara Ramadhani - 084**  
**Maritza Adelia Sucipto - 111**
