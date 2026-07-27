from fastapi import APIRouter, Depends, Response, status

from apps.backend.app.core.security import get_current_user
from apps.backend.app.schemas.task import TaskCreate, TaskUpdate
from apps.backend.app.services.task_service import (
    create_task,
    delete_task,
    get_task_by_id,
    get_tasks,
    update_task,
)

router = APIRouter()


@router.get("/tasks", tags=["Tasks"])
def read_tasks(
    current_user=Depends(get_current_user)
):

    return get_tasks(current_user["id"])


@router.get("/tasks/{task_id}", tags=["Tasks"])
def read_task(
    task_id: str,
    current_user=Depends(get_current_user)
):

    return get_task_by_id(
        task_id,
        current_user["id"]
    )


@router.post(
    "/tasks",
    tags=["Tasks"],
    status_code=status.HTTP_201_CREATED
)
def add_task(
    task: TaskCreate,
    current_user=Depends(get_current_user)
):

    return create_task(
        task,
        current_user["id"]
    )


@router.put("/tasks/{task_id}", tags=["Tasks"])
def edit_task(
    task_id: str,
    task: TaskUpdate,
    current_user=Depends(get_current_user)
):

    return update_task(
        task_id,
        task,
        current_user["id"]
    )


@router.delete(
    "/tasks/{task_id}",
    tags=["Tasks"],
    status_code=status.HTTP_204_NO_CONTENT
)
def remove_task(
    task_id: str,
    current_user=Depends(get_current_user)
):

    delete_task(
        task_id,
        current_user["id"]
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)