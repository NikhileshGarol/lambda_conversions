from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post("/login", status_code=status.HTTP_200_OK)
def login(username: str, password: str, db: Session = Depends(get_db)):
    # Placeholder logic for user authentication
    user = db.execute(
        "SELECT * FROM users WHERE username = :username AND password = :password",
        {"username": username, "password": password}
    ).fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    return {"message": "Login successful", "user_id": user.id}