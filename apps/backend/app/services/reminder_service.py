from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from postgrest import APIError
from supabase import Client

from apps.backend.app.schemas.reminder import (
    ReminderCreate,
    ReminderStatus,
    ReminderUpdate,
    TaskReminderCreate,
)


def _raise_database_error(error: APIError):
    if error.code == "42501":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a este recordatorio"
        ) from error

    if error.code in {"22P02", "23514"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Los datos del recordatorio no son válidos"
        ) from error

    if error.code == "23505":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El recordatorio ya existe"
        ) from error

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Error al acceder al servicio de recordatorios"
    ) from error


def get_reminders(client: Client, user_id: str):
    try:
        response = (
            client
            .table("reminders")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
    except APIError as error:
        _raise_database_error(error)

    return response.data


def get_reminder_by_id(
    client: Client,
    reminder_id: str,
    user_id: str
):
    try:
        response = (
            client
            .table("reminders")
            .select("*")
            .eq("id", reminder_id)
            .eq("user_id", user_id)
            .execute()
        )
    except APIError as error:
        _raise_database_error(error)

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recordatorio no encontrado"
        )

    return response.data[0]


def _validate_task_ownership(client: Client, task_id: str, user_id: str):
    try:
        response = (
            client
            .table("tasks")
            .select("id")
            .eq("id", task_id)
            .eq("user_id", user_id)
            .execute()
        )
    except APIError as error:
        _raise_database_error(error)

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )


def create_reminder(
    client: Client,
    reminder: ReminderCreate,
    user_id: str
):
    data = jsonable_encoder(reminder)
    _validate_task_ownership(client, data["task_id"], user_id)
    data["user_id"] = user_id
    data["status"] = ReminderStatus.pending.value

    try:
        response = (
            client
            .table("reminders")
            .insert(data)
            .select("*")
            .execute()
        )
    except APIError as error:
        _raise_database_error(error)

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase no devolvió el recordatorio creado"
        )

    return response.data[0]


def create_reminder_for_task(
    client: Client,
    task_id: str,
    reminder: TaskReminderCreate,
    user_id: str
):
    _validate_task_ownership(client, task_id, user_id)

    data = jsonable_encoder(reminder)
    data["task_id"] = task_id
    data["user_id"] = user_id
    data["status"] = ReminderStatus.pending.value

    try:
        response = (
            client
            .table("reminders")
            .insert(data)
            .select("*")
            .execute()
        )
    except APIError as error:
        _raise_database_error(error)

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase no devolvió el recordatorio creado"
        )

    return response.data[0]


def update_reminder(
    client: Client,
    reminder_id: str,
    reminder: ReminderUpdate,
    user_id: str
):
    data = jsonable_encoder(
        reminder,
        exclude_unset=True
    )

    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionarse al menos un campo para actualizar"
        )

    try:
        response = (
            client
            .table("reminders")
            .update(data)
            .eq("id", reminder_id)
            .eq("user_id", user_id)
            .eq("status", ReminderStatus.pending.value)
            .select("*")
            .execute()
        )
    except APIError as error:
        _raise_database_error(error)

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recordatorio no encontrado"
        )

    return response.data[0]


def delete_reminder(client: Client, reminder_id: str, user_id: str):
    try:
        response = (
            client
            .table("reminders")
            .delete()
            .eq("id", reminder_id)
            .eq("user_id", user_id)
            .select("id")
            .execute()
        )
    except APIError as error:
        _raise_database_error(error)

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recordatorio no encontrado"
        )
