#!/usr/bin/env python3
"""
Test the signing service with mock keys.
"""

import asyncio
import os

from signing import signing_service

# Set debug mode to use mock keys
os.environ["DEBUG_SIGNING"] = "true"


async def main():
    print("🧪 Testing signing service...\n")

    # Initialize signing service
    await signing_service.initialize()

    # Create a sample response
    response_data = {
        "status": "completed",
        "summary": "This is a test summary",
        "word_count": 100,
        "reading_time": "1 minute",
    }

    print("📝 Original response:")
    print(response_data)
    print()

    # Sign the response
    signed_response = signing_service.sign_response(response_data)

    print("✅ Signed response:")
    for key, value in signed_response.items():
        if key in ("signature", "public_key"):
            print(f"  {key}: {value[:32]}... ({len(value)} chars)")
        else:
            print(f"  {key}: {value}")
    print()

    # Verify the signature
    print("🔍 Verifying signature...")

    import hashlib
    import json

    from coincurve import PublicKey

    # Recreate canonical JSON (excluding signature and public_key)
    data_to_verify = {
        k: v for k, v in signed_response.items() if k not in ("signature", "public_key")
    }
    canonical_json = json.dumps(data_to_verify, sort_keys=True, separators=(",", ":"))
    message_hash = hashlib.sha256(canonical_json.encode()).digest()

    # Recover public key from signature
    signature_bytes = bytes.fromhex(signed_response["signature"])
    expected_public_key_bytes = bytes.fromhex(signed_response["public_key"])

    recovered_pubkey = PublicKey.from_signature_and_message(
        signature_bytes, message_hash, hasher=None
    )

    if recovered_pubkey.format(compressed=True) == expected_public_key_bytes:
        print("✅ Signature verified successfully!")
        print(f"   Recovered public key matches: {recovered_pubkey.format(compressed=True).hex()}")
    else:
        print("❌ Signature verification failed!")

    print("\n🎉 Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
