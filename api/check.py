"""Token Guard as a Vercel serverless function.

POST /api/check {"address": "0x..."} -> JSON risk brief (score 0-100 + reasons).
Self-contained copy of the scoring logic from guard.py (stdlib only),
so the function runs without importing anything from the repo root.
"""
import json
import re
import urllib.request
from http.server import BaseHTTPRequestHandler

BSC_RPCS = [
    "https://bsc-dataseed2.defibit.io/",
    "https://bsc-dataseed1.binance.org/",
    "https://bsc.publicnode.com/",
]
DEX_URL = "https://api.dexscreener.com/tokens/v1/bsc/{}"
ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


def http_get_json(url, timeout=5):
    req = urllib.request.Request(url, headers={"User-Agent": "token-guard/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def rpc_call(method, params):
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode()
    last_error = None
    for url in BSC_RPCS:
        for _attempt in range(2):
            req = urllib.request.Request(
                url, data=body,
                headers={"Content-Type": "application/json",
                         "User-Agent": "token-guard/1.0"},
            )
            try:
                with urllib.request.urlopen(req, timeout=3) as r:
                    return json.loads(r.read().decode("utf-8"))
            except Exception as e:
                last_error = e
    raise RuntimeError(f"all BSC RPC endpoints failed ({last_error})")


def check_token(address):
    reasons = []
    score = 100

    try:
        code = rpc_call("eth_getCode", [address, "latest"]).get("result", "0x")
        has_code = code not in ("0x", "0x0", "")
    except Exception as e:
        has_code = None
        reasons.append(f"Could not reach BSC RPC to verify contract code ({e}).")
        score -= 10
    if has_code is False:
        reasons.append("No contract code at this address on BSC — it is not a token contract.")
        score -= 60

    pairs = []
    try:
        pairs = http_get_json(DEX_URL.format(address)) or []
    except Exception as e:
        reasons.append(f"Dexscreener lookup failed ({e}); market data unknown.")
        score -= 10
    if not pairs:
        reasons.append("No trading pair found on Dexscreener — token may be unlisted or untradeable.")
        score -= 40
    else:
        best = max(pairs, key=lambda p: (p.get("liquidity") or {}).get("usd", 0))
        liq = (best.get("liquidity") or {}).get("usd", 0)
        vol24 = (best.get("volume") or {}).get("h24", 0)
        txns = (best.get("txns") or {}).get("h24", {})
        buys = txns.get("buys") or 0
        sells = txns.get("sells") or 0
        change24 = (best.get("priceChange") or {}).get("h24")
        if liq < 1000:
            reasons.append(f"Very low liquidity (${liq:,.0f}) — easy to manipulate, hard to exit.")
            score -= 25
        elif liq < 10000:
            reasons.append(f"Low liquidity (${liq:,.0f}).")
            score -= 10
        if buys + sells == 0:
            reasons.append("Zero trades in the last 24h — market looks dead.")
            score -= 15
        if change24 is not None and change24 <= -90:
            reasons.append(f"Price down {change24:.0f}% in 24h.")
            score -= 15
        if sells and buys == 0:
            reasons.append("Only sells in the last 24h, no buys — possible one-way exit.")
            score -= 15

    score = max(0, min(100, score))
    verdict = (
        "LOW RISK" if score >= 75 else
        "MEDIUM RISK" if score >= 45 else
        "HIGH RISK"
    )
    return {
        "address": address,
        "score": score,
        "verdict": verdict,
        "reasons": reasons,
        "pairs_found": len(pairs),
        "disclaimer": "First-pass screener, not financial advice. Always verify the contract yourself.",
    }


class handler(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._json(200, {"status": "ok", "agent": "token-guard",
                         "usage": 'POST /api/check {"address": "0x..."}'})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self._json(400, {"error": "invalid JSON body"})
            return
        address = (body.get("address") or "").strip()
        if not ADDR_RE.match(address):
            self._json(400, {"error": "address must be a 0x-prefixed 40-hex BSC address"})
            return
        try:
            self._json(200, check_token(address))
        except Exception as e:
            self._json(502, {"error": f"upstream check failed: {e}"})

    def log_message(self, *args):
        pass
