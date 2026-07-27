from apps.backend.app.db.supabase import supabase


def get_user_by_email(email: str):

    response = (
        supabase
        .table("users")
        .select("*")
        .eq("email", email)
        .execute()
    )

    return response.data