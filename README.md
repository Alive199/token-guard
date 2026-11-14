# Token Guard — zkVerify Agent Games (Wildcard)

A small agent that screens a BSC token contract **before** you interact with
it. Give it a contract address, it returns a risk score (0–100), a verdict
(LOW / MEDIUM / HIGH RISK) and the reasons — from public data only.

## Why this agent

AI agents are starting to move real money: they approve transactions, swap
tokens, and sign on your behalf. Most of them do that on trust alone. Token
Guard is the check that runs *before* the signature — the same "verify
first" idea behind zkVerify's Agent Games, applied to the token you are
about to touch.

## How it works

`POST /check {"address": "0x..."}`

1. Asks a public BSC RPC whether contract code exists at the address.
2. Asks Dexscreener for the token's pairs, liquidity, 24h volume and
   buy/sell flow.
3. Deducts points for each red flag: no code, no pair, low liquidity,
   dead market, one-way selling, steep 24h drop.

## Run it

```sh
python3 guard.py            # listens on :8080 (set PORT to change)
curl -s -X POST localhost:8080/check -d '{"address":"0x..."}'
```

Standard library only — no dependencies, no API keys. The agent only reads
public data; it never signs, sends, or approves a transaction.

## Try it in the browser (no server needed)

`index.html` is the same checker as a static page: it runs the same
scoring logic in your browser, calling Dexscreener + BSC RPC directly.
Open it from any static host (e.g. GitHub Pages) and paste a contract
address — no install, no keys. See `demo.md` for a recorded live run:
WBNB scores 100 (LOW RISK), AMNC scores 60 (MEDIUM RISK, unlisted).

## Deploy

- **Static demo:** publish `index.html` on GitHub Pages / any static host.
- **API server:** run `guard.py` on any host with Python 3
  (Render, Railway, a VPS…) and point clients at `POST /check`.

## What it can and cannot do

- Can: give a fast first-pass risk read on any BSC token.
- Cannot: guarantee a token is safe, read closed source, or replace your
  own checks. Treat the score as a starting point, not financial advice.

## zkVerify relevance

The verdict Token Guard produces is exactly the kind of claim that should
be provable, not just asserted: "this check ran, on this contract, at this
time, and this was the result." Wiring that claim into a zkVerify proof is
the natural next step — the check becomes evidence anyone can verify,
instead of a log line only the agent's operator can see.
