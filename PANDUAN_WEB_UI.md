# Panduan Menjalankan Web Chat gRPC

Dokumen ini berisi panduan lengkap untuk menjalankan **Web UI Realtime Chat** berbasis gRPC Bidirectional Streaming + FastAPI WebSocket Proxy.

---

## Gambaran Arsitektur

```
┌──────────────────────────────────────────────────────┐
│            Browser / CLI Client                      │
│         (WebSocket / gRPC Bidirectional)             │
└─────────────────────┬────────────────────────────────┘
                      │ WebSocket (ws://)
          ┌───────────▼──────────────┐
          │   Web Proxy — FastAPI    │  <- Port 8000
          │   (web_proxy.py)         │
          └──┬──────────┬────────────┘
             │ gRPC     │ gRPC      │ gRPC
    ┌────────▼──┐  ┌────▼───┐  ┌───▼──────┐
    │  User     │  │  Room  │  │  Chat    │
    │  Service  │  │Service │  │  Service │
    │ :50052    │  │ :50053 │  │  :50051  │
    └───────────┘  └────────┘  └──────────┘
```

Setiap komponen berjalan sebagai **proses terpisah**. Web Proxy bertugas menjembatani browser (HTTP/WebSocket) dengan ketiga server gRPC di belakangnya.

---

## Prasyarat

Pastikan sudah terinstall di komputer Anda:

- **Python 3.8+** — cek dengan `python --version`
- **pip** — cek dengan `pip --version`
- **Git** — cek dengan `git --version`

---

## 1. Tarik (Pull) Kode Terbaru

Buka terminal di dalam folder project, lalu jalankan:

```bash
git fetch origin
git checkout main
git pull origin main
```

> Jika kamu bekerja di branch lain, ganti `main` dengan nama branch yang sesuai.

---

## 2. Install Dependensi

Instal semua dependensi Python yang dibutuhkan:

```bash
pip install -r requirements.txt
```

Paket yang akan diinstall antara lain:

| Paket | Fungsi |
|---|---|
| `grpcio` | Core library gRPC untuk Python |
| `grpcio-tools` | Compiler file `.proto` ke `.py` |
| `fastapi` | Web framework untuk proxy server |
| `uvicorn[standard]` | ASGI server untuk menjalankan FastAPI |
| `websockets` | Dukungan WebSocket di server |

---

## 3. Compile File Protobuf (Jika Diperlukan)

> **Lewati langkah ini** jika file `chat_pb2.py`, `user_pb2.py`, `room_pb2.py` sudah ada di folder root project.

Jika file tersebut belum ada atau proto baru saja diubah, jalankan perintah berikut dari folder root project:

```bash
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/user.proto ./proto/room.proto ./proto/chat.proto
```

Pastikan file-file berikut muncul di folder root:

```
chat_pb2.py      chat_pb2_grpc.py
room_pb2.py      room_pb2_grpc.py
user_pb2.py      user_pb2_grpc.py
```

---

## 4. Cara Menjalankan

### Cara 1: Otomatis — Semua Sekaligus (Direkomendasikan)

Cukup jalankan **satu perintah** ini dari root folder project:

```bash
python run_all.py
```

Script ini akan otomatis menjalankan **keempat service** sekaligus dan menampilkan log berwarna dari masing-masing service di terminal yang sama.

```
=======================================================
  gRPC Chat System - Starting All Services
=======================================================

[OK] User Service started (port 50052)
[OK] Room Service started (port 50053)
[OK] Chat Service started (port 50051)
[OK] Web Proxy      started (port 8000)
-------------------------------------------------------
  Web UI  : http://localhost:8000
  Chat    : gRPC @ localhost:50051
  User    : gRPC @ localhost:50052
  Room    : gRPC @ localhost:50053
-------------------------------------------------------
  Tekan Ctrl+C untuk menghentikan semua service.
```

Tekan **Ctrl+C** untuk menghentikan semua service sekaligus.

---

### Cara 2: Manual — 4 Terminal Terpisah

Buka **4 terminal** (bisa pakai fitur Split Terminal di VS Code) dan jalankan masing-masing:

**Terminal 1 — Chat Service** (Port 50051):
```bash
python -m server.chat_service.chat_server
```

**Terminal 2 — User Service** (Port 50052):
```bash
python -m server.user_service.user_server
```

**Terminal 3 — Room Service** (Port 50053):
```bash
python -m server.room_service.room_server
```

**Terminal 4 — Web Proxy** (Port 8000):
```bash
python web_proxy.py
```

Pastikan tiap terminal menampilkan output bahwa server sudah berjalan.

---

## 5. Buka Aplikasi di Browser

