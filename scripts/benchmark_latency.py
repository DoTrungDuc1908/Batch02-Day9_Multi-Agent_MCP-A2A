"""Benchmark end-to-end Customer Agent latency.

Run with all services already started:
    py scripts/benchmark_latency.py --runs 3

To compare routing modes, restart services with FAST_ROUTING=false, run this
script, then restart with FAST_ROUTING=true and run it again.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import statistics
import time
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from a2a.client import A2AClient
from a2a.types import AgentCard, Message, Part, Role, SendMessageRequest, TextPart
from a2a.types import MessageSendParams as MSP
from dotenv import load_dotenv

from common.auth import auth_headers


DEFAULT_QUESTION = (
    "If a company breaks a contract, avoids taxes, and leaks customer data, "
    "what are the legal, tax, privacy, and regulatory consequences?"
)


def extract_text(response: object) -> str:
    if hasattr(response, "root"):
        response = response.root
    result = getattr(response, "result", None)
    if result is None:
        return ""

    for container_name in ("artifacts", "parts"):
        container = getattr(result, container_name, None)
        if not container:
            continue
        items = container
        if container_name == "artifacts":
            items = [part for artifact in container for part in artifact.parts]
        text = "".join(getattr(getattr(part, "root", part), "text", "") for part in items)
        if text:
            return text

    status = getattr(result, "status", None)
    message = getattr(status, "message", None)
    if message:
        return "".join(
            getattr(getattr(part, "root", part), "text", "")
            for part in getattr(message, "parts", []) or []
        )
    return ""


async def run_once(url: str, question: str) -> tuple[float, str]:
    async with httpx.AsyncClient(timeout=300.0, headers=auth_headers()) as http_client:
        card_resp = await http_client.get(f"{url}/.well-known/agent.json")
        card_resp.raise_for_status()
        client = A2AClient(
            httpx_client=http_client,
            agent_card=AgentCard.model_validate(card_resp.json()),
        )
        message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=question))],
            message_id=str(uuid4()),
        )
        request = SendMessageRequest(id=str(uuid4()), params=MSP(message=message))

        started = time.perf_counter()
        response = await client.send_message(request)
        elapsed = time.perf_counter() - started
        return elapsed, extract_text(response)


async def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:10100")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    timings: list[float] = []
    for index in range(1, args.runs + 1):
        elapsed, text = await run_once(args.url, args.question)
        timings.append(elapsed)
        status = "ok" if text and "failed:" not in text.lower() else "check-output"
        print(f"run={index} latency={elapsed:.2f}s status={status} chars={len(text)}")

    print("-" * 60)
    print(f"runs={len(timings)}")
    print(f"min={min(timings):.2f}s")
    print(f"avg={statistics.mean(timings):.2f}s")
    print(f"max={max(timings):.2f}s")
    if len(timings) > 1:
        print(f"stdev={statistics.stdev(timings):.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
