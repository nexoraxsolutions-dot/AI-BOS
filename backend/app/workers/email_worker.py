"""
Background worker that processes the email queue.

This script runs as a standalone process that continuously polls
the Redis email queue and sends emails asynchronously.

Usage:
    python -m app.workers.email_worker
"""
import asyncio
import logging

from app.services.email import send_email
from app.services.email_queue import dequeue_email, get_queue_length

logger = logging.getLogger("ai_bos")


async def process_email_task(task: dict) -> bool:
    """Process a single email task from the queue."""
    try:
        to_email = task["to_email"]
        subject = task["subject"]
        html_content = task["html_content"]
        text_content = task.get("text_content")

        success = await send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

        if success:
            logger.info("Email sent to %s: %s", to_email, subject)
        else:
            logger.error("Failed to send email to %s: %s", to_email, subject)

        return success
    except Exception as exc:
        logger.error("Error processing email task: %s", exc)
        return False


async def run_worker():
    """Main worker loop — continuously polls the queue and processes tasks."""
    logger.info("Email worker started. Waiting for tasks...")

    while True:
        try:
            task = await dequeue_email()
            if task is None:
                # No tasks in queue, sleep briefly before polling again
                await asyncio.sleep(1)
                continue

            await process_email_task(task)
        except asyncio.CancelledError:
            logger.info("Email worker shutting down...")
            break
        except Exception as exc:
            logger.error("Unexpected error in email worker: %s", exc)
            await asyncio.sleep(5)


async def main():
    """Entry point for the email worker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    queue_length = await get_queue_length()
    logger.info("Initial queue length: %d", queue_length)

    await run_worker()


if __name__ == "__main__":
    asyncio.run(main())