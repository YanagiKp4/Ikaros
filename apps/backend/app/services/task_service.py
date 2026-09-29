from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from postgrest import APIError
from supabase import Client

from apps.backend.app.schemas.task import TaskCreate, TaskUpdate


def _raise_database_error(error: APIError):
    if error.code == "42501":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a esta tarea"
        ) from error

    if error.code in {"22P02", "23514"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Los datos de la tarea no son válidos"
        ) from error

    if error.code == "23505":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La tarea ya existe"
        ) from error

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Error al acceder al servicio de tareas"
    ) from error


def get_tasks(client: Client, user_id: str):
    try:
        response = (
            client
            .table("tasks")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
    except APIError as error:
        _raise_database_error(error)

    return response.data


def get_task_by_id(client: Client, task_id: str, user_id: str):
    try:
        response = (
            client
            .table("tasks")
            .select("*")
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

    return response.data[0]


def create_task(client: Client, task: TaskCreate, user_id: str):
    data = jsonable_encoder(task)
    data["user_id"] = user_id

    try:
        response = (
            client
            .table("tasks")
            .insert(data)
            .select("*")
            .execute()
        )
    except APIError as error:
        _raise_database_error(error)

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase no devolvió la tarea creada"
        )

    return response.data[0]


def update_task(
    client: Client,
    task_id: str,
    task: TaskUpdate,
    user_id: str
):
    data = jsonable_encoder(
        task,
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
            .table("tasks")
            .update(data)
            .eq("id", task_id)
            .eq("user_id", user_id)
            .select("*")
            .execute()
        )
    except APIError as error:
        _raise_database_error(error)

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return response.data[0]


def delete_task(client: Client, task_id: str, user_id: str):
    try:
        response = (
            client
            .table("tasks")
            .delete()
            .eq("id", task_id)
            .eq("user_id", user_id)
            .select("id")
            .execute()
        )
    except APIError as error:
        _raise_database_error(error)

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
