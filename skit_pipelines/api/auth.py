import json
import os
from datetime import datetime, timedelta
from typing import Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from skit_pipelines import constants as const
from skit_pipelines.api.models.auth_models import Token, TokenData, User, UserInDB

with open(os.path.join("pipeline_secrets", "auth_config.json")) as f:
    auth_config = json.load(f)
    ACCESS_TOKEN_EXPIRE_MINUTES = auth_config["ACCESS_TOKEN_EXPIRE_MINUTES"]
    CRYPT_SCHEME = auth_config["PASSWORD_CRYPT_SCHEME"]
    ALGORITHM = auth_config["ALGORITHM"]


pwd_context = CryptContext(schemes=[CRYPT_SCHEME], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_users_db():
    return {
        const.KF_USERNAME: {
            "username": const.KF_USERNAME,
            "hashed_password": pwd_context.hash(const.KF_PASSWORD),
        }
    }


def get_user(db, username: str):
    if user_dict := db.get(username):
        return UserInDB(**user_dict)


def authenticate_user(username: str, password: str, db=get_users_db()):
    if not (user := get_user(db, username)) or not verify_password(
        password, user.hashed_password
    ):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, const.JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def valid_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, const.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        if not (username := payload.get("sub")):
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    if not get_user(get_users_db(), username=token_data.username):
        raise credentials_exception
    return True
