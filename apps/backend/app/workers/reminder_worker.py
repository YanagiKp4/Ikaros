import logging
import time
from datetime import datetime, timezone

from apps.backend.app.core.config import (
    REMINDER_WORKER_BATCH_SIZE,
    REMINDER_WORKER_INTERVAL_SECONDS,
)
from apps.backend.app.workers.reminder_processor import (
    ReminderProcessor,
    create_worker_client,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger(__name__)


def run_worker():
    if REMINDER_WORKER_INTERVAL_SECONDS <= 0:
        raise ValueError("Reminder worker interval must be positive")

    client = create_worker_client()
    processor = ReminderProcessor(
        client,
        REMINDER_WORKER_BATCH_SIZE
    )

    logger.info(
        "Reminder worker started interval_seconds=%s batch_size=%s",
        REMINDER_WORKER_INTERVAL_SECONDS,
        REMINDER_WORKER_BATCH_SIZE
    )

    try:
        while True:
            cycle_started_at = datetime.now(timezone.utc)
            logger.info(
                "Reminder worker cycle started at=%s",
                cycle_started_at.isoformat()
            )

            processor.process_due_reminders(cycle_started_at)
            time.sleep(REMINDER_WORKER_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logger.info("Reminder worker shutting down")


if __name__ == "__main__":
    run_worker()
