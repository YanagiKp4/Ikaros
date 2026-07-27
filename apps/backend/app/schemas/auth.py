from pydantic import BaseModel, EmailStr


class RegisterUser(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class LoginUser(BaseModel):
    email: EmailStr
    password: str