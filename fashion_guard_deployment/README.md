#  Fashion Guard - RunPod Serverless Deployment

This directory contains everything needed to deploy the Fashion Guard AI model on RunPod's Serverless infrastructure.

---

##  Directory Structure

```
fashion_guard_deployment/
├── README.md                          # This file
├── RUNPOD_DEPLOYMENT_GUIDE.md         # Step-by-step deployment guide
├── API_REFERENCE.md                   # API documentation & examples
├── deploy.sh                          # Automated build & push script
├── Dockerfile                         # Container definition
├── .dockerignore                      # Docker build exclusions
├── requirements.txt                   # Python dependencies
├── config.yaml                        # Model configuration
├── runpod_handler.py                  # RunPod serverless handler
└── fashion_guard/                     # Main application package
    ├── __init__.py
    ├── guard.py                       # Core guard logic
    ├── model.py                       # Qwen model wrapper
    ├── language.py                    # Language detection
    ├── parser.py                      # Output parsing
    ├── prompts.py                     # System prompts
    └── responses.py                   # Response templates
```

---

##  Quick Start (3 Steps)

### **Step 1: Make deploy script executable**
```bash
chmod +x deploy.sh
```

### **Step 2: Run deployment script**
```bash
./deploy.sh
```
This will:
-  Build Docker image
-  Push to Docker Hub
-  Show next steps

### **Step 3: Deploy on RunPod**
Go to https://www.runpod.io/console/serverless and follow the guide.

---

##  Documentation Files

### [RUNPOD_DEPLOYMENT_GUIDE.md](RUNPOD_DEPLOYMENT_GUIDE.md)
**Complete step-by-step guide with:**
- Pre-requisites checklist
- Docker build & push instructions
- RunPod configuration form setup
- Testing procedures
- Troubleshooting guide
- Performance metrics

### [API_REFERENCE.md](API_REFERENCE.md)
**API documentation including:**
- Request/response format
- Python, JavaScript, and curl examples
- Error handling & retry strategies
- Language codes and intent types
- Monitoring & logging

---

##  Installation & Setup

### **Prerequisites**
-  Docker Desktop or Docker CLI
-  Docker Hub account
-  RunPod.io account
-  RunPod API key

### **Manual Setup (if not using deploy.sh)**

```bash
# 1. From project root, build image
cd /Users/burak.yilmaz/apprel_guard
docker build -f runpod_Dockerfile -t your-username/fashion-guard:v1 .

# 2. Push to Docker Hub
docker login
docker push your-username/fashion-guard:v1

# 3. Go to RunPod console and deploy
# https://www.runpod.io/console/serverless
```

---

##  Local Testing

### **Test the handler locally (Python)**
```bash
cd fashion_guard_deployment
python runpod_handler.py
```

Expected output:
```
Testing RunPod Handler...

--- Test 1: Turkish product search ---
{
  "status": "success",
  "query": "Siyah bir kışlık mont arıyorum.",
  "intent": "product_search",
  "language": "tr",
  "route": "SEARCH",
  "latency_ms": 325.45
}
```

### **Test in Docker (locally)**
```bash
# Build image
docker build -f Dockerfile -t fashion-guard:test .

# Run container
docker run --rm fashion-guard:test

# Or with GPU (if available)
docker run --rm --gpus all fashion-guard:test
```

---

##  Configuration

### **config.yaml**
Main model configuration file:

```yaml
model_name: Qwen/Qwen3-4B-Instruct-2507    # Model to use
max_chars: 4000                            # Max input length
max_new_tokens: 20                         # Max output tokens
context_messages: 3                        # Context window
language_detection: true                   # Auto-detect language
route_uncertain_to_main_agent: true        # Fallback behavior
```

### **Environment Variables** (RunPod Dashboard)
```
MODEL_NAME=Qwen/Qwen3-4B-Instruct-2507
ACCELERATOR=auto
QUANTIZATION=none
HF_HUB_ENABLE_HF_TRANSFER=0
TRANSFORMERS_CACHE=/app/.cache/huggingface
```

---

##  Performance & Costs

| Metric | Value |
|--------|-------|
| **Model Size** | ~5-6 GB (quantized) |
| **Cold Start** | ~10-15 seconds |
| **Warm Latency** | 0.3-0.5 seconds |
| **GPU Memory** | 16-24 GB required |
| **Idle Cost (Min Workers=0)** | $0.00 |
| **Active Cost** | ~$0.46 per hour (RTX 4090) |

