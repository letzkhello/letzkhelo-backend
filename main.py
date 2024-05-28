
from fastapi import FastAPI
from uvicorn import run

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from fastapi import Request

from admin.admin import get_competitions, has_access_for_competition, provide_admin_access, get_registered_users_by_sport_name


app = FastAPI()

SECRET_KEY = "138r3h788dhhd9yer8hd38h3hhd8ih3"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1800


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False


class get_competitions_class(BaseModel):
    email: str | None = None

class admin_access_class(BaseModel):
    email: str | None = None
    sportName: str | None = None
    superadmin_email: str | None = None

class registered_users_by_sport_name_class(BaseModel):
    sportName: str | None = None
    email: str | None = None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)


def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = form_data.username
    password = form_data.password
    if user != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if password != "abc":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print(user)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
async def root(current_user: User = Depends(get_current_active_user)):
    return {"message": "Hello World!"}


@app.get("/admin/competitions")
async def get_competitions_api(request: get_competitions_class, current_user: User = Depends(get_current_active_user)):
    res = await get_competitions(request)
    return res

@app.get("/admin/has_access_to_sport")
async def has_access_to_sport(request: registered_users_by_sport_name_class, current_user: User = Depends(get_current_active_user)):
    res = await has_access_for_competition(request)
    return res

@app.post("/admin/provide_admin_access")
async def provide_admin_access_api(request: admin_access_class, current_user: User = Depends(get_current_active_user)):
    res = await provide_admin_access(request)
    return res

@app.get("/admin/get_registered_users_by_sport_name")
async def get_registered_users_by_sport_name_api(request: registered_users_by_sport_name_class, current_user: User = Depends(get_current_active_user)):
    res = await get_registered_users_by_sport_name(request)
    return res

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8000)