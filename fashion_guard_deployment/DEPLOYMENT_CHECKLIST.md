#  Fashion Guard RunPod Deployment - Complete Checklist

##  TAMAMLANAN HAZIRLIKLAR

### **Konfigürasyon Dosyaları**
- [x] `requirements.txt` - runpod paketini ekledi
- [x] `config.yaml` - Model konfigürasyonu
- [x] `Dockerfile` - Container imajı (fashion_guard_deployment klasöründe)
- [x] `.dockerignore` - Build sırasında hariç tutulacak dosyalar

### **Handler & Entry Points**
- [x] `runpod_handler.py` - Import paths düzeltildi
- [x] `runpod_handler.py` - RunPod serverless entrypoint eklendi
- [x] `runpod_handler.py` - Local testing modu korundu

### **Root Dockerfile**
- [x] `runpod_Dockerfile` - Paths düzeltildi
- [x] `runpod_Dockerfile` - Unbuffered output (-u flag)
- [x] `runpod_Dockerfile` - Cache directory oluşturma

### **Dokumentasyon**
- [x] `README.md` - Genel başlangıç rehberi
- [x] `RUNPOD_DEPLOYMENT_GUIDE.md` - Detaylı adım adım kılavuz
- [x] `API_REFERENCE.md` - API belgeleri & kod örnekleri
- [x] `RUNPOD_DEPLOYMENT_CHECKLIST.md` - Bu dosya

### **Otomasyon**
- [x] `deploy.sh` - Automated build & push script

---

##  DEPLOYMENT ADIMLAR

### **ADIM 1: Deployment Script'i Çalıştırın** 
```bash
cd /Users/burak.yilmaz/apprel_guard/fashion_guard_deployment
chmod +x deploy.sh
./deploy.sh
```

Script yapacakları:
-  Docker image build et: `fashion-guard:v1`
-  Docker Hub'a push et
-  Konfigürasyon dosyası kaydet

---

### **ADIM 2: RunPod Konsolunda Deploy Et**

**2.1 RunPod'a Git**
```
https://www.runpod.io/console/serverless
```

**2.2 "Create an endpoint" Tıkla**
- Veya: "+ New Endpoint"

**2.3 "Deploy from a Docker image" Seç**

**2.4 Formu Doldur:**

| Alan | Değer | Zorunlu? |
|------|-------|----------|
| Endpoint Name | `fashion-guard-inference` |  Opsiyonel |
| Container Image | `your-username/fashion-guard:v1` |  ZORUNLU |
| Container Registry | `Public` |  ZORUNLU |
| GPU | 16GB (A4000) **veya** 24GB (RTX 4090) |  ZORUNLU |
| Min Workers | `0` |  ZORUNLU  |
| Max Workers | `1` veya `2` |  ZORUNLU |
| Execution Timeout | `60` |  ZORUNLU |

** ÖNEMLI NOTLAR:**
- Min Workers = **0** = Idle ücret **$0**
- GPU = **16 GB** en azı (Qwen3-4B için yeterli)
- Timeout = **60 saniye** model inference'ı için

**2.5 (Opsiyonel) Environment Variables Ekle**
```
MODEL_NAME=Qwen/Qwen3-4B-Instruct-2507
ACCELERATOR=auto
QUANTIZATION=none
HF_HUB_ENABLE_HF_TRANSFER=0
TRANSFORMERS_CACHE=/app/.cache/huggingface
```

**2.6 "Deploy Endpoint" Tıkla**
- Deployment 2-5 dakika sürer
- Durumu "ACTIVE" olunca devam et

---

### **ADIM 3: Endpoint ID'ni Kopyala**

Deployment tamamlandığında:
```
https://api.runpod.io/v2/{ENDPOINT_ID}/runsync
                          ↑
                    Bunu kopyala
```

Ayrıca **API Key** de ihtiyaç:
- RunPod Console → Settings (⚙️) → API Keys → Copy

---

### **ADIM 4: Test İsteği Gönder**

```bash
# Değişkenleri set et
ENDPOINT_ID="your-endpoint-id"
API_KEY="your-runpod-api-key"

# Test isteği gönder
curl -X POST "https://api.runpod.io/v2/${ENDPOINT_ID}/runsync" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "query": "Bana 2000 TL altı kırmızı abiye önerir misin?",
      "session_language": "tr-TR"
    }
  }' | jq
```

**Beklenen Başarı Response:**
```json
{
  "delayTime": 245,
  "executionTime": 350,
  "output": {
    "status": "success",
    "query": "Bana 2000 TL altı kırmızı abiye önerir misin?",
    "intent": "product_search",
    "language": "tr",
    "route": "SEARCH",
    "latency_ms": 325.45
  }
}
```

 **"route": "SEARCH"** = Her şey düzgün çalışıyor!

---

##  PRE-DEPLOYMENT KONTROL LİSTESİ

Deployment'tan ÖNCE:

- [ ] Docker yüklü: `docker --version`
- [ ] Docker çalışıyor: `docker info`
- [ ] Docker Hub hesabı hazır ve login olmuş
- [ ] RunPod hesabı hazır
- [ ] RunPod API Key kopyalandı
- [ ] Internet bağlantısı stabil
- [ ] En az 10 GB disk alanı boş (model download için)

