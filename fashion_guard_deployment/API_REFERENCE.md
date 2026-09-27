# Fashion Guard - RunPod API Quick Reference

##  Endpoint URL

```
https://api.runpod.io/v2/{ENDPOINT_ID}/runsync
```

Replace `{ENDPOINT_ID}` with your actual endpoint ID from RunPod dashboard.

---

##  Request Format

### **Headers**
```
Authorization: Bearer {API_KEY}
Content-Type: application/json
```

### **Body - Basic**
```json
{
  "input": {
    "query": "Siyah bayan çantası arıyorum"
  }
}
```

### **Body - Full (All Options)**
```json
{
  "input": {
    "query": "string - required",
    "session_language": "tr-TR",
    "context": ["previous_query_1", "previous_query_2"],
    "awaiting_clarification": false,
    "request_id": "req-12345",
    "session_id": "session-xyz"
  }
}
```

---

##  Response Format

### **Success Response (200 OK)**

**Route: SEARCH (Product Search)**
```json
{
  "delayTime": 245,
  "executionTime": 350,
  "id": "sync-req-abc123",
  "output": {
    "status": "success",
    "query": "Siyah bayan çantası arıyorum",
    "intent": "product_search",
    "language": "tr",
    "route": "SEARCH",
    "latency_ms": 325.45,
    "raw_output": "..model output.."
  }
}
```

**Route: NEEDS_MORE_DETAIL (Clarification Needed)**
```json
{
  "delayTime": 245,
  "executionTime": 350,
  "id": "sync-req-abc123",
  "output": {
    "status": "success",
    "query": "Çanta arıyorum",
    "intent": "nothing_to_search",
    "language": "tr",
    "route": "NEEDS_MORE_DETAIL",
    "response": "Lütfen ne tür bir çanta aradığınızı belirtiniz. (renk, model, fiyat aralığı vb.)",
    "latency_ms": 285.30,
    "raw_output": "..model output.."
  }
}
```

**Route: REJECT (Out of Scope)**
```json
{
  "delayTime": 245,
  "executionTime": 350,
  "id": "sync-req-abc123",
  "output": {
    "status": "success",
    "query": "Dünyanın en uzun nehri hangisidir?",
    "intent": "out_of_scope",
    "language": "tr",
    "route": "REJECT",
    "response": "Bu soru moda ve giyim ürünleri ile ilgili değildir. Lütfen ürün arama ile ilgili bir soru sorunuz.",
    "latency_ms": 125.45,
    "raw_output": "..model output.."
  }
}
```

### **Error Response (500 Internal Server Error)**
```json
{
  "delayTime": 100,
  "executionTime": 50,
  "id": "sync-req-xyz",
  "output": {
    "status": "error",
    "message": "Model initialization failed",
    "query": "input query"
  }
}
```

---

##  Language Codes Supported

| Language | Code | Example |
|----------|------|---------|
| Turkish | `tr` / `tr-TR` | Siyah bayan çantası |
| English | `en` / `en-GB` | Black leather handbag |
| German | `de` / `de-DE` | Schwarze Damenhandtasche |
| French | `fr` / `fr-FR` | Sac à main noir pour femme |
| Spanish | `es` / `es-ES` | Bolso negro para mujer |

*Auto-detection: If `session_language` not provided, language is auto-detected*

---

##  Intent Types

| Intent | Meaning | Route |
|--------|---------|-------|
| `product_search` | Valid product search query | `SEARCH` |
| `nothing_to_search` | Vague query needing clarification | `NEEDS_MORE_DETAIL` |
| `out_of_scope` | Non-fashion related query | `REJECT` |

---

##  Code Examples

