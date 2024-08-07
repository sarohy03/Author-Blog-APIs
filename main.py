from fastapi import FastAPI
import APIs.Blog,APIs.Accounts
app = FastAPI()

app.include_router(APIs.Blog.router)
app.include_router(APIs.Accounts.router)