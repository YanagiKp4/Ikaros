from fastapi import APIRouter, Depends

from apps.backend.app.schemas.profile import (
    ProfileCreate,
    ProfileUpdate
)

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

    return get_profiles(
        current_user["client"],
        current_user["id"]
    )


@router.get("/profiles/{profile_id}", tags=["Profiles"])
def read_profile(
    profile_id: str,
    current_user=Depends(get_current_user)
):

    return get_profile_by_id(
        current_user["client"],
        profile_id,
        current_user["id"]
    )


@router.post("/profiles", tags=["Profiles"])
def add_profile(
    profile: ProfileCreate,
    current_user=Depends(get_current_user)
):

    return create_profile(
        current_user["client"],
        profile,
        current_user["id"]
    )


@router.put("/profiles/{profile_id}", tags=["Profiles"])
def edit_profile(
    profile_id: str,
    profile: ProfileUpdate,
    current_user=Depends(get_current_user)
):

    return update_profile(
        current_user["client"],
        profile_id,
        profile,
        current_user["id"]
    )


@router.delete("/profiles/{profile_id}", tags=["Profiles"])
def remove_profile(
    profile_id: str,
    current_user=Depends(get_current_user)
):

    return delete_profile(
        current_user["client"],
        profile_id,
        current_user["id"]
    )
