from typing import List

from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta

import models
from database import SessionLocal
from sqlalchemy.testing.pickleable import User
import schemas
from models import Post
from security import get_password_hash, SECRET_KEY, ALGORITHM, verify_password, get_token, decode_token
#from fastapi_cache import caches, close_caches
from fastapi_cache.backends.memory import CACHE_KEY
#from fastapi_cache.middleware import CacheControlMiddleware


# use the `cache` object to cache responses

app = FastAPI()
#cache = caches.get(CACHE_KEY)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.post("/signup")
# Check for a user with the same email address in the database
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(schemas.User).filter(schemas.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)

    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Generating an access token for a response
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token}


@app.post("/login/", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    # Checking the existence of a user and the correctness of the entered password
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token}


@app.post("/addPost/")
def add_post(post: schemas.PostCreate, request: Request, token: str = Depends(get_token),
             db: Session = Depends(get_db)):
    content_length = int(request.headers.get('content-length', 0))
    if content_length > 1024 * 1024:  # 1 MB limit
        raise HTTPException(status_code=400, detail="Payload size exceeds 1 MB limit")

    decoded_token = decode_token(token)
    if not decoded_token:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == decoded_token["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_post = Post(text=post.text, user_id=user.id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@app.get("/getPosts/", response_model=List[schemas.PostCreate])
def get_posts(token: str = Depends(get_token), db: Session = Depends(get_db)):
    decoded_token = decode_token(token)
    if not decoded_token:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.email == decoded_token["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    posts = db.query(models.Post).filter(models.Post.user_id == user.id).all()
    return posts


# app.add_middleware(
#     CacheControlMiddleware,
#     cache_timeout=300  # 5 minutes
# )




# @app.on_event("shutdown")
# def shutdown_event():
#     close_caches()


@app.get("/deletePost/{post_id}")
def delete_post(post_id: str, token: str = Depends(get_token), db: Session = Depends(get_db)):
    decoded_token = decode_token(token)
    if not decoded_token:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == decoded_token["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    db.delete(post)
    db.commit()

    return {"message": "Post deleted"}
