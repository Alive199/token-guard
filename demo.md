# Token Guard — live demo transcript

Recorded 2026-11-14 ~21:10 WIB against the Python server (`python3 guard.py`, stdlib only) running on :8080.

## WBNB (listed, high liquidity)
```
$ curl -s -X POST localhost:8080/check -d '{"address":"0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"}'
{"address": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c", "score": 100, "verdict": "LOW RISK", "reasons": [], "pairs_found": 1, "disclaimer": "First-pass screener, not financial advice. Always verify the contract yourself."}
```

## AMNC (unlisted, no Dexscreener pair)
```
$ curl -s -X POST localhost:8080/check -d '{"address":"0x04efC2D45f9D6b06f3A517218F164d473f74CAdD"}'
{"address": "0x04efC2D45f9D6b06f3A517218F164d473f74CAdD", "score": 60, "verdict": "MEDIUM RISK", "reasons": ["No trading pair found on Dexscreener \u2014 token may be unlisted or untradeable."], "pairs_found": 0, "disclaimer": "First-pass screener, not financial advice. Always verify the contract yourself."}
```

## Health
```
{"status": "ok", "agent": "token-guard", "usage": "POST /check {\"address\": \"0x...\"}"}
```
