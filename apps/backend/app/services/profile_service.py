from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from postgrest import APIError
from supabase import Client

from apps.backend.app.schemas.profile import ProfileCreate, ProfileUpdate


def _raise_database_error(error: APIError):
    if error.code == "23505":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario ya tiene un perfil"
        ) from error

    if error.code == "42501":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a este perfil"
        ) from error

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Error al acceder al servicio de perfiles"
    ) from error


def get_profiles(client: Client, user_id: str):
    try:
        response = (
            client
            .table("profiles")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
    except APIError as error:
        _raise_database_error(error)

    return response.data


def get_profile_by_id(client: Client, profile_id: str, user_id: str):
    try:
        response = (
            client
            .table("profiles")
            .select("*")
            .eq("id", profile_id)
            .eq("user_id", user_id)
            .execute()
        )
    except APIError as error:
        _raise_database_error(error)

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado"
        )

    return response.data[0]


def create_profile(client: Client, profile: ProfileCreate, user_id: str):
    data = jsonable_encoder(profile)
    data["user_id"] = user_id

    try:
        response = (
            client
            .table("profiles")
            .insert(data)
            .execute()
        )
    except APIError as error:
        _raise_database_error(error)

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase no devolvió el perfil creado"
        )

    return response.data[0]


def update_profile(
    client: Client,
    profile_id: str,
    profile: ProfileUpdate,
    user_id: str
):
    data = jsonable_encoder(
        profile,
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
            .table("profiles")
            .update(data)
            .eq("id", profile_id)
            .eq("user_id", user_id)
            .execute()
        )
    except APIError as error:
        _raise_database_error(error)

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado"
        )

    return response.data[0]


def delete_profile(client: Client, profile_id: str, user_id: str):
    try:
        response = (
            client
            .table("profiles")
            .delete()
            .eq("id", profile_id)
            .eq("user_id", user_id)
            .execute()
        )
    except APIError as error:
        _raise_database_error(error)

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado"
        )

    return response.data
