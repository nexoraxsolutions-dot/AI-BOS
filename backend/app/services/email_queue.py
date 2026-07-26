"""
Email queue service using Redis lists.

Instead of sending emails synchronously during an HTTP request,
we push email tasks to a Redis list. A background worker process
pops tasks from the queue and sends them asynchronously.

This prevents the forgot-password endpoint from being slowed down
by SMTP latency and provides better resilience (emails can be retried).
"""
import json
import logging
from typing import Optional

from app.core.redis import get_redis_client

logger = logging.getLogger("ai_bos")

EMAIL_QUEUE_KEY = "email_queue"


async def enqueue_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
) -> bool:
    """
    Push an email task onto the Redis queue.

    Returns True if the task was queued successfully, False otherwise.
    The actual email sending happens asynchronously in the background worker.
    """
    try:
        client = await get_redis_client()
        task = {
            "to_email": to_email,
            "subject": subject,
            "html_content": html_content,
            "text_content": text_content,
        }
        serialized = json.dumps(task)
        await client.lpush(EMAIL_QUEUE_KEY, serialized)
        logger.info("Email queued for %s: %s", to_email, subject)
        return True
    except Exception as exc:
        logger.error("Failed to queue email for %s: %s", to_email, exc)
        return False


async def dequeue_email() -> Optional[dict]:
    """
    Pop an email task from the Redis queue (blocking).

    Returns the task dict or None if the queue is empty.
    This is used by the background worker process.
    """
    try:
        client = await get_redis_client()
        # Blocking pop with 1 second timeout
        result = await client.brpop(EMAIL_QUEUE_KEY, timeout=1)
        if result is None:
            return None
        _, serialized = result
        return json.loads(serialized)
    except Exception as exc:
        logger.error("Failed to dequeue email: %s", exc)
        return None


async def get_queue_length() -> int:
    """Get the number of pending emails in the queue."""
    try:
        client = await get_redis_client()
        return await client.llen(EMAIL_QUEUE_KEY)
    except Exception as exc:
        logger.error("Failed to get queue length: %s", exc)
        return 0