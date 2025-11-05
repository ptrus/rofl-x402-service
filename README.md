# Oasis ROFL x402 Document Summarization Service

A confidential AI microservice that summarizes documents inside a verifiable TEE, paid via x402 micropayments.

- **🔒 Private**: Documents processed inside a confidential Oasis ROFL container using Ollama (qwen2:0.5b) or Gaia Nodes
- **🔐 Secure**: Uses aTLS (Attested TLS) with end-to-end TLS authentication from the TEE
- **✅ Verifiable**: Remote attestation proves the exact code running in the TEE
- **🔏 Signed**: All responses cryptographically signed with TEE-generated SECP256K1 keys
- **💰 Monetizable**: x402 micropayments - $0.001 per summary on Base Sepolia (testnet)
- **📝 Discoverable**: Registered on-chain using [ERC-8004](https://eips.ethereum.org/EIPS/eip-8004) Agent Identity Standard

**Tech Stack**
- Python FastAPI backend
- Ollama (Qwen2 0.5B model) or Gaia Nodes (OpenAI compatible API)
- x402 protocol for micropayments
- ERC-8004 on-chain agent registration with [Agent0 SDK](https://github.com/agent0lab/agent0-py)
- Oasis ROFL keymanager for TEE-based cryptographic signing
- Runs in an Oasis ROFL TEE on the Oasis Network

## Testing Locally

```bash
docker compose up
```

The test client (in the `test/` folder) automatically performs an x402 payment and then requests the summary, verifying the on-chain transaction.

```bash
cd test
uv sync

# Generate a test wallet (save the private key!)
uv run python -c "from eth_account import Account; acc = Account.create(); print(f'Address: {acc.address}\nPrivate Key: {acc.key.hex()}')"

# Fund the wallet with Base Sepolia ETH and USDC
# - ETH for gas: https://www.coinbase.com/en-gb/developer-platform/products/faucet
# - USDC: 0x036CbD53842c5426634e7929541eC2318f3dCF7e

# Configure .env with your private key
echo "PRIVATE_KEY=0x..." > .env
echo "API_URL=http://localhost:4021" >> .env

# Run the test (uses test_document.txt by default)
uv run python test_client.py

# Or test with your own document
uv run python test_client.py /path/to/your/document.txt
```

**Example output:**

```
🔒 Testing without payment (should fail)...
   ✅ Correctly rejected with 402 Payment Required

✅ Job created (took 1.66s)

🔒 Testing payment reuse (should fail)...
   ✅ Correctly rejected payment reuse with 402

⏳ Polling for result...
   ✅ Completed after ~44s

📄 Summary:
   The document discusses the technology zkTLS that combines two cryptographic
   approaches: TLS providing encryption and authentication for secure data
   transmission in HTTPS while zero-knowledge proofs allow one party to prove
   knowledge of information without revealing it...

📊 Stats:
   Word count: 304
   Reading time: 1 minute
```

**Example output with a Gaia Node:**

```
🔒 Testing without payment (should fail)...
   ✅ Correctly rejected with 402 Payment Required

✅ Job created (took 1.66s)

🔒 Testing payment reuse (should fail)...
   ✅ Correctly rejected payment reuse with 402

⏳ Polling for result...
   ✅ Completed after ~272s

📄 Summary:
   ZkTLS is a cryptographic protocol that combines two approaches for secure communication over internet protocols such as HTTPS, such as TLS for encrypting data during transmission. It provides encryption and authentication for securing data transmission through secure sessions. This protocol allows only trusted nodes to prove knowledge of information without revealing it. The Proof can then be recorded on a blockchain and used for verification. The protocol supports three types of approaches, MPC-based, TEE-based, and Proxy-based. zkTLS solves the problem of oracle problem in identity verification and provides privacy protection. It has important applications in DeFi lending platforms, Identity verification using secure web sources, Privacy-preserving oracles providing verifiable data feeds, and Verifiable airdrops confirming off-chain eligibility. There are also some potential drawbacks to zkTLS such as completeness, partial solution for the oracle problem, and need for complementary safeguards like reputation systems and cross-checks for maximum effectiveness.

📊 Stats:
   Word count: 304
   Reading time: 1 minute
```

Testing with [zkTLS article](https://oasis.net/blog/zktls-blockchain-security) (2,362 characters).

## AI Provider Options

This service supports two AI providers for document summarization:

1. **Ollama** (default) - Local inference with the Qwen2 0.5B model
2. **Gaia Nodes** - Decentralized AI inference network with OpenAI-compatible API

To switch between providers, set the `AI_PROVIDER` environment variable:

```bash
# Use Ollama (default)
AI_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434

# Use Gaia Nodes
AI_PROVIDER=gaia
GAIA_NODE_URL=https://your-node-id.gaia.domains/v1
GAIA_MODEL_NAME=Qwen3-30B-A3B-Q5_K_M
GAIA_API_KEY=your-gaia-api-key
```

When using Gaia Nodes, you must provide:
- `GAIA_NODE_URL`: The URL of your Gaia Node
- `GAIA_MODEL_NAME`: The model name to use (e.g., gpt-4, gpt-3.5-turbo)
- `GAIA_API_KEY`: Your API key for authentication

Learn how to launch your own Gaia node at [docs.gaianet.ai/getting-started/quick-start](https://docs.gaianet.ai/getting-started/quick-start).

**Note:** Dependencies are split into optional groups (`ollama` and `gaia`) to reduce Docker image size. The Dockerfile installs `ollama` by default. To use Gaia, update the Dockerfile line:
```dockerfile
RUN uv sync --frozen --no-dev --group gaia
```

## ERC-8004 Agent Registration

This service supports on-chain agent registration using the [ERC-8004 Agent Identity Standard](https://eips.ethereum.org/EIPS/eip-8004) via the [Agent0 SDK](https://github.com/agent0lab/agent0-py). For Oasis ROFL-specific validation tooling, see [ERC-8004 on Oasis](https://github.com/oasisprotocol/erc-8004).

When the service starts running in an Oasis ROFL TEE, it automatically:
- Registers the agent on-chain with metadata (name, description, capabilities)
- Publishes the agent card to IPFS
- Configures trust models (reputation + TEE attestation)
- Enables x402 payment support
- Registers the service endpoint for discovery

### Configuration

To enable agent registration, set these environment variables:

```bash
# Agent0 SDK Configuration
AGENT0_CHAIN_ID=84532  # Base Sepolia testnet
AGENT0_RPC_URL=https://base-sepolia.g.alchemy.com/v2/your-api-key
AGENT0_PRIVATE_KEY=your-private-key-here
AGENT0_IPFS_PROVIDER=pinata
AGENT0_PINATA_JWT=your-pinata-jwt-token

# Agent Configuration
AGENT_NAME=Oasis ROFL x402 Summarization Agent
AGENT_DESCRIPTION=x402-enabled document processing agent running in Oasis TEE
AGENT_IMAGE=https://your-domain.com/logo.png  # Served from /logo.png endpoint
AGENT_WALLET_ADDRESS=0x...  # Optional: agent's payment wallet

# x402 Endpoint
X402_ENDPOINT_URL=https://your-domain.com/summarize-doc
```

The agent ID is persisted in Oasis ROFL metadata (production) or a local `.agent_id` file (development). On subsequent restarts, the service will load and update the existing agent rather than creating a new one.

### Agent Card Example

Once registered, your agent will have an on-chain identity with metadata like:

```json
{
  "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
  "name": "Oasis ROFL x402 Summarization Agent",
  "description": "x402-enabled document processing agent running in Oasis TEE. REST API for async summarization. Multi-provider AI backend (Ollama/Gaia). On-chain registered with reputation trust model.",
  "image": "http://localhost:4021/logo.png",
  "endpoints": [
    {
      "name": "A2A",
      "endpoint": "https://summary.updev.si/summarize-doc",
      "version": "1.0"
    },
    {
      "name": "agentWallet",
      "endpoint": "eip155:84532:0xebD8A84C29E1f534c0E8fA555E1Ee63Ff4E0592C"
    }
  ],
  "registrations": [
    {
      "agentId": 380,
      "agentRegistry": "eip155:1:{identityRegistry}"
    }
  ],
  "supportedTrust": ["reputation", "tee-attestation"],
  "active": true,
  "x402support": true,
  "updatedAt": 1762363389
}
```

## TEE-Attested Response Signing

All API responses are cryptographically signed using SECP256K1 keys generated inside the Oasis ROFL TEE, providing cryptographic proof that responses originated from the attested service.

**How it works:**
1. On startup, the service generates a SECP256K1 key pair using Oasis ROFL's keymanager
2. The public key is registered in Oasis ROFL metadata and ERC-8004 agent metadata as `rofl_signing_public_key`
3. Each response is signed with a recoverable ECDSA signature over canonical JSON
4. Clients can verify signatures by recovering the public key and comparing to the registered key

**Signed response format:**
```json
{
  "status": "completed",
  "summary": "...",
  "timestamp": 1730000000,
  "signature": "df9528e21e543b31a6b909d66002f974...",
  "public_key": "03e1e2206b206770bb69feb6f37ec091..."
}
```

**Configuration:**
```bash
ENVIRONMENT=production      # Uses Oasis ROFL keymanager for signing
ENVIRONMENT=development     # Signing disabled
DEBUG_SIGNING=true         # Use mock keys for testing
```

In production, the signing key is generated by Oasis ROFL's secure keymanager and never leaves the TEE. The public key can be verified against the on-chain attested state in the [Oasis ROFL registry](https://github.com/ptrus/rofl-registry).

## Try the Live Testnet Deployment

**Live service running on Oasis Testnet** at **https://summary.updev.si** ([App ID: `rofl1qq6m08wlj3qawcfrd3ljyge2t0praed5ycwh7upg`](https://explorer.oasis.io/testnet/sapphire/rofl/app/rofl1qq6m08wlj3qawcfrd3ljyge2t0praed5ycwh7upg))

Test the live deployment:

```bash
cd test
echo "API_URL=https://summary.updev.si" >> .env

# Test with default document
uv run python test_client.py

# Or test with this README
uv run python test_client.py ../README.md
```

**Example output (summarizing this README):**

```
✅ Job created (took 2.46s)

🔒 Testing payment reuse (should fail)...
   ✅ Correctly rejected payment reuse with 402

⏳ Polling for result...
   ✅ Completed after ~196s

📄 Summary:
   The document outlines a new AI microservice called ROFL that utilizes the
   Ollama model from the Qwen2 series. This microservice is paid via x402
   protocol payments and can be used to summarize documents inside a private
   container using encryption. The document also mentions the ability to
   monetize the service through x402 protocols and uses Base Sepolia as a
   test network for testing purposes.

📊 Stats:
   Word count: 604
   Reading time: 3 minutes
```

**Example output (summarizing this README):**

```
✅ Job created (took 2.46s)

🔒 Testing payment reuse (should fail)...
   ✅ Correctly rejected payment reuse with 402

⏳ Polling for result...
   ✅ Completed after ~196s

📄 Summary:
   The document outlines a new AI microservice called ROFL that utilizes the
   Ollama model from the Qwen2 series. This microservice is paid via x402
   protocol payments and can be used to summarize documents inside a private
   container using encryption. The document also mentions the ability to
   monetize the service through x402 protocols and uses Base Sepolia as a
   test network for testing purposes.

📊 Stats:
   Word count: 604
   Reading time: 3 minutes
```

To verify the app code, attestation, and TLS connection, see [rofl-registry](https://github.com/ptrus/rofl-registry).

## Deploy Your Own Service

**Ready to build your own paid AI service?** Follow these steps to deploy on Oasis:

### 1. Clone the Repository

```bash
git clone https://github.com/ptrus/rofl-x402-service
cd rofl-x402-service
```

### 2. Reset ROFL Manifest

Clear existing deployment configuration using [oasis-cli](https://github.com/oasisprotocol/cli):

```bash
oasis rofl init --reset
```

### 3. Customize Your Service

Modify the endpoint implementation in `app/main.py` (lines 51-84) to create your own paid service:

```python
@app.post("/summarize-doc")
async def summarize_doc(request: DocumentRequest) -> Dict[str, Any]:
    # Your custom service logic here
    # Example: image generation, data analysis, API access, etc.
    ...
```

Update the payment configuration:
- Change `X402_PRICE` in `.env` for your desired pricing
- Modify `X402_NETWORK` if deploying to mainnet

### 4. Configure AI Provider

To use Gaia Nodes instead of Ollama, set the following environment variables in your `.env` file:

```bash
AI_PROVIDER=gaia
GAIA_NODE_URL=https://your-node-id.gaia.domains/v1
GAIA_MODEL_NAME=Qwen3-30B-A3B-Q5_K_M
GAIA_API_KEY=your-gaia-api-key
```

### 5. Deploy to ROFL

Follow the [ROFL deployment guide](https://docs.oasis.io/build/tools/cli/rofl) to deploy your service:

```bash
# Build the container
docker compose build

# Push to registry (if needed)
docker tag docker.io/ptrusr/rofl-x402-docs:latest your-registry/your-app:latest
docker push your-registry/your-app:latest

# Deploy using oasis-cli
oasis rofl deploy
```

Your service will be deployed with verifiable code execution and ready to accept x402 payments!

## Learn More

- [Oasis ROFL](https://docs.oasis.io/rofl) - Runtime Off-chain Logic documentation
- [x402 Protocol](https://github.com/coinbase/x402) - Internet-native payment protocol
- [Ollama](https://ollama.com) - Run large language models locally
- [Gaia](https://gaianet.ai) - Decentralized AI inference network

## License

This is example code for demonstration purposes.
