# Panduan Walkthrough Presentasi: gRPC Chat System (Week 9)

Dokumen ini berisi panduan skenario, pembagian tugas, dan poin-poin penting untuk video presentasi tugas Week 9.

## 🕒 Informasi Umum
- **Durasi Maksimal**: 15 Menit.
- **Presenter**: 
  1. **Oryza Qiara Ramadhani (084)** - Fokus: Arsitektur & Back-end gRPC.
  2. **Maritza Adelia Sucipto (111)** - Fokus: Web UI, WebSocket Proxy, & Fitur Integrasi.

---

## 📅 Struktur Waktu (Estimasi)
| No | Bagian | Durasi | Presenter |
|---|---|---|---|
| 1 | Pendahuluan & Deskripsi Proyek | 2 Menit | Oryza |
| 2 | Arsitektur Sistem (gRPC + Proxy + WS) | 2 Menit | Oryza |
| 3 | Demo Fitur 1 & 2: Login JWT & WebSocket Streaming | 3 Menit | Maritza |
| 4 | Demo Fitur 3 & 4: Event-Driven UI & Server-Initiated Events | 3 Menit | Maritza |
| 5 | Demo Fitur 5: Command & Control Bridge | 2 Menit | Maritza |
| 6 | Code Walkthrough (Alur gRPC ↔ WebSocket) | 2 Menit | Oryza |
| 7 | Penutup | 1 Menit | Bersama |

---

## 🎙️ Skenario & Skrip Video

### Bagian 1: Pendahuluan & Deskripsi Proyek (Oryza)
- **Tampilan**: On-camera + Judul Proyek.
- **Poin Penjelasan**:
  - Salam pembuka dan perkenalan anggota kelompok.
  - Deskripsi Proyek: "Sistem chat real-time yang mengoptimalkan komunikasi gRPC backend dengan antarmuka web melalui WebSocket proxy."
  - Tujuan: Mengintegrasikan gRPC Bidirectional Streaming ke Web UI agar performa backend yang cepat bisa dinikmati langsung di browser.

### Bagian 2: Arsitektur Sistem (Oryza)
- **Tampilan**: Diagram Arsitektur (bisa diambil dari README.md).
- **Poin Penjelasan**:
  - Jelaskan 3 Microservices gRPC: **User Service** (Unary), **Room Service** (Unary), dan **Chat Service** (Bidirectional Streaming).
  - Jelaskan peran **Web Proxy (FastAPI)**: Sebagai jembatan (bridge) yang mengubah protokol gRPC menjadi WebSocket agar bisa dibaca oleh browser.
  - Mengapa pakai Proxy? Karena browser tidak mendukung gRPC secara native dengan mudah.

### Bagian 3: Demo Fitur 1 & 2 (Maritza)
- **Tampilan**: Screen Record Browser (localhost:8000).
- **Poin Penjelasan**:
  - **Login JWT**: Tunjukkan proses login. Jelaskan bahwa setelah login, browser mendapatkan token JWT yang akan divalidasi saat membuka koneksi WebSocket.
  - **WebSocket gRPC Stream**: Masuk ke sebuah room (misal: 'umum'). Kirim pesan. Tunjukkan pesan terkirim secara instan di sisi lain (buka 2 tab browser).
  - Tekankan: "Data mengalir dari gRPC stream backend, diteruskan oleh proxy ke WebSocket, dan tampil otomatis tanpa refresh."

### Bagian 4: Demo Fitur 3 & 4 (Maritza)
- **Tampilan**: Fokus pada komponen UI di Sidebar & Header.
- **Poin Penjelasan**:
  - **Event-Driven UI**: Tunjukkan 3 komponen yang berubah dinamis:
    1. **Server Monitor**: Grafik CPU & RAM yang update tiap 5 detik (data dari server).
    2. **Online Users**: Daftar user di sebelah kiri yang update otomatis saat ada yang join/leave.
    3. **Activity Log**: Konsol log kecil di atas chat yang mencatat event sistem.
  - **Server-Initiated Events**: Tunggu sampai muncul notifikasi alert dari server (misal: "Sistem berjalan normal" atau "Maintenance notice"). Jelaskan bahwa ini didorong (pushed) oleh server secara proaktif tanpa request dari client.

### Bagian 5: Demo Fitur 5 (Maritza)
- **Tampilan**: Input Chat.
- **Poin Penjelasan**:
  - **Command & Control Bridge**: Ketik perintah `/cmd ping_services` di input chat.
  - Tunjukkan hasilnya di layar: UI menampilkan status kesehatan semua service gRPC.
  - Jelaskan: "Perintah ini dikirim via WebSocket, proxy memprosesnya dan memicu fungsi gRPC di backend, lalu hasilnya dikirim balik ke UI."

### Bagian 6: Code Walkthrough (Oryza)
- **Tampilan**: VS Code (File `web_proxy.py` dan `proto/chat.proto`).
- **Poin Penjelasan**:
  - Tunjukkan `chat.proto`: Definisi `ChatStream` sebagai `stream ChatMessage`.
  - Tunjukkan `web_proxy.py`: Fungsi `websocket_chat`.
  - Jelaskan alur: "Saat WebSocket dibuka, Proxy membuat thread `run_grpc_stream` yang mendengarkan stream gRPC. Setiap ada data dari gRPC, Proxy langsung melakukan `send_json` ke WebSocket browser."
  - Tunjukkan background task `server_metrics_broadcaster` yang mengurus Server-Initiated Events.

### Bagian 7: Penutup (Oryza & Maritza)
- **Tampilan**: On-camera.
- **Poin Penjelasan**:
  - Ringkasan singkat keberhasilan integrasi.
  - Ucapan terima kasih.

---

## 💡 Tips Presentasi
1. **Gunakan 2 Tab Browser**: Saat demo chat, buka dua jendela browser berdampingan (User A dan User B) untuk menunjukkan real-time streaming dengan jelas.
2. **Sorot Komponen UI**: Gunakan kursor atau tool penyorot saat menjelaskan "Server Monitor" atau "Activity Log".
3. **Koneksi Stabil**: Pastikan semua service sudah dijalankan dengan `python run_all.py` sebelum mulai merekam.
4. **On-Camera**: Pastikan wajah terlihat jelas di pojok layar sesuai instruksi tugas.

---
**Dibuat untuk membantu tugas InSis Week 9.**
**Oryza Qiara Ramadhani - 084 & Maritza Adelia Sucipto - 111**
