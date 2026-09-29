from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskStatus(str, Enum):
    pending = "pending"
    completed = "completed"


class TaskBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        min_length=3,
        max_length=100
    )

    description: Optional[str] = Field(
        default=None,
        max_length=500
    )

    status: TaskStatus = TaskStatus.pending

    priority: TaskPriority = TaskPriority.medium

    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=100
    )

    description: Optional[str] = Field(
        default=None,
        max_length=500
    )

    status: Optional[TaskStatus] = None

    priority: Optional[TaskPriority] = None

    due_date: Optional[datetime] = None


class TaskResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
