# ₿ITCOIN 101 — Lightning-Native Education Site

## Stack
- **Frontend**: Vanilla HTML/CSS/JS (no build step needed)
- **Backend**: Python + FastAPI
- **Lightning**: LND via REST API

## Structure
```
bitcoin-site/
├── index.html          ← The full frontend (self-contained)
└── backend/
    ├── main.py         ← FastAPI + LND integration
    └── .env.example    ← Rename to .env and fill in your LND details
```

## Frontend Features
- Witty, educational Bitcoin content (5 core concepts)
- One concept locked behind a 1-sat Lightning paywall
- Lightning channel simulator (interactive demo)
- Mock invoice generator (wire up to backend for real invoices)
- Bitcoin quiz (5 questions)
- Tip jar with LNURL + sat amount buttons
- Copy-to-clipboard LNURL

## Backend API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Check LND connectivity |
| POST | /invoice/create | Generate a BOLT11 invoice |
| POST | /invoice/check | Check if invoice is paid |
| POST | /unlock/concept | Unlock a concept after payment |
| GET | /lnurl/tip | Return LNURL for tip jar |
| POST | /simulate/payment | Channel simulator (no LND needed) |

## Setup

### 1. Backend
```bash
cd backend
cp .env.example .env
# Edit .env with your LND node details

pip install fastapi uvicorn httpx python-dotenv
uvicorn main:app --reload --port 8000
```

### 2. Connect Frontend to Backend
In `index.html`, replace the mock invoice generator with:
```javascript
const res = await fetch('http://localhost:8000/invoice/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ sats: 1, memo: 'Unlock Concept 04' })
});
const { payment_request, payment_hash } = await res.json();
// Show payment_request as QR code
// Poll /invoice/check every 2s with payment_hash
```

### 3. Polling for Payment
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

## LND Node Options
- **Umbrel** (self-hosted, easy): https://umbrel.com
- **Voltage** (cloud, managed): https://voltage.cloud
- **Start9** (self-hosted): https://start9.com
- **Raspiblitz** (DIY, Raspberry Pi): https://raspiblitz.org

## Deploying
Frontend: Any static host (Netlify, Vercel, Render, Cloudflare Pages)
Backend: Railway, Render, Fly.io, or your own server

## Notes
- The 1-sat paywall is intentional UX — it proves Lightning works and creates a micro-commitment
- For production: replace the in-memory `paid_invoices` set with Redis or a DB
- TLS: LND uses a self-signed cert by default — set `LND_TLS_VERIFY=false` for local dev
