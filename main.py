from fastapi import FastAPI, APIRouter, HTTPException, Request, Form, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import select
from typing import Optional
import random
import string
import requests
from models import database, passwords

app = FastAPI()

router = APIRouter()

templates = Jinja2Templates(directory="templates")


def generate_random_password(length: int) -> str:
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/random_pass", response_class=HTMLResponse)
async def index(request: Request):
    initial_length = 16
    initial_password = generate_random_password(initial_length)
    return templates.TemplateResponse("index.html", {"request": request, "length": initial_length, "password": initial_password})


@router.get("/generate_password", response_class=JSONResponse)
async def generate_password(request: Request, length: int):
    if length < 1:
        raise HTTPException(status_code=400, detail='Length must be greater than zero')
    password = generate_random_password(length)
    return {"password": password}


class SavePasswordRequest(BaseModel):
    name: str
    password: str


@router.post("/save_password", response_class=JSONResponse)
async def save_password(request: SavePasswordRequest):
    query = passwords.insert().values(password=request.password, length=len(request.password), name=request.name)
    await database.execute(query)
    return {"message": "Password saved successfully"}


@router.get("/stored_passwords", response_class=HTMLResponse)
async def stored_passwords(request: Request):
    query = select(passwords.c.name, passwords.c.password, passwords.c.length, passwords.c.created_at)
    saved_passwords = await database.fetch_all(query)
    return templates.TemplateResponse("stored_passwords.html", {"request": request, "passwords": saved_passwords})


def check_pwned_email(email: str) -> dict:
    response = requests.get(f'https://leakcheck.io/api/public?check={email}')
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail='Failed to retrieve data from Have I Been Pwned API.')
    return response.json()


@router.get("/check_email", response_class=HTMLResponse)
async def check_email_get(request: Request):
    return templates.TemplateResponse("email_check.html", {"request": request})


@router.post("/check_email", response_class=HTMLResponse)
async def check_email_post(request: Request, email: str = Form(...), hx_request: Optional[str] = Header(None)):
    data = check_pwned_email(email)
    if data['found'] == 0:
        message = 'Your email has not been found in any data breaches.'
        sources = []
    else:
        message = f'Your email has been found in {data["found"]} data breaches.'
        sources = data['sources']
    if hx_request:
        return templates.TemplateResponse("table_sources.html",  {"request": request, "message": message, "sources": sources, "email": email})
    return templates.TemplateResponse("email_check.html", {"request": request, "message": message, "sources": sources, "email": email})


@router.get("/stored_passwords", response_class=HTMLResponse)
async def stored_passwords(request: Request):
    query = passwords.select()
    saved_passwords = await database.fetch_all(query)
    return templates.TemplateResponse("stored_passwords.html", {"request": request, "passwords": saved_passwords})


app.include_router(router)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
