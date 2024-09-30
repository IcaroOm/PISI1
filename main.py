from fastapi import FastAPI, APIRouter, HTTPException, Request, Form, Header, Depends
from fastapi.responses import HTMLResponse, JSONResponse, Response, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import html
import re
import random
import string
import requests
from models import database, passwords, users, pwd_context, SessionLocal

app = FastAPI()

router = APIRouter()

templates = Jinja2Templates(directory="templates")

app.add_middleware(SessionMiddleware, secret_key="your-secret-key")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


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


async def get_user_by_username(db: Session, username: str):
    query = users.select().where(users.c.username == username)
    return await database.fetch_one(query)


async def create_user(db: Session, email: str, password: str):
    hashed_password = pwd_context.hash(password)
    query = users.insert().values(email=email, hashed_password=hashed_password)
    await database.execute(query)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/suggest_password", response_class=JSONResponse)
async def generate_password(request: Request, hx_request: Optional[str] = Header(None)):
    password = generate_random_password(12, True, True, True, True)
    if hx_request:
        return templates.TemplateResponse("partials/password_suggest_register.html", {"request": request, "password": password})
    else:
        return templates.TemplateResponse("register.html", {"request": request, "password": password})


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


@router.put("/save_password", response_class=JSONResponse)
async def save_password(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    print(form_data)
    password = form_data.get('password')
    name = form_data.get('name')
    username = form_data.get('username')
    email = form_data.get('email')

    username = request.session.get("user")

    if not username:
        raise HTTPException(status_code=403, detail="Not logged in")

    user = await get_user_by_username(db, username)

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
    username = request.session.get("user")

    if not username:
        raise HTTPException(status_code=403, detail="Not logged in")

    query = passwords.select().where(passwords.c.username == username)
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
async def login(request: Request, db: Session = Depends(get_db), email: str = Form(...), password: str = Form(...)):
    user = db.query(users).filter(users.email == email).first()
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse("partials/login_error.html", {"request": request, "error": "Invalid email or "
                                                                                                     "password"})

    request.session["user"] = user.username
    return RedirectResponse(url="/", status_code=302)

@router.get("/session-check", response_class=HTMLResponse)
async def session_check(request: Request):
    if request.session.get("user"):
        return HTMLResponse("Logged in")
    else:
        raise HTTPException(status_code=403, detail="Not logged in")


@router.get("/session-status", response_class=HTMLResponse)
async def session_status(request: Request):
    if request.session.get("user"):
        return HTMLResponse("Logged in")
    else:
        return HTMLResponse("Not logged in")


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    request.session.pop("user", None)
    return Response(status_code=204, headers={"HX-Redirect": "/"})


# Register page
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# Register logic
@router.post("/register", response_class=HTMLResponse)
async def register(request: Request, db: Session = Depends(get_db), username: str = Form(...),
                   password: str = Form(...), email: str = Form(...)):
    existing_user = db.query(users).filter(users.c.username == username).first()
    existing_email = db.query(users).filter(users.c.email == email).first()
    if existing_user or existing_email:
        return templates.TemplateResponse("partials/login_error.html", {"request": request, "error": "Username already taken"})

    hashed_password = get_password_hash(password)
    stmt = users.insert().values(email=email, username=username, hashed_password=hashed_password)

    db.execute(stmt)
    db.commit()

    new_user = db.query(users).filter(users.c.username == username).first()

    platform_password = password
    password_length = len(platform_password)
    password_name = f"{username}'s Password"

    password_stmt = passwords.insert().values(
        password=platform_password,
        length=password_length,
        name=password_name,
        email=email,
        username=username,
        user_id=new_user.id,
    )
    db.execute(password_stmt)
    db.commit()

    request.session["user"] = new_user.username
    return Response(status_code=204, headers={"HX-Redirect": "/"})


@router.get("/auth_buttons", response_class=HTMLResponse)
async def auth_buttons(request: Request):
    return templates.TemplateResponse("partials/auth_buttons.html", {"request": request})


app.include_router(router)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
