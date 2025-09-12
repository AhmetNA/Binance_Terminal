# CI/CD Test Rehberi

Bu proje için GitHub Actions CI/CD pipeline'ı kurulmuştur ve kapsamlı test sistemi eklenmiştir.

## 🔧 Test Yapısı

### 1. Smoke Tests (`test_smoke.py`)

- **Amaç**: Temel sistem bütünlüğünü kontrol eder
- **İçerik**:
  - Proje yapısı kontrolü
  - Temel import işlemleri
  - Requirements dosyası validasyonu
  - Konfigürasyon dosyalarının varlığı
- **Kritiklik**: ⚠️ KRITIK - Bu testler başarısız olursa CI/CD fail olur

### 2. Unit Tests

- **Trade Execution Tests** (`test_trade_execution.py`): Trade işlemlerinin simülasyonu
- **Client Service Tests** (`test_client_service.py`): API client bağlantı testleri
- **Data Management Tests** (`test_data_management.py`): Veri kaydetme/yükleme testleri
- **Order Service Tests** (`test_order_service.py`): Emir verme sistemi testleri

### 3. Integration Tests

- **End-to-End Tests** (`test_end_to_end.py`): Tam süreç testleri
- **Multi-trade Scenarios**: Çoklu işlem senaryoları
- **Error Recovery**: Hata durumu testleri

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow (`.github/workflows/ci.yml`)

Pipeline şu adımları içerir:

1. **Environment Setup**

   - Python 3.8, 3.9, 3.10, 3.11 sürümleri test edilir
   - Dependencies cache'lenir
   - Requirements yüklenir

2. **Code Quality Checks**

   - **Flake8**: Kritik syntax hataları kontrol edilir (E9, F63, F7, F82)
   - **Black**: Code formatting kontrolü (non-blocking)
   - **MyPy**: Type checking (non-blocking)

3. **Testing**

   - **Smoke Tests**: Kritik sistem testleri (MUST PASS)
   - **All Tests**: Tüm testler çalıştırılır (failures allowed for now)
   - **Coverage**: Code coverage raporu oluşturulur

4. **Build Test** (sadece main branch push'larında)
   - Package build testi
   - Installation doğrulaması

## 📊 Test Coverage

Mevcut coverage: ~11% (başlangıç seviyesi)

Test coverage artırmak için:

```bash
pytest tests/ --cov=src --cov-report=html
```

HTML coverage raporu `htmlcov/` klasöründe oluşturulur.

## 🔄 Local Test Çalıştırma

### Tüm testleri çalıştırma:

```bash
pytest tests/ -v
```

### Sadece smoke testler:

```bash
pytest tests/test_smoke.py -v
```

### Coverage ile:

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

### Specific test dosyası:

```bash
pytest tests/unit/test_trade_execution.py -v
```

## 🛠️ Code Quality Tools

### Linting:

```bash
flake8 src --count --select=E9,F63,F7,F82 --show-source --statistics
```

### Formatting:

```bash
black src/
```

### Type Checking:

```bash
mypy src/ --ignore-missing-imports
```

## 📈 CI/CD İyileştirme Planı

### Kısa Vadeli (1-2 hafta):

- [ ] Mevcut test failures'ları düzelt
- [ ] Mock'ları iyileştir
- [ ] Test coverage'ı %30'a çıkar

### Orta Vadeli (1 ay):

- [ ] Integration testlerini genişlet
- [ ] Performance testleri ekle
- [ ] Test coverage'ı %60'a çıkar

### Uzun Vadeli (2-3 ay):

- [ ] E2E testler ekle
- [ ] Security testleri
- [ ] Load testing
- [ ] Test coverage'ı %80+'a çıkar

## 🔒 API Key Güvenliği

Testler için gerçek API key'leri kullanılmaz. Tüm external API çağrıları mock'lanır.

Production ortamında API key'leri environment variables olarak ayarlanmalı:

```bash
export BINANCE_API_KEY="your_api_key"
export BINANCE_SECRET_KEY="your_secret_key"
```

## 🐛 Test Debugging

### Test failed durumunda:

1. Log dosyalarını kontrol et
2. Mock ayarlarını gözden geçir
3. Import path'lerini kontrol et
4. Environment variables'ları doğrula

### Common Issues:

- Import errors: `sys.path` ayarlarını kontrol et
- Mock failures: Mock return values'ları doğrula
- API key errors: Test ortamında mock kullanıldığından emin ol

## 📝 Test Yazma Rehberi

### Yeni test dosyası oluştururken:

1. `tests/unit/` veya `tests/integration/` klasörüne ekle
2. `test_` prefix'i kullan
3. `conftest.py`'daki fixture'ları kullan
4. Mock'ları doğru şekilde ayarla

### Test naming convention:

- `test_function_name_scenario`
- Örnek: `test_place_buy_order_success`

### Test structure:

```python
def test_something(self):
    # Arrange
    setup_test_data()

    # Act
    result = function_under_test()

    # Assert
    self.assertEqual(expected, result)
```

## 🎯 Success Criteria

CI/CD'nin başarılı olması için:

- ✅ Smoke tests geçmeli
- ✅ Critical linting errors olmamalı
- ✅ Build işlemi başarılı olmalı
- ⚠️ Unit testlerin bazıları fail olabilir (geçici)

---

Bu CI/CD sistemi projenizin kod kalitesini ve güvenilirliğini artıracak. Her GitHub push'ında otomatik olarak çalışacak ve sorunları erken aşamada yakalayacaktır.
