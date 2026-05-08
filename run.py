"""
Launcher for the AI Underwriting API server.

Use this instead of invoking uvicorn directly on Windows.
psycopg3 async requires SelectorEventLoop, but Python 3.8+ defaults to
ProactorEventLoop on Windows. Setting the policy here — before uvicorn
creates its event loop — is the only reliable fix.
"""
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
    )
