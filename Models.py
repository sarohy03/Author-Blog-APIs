from pydantic import BaseModel


class Blog(BaseModel):
    id: int
    description: str


class Author(BaseModel):
    username: str
    password: str
    age: int


class Author_Blog(BaseModel):
    Author_id: int
    Blog_id: int
