from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, Response, Request, Query, Form
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from starlette import status
from starlette.responses import RedirectResponse

from DriveShareWeb.deps import ensure_user_not_logged_in, get_current_user
from DriveShareWeb.orm.connect import prepare_db
from DriveShareWeb.security import password
from DriveShareWeb.security.token import Token, create_access_token

app = FastAPI()

app.mount("/static", StaticFiles(directory="DriveShareWeb/static"), name="static")


@app.on_event("startup")
def on_startup():
    prepare_db()


# URL rewrite

@app.get("/", response_class=HTMLResponse)
async def home(account=Depends(get_current_user)):
    with open("DriveShareWeb/static/home.html") as f:
        html = f.readlines()

    return HTMLResponse(content=str.join("", html), status_code=200)


@app.get("/login", response_class=HTMLResponse)
async def login(not_login=Depends(ensure_user_not_logged_in)):
    with open("DriveShareWeb/static/login.html") as f:
        html = f.readlines()

    return HTMLResponse(content=str.join("", html), status_code=200)


# Login

# TODO add signup

@app.post("/token", response_model=Token)
async def create_token(
        form: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response
):
    """Creates an OAuth2 token"""
    if password.verify_password(form.password, form.username):
        access_token = create_access_token(form.username)
        # Set token in cookie and respond as JSON
        response.set_cookie("access_token", f"bearer {access_token}", httponly=True)
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/logout")
async def logout():
    """Destroys the login token"""
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response
