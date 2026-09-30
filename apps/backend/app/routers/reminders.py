from fastapi import APIRouter, Depends, Response, status

from apps.backend.app.core.security import get_current_user
from apps.backend.app.schemas.reminder import (
    ReminderCreate,
    ReminderResponse,
    ReminderUpdate,
    TaskReminderCreate,
)
from apps.backend.app.services.reminder_service import (
    create_reminder,
    create_reminder_for_task,
    delete_reminder,
    get_reminder_by_id,
    get_reminders,
    update_reminder,
)


router = APIRouter()


@router.get(
    "/reminders",
    tags=["Reminders"],
    response_model=list[ReminderResponse]
)
def read_reminders(
    current_user=Depends(get_current_user)
):
    return get_reminders(
        current_user["client"],
        current_user["id"]
    )


@router.get(
    "/reminders/{reminder_id}",
    tags=["Reminders"],
    response_model=ReminderResponse
)
def read_reminder(
    reminder_id: str,
    current_user=Depends(get_current_user)
):
    return get_reminder_by_id(
        current_user["client"],
        reminder_id,
        current_user["id"]
    )


@router.post(
    "/reminders",
    tags=["Reminders"],
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED
)
def add_reminder(
    reminder: ReminderCreate,
    current_user=Depends(get_current_user)
):
    return create_reminder(
        current_user["client"],
        reminder,
        current_user["id"]
    )


@router.post(
    "/tasks/{task_id}/reminders",
    tags=["Reminders"],
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED
)
def add_task_reminder(
    task_id: str,
    reminder: TaskReminderCreate,
    current_user=Depends(get_current_user)
):
    return create_reminder_for_task(
        current_user["client"],
        task_id,
        reminder,
        current_user["id"]
    )


@router.put(
    "/reminders/{reminder_id}",
    tags=["Reminders"],
    response_model=ReminderResponse
)
def edit_reminder(
    reminder_id: str,
    reminder: ReminderUpdate,
    current_user=Depends(get_current_user)
):
    return update_reminder(
        current_user["client"],
        reminder_id,
        reminder,
        current_user["id"]
    )


@router.delete(
    "/reminders/{reminder_id}",
    tags=["Reminders"],
    status_code=status.HTTP_204_NO_CONTENT
)
def remove_reminder(
    reminder_id: str,
    current_user=Depends(get_current_user)
):
    delete_reminder(
        current_user["client"],
        reminder_id,
        current_user["id"]
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
