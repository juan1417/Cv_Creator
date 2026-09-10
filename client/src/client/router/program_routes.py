from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from sqlmodel import Session, select

from database.DB import get_engine
from models.program import Program

router = APIRouter(prefix="/api/programs", tags=["programs"])


class ProgramResponse(BaseModel):
    id: str
    name: str


class AddProgramRequest(BaseModel):
    user_id: UUID
    name: str


@router.post("", response_model=ProgramResponse, status_code=201)
async def add_program(req: AddProgramRequest):
    engine = get_engine()
    with Session(engine) as session:
        # Check duplicate
        existing = session.exec(
            select(Program).where(Program.idUser == req.user_id, Program.name == req.name)
        ).first()
        if existing:
            return ProgramResponse(id=str(existing.id), name=existing.name or "")

        prog = Program(name=req.name, idUser=req.user_id)
        session.add(prog)
        session.commit()
        session.refresh(prog)
        return ProgramResponse(id=str(prog.id), name=prog.name or "")


@router.delete("/{program_id}")
async def delete_program(program_id: UUID, user_id: UUID):
    engine = get_engine()
    with Session(engine) as session:
        prog = session.get(Program, program_id)
        if not prog or prog.idUser != user_id:
            raise HTTPException(status_code=404, detail="Programa no encontrado")
        session.delete(prog)
        session.commit()
        return {"message": "Programa eliminado"}
