# <div align="center">LAYANAN EKSTRAKSI ENTITAS BERNAMA PADA ARTIKEL BERITA</div>

## **Arsitektur Sistem**

```
Panel Web Interaktif
        │
        ▼ (POST /extract-entities JSON)
FastAPI Backend
        │
        ├── Validasi Input Pydantic (teks tidak kosong, panjang <= 10.000 karakter)
        │
        ▼
Pipeline NER
        ├── Penggabungan Judul dan Isi
        └── Model spaCy Hasil Adaptasi (models/trained_ner)
                │
                ▼
Respons JSON Deterministik (Daftar Entitas, Rentang Offset, Metadata)
```

## **Prasyarat Sistem**

Dokumen ini mengasumsikan lingkungan eksekusi telah memenuhi dependensi berikut:
* Lingkungan Python versi 3.10 atau versi di atasnya
* Manajer paket *pip*
* Lingkungan virtual terisolasi

## **Langkah Pemasangan**

Inisialisasi lingkungan kerja dan instalasi pustaka dilakukan melalui konsol:

```bash
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## **Pengolahan Data**

Pembersihan berkas mentah dan pembentukan dataset teranotasi dijalankan dengan urutan:

```bash
python src/profile_data.py
python src/prepare_dataset.py
```

## **Pelatihan Model**

Proses adaptasi komponen pengenal entitas terhadap domain berita finansial dieksekusi melalui perintah:

```bash
python src/train_and_eval.py
```

## **Menjalankan Layanan Web**

Server lokal diaktifkan menggunakan *uvicorn*:

```bash
uvicorn src.app:app --reload --port 8000
```

Antarmuka formulir peramban dapat diakses pada alamat `http://127.0.0.1:8000`.

## **Pengujian Otomatis**

Validasi fungsionalitas menyeluruh dijalankan menggunakan modul *pytest*:

```bash
pytest tests/test_api.py
```

## **Spesifikasi Input API**

Layanan menyediakan gerbang ekstraksi melalui metode HTTP `POST` pada *endpoint* `/extract-entities`. Struktur data yang dikirimkan menggunakan format JSON:

```json
{
  "title": "UOB Malaysia and Maybank complete landmark transaction",
  "body": "UOB Malaysia, RHB Banking Group and Maybank completed a financial transaction in Kuala Lumpur on Monday."
}
```

Ketentuan parameter masukan mencakup:
* Nilai `title` dan `body` wajib berupa teks
* Input tidak boleh kosong maupun hanya berisi spasi
* Panjang karakter dibatasi paling banyak 10.000 karakter

## **Spesifikasi Output API**

Permintaan yang lolos validasi menghasilkan kode status HTTP 200 disertai daftar luaran entitas terstruktur:

```json
{
  "entities": [
    {
      "text": "UOB Malaysia",
      "label": "ORG",
      "start": 0,
      "end": 12
    },
    {
      "text": "Maybank",
      "label": "ORG",
      "start": 17,
      "end": 24
    },
    {
      "text": "Kuala Lumpur",
      "label": "GPE",
      "start": 139,
      "end": 151
    }
  ],
  "meta": {
    "entity_count": 3,
    "model": "models/trained_ner",
    "combined_length": 162
  }
}
```

Bila terjadi pelanggaran format atau nilai kosong, server mengembalikan status HTTP 400 dengan rincian galat.

## **Metodologi Pembagian Data**

Dataset dipecah dengan rasio 70% data latih, 15% data validasi, dan 15% data uji. Penentuan partisi didasarkan pada identitas unik artikel menggunakan nilai pengacak konstan `42` guna mencegah kebocoran informasi antarpartisi.

## **Hasil Evaluasi Model**

Evaluasi menggunakan metode pencocokan batas rentang ketat (*exact-span matching*) pada data uji yang belum pernah dilihat model selama proses latihan:

| Metrik Evaluasi | Model Acuan (*en_core_web_sm*) | Model Adaptasi (*models/trained_ner*) |
| :--- | :--- | :--- |
| **Precision Keseluruhan** | 0.8571 | 0.8636 |
| **Recall Keseluruhan** | 0.8571 | 0.9048 |
| **F1-Score Keseluruhan** | 0.8571 | 0.8837 |
| *F1 Organisasi (ORG)* | 0.9100 | 0.9600 |
| *F1 Wilayah Geopolitik (GPE)* | 0.8900 | 0.8900 |
| *F1 Tokoh (PERSON)* | 1.0000 | 1.0000 |
| *F1 Tanggal (DATE)* | 1.0000 | 1.0000 |
| *F1 Lokasi Geografis (LOC)* | 0.5000 | 0.5000 |

## **Analisis Kesalahan Kasus Nyata**

* Batas Gelar Kehormatan Lokal
  Rentang nama tokoh seperti "Tan Sri Razarudin Husain" kerap terpotong menjadi "Razarudin Husain". Model dasar bahasa Inggris cenderung memperlakukan kata sandang gelar kenegaraan kawasan Melayu sebagai kata benda terpisah di luar entitas individu.
