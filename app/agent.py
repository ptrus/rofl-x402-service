"""
ERC-8004 Agent registration and management for Oasis ROFL x402 service.
"""

import json
import os
from typing import Any

from agent0_sdk import SDK


async def get_agent_id_from_rofl_metadata() -> str | None:
    """Get agent ID from ROFL metadata (production) or file (development).

    Returns:
        Agent ID string or None if not found
    """
    if os.getenv("ENVIRONMENT") != "production":
        # Development: use file storage
        agent_id_file = os.path.join(os.path.dirname(__file__), ".agent_id")
        if os.path.exists(agent_id_file):
            with open(agent_id_file) as f:
                return f.read().strip()
        return None

    # Production: use ROFL metadata
    try:
        from oasis_rofl_client import RoflClient

        rofl_client = RoflClient()
        metadata = await rofl_client.get_metadata()

        if metadata and "agent_id" in metadata:
            return metadata["agent_id"]
    except Exception:
        pass

    return None


async def store_agent_id_in_rofl_metadata(agent_id: str):
    """Store agent ID in ROFL metadata (production) or file (development).

    Args:
        agent_id: The agent ID to store
    """
    if os.getenv("ENVIRONMENT") != "production":
        # Development: use file storage
        agent_id_file = os.path.join(os.path.dirname(__file__), ".agent_id")
        with open(agent_id_file, "w") as f:
            f.write(agent_id)
        return

    # Production: use ROFL metadata
    try:
        from oasis_rofl_client import RoflClient

        rofl_client = RoflClient()
        await rofl_client.set_metadata({"agent_id": agent_id})
    except json.JSONDecodeError:
        # set_metadata returns 200 OK with empty body, which causes JSON decode error
        # This is expected - treat as success
        pass
    except Exception as e:
        print(f"⚠️  Could not store agent ID in ROFL metadata: {e}")


async def initialize_agent(
    agent0_chain_id: int,
    agent0_rpc_url: str | None,
    agent0_private_key: str | None,
    agent0_ipfs_provider: str,
    agent0_pinata_jwt: str | None,
    agent_name: str,
    agent_description: str,
    agent_image: str,
    agent_wallet_address: str | None,
    x402_endpoint_url: str,
    ai_provider: str,
) -> tuple[SDK | None, Any]:
    """Initialize Agent0 SDK and create agent.

    Returns:
        tuple: (sdk, agent) - SDK instance and agent object, or (None, None) if not configured
    """
    # Only initialize if Agent0 configuration is provided
    if not agent0_rpc_url or not agent0_private_key:
        print("⚠️  Agent0 SDK not configured - skipping agent registration")
        return None, None

    try:
        # Initialize SDK
        initialized_sdk = SDK(
            chainId=agent0_chain_id,
            rpcUrl=agent0_rpc_url,
            signer=agent0_private_key,
            ipfs=agent0_ipfs_provider,
            pinataJwt=agent0_pinata_jwt,
        )

        # Check if we have an existing agent ID stored in ROFL metadata
        existing_agent_id = await get_agent_id_from_rofl_metadata()

        # Load or create agent
        if existing_agent_id:
            try:
                initialized_agent = initialized_sdk.loadAgent(existing_agent_id)
            except Exception as e:
                print(f"⚠️  Could not load existing agent: {e}")
                initialized_agent = initialized_sdk.createAgent(
                    name=agent_name, description=agent_description, image=agent_image
                )
        else:
            initialized_agent = initialized_sdk.createAgent(
                name=agent_name, description=agent_description, image=agent_image
            )

        # Configure wallet if provided
        if agent_wallet_address:
            initialized_agent.setAgentWallet(agent_wallet_address, chainId=agent0_chain_id)

        # Set trust with reputation and TEE attestation
        initialized_agent.setTrust(reputation=True, teeAttestation=True)

        # Enable x402 payment support
        initialized_agent.setX402Support(True)

        # Register x402 endpoint as A2A endpoint
        initialized_agent.setA2A(x402_endpoint_url, version="1.0", auto_fetch=False)

        # Add metadata
        initialized_agent.setMetadata(
            {
                "version": "1.0.0",
                "category": "ai-assistant",
                "service": "document-summarization",
                "ai_provider": ai_provider,
            }
        )

        # Set agent as active
        initialized_agent.setActive(True)

        # Register on-chain with IPFS
        initialized_agent.registerIPFS()

        print(f"✅ Agent registered: {initialized_agent.agentId}")

        # Save agent ID to ROFL metadata for future use
        if initialized_agent.agentId and not existing_agent_id:
            await store_agent_id_in_rofl_metadata(initialized_agent.agentId)

        return initialized_sdk, initialized_agent

    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        import traceback

        traceback.print_exc()
        return None, None


async def add_signing_key_to_agent(agent: Any, signing_public_key: str):
    """Add signing public key to agent metadata and update registration.

    Args:
        agent: Agent instance
        signing_public_key: Hex-encoded public key from signing service
    """
    if not agent or not signing_public_key:
        return

    try:
        agent.setMetadata({"rofl_signing_public_key": signing_public_key})
        # Re-register to update metadata on-chain
        agent.registerIPFS()
    except Exception as e:
        print(f"⚠️  Failed to add signing key to agent metadata: {e}")
