# gRPC Real-Time Chat System & Web Bridge (Week 9)

Proyek ini adalah sistem komunikasi terintegrasi yang menggabungkan efisiensi **gRPC microservices** dengan fleksibilitas **WebSocket** untuk antarmuka Web yang modern dan responsif.

---

## 🛠️ Panduan Memulai (Quick Start)

Ikuti langkah ini untuk menjalankan seluruh sistem di komputer Anda:

1.  **Persiapan environment**:
    Pastikan Python 3.8+ sudah terinstall. Buka terminal di folder proyek dan jalankan:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Menjalankan Sistem**:
    Gunakan launcher otomatis yang telah disediakan untuk menyalakan 4 service sekaligus (User, Room, Chat, dan Web Proxy):
    ```bash
    python run_all.py
    ```

3.  **Akses Antarmuka**:
    Buka browser Anda dan akses: **[http://localhost:8000](http://localhost:8000)**

---

## 📘 Penjelasan Fitur & Implementasi Tugas

Sistem ini dibangun secara khusus untuk memenuhi 4 kriteria wajib tugas Integration Systems:

### 1. Implementasi WebSocket (gRPC Bridge)
*   **Implementasi**: Terletak pada `web_proxy.py`.
*   **Cara Kerja**: Backend menggunakan gRPC *Bidirectional Streaming*. Karena browser tidak bisa melakukan gRPC secara native, Proxy FastAPI bertindak sebagai "jembatan". Proxy membuka koneksi WebSocket ke browser dan secara simultan membuka gRPC stream ke Chat Server. Data dipompa secara dua arah tanpa putus.
*   **Hasil**: Pesan chat muncul seketika di UI tanpa perlu refresh halaman.

### 2. Event-Driven UI (Dynamic Components)
UI dirancang untuk bereaksi terhadap pesan (event) yang datang dari WebSocket. Terdapat lebih dari 3 komponen dinamis:
*   **Server Monitor**: Bar CPU, Memory, dan koneksi aktif yang bergerak dinamis.
*   **Activity Log**: Konsol sistem yang mencatat aktivitas server secara real-time.
*   **Status Indicators**: Dot "Live" yang berkedip dan status koneksi yang berubah otomatis jika server mati/nyala.
*   **Chat Bubbles**: Area pesan yang bertambah secara dinamis saat ada aktivitas chat.

### 3. Server-Initiated Events (Proactive Push)
*   **Implementasi**: Menggunakan background task `asyncio` di sisi Proxy.
*   **Cara Kerja**: Server tidak menunggu permintaan klien. Sebuah timer di backend (`server_metrics_broadcaster`) secara proaktif mengumpulkan data kesehatan server dan mendorongnya ke semua browser yang terhubung.
*   **Contoh**: Notifikasi sistem seperti "Auto-backup database sedang berjalan" atau alert "CPU Usage kritis" yang muncul otomatis di layar user.

### 4. Command & Control Bridge
*   **Implementasi**: Protokol pesan berbasis prefix `/cmd`.
*   **Cara Kerja**: Saat user mengetik perintah diawali `/cmd`, Proxy akan menangkap pesan tersebut, membedah instruksinya, dan melakukan pemanggilan fungsi gRPC *Unary RPC* (seperti `GetRoomMembers`) ke layanan backend yang sesuai.
*   **Daftar Command**:
    *   `/cmd get_members` : Mengetahui siapa saja yang ada di room saat ini.
    *   `/cmd ping_services` : Memeriksa kesehatan koneksi antar semua microservices.
    *   `/cmd broadcast <pesan>` : Mengirim pengumuman sistem ke seluruh anggota room.

---

## 📐 Arsitektur Microservices

| Service | Port | Teknologi | Tanggung Jawab |
| :--- | :--- | :--- | :--- |
| **Web Proxy** | 8000 | FastAPI | Jembatan WebSocket <-> gRPC & Provider Web UI |
| **User Service** | 50052 | gRPC Unary | Autentikasi dan manajemen user |
| **Room Service** | 50053 | gRPC Unary | Manajemen grup dan Command & Control |
| **Chat Service** | 50054 | gRPC Bidi-Stream | Inti pengiriman pesan real-time |

---

## 📂 Struktur Folder Proyek
*   `proto/` : Berisi file `.proto` yang mendefinisikan kontrak komunikasi antar service.
*   `server/` : Berisi kode sumber untuk 3 microservices backend.
*   `web/` : Berisi file `index.html` yang mencakup HTML, CSS modern, dan JavaScript logic.
*   `web_proxy.py` : Logika utama penghubung (bridge) sistem.
*   `run_all.py` : Script pembantu untuk menjalankan sistem dengan satu perintah.

---

**Disusun Oleh:**
*   Oryza Qiara Ramadhani - 084
*   Maritza Adelia Sucipto - 111
