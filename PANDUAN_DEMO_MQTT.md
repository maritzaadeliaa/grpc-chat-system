# 🎓 Panduan Demo Implementasi Fitur MQTT v5

Dokumen ini adalah skrip panduan untuk presentasi/demo tugas. Di sini terdapat daftar fitur wajib, **cara mendemokannya** di depan dosen, dan **referensi baris kode (Implementation Code)** untuk membuktikan bahwa fitur tersebut dikerjakan dengan murni (*hardcoded*) pada protokol MQTT v5.

---

## 1. 📊 Dashboard Monitoring MQTT (Fitur Spesial)
Sebuah fitur tambahan untuk memonitor lalu lintas data asli dari Mosquitto Broker.

*   **Cara Demo:**
    1. Buka `http://localhost:8000/dashboard` di layar terpisah.
    2. Tunjukkan *Broker Internal Metrics* yang menunjukkan Uptime, Active Clients, dan pergerakan Bytes In/Out yang ter-update otomatis menggunakan topik bawaan `$SYS/#`.
    3. Kirim pesan chat biasa dan perhatikan bagian **Live Server Traffic Log** yang akan merekam aktivitas *real-time*.
*   **Bukti Kode (`web_proxy.py`):**
    *   **Line 137-138:** `client.subscribe("$SYS/#")` untuk menyadap metrik asli Mosquitto.
    *   **Line 152-158:** Menangkap log broker yang masuk dari topik `$SYS` dan menyimpannya di memori.
    *   **Line 229-234:** *Proxy* mem-*broadcast* log *traffic chat* langsung ke layar Dashboard (`notify_dashboards`).

---

## 2. ⚡ QoS (Quality of Service) 0, 1, dan 2
Menjamin tingkat pengiriman pesan. QoS 2 menjamin pesan dikirim tepat satu kali tanpa duplikasi (*four-way handshake*).

*   **Cara Demo:**
    1. Di UI Chat (`http://localhost:8000`), ketik pesan "Halo QoS 2".
    2. Ubah *dropdown* pengaturan di sebelah tombol kirim menjadi **QoS 2**.
    3. Klik kirim. Tunjukkan di layar **Dashboard** bahwa grafik dan angka **"QoS 2 Sent"** langsung bertambah `+1`.
*   **Bukti Kode (`web_proxy.py`):**
    *   **Line 815-820:** Mengambil nilai `qos=qos` dari input UI.
    *   **Line 820:** `mqtt_client.publish(publish_topic, payload, qos=qos, retain=retain, properties=publish_props)`.

---

## 3. 📌 Retained Message (Fitur "Pin Message")
Memerintahkan broker untuk menyimpan pesan terakhir di suatu topik, sehingga pengguna yang baru *subscribe* (baru *join* room) akan langsung menerima pesan tersebut.

*   **Cara Demo:**
    1. *User* A mengirim pesan "Selamat datang di grup!" dan mencentang kotak **[x] Pin Message**.
    2. Pesan muncul dengan *badge* merah `📌 PINNED`.
    3. Buka tab browser baru, login sebagai *User* B, dan gabung ke room yang sama.
    4. *User* B akan **langsung** melihat pesan yang di-*pin* tadi saat baru bergabung.
*   **Bukti Kode (`web_proxy.py`):**
    *   **Line 820:** Menggunakan argumen `retain=retain` saat memanggil fungsi `publish()`.
    *   **Line 210-218:** Logika di sisi *Proxy* untuk menangkap bendera (*flag*) `msg.retain` dari broker dan menyimpannya (`retained_messages[room] = payload`).

---

## 4. ⏳ Message Expiry Interval
Fitur khusus MQTT v5 di mana Broker akan otomatis membuang/menghapus pesan dari antreannya jika sudah melewati batas waktu (mencegah penumpukan data usang).

*   **Cara Demo:**
    1. Ketik pesan, atur *dropdown* **Expiry** menjadi **10 Detik**, lalu kirim.
    2. Lihat di layar **Dashboard**, pesan chat tersebut akan dilacak. Setelah 10 detik, akan muncul log merah: `🗑️ [EXPIRED] Pesan telah dihapus dari MQTT Broker.`
    3. Bersamaan dengan itu, pesan di layar UI Chat juga akan memiliki *timer* dan **menghilang otomatis** dari layar (efek *self-destruct*).
