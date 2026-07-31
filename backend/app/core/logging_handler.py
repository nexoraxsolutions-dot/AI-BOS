"""Database log handler for persisting application logs.

Provides a logging.Handler subclass that writes structured log records
to the database via the LogEntry model.  This enables administrators
to review historical application/system logs through the REST API and
frontend UI.

The handler is designed to be safe for production use:
- Errors during database writes are caught and logged to the standard
  logger to avoid breaking the application.
- The handler uses a lightweight synchronous write because Python's
  logging module is synchronous by nature.
- Log level filtering is configurable.
"""
import logging
from datetime import datetime
from typing import Optional

from app.models.logging_history import LogEntry


class DatabaseLogHandler(logging.Handler):
    """A logging handler that persists log records to the database.

    Usage::

        from app.core.logging_handler import DatabaseLogHandler
        handler = DatabaseLogHandler()
        handler.setLevel(logging.INFO)
        logging.getLogger("ai_bos").addHandler(handler)

    The handler creates its own database session for each record to
    avoid sharing sessions across threads/contexts.
    """

    def __init__(self, level: int = logging.NOTSET):
        super().__init__(level=level)
        self._logger = logging.getLogger("ai_bos")

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to the database.

        This method is called by the logging framework for each record
        that passes the handler's level filter.  Any errors are caught
        and logged to avoid disrupting the application.
        """
        try:
            # Import locally to avoid circular imports at module load time
            from app.db import AsyncSessionLocal

            # Build the log entry from the record
            entry = LogEntry(
                level=record.levelname,
                logger_name=record.name,
                message=self._format_message(record),
                module=record.module,
                func_name=record.funcName,
                line_no=record.lineno,
                pathname=record.pathname,
                thread_name=record.threadName,
                process=str(record.process),
                timestamp=datetime.utcfromtimestamp(record.created),
            )

            # Attach extra context if available
            if hasattr(record, "user_id"):
                entry.user_id = record.user_id
            if hasattr(record, "ip_address"):
                entry.ip_address = record.ip_address
            if hasattr(record, "user_agent"):
                entry.user_agent = record.user_agent

            # Persist synchronously using a dedicated session
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're inside an async context — schedule the write
                    asyncio.ensure_future(self._save_entry(entry))
                else:
                    asyncio.run(self._save_entry(entry))
            except RuntimeError:
                # Fallback: try to run in a new event loop
                asyncio.run(self._save_entry(entry))

        except Exception as exc:
            # Never let logging errors propagate
            self._logger.error("Failed to write log entry to database: %s", exc)

    async def _save_entry(self, entry: LogEntry) -> None:
        """Save a LogEntry to the database using an async session."""
        from app.db import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            session.add(entry)
            await session.commit()

    def _format_message(self, record: logging.LogRecord) -> str:
        """Format the log message, including any args."""
        try:
            if record.args:
                return record.msg % record.args
            return str(record.msg)
        except Exception:
            return str(record.msg)


def setup_database_logging(level: int = logging.INFO) -> DatabaseLogHandler:
    """Create and configure a DatabaseLogHandler.

    Args:
        level: The minimum log level to capture (default: INFO)

    Returns:
        The configured DatabaseLogHandler instance
    """
    handler = DatabaseLogHandler(level=level)
    handler.setFormatter(logging.Formatter("%(message)s"))
    return handler
