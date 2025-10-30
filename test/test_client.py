"""
Test client for the x402 document summarization service.

This script demonstrates the full payment flow using x402HttpxClient:
1. Create a wallet with eth_account
2. Make a request to the protected endpoint
3. x402HttpxClient automatically handles 402 response, signs and pays
4. Poll for the result
5. Test payment verification (without payment should fail, reusing payment should fail)
"""

import asyncio
import os
import sys
import time

import httpx
from dotenv import load_dotenv
from eth_account import Account
from x402.clients.httpx import x402HttpxClient

# Load environment variables
load_dotenv()

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:4021")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")


async def test_without_payment(document_text: str):
    """Test that requests without payment are rejected"""
    print("🔒 Testing without payment (should fail)...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_URL}/summarize-doc",
                json={"document": document_text},
            )
            if response.status_code == 402:
                print("   ✅ Correctly rejected with 402 Payment Required\n")
            else:
                print(f"   ❌ Unexpected status: {response.status_code}\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")


async def test_payment_reuse(document_text: str, payment_header: str):
    """Test that reusing the same payment is rejected"""
    print("🔒 Testing payment reuse (should fail)...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_URL}/summarize-doc",
                json={"document": document_text},
                headers={"X-Payment": payment_header},
            )
            if response.status_code == 402:
                print("   ✅ Correctly rejected payment reuse with 402\n")
            elif response.status_code == 400:
                print("   ✅ Correctly rejected payment reuse with 400\n")
            else:
                print(f"   ❌ Unexpected status: {response.status_code}\n")
                print(f"   Response: {response.text}\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")


async def test_summarize_document(document_text: str):
    """
    Test the document summarization endpoint with automatic payment handling.

    Args:
        document_text: The document to summarize
    """
    print("🚀 Starting x402 payment flow test...\n")

    # Check for private key
    if not PRIVATE_KEY:
        print("❌ Error: PRIVATE_KEY environment variable not set")
        print("   Generate a key with: from eth_account import Account; Account.create()")
        sys.exit(1)

    # Create account from private key
    print("💼 Setting up wallet...")
    account = Account.from_key(PRIVATE_KEY)
    print(f"   Wallet address: {account.address}\n")

    # Test without payment first
    await test_without_payment(document_text)

    # Create x402-enabled HTTP client
    print("📡 Creating x402 HTTP client...")
    async with x402HttpxClient(
        account, max_value=10000, timeout=60.0
    ) as client:
        print(f"   Client ready with automatic payment handling\n")

        # Make request - payment will be handled automatically
        print(f"📝 Requesting document summary from {API_URL}/summarize-doc...")
        print(f"   Document length: {len(document_text)} characters")
        print(f"   (Payment will be handled automatically if required)\n")

        try:
            start_time = time.time()
            response = await client.post(
                f"{API_URL}/summarize-doc",
                json={"document": document_text},
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Job created (took {elapsed:.2f}s)")
                print(f"   Job ID: {result['job_id']}")
                print(f"   Status: {result['status']}")
                print(f"   Status URL: {result['status_url']}\n")

                # Test payment reuse with the same payment header
                payment_header = response.request.headers.get("X-Payment")
                if payment_header:
                    await test_payment_reuse(document_text, payment_header)

                # Poll for result
                job_id = result["job_id"]
                print(f"⏳ Polling for result...")

                max_polls = 150  # Poll for up to 10 minutes
                poll_interval = 4  # seconds

                for i in range(max_polls):
                    await asyncio.sleep(poll_interval)

                    status_response = await client.get(f"{API_URL}/summarize-doc/{job_id}")
                    status_data = status_response.json()

                    if status_data["status"] == "completed":
                        print(f"   ✅ Completed after ~{(i+1) * poll_interval}s\n")
                        print(f"📄 Summary:")
                        print(f"   {status_data['summary']}\n")
                        print(f"📊 Stats:")
                        print(f"   Word count: {status_data['word_count']}")
                        print(f"   Reading time: {status_data['reading_time']}")
                        return status_data
                    elif status_data["status"] == "failed":
                        print(f"   ❌ Job failed: {status_data.get('error')}")
                        sys.exit(1)
                    else:
                        print(f"   Still processing... ({i+1}/{max_polls})")

                print(f"   ❌ Timeout waiting for result")
                sys.exit(1)

            else:
                print(f"❌ Request failed with status {response.status_code} (after {elapsed:.2f}s)")
                print(f"   Response: {response.text}")
                sys.exit(1)

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Error after {elapsed:.2f}s: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    # Load test document from file
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Use provided file path or default to test_document.txt
    if len(sys.argv) > 1:
        doc_path = sys.argv[1]
    else:
        doc_path = os.path.join(script_dir, "test_document.txt")

    with open(doc_path, "r") as f:
        test_doc = f.read()

    asyncio.run(test_summarize_document(test_doc))
