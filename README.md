# Implementasi Real-Time Chat Berbasis gRPC

Sistem ini adalah implementasi **Real-Time Chat** berbasis **gRPC** dengan arsitektur Client-Server yang mendukung Multi-Client, dirancang untuk efisiensi koneksi tinggi tanpa kompromi. Dilengkapi pula dengan antarmuka **Web UI (FastAPI Proxy)** yang modern!

## Masalah & Solusi
* **Masalah:** Komunikasi HTTP konvensional lambat dan mengharuskan *refresh* halaman untuk melihat pesan terbaru.
* **Solusi & Tujuan:** Menggunakan gRPC untuk mendapatkan performa realtime tanpa *delay*, membangun backend yang efisien untuk banyak koneksi sekaligus.

## Mengapa gRPC?
1. **PROTOBUF:** Data diserialisasi sehingga ukurannya menjadi jauh lebih kecil & lebih cepat dibandingkan format teks seperti JSON.
2. **BIDIRECTIONAL STREAMING:** Memungkinkan server dan *client* mengirimkan data secara terus-menerus melalui satu koneksi abadi.

---

## Pembagian Microservices

Untuk menjaga agar *backend* tetap rapi dan terstruktur, kami membagi sistem menjadi tiga servis utama:

### 1. User Service (Unary RPC)
* **Fungsi:** Mengelola data pengguna, seperti proses login, registrasi, dan pencatatan status online/offline.
* **Implementasi Kode:** `server/user_service/user_server.py` dan `proto/user.proto`
* **Alur:** Digunakan pada **LANGKAH 1 (LOGIN)**.

### 2. Room Service (Unary RPC)
* **Fungsi:** Mengatur ruang obrolan, termasuk pembuatan grup dan pengelolaan keanggotaan pengguna.
* **Implementasi Kode:** `server/room_service/room_server.py` dan `proto/room.proto`
* **Alur:** Digunakan pada **LANGKAH 2 (JOIN ROOM)**. Mendukung *Personal Chat* (1-on-1) maupun *Group Chat*.

### 3. Chat Service (Bidirectional Streaming)
* **Fungsi:** Layanan inti yang bertugas menerima pesan masuk dan melakukan *broadcast* ke penerima yang tepat secara *real-time*.
* **Implementasi Kode:** `server/chat_service/chat_server.py` dan `proto/chat.proto`
* **Alur:** Digunakan pada **LANGKAH 3 (KIRIM CHAT)**.

---

## State Management & Error Handling

Sistem dibangun agar tahan banting dengan fitur *State Management* (Multi-Client) dan Penanganan Error yang modern:

- **In-Memory Storage & Connection Tracking:** Menyimpan daftar user aktif dan mencatat koneksi tiap user secara dinamis menggunakan *dictionary pool* antrean utas di memori sistem.
- **Targeted Broadcasting:** Pesan otomatis difilter sehingga hanya dikirim kepada user yang berada dalam Room yang sama.
- **Disconnect Detection:** Mendeteksi *client* Web atau CLI yang terputus statusnya (`context.is_active()`).
- **Cleanup Process:** Menghapus *overhead* (seperti `Logout` & *Queue deletion*) secara mulus pada server ketika terputus untuk menjaga **System Stability**.

---

## Cara Menjalankan Project

Jika Anda ingin menjalankan layanan secara lokal, bacalah panduannya di:
**[PANDUAN_WEB_UI.md](./PANDUAN_WEB_UI.md)**

---

## Masalah & Solusi

**Masalah:** Komunikasi HTTP konvensional lambat dan mengharuskan refresh halaman untuk melihat pesan terbaru.

**Solusi & Tujuan:** Menggunakan gRPC untuk mendapatkan performa realtime tanpa delay, membangun backend yang efisien untuk banyak koneksi sekaligus.

---

