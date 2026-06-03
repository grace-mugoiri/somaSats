# ₿ITCOIN 101 — Lightning-Native Education Site

> **This project is purely for learning and educational purposes.** It is not financial advice, not a financial product, and not affiliated with any Bitcoin organisation. It exists to make Bitcoin concepts accessible to curious people everywhere.

## Stack
- **Frontend**: Vanilla HTML/CSS/JS (no build step needed)
- **Backend**: Python + FastAPI
- **Lightning**: LND via REST API
- **Deployed on**: Render

## Structure
```
bitcoin-site/
├── index.html          ← Full frontend (self-contained, no build step)
├── app.py              ← FastAPI backend + LND integration
├── requirements.txt    ← Python dependencies
└── .env.example        ← Rename to .env and fill in your LND details
```

## What This Teaches
- Why Bitcoin has a fixed supply and why that matters
- How the blockchain works (without the hype)
- What Proof of Work actually does
- The halving schedule and why it's significant
- Self-custody: why "not your keys, not your coins" is not a slogan
- How Lightning Network payment channels work
- What a real BOLT11 invoice looks like

## Frontend Features
- Witty, educational Bitcoin content — 4 core concepts
- One concept locked behind a 1-sat Lightning paywall (demo-able without real LND)
- Interactive Lightning channel simulator — drag, send, watch balances shift
- Mock BOLT11 invoice generator (wire to real LND node for production)
- Bitcoin quiz — 5 questions with real explanations
- Tip jar with LNURL + sat amount buttons
- Fully responsive — mobile, tablet, desktop

## Backend API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serves the frontend (`index.html`) |
| GET | `/health` | Check LND node connectivity |
| POST | `/invoice/create` | Generate a real BOLT11 invoice via LND |
| POST | `/invoice/check` | Check if an invoice has been paid |
| POST | `/unlock/concept` | Gate content unlock behind confirmed payment |
| GET | `/lnurl/tip` | Return LNURL for the tip jar |
| POST | `/simulate/payment` | Channel simulator (no LND node required) |

## Setup

### 1. Clone & install
```bash
git clone <your-repo>
cd bitcoin-site

pip install fastapi uvicorn httpx python-dotenv gunicorn
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your LND node details
```

### 3. Run locally
```bash
uvicorn app:app --reload --port 8000
```

### 4. Connect frontend to real LND invoices
In `index.html`, replace the mock invoice generator with a real fetch:
```javascript
const res = await fetch('/invoice/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ sats: 1, memo: 'Unlock Concept 04' })
});
const { payment_request, payment_hash } = await res.json();
// Render payment_request as a QR code
// Poll /invoice/check every 2s with payment_hash
```

### 5. Poll for payment confirmation
```javascript
async function pollPayment(payment_hash, onPaid) {
  const interval = setInterval(async () => {
    const res = await fetch('/invoice/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ payment_hash })
    });
    const { paid } = await res.json();
    if (paid) {
      clearInterval(interval);
      onPaid();
    }
  }, 2000);
}
```

## Deploying to Render
1. Push repo to GitHub
2. Create a new **Web Service** on Render, connect your repo
3. Set **Start Command** to:
   ```
   python -m uvicorn app:app --host 0.0.0.0 --port $PORT
   ```
4. Add your environment variables from `.env` in Render → Environment
5. Deploy — done

## LND Node Options
If you want real Lightning payments (not just the demo):
- **Umbrel** (self-hosted, beginner-friendly): https://umbrel.com
- **Voltage** (cloud-hosted, managed): https://voltage.cloud
- **Start9** (self-hosted, privacy-focused): https://start9.com
- **Raspiblitz** (DIY on Raspberry Pi): https://raspiblitz.org

## Production Notes
- Replace the in-memory `paid_invoices` set with Redis or a proper DB
- Set `LND_TLS_VERIFY=false` for self-signed certs (default on most home nodes)
- Restrict `allow_origins` in CORS middleware to your actual domain
- The 1-sat paywall is intentional UX — it proves Lightning works in real life and creates a micro-commitment from the learner

## Disclaimer
This site is an educational resource. Nothing here is financial advice. Do your own research. Don't trust, verify.