# Implementasi Real-Time Chat Berbasis gRPC

Sistem ini adalah implementasi **Real-Time Chat** berbasis **gRPC** dengan arsitektur Client-Server yang mendukung Multi-Client, dirancang untuk efisiensi koneksi tinggi tanpa kompromi. Dilengkapi pula dengan antarmuka **Web UI (FastAPI Proxy)** yang modern!

## 🚀 Update & Penyempurnaan (Week 9)
Pada tahap pengembangan ini, sistem telah disempurnakan untuk memenuhi kriteria integrasi sistem yang lebih kompleks:

1.  **WebSocket Bridge**: Integrasi penuh antara gRPC Bidirectional Streaming dan WebSocket untuk komunikasi real-time di browser.
2.  **Event-Driven UI**: Antarmuka dinamis dengan komponen yang berubah otomatis (Grafik Server Monitor, Activity Log, dan Status Indicators).
3.  **Server-Initiated Events**: Server secara proaktif mendorong data metrics dan alert sistem (seperti notifikasi maintenance) ke browser tanpa request dari client.
4.  **Command & Control Bridge**: Dukungan perintah teks (prefix `/cmd`) untuk memicu fungsi internal gRPC di backend secara langsung dari UI.

---

## Masalah & Solusi
* **Masalah:** Komunikasi HTTP konvensional lambat dan mengharuskan *refresh* halaman untuk melihat pesan terbaru.
* **Solusi & Tujuan:** Menggunakan gRPC untuk mendapatkan performa realtime tanpa *delay*, membangun backend yang efisien untuk banyak koneksi sekaligus.

## Mengapa gRPC?
1. **PROTOBUF:** Data diserialisasi sehingga ukurannya menjadi jauh lebih kecil & lebih cepat dibandingkan format teks seperti JSON.
2. **BIDIRECTIONAL STREAMING:** Memungkinkan server dan *client* mengirimkan data secara terus-menerus melalui satu koneksi abadi.

---

## Pembagian Microservices

Untuk menjaga agar *backend* tetap rapi dan terstruktur, kami membagi sistem menjadi tiga servis utama:

### 1. User Service (Unary RPC) - Port 50052
* **Fungsi:** Mengelola data pengguna, seperti proses login dan pencatatan status online.

### 2. Room Service (Unary RPC) - Port 50053
* **Fungsi:** Mengatur ruang obrolan dan menangani instruksi **Command & Control**.

### 3. Chat Service (Bidirectional Streaming) - Port 50054
* **Fungsi:** Layanan inti yang bertugas melakukan *broadcast* pesan secara *real-time*.
* *Catatan: Port diubah ke 50054 untuk menghindari konflik port sistem di Windows.*

---

## State Management & Error Handling

Sistem dibangun agar tahan banting dengan fitur *State Management* (Multi-Client) dan Penanganan Error yang modern:

- **In-Memory Storage:** Menyimpan data secara efisien di RAM untuk respon instan.
- **Targeted Broadcasting:** Pesan otomatis difilter berdasarkan Room.
- **Disconnect Detection:** Pembersihan data otomatis saat client terputus untuk menjaga stabilitas.

---

## Cara Menjalankan Project

1.  Install requirements:
    ```bash
    pip install -r requirements.txt
    ```
2.  Jalankan seluruh sistem (4 service) dengan satu perintah:
    ```bash
    python run_all.py
    ```
3.  Buka browser di: **http://localhost:8000**

Jika Anda membutuhkan panduan lebih detail mengenai penggunaan Web UI, silakan baca:
**[PANDUAN_WEB_UI.md](./PANDUAN_WEB_UI.md)**

---

**Disusun Oleh:**
*   Oryza Qiara Ramadhani - 084
*   Maritza Adelia Sucipto - 111
