# Implementasi Real-Time Chat Berbasis gRPC

Sistem ini adalah implementasi **Real-Time Chat** berbasis **gRPC** dengan arsitektur Client-Server yang mendukung Multi-Client, dirancang untuk efisiensi koneksi tinggi tanpa kompromi. Dilengkapi pula dengan antarmuka **Web UI (FastAPI Proxy)** yang modern!

---

## 🚀 Penyempurnaan Sistem & Integrasi WebSocket (Week 9)
Sistem ini telah dimodifikasi untuk memenuhi 4 kriteria wajib tugas mengenai optimalisasi integrasi antara back-end (gRPC) dengan front-end (WebSocket):

### 1. Implementasi WebSocket (Core Requirement)
*   **Tugas**: Wajib menghubungkan fitur Streaming gRPC yang sudah ada ke WebSocket. Data yang mengalir di gRPC stream harus ditampilkan secara otomatis di Web UI.
*   **Implementasi Teknis**: Menggunakan **FastAPI WebSocket** di file `web_proxy.py`. Proxy ini secara aktif mendengarkan (`listen`) aliran data dari gRPC *Bidirectional Stream* dan secara otomatis mendorong (*push*) data tersebut ke browser melalui WebSocket tanpa perlu adanya *request* tambahan dari client. Hal ini memastikan data tampil secara otomatis dan real-time di antarmuka Web.

### 2. Event-Driven UI
*   **Tugas**: Minimal terdapat 3 komponen di UI yang berubah secara dinamis berdasarkan pesan dari WebSocket.
*   **Implementasi**: 
    *   **Grafik Server Monitor**: Bar CPU & Memory yang bereaksi dinamis terhadap pesan metrics dari WebSocket.
    *   **Activity Log**: Baris log aktivitas yang bertambah secara dinamis saat ada event dari server.
    *   **Status Indicators**: Status "Live" dan jumlah user aktif yang terupdate secara otomatis.

### 3. Server-Initiated Events
*   **Tugas**: Server harus bisa mendorong data secara proaktif ke browser tanpa ada permintaan dari klien (contoh: alert sistem, notifikasi otomatis).
*   **Implementasi**: Backend memiliki background task proaktif yang mengirimkan metrics kesehatan server dan broadcast notifikasi sistem (alert maintenance) langsung ke browser setiap 60 detik.

### 4. Command & Control Bridge
*   **Tugas**: Browser harus mampu mengirim instruksi via WebSocket yang secara otomatis memicu pemanggilan fungsi gRPC di layanan back-end.
*   **Implementasi**: UI mendukung perintah dengan prefix `/cmd`. Saat dikirim, Proxy akan mengeksekusi fungsi gRPC yang sesuai (seperti `GetRoomMembers` atau `PingServices`) dan mengirimkan hasilnya kembali ke browser.

---

## 📖 Deskripsi Proyek

### Masalah & Solusi
* **Masalah:** Komunikasi HTTP konvensional lambat dan mengharuskan *refresh* halaman untuk melihat pesan terbaru.
* **Solusi & Tujuan:** Menggunakan gRPC untuk mendapatkan performa realtime tanpa *delay*, membangun backend yang efisien untuk banyak koneksi sekaligus.

### Mengapa gRPC?
1. **PROTOBUF:** Data diserialisasi sehingga ukurannya menjadi jauh lebih kecil & lebih cepat dibandingkan format teks seperti JSON.
2. **BIDIRECTIONAL STREAMING:** Memungkinkan server dan *client* mengirimkan data secara terus-menerus melalui satu koneksi abadi.

---

## 🏗️ Arsitektur & Microservices
Sistem dibagi menjadi tiga servis utama:
1.  **User Service (Port 50052)**: Mengelola login dan registrasi.
2.  **Room Service (Port 50053)**: Mengatur keanggotaan room dan Command & Control.
3.  **Chat Service (Port 50054)**: Menangani *broadcast* pesan via Bidirectional Streaming.

---

## 🛡️ State Management
Sistem menggunakan penyimpanan **In-Memory (RAM)** untuk menjaga kecepatan integrasi real-time. Seluruh tracking koneksi WebSocket dan gRPC stream dikelola secara dinamis di dalam Proxy untuk memastikan data tersinkronisasi antar semua client.

---

## 💻 Cara Menjalankan Project
1.  Install requirements: `pip install -r requirements.txt`
2.  Jalankan sistem: `python run_all.py`
3.  Akses Web UI: **http://localhost:8000**
4.  Panduan Web UI Lengkap: **[PANDUAN_WEB_UI.md](./PANDUAN_WEB_UI.md)**

---

**Disusun Oleh:**
*   Oryza Qiara Ramadhani - 084
*   Maritza Adelia Sucipto - 111
