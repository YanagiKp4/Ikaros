from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReminderStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    sent = "sent"
    failed = "failed"
    cancelled = "cancelled"


class ReminderChannel(str, Enum):
    in_app = "in_app"
    email = "email"
    whatsapp = "whatsapp"
    push = "push"


class ReminderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: UUID
    remind_at: datetime
    status: ReminderStatus = ReminderStatus.pending
    channel: ReminderChannel = ReminderChannel.in_app


class ReminderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    remind_at: datetime = None
    status: ReminderStatus = None
    channel: ReminderChannel = None


class ReminderResponse(BaseModel):
    id: UUID
    task_id: UUID
    user_id: UUID
    remind_at: datetime
    status: ReminderStatus
    channel: ReminderChannel
    created_at: datetime
    updated_at: datetime
