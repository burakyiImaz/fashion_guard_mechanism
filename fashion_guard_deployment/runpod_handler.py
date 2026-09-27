"""
RunPod Serverless Handler for Fashion Guard
This file handles incoming requests to the guard API
"""

import json
import logging
import os
from typing import Any

# Configure environment
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

# Import fashion guard (correct path for container deployment)
from fashion_guard import FashionGuard
from fashion_guard.model import QwenGuardModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global guard instance - initialized once
_guard_instance = None


def initialize_guard():
    """Initialize the guard model (called once on first request)"""
    global _guard_instance
    if _guard_instance is None:
        logger.info("Initializing FashionGuard model...")
        try:
            model_name = os.getenv("MODEL_NAME", "Qwen/Qwen3-4B-Instruct-2507")
            accelerator = os.getenv("ACCELERATOR", "auto")
            quantization = os.getenv("QUANTIZATION", "none")
            
            qwen_model = QwenGuardModel(
                model_name=model_name,
                accelerator=accelerator,
                quantization=quantization
            )
            _guard_instance = FashionGuard(model=qwen_model)
            logger.info(f"FashionGuard initialized successfully with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize FashionGuard: {str(e)}")
            raise
    return _guard_instance


def handler(event: dict) -> dict:
    """
    Main handler function for RunPod Serverless
    
    Expected input (JSON):
    {
        "query": "string - the user query",
        "session_language": "string (optional) - e.g., 'tr-TR', 'en-GB'",
        "context": "list (optional) - previous queries for context",
        "awaiting_clarification": "boolean (optional) - if waiting for clarification",
        "request_id": "string (optional) - unique request identifier",
        "session_id": "string (optional) - unique session identifier"
    }
    
    Returns (JSON):
    {
        "status": "success" or "error",
        "query": "the input query",
        "intent": "the detected intent",
        "language": "detected language",
        "route": "SEARCH, NEEDS_MORE_DETAIL, or REJECT",
        "latency_ms": "processing time in milliseconds",
        "response": "optional response message",
        "raw_output": "raw model output"
    }
    """
    try:
        # Initialize guard on first request
        guard = initialize_guard()
        
        # Extract parameters from event
        query = event.get("query", "").strip()
        session_language = event.get("session_language")
        context = event.get("context", [])
        awaiting_clarification = event.get("awaiting_clarification", False)
        request_id = event.get("request_id")
        session_id = event.get("session_id")
        
        # Validate query
        if not query:
            return {
                "status": "error",
                "message": "Query cannot be empty",
                "query": query
            }
        
        # Route the query
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
        
        # Add response message if not a SEARCH
        if route != "SEARCH":
            payload["response"] = response
        
        logger.info(f"Request processed: intent={result.intent}, route={route}, latency={result.latency_ms}ms")
        return payload
        
    except Exception as e:
        logger.error(f"Handler error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "query": event.get("query", "")
        }


# For local testing and RunPod deployment
if __name__ == "__main__":
    import sys
    
    # Check if running in RunPod environment
    if "RUNPOD_POD_ID" in os.environ or len(sys.argv) > 1 and sys.argv[1] == "--runpod":
        # RunPod Serverless mode
        logger.info("Starting RunPod Serverless handler...")
        import runpod # pyright: ignore[reportMissingImports]
        runpod.serverless.start({"handler": handler})
    else:
        # Local testing mode
        # Test case 1: Product search (Turkish)
        test_event_1 = {
            "query": "Siyah bir kışlık mont arıyorum.",
            "session_language": "tr-TR"
        }
        
        # Test case 2: Product search (English)
        test_event_2 = {
            "query": "Black leather ankle boots under 200 euros.",
            "session_language": "en-GB"
        }
        
        # Test case 3: Out of scope
        test_event_3 = {
            "query": "What is the capital of France?",
            "session_language": "en-GB"
        }
        
        print("Testing RunPod Handler...")
        print("\n--- Test 1: Turkish product search ---")
        result = handler(test_event_1)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        print("\n--- Test 2: English product search ---")
        result = handler(test_event_2)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        print("\n--- Test 3: Out of scope ---")
        result = handler(test_event_3)
        print(json.dumps(result, ensure_ascii=False, indent=2))