* Variasi Akhiran Badan Hukum
  Pencocokan rentang ketat gagal saat model mengekstraksi "RHB Bank" sementara label acuan mencatat "RHB Bank Berhad". Ketidakteraturan penyertaan istilah legal perseroan memicu penalti ganda pada metrik presisi dan perolehan kembali.
* Interferensi Alih Kode Bahasa
  Kalimat berita yang memadukan kosakata bahasa Melayu dan bahasa Inggris membingungkan pembacaan tata bahasa model. Gejala ini berakibat pada hilangnya deteksi nama divisi korporasi akibat ketiadaan kosakata morfologi lokal dalam kamus vektor bawaan.

## **Definisi Entitas Bernama**

Rentang teks diakui sebagai entitas bernama apabila teks merujuk pada objek riil spesifik lewat penanda khusus atau nama diri. Entitas tersebut dikelompokkan ke dalam kategori semantik terdefinisi, mencakup korporasi, pembagian wilayah administratif, nama individu, serta penanggalan kalender.

## **Urgensi Penggabungan Judul dan Isi**

Pengolahan judul dan isi secara terpadu diperlukan demi mempertahankan keutuhan konteks diskursus. Judul berita lazim memuat akronim padat tanpa artikel penjelas, sedangkan bentuk panjang dari entitas lazim diuraikan pada alinea pembuka. Pemrosesan yang terisolasi menghilangkan relasi koreferensi lintas batas teks.

## **Kategori Entitas yang Didukung**

Sistem mendeteksi lima kategori utama:
* ORG
  Mencakup korporasi perbankan, konglomerasi industri, dan otoritas regulator moneter.
* GPE
  Merujuk pada kedaulatan negara, provinsi, serta entitas perkotaan resmi.
* LOC
  Mengidentifikasi kawasan regional geografis non-politik atau bangunan fisik.
* PERSON
  Meliputi figur pejabat publik, direksi perbankan, dan pengambil kebijakan korporasi.
* DATE
  Mencakup nama hari, penanda bulan, serta format tahun numerik.

## **Dampak Variabel Linguistik**

Karakteristik teks memberikan pengaruh nyata terhadap akurasi ekstraksi:
* Tanda Baca
  Penyebutan nama yang memuat karakter ampersand atau titik singkatan memerlukan pemisahan token yang konsisten agar batas karakter tidak terfragmentasi.
* Kapitalisasi
  Pola *title case* menjadi sinyal utama pembeda entitas. Teks judul yang menggunakan huruf kapital penuh menurunkan kepekaan model secara drastis.
* Variasi Bahasa
  Ketiadaan kosakata afiksasi bahasa Melayu pada representasi vektor bahasa Inggris memicu kegagalan pembacaan konteks gramatikal lokal.

## **Distingsi Komponen Luaran**

Struktur hasil ekstraksi memisahkan tiga dimensi informasi:
* Teks
  Karakter harfiah persis sebagaimana tercantum pada naskah berita sumber.
* Label
  Penetapan kelas semantik yang mewakili peran entitas di dunia nyata.
* Nilai Rentang Karakter
  Penunjuk posisi indeks berbasis nol yang menandai titik mula serta titik akhir pembacaan token di dalam untaian teks gabungan.

## **Penanganan Kemunculan Berulang**

Setiap kemunculan kata yang sama diekstraksi sebagai instans mandiri berdasarkan koordinat posisi masing-masing. Penulisan nama dengan kapitalisasi tidak seragam dicatat sebagai rentang terpisah. Penyatuan entitas berulang menjadi satu identitas kanonikal memerlukan modul lanjutan berupa penautan entitas.

## **Prioritas Perbaikan untuk Pemantauan Media**

Kegagalan mendeteksi entitas institusi dan eksekutif kunci merupakan galat paling merugikan dalam alur pemantauan berita. Kehilangan informasi tersebut mengakibatkan analisis eksposur risiko pasar menjadi tidak akurat. Akurasi dapat ditingkatkan melalui integrasi kamus entitas terdaftar pada bursa efek lokal, penggunaan arsitektur *transformer* dwibahasa, serta perluasan korpus anotasi.

## **Aspek Etika dan Regulasi Pemrosesan Teks**

Penerapan ekstraksi data berita wajib memperhatikan batasan hukum:
* Hak Cipta
  Penyimpanan naskah artikel berita secara utuh tanpa lisensi resmi berpotensi melanggar hak eksklusif penerbit media komersial.
* Privasi Individu
  Pengindeksan otomatis terhadap nama warga yang tercantum dalam berita perkara hukum menyentuh kepatuhan undang-undang pelindungan data pribadi.
* Bias Korpus Latih
  Model dasar yang didominasi oleh korpus berita Barat memperlihatkan akurasi yang lebih rendah terhadap penyebutan nama tokoh dan struktur kelembagaan regional Asia Tenggara.

## **Batasan Teknis Sistem**

* Pipeline dioptimalkan secara dominan untuk naskah berbahasa Inggris, sehingga kinerja mengalami reduksi ketika menerima naskah berbahasa Melayu murni.
* Penilaian berbasis pencocokan rentang ketat sangat rentan terhadap inkonsistensi penulisan bentuk badan usaha.
* Beban memori komputasi membatasi volume karakter paling banyak 10.000 karakter untuk setiap panggilan layanan.
