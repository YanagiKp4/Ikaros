from apps.backend.app.db.supabase import supabase
from apps.backend.app.schemas.profile import ProfileCreate, ProfileUpdate


def get_profiles():

    response = (
        supabase
        .table("profiles")
        .select("*")
        .execute()
    )

    return response.data

def get_profile_by_id(profile_id: str):

    response = (
        supabase
        .table("profiles")
        .select("*")
        .eq("id", profile_id)
        .execute()
    )

    return response.data

def create_profile(profile: ProfileCreate):

    data = {
        "email": profile.email,
        "full_name": profile.full_name,
        "avatar_url": profile.avatar_url,
    }

    response = (
        supabase
        .table("profiles")
        .insert(data)
        .execute()
    )

    return response.data

def update_profile(profile_id: str, profile: ProfileUpdate):

    data = {
        "email": profile.email,
        "full_name": profile.full_name,
        "avatar_url": profile.avatar_url,
    }

    response = (
        supabase
        .table("profiles")
        .update(data)
        .eq("id", profile_id)
        .execute()
    )

    return response.data

def delete_profile(profile_id: str):

    response = (
        supabase
        .table("profiles")
        .delete()
        .eq("id", profile_id)
        .execute()
    )

    return response.data