## Arsitektur Sistem

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
│:50052  │ │:50053 │ │  :50051   │
└────────┘ └───────┘ └───────────┘
```

---

## Pembagian Microservices

Untuk menjaga agar backend tetap rapi dan terstruktur, sistem dibagi menjadi tiga servis utama:

### 1. User Service (Unary RPC)
- **Fungsi:** Mengelola data pengguna, seperti proses login, registrasi, dan pencatatan status online/offline.
- **Implementasi Kode:** `server/user_service/user_server.py` dan `proto/user.proto`
- **Alur:** Digunakan pada **LANGKAH 1 (LOGIN)**.

### 2. Room Service (Unary RPC)
- **Fungsi:** Mengatur ruang obrolan, termasuk pembuatan grup dan pengelolaan keanggotaan pengguna.
- **Implementasi Kode:** `server/room_service/room_server.py` dan `proto/room.proto`
- **Alur:** Digunakan pada **LANGKAH 2 (JOIN ROOM)**. Mendukung Personal Chat (1-on-1) maupun Group Chat.

### 3. Chat Service (Bidirectional Streaming)
- **Fungsi:** Layanan inti yang bertugas menerima pesan masuk dan melakukan broadcast ke penerima yang tepat secara real-time.
- **Implementasi Kode:** `server/chat_service/chat_server.py` dan `proto/chat.proto`
- **Alur:** Digunakan pada **LANGKAH 3 (KIRIM CHAT)**.

---

## State Management & Error Handling

Sistem dibangun agar tahan banting dengan fitur **State Management (Multi-Client)** dan **Penanganan Error** yang modern:

- **In-Memory Storage & Connection Tracking:** Menyimpan daftar user aktif dan mencatat koneksi tiap user secara dinamis menggunakan dictionary pool antrean utas di memori sistem.
- **Targeted Broadcasting:** Pesan otomatis difilter sehingga hanya dikirim kepada user yang berada dalam Room yang sama.
- **Disconnect Detection:** Mendeteksi client Web atau CLI yang terputus statusnya (`context.is_active()`).
- **Cleanup Process:** Menghapus overhead (seperti Logout & Queue deletion) secara mulus pada server ketika terputus untuk menjaga System Stability.

> **Catatan:** Sistem ini menggunakan penyimpanan **In-Memory (RAM)** — data pesan, user, dan room tidak disimpan ke database. Semua data akan hilang ketika server di-restart. Ini adalah desain yang disengaja untuk menjaga sistem tetap ringan dan fokus pada demonstrasi gRPC Streaming.

---

## Cara Menjalankan Project

Jika Anda ingin menjalankan layanan secara lokal, bacalah panduannya di: **[PANDUAN_WEB_UI.md](PANDUAN_WEB_UI.md)**

Panduan tersebut mencakup instalasi requirements, eksekusi ketiga backend microservice di atas, serta pengoperasian proxy UI Web-nya.

---

## Fitur

- ✅ **Real-time chat** via gRPC Bidirectional Streaming
- ✅ **Multi-room** — bisa join beberapa room sekaligus
- ✅ **Web UI** — antarmuka browser modern (dark mode)
- ✅ **CLI Client** — send & receive secara bersamaan (threading)
- ✅ **Auto-cleanup** — user/room otomatis dihapus saat disconnect
- ✅ **Login/Logout** — tracking user aktif

---

## Struktur Proyek

```
grpc-chat-system/
├── proto/
│   ├── user.proto          # Definisi UserService
│   ├── room.proto          # Definisi RoomService
│   └── chat.proto          # Definisi ChatService (Bidirectional Stream)
├── server/
│   ├── user_service/
│   │   └── user_server.py  # Login/Logout (Port 50052)
│   ├── room_service/
│   │   └── room_server.py  # Join/Leave Room (Port 50053)
│   └── chat_service/
│       └── chat_server.py  # Bidirectional Chat Stream (Port 50051)
├── client/
│   └── client.py           # CLI Client dengan threading
├── web/
│   └── index.html          # Web UI
├── web_proxy.py            # FastAPI proxy (HTTP/WS <-> gRPC)
├── run_all.py              # Launcher semua service
├── requirements.txt
└── README.md
```

---

**Oryza Qiara Ramadhani - 084**  
**Maritza Adelia Sucipto - 111**

