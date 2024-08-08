from dataclasses import Field
from typing import Optional

from pydantic import BaseModel


class Blog(BaseModel):
    id: int
    description: str


class Author(BaseModel):
    email: str
    username: str
    password: str
    age: int
    is_verified: bool = False
    verification_token: str = None


class Author_Blog(BaseModel):
    Author_id: int
    Blog_id: int
