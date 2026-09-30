import logging
from datetime import datetime, timezone

from supabase import Client, create_client

from apps.backend.app.core.config import (
    SUPABASE_URL,
    SUPABASE_WORKER_KEY,
)


logger = logging.getLogger(__name__)


def create_worker_client() -> Client:
    if not SUPABASE_WORKER_KEY:
        raise RuntimeError(
            "SUPABASE_WORKER_KEY is required to run the reminder worker"
        )

    return create_client(
        SUPABASE_URL,
        SUPABASE_WORKER_KEY
    )


class ReminderProcessor:
    def __init__(self, client: Client, batch_size: int):
        if batch_size <= 0:
            raise ValueError("Reminder worker batch size must be positive")

        self.client = client
        self.batch_size = batch_size

    def get_due_reminders(self, now: datetime):
        response = (
            self.client
            .table("reminders")
            .select("id, task_id, remind_at, status, channel")
            .eq("status", "pending")
            .lte("remind_at", now.isoformat())
            .order("remind_at")
            .limit(self.batch_size)
            .execute()
        )

        return response.data

    def claim_reminder(self, reminder_id: str, now: datetime) -> bool:
        response = (
            self.client
            .table("reminders")
            .update({"status": "processing"})
            .eq("id", reminder_id)
            .eq("status", "pending")
            .lte("remind_at", now.isoformat())
            .select("id")
            .execute()
        )

        return bool(response.data)

    def transition_status(
        self,
        reminder_id: str,
        expected_status: str,
        new_status: str
    ) -> bool:
        response = (
            self.client
            .table("reminders")
            .update({"status": new_status})
            .eq("id", reminder_id)
            .eq("status", expected_status)
            .select("id")
            .execute()
        )

        return bool(response.data)

    def process_reminder(self, reminder: dict):
        logger.info(
            "Simulating reminder processing reminder_id=%s task_id=%s channel=%s",
            reminder["id"],
            reminder["task_id"],
            reminder["channel"]
        )

    def process_due_reminders(self, now: datetime | None = None) -> int:
        current_time = now or datetime.now(timezone.utc)

        try:
            reminders = self.get_due_reminders(current_time)
        except Exception:
            logger.exception("Failed to fetch due reminders")
            return 0

        logger.info("Due reminders found count=%s", len(reminders))
        processed_count = 0

        for reminder in reminders:
            reminder_id = reminder["id"]

            try:
                claimed = self.claim_reminder(reminder_id, current_time)
            except Exception:
                logger.exception(
                    "Failed to claim reminder reminder_id=%s",
                    reminder_id
                )
                continue

            if not claimed:
                logger.info(
                    "Reminder was claimed by another worker reminder_id=%s",
                    reminder_id
                )
                continue

            logger.info("Reminder claimed reminder_id=%s", reminder_id)

            try:
                self.process_reminder(reminder)
            except Exception:
                logger.exception(
                    "Reminder processing failed reminder_id=%s",
                    reminder_id
                )

                try:
                    failed = self.transition_status(
                        reminder_id,
                        "processing",
                        "failed"
                    )
                    if failed:
                        logger.info(
                            "Reminder transitioned to failed reminder_id=%s",
                            reminder_id
                        )
                    else:
                        logger.warning(
                            "Reminder was no longer processing reminder_id=%s",
                            reminder_id
                        )
                except Exception:
                    logger.exception(
                        "Failed to transition reminder to failed reminder_id=%s",
                        reminder_id
                    )

                continue

            try:
                sent = self.transition_status(
                    reminder_id,
                    "processing",
                    "sent"
                )
                if sent:
                    logger.info(
                        "Reminder processed and transitioned to sent reminder_id=%s",
                        reminder_id
                    )
                    processed_count += 1
                else:
                    logger.warning(
                        "Reminder was no longer processing reminder_id=%s",
                        reminder_id
                    )
            except Exception:
                logger.exception(
                    "Failed to transition reminder to sent reminder_id=%s",
                    reminder_id
                )

        return processed_count
