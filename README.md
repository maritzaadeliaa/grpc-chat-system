# Implementasi Real-Time Chat Berbasis gRPC

Sistem ini adalah implementasi **Real-Time Chat** berbasis **gRPC** dengan arsitektur Client-Server yang mendukung Multi-Client, dirancang untuk efisiensi koneksi tinggi tanpa kompromi. Dilengkapi pula dengan antarmuka **Web UI (FastAPI Proxy)** yang modern!

---

## 🚀 Penyempurnaan Sistem (Week 9)
Proyek ini telah diperbarui untuk memenuhi seluruh **Fitur Wajib** tugas Week 9 mengenai integrasi sistem:

### 1. Implementasi WebSocket
*   **Tugas**: Menghubungkan fitur Streaming gRPC ke WebSocket. Data gRPC stream harus tampil otomatis di Web UI.
*   **Implementasi**: Terletak di `web_proxy.py` pada fungsi `websocket_chat`. Proxy menjembatani `ChatStream` gRPC langsung ke koneksi WebSocket browser secara real-time.

### 2. Event-Driven UI
*   **Tugas**: Minimal 3 komponen UI berubah dinamis berdasarkan pesan WebSocket.
*   **Implementasi**: 
    *   **Grafik Server Monitor**: Bar CPU & Memory yang update tiap 5 detik.
    *   **Activity Log**: Konsol log sistem di bagian atas chat yang mencatat event server.
    *   **Status Indicators**: Indikator "Live" dan jumlah koneksi aktif yang berubah otomatis.

### 3. Server-Initiated Events
*   **Tugas**: Server mendorong data secara proaktif tanpa permintaan klien.
*   **Implementasi**: Background task `server_metrics_broadcaster` di `web_proxy.py` yang mengirimkan data kesehatan server dan pesan broadcast otomatis secara proaktif.

### 4. Command & Control Bridge
*   **Tugas**: Browser mengirim instruksi via WebSocket yang memicu fungsi gRPC di back-end.
*   **Implementasi**: User dapat menggunakan prefix `/cmd` (contoh: `/cmd ping_services`) yang akan diproses oleh Proxy dan diteruskan ke backend gRPC.

---

## 📖 Deskripsi Proyek Original

### Masalah & Solusi
* **Masalah:** Komunikasi HTTP konvensional lambat dan mengharuskan *refresh* halaman untuk melihat pesan terbaru.
* **Solusi & Tujuan:** Menggunakan gRPC untuk mendapatkan performa realtime tanpa *delay*, membangun backend yang efisien untuk banyak koneksi sekaligus.

### Mengapa gRPC?
1. **PROTOBUF:** Data diserialisasi sehingga ukurannya menjadi jauh lebih kecil & lebih cepat dibandingkan format teks seperti JSON.
2. **BIDIRECTIONAL STREAMING:** Memungkinkan server dan *client* mengirimkan data secara terus-menerus melalui satu koneksi abadi.

---

## 🏗️ Arsitektur & Microservices

Untuk menjaga agar *backend* tetap rapi dan terstruktur, kami membagi sistem menjadi tiga servis utama:

1.  **User Service (Unary RPC) - Port 50052**
    *   Mengelola data pengguna, seperti proses login, registrasi, dan pencatatan status online.
2.  **Room Service (Unary RPC) - Port 50053**
    *   Mengatur ruang obrolan, termasuk pembuatan grup dan pengelolaan keanggotaan pengguna.
3.  **Chat Service (Bidirectional Streaming) - Port 50054**
    *   Layanan inti yang bertugas menerima pesan masuk dan melakukan *broadcast* pesan secara *real-time*.
    *   *Catatan: Port dipindah ke 50054 untuk kompatibilitas Windows (menghindari konflik port 50051).*

---

## 🛡️ State Management & Error Handling
Sistem dibangun agar tahan banting dengan fitur *State Management* dan Penanganan Error modern:
- **In-Memory Storage:** Menyimpan daftar user aktif dan koneksi secara dinamis di RAM.
- **Cleanup Process:** Menghapus data user otomatis saat terputus untuk menjaga stabilitas sistem.
- **Port Conflict Protection:** Konfigurasi binding `0.0.0.0` untuk memastikan aksesibilitas di sistem Windows.

---

## 📹 Panduan Video Presentasi
Video presentasi (Max 15 Menit) mencakup:
1.  **Deskripsi & Arsitektur**: Penjelasan integrasi Browser -> WebSocket -> Proxy -> gRPC.
2.  **Demo Fitur**: Simulasi chat, update grafik monitor, dan penggunaan `/cmd`.
3.  **Code Walkthrough**: Penjelasan alur gRPC stream dan WebSocket bridge di `web_proxy.py`.

---

## 💻 Cara Menjalankan Project
1.  Install requirements: `pip install -r requirements.txt`
2.  Jalankan sistem: `python run_all.py`
3.  Akses Web UI: **http://localhost:8000**
4.  Panduan Web UI: **[PANDUAN_WEB_UI.md](./PANDUAN_WEB_UI.md)**

---

## 📂 Struktur Folder
```
grpc-chat-system/
├── proto/              # Definisi .proto untuk gRPC
├── server/             # Kode sumber microservices backend
│   ├── user_service/   # User server logic
│   ├── room_service/   # Room & Command logic
│   └── chat_service/   # Streaming chat logic
├── web/                # Frontend (HTML/CSS/JS)
├── web_proxy.py        # Bridge WebSocket <-> gRPC
├── run_all.py          # Unified launcher script
└── requirements.txt    # Daftar library Python
```

---

**Oryza Qiara Ramadhani - 084**  
**Maritza Adelia Sucipto - 111**
