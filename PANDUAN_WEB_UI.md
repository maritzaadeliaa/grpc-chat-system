# Panduan Menjalankan Web Chat gRPC (Branch `caca`)

Dokumen ini berisi panduan langkah demi langkah untuk menarik kode terbaru dari branch `caca` dan menjalankan Web UI Realtime Chat berbasis gRPC + FastAPI.

## 1. Tarik (Pull) Kode Terbaru
Buka terminal/CMD di dalam folder project Anda, lalu jalankan perintah berikut untuk mengunduh branch `caca` dari repository:
```bash
git fetch origin
git checkout caca
git pull origin caca
```

## 2. Install Dependensi Baru
Karena ada tambahan fitur UI Web dan WebSocket, Anda wajib menginstal dependensi Python yang baru ditambahkan:
```bash
pip install -r requirements.txt
```
*(Paket yang ditambahkan antara lain: `fastapi`, `uvicorn`, dan `websockets`)*.

---

## 3. Jalankan Ketiga Server gRPC (Backend)
Buka **3 Terminal yang Berbeda** (split terminal) dan jalankan masing-masing servis gRPC:

**Terminal 1:**
```bash
python -m server.user_service.user_server
```
**Terminal 2:**
```bash
python -m server.room_service.room_server
```
**Terminal 3:**
```bash
python -m server.chat_service.chat_server
```
Pastikan tidak ada *error* dan terminal Anda mencetak bahwa server berjalan (port `50051`, `50052`, `50053`).

---

## 4. Jalankan Web Proxy Server
Buka **Satu Terminal Tambahan (Terminal 4)**, lalu jalankan Uvicorn Proxy untuk menjembatani Browser dengan server gRPC:
```bash
python -m uvicorn proxy_server:app --reload
```
Tunggu hingga tertulis keterangan hijau `Application startup complete.`

---

## 5. Buka Aplikasi di Browser
Buka browser kesayangan Anda (Chrome/Firefox/Edge), dan ketik alamat berikut di *Address Bar*:
👉 **[http://localhost:8000/app](http://localhost:8000/app)**

Aplikasi Chat Web berdesain elegan (Glassmorphism) siap digunakan! 
* **Tips 1:** Untuk mengetes chat asinkron realtime antarpengguna, buka dua *tab* browser yang berbeda, login berdua menuju `Room` yang memiliki nama sama, dan cobalah mengobrol!
* **Tips 2:** Menyegarkan halaman (F5) tidak akan me-logout Anda berkat fitur sesi latar belakang!
