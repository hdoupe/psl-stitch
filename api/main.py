from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import secrets
from typing import Mapping, Optional, List
from enum import Enum

import httpx

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyCookie

from starlette.responses import Response, RedirectResponse, HTMLResponse
from starlette import status
from pydantic import BaseModel
from jose import jwt

import psl_stitch
from .schemas import (
    AppException,
    AppResponse,
    OauthResponse,
    OauthToken,
    ConnectConfig,
    User,
    UserWithToken,
)
from .settings import settings

app = FastAPI()

origins = list(
    set(("http://localhost", "http://localhost:3000", settings.FRONTEND_URL))
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
cookie_sec = APIKeyCookie(name="session")

cs_base_url = "https://compute.studio"

oauth2_state = {}

authorization_uri_template = (
    f"{settings.CS_BASE_URL}/o/authorize/"
    f"?response_type=code&client_id={settings.CLIENT_ID}&redirect_uri={settings.API_URL}{settings.REDIRECT_URI_PATH}&state={{state}}"
)


async def get_current_user(session: str = Depends(cookie_sec)) -> UserWithToken:
    try:
        print("getting current user")
        payload = jwt.decode(session, settings.SECRET_KEY)
        user = UserWithToken(**json.loads(payload["sub"]))
        if user.token.expires_at < datetime.utcnow() - timedelta(seconds=60):
            print("TODO token expired.")
            # async with httpx.AsyncClient() as client:
            #     clieng
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid authentication"
        )


async def cs_me(access_token: str) -> User:
    async with httpx.AsyncClient() as client:
        me_resp = await client.get(
            f"{cs_base_url}/users/me/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    me_resp.raise_for_status()
    data = me_resp.json()
    if data["status"] == "anon":
        raise HTTPException(403)
    return User(**me_resp.json())


oauth2_states = set([])


def get_redirect_home() -> RedirectResponse:
    return RedirectResponse(settings.FRONTEND_URL)


@app.get("/oauth2/access/")
async def oauth2_access(
    code: str, state: str, response: RedirectResponse = Depends(get_redirect_home)
):
    global oauth2_states
    if state not in oauth2_states:
        raise HTTPException(403)
    oauth2_states -= {state}
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{cs_base_url}/o/token/",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{settings.API_URL}{settings.REDIRECT_URI_PATH}",
                "client_id": settings.CLIENT_ID,
                "client_secret": settings.CLIENT_SECRET,
            },
        )
    resp.raise_for_status()

    oauth_resp = OauthResponse(**resp.json())

    user = await cs_me(oauth_resp.access_token)
    user_data = user.dict()
    user_data.update(
        {
            "token": {
                "access_token": oauth_resp.access_token,
                "refresh_token": oauth_resp.refresh_token,
                "expires_at": datetime.utcnow()
                + timedelta(seconds=oauth_resp.expires_in),
            }
        }
    )
    user = UserWithToken(**user_data)
    token = jwt.encode({"sub": user.json()}, settings.SECRET_KEY)
    response.set_cookie("session", token)
    return response


@app.get("/connect/", response_model=ConnectConfig)
async def connect():
    state = secrets.token_hex(9)
    global oauth2_states
    oauth2_states.add(state)
    return ConnectConfig(
        authorization_uri=authorization_uri_template.format(state=state), state=state
    )


@app.get("/me/", response_model=User)
async def home(user_with_token: str = Depends(get_current_user)):
    me = await cs_me(user_with_token.token.access_token)
    return me


class PSLStitchParams(BaseModel):
    policy_params: Optional[str]
    taxcrunch_params: Optional[str]
    ccc_params: Optional[str]
    behavior_params: Optional[str]


@app.post("/create/", response_model=List[AppResponse])
async def create_simulations(
    stitch_params: PSLStitchParams, user: UserWithToken = Depends(get_current_user),
):
    try:
        print("got data", stitch_params.dict())
        responses, exceptions = await psl_stitch.create(
            bearer_token=user.token.access_token, **stitch_params.dict()
        )
    except psl_stitch.InvalidJSON as e:
        raise HTTPException(400, detail=f"Invalid {e.app} inputs: {str(e.msg)}")

    data = []
    for response in responses.values():
        detail = response["detail"]
        owner, title = detail["project"]["owner"], detail["project"]["title"]
        url = f"{cs_base_url}{detail['gui_url']}"
        data.append(
            AppResponse(
                project=f"{owner}/{title}",
                ready=False,
                status=detail["status"],
                model_pk=response["model_pk"],
                url=url,
                exceptions=None,
            )
        )

    for exception in exceptions:
        data.append(
            AppResponse(
                project=f"{exception.owner}/{exception.title}",
                ready=True,
                status="INVALID",
                model_pk=None,
                exceptions=exception.msg,
            )
        )
    return data


@app.get("/inputs/{owner}/{title}/{model_pk}/")
async def inputs_status(
    owner: str,
    title: str,
    model_pk: int,
    user: UserWithToken = Depends(get_current_user),
):
    app = f"{owner}/{title}"
    return await psl_stitch.get_inputs(
        app, model_pk, bearer_token=user.token.access_token
    )


@app.get("/sim/{owner}/{title}/{model_pk}/")
async def sim(
    owner: str,
    title: str,
    model_pk: int,
    user: UserWithToken = Depends(get_current_user),
):
    app = f"{owner}/{title}"
    return await psl_stitch.get_sim(app, model_pk, bearer_token=user.token.access_token)