*   **Bukti Kode:**
    *   **Backend (`web_proxy.py` Line 801-803):** `publish_props.MessageExpiryInterval = int(expiry)`. Menyuntikkan properti khusus v5 ke dalam paket MQTT.
    *   **Backend (Line 345 & 695):** Logika pengecekan kapan *Retained Message* harus dihapus otomatis dari *cache* jika umurnya sudah lewat `expiry`.
    *   **Frontend (`web/index.html` Line 580):** Menangkap properti *expiry* dan menciptakan efek visual hitung mundur (⏱️) untuk menghapus elemen HTML.

---

## 5. 🤖 Chat Bot (Request-Response, User Property)
Menggunakan pola *Request-Response* MQTT v5 untuk meminta balasan langsung tanpa mengirim pesan secara *broadcast* ke seluruh room.

*   **Cara Demo:**
    1. Di ruang obrolan, ketik perintah `/bot ping` atau `/bot time`.
    2. Bot (dari *Chat Worker*) akan merespons **hanya kepada pengirimnya saja** (bersifat *private*), tidak muncul di layar pengguna lain.
*   **Bukti Kode (`web_proxy.py` & `chat_server.py`):**
    *   **Proxy (`web_proxy.py` Line 778-779):** Menyetel properti `req_props.ResponseTopic = bot_res_topic` dan `req_props.UserProperty = [("user_id", username)]`.
    *   **Worker (`chat_server.py` Line 74-76):** Bot membaca properti `res_topic = dict(props.UserProperty).get("user_id")` lalu mengirim balasan persis ke *topic* balasan tersebut.

---

## 6. 🚨 LWT (Last Will and Testament)
Pesan wasiat. Jika *Proxy Server* tiba-tiba terputus koneksinya (mati lampu, *crash*), Mosquitto Broker akan otomatis menyebarkan pesan peringatan ke klien yang tersisa.

*   **Cara Demo:**
    1. Buka aplikasi di *browser* dan buka layar Dashboard.
    2. Matikan paksa program Python (`web_proxy.py`) di *terminal* dengan `Ctrl+C`.
    3. Tunggu beberapa detik, semua halaman browser akan memunculkan kotak Alert Merah besar: **"🚨 Proxy Server Terputus! Coba muat ulang halaman."**
*   **Bukti Kode (`web_proxy.py`):**
    *   **Line 238-246:** Menyetel wasiat sebelum terhubung ke broker menggunakan `lwt_props = Properties(PacketTypes.WILLMESSAGE)` dan memanggil fungsi `mqtt_client.will_set("alert/system", ..., properties=lwt_props)`.

---

## 7. ⚖️ Shared Subscriptions (Load Balancing)
Membagi beban kerja ke beberapa *subscriber*. Jika ratusan ribu *chat* masuk, beban tidak ditanggung oleh satu program saja.

*   **Cara Demo:**
    Jelaskan kepada dosen bahwa *Chat Worker* (yang bertugas menjalankan Bot) tidak *subscribe* ke topik mentah, melainkan ke antrean bersama (*Shared Group*).
*   **Bukti Kode (`chat_server.py`):**
    *   **Line 104:** `client.subscribe("$share/chat_workers/chat/room/#", qos=1)`. Ini membagi rata pesan ke semua *worker* yang terhubung dalam grup `chat_workers`.

---

## 8. 🛡️ Flow Control (Receive Maximum)
Mencegah server *worker* kebanjiran beban trafik (*overload/DDoS*) dengan membatasi jumlah pesan "belum dikonfirmasi" yang boleh dikirim oleh Broker.

*   **Cara Demo:**
    Jelaskan bahwa sistem dirancang agar *Worker* memberitahu Broker *limit* kapasitas proses aslinya di awal koneksi.
*   **Bukti Kode (`chat_server.py`):**
    *   **Line 93:** Menyetel `connect_props.ReceiveMaximum = 10`. Ini berarti Mosquitto Broker maksimal hanya akan melempar 10 pesan beruntun ke *Worker* sebelum *Worker* membalas dengan sinyal `PUBACK` (Acknowledge).

---
> **💡 Tips Presentasi:** 
> Mulailah dari menunjukkan UI aplikasi secara kasual, lalu buka *Dashboard Monitoring*, lalu buktikan metrik QoS, Pin, dan Expiry berjalan lancar karena ini yang paling interaktif. Terakhir, tunjukkan fitur Bot, dan tutup dengan mematikan server secara paksa untuk mendemokan LWT! Semoga sukses! 🎯
