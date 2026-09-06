from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4

class Skills(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(default="")
    level: str = Field(default="")
    at_Created: datetime = Field(default_factory=datetime.utcnow)
    at_Updated: datetime = Field(default_factory=datetime.utcnow)
    idUser: UUID = Field(foreign_key="user.id")