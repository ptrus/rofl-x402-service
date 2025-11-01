"""
FastAPI server with x402 payment middleware.

For a full example with more features, see:
https://github.com/coinbase/x402/tree/main/examples/python/servers/fastapi

Updated: 2025-10-30
"""

import asyncio
import os
import uuid
from typing import Any, Dict, Optional
from enum import Enum

import ollama
import openai
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel
from x402.fastapi.middleware import require_payment

# Load environment variables
load_dotenv()

# Get configuration from environment
ADDRESS = os.getenv("ADDRESS")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
X402_NETWORK = os.getenv("X402_NETWORK", "base-sepolia")
X402_PRICE = os.getenv("X402_PRICE", "$0.001")

# Gaia Node configuration
GAIA_NODE_URL = os.getenv("GAIA_NODE_URL")
GAIA_MODEL_NAME = os.getenv("GAIA_MODEL_NAME", "Qwen3-30B-A3B-Q5_K_M")
GAIA_API_KEY = os.getenv("GAIA_API_KEY")

# AI Backend selection
class AIProvider(str, Enum):
    OLLAMA = "ollama"
    GAIA = "gaia"

AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()

if not ADDRESS:
    raise ValueError("Missing required environment variable: ADDRESS")

# Validate provider configuration
if AI_PROVIDER == "gaia":
    if not GAIA_NODE_URL:
        raise ValueError("GAIA_NODE_URL is required when using Gaia provider")
    if not GAIA_API_KEY:
        raise ValueError("GAIA_API_KEY is required when using Gaia provider")

app = FastAPI()

# Model constraints
MAX_DOCUMENT_LENGTH = 400000  # ~100K tokens (rough estimate: 4 chars per token)
MIN_DOCUMENT_LENGTH = 50  # Minimum meaningful document length

# In-memory job storage (in production, use Redis or similar)
jobs: Dict[str, Dict[str, Any]] = {}


class DocumentRequest(BaseModel):
    document: str


# Apply payment middleware to POST endpoint only (not GET status polling)
app.middleware("http")(
    require_payment(
        path="/summarize-doc",
        price=X402_PRICE,
        pay_to_address=ADDRESS,
        network=X402_NETWORK,
    )
)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with service information"""
    return {
        "service": "ROFL x402 Document Summarization",
        "endpoint": "POST /summarize-doc",
        "price": X402_PRICE,
        "network": X402_NETWORK,
        "ai_provider": AI_PROVIDER,
    }


def process_summary_with_ollama(job_id: str, document: str):
    """Process document summarization using Ollama"""
    try:
        # Configure ollama client
        client = ollama.Client(host=OLLAMA_HOST)

        # System prompt for document summarization
        system_prompt = """You are an expert document summarizer. Your task is to:
1. Read the provided document carefully
2. Extract the main ideas and key points
3. Create a concise, well-structured summary
4. Identify key topics covered in the document

Provide a clear and informative summary that captures the essence of the document."""

        # Generate summary using Ollama
        response = client.chat(
            model="qwen2:0.5b",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Please summarize the following document:\n\n{document}",
                },
            ],
        )

        summary = response["message"]["content"]

        # Calculate basic statistics
        word_count = len(document.split())
        reading_time = max(1, word_count // 200)  # Assume 200 words per minute

        # Update job with result
        jobs[job_id] = {
            "status": "completed",
            "summary": summary,
            "word_count": word_count,
            "reading_time": f"{reading_time} minute{'s' if reading_time != 1 else ''}",
        }

    except Exception as e:
        import traceback
        error_details = f"{str(e)}\n{traceback.format_exc()}"
        jobs[job_id] = {
            "status": "failed",
            "error": str(e),
            "error_details": error_details,
        }


def process_summary_with_gaia(job_id: str, document: str):
    """Process document summarization using Gaia Nodes"""
    try:
        # Configure OpenAI client for Gaia compatibility
        client = openai.OpenAI(
            base_url=GAIA_NODE_URL,
            api_key=GAIA_API_KEY,
        )

        # System prompt for document summarization
        system_prompt = """You are an expert document summarizer. Your task is to:
1. Read the provided document carefully
2. Extract the main ideas and key points
3. Create a concise, well-structured summary
4. Identify key topics covered in the document

Provide a clear and informative summary that captures the essence of the document."""

        # Generate summary using Gaia
        response = client.chat.completions.create(
            model=GAIA_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Please summarize the following document:\n\n{document}",
                },
            ],
        )

        summary = response.choices[0].message.content

        # Calculate basic statistics
        word_count = len(document.split())
        reading_time = max(1, word_count // 200)  # Assume 200 words per minute

        # Update job with result
        jobs[job_id] = {
            "status": "completed",
            "summary": summary,
            "word_count": word_count,
            "reading_time": f"{reading_time} minute{'s' if reading_time != 1 else ''}",
        }

    except Exception as e:
        import traceback
        error_details = f"{str(e)}\n{traceback.format_exc()}"
        jobs[job_id] = {
            "status": "failed",
            "error": str(e),
            "error_details": error_details,
        }


def process_summary(job_id: str, document: str):
    """Background task to process document summarization"""
    if AI_PROVIDER == "gaia":
        process_summary_with_gaia(job_id, document)
    else:
        process_summary_with_ollama(job_id, document)


@app.post("/summarize-doc")
async def summarize_doc(request: DocumentRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    # Validate document length
    doc_length = len(request.document)

    if doc_length < MIN_DOCUMENT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Document too short. Minimum length is {MIN_DOCUMENT_LENGTH} characters.",
        )

    if doc_length > MAX_DOCUMENT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Document too long. Maximum length is {MAX_DOCUMENT_LENGTH} characters (~100K tokens).",
        )

    # Create job ID
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing"}

    # Start background processing
    background_tasks.add_task(process_summary, job_id, request.document)

    # Return job ID immediately
    return {
        "job_id": job_id,
        "status": "processing",
        "status_url": f"/summarize-doc/{job_id}",
        "provider": AI_PROVIDER,
    }


@app.get("/summarize-doc/{job_id}")
async def get_summary_status(job_id: str) -> Dict[str, Any]:
    """Get the status of a summarization job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs[job_id]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=4021)