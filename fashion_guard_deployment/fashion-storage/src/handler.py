"""
RunPod Serverless Handler for Fashion Guard
"""

import json
import logging
import os
import sys
from typing import Any


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VOLUME_DIR = "/workspace" if os.path.exists("/workspace") else "/runpod-volume"
HF_CACHE = os.path.join(VOLUME_DIR, "huggingface")

os.environ["HF_HOME"] = HF_CACHE
os.environ["TRANSFORMERS_CACHE"] = HF_CACHE
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

logger.info(f"Using HuggingFace cache directory: {HF_CACHE}")


from fashion_guard import FashionGuard
from fashion_guard.model import QwenGuardModel


logger.info("Initializing FashionGuard model globally before accepting traffic...")
try:
    model_name = os.getenv("MODEL_NAME", "Qwen/Qwen3-4B-Instruct-2507")
    accelerator = os.getenv("ACCELERATOR", "auto")
    quantization = os.getenv("QUANTIZATION", "none")
    
    qwen_model = QwenGuardModel(
        model_name=model_name,
        accelerator=accelerator,
        quantization=quantization
    )
    guard = FashionGuard(model=qwen_model)
    logger.info("FashionGuard model loaded and ready on GPU!")
except Exception as e:
    logger.error(f"Fatal error loading model: {str(e)}", exc_info=True)
    raise e


def handler(event: dict) -> dict:
    """Main handler function for RunPod Serverless"""
    try:
        # Extract parameters
        input_data = event.get("input", event) if isinstance(event.get("input"), dict) else event

        query = input_data.get("query", "").strip()
        session_language = input_data.get("session_language") or "tr-TR"
        context = input_data.get("context", [])
        awaiting_clarification = input_data.get("awaiting_clarification", False)
        request_id = input_data.get("request_id")
        session_id = input_data.get("session_id")
        
        # Validate query
        if not query:
            return {
                "status": "error",
                "message": "Query cannot be empty",
                "query": query
            }
        
        # Route the query (Model zaten GPU'da hazır, bekleme süresi 0)
        response, result = guard.route(
            query=query,
            context=context if context else None,
            session_language=session_language,
            awaiting_clarification=awaiting_clarification,
            request_id=request_id,
            session_id=session_id
        )
        
        # Determine route
        if response == "SEARCH":
            route = "SEARCH"
        elif result.intent == "nothing_to_search":
            route = "NEEDS_MORE_DETAIL"
        else:
            route = "REJECT"
        
        # Build response payload
        payload = {
            "status": "success",
            "query": query,
            "intent": result.intent,
            "language": result.language,
            "latency_ms": round(result.latency_ms, 2),
            "route": route,
            "raw_output": result.raw_output
        }
        
        if route != "SEARCH":
            payload["response"] = response
        
        logger.info(f"Request processed: intent={result.intent}, route={route}, latency={result.latency_ms}ms")
        return payload
        
    except Exception as e:
        logger.error(f"Handler error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "query": input_data.get("query", "") if isinstance(input_data, dict) else ""
        }


if __name__ == "__main__":
    import runpod
    logger.info("Starting RunPod Serverless listener...")
    runpod.serverless.start({"handler": handler})
