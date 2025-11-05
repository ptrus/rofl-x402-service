"""Gaia Nodes AI provider implementation."""

import os
import time
from typing import Any

import openai

GAIA_NODE_URL = os.getenv("GAIA_NODE_URL")
GAIA_MODEL_NAME = os.getenv("GAIA_MODEL_NAME", "Qwen3-30B-A3B-Q5_K_M")
GAIA_API_KEY = os.getenv("GAIA_API_KEY")


def process_summary(job_id: str, document: str, jobs: dict[str, dict[str, Any]]):
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
            "timestamp": int(time.time()),
        }

    except Exception as e:
        import traceback

        error_details = f"{str(e)}\n{traceback.format_exc()}"
        jobs[job_id] = {
            "status": "failed",
            "error": str(e),
            "error_details": error_details,
            "timestamp": int(time.time()),
        }