---

##  API Usage

### **Quick API Test**
```bash
curl -X POST "https://api.runpod.io/v2/{ENDPOINT_ID}/runsync" \
  -H "Authorization: Bearer {API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "query": "Bana 2000 TL altı kırmızı abiye önerir misin?",
      "session_language": "tr-TR"
    }
  }'
```

### **Response Example**
```json
{
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

**See [API_REFERENCE.md](API_REFERENCE.md) for complete documentation.**

---

##  Model Updates

### **Update Configuration**
```bash
# 1. Edit configuration
nano config.yaml

# 2. Rebuild Docker image
docker build -f Dockerfile -t your-username/fashion-guard:v2 .

# 3. Push to Docker Hub
docker push your-username/fashion-guard:v2

# 4. Update RunPod endpoint
# Dashboard > Endpoint > Edit > New Image URL
```

### **Update Model**
```yaml
# In config.yaml, change:
model_name: Qwen/Qwen3-4B-Instruct-2507  # Change this
# To:
model_name: Qwen/Qwen3-8B-Instruct       # New model
```

---

##  Troubleshooting

### **Image Build Fails**
```bash
# Check Docker installation
docker --version

# Clear build cache and retry
docker build --no-cache -f Dockerfile -t your-username/fashion-guard:v1 .
```

### **Push to Docker Hub Fails**
```bash
# Login to Docker Hub
docker login

# Retry push
docker push your-username/fashion-guard:v1
```

### **RunPod Deployment Issues**

| Issue | Solution |
|-------|----------|
| Image not found | Check username, ensure image is public |
| Pod offline | Min Workers=0, retry request in 1-2 min |
| Model loading fails | Increase GPU from 16GB to 24GB |
| Timeout errors | Increase execution timeout to 90 seconds |

**Check RunPod logs:**
1. Dashboard > Your Endpoint > View Logs
2. Look for error messages
3. Check model download status

---

##  Dependencies

Key Python packages:
- `torch>=2.1` - PyTorch for GPU computation
- `transformers>=4.53` - Hugging Face transformers
- `accelerate>=0.34` - Multi-GPU/TPU support
- `langdetect>=1.0.9` - Language detection
- `runpod>=0.10.0` - RunPod SDK

See `requirements.txt` for complete list.

---

##  Security Notes

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data (HF_TOKEN, API_KEY)
3. **Keep images private** if using proprietary models
4. **Rotate API keys** regularly
5. **Monitor endpoint usage** for unauthorized access

---

##  Monitoring & Logs

### **View Real-time Logs**
```bash
# Via RunPod Dashboard
https://www.runpod.io/console/serverless
→ Your Endpoint → View Logs

# Via CLI (if available)
runpod logs --endpoint {ENDPOINT_ID}
```

### **Key Metrics to Monitor**
- Request latency
- Error rate
- GPU memory usage
- Model inference time
- Cold/warm start times

---

##  Scaling Strategies

### **For Development/Testing**
```yaml
Min Workers: 0      # No idle cost
Max Workers: 1      # Single concurrent request
GPU: 16GB (A4000)   # Budget option
```

### **For Production**
```yaml
Min Workers: 1      # Always ready
Max Workers: 3-5    # Handle traffic
GPU: 24GB (RTX 4090) # Better performance
```

---



## 📞 Support & Resources

- **RunPod Documentation**: https://docs.runpod.io/
- **RunPod Community**: https://discord.gg/runpod
- **Hugging Face Models**: https://huggingface.co/Qwen/
- **This Project**: Check RUNPOD_DEPLOYMENT_GUIDE.md

---

## 🎓 Learning Resources

- [Docker Documentation](https://docs.docker.com/)
- [RunPod Serverless Guide](https://docs.runpod.io/serverless/overview)
- [Qwen Model Card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
- [Transformers Documentation](https://huggingface.co/docs/transformers/)

---

##  Version History

- **v1** (2025-09-14): Initial release
  - Qwen3-4B model
  - Turkish & English support
  - Basic filtering



---

**Last Updated:** 2025-09-14
**Status:** Production Ready
