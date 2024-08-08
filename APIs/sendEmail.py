import secrets

from fastapi_mail import  FastMail, MessageSchema, ConnectionConfig
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from Config import author_collection


class Envs:
    MAIL_USERNAME = 'a.h.sarohy@gmail.com'
    MAIL_PASSWORD = 'rnpf pahs yfnm dses'
    MAIL_FROM = 'a.h.sarohy@gmail.com'
    MAIL_PORT = 587
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_FROM_NAME = 'Welcome'

router=APIRouter()


conf = ConnectionConfig(
    MAIL_USERNAME=Envs.MAIL_USERNAME,
    MAIL_PASSWORD=Envs.MAIL_PASSWORD,
    MAIL_FROM=Envs.MAIL_FROM,
    MAIL_PORT=465,
    MAIL_SERVER=Envs.MAIL_SERVER,
    MAIL_FROM_NAME=Envs.MAIL_FROM_NAME,
    USE_CREDENTIALS=True,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
)


async def send_email(subject: str, email_to: str, body: str):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype='html',
    )

    fm = FastMail(conf)
    await fm.send_message(message)


class EmailRequest(BaseModel):
    email: str



async def send_verification_email(email_request: EmailRequest , apiEndPoint: str):
    user = author_collection.find_one({"email": email_request.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("is_verified"):
        raise HTTPException(status_code=400, detail="Email already verified")

    verification_token = secrets.token_urlsafe()
    r = author_collection.update_many({"email": email_request.email}, {"$set": {"verification_token": verification_token}})
    if not r:
        return {"message": "Not verified"}
    verification_link = f"https://de5e-110-39-21-190.ngrok-free.app/{apiEndPoint}?token={verification_token}"
    email_body = f"Please verify your email by clicking the following link: {verification_link}"

    await send_email('Verify your email', email_request.email, email_body)

    return {"message": "Verification email sent successfully"}

