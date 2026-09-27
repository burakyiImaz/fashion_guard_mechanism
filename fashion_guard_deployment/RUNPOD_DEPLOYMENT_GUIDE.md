# RunPod Serverless Deployment Guide - Fashion Guard

##  Pre-requisites

- [x] Docker Desktop veya Docker CLI yüklü
- [x] Docker Hub hesabı (veya private registry)
- [x] RunPod.io hesabı
- [x] RunPod API key (Settings > API Keys)

---

##  Step-by-Step Deployment

### **STEP 1: Docker Image'ı Build Edin**

```bash
# Bu komutlar proje root'unda çalıştırılacak
cd /Users/burak.yilmaz/apprel_guard

# Build image (username yerine DockerHub username'iniz yazın)
docker build -f runpod_Dockerfile -t your-username/fashion-guard:v1 .

# Örnek:
# docker build -f runpod_Dockerfile -t burak123/fashion-guard:v1 .
```

**Build Çıktısı Örneği:**
```
Sending build context to Docker daemon   ...
Step 1/15 : FROM python:3.10-slim
 ---> abc123...
...
Step 15/15 : CMD ["python", "-u", "runpod_handler.py"]
 ---> Running in xyz...
Successfully tagged your-username/fashion-guard:v1
```

---

### **STEP 2: Docker Hub'a Push Edin**

```bash
# Docker Hub'a giriş yapın
docker login

# Image'ı push edin
docker push your-username/fashion-guard:v1
```

**Push Çıktısı Örneği:**
```
The push refers to repository [docker.io/your-username/fashion-guard]
v1: digest: sha256:abc123... size: 2500
```

---

### **STEP 3: RunPod Paneline Girin**

1. https://www.runpod.io/console/serverless öğesine gidin
2. **"Create an endpoint"** / **"+ New Endpoint"** butonuna tıklayın
3. **"Custom code"** kutusunda **"Deploy from a Docker image"** seçin

---

### **STEP 4: RunPod Konfigürasyonunu Yapın**

**Açılan form'da şu değerleri girin:**

| Alan | Değer | Açıklama |
|------|-------|----------|
| **Endpoint Name** | `fashion-guard-inference` | İsteğe bağlı, tanımlayıcı isim |
| **Container Image** | `your-username/fashion-guard:v1` | Docker Hub image URL |
| **Container Registry** | `Public` | Docker Hub public image |
| **GPU** | `16 GB (A4000)` veya `24 GB (RTX 4090)` | Seçeneklerden biri |
| **Min Workers** | `0` |  ÖNEMLİ: Idle ücret = $0 |
| **Max Workers** | `1` | Basit inference için yeterli |
| **Execution Timeout** | `60` saniye | Model inference için |

**Opsiyonel Ayarlar:**
- **Environment Variables:**
  ```
  MODEL_NAME=Qwen/Qwen3-4B-Instruct-2507
  ACCELERATOR=auto
  QUANTIZATION=none
  HF_HUB_ENABLE_HF_TRANSFER=0
  ```

- **Requests/Min** (rate limiting): `100` (istediğiniz gibi)

---

### **STEP 5: Deploy Edin**

1. Sayfanın altında **"Deploy Endpoint"** butonuna tıklayın
2. ⏳ Deployment 2-5 dakika sürer
3. Durumu "ACTIVE" olunca, **Endpoint ID** kopyalayın

**Endpoint URL Formatı:**
```
https://api.runpod.io/v2/{ENDPOINT_ID}/runsync
```

---

##  Testing

### **Test İstek Gönderin**

```bash
# curl kullanarak test
ENDPOINT_ID="your-endpoint-id-here"
API_KEY="your-runpod-api-key-here"

curl -X POST "https://api.runpod.io/v2/${ENDPOINT_ID}/runsync" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "query": "Bana 2000 TL altı kırmızı abiye önerir misin?",
      "session_language": "tr-TR"
    }
  }'
```

### **Beklenen Response (Success):**

