from Config import author_collection
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Union
from Models import Author
from typing import List
from .sendEmail import send_email, send_verification_email, EmailRequest

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class PasswordUpdateRequest(BaseModel):
    new_password: str


class User(BaseModel):
    username: str


class UserInDB(User):
    hashed_password: str


class UserCreate(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    password: Union[str, None] = None
    age: Union[str, None] = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_user(username: str) -> Union[UserInDB, None]:
    user = author_collection.find_one({"username": username})
    if user:
        return UserInDB(**user)


async def authenticate_user(username: str, password: str) -> Union[UserInDB, bool]:
    user = await get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Union[User, HTTPException]:
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credential_exception
    user = await get_user(token_data.username)
    if user is None:
        raise credential_exception
    return user


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/Author/", status_code=201)
async def create_user(user: Author):
    if author_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    print(user)
    user_dict = user.dict()
    user_dict["hashed_password"] = hashed_password
    user_dict["email"] = user.email
    author_collection.insert_one(user_dict)
    email = user.email

    r = await send_verification_email(EmailRequest(email=email), "verify-email")
    if not r:
        raise HTTPException(status_code=500, detail="Failed to send verification email")
    return {"message": "Signed up successfully"}


@router.delete("/Author/me", response_model=dict)
async def delete_user(current_user: User = Depends(get_current_user)):
    result = author_collection.delete_one({"username": current_user.username})
    if result.deleted_count == 1:
        return {"message": "User deleted successfully"}
    raise HTTPException(status_code=404, detail="User not found")


@router.patch("/Author/me", response_model=dict)
async def partial_update_user(user_update: UserUpdate, current_user: User = Depends(get_current_user)):
    update_data = {}
    for k, v in user_update.dict().items():
        if v is not None:
            update_data[k] = v

    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    result = author_collection.update_one({"username": current_user.username}, {"$set": update_data})
    if result:
        return {"message": "User updated successfully"}
    raise HTTPException(status_code=400, detail="No changes made")


@router.get("/Author/me", response_model=Author)
async def read_current_user(current_user: User = Depends(get_current_user)):
    result = author_collection.find_one({"username": current_user.username})
    result.pop('_id')
    result.pop('hashed_password')
    if result:
        return result
    raise HTTPException(status_code=404, detail="User not found")


@router.get("/authors/", response_model=List[Author])
async def get_authors():
    authors = list(author_collection.find())
    for i in authors:
        i.pop("_id")
        i.pop("hashed_password")

    return authors


@router.get("/verify-email")
async def verify_email(token: str = Query(...)):
    user = author_collection.find_one({"verification_token": token})

    if not user:
        raise HTTPException(status_code=404, detail="Invalid or expired verification token")

    if user.get("is_verified"):
        raise HTTPException(status_code=400, detail="Email already verified")

    author_collection.update_one(
        {"verification_token": token},
        {"$set": {"is_verified": True, "verification_token": None}}
    )

    return {"message": "Email verified successfully"}


@router.post("/forgot-password/")
async def forgot_password(user: User):
    author = author_collection.find_one({"username": user.username})
    author_collection.update_one({"username": user.username}, {"$set": {"is_verified": False}})

    if not author:
        raise HTTPException(status_code=404, detail="User not found")

    email = author.get("email")
    if not email:
        raise HTTPException(status_code=404, detail="Email not found for user")

    r = await send_verification_email(EmailRequest(email=email), "change-password")

    if not r:
        raise HTTPException(status_code=500, detail="Failed to send verification email")

    return {"message": "Verification email sent successfully"}


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


@router.get("/change-password")
async def change_password(token: str = Query(...)):
    user = author_collection.find_one({"verification_token": token})

    if not user:
        raise HTTPException(status_code=404, detail="Invalid or expired verification token")
    await changing_password(token)

    return {"NOTE": "DONE"}


async def changing_password(token: str):
    hashed_password = get_password_hash("New pass")

    result = author_collection.update_one(
        {"verification_token": token},
        {"$set": {"hashed_password": hashed_password, "verification_token": None, "is_verified": True , "password": "New pass"}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update password")

    return {"message": "Password updated successfully to the hard-coded password"}
