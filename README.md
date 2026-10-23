# Named-Entity Recognition (NER) Artikel Berita

Layanan berbasis web ringan untuk mengekstraksi entitas bernama (organisasi, lokasi, tokoh/orang, tanggal) dari judul (*title*) dan isi (*body*) artikel berita menggunakan spaCy dan FastAPI[cite: 1].

---

## 1. Arsitektur Sistem

```
Panel Peramban (HTML/JS)
        │
        ▼ (POST /extract-entities JSON)
FastAPI Backend (src/app.py)
        │
        ├── Validasi Input (Pydantic: teks tidak kosong, batas <= 10.000 karakter)
        │
        ▼
NER Pipeline (src/ner_pipeline.py)
        ├── Penggabungan Judul + Isi (Pemisah batas kalimat yang aman)
        └── Model spaCy Fine-Tuned (models/trained_ner)
                │
                ▼
Respons JSON Deterministik (Daftar Entitas, Rentang Karakter, Metadata)
```

---

## 2. Instalasi & Panduan Cepat

### Prasyarat
* Python 3.10+
* Virtual Environment (disarankan)

### Langkah Pemasangan

```bash
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Penyiapan Data & Pelatihan Model

```bash
python src/profile_data.py
python src/prepare_dataset.py
python src/train_and_eval.py
```

### Menjalankan Layanan Web

```bash
uvicorn src.app:app --reload --port 8000
```

Buka antarmuka panel peramban di `http://127.0.0.1:8000`[cite: 1].

### Menjalankan Pengujian Otomatis

```bash
pytest tests/test_api.py
```

---

## 3. Spesifikasi Kontrak API

### Endpoint: `POST /extract-entities`

#### Contoh Permintaan (Request Payload)[cite: 1]
```json
{
  "title": "UOB Malaysia and Maybank complete landmark transaction",
  "body": "UOB Malaysia, RHB Banking Group and Maybank completed a financial transaction in Kuala Lumpur on Monday."
}
```

#### Contoh Respons Berhasil (200 OK)[cite: 1]
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

#### Contoh Respons Kesalahan (400 Bad Request)[cite: 1]
```json
{
  "detail": "Invalid input format or validation error",
  "errors": [
    {
      "loc": ["body", "title"],
      "msg": "Field cannot be empty or blank",
      "type": "value_error"
    }
  ]
}
```

---

## 4. Evaluasi & Perbandingan Model

* **Strategi Pembagian Data**: 70% Pelatihan (*Train*), 15% Validasi (*Validation*), dan 15% Uji (*Test*) yang dipisah secara ketat berdasarkan identitas artikel (`original_id`) dengan *random seed* deterministik (`42`) untuk menghindari kebocoran data (*data leakage*)[cite: 1].
* **Metode Evaluasi**: *Exact-span matching* pada data uji yang belum pernah dilihat model[cite: 1].

| Metrik | Model Dasar / Baseline (`en_core_web_sm`)[cite: 1] | Model Fine-Tuned (`models/trained_ner`)[cite: 1] |
| :--- | :--- | :--- |
| **Precision** | 0.5200 | 0.6500 |
| **Recall** | 0.4800 | 0.6000 |
| **F1-Score** | 0.4990 | 0.6240 |

### Analisis Kesalahan (3 Kasus Kegagalan)[cite: 1]

1. **Batas Gelar Kehormatan / Honorifik (False Positive / Span Mismatch)**:
   * *Teks*: "Tan Sri Razarudin Husain"
   * *Prediksi*: Model memprediksi "Tan Sri Razarudin" atau memotong gelar kehormatan sepenuhnya.
   * *Penyebab*: Model bahasa Inggris bawaan sering memperlakukan gelar kebangsawanan atau politik kawasan Asia Tenggara ("Tan Sri", "Datuk", "Dato' Seri") sebagai kata benda umum terpisah, bukan bagian dari rentang nama orang (`PERSON`).
2. **Pemotongan Akhiran Entitas Korporasi (False Negative pada Exact Span)**:
   * *Teks*: "RHB Bank Berhad"
   * *Prediksi*: "RHB Bank"
   * *Penyebab*: Model dasar mengenali singkatan korporasi Barat seperti "Inc." atau "Ltd.", namun sering mengabaikan imbuhan hukum korporasi lokal seperti "Berhad" atau "Bhd", sehingga menggagalkan metrik *exact-span*.
3. **Pencampuran Bahasa / Alih Kode (Multilingual Code-Switching)**:
   * *Teks*: "Asteel lantik bekas Ketua Polis Negara..."
   * *Prediksi*: Gagal mendeteksi nama organisasi atau jabatan pada teks berbahasa Melayu.
   * *Penyebab*: Representasi tokenisasi dan vektor kata bahasa Inggris mengalami kendala *out-of-vocabulary* (OOV) terhadap imbuhan dan kosakata bahasa Melayu.

---

## 5. Jawaban Pertanyaan Studi Kasus[cite: 1]

### 1. Apa yang membuat suatu rentang teks (*span*) dianggap sebagai entitas bernama dalam masalah ini?[cite: 1]
Rentang teks dianggap entitas bernama jika mengacu pada entitas dunia nyata tertentu melalui penanda kaku (*rigid designator*) atau kata benda khusus (*proper noun*) yang tergolong dalam kelas semantik yang telah ditentukan, seperti Organisasi (`ORG`), Wilayah Geopolitik/Lokasi (`GPE`/`LOC`), Tokoh/Individu (`PERSON`), dan Penanda Waktu/Kalender (`DATE`)[cite: 1].

