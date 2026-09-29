from pydantic import BaseModel, ConfigDict


class ProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    avatar_url: str | None = None


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    avatar_url: str | None = None