---

##  TEST SENARYOLARI

Test etmek için API Reference'da örnekler var: [API_REFERENCE.md](API_REFERENCE.md)

### **Test 1: Turkish Product Search** 
```json
{
  "input": {
    "query": "Siyah bot arıyorum",
    "session_language": "tr-TR"
  }
}
```
**Beklenen Route:** SEARCH

### **Test 2: English Product Search** 
```json
{
  "input": {
    "query": "Blue dress under 100 euros",
    "session_language": "en-GB"
  }
}
```
**Beklenen Route:** SEARCH

### **Test 3: Vague Query (Needs Clarification)** 
```json
{
  "input": {
    "query": "Çanta arıyorum",
    "session_language": "tr-TR"
  }
}
```
**Beklenen Route:** NEEDS_MORE_DETAIL

### **Test 4: Out of Scope** 
```json
{
  "input": {
    "query": "Dünyanın en uzun nehri hangisidir?",
    "session_language": "tr-TR"
  }
}
```
**Beklenen Route:** REJECT

---

##  HATA AYIKLAMA

### **Hata: "Image not found"**
```
Çözüm:
1. Docker Hub'da username'i kontrol et
2. Image'ın public olduğundan emin ol
3. Full URL'yi kontrol et: your-username/fashion-guard:v1
```

### **Hata: "Pod not available"**
```
Çözüm:
1. Min Workers = 0 ise, GPU başlatılıyor (1-2 dk)
2. RunPod Dashboard > Logs'u kontrol et
3. 2 dakika sonra tekrar dene
```

### **Hata: "401 Unauthorized"**
```
Çözüm:
1. RunPod API Key'i kontrol et
2. Settings > API Keys'te yeni key oluştur
3. Authorization header'ı kontrol et
```

### **Hata: "500 Internal Server Error"**
```
Çözüm:
1. RunPod Logs'u kontrol et (Dashboard)
2. Model indir hatası mı?
3. GPU memory yetersiz mi?
   → GPU'yu 24GB'a upgrade et
```

---

##  PERFORMANCE BEKLENTILERI

| Metrik | Değer | Not |
|--------|-------|-----|
| **Cold Start** | 10-15 saniye | İlk istek, model loading |
| **Warm Latency** | 0.3-0.5 saniye | Sonraki istekler |
| **Inference Time** | 200-400ms | Model çalışma süresi |
| **Total Response Time** | 250-500ms | Network + inference |
| **GPU Idle Cost** | $0.00 | Min Workers=0 |
| **GPU Active Cost** | ~$0.46/saat | RTX 4090 örneği |

---

## 🔄 MODEL GÜNCELLEMESI

Yeni model versiyonu deploy etmek için:

```bash
# 1. Dosyaları güncelle
nano config.yaml
nano runpod_handler.py

# 2. Yeni image build et
docker build -f Dockerfile -t your-username/fashion-guard:v2 .

# 3. Push et
docker push your-username/fashion-guard:v2

# 4. RunPod'da güncelleştir
# Dashboard > Endpoint > Edit > New Image URL
# your-username/fashion-guard:v2
```

---

##  KAYNAKLAR

-  [RUNPOD_DEPLOYMENT_GUIDE.md](RUNPOD_DEPLOYMENT_GUIDE.md) - Detaylı rehber
- 🔌 [API_REFERENCE.md](API_REFERENCE.md) - API dokumentasyonu
- 📁 [README.md](README.md) - Genel başlangıç
- 🐳 [Dockerfile](Dockerfile) - Container tanımı
- 🔧 [config.yaml](config.yaml) - Model konfigürasyonu

---

##  COMPLETION CHECKLIST

Deployment tamamlandıktan sonra:

- [ ] Endpoint deployed ve ACTIVE durumda
- [ ] ENDPOINT_ID kaydedildi
- [ ] API KEY kaydedildi
- [ ] Test isteği başarılı (response alındı)
- [ ] Latency 0.3-0.5 saniye aralığında
- [ ] En az 4 test senaryo çalıştırıldı
- [ ] Logs kontrol edildi ve hata yok
- [ ] Kurumumuz/client'ımız integration'ı hazırladı
- [ ] Production kullanıma başlandı 

---

##  PRODUCTION BEST PRACTICES

1. **Min Workers:**
   - Development: 0
   - Production: 1

2. **Max Workers:**
   - Hafif traffic: 1-2
   - Orta traffic: 3-5
   - Yüksek traffic: 5+

3. **Monitoring:**
   - Günlük logs kontrol
   - Error rate < %1
   - Latency < 1 saniye

4. **Updates:**
   - Test -> v1 -> v2 -> ... progression
   - Rollback için eski version'u tut

---

## 📞 DESTEK

- **RunPod Docs:** https://docs.runpod.io/
- **Discord:** https://discord.gg/runpod
- **Status:** https://status.runpod.io/

---

**Son Güncelleme:** 2025-09-14
**Durum:**  ÜRETIM'E HAZIR
**Versiyon:** 1.0
