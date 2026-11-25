#!/usr/bin/env python3
"""
Standalone latency benchmark for old vs new OHLCV API endpoints.

Usage:
    python3 benchmark.py

Prerequisites:
    - uvicorn server running on localhost:8080
    - .env file with API_KEY

This script is NOT imported by any production code.
"""

import asyncio
import os
import time
import statistics
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "")
BASE_URL = "http://localhost:8080"
ITERATIONS = 5
TIMEOUT_S = 30

TEST_PAIRS = [
    {
        "label": "Historical single ticker (US stock)",
        "old": "/ohlcv/?tickers=AAPL&year=2026&per_page=10",
        "new": "/ohlcv/?tickers=AAPL.US&year=2026&per_page=10",
    },
    {
        "label": "Historical exchange filter (UK stocks)",
        "old": "/uk/?per_page=10",
        "new": "/ohlcv/?exchange=LSE&year=2026&per_page=10",
    },
    {
        "label": "Single latest close (UK stock)",
        "old": "/uk/latest_close/BP",
        "new": "/ohlcv/latest_close/BP.LSE",
    },
    {
        "label": "Batch latest close (2 US tickers)",
        "old": "/ohlcv/latest_close/?tickers=AAPL,MSFT",
        "new": "/ohlcv/latest_close/?tickers=AAPL.US,MSFT.US",
    },
    {
        "label": "Crypto top 100 by volume",
        "old": "/crypto/top100/",
        "new": "/ohlcv/latest_close/?asset_type=Cryptocurrencies&sort_by=volume&per_page=100",
    },
    {
        "label": "Historical crypto filter",
        "old": "/crypto/?per_page=10",
        "new": "/ohlcv/?asset_type=Cryptocurrencies&year=2026&per_page=10",
    },
    {
        "label": "OHLCV stats (US stock)",
        "old": "/ohlcv/stats/AAPL",
        "new": "/ohlcv/stats/AAPL.US?start_date=2026-01-01",
    },
    {
        "label": "Single latest close (forex)",
        "old": "/fx/latest_close/EURUSD",
        "new": "/ohlcv/latest_close/EURUSD.FOREX",
    },
    {
        "label": "Batch latest close (all UK tickers)",
        "old": "/uk/latest_close/",
        "new": "/ohlcv/latest_close/?exchange=LSE",
    },
    {
        "label": "Asset metadata lookup (AAPL)",
        "old": "/assets/AAPL",
        "new": "/assets/AAPL",
    },
]


async def bench(client: httpx.AsyncClient, path: str) -> tuple[float, float, float]:
    url = f"{BASE_URL}{path}"
    sep = "&" if "?" in path else "?"
    url = f"{url}{sep}api_key={API_KEY}"

    times: list[float] = []
    for i in range(ITERATIONS):
        t0 = time.perf_counter()
        resp = await client.get(url, timeout=TIMEOUT_S)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        if resp.status_code != 200:
            print(f"    WARNING: {resp.status_code} on {path}")
        times.append(elapsed_ms)

    warm = times[1:]
    return statistics.mean(warm), min(warm), max(warm)


async def main():
    print("=" * 90)
    print("OHLCV API Latency Benchmark — Old vs New Endpoints")
    print(f"Server: {BASE_URL}  |  Iterations: {ITERATIONS} (1 cold discarded)  |  API Key: {'✓' if API_KEY else '✗'}")
    print("=" * 90)

    async with httpx.AsyncClient() as client:
        for pair in TEST_PAIRS:
            label = pair["label"]
            print(f"\n── {label} ──")

            old_avg, old_min, old_max = await bench(client, pair["old"])
            print(f"  OLD: {pair['old'][:70]}")
            print(f"       avg={old_avg:8.1f}ms  min={old_min:8.1f}ms  max={old_max:8.1f}ms")

            new_avg, new_min, new_max = await bench(client, pair["new"])
            print(f"  NEW: {pair['new'][:70]}")
            print(f"       avg={new_avg:8.1f}ms  min={new_min:8.1f}ms  max={new_max:8.1f}ms")

            if new_avg < old_avg:
                pct = ((old_avg - new_avg) / old_avg) * 100
                print(f"       ↓ NEW is {pct:.0f}% faster")
            elif old_avg < new_avg:
                pct = ((new_avg - old_avg) / new_avg) * 100
                print(f"       ↑ OLD is {pct:.0f}% faster")
            else:
                print(f"       = Same speed")

    print("\n" + "=" * 90)
    print("Benchmark complete.")
    print("=" * 90)


if __name__ == "__main__":
    asyncio.run(main())