### **Python Example**
```python
import requests
import json

ENDPOINT_ID = "your-endpoint-id"
API_KEY = "your-api-key"
URL = f"https://api.runpod.io/v2/{ENDPOINT_ID}/runsync"

def query_fashion_guard(query: str, language: str = "en-GB"):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "query": query,
            "session_language": language
        }
    }
    
    response = requests.post(URL, json=payload, headers=headers)
    result = response.json()
    
    return result["output"]

# Usage
result = query_fashion_guard("Black leather boots under 200 euros", "en-GB")
print(f"Route: {result['route']}")
print(f"Intent: {result['intent']}")
if result['route'] == 'SEARCH':
    print(" Ready for search")
else:
    print(f"Response: {result.get('response')}")
```

### **JavaScript/Node.js Example**
```javascript
const ENDPOINT_ID = "your-endpoint-id";
const API_KEY = "your-api-key";
const URL = `https://api.runpod.io/v2/${ENDPOINT_ID}/runsync`;

async function queryFashionGuard(query, language = "en-GB") {
  const response = await fetch(URL, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      input: {
        query: query,
        session_language: language
      }
    })
  });

  const data = await response.json();
  return data.output;
}

// Usage
const result = await queryFashionGuard("Red dress under $100", "en-GB");
console.log(`Route: ${result.route}`);
console.log(`Intent: ${result.intent}`);
```

### **curl Example**
```bash
#!/bin/bash

ENDPOINT_ID="your-endpoint-id"
API_KEY="your-api-key"
QUERY="Siyah bot arıyorum"
LANGUAGE="tr-TR"

curl -X POST "https://api.runpod.io/v2/${ENDPOINT_ID}/runsync" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"input\": {
      \"query\": \"${QUERY}\",
      \"session_language\": \"${LANGUAGE}\"
    }
  }" | jq '.output'
```

---

## ⚡ Performance Metrics

- **Cold Start**: ~10-15 seconds (first request, model loading)
- **Warm Start**: ~0.3-0.5 seconds (subsequent requests)
- **Typical Latency**: 250-400ms (inference only)
- **Max Execution Time**: 60 seconds

---

##  Error Handling

### **Common Errors and Solutions**

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Check API key in RunPod settings |
| `404 Not Found` | Invalid endpoint ID | Verify endpoint ID from dashboard |
| `429 Too Many Requests` | Rate limit exceeded | Reduce request frequency or increase `Max Workers` |
| `503 Service Unavailable` | Pod offline/scaling | Check pod status, retry with exponential backoff |
| `{"status": "error", "message": "Model initialization failed"}` | GPU memory issue or model loading error | Check RunPod logs, try with larger GPU |

### **Retry Strategy (Python)**
```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def query_with_retry(query: str):
    return requests.post(URL, json=payload, headers=headers)
```

---

##  Monitoring & Logging

### **Check Endpoint Status**
```bash
curl -X GET "https://api.runpod.io/v2/{ENDPOINT_ID}/health" \
  -H "Authorization: Bearer {API_KEY}"
```

### **View Recent Logs**
Visit: https://www.runpod.io/console/serverless
→ Select your endpoint → "View Logs" (right side)

---

##  Authentication

**Where to find your keys:**

1. **API Key**: RunPod Console → Settings (icon top-right) → API Keys → Copy
2. **Endpoint ID**: RunPod Console → Serverless → Your endpoint → URL contains ID

**Example URL:**
```
https://api.runpod.io/v2/abc123def456ghi/runsync
                          ↑
                      ENDPOINT_ID
```

---

## 🎓 Best Practices

1. **Always use `runsync` endpoint** (not `/run`) for this guard application
2. **Include language code** for better accuracy
3. **Add timeout handling** on client side (60+ seconds)
4. **Log request/response** for monitoring and debugging
5. **Use unique request_id** for tracking in logs
6. **Implement retry logic** for transient failures

---

## 📞 Support

- **RunPod Docs**: https://docs.runpod.io/
- **Status**: https://status.runpod.io/
- **Community Discord**: https://discord.gg/runpod

---

**Last Updated:** 2025-09-14
**API Version:** v2 (sync)
