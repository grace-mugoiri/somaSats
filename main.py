"""
Bitcoin Education Site — Lightning Backend
Stack: FastAPI + LND (via REST API)

Install:
  pip install fastapi uvicorn httpx python-dotenv

Run:
  uvicorn main:app --reload --port 8000

Requires a running LND node (local, Voltage, Umbrel, etc.)
Set env vars in a .env file (see below).
"""

from fastapi.responses import FileResponse
import os, hashlib, time, httpx, base64
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ── CONFIG ─────────────────────────────────────────────────────────────────
LND_REST_HOST   = os.getenv("LND_REST_HOST", "https://127.0.0.1:8080")
LND_MACAROON    = os.getenv("LND_MACAROON_HEX", "")   # hex-encoded admin.macaroon
LND_TLS_VERIFY  = os.getenv("LND_TLS_VERIFY", "false").lower() == "true"
UNLOCK_SAT_COST = int(os.getenv("UNLOCK_SAT_COST", "1"))    # sats to unlock concept 04
TIP_LNURL       = os.getenv("TIP_LNURL", "")                 # your LNURL for tip jar

# In-memory store (replace with Redis/DB in production)
paid_invoices: set[str] = set()   # payment_hashes of settled invoices
unlocked_ips:  set[str] = set()   # IPs that have unlocked concept 04 (demo only)

# ── APP ─────────────────────────────────────────────────────────────────────
app = FastAPI(title="Bitcoin Education — Lightning API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # restrict to your domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── LND HELPERS ─────────────────────────────────────────────────────────────
def lnd_headers() -> dict:
    return {"Grpc-Metadata-macaroon": LND_MACAROON}

async def lnd_get(path: str) -> dict:
    async with httpx.AsyncClient(verify=LND_TLS_VERIFY) as client:
        r = await client.get(f"{LND_REST_HOST}{path}", headers=lnd_headers(), timeout=10)
        r.raise_for_status()
        return r.json()

async def lnd_post(path: str, body: dict) -> dict:
    async with httpx.AsyncClient(verify=LND_TLS_VERIFY) as client:
        r = await client.post(f"{LND_REST_HOST}{path}", headers=lnd_headers(), json=body, timeout=10)
        r.raise_for_status()
        return r.json()

# ── MODELS ──────────────────────────────────────────────────────────────────
class InvoiceRequest(BaseModel):
    sats: int = 1
    memo: str = "Bitcoin Education"

class CheckPaymentRequest(BaseModel):
    payment_hash: str

# ── ROUTES ──────────────────────────────────────────────────────────────────

@app.get("/")
async def homepage():
    return FileResponse("index.html")

@app.get("/health")
async def health():
    """Check if backend + LND are reachable."""
    try:
        info = await lnd_get("/v1/getinfo")
        return {
            "status": "ok",
            "node_alias": info.get("alias", "unknown"),
            "block_height": info.get("block_height"),
            "num_active_channels": info.get("num_active_channels"),
        }
    except Exception as e:
        raise HTTPException(502, f"LND unreachable: {e}")


@app.post("/invoice/create")
async def create_invoice(req: InvoiceRequest):
    """
    Create a Lightning invoice via LND.
    Returns a BOLT11 payment request the frontend displays as a QR code.
    """
    if req.sats < 1:
        raise HTTPException(400, "Minimum 1 sat")

    try:
        data = await lnd_post("/v1/invoices", {
            "value": req.sats,
            "memo": req.memo,
            "expiry": 600,          # 10 minutes
        })
        return {
            "payment_request": data["payment_request"],   # BOLT11 invoice string
            "payment_hash":    data["r_hash"],             # use to check settlement
            "expires_in":      600,
            "sats":            req.sats,
        }
    except httpx.HTTPStatusError as e:
        raise HTTPException(500, f"LND error: {e.response.text}")


@app.post("/invoice/check")
async def check_invoice(req: CheckPaymentRequest):
    """
    Poll this endpoint after showing the QR code.
    Returns { paid: true } once settled so the frontend can unlock content.
    """
    try:
        # LND expects base64-encoded r_hash for lookup
        ph_b64 = base64.urlsafe_b64encode(
            bytes.fromhex(req.payment_hash)
        ).decode().rstrip("=")

        data = await lnd_get(f"/v1/invoice/{ph_b64}")
        settled = data.get("state") == "SETTLED"

        if settled:
            paid_invoices.add(req.payment_hash)

        return {"paid": settled, "state": data.get("state")}
    except Exception as e:
        raise HTTPException(500, f"Check failed: {e}")


@app.post("/unlock/concept")
async def unlock_concept(payment_hash: str, concept_id: int = 4):
    """
    After a verified payment, mark a concept as unlocked.
    concept_id 4 = Self-Custody (the locked card).
    """
    if payment_hash not in paid_invoices:
        # Double-check with LND directly
        check = await check_invoice(CheckPaymentRequest(payment_hash=payment_hash))
        if not check["paid"]:
            raise HTTPException(402, "Payment not confirmed yet")

    # In production: store in DB keyed by session/user
    return {"unlocked": True, "concept_id": concept_id, "message": "Not your keys, not your coins. Now you know why."}


@app.get("/lnurl/tip")
async def tip_lnurl():
    """Return the LNURL for the tip jar section."""
    return {"lnurl": TIP_LNURL, "label": "Support Bitcoin Education"}


# ── PAYMENT CHANNEL SIMULATOR DATA ──────────────────────────────────────────

class ChannelState(BaseModel):
    balance_a: int = 50000
    balance_b: int = 50000
    send_sats: int = 1000

@app.post("/simulate/payment")
async def simulate_payment(state: ChannelState):
    """
    Simulate a Lightning channel payment — no real LND needed.
    Used by the frontend demo. In production this is all off-chain.
    """
    if state.send_sats > state.balance_a:
        raise HTTPException(400, "Insufficient channel balance")

    new_a = state.balance_a - state.send_sats
    new_b = state.balance_b + state.send_sats
    latency_ms = round(100 + (hash(str(time.time())) % 400))  # fake 100-500ms

    return {
        "success": True,
        "balance_a": new_a,
        "balance_b": new_b,
        "latency_ms": latency_ms,
        "fee_sats": 0,
        "log": f"⚡ Routed {state.send_sats:,} sats in {latency_ms}ms — zero on-chain fees",
    }


# ── MAIN ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)