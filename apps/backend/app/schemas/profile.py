from pydantic import BaseModel, EmailStr


class ProfileCreate(BaseModel):
    email: EmailStr
    full_name: str
    avatar_url: str | None = None

class ProfileUpdate(BaseModel):
    email: EmailStr
    full_name: str
    avatar_url: str | None = None    