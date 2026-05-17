<div align="center">

<img src="https://img.shields.io/badge/WebScan%20Pro-v2.0-00D4FF?style=for-the-badge&logo=shield&logoColor=white" alt="WebScan Pro"/>

# 🔒 WebScan Pro

### Yapay Zeka Destekli Siber Güvenlik & Zafiyet Tarama Aracı
### AI-Powered Cybersecurity & Vulnerability Scanning Tool

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flutter](https://img.shields.io/badge/Flutter-Desktop-02569B?style=flat-square&logo=flutter&logoColor=white)](https://flutter.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![DeepSeek](https://img.shields.io/badge/AI-DeepSeek-7C3AED?style=flat-square&logo=openai&logoColor=white)](https://deepseek.com)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=flat-square)](LICENSE)

<br/>

> **Mezuniyet Projesi** — Bilgi Güvenliği Bölümü | 2025/2026
>
> **Graduation Project** — Information Security Department | 2025/2026

</div>

---

## 📋 İçindekiler / Table of Contents

- [Genel Bakış / Overview](#-genel-bakış--overview)
- [Özellikler / Features](#-özellikler--features)
- [Mimari / Architecture](#-mimari--architecture)
- [Teknoloji Yığını / Tech Stack](#-teknoloji-yığını--tech-stack)
- [Kurulum / Installation](#-kurulum--installation)
- [Kullanım / Usage](#-kullanım--usage)
- [API Endpoints](#-api-endpoints)
- [Güvenlik Modülleri / Security Modules](#-güvenlik-modülleri--security-modules)
- [Ekran Görüntüleri / Screenshots](#-ekran-görüntüleri--screenshots)
- [Etik Uyarı / Ethical Notice](#%EF%B8%8F-etik-uyarı--ethical-notice)
- [Katkı / Contributing](#-katkı--contributing)

---

## 🌐 Genel Bakış / Overview

**WebScan Pro**, ayrıştırılmış Backend/Frontend mimarisi üzerine kurulu gelişmiş bir masaüstü siber güvenlik tarama aracıdır. Web uygulamalarındaki güvenlik açıklarını tespit etmek için güçlü bir Python tarama motorunu modern bir Flutter arayüzüyle birleştirmektedir.

**WebScan Pro** is an advanced desktop cybersecurity tool built on a decoupled Backend/Frontend architecture. It combines a powerful Python scanning engine with a modern Flutter UI to detect web application vulnerabilities, powered by DeepSeek AI for intelligent analysis.

### Neden WebScan Pro? / Why WebScan Pro?

| Sorun / Problem | Çözüm / Solution |
|---|---|
| 💰 Ticari araçlar çok pahalı / Commercial tools too expensive | ✅ Açık kaynak ve ücretsiz / Open source & free |
| 🛡️ WAF sistemleri tarayıcıları engelliyor / WAF blocks scanners | ✅ Gelişmiş WAF atlatma motoru / Advanced WAF evasion |
| 🤖 YZ destekli analiz eksikliği / No AI-powered analysis | ✅ DeepSeek YZ entegrasyonu / DeepSeek AI integration |
| 🌐 Türkçe dil desteği yok / No Turkish language support | ✅ Tam TR/EN çift dil / Full TR/EN bilingual |

---

## ✨ Özellikler / Features

### 🔍 Güvenlik Tarama / Security Scanning
- **Pasif Tarama** — SSL/TLS, güvenlik başlıkları, çerez bayrakları, bilgi ifşası
- **Aktif Tarama** — SQL Enjeksiyonu (50+ yük), XSS, Dizin Geçişi
- **Çok Sinyalli Tespit** — Hata tabanlı, kör ve zaman tabanlı tespit

### 🛡️ WAF Atlatma / WAF Evasion
- **9 WAF türü tespiti** — Cloudflare, Akamai, AWS WAF, ModSecurity, Imperva, F5, Sucuri, Barracuda, Wordfence
- **İnsan benzeri davranış** — Rastgele gecikmeler ve User-Agent rotasyonu
- **Çok katmanlı yük kodlama** — URL, Çift-URL, HTML, Karma büyük-küçük harf

### 🤖 Yapay Zeka Analizi / AI Analysis
- **DeepSeek API** entegrasyonu ile önem skorlaması
- **Kod düzeyinde düzeltme önerileri** — Her açık için spesifik çözüm
- **Türkçe & İngilizce** yönetici özeti oluşturma

### 📄 Profesyonel Raporlar / Professional Reports
- **PDF rapor** oluşturma — TR/EN çift dil desteği
- **Renkli şiddet rozetleri** — Kritik, Yüksek, Orta, Düşük
- **DejaVuSans fontları** — Türkçe & Unicode karakter desteği

### 📊 Kontrol Paneli / Dashboard
- **Gerçek zamanlı istatistikler** — Toplam tarama, açık sayısı
- **Etkileşimli grafikler** — Pasta grafik ve 30 günlük trend
- **Tarama geçmişi** — SQLite ile yerel depolama

---

## 🏗️ Mimari / Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FLUTTER FRONTEND                      │
│  Dashboard │ New Scan │ Results │ History │ Settings     │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP (localhost:8000)
                           │ FastAPI Bridge
┌──────────────────────────┴──────────────────────────────┐
│                    PYTHON BACKEND                        │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   Passive   │  │   Active    │  │  WAF Evasion    │  │
│  │   Scanner   │  │   Scanner   │  │    Engine       │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  DeepSeek   │  │    PDF      │  │    SQLite       │  │
│  │  AI Client  │  │  Generator  │  │  + Alembic      │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Teknoloji Yığını / Tech Stack

| Katman / Layer | Teknoloji / Technology | Açıklama / Description |
|---|---|---|
| **Ön Yüzey** | Flutter + Dart | Masaüstü UI, etkileşimli grafikler, TR/EN i18n |
| **Arka Yüzey** | Python 3.11+ | Tarama motoru, siber güvenlik mantığı |
| **API Köprüsü** | FastAPI | Async localhost köprüsü (port 8000) |
| **HTTP İstemcisi** | httpx + Requests | Async istekler, çerez yönetimi |
| **YZ Motoru** | DeepSeek API | Zafiyet analizi ve düzeltme önerileri |
| **Veritabanı** | SQLite + Alembic | Şema sürümleme, async desteği (aiosqlite) |
| **PDF Raporları** | ReportLab | TR/EN profesyonel raporlar, Unicode font |
| **WAF Atlatma** | Özel Motor | UA rotasyonu, yük kodlama, WAF tespiti |

---

## 🚀 Kurulum / Installation

### Gereksinimler / Prerequisites

```bash
# Python 3.11+
python --version

# Flutter 3.x+
flutter --version

# Git
git --version
```

### 1. Depoyu Klonlayın / Clone Repository

```bash
git clone https://github.com/kullanici-adi/webscan-pro.git
cd webscan-pro
```

### 2. Backend Kurulumu / Backend Setup

```bash
cd backend

# Sanal ortam oluşturun / Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükleyin / Install dependencies
pip install -r requirements.txt

# Ortam değişkenlerini ayarlayın / Setup environment
cp .env.example .env
# .env dosyasını düzenleyin / Edit .env file
```

### 3. `.env` Dosyasını Yapılandırın / Configure `.env`

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-chat
DATABASE_URL=sqlite+aiosqlite:///./webscanpro.db
API_HOST=127.0.0.1
API_PORT=8000
SCAN_TIMEOUT=15
MAX_RETRIES=3
```

> ⚠️ **Önemli / Important:** `.env` dosyasını asla Git'e yüklemeyin! / Never commit `.env` to Git!

### 4. Font Dosyalarını Yükleyin / Install Font Files

```bash
# DejaVuSans fontlarını backend/assets/fonts/ klasörüne kopyalayın
# Copy DejaVuSans fonts to backend/assets/fonts/ folder

mkdir -p backend/assets/fonts

# Font indirme / Download fonts
python -c "
import urllib.request
urllib.request.urlretrieve(
    'https://raw.githubusercontent.com/matplotlib/matplotlib/main/lib/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf',
    'backend/assets/fonts/DejaVuSans.ttf'
)
urllib.request.urlretrieve(
    'https://raw.githubusercontent.com/matplotlib/matplotlib/main/lib/matplotlib/mpl-data/fonts/ttf/DejaVuSans-Bold.ttf',
    'backend/assets/fonts/DejaVuSans-Bold.ttf'
)
print('Fontlar indirildi / Fonts downloaded')
"
```

### 5. Veritabanı Migration / Database Migration

```bash
cd backend
alembic upgrade head
```

### 6. Frontend Kurulumu / Frontend Setup

```bash
cd frontend
flutter pub get
```

---

## 💻 Kullanım / Usage

### Backend'i Başlatın / Start Backend

```bash
cd backend
python main.py
# Sunucu başlıyor / Server starting at http://127.0.0.1:8000
```

### Frontend'i Başlatın / Start Frontend

```bash
cd frontend
flutter run -d windows   # Windows
flutter run -d macos     # macOS
flutter run -d linux     # Linux
```

### İlk Çalıştırma Kontrol Listesi / First Run Checklist

```
✅ .env dosyası yapılandırıldı / .env file configured
✅ DeepSeek API anahtarı eklendi / DeepSeek API key added
✅ alembic upgrade head çalıştırıldı / alembic upgrade head executed
✅ DejaVuSans.ttf fontları mevcut / DejaVuSans.ttf fonts present
✅ python main.py çalışıyor / python main.py running
✅ flutter run başarılı / flutter run successful
✅ Ayarlar → Backend Durumu: Çevrimiçi / Settings → Backend Status: Online
```

---

## 📡 API Endpoints

| Metot / Method | Endpoint | Açıklama / Description |
|---|---|---|
| `GET` | `/health` | Backend durum kontrolü / Backend health check |
| `POST` | `/scan/start` | Yeni tarama başlat / Start new scan |
| `GET` | `/scan/status/{id}` | Tarama ilerlemesi / Scan progress (0-100%) |
| `GET` | `/scan/results/{id}` | Tarama sonuçları / Full scan results |
| `GET` | `/history` | Son 20 tarama / Last 20 scan sessions |
| `GET` | `/report/pdf/{id}` | PDF rapor indir / Download PDF report |
| `POST` | `/settings/update` | Çalışma zamanı ayarları / Runtime settings |
| `GET` | `/settings/current` | Mevcut ayarlar / Current settings |

### Örnek İstek / Example Request

```bash
# Tarama başlat / Start scan
curl -X POST http://127.0.0.1:8000/scan/start \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com", "language": "tr"}'

# Sonuç / Response
{
  "session_id": "abc123-...",
  "status": "started"
}
```

---

## 🔒 Güvenlik Modülleri / Security Modules

### 01 — Pasif Tarayıcı / Passive Scanner
```
✓ SSL/TLS sertifika geçerliliği ve son kullanma tarihi
✓ Güvenlik Başlıkları: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
✓ Çerez bayrakları: HttpOnly, Secure, SameSite
✓ Bilgi ifşası: robots.txt, .env, .git, /admin yolları
```

### 02 — Aktif Tarayıcı / Active Scanner
```
✓ SQL Enjeksiyonu — 14 yük, hata tabanlı + kör + zaman tabanlı
✓ XSS — Yansıtmalı & Depolanmış, 10 yük, DOM & öznitelik bağlamı
✓ Dizin Geçişi — 9 yük, çok sinyalli tespit (2/3 sinyal gerekli)
```

### 03 — WAF Atlatma Motoru / WAF Evasion Engine
```
✓ Otomatik WAF tespiti: Cloudflare, Akamai, AWS WAF, ModSecurity...
✓ Güven skoru sistemi (0.0 → 1.0)
✓ User-Agent rotasyonu — 8+ gerçek tarayıcı parmak izi
✓ İnsan benzeri gecikme titremesi (1.5s → 4.0s)
✓ Çok katmanlı yük kodlama: URL, Çift-URL, HTML, Karma
✓ Oturum ısınması — Aktif taramadan önce çerez toplama
```

### 04 — DeepSeek YZ Analizi / AI Analysis
```
✓ Önem skorlaması: Kritik / Yüksek / Orta / Düşük
✓ Her açık için teknik açıklama ve saldırı senaryosu
✓ Kod düzeyinde düzeltme önerileri
✓ TR & EN yönetici özeti
✓ YZ başarısız olursa yedek hesaplama

Skor Formülü / Scoring Formula:
  Başlangıç: 100 puan
  Kritik açık: −25 puan
  Yüksek açık: −15 puan
  Orta açık:   −8 puan
  Düşük açık:  −3 puan
  Minimum:      0 puan
```

### 05 — PDF Rapor Üreticisi / PDF Report Generator
```
✓ Kapak sayfası — güvenlik skoru ve risk seviyesi
✓ Yönetici özeti (DeepSeek tarafından oluşturulur)
✓ Renkli şiddet rozetleri içeren zafiyet tablosu
✓ Kritik/Yüksek açıklar için detaylı bölümler
✓ Tam TR/EN yerelleştirme
✓ Türkçe & Unicode için DejaVuSans fontları
```

---

## 📁 Proje Yapısı / Project Structure

```
webscan-pro/
├── backend/
│   ├── main.py                  # FastAPI giriş noktası / entry point
│   ├── config.py                # Pydantic ayarları / settings
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic/                 # DB migration dosyaları
│   ├── database/
│   │   ├── models.py            # ScanSession + Vulnerability modelleri
│   │   └── crud.py              # Async CRUD işlemleri
│   ├── scanners/
│   │   ├── passive_scanner.py   # SSL, Başlıklar, Çerezler
│   │   └── active_scanner.py    # SQLi, XSS, Dizin Geçişi
│   ├── ai/
│   │   └── deepseek_client.py   # DeepSeek API entegrasyonu
│   ├── reports/
│   │   └── pdf_generator.py     # ReportLab PDF üretici
│   ├── utils/
│   │   ├── stealth.py           # WAF Atlatma motoru
│   │   └── waf_detector.py      # WAF tespiti
│   └── assets/
│       └── fonts/
│           ├── DejaVuSans.ttf
│           └── DejaVuSans-Bold.ttf
└── frontend/
    ├── pubspec.yaml
    └── lib/
        ├── main.dart
        ├── l10n/
        │   ├── app_tr.arb       # Türkçe dizeler
        │   └── app_en.arb       # İngilizce dizeler
        ├── core/
        │   ├── api_client.dart
        │   └── constants.dart
        ├── screens/
        │   ├── main_dashboard.dart
        │   ├── dashboard_overview.dart
        │   ├── scan_screen.dart
        │   ├── results_screen.dart
        │   ├── history_screen.dart
        │   └── settings_screen.dart
        └── widgets/
            ├── score_gauge.dart
            └── vulnerability_card.dart
```

---

## 🎨 Renk Sistemi / Color System

```
Background:    #0D1117  ████  Uygulama arka planı
Card:          #1A2130  ████  Kartlar ve konteynerler
Accent Cyan:   #00D4FF  ████  Bölüm başlıkları, vurgular
Accent Blue:   #3B82F6  ████  Ana buton, Orta severity
Critical:      #EF4444  ████  Kritik severity rozeti
High:          #F59E0B  ████  Yüksek severity rozeti
Medium:        #3B82F6  ████  Orta severity rozeti
Low:           #22C55E  ████  Düşük severity rozeti
```

---

## ⚙️ Ayarlar / Settings

Uygulama içinden çalışma zamanında değiştirilebilir / Configurable at runtime via the app:

| Ayar / Setting | Varsayılan / Default | Açıklama / Description |
|---|---|---|
| `deepseek_api_key` | — | DeepSeek API anahtarı |
| `deepseek_model` | `deepseek-chat` | Kullanılacak YZ modeli |
| `scan_timeout` | `15s` | İstek zaman aşımı (5-30s) |
| `max_retries` | `3` | Maksimum yeniden deneme |
| `waf_evasion` | `true` | WAF atlatma modu |
| `stealth_mode` | `true` | Gizli tarama modu |

---

## 🖼️ Ekran Görüntüleri / Screenshots

> Ekran görüntüleri için `screenshots/` klasörüne bakın.
> See `screenshots/` folder for screenshots.

| Dashboard | Tarama Sonuçları | PDF Rapor |
|---|---|---|
| Gerçek zamanlı istatistikler | Güvenlik skoru göstergesi | Profesyonel TR/EN rapor |

---

## ⚠️ Etik Uyarı / Ethical Notice

> **🇹🇷 Türkçe:** WebScan Pro yalnızca **açık yetkilendirmeye sahip olduğunuz sistemlerde** kullanılmalıdır. Yetkisiz tarama yasadışıdır ve etik değildir. Bu araç yalnızca güvenlik araştırması, eğitim ve yetkili penetrasyon testi amacıyla geliştirilmiştir.

> **🇬🇧 English:** WebScan Pro must only be used on systems **you own or have explicit written permission** to test. Unauthorized scanning is illegal and unethical. This tool is developed solely for security research, education, and authorized penetration testing.

**Test ortamları / Test environments:**
- `http://testfire.net` — IBM test sitesi
- `http://testasp.vulnweb.com` — ASP.NET test sitesi
- `http://testphp.vulnweb.com` — PHP test sitesi

---

## 📦 Gereksinimler / Requirements

### Backend (`requirements.txt`)
```
fastapi==0.111.0
uvicorn[standard]==0.30.1
httpx==0.27.0
requests==2.32.3
beautifulsoup4==4.12.3
sqlalchemy==2.0.30
aiosqlite==0.20.0
alembic==1.13.1
reportlab==4.2.0
arabic-reshaper==3.0.0
python-bidi==0.4.2
python-dotenv==1.0.1
pydantic==2.7.1
pydantic-settings==2.3.0
fake-useragent==1.5.1
openai==1.30.1
```

### Frontend (`pubspec.yaml`)
```yaml
dependencies:
  flutter_localizations:
    sdk: flutter
  http: ^1.2.1
  fl_chart: ^0.67.0
  provider: ^6.1.2
  shared_preferences: ^2.2.3
  intl: ^0.19.0
  google_fonts: ^6.2.1
```

---

## 🤝 Katkı / Contributing

1. Fork yapın / Fork the repository
2. Feature branch oluşturun / Create feature branch (`git checkout -b feature/YeniOzellik`)
3. Değişikliklerinizi commit edin / Commit changes (`git commit -m 'feat: YeniOzellik eklendi'`)
4. Branch'i push edin / Push branch (`git push origin feature/YeniOzellik`)
5. Pull Request açın / Open Pull Request

---

## 📄 Lisans / License

Bu proje MIT Lisansı altında lisanslanmıştır.
This project is licensed under the MIT License.

---

<div align="center">

**WebScan Pro v2.0**

Yapay Zeka Destekli Siber Güvenlik & Zafiyet Tarama Aracı


</div>
