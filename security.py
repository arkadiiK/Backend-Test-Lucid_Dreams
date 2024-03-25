from passlib.context import CryptContext
from fastapi import HTTPException, Header, Depends
from sqlalchemy.orm import Session

from models import User
from database import SessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


from jose import JWTError, jwt

SECRET_KEY = "KmANErD4fg3BVaevMBYlJZbFA8fbLaBu"
ALGORITHM = "HS256"


def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_token(authorization: str = Header(...)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.split()[1]
    return token


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(token: str = Depends(get_token), db: Session = Depends(SessionLocal)):
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    email: str = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
