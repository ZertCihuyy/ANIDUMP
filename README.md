# ANIDB.MY.ID - AniList Data Dump

Repositori ini menyimpan *dump data* (salinan data) lengkap anime dari **AniList** secara gratis. Data diperbarui secara otomatis setiap jam menggunakan GitHub Actions.

## Isi Data
- **Data Raw Anime**: Informasi lengkap termasuk Judul (Romaji, English, Native), Sinopsis/Deskripsi, Status, Total Episode.
- **Genre & Tags**: Kategori dan tag beserta peringkat (rank).
- **Studio**: Studio animasi utama.
- **Karakter & Seiyuu**: Daftar karakter dan pengisi suara (Seiyuu) berbahasa Jepang.
- **Top & Musiman**: Data mencakup metrik skor, popularitas, serta season rilis.
- Format file berupa **JSON** yang dikelompokkan berdasarkan rentang ID anime agar ringan untuk diakses dan perubahan (*diff*) git tetap minimal.

## Struktur Folder
- `data/raw/anime/`: Berisi file JSON yang di-dump per kelompok (group) 1000 ID anime. Contoh: 
  - `anime_0-999.json` (Berisi anime dengan ID 0 sampai 999)
  - `anime_1000-1999.json` (Berisi anime dengan ID 1000 sampai 1999)
- `scripts/`: Berisi skrip utama (`dump_anilist.py`) dan dependenciesnya.

## Cara Kerja
1. **Source**: Script `scripts/dump_anilist.py` menggunakan **GraphQL API AniList**.
2. **Otomatisasi**: GitHub Actions (`.github/workflows/dump.yml`) akan menjalankan script setiap 1 jam untuk mengambil data terbaru secara **inkremental** (hanya mengambil data yang baru di-update di AniList pada jam-jam terakhir).
3. **Manual**: Anda juga dapat memicu dari tab *Actions* GitHub secara manual untuk mengambil data *full* (seluruh anime dari awal).

## Setup Repositori Ini (Untuk Pertama Kali)
1. Aktifkan *GitHub Actions* di repo ini.
2. Jalankan workflow "Hourly AniList Data Dump" secara manual dan pilih mode **full** untuk tarikan pertama (ini mungkin memakan waktu beberapa menit).
3. Setelah itu biarkan mode **incremental** berjalan otomatis setiap jam.

## Worker Script Sederhana (Mendatang)
Data ini disimpan dalam format JSON statis yang dapat diakses dengan cepat secara langsung melalui Raw URL GitHub. 
*Worker script* (misalnya Cloudflare Worker) dapat dirancang belakangan untuk membungkus Raw URL ini dan menyediakan pencarian, filter, dan routing API layaknya database asli (misal `api.anidb.my.id/anime/1`).

## Penggunaan
Anda bebas meng-clone dan menggunakan repositori ini untuk keperluan pengembangan web/aplikasi anime Anda (misalnya streaming app, database wiki, dll).

> **Peringatan & Catatan**: Data ini ditarik secara otomatis dari AniList API. Script ini telah dilengkapi pengaturan rate-limit untuk menghormati kebijakan AniList (maksimal 90 request/menit). Harap gunakan secara bijaksana.
# ANIDUMP
