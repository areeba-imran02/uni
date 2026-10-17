from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.models import User
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
def hash_password(p): return pwd.hash(p)
def verify_password(p,h): return pwd.verify(p,h)
def create_token(user_id): return jwt.encode({"sub":str(user_id),"exp":datetime.now(timezone.utc)+timedelta(hours=24)}, settings.secret_key, algorithm="HS256")
def current_user(token: str = Depends(oauth), db: Session = Depends(get_db)):
    try: uid=int(jwt.decode(token, settings.secret_key, algorithms=["HS256"])["sub"])
    except (JWTError, ValueError, KeyError): raise HTTPException(status_code=401, detail="Invalid or expired session")
    user=db.get(User,uid)
    if not user: raise HTTPException(status_code=401, detail="Account not found")
    return user
