"""Check Registry dynamic discovery behavior."""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from dotenv import load_dotenv

from common.auth import auth_headers


EXPECTED_TASKS = ["legal_question", "tax_question", "compliance_question"]


async def main() -> None:
    load_dotenv()
    registry_url = os.getenv("REGISTRY_URL", "http://localhost:10000")
    async with httpx.AsyncClient(timeout=10.0, headers=auth_headers()) as client:
        health = await client.get(f"{registry_url}/health")
        health.raise_for_status()
        print(f"health: {health.json()}")

        for task in EXPECTED_TASKS:
            resp = await client.get(f"{registry_url}/discover/{task}")
            print(f"discover {task}: {resp.status_code} {resp.text}")

        missing = await client.get(f"{registry_url}/discover/not_a_real_task")
        print(f"discover not_a_real_task: {missing.status_code} {missing.text}")


if __name__ == "__main__":
    asyncio.run(main())