```json
{
  "delayTime": 245,
  "executionTime": 350,
  "id": "req-12345abc",
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

### **Hata Ayıklama (Troubleshooting)**

| Hata | Nedeni | Çözüm |
|------|--------|-------|
| `"Pod not available"` | GPU kaynaklı | Min Workers=0, yeniden deneyin |
| `"500 Internal Server Error"` | Handler hatası | Logs'ta kontrol edin |
| `"Unauthorized"` | API Key yanlış | RunPod Settings'te API Key'i kontrol edin |
| `"Image not found"` | Docker image invalid | Docker Hub'da image'ın public olduğunu kontrol edin |

---

##  Performance Özeti

| Metrik | Değer | Not |
|--------|-------|-----|
| **Cold Start** | ~10-15 saniye | İlk istek, model loading |
| **Warm Start** | ~0.3-0.5 saniye | Sonraki istekler |
| **GPU Idle Cost** | $0.00 | Min Workers=0 sayesinde |
| **Max Latency** | 60 saniye | Timeout değeri |
| **Model Size** | ~5-6 GB | Qwen3-4B quantized |

---

##  Geliştirme & İterasyon

Model veya config'i güncellemek için:

```bash
# 1. Dosyaları düzenleyin
nano fashion_guard_deployment/config.yaml
nano fashion_guard_deployment/fashion_guard/prompts.py

# 2. Yeni image build edin
docker build -f runpod_Dockerfile -t your-username/fashion-guard:v2 .

# 3. Push edin
docker push your-username/fashion-guard:v2

# 4. RunPod'da endpoint'i update edin
#    (Dashboard > Endpoint > Update > New image URL)
```

---

##  Endpoint'i Durdurmak

RunPod Dashboard'da:
1. Endpoint'i seçin
2. **"Pause"** veya **"Delete"** tıklayın
3.  Deployed iken ücret ödü**n**eme başlanır

---

##  API Reference

### **Geçerli Input Parametreleri**

```python
{
  "query": "string",                    # Zorunlu
  "session_language": "string",         # Opsiyonel: "tr-TR", "en-GB"
  "context": ["prev_query_1", "..."],   # Opsiyonel: İçerik
  "awaiting_clarification": false,      # Opsiyonel: Clarification state
  "request_id": "unique-id",            # Opsiyonel: Request tracking
  "session_id": "session-id"            # Opsiyonel: Session tracking
}
```

### **Output Parametreleri**

```python
{
  "status": "success|error",
  "query": "input query",
  "intent": "product_search|nothing_to_search|out_of_scope",
  "language": "detected language",
  "route": "SEARCH|NEEDS_MORE_DETAIL|REJECT",
  "latency_ms": 325.45,
  "response": "rejection message (if route=REJECT)",
  "raw_output": "raw model output"
}
```

---

##  Best Practices

1. **Min Workers = 0** kullanarak maliyeti minimize edin
2. **Execution Timeout = 60** saniye yeterlidir
3. Model updates'i v1, v2, v3 şeklinde tag'leyin
4. Test'ler production'a push etmeden önce local'de çalıştırın
5. **Request logging** ekleyerek monitoring yapın

---

##  Support & Debug

### **Logs Nasıl Kontrol Edilir?**

1. RunPod Dashboard'da endpoint'i seçin
2. **"View Logs"** tıklayın (sa**ğ** tarafta)
3. Son 100 log satırı görüntülenecektir

### **Model İndirme Sorunu?**

HF_TOKEN set edin (private models için):
```bash
# Environment variable olarak ekleyin (RunPod Dashboard):
HF_TOKEN=your_hugging_face_token
```

---

##  Deployment Checklist

- [ ] Docker yüklü ve çalışıyor
- [ ] Docker Hub hesabı hazır ve image push edildikçi
- [ ] RunPod API key kopyalanan
- [ ] Image build edildi: `docker build -f runpod_Dockerfile ...`
- [ ] Image push edildi: `docker push ...`
- [ ] RunPod endpoint oluşturuldu
- [ ] Container Image URL doğru: `your-username/fashion-guard:v1`
- [ ] GPU seçildi: A4000 16GB veya RTX 4090 24GB
- [ ] Min Workers = 0 ayarlandı
- [ ] Execution Timeout = 60 saniye
- [ ] Test isteği gönderildi ve başarılı response alındı
- [ ] Endpoint ID ve API Key kaydedildi

---

**Son Güncelleme:** 2025-09-14
**Versiyon:** 1.0
