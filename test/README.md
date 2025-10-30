# Test Client

Test client for the x402 document summarization service demonstrating the full payment flow.

## Setup

1. Install dependencies:
```bash
cd test
uv sync
```

2. Get CDP API credentials:
   - Go to [Coinbase Developer Platform](https://portal.cdp.coinbase.com/)
   - Create an API key
   - Save your credentials

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your CDP API credentials
```

## Usage

Run the test client:

```bash
uv run python test_client.py
```

The client will:
1. Make a request to the protected endpoint
2. Receive a 402 Payment Required response
3. Use CDP SDK to make a payment on BASE Sepolia
4. Retry the request with the payment proof
5. Receive and display the document summary

## Configuration

Set the following in `.env`:

- `CDP_API_KEY_NAME`: Your CDP API key name
- `CDP_API_KEY_PRIVATE_KEY`: Your CDP API private key
- `API_URL`: The API endpoint (default: http://localhost:4021)
