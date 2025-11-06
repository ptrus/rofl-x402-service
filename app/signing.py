"""
ROFL signing service for TEE-attested response signatures.

This module handles:
1. Key generation using ROFL keymanager (SECP256K1)
2. Registration of public key in ROFL metadata
3. Signing of API responses with recoverable ECDSA signatures
"""

import hashlib
import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class SigningService:
    """Service for signing API responses using ROFL keymanager."""

    def __init__(self):
        """Initialize signing service."""
        self.rofl_client = None
        self.private_key_hex: str | None = None
        self.public_key_hex: str | None = None

    async def initialize(self):
        """Initialize ROFL client and generate signing key (production only)."""
        debug_signing = os.getenv("DEBUG_SIGNING", "false").lower() == "true"
        environment = os.getenv("ENVIRONMENT", "development")

        if debug_signing:
            import secrets

            logger.info("Using mock signing key (DEBUG_SIGNING=true)")
            self.private_key_hex = secrets.token_hex(32)  # 32 bytes = 64 hex chars
            self.public_key_hex = self._derive_public_key(self.private_key_hex)
            logger.info(f"Mock signing public key: {self.public_key_hex}")
            return

        if environment != "production":
            logger.info("Signing disabled in non-production environment")
            return

        try:
            from oasis_rofl_client import KeyKind, RoflClient

            logger.info("Initializing ROFL client for TEE signing...")
            self.rofl_client = RoflClient()

            # Generate SECP256K1 key using ROFL keymanager
            # This returns the private key as a hex string
            logger.info("Generating SECP256K1 signing key...")
            self.private_key_hex = await self.rofl_client.generate_key(
                "rofl-x402-signing-key-v1", kind=KeyKind.SECP256K1
            )
            logger.info("Signing key generated")

            # Derive public key from private key
            self.public_key_hex = self._derive_public_key(self.private_key_hex)
            logger.info(f"Public key: {self.public_key_hex}")

            # Upload public key to metadata
            logger.info("Updating ROFL metadata...")
            await self.rofl_client.set_metadata({"signing_public_key": self.public_key_hex})
            logger.info("Metadata updated")

            logger.info("ROFL signing service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ROFL signing service: {e}", exc_info=True)

    def _derive_public_key(self, private_key_hex: str) -> str:
        """Derive SECP256K1 public key from private key.

        Args:
            private_key_hex: Hex-encoded private key

        Returns:
            Hex-encoded compressed public key
        """
        try:
            from coincurve import PrivateKey

            private_key_bytes = bytes.fromhex(private_key_hex)
            privkey = PrivateKey(private_key_bytes)
            pubkey_bytes = privkey.public_key.format(compressed=True)
            return pubkey_bytes.hex()
        except ImportError:
            logger.error("coincurve library not installed, cannot derive public key")
            raise

    def sign_response(self, response_data: dict[str, Any]) -> dict[str, Any]:
        """Sign an API response with ROFL TEE key.

        Args:
            response_data: The response dictionary to sign

        Returns:
            Response with signature and public_key fields added
        """
        if not self.private_key_hex:
            # Signing not initialized - return unsigned response
            return response_data

        try:
            from coincurve import PrivateKey

            # Create a copy to avoid modifying the original
            data_to_sign = {
                k: v for k, v in response_data.items() if k not in ("signature", "public_key")
            }

            # Create canonical JSON representation for signing
            canonical_json = json.dumps(data_to_sign, sort_keys=True, separators=(",", ":"))

            # Hash the canonical JSON
            message_hash = hashlib.sha256(canonical_json.encode()).digest()

            # Sign the hash using SECP256K1
            private_key_bytes = bytes.fromhex(self.private_key_hex)
            privkey = PrivateKey(private_key_bytes)
            signature_bytes = privkey.sign_recoverable(message_hash, hasher=None)
            signature_hex = signature_bytes.hex()

            # Return response with signature
            signed_response = response_data.copy()
            signed_response["signature"] = signature_hex
            signed_response["public_key"] = self.public_key_hex

            return signed_response

        except Exception as e:
            logger.error(f"Failed to sign response: {e}", exc_info=True)
            # Return unsigned response rather than failing
            return response_data


# Global signing service instance
signing_service = SigningService()