Setelah semua service berjalan, buka browser (Chrome / Firefox / Edge) dan akses:

### http://localhost:8000

Tampilan aplikasi chat berdesain gelap (dark mode) akan langsung muncul!

---

## 6. Cara Menggunakan Aplikasi

### Login & Masuk Room

1. Masukkan **Username** yang unik (tidak boleh sama dengan user lain yang sedang online)
2. Masukkan **Nama Room** yang ingin dimasuki (bebas, contoh: `room-it`, `umum`, `diskusi`)
3. Klik tombol **"Masuk ke Chat"**

### Chatting

- Ketik pesan di kolom input bawah, lalu tekan **Enter** atau klik tombol kirim
- Tekan **Shift+Enter** untuk pindah baris tanpa mengirim
- Pesan dari dirimu muncul di **kanan** (warna ungu)
- Pesan dari orang lain muncul di **kiri** (abu-abu)

### Multi-Room

- Klik **"+ Join"** di sidebar kiri untuk masuk ke room tambahan
- Klik nama room di sidebar untuk berpindah antar room
- Angka merah di samping nama room menunjukkan **pesan belum dibaca**

### Keluar

- Klik **"Keluar Room"** di pojok kanan atas untuk keluar dari room aktif
- Klik **"Keluar"** di sidebar bawah untuk logout sepenuhnya

---

## 7. Cara Menggunakan CLI Client (Opsional)

Selain Web UI, tersedia juga **terminal client** yang bisa digunakan bersamaan:

```bash
python -m client.client
```

Masukkan username dan room saat diminta. CLI client mendukung **send & receive sekaligus** menggunakan threading — kamu bisa mengetik pesan sambil menerima pesan dari user lain secara real-time.

Ketik `/keluar` untuk keluar dari CLI client.

---

## Tips & Trik

> **Tip 1 — Test Multi-User:** Buka **dua tab browser** (atau dua browser berbeda), login dengan username berbeda ke room yang sama. Coba ngobrol antara keduanya untuk merasakan efek real-time!

> **Tip 2 — Multi-Room:** Satu user bisa join ke beberapa room sekaligus. Coba join ke `room-a` dan `room-b`, lalu test kirim pesan di masing-masing room.

> **Tip 3 — Mix CLI + Web:** Jalankan CLI client di terminal dan buka Web UI di browser, login ke room yang sama, lalu chat antara keduanya!

> **Tip 4 — Lihat Log Server:** Saat menjalankan `python run_all.py`, amati log berwarna di terminal untuk melihat setiap user yang join/leave dan setiap pesan yang dibroadcast secara real-time.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'grpcio'`
```bash
pip install -r requirements.txt
```

### `Address already in use` / Port sudah terpakai
Ada instance server yang masih berjalan. Hentikan semua proses Python dahulu:
```bash
# Windows (PowerShell)
Get-Process python* | Stop-Process -Force
```
Lalu jalankan ulang.

### `chat_pb2.py not found` / ImportError pada pb2
Compile ulang file proto:
```bash
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/user.proto ./proto/room.proto ./proto/chat.proto
```

### Web UI terbuka tapi tidak bisa login
Pastikan **semua 4 proses** sudah berjalan (Chat, User, Room Service + Web Proxy). Cek terminal masing-masing untuk error.

### Username sudah dipakai
Setiap username harus unik saat online. Gunakan username lain atau restart server untuk me-reset semua sesi.

---

## Struktur Proyek

```
grpc-chat-system/
├── proto/
│   ├── user.proto              # Definisi UserService (Login/Logout)
│   ├── room.proto              # Definisi RoomService (Join/Leave)
│   └── chat.proto              # Definisi ChatService (Bidirectional Stream)
├── server/
│   ├── user_service/
│   │   └── user_server.py      # gRPC server — port 50052
│   ├── room_service/
│   │   └── room_server.py      # gRPC server — port 50053
│   └── chat_service/
│       └── chat_server.py      # gRPC server — port 50051
├── client/
│   └── client.py               # CLI Client (threading)
├── web/
│   └── index.html              # Web UI (dark mode)
├── web_proxy.py                # FastAPI proxy: HTTP/WebSocket <-> gRPC
├── run_all.py                  # Launcher semua service sekaligus
├── requirements.txt            # Daftar dependensi Python
├── PANDUAN_WEB_UI.md           # Dokumen ini
└── README.md                   # Deskripsi project
```

---

*Dibuat untuk tugas mata kuliah Integrasi Sistem Informasi — Semester 4*  
*Oryza Qiara Ramadhani - 084 | Maritza Adelia Sucipto - 111*
