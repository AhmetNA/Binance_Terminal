# Paths Modülü - Centralized Path Management

Bu modül, Binance Terminal uygulamasında kullanılan tüm dosya ve dizin yollarını merkezi olarak yöneten path sistemidir.

## 🎯 Amaç

Daha önce her dosyada ayrı ayrı tanımlanan path'leri tek bir yerde toplamak ve:

- ✅ **Organizasyon**: Tüm path'ler tek yerde
- ✅ **Bakım kolaylığı**: Path değişiklikleri tek yerden
- ✅ **Tutarlılık**: Aynı path'ler her yerde aynı
- ✅ **PyInstaller uyumluluğu**: Bundle desteği
- ✅ **Platform bağımsızlığı**: Windows/Linux/Mac uyumlu

## 📁 Modül Yapısı

```
src/core/paths.py   # ← Yeni merkezi path modülü
```

## 🔧 Kullanım

### Temel Import

```python
# Temel path'leri import et
from core.paths import PREFERENCES_FILE, SETTINGS_DIR, PROJECT_ROOT

# Kullan
with open(PREFERENCES_FILE, 'r') as f:
    content = f.read()
```

### Tüm Path'leri Import Etme

```python
from core.paths import (
    # Base directories
    PROJECT_ROOT, SRC_DIR, CURRENT_DIR,

    # Configuration
    SETTINGS_DIR, CONFIG_DIR,

    # Data directories
    DATA_DIR, TRADES_DIR, PORTFOLIO_DIR, ANALYTICS_DIR,

    # Configuration files
    PREFERENCES_FILE, FAV_COINS_FILE, ENV_FILE,

    # Helper functions
    get_daily_trades_file, ensure_directories
)
```

### Helper Fonksiyonları

```python
from core.paths import get_daily_trades_file, get_daily_portfolio_file

# Bugünün trades dosyası
today_trades = get_daily_trades_file()

# Belirli bir tarih için
specific_date_trades = get_daily_trades_file("2025-08-22")
```

## 📋 Mevcut Path'ler

### Base Directories

- `PROJECT_ROOT`: Proje kök dizini
- `SRC_DIR`: src/ dizini
- `CURRENT_DIR`: core/ dizini

### Configuration

- `SETTINGS_DIR`: config/ dizini
- `PREFERENCES_FILE`: Preferences.txt dosyası
- `FAV_COINS_FILE`: fav_coins.json dosyası
- `ENV_FILE`: .env dosyası

### Data Directories

- `DATA_DIR`: data/ dizini
- `TRADES_DIR`: data/trades/ dizini
- `PORTFOLIO_DIR`: data/portfolio/ dizini
- `ANALYTICS_DIR`: data/analytics/ dizini

### Log Files

- `LOGS_DIR`: logs/ dizini
- `MAIN_LOG_FILE`: ana log dosyası
- `DEBUG_LOG_FILE`: debug log dosyası

### Assets

- `ASSETS_DIR`: assets/ dizini
- `BTC_ICON_FILE`: btc.png icon dosyası

## 🔄 Migration Guide

### Önceki Kod (❌ Eski Yöntem)

```python
# order_service.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
SETTINGS_DIR = os.path.join(PROJECT_ROOT, 'config')
PREFERENCES_FILE = os.path.join(SETTINGS_DIR, 'Preferences.txt')
```

### Yeni Kod (✅ Yeni Yöntem)

```python
# order_service.py
from core.paths import PREFERENCES_FILE, SETTINGS_DIR, PROJECT_ROOT
```

## 🚀 Faydalar

### 1. **Kod Tekrarını Önler**

```python
# Önceden her dosyada:
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Şimdi tek satır:
from core.paths import PROJECT_ROOT
```

### 2. **Merkezi Bakım**

```python
# Sadece paths.py'da değiştir, her yerde otomatik güncellenir
SETTINGS_DIR = get_settings_dir()  # PyInstaller logic burada
```

### 3. **Type Safety**

```python
# Helper fonksiyonlarla güvenli path oluşturma
trades_file = get_daily_trades_file("2025-08-22")  # ✅ Güvenli
# trades_file = f"trades_{date}.json"  # ❌ Hata riski
```

### 4. **Automatic Directory Creation**

```python
# Uygulama başlarken otomatik olarak gerekli dizinler oluşturulur
ensure_directories()  # Tüm dizinleri oluştur
```

## 🧪 Test Etme

Test script'i çalıştırarak doğru çalışıp çalışmadığını kontrol edin:

```bash
python test_paths.py
```

## 🔧 Helper Fonksiyonları

### Dated Files

```python
from core.paths import get_daily_trades_file, get_daily_portfolio_file

# Bugünün dosyaları
today_trades = get_daily_trades_file()  # trades_2025-08-22.json
today_portfolio = get_daily_portfolio_file()  # portfolio_2025-08-22.json

# Belirli tarih
specific_trades = get_daily_trades_file("2025-08-20")
```

### Path Validation

```python
from core.paths import validate_paths, get_path_info

# Tüm critical path'leri doğrula
is_valid = validate_paths()

# Detaylı path bilgisi
path_info = get_path_info()
print(path_info)
```

### Directory Management

```python
from core.paths import ensure_directories

# Tüm gerekli dizinleri oluştur
ensure_directories()
```

## 📚 Backwards Compatibility

Eski sabitler hala kullanılabilir:

```python
from core.paths import (
    FAVORITE_COIN_COUNT,  # 5
    DYNAMIC_COIN_INDEX,   # 6
    USDT,                 # "USDT"
    TICKER_SUFFIX,        # "@ticker"
    RECONNECT_DELAY,      # 5
    COINS_KEY,            # "coins"
    DYNAMIC_COIN_KEY      # "dynamic_coin"
)
```

## 🎯 Kullanım Örnekleri

### Order Service

```python
# Önceki kod
# PREFERENCES_FILE = os.path.join(SETTINGS_DIR, 'Preferences.txt')

# Yeni kod
from core.paths import PREFERENCES_FILE

def _load_preferences_once():
    with open(PREFERENCES_FILE, "r") as file:
        # ... preferences okuma logic
```

### Data Manager

```python
# Önceki kod
# self.trades_dir = os.path.join(self.project_root, 'data', 'trades')

# Yeni kod
from core.paths import TRADES_DIR, get_daily_trades_file

def save_trade(self, trade_data):
    trades_file = get_daily_trades_file()
    # ... save logic
```

### Main Window

```python
# Önceki kod
# icon_path = os.path.join(current_dir, '..', '..', 'assets', 'btc.png')

# Yeni kod
from core.paths import BTC_ICON_FILE

def setup_application_icon(self):
    if os.path.exists(BTC_ICON_FILE):
        self.setWindowIcon(QIcon(BTC_ICON_FILE))
```

## 🏗️ Gelecek Geliştirmeler

- [ ] **Config validation**: Automatically validate config file formats
- [ ] **Path watching**: Auto-reload when files change
- [ ] **Network paths**: Support for network drives
- [ ] **Docker support**: Container-friendly paths
- [ ] **Backup paths**: Automatic backup location management

## ⚠️ Önemli Notlar

1. **Import Order**: paths modülü diğer core modüllerden önce import edilmelidir
2. **PyInstaller**: Bundle modunda otomatik olarak executable dizini kullanılır
3. **Directory Creation**: İlk import'ta otomatik olarak gerekli dizinler oluşturulur
4. **Error Handling**: Path validation hatalarında warning verilir ama uygulama durmuyor

Bu modül sayesinde tüm path yönetimi merkezi, güvenli ve bakım dostu hale gelmiştir! 🎉
