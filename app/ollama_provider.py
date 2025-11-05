"""Ollama AI provider implementation."""

import os
import time
from typing import Any

import ollama

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


def process_summary(job_id: str, document: str, jobs: dict[str, dict[str, Any]]):
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
