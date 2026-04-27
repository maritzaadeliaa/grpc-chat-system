# Implementasi Real-Time Chat Berbasis gRPC

Sistem ini adalah implementasi **Real-Time Chat** berbasis **gRPC** dengan arsitektur Client-Server yang mendukung Multi-Client, dirancang untuk efisiensi koneksi tinggi tanpa kompromi. Dilengkapi pula dengan antarmuka **Web UI (FastAPI Proxy)** yang modern!

## 🚀 Penyempurnaan Sistem (Week 9)
Proyek ini telah diperbarui untuk memenuhi seluruh **Fitur Wajib** tugas Week 9:

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
*   **Tugas**: Server mendorong data secara proaktif tanpa permintaan klien (alert sistem, notifikasi otomatis).
*   **Implementasi**: Background task `server_metrics_broadcaster` di `web_proxy.py` yang mengirimkan data kesehatan server dan pesan broadcast otomatis (seperti jadwal maintenance) setiap 60 detik ke semua user.

### 4. Command & Control Bridge
*   **Tugas**: Browser mengirim instruksi via WebSocket yang memicu fungsi gRPC di back-end.
*   **Implementasi**: User dapat menggunakan prefix `/cmd` di kolom chat. Instruksi ini ditangkap oleh Proxy dan diteruskan sebagai pemanggilan RPC ke `RoomService` atau `UserService`.

---

## 📹 Panduan Video Presentasi
Sesuai ketentuan tugas, video presentasi (Max 15 Menit, On-Camera) mencakup:
1.  **Deskripsi & Arsitektur**: Penjelasan alur dari Browser -> WebSocket -> Proxy -> gRPC Services.
2.  **Demo Fitur**: Menunjukkan chat real-time, grafik monitor yang bergerak, dan penggunaan perintah `/cmd`.
3.  **Code Walkthrough**: Penjelasan singkat alur program di `web_proxy.py` (WebSocket bridge) dan `chat_server.py` (gRPC stream).

---

## 🛠️ Pembagian Microservices
*   **User Service (Port 50052)**: Autentikasi dan login.
*   **Room Service (Port 50053)**: Manajemen room dan Command & Control.
*   **Chat Service (Port 50054)**: Bidirectional Chat Streaming.

---

## 💻 Cara Menjalankan Project
1.  Install requirements: `pip install -r requirements.txt`
2.  Jalankan sistem: `python run_all.py`
3.  Akses Web UI: **http://localhost:8000**

Panduan penggunaan lebih detail: **[PANDUAN_WEB_UI.md](./PANDUAN_WEB_UI.md)**

---

**Disusun Oleh:**
*   Oryza Qiara Ramadhani - 084
*   Maritza Adelia Sucipto - 111
