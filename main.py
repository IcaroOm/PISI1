from fastapi import FastAPI, APIRouter, HTTPException, Request, Form, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
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
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/random_pass", response_class=JSONResponse)
async def generate_password(request: Request, length: int = Form(...), hx_request: Optional[str] = Header(None)):
    if length < 1:
        return HTMLResponse(status_code=422, content="<h2>Password length must be between 1 and 50</h2>")
    password = generate_random_password(length)
    if hx_request:
        return templates.TemplateResponse("partials/password_value.html", {"request": request, "password": password})
    else:
        return templates.TemplateResponse("index.html", {"request": requests})


@router.put("/save_password", response_class=JSONResponse)
async def save_password(request: Request):
    form_data = await request.form()
    print(form_data)
    password = form_data.get('password')
    name = form_data.get('name')
    username = form_data.get('username')
    email = form_data.get('email')

    query = passwords.insert().values(password=password, length=len(password), name=name, username=username, email=email)
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
        return templates.TemplateResponse("partials/table_sources.html",  {"request": request, "message": message, "sources": sources, "email": email})
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
