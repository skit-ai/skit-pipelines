import json
from typing import Union
import skit_pipelines.constants as const
from pydantic import BaseModel



class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: str
    
class UserInDB(User):
    hashed_password: str