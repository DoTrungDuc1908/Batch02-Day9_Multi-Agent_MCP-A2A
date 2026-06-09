"""A2A delegation helper with trace propagation, optional auth, and retries."""

from __future__ import annotations

import asyncio
import logging
import os
from uuid import uuid4

import httpx

from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    TextPart,
)
from common.auth import auth_headers

logger = logging.getLogger(__name__)


async def delegate(
    endpoint: str,
    question: str,
    context_id: str,
    trace_id: str,
    depth: int,
) -> str:
    """Send a question to an A2A agent and return its text response."""
    attempts = max(1, int(os.getenv("A2A_RETRY_ATTEMPTS", "3")))
    delay = float(os.getenv("A2A_RETRY_INITIAL_DELAY", "0.5"))
    last_exc: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            return await _delegate_once(endpoint, question, context_id, trace_id, depth)
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            last_exc = exc
            if attempt >= attempts:
                break
            logger.warning(
                "A2A delegate attempt %d/%d to %s failed: %s; retrying in %.1fs",
                attempt,
                attempts,
                endpoint,
                exc,
                delay,
            )
            await asyncio.sleep(delay)
            delay *= 2

    assert last_exc is not None
    raise last_exc


async def _delegate_once(
    endpoint: str,
    question: str,
    context_id: str,
    trace_id: str,
    depth: int,
) -> str:
    async with httpx.AsyncClient(timeout=300.0, headers=auth_headers()) as http_client:
        card_resp = await http_client.get(f"{endpoint}/.well-known/agent.json")
        card_resp.raise_for_status()
        agent_card = AgentCard.model_validate(card_resp.json())

        client = A2AClient(httpx_client=http_client, agent_card=agent_card)
        message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=question))],
            message_id=str(uuid4()),
            context_id=context_id,
            metadata={
                "trace_id": trace_id,
                "context_id": context_id,
                "delegation_depth": depth,
            },
        )
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(message=message),
        )

        logger.debug("Delegating to %s (depth=%d, trace=%s)", endpoint, depth, trace_id)
        response = await client.send_message(request)
        return _extract_text(response)


def _extract_text(response: object) -> str:
    """Walk the response tree and collect all TextPart.text values."""
    text = ""

    if hasattr(response, "root"):
        response = response.root

    result = getattr(response, "result", None)
    if result is None:
        return text

    artifacts = getattr(result, "artifacts", None)
    if artifacts:
        for artifact in artifacts:
            for part in getattr(artifact, "parts", []) or []:
                text += _part_text(part)
        if text:
            return text

    parts = getattr(result, "parts", None)
    if parts:
        for part in parts:
            text += _part_text(part)

    if not text:
        history = getattr(result, "history", None)
        if history:
            for msg in history:
                for part in getattr(msg, "parts", []) or []:
                    text += _part_text(part)

    status = getattr(result, "status", None)
    status_message = getattr(status, "message", None)
    if not text and status_message is not None:
        for part in getattr(status_message, "parts", []) or []:
            text += _part_text(part)

    return text


def _part_text(part: object) -> str:
    """Extract text from a Part object or raw TextPart."""
    inner = getattr(part, "root", part)
    return getattr(inner, "text", "") or ""
