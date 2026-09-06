from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4

class Experience(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(default="")
    company: str = Field(default="")
    start_date: datetime = Field(default=None)
    end_date: Optional[datetime] = None
    description: str = Field(default="")
    at_Created: datetime = Field(default_factory=datetime.utcnow)
    at_Updated: datetime = Field(default_factory=datetime.utcnow)
    idUser: UUID = Field(foreign_key="user.id")