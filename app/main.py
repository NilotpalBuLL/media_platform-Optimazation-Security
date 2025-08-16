from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
import redis.asyncio as redis
from collections import defaultdict
import asyncio

# ---------------- CONFIG ---------------- #
class Settings(BaseSettings):
    SECRET_KEY: str = "supersecret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REDIS_URL: str = "redis://localhost:6379"

settings = Settings()

# ---------------- INIT ---------------- #
app = FastAPI(title="Media Platform Analytics")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Redis client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# Mock databases
users_db: Dict[str, Dict] = {}
media_db: Dict[int, Dict] = {}
views_db: Dict[int, list] = defaultdict(list)

# Rate limit tracker { ip: [timestamps] }
rate_limit_store: Dict[str, list] = defaultdict(list)
RATE_LIMIT = 5   # 5 requests
WINDOW = 60      # per 60 seconds

# ---------------- MODELS ---------------- #
class User(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Media(BaseModel):
    title: str
    type: str
    file_url: str

# ---------------- UTILS ---------------- #
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None or email not in users_db:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return users_db[email]

def rate_limit(ip: str):
    now = datetime.utcnow()
    timestamps = rate_limit_store[ip]
    # keep only recent requests
    rate_limit_store[ip] = [ts for ts in timestamps if (now - ts).seconds < WINDOW]
    if len(rate_limit_store[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests")
    rate_limit_store[ip].append(now)

# ---------------- ROUTES ---------------- #
@app.post("/auth/signup")
async def signup(user: User):
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    users_db[user.email] = {"email": user.email, "password": user.password}
    return {"msg": "User created"}

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer"}

@app.post("/media")
async def create_media(media: Media, user: dict = Depends(get_current_user)):
    media_id = len(media_db) + 1
    media_db[media_id] = media.dict()
    return {"id": media_id, **media.dict()}

@app.post("/media/{media_id}/view")
async def log_view(media_id: int, request: Request, user: dict = Depends(get_current_user)):
    rate_limit(request.client.host)  # apply rate limit

    if media_id not in media_db:
        raise HTTPException(status_code=404, detail="Media not found")

    ip = request.client.host
    now = datetime.utcnow()
    views_db[media_id].append({"ip": ip, "time": now})

    # invalidate cache
    await redis_client.delete(f"analytics:{media_id}")

    return {"msg": "View logged"}

@app.get("/media/{media_id}/analytics")
async def get_analytics(media_id: int, user: dict = Depends(get_current_user)):
    if media_id not in media_db:
        raise HTTPException(status_code=404, detail="Media not found")

    # check Redis cache
    cache_key = f"analytics:{media_id}"
    cached = await redis_client.get(cache_key)
    if cached:
        return {"cached": True, **eval(cached)}

    views = views_db[media_id]
    total_views = len(views)
    unique_ips = len(set(v["ip"] for v in views))

    views_per_day = defaultdict(int)
    for v in views:
        views_per_day[v["time"].date().isoformat()] += 1

    analytics = {
        "total_views": total_views,
        "unique_ips": unique_ips,
        "views_per_day": dict(views_per_day),
    }

    # store in cache for 60s
    await redis_client.setex(cache_key, 60, str(analytics))

    return {"cached": False, **analytics}

@app.get("/health")
async def health_check():
    try:
        pong = await redis_client.ping()
    except Exception:
        pong = False
    return {
        "status": "ok",
        "time": datetime.utcnow().isoformat(),
        "redis": pong,
    }
