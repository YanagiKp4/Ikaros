from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder

from apps.backend.app.db.supabase import supabase
from apps.backend.app.schemas.task import TaskCreate, TaskUpdate


def get_tasks(user_id: str):

    response = (
        supabase
        .table("tasks")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    return response.data


def get_task_by_id(task_id: str, user_id: str):

    response = (
        supabase
        .table("tasks")
        .select("*")
        .eq("id", task_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return response.data[0]

def create_task(task: TaskCreate, user_id: str):

    data = {
        "user_id": user_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "due_date": task.due_date,
    }

    response = (
        supabase
        .table("tasks")
        .insert(data)
        .execute()
    )

    return response.data

def update_task(task_id: str, task: TaskUpdate, user_id: str):

    data = jsonable_encoder(
    task,
    exclude_unset=True
)

    response = (
        supabase
        .table("tasks")
        .update(data)
        .eq("id", task_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return response.data[0]

def delete_task(task_id: str, user_id: str):

    response = (
        supabase
        .table("tasks")
        .delete()
        .eq("id", task_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return