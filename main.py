from fastapi import FastAPI, APIRouter, HTTPException, Request, Form, Header, Depends
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional
import re
import random
import string
import requests
from models import database, passwords, users, pwd_context, SessionLocal

app = FastAPI()

router = APIRouter()

templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_random_password(length: int, use_lowercase: bool, use_uppercase: bool, use_digits: bool,
                             use_special: bool) -> str:
    characters = ''
    if use_lowercase:
        characters += string.ascii_lowercase
    if use_uppercase:
        characters += string.ascii_uppercase
    if use_digits:
        characters += string.digits
    if use_special:
        characters += string.punctuation

    if not characters:
        characters = string.ascii_letters  # Fallback to letters if no category selected

    return ''.join(random.choice(characters) for _ in range(length))


def check_password_strength(password: str) -> str:
    length_ok = len(password) >= 8
    has_upper = re.search(r'[A-Z]', password)
    has_lower = re.search(r'[a-z]', password)
    has_digit = re.search(r'\d', password)
    has_special = re.search(r'[!@#$%^&*(),.?":{}|<>]', password)

    strength = "Weak"
    if length_ok and has_upper and has_lower and has_digit and has_special:
        strength = "Strong"
    elif length_ok and (has_upper or has_lower) and (has_digit or has_special):
        strength = "Moderate"

    return strength


async def get_user_by_email(db: Session, email: str):
    query = users.select().where(users.c.email == email)
    return await database.fetch_one(query)


async def create_user(db: Session, email: str, password: str):
    hashed_password = pwd_context.hash(password)
    query = users.insert().values(email=email, hashed_password=hashed_password)
    await database.execute(query)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/password_strength", response_class=HTMLResponse)
async def password_strength(request: Request):
    return templates.TemplateResponse("password_strength.html", {"request": request})


@router.get("/random_pass", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/random_pass", response_class=JSONResponse)
async def generate_password(
        request: Request,
        length: int = Form(...),
        lowercase: bool = Form(False),
        uppercase: bool = Form(False),
        nums: bool = Form(False),
        specialchars: bool = Form(False),
        hx_request: Optional[str] = Header(None)
):
    if length < 1:
        return HTMLResponse(status_code=422, content="<h2>Password length must be between 1 and 50</h2>")

    password = generate_random_password(length, lowercase, uppercase, nums, specialchars)

    if hx_request:
        return templates.TemplateResponse("partials/password_value.html", {"request": request, "password": password})
    else:
        return templates.TemplateResponse("index.html", {"request": request, "password": password})


@router.post("/check_password_strength")
async def check_password(request: Request, password: str = Form(...), hx_request: Optional[str] = Header(None)):
    strength = check_password_strength(password)
    if hx_request:
        return templates.TemplateResponse("partials/strength_pass_result.html",
                                          {"request": request, "strength": strength})
    return JSONResponse(content={"strength": strength})


@router.put("/save_password", response_class=JSONResponse)
async def save_password(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    print(form_data)
    password = form_data.get('password')
    name = form_data.get('name')
    username = form_data.get('username')
    email = form_data.get('email')

    user_email = request.cookies.get("user_email")

    if not user_email:
        raise HTTPException(status_code=403, detail="Not logged in")

    user = await get_user_by_email(db, user_email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user['id']

    name_check_query = passwords.select().where(
        passwords.c.name == name,
        passwords.c.user_id == user_id
    )
    existing_password = await database.fetch_one(name_check_query)

    if existing_password:
        raise HTTPException(status_code=400, detail=f"A password with the name '{name}' already exists.")


    query = passwords.insert().values(
        password=password,
        length=len(password),
        name=name,
        username=username,
        user_id=user['id']
    )
    await database.execute(query)

    return {"message": "Password saved successfully"}


@router.get("/stored_passwords", response_class=HTMLResponse)
async def stored_passwords(request: Request):
    user_email = request.cookies.get("user_email")

    if not user_email:
        raise HTTPException(status_code=403, detail="Not logged in")

    query = passwords.select().where(passwords.c.email == user_email)
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
        return templates.TemplateResponse("partials/table_sources.html",
                                          {"request": request, "message": message, "sources": sources, "email": email})
    return templates.TemplateResponse("email_check.html",
                                      {"request": request, "message": message, "sources": sources, "email": email})


@router.get("/stored_passwords", response_class=HTMLResponse)
async def stored_passwords(request: Request):
    query = passwords.select()
    saved_passwords = await database.fetch_all(query)
    return templates.TemplateResponse("stored_passwords.html", {"request": request, "passwords": saved_passwords})


@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login_post(
        request: Request,
        response: Response,
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db),
):
    user = await get_user_by_email(db, email)
    if user and verify_password(password, user["hashed_password"]):
        response.set_cookie(key="user_email", value=email)
        return templates.TemplateResponse("partials/login_success.html", {"request": request, "email": email})
    else:
        return templates.TemplateResponse("partials/login_error.html", {"request": request, "error": "Invalid email or "
                                                                                                     "password"})


@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    existing_user = await get_user_by_email(db, email)
    if existing_user:
        return templates.TemplateResponse("partials/login_error.html",
                                          {"request": request, "error": "Email already registered"})

    await create_user(db, email, password)
    return templates.TemplateResponse("partials/register_success.html", {"request": request, "email": email})


app.include_router(router)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
