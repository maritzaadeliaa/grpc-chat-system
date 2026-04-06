# gRPC Chat System

Sistem real-time chat menggunakan **gRPC Bidirectional Streaming** dengan Web UI dan CLI client.

## Arsitektur

```
┌─────────────────────────────────────────────────┐
│  Web Browser / CLI Client                        │
│  (WebSocket / gRPC)                              │
└────────────────┬────────────────────────────────┘
                 │
     ┌───────────▼────────────┐
     │  Web Proxy (FastAPI)   │  ← port 8000
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

## Setup & Instalasi

```bash
pip install -r requirements.txt
```

## Compile Protobuf

```bash
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/user.proto ./proto/room.proto ./proto/chat.proto
```

## Jalankan Semua Sekaligus (Recommended)

```bash
python run_all.py
```

Lalu buka browser ke: **http://localhost:8000**

---

## Jalankan Manual (Masing-masing Terminal)

### Terminal 1 - Chat Service (Port 50051)
```bash
python -m server.chat_service.chat_server
```

### Terminal 2 - User Service (Port 50052)
```bash
python -m server.user_service.user_server
```

### Terminal 3 - Room Service (Port 50053)
```bash
python -m server.room_service.room_server
```

### Terminal 4 - Web Proxy (Port 8000)
```bash
python web_proxy.py
```

### Terminal 5 - CLI Client (Opsional)
```bash
python -m client.client
```

## Fitur

- ✅ **Real-time chat** via gRPC Bidirectional Streaming
- ✅ **Multi-room** — bisa join beberapa room sekaligus
- ✅ **Web UI** — antarmuka browser modern
- ✅ **CLI Client** — send & receive secara bersamaan (threading)
- ✅ **Auto-cleanup** — user/room otomatis dihapus saat disconnect
- ✅ **Login/Logout** — tracking user aktif

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
├── web_proxy.py            # FastAPI proxy (HTTP/WS ↔ gRPC)
├── run_all.py              # Launcher semua service
├── requirements.txt
└── README.md
```
