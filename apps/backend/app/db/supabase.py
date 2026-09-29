from supabase import Client, create_client

from apps.backend.app.core.config import (
    SUPABASE_URL,
    SUPABASE_PUBLIC_KEY
)


def create_public_client() -> Client:
    return create_client(
        SUPABASE_URL,
        SUPABASE_PUBLIC_KEY
    )


def create_authenticated_client(access_token: str) -> Client:
    client = create_public_client()
    client.postgrest.auth(access_token)
    return client
