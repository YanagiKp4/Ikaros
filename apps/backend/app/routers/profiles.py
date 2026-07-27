from fastapi import APIRouter, Depends

from apps.backend.app.schemas.profile import ProfileCreate, ProfileUpdate
from apps.backend.app.services.profile_service import (
    create_profile,
    delete_profile,
    get_profile_by_id,
    get_profiles,
    update_profile,
)

from apps.backend.app.core.security import get_current_user

router = APIRouter()


@router.get("/profiles", tags=["Profiles"])
def read_profiles(
    current_user=Depends(get_current_user)
):

    return get_profiles()


@router.get("/profiles/{profile_id}", tags=["Profiles"])
def read_profile(profile_id: str):
    return get_profile_by_id(profile_id)


@router.put("/profiles/{profile_id}", tags=["Profiles"])
def edit_profile(profile_id: str, profile: ProfileUpdate):
    return update_profile(profile_id, profile)


@router.post("/profiles", tags=["Profiles"])
def add_profile(profile: ProfileCreate):
    return create_profile(profile)


@router.delete("/profiles/{profile_id}", tags=["Profiles"])
def remove_profile(profile_id: str):
    return delete_profile(profile_id)