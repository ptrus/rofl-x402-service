# ROFL x402 Document Summarization Service

A confidential AI microservice that summarizes documents inside a verifiable TEE, paid via x402 micropayments.

- **🔒 Private**: Documents processed inside a confidential ROFL container using Ollama (qwen2:0.5b)
- **🔐 Secure**: Uses [zkTLS](https://oasis.net/blog/zktls-blockchain-security) with end-to-end TLS authentication
- **✅ Verifiable**: Remote attestation proves the exact code running in the TEE
- **💰 Monetizable**: x402 micropayments - $0.001 per summary on Base Sepolia (testnet)

**Tech Stack**
- Python FastAPI backend
- Ollama (Qwen2 0.5B model)
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
# - ETH for gas: https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet
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
✅ Success! Received summary:

📄 Summary:
   ZkTLS is combining two cryptographic approaches - TLS for secure HTTPS
   communication and zk-SNARK circuit-based verification of data authenticity...

📊 Stats:
   Word count: 304
   Reading time: 1 minute
```

Testing with [zkTLS article](https://oasis.net/blog/zktls-blockchain-security) (2,362 characters).

## Try the Live Testnet Deployment

**Live service running on Oasis Testnet** at **https://summary.updev.si** ([App ID: `rofl1qq6m08wlj3qawcfrd3ljyge2t0praed5ycwh7upg`](https://explorer.oasis.io/testnet/sapphire/rofl/app/rofl1qq6m08wlj3qawcfrd3ljyge2t0praed5ycwh7upg))

Test the live deployment with:

```bash
cd test
echo "API_URL=https://summary.updev.si" >> .env
uv run python test_client.py
```

**Example output (testnet):**

```
✅ Success! Received summary:

📄 Summary:
   ZkTLS is combining two cryptographic approaches - TLS for secure HTTPS
   communication and zk-SNARK circuit-based verification...

📊 Stats:
   Word count: 304
   Reading time: 1 minute

💳 Payment Details:
   Transaction: 0x68ef147a3f205412b890211b855dd78c00cb9c047eb0d4924ea2a9283bea0a2f
   Network: base-sepolia
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

### 4. Deploy to ROFL

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

## License

This is example code for demonstration purposes.
