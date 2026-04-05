# Implementasi Real-Time Chat Berbasis gRPC

Sistem ini adalah implementasi **Real-Time Chat** berbasis **gRPC** dengan arsitektur arsitektur Client-Server yang mendukung Multi-Client, dirancang untuk efisiensi koneksi tinggi tanpa kompromi. Dilengkapi pula dengan antarmuka **Web UI (FastAPI Proxy)** yang modern!

## 📌 Masalah & Solusi
* **Masalah:** Komunikasi HTTP konvensional lambat dan mengharuskan *refresh* halaman untuk melihat pesan terbaru.
* **Solusi & Tujuan:** Menggunakan gRPC untuk mendapatkan performa realtime tanpa *delay*, membangun backend yang efisien untuk banyak koneksi sekaligus.

## 🛠️ Mengapa gRPC?
1. **PROTOBUF:** Data diserialisasi sehingga ukurannya menjadi jauh lebih kecil & lebih cepat dibandingkan format teks seperti JSON.
2. **BIDIRECTIONAL STREAMING:** Memungkinkan server dan *client* mengirimkan data secara terus-menerus melalui satu koneksi abadi.

---

## 🏗️ Pembagian Microservices

Untuk menjaga agar *backend* tetap rapi dan terstruktur, kami membagi sistem menjadi tiga servis utama:

### 1. 👤 User Service (Unary RPC)
* **Fungsi:** Mengelola data pengguna, seperti proses login, registrasi, dan pencatatan status online/offline.
* **Implementasi Kode:** `server/user_service/user_server.py` dan `proto/user.proto`
* **Alur:** Digunakan pada **LANGKAH 1 (LOGIN)**.

### 2. 🏠 Room Service (Unary RPC)
* **Fungsi:** Mengatur ruang obrolan, termasuk pembuatan grup dan pengelolaan keanggotaan pengguna.
* **Implementasi Kode:** `server/room_service/room_server.py` dan `proto/room.proto`
* **Alur:** Digunakan pada **LANGKAH 2 (JOIN ROOM)**. Mendukung *Personal Chat* (1-on-1) maupun *Group Chat*.

### 3. 💬 Chat Service (Bidirectional Streaming)
* **Fungsi:** Layanan inti yang bertugas menerima pesan masuk dan melakukan *broadcast* ke penerima yang tepat secara *real-time*.
* **Implementasi Kode:** `server/chat_service/chat_server.py` dan `proto/chat.proto`
* **Alur:** Digunakan pada **LANGKAH 3 (KIRIM CHAT)**.

---

## ⚙️ State Management & Error Handling

Sistem dibangun agar tahan banting dengan fitur *State Management* (Multi-Client) dan Penanganan Error yang modern:

- **In-Memory Storage & Connection Tracking:** Menyimpan daftar user aktif dan mencatat koneksi tiap user secara dinamis menggunakan *dictionary pool* antrean utas di memori sistem.
- **Targeted Broadcasting:** Pesan otomatis difilter sehingga hanya dikirim kepada user yang berada dalam Room yang sama.
- **Disconnect Detection:** Mendeteksi *client* Web atau CLI yang terputus statusnya (`context.is_active()`).
- **Cleanup Process:** Menghapus *overhead* (seperti `Logout` & *Queue deletion*) secara mulus pada server ketika terputus untuk menjaga **System Stability**.

---

## 💻 Cara Menjalankan Project

Jika Anda ingin menjalankan layanan secara lokal, bacalah panduannya di:
👉 **[PANDUAN_WEB_UI.md](./PANDUAN_WEB_UI.md)**

*Panduan tersebut mencakup instalasi requirements, eksekusi ketiga backend microservice di atas, serta pengoperasian proxy UI Web-nya.*

> **Tim Wardiere, Inc.** 
> * Oryza Qiara Ramadhani - 084
> * Maritza Adelia Sucipto - 111
