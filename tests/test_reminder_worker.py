from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from apps.backend.app.workers import reminder_processor, reminder_worker
from apps.backend.app.workers.reminder_processor import ReminderProcessor


NOW = datetime(2026, 10, 1, 21, 0, tzinfo=timezone.utc)
REMINDER_A_ID = "00000000-0000-0000-0000-000000000111"
REMINDER_B_ID = "00000000-0000-0000-0000-000000000222"
REMINDER_C_ID = "00000000-0000-0000-0000-000000000333"


def reminder_row(reminder_id, remind_at, status="pending"):
    return {
        "id": reminder_id,
        "task_id": "00000000-0000-0000-0000-000000000011",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "remind_at": remind_at,
        "status": status,
        "channel": "in_app",
    }


def test_get_due_reminders_selects_pending_expired_batch(
    fake_supabase_client,
):
    fake_supabase_client.seed(
        "reminders",
        [
            reminder_row(REMINDER_A_ID, "2026-10-01T19:00:00+00:00"),
            reminder_row(REMINDER_B_ID, "2026-10-01T22:00:00+00:00"),
            reminder_row(REMINDER_C_ID, "2026-10-01T20:00:00+00:00", "sent"),
        ],
    )
    processor = ReminderProcessor(fake_supabase_client, batch_size=10)

    due = processor.get_due_reminders(NOW)

    assert [reminder["id"] for reminder in due] == [REMINDER_A_ID]
    operation = fake_supabase_client.operations[-1]
    assert operation["filters"] == [
        ("eq", "status", "pending"),
        ("lte", "remind_at", NOW.isoformat()),
    ]


def test_claim_reminder_updates_pending_to_processing(
    fake_supabase_client,
):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_A_ID, "2026-10-01T19:00:00+00:00")],
    )
    processor = ReminderProcessor(fake_supabase_client, batch_size=10)

    claimed = processor.claim_reminder(REMINDER_A_ID, NOW)

    assert claimed is True
    assert fake_supabase_client.tables["reminders"][0]["status"] == "processing"
    operation = fake_supabase_client.operations[-1]
    assert operation["filters"] == [
        ("eq", "id", REMINDER_A_ID),
        ("eq", "status", "pending"),
        ("lte", "remind_at", NOW.isoformat()),
    ]


def test_claim_does_not_reclaim_non_pending_reminder(fake_supabase_client):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_A_ID, "2026-10-01T19:00:00+00:00", "sent")],
    )
    processor = ReminderProcessor(fake_supabase_client, batch_size=10)

    claimed = processor.claim_reminder(REMINDER_A_ID, NOW)

    assert claimed is False
    assert fake_supabase_client.tables["reminders"][0]["status"] == "sent"


def test_successful_processing_transitions_to_sent(fake_supabase_client):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_A_ID, "2026-10-01T19:00:00+00:00")],
    )
    processor = ReminderProcessor(fake_supabase_client, batch_size=10)

    processed = processor.process_due_reminders(NOW)

    assert processed == 1
    assert fake_supabase_client.tables["reminders"][0]["status"] == "sent"
    update_operations = [
        operation
        for operation in fake_supabase_client.operations
        if operation["operation"] == "update"
    ]
    assert [operation["payload"] for operation in update_operations] == [
        {"status": "processing"},
        {"status": "sent"},
    ]


def test_processing_error_transitions_to_failed(
    fake_supabase_client,
    monkeypatch,
):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_A_ID, "2026-10-01T19:00:00+00:00")],
    )
    processor = ReminderProcessor(fake_supabase_client, batch_size=10)
    monkeypatch.setattr(
        processor,
        "process_reminder",
        Mock(side_effect=RuntimeError("simulated processing failure")),
    )

    processed = processor.process_due_reminders(NOW)

    assert processed == 0
    assert fake_supabase_client.tables["reminders"][0]["status"] == "failed"


def test_batch_limits_number_of_processed_reminders(fake_supabase_client):
    fake_supabase_client.seed(
        "reminders",
        [
            reminder_row(REMINDER_A_ID, "2026-10-01T18:00:00+00:00"),
            reminder_row(REMINDER_B_ID, "2026-10-01T19:00:00+00:00"),
            reminder_row(REMINDER_C_ID, "2026-10-01T20:00:00+00:00"),
        ],
    )
    processor = ReminderProcessor(fake_supabase_client, batch_size=2)

    processed = processor.process_due_reminders(NOW)

    assert processed == 2
    statuses = {
        reminder["id"]: reminder["status"]
        for reminder in fake_supabase_client.tables["reminders"]
    }
    assert statuses == {
        REMINDER_A_ID: "sent",
        REMINDER_B_ID: "sent",
        REMINDER_C_ID: "pending",
    }


def test_no_due_reminders_performs_no_updates(fake_supabase_client):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_A_ID, "2026-10-01T22:00:00+00:00")],
    )
    processor = ReminderProcessor(fake_supabase_client, batch_size=10)

    processed = processor.process_due_reminders(NOW)

    assert processed == 0
    assert [
        operation["operation"]
        for operation in fake_supabase_client.operations
    ] == ["select"]


def test_create_worker_client_uses_privileged_worker_configuration(
    fake_supabase_client,
    monkeypatch,
):
    create_client = Mock(return_value=fake_supabase_client)
    monkeypatch.setattr(reminder_processor, "create_client", create_client)

    client = reminder_processor.create_worker_client()

    assert client is fake_supabase_client
    create_client.assert_called_once_with(
        reminder_processor.SUPABASE_URL,
        reminder_processor.SUPABASE_WORKER_KEY,
    )


def test_create_worker_client_requires_worker_key(monkeypatch):
    monkeypatch.setattr(reminder_processor, "SUPABASE_WORKER_KEY", None)

    with pytest.raises(
        RuntimeError,
        match="SUPABASE_WORKER_KEY is required to run the reminder worker",
    ):
        reminder_processor.create_worker_client()


def test_worker_loop_runs_one_controlled_cycle_and_shuts_down(
    fake_supabase_client,
    monkeypatch,
):
    processor = Mock()
    create_client = Mock(return_value=fake_supabase_client)
    monkeypatch.setattr(reminder_worker, "create_worker_client", create_client)
    monkeypatch.setattr(reminder_worker, "ReminderProcessor", Mock(return_value=processor))
    monkeypatch.setattr(
        reminder_worker.time,
        "sleep",
        Mock(side_effect=KeyboardInterrupt),
    )

    reminder_worker.run_worker()

    create_client.assert_called_once_with()
    processor.process_due_reminders.assert_called_once()
