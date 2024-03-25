from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class PostCreate(BaseModel):
    text: str
    token: str


class Token(BaseModel):
    access_token: str