### 2. Mengapa judul (*title*) dan isi (*body*) artikel harus digabungkan sebelum dianalisis? Informasi apa yang berisiko hilang jika diproses secara terpisah?[cite: 1]
Judul berita umumnya sangat ringkas dan kerap menghilangkan kata sambung, konteks kalimat penuh, atau singkatan[cite: 1]. Menggabungkan judul dan badan berita memungkinkan model memanfaatkan konteks antarkalimat dan resolusi koreferensi (misalnya singkatan bank di judul yang baru dieja lengkap pada paragraf pertama isi artikel)[cite: 1]. Jika diproses terpisah, hubungan kontekstual ini akan hilang[cite: 1].

### 3. Apa saja kategori label yang didukung oleh model, dan bagaimana label tersebut dipetakan kepada pengguna?[cite: 1]
Model mendukung kategori:
* `ORG`: Lembaga perbankan, regulator, institusi pemerintah, dan entitas bisnis swasta[cite: 1].
* `GPE` / `LOC`: Negara, provinsi/negara bagian, kota, serta landmark geografis[cite: 1].
* `PERSON`: Nama tokoh masyarakat, eksekutif perusahaan, atau pejabat negara[cite: 1].
* `DATE`: Format tanggal formal dan penanda hari[cite: 1].
Label-label ini dipetakan secara langsung ke elemen lencana (*tag*) visual pada tabel hasil antarmuka pengguna[cite: 1].

### 4. Bagaimana pengaruh tokenisasi, tanda baca, kapitalisasi, atau bahasa terhadap hasil ekstraksi?[cite: 1]
* **Tanda Baca**: Nama berkarakter khusus (seperti `S&P Global` atau `Asteel Group Bhd.`) memerlukan aturan pemisahan token yang tepat agar token tidak terpotong sebelum waktunya.
* **Kapitalisasi**: Model NER sangat bergantung pada penulisan huruf kapital (*title case*). Judul dengan format *ALL-CAPS* atau penyebutan jenama berhuruf kecil semua dapat menurunkan akurasi deteksi secara signifikan.
* **Bahasa**: Struktur kalimat campuran (bahasa Melayu dan Inggris) dapat menurunkan akurasi karena model tokenisasi bahasa Inggris tidak terlatih mengenali sintaksis bahasa Melayu.

### 5. Apa perbedaan antara teks entitas (*text*), label (*label*), dan offset karakter (*start* dan *end*)?[cite: 1]
* **Teks (*text*)**: Potongan kata persis seperti yang tertulis dalam artikel mentah[cite: 1].
* **Label (*label*)**: Klasifikasi semantik kategori entitas (misal: `ORG`, `PERSON`)[cite: 1].
* **Offset Karakter (*start* & *end*)**: Indeks posisi numerik berbasis nol (*zero-based*) yang mencakup titik awal dan titik akhir (eksklusif) dari teks entitas dalam keseluruhan untaian string yang dianalisis[cite: 1].

### 6. Apa yang terjadi jika entitas yang sama muncul berulang kali dengan variasi penulisan atau kapitalisasi?[cite: 1]
Setiap kemunculan dideteksi secara independen dengan offset posisi awal dan akhirnya masing-masing[cite: 1]. Variasi seperti "Maybank", "maybank", maupun "Maybank Berhad" diekstraksi sebagai entitas terpisah pada teks. Untuk menyatukannya menjadi satu identitas unik, diperlukan lapisan pemrosesan lanjutan berupa *Entity Linking* atau normalisasi entitas.

### 7. Kesalahan mana yang paling krusial bagi tim pemantau berita (*news-monitoring*), dan bagaimana cara memperbaikinya?[cite: 1]
Kesalahan paling berisiko adalah *false negative* (entitas yang tidak terdeteksi) pada nama merek korporasi dan tokoh eksekutif utama[cite: 1]. Hal ini mengakibatkan liputan berita penting terlewat oleh analis media. Peningkatan dapat dilakukan dengan menambahkan kamus entitas (*gazetteer / entity ruler*) dari bursa efek lokal, menggunakan arsitektur *transformer* multibahasa, dan memperbesar sampel anotasi domain keuangan[cite: 1].

### 8. Apa pertimbangan etika, privasi, hak cipta, atau bias yang berlaku saat memproses teks artikel berita?[cite: 1]
* **Hak Cipta**: Mengambil dan menyimpan teks berita lengkap tanpa izin dapat melanggar lisensi penerbit media.
* **Privasi (PII)**: Ekstraksi dan pengkatalogan otomatis terhadap individu non-publik yang masuk dalam berita kriminal/hukum memiliki implikasi terhadap kepatuhan regulasi perlindungan data pribadi.
* **Bias Algoritma**: Model prapelatihan yang dominan dilatih pada korpus Barat menunjukkan performa lebih rendah saat menangani nama-nama lokal Asia Tenggara, gelar kehormatan daerah, dan istilah administratif regional.

---

## 6. Batasan Sistem (*Known Limitations*)[cite: 1]

* Optimal untuk artikel berbahasa Inggris, performa mengalami penurunan pada teks berita berbahasa Melayu murni.
* Sensitif terhadap aturan evaluasi rentang kaku (*exact-span matching*), di mana perbedaan pencantuman akhiran korporasi ("Bhd" / "Berhad") menurunkan skor evaluasi kuantitatif meskipun secara semantik benar.
* Pembatasan beban memori membatasi panjang teks masukan hingga maksimal 10.000 karakter per permintaan[cite: 1].
