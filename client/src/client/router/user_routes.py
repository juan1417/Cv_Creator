from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select

from ...database.DB import get_engine
from ...models.user import User
from argon2 import PasswordHasher

router = APIRouter(prefix="/api/users", tags=["users"])


class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str


class UpdateUserRequest(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str | None = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: str
    updated_at: str


def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        created_at=user.at_Created.isoformat() if user.at_Created else "",
        updated_at=user.at_Updated.isoformat() if user.at_Updated else "",
    )


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(req: CreateUserRequest):
    engine = get_engine()
    with Session(engine) as session:
        existing = session.exec(
            select(User).where((User.email == req.email) | (User.username == req.username))
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="El email o username ya está registrado")

        ph = PasswordHasher()
        user = User(
            username=req.username,
            email=req.email,
            hashed_password=ph.hash(req.password),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        return _user_to_response(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID):
    engine = get_engine()
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return _user_to_response(user)


@router.get("/by-email/{email}", response_model=UserResponse)
async def get_user_by_email(email: str):
    engine = get_engine()
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return _user_to_response(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: UUID, req: UpdateUserRequest):
    engine = get_engine()
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if req.username is not None:
            conflict = session.exec(
                select(User).where(User.username == req.username, User.id != user_id)
            ).first()
            if conflict:
                raise HTTPException(status_code=409, detail="El username ya está en uso")
            user.username = req.username

        if req.email is not None:
            conflict = session.exec(
                select(User).where(User.email == req.email, User.id != user_id)
            ).first()
            if conflict:
                raise HTTPException(status_code=409, detail="El email ya está en uso")
            user.email = req.email

        if req.password is not None:
            ph = PasswordHasher()
            user.hashed_password = ph.hash(req.password)

        user.at_Updated = datetime.utcnow()
        session.add(user)
        session.commit()
        session.refresh(user)

        return _user_to_response(user)


@router.delete("/{user_id}")
async def delete_user(user_id: UUID):
    engine = get_engine()
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        session.delete(user)
        session.commit()

        return {"message": "Usuario eliminado correctamente"}
