from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID, uuid4


class SkillCatalog(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True, unique=True)
    category: str = Field(default="general")
    is_custom: bool = Field(default=False)
    idUser: Optional[UUID] = Field(default=None, foreign_key="user.id", nullable=True)
