from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AppException(BaseModel):
    owner: str
    title: str
    msg: str


class AppResponse(BaseModel):
    model_pk: Optional[int]
    status: str
    ready: bool
    project: str
    url: Optional[str]
    exception: Optional[AppException]


class OauthResponse(BaseModel):
    access_token: str
    expires_in: int
    token_type: str
    scope: str
    refresh_token: str


class OauthToken(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: datetime


class ConnectConfig(BaseModel):
    authorization_uri: str
    state: str


class User(BaseModel):
    username: str
    status: str


class UserWithToken(User):
    token: OauthToken
