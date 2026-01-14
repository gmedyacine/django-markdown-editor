
# proxy.py
import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response

UPSTREAM = os.getenv("PHOENIX_UPSTREAM", "http://127.0.0.1:8899").rstrip("/")
ALT_HEADER = os.getenv("PHOENIX_ALT_AUTH_HEADER", "x-phoenix-api-key").lower()
FALLBACK_HEADER = "api_key"  # au cas où tu préfères ce nom côté client

app = FastAPI()

def _get_api_key(req: Request) -> str | None:
    h = req.headers
    return h.get(ALT_HEADER) or h.get(FALLBACK_HEADER)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy(path: str, request: Request):
    # Build target URL
    url = f"{UPSTREAM}/{path}"

    # Body
    body = await request.body()

    # Copy headers (remove hop-by-hop / host)
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)

    # Rebuild Authorization for Phoenix
    api_key = _get_api_key(request)
    if api_key:
        headers["authorization"] = f"Bearer {api_key}"

    # Forward
    async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
        resp = await client.request(
            method=request.method,
            url=url,
            params=dict(request.query_params),
            headers=headers,
            content=body,
        )

    # Return response (filter a couple of headers)
    excluded = {"transfer-encoding", "connection", "content-encoding"}
    out_headers = {k: v for k, v in resp.headers.items() if k.lower() not in excluded}

    return Response(content=resp.content, status_code=resp.status_code, headers=out_headers)
