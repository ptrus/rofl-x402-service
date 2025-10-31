# ROFL x402 Document Summarization Service

A confidential AI microservice that summarizes documents inside a verifiable TEE, paid via x402 micropayments.

- **🔒 Private**: Documents processed inside a confidential ROFL container using Ollama (qwen2:0.5b) or Gaia Nodes
- **🔐 Secure**: Uses [zkTLS](https://oasis.net/blog/zktls-blockchain-security) with end-to-end TLS authentication
- **✅ Verifiable**: Remote attestation proves the exact code running in the TEE
- **💰 Monetizable**: x402 micropayments - $0.001 per summary on Base Sepolia (testnet)

**Tech Stack**
- Python FastAPI backend
- Ollama (Qwen2 0.5B model) or Gaia Nodes (OpenAI compatible API)
- x402 protocol for micropayments
- Runs in a ROFL TEE on the Oasis Network

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
2. **Gaia Nodes** - Cloud-based inference with OpenAI compatible API

To switch between providers, set the `AI_PROVIDER` environment variable:

```bash
# Use Ollama (default)
AI_PROVIDER=ollama

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