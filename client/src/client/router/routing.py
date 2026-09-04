from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/validate_session")
async def validate_session(email: str, password: str):
    """Validate a user's session."""
    from database.get_user import validate_seccion
    is_valid = validate_seccion(email, password)
    if is_valid:
        return JSONResponse(content={"message": "Session is valid"}, status_code=200)
    else:
        raise HTTPException(status_code=401, detail="Invalid session")

@router.get("/get_user_by_email")
async def get_user_by_email(email: str):
    """Get a user by email."""
    from database.get_user import get_user_by_email
    user = get_user_by_email(email)
    if user:
        return JSONResponse(content={"id": str(user.id), "username": user.username, "email": user.email}, status_code=200)
    else:
        raise HTTPException(status_code=404, detail="User not found")