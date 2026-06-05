from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import random
import string

from .database import engine, get_db, Base
from .models import URL

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="URL Shortener", lifespan=lifespan)

class URLCreate(BaseModel):
    url: str

def generate_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/shorten")
def shorten_url(payload: URLCreate, db: Session = Depends(get_db)):
    code = generate_code()
    while db.query(URL).filter(URL.short_code == code).first():
        code = generate_code()
    url = URL(original_url=payload.url, short_code=code)
    db.add(url)
    db.commit()
    db.refresh(url)
    return {"short_code": code, "short_url": f"http://localhost:8000/{code}"}

@app.get("/stats/{code}")
def get_stats(code: str, db: Session = Depends(get_db)):
    url = db.query(URL).filter(URL.short_code == code).first()
    if not url:
        raise HTTPException(status_code=404, detail="Not found")
    return {"original_url": url.original_url, "clicks": url.clicks, "created_at": url.created_at}

@app.get("/{code}")
def redirect(code: str, db: Session = Depends(get_db)):
    url = db.query(URL).filter(URL.short_code == code).first()
    if not url:
        raise HTTPException(status_code=404, detail="Not found")
    url.clicks += 1
    db.commit()
    return RedirectResponse(url.original_url)