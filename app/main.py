"""
Oasis ROFL FastAPI server with x402 payment middleware.
"""

import os
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from x402.fastapi.middleware import require_payment

from agent import add_signing_key_to_agent, initialize_agent
from signing import signing_service

# Load environment variables
load_dotenv()

# Get configuration from environment
ADDRESS = os.getenv("ADDRESS")
X402_NETWORK = os.getenv("X402_NETWORK", "base-sepolia")
X402_PRICE = os.getenv("X402_PRICE", "$0.001")
X402_ENDPOINT_URL = os.getenv("X402_ENDPOINT_URL", "http://localhost:4021/summarize-doc")


# AI Backend selection
class AIProvider(str, Enum):
    OLLAMA = "ollama"
    GAIA = "gaia"


AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()

# Conditionally import AI provider modules
if AI_PROVIDER == "gaia":
    try:
        import gaia_provider as ai_provider
    except ImportError as e:
        raise ImportError(
            "Gaia provider selected but openai package not installed. "
            "Install with: uv sync --group gaia"
        ) from e
else:
    try:
        import ollama_provider as ai_provider
    except ImportError as e:
        raise ImportError(
            "Ollama provider selected but ollama package not installed. "
            "Install with: uv sync --group ollama"
        ) from e

# Agent0 SDK configuration
AGENT0_CHAIN_ID = int(os.getenv("AGENT0_CHAIN_ID", "11155111"))
AGENT0_RPC_URL = os.getenv("AGENT0_RPC_URL")
AGENT0_PRIVATE_KEY = os.getenv("AGENT0_PRIVATE_KEY")
AGENT0_IPFS_PROVIDER = os.getenv("AGENT0_IPFS_PROVIDER", "pinata")
AGENT0_PINATA_JWT = os.getenv("AGENT0_PINATA_JWT")

# Agent configuration
AGENT_NAME = os.getenv("AGENT_NAME", "Oasis ROFL x402 Summarization Agent")
AGENT_DESCRIPTION = os.getenv(
    "AGENT_DESCRIPTION",
    "Oasis ROFL x402-enabled document processing agent running in TEE. REST API for async summarization. Multi-provider AI backend (Ollama/Gaia). On-chain registered with reputation trust model.",
)
AGENT_IMAGE = os.getenv("AGENT_IMAGE", "https://example.com/agent-image.png")
AGENT_WALLET_ADDRESS = os.getenv("AGENT_WALLET_ADDRESS")

if not ADDRESS:
    raise ValueError("Missing required environment variable: ADDRESS")

app = FastAPI()

# Logo path
LOGO_PATH = Path(__file__).parent / "logo.png"

# Model constraints
MAX_DOCUMENT_LENGTH = 400000  # ~100K tokens (rough estimate: 4 chars per token)
MIN_DOCUMENT_LENGTH = 50  # Minimum meaningful document length

# In-memory job storage (in production, use Redis or similar)
jobs: dict[str, dict[str, Any]] = {}

# Global agent instance
agent = None


@app.on_event("startup")
async def startup_event():
    """Initialize Agent0 SDK, signing service, and create agent on startup"""
    global agent

    # Initialize ROFL signing service
    await signing_service.initialize()

    # Initialize Agent0 SDK and create agent
    _, agent = await initialize_agent(
        agent0_chain_id=AGENT0_CHAIN_ID,
        agent0_rpc_url=AGENT0_RPC_URL,
        agent0_private_key=AGENT0_PRIVATE_KEY,
        agent0_ipfs_provider=AGENT0_IPFS_PROVIDER,
        agent0_pinata_jwt=AGENT0_PINATA_JWT,
        agent_name=AGENT_NAME,
        agent_description=AGENT_DESCRIPTION,
        agent_image=AGENT_IMAGE,
        agent_wallet_address=AGENT_WALLET_ADDRESS,
        x402_endpoint_url=X402_ENDPOINT_URL,
        ai_provider=AI_PROVIDER,
    )

    # Add signing public key to agent metadata if available
    if agent and signing_service.public_key_hex:
        await add_signing_key_to_agent(agent, signing_service.public_key_hex)


class DocumentRequest(BaseModel):
    document: str


# Apply payment middleware to POST endpoint only (not GET status polling)
# IMPORTANT: If using production endpoints, ensure payment settlement is completed
# on-chain before starting the job to avoid processing unpaid requests.
app.middleware("http")(
    require_payment(
        path="/summarize-doc",
        price=X402_PRICE,
        pay_to_address=ADDRESS,
        network=X402_NETWORK,
    )
)


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint with service information"""
    response = {
        "service": "ROFL x402 Document Summarization",
        "endpoint": "POST /summarize-doc",
        "price": X402_PRICE,
        "network": X402_NETWORK,
        "ai_provider": AI_PROVIDER,
    }

    # Add agent information if available
    if agent:
        response["agent"] = {
            "id": getattr(agent, "agentId", None),
            "uri": getattr(agent, "agentURI", None),
            "name": AGENT_NAME,
        }

    return response


@app.get("/logo.png")
async def get_logo():
    """Serve the agent logo"""
    if LOGO_PATH.exists():
        return FileResponse(LOGO_PATH, media_type="image/png")
    raise HTTPException(status_code=404, detail="Logo not found")


@app.post("/summarize-doc")
async def summarize_doc(
    request: DocumentRequest, background_tasks: BackgroundTasks
) -> dict[str, Any]:
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
    jobs[job_id] = {"status": "processing", "timestamp": int(time.time())}

    # Start background processing using the selected AI provider
    background_tasks.add_task(ai_provider.process_summary, job_id, request.document, jobs)

    # Return job ID immediately
    return {
        "job_id": job_id,
        "status": "processing",
        "status_url": f"/summarize-doc/{job_id}",
        "provider": AI_PROVIDER,
        "timestamp": int(time.time()),
    }


@app.get("/summarize-doc/{job_id}")
async def get_summary_status(job_id: str) -> dict[str, Any]:
    """Get the status of a summarization job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    response = jobs[job_id]

    # Sign the response if signing is enabled
    signed_response = signing_service.sign_response(response)

    return signed_response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=4021)
