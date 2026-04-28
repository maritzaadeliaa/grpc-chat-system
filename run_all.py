"""
gRPC Chat System - Full System Launcher
Menjalankan semua server (User, Room, Chat) + Web Proxy sekaligus.

Usage: python run_all.py
"""

import subprocess
import sys
import time
import os
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SERVICES = [
    {
        "name": "User Service",
        "cmd": [sys.executable, "-m", "server.user_service.user_server"],
        "port": 50052,
        "color": "\033[36m",  # Cyan
    },
    {
        "name": "Room Service",
        "cmd": [sys.executable, "-m", "server.room_service.room_server"],
        "port": 50053,
        "color": "\033[33m",  # Yellow
    },
    {
        "name": "Chat Service",
        "cmd": [sys.executable, "-m", "server.chat_service.chat_server"],
        "port": 50051,
        "color": "\033[35m",  # Magenta
    },
    {
        "name": "Web Proxy",
        "cmd": [sys.executable, "-m", "uvicorn", "web_proxy:app",
                "--host", "0.0.0.0", "--port", "8000", "--log-level", "warning"],
        "port": 8000,
        "color": "\033[32m",  # Green
    },
    {
        "name": "System Bot",
        "cmd": [sys.executable, "bot.py"],
        "port": "N/A",
        "color": "\033[34m",  # Blue
    },
]

RESET = "\033[0m"
BOLD  = "\033[1m"

processes = []

# Environment untuk subprocess: paksa UTF-8 agar emoji di child process bisa di-encode
CHILD_ENV = os.environ.copy()
CHILD_ENV["PYTHONUTF8"] = "1"
CHILD_ENV["PYTHONIOENCODING"] = "utf-8"


def stream_output(proc, name, color):
    """Stream output dari subprocess ke console dengan prefix warna."""
    try:
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                # Cetak dengan encoding-safe fallback
                try:
                    print(f"{color}[{name}]{RESET} {line}", flush=True)
                except UnicodeEncodeError:
                    safe = line.encode('ascii', errors='replace').decode('ascii')
                    print(f"{color}[{name}]{RESET} {safe}", flush=True)
    except Exception:
        pass


def start_all():
    print(f"\n{'=' * 55}")
    print(f"  gRPC Chat System - Starting All Services")
    print(f"{'=' * 55}\n")

    for svc in SERVICES:
        proc = subprocess.Popen(
            svc["cmd"],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",      # Baca output child sebagai UTF-8
            errors="replace",      # Karakter yang tidak bisa di-decode diganti ?
            bufsize=1,
            env=CHILD_ENV,         # Kirim env dengan PYTHONUTF8=1
        )
        processes.append(proc)

        # Thread untuk streaming output
        t = threading.Thread(
            target=stream_output,
            args=(proc, svc["name"], svc["color"]),
            daemon=True
        )
        t.start()

        # Tunggu sebentar antar launch biar tidak rebutan port
        time.sleep(1.0)
        print(f"{svc['color']}[OK] {svc['name']}{RESET} started (port {svc['port']})")

    print(f"\n{BOLD}{'─' * 55}{RESET}")
    print(f"{BOLD}  Web UI  : http://localhost:8000{RESET}")
    print(f"{BOLD}  Chat    : gRPC @ localhost:50051{RESET}")
    print(f"{BOLD}  User    : gRPC @ localhost:50052{RESET}")
    print(f"{BOLD}  Room    : gRPC @ localhost:50053{RESET}")
    print(f"{BOLD}{'─' * 55}{RESET}")
    print(f"\n  Tekan {BOLD}Ctrl+C{RESET} untuk menghentikan semua service.\n")


def stop_all():
    print(f"\n{BOLD}[STOP] Menghentikan semua service...{RESET}")
    for proc in processes:
        try:
            proc.terminate()
        except Exception:
            pass
    time.sleep(1.0)
    for proc in processes:
        try:
            proc.kill()
        except Exception:
            pass
    print(f"{BOLD}[OK] Semua service dihentikan.{RESET}\n")


def main():
    start_all()
    crashed = set()
    try:
        while True:
            for i, proc in enumerate(processes):
                if proc.poll() is not None and i not in crashed:
                    crashed.add(i)
                    svc_name = SERVICES[i]["name"]
                    print(f"\033[31m[!] {svc_name} crash (exit code {proc.returncode})!\033[0m")
            time.sleep(2)
    except KeyboardInterrupt:
        stop_all()


if __name__ == "__main__":
    main()
