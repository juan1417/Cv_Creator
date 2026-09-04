from sqlmodel import Model, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4

class Education(Model, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    degree: str = Field(default="")
    institution: str = Field(default="")
    start_date: datetime = Field(default=None)
    end_date: Optional[datetime] = None
    description: str = Field(default="")
    at_Created: datetime = Field(default=None, default_factory=datetime.utcnow)
    at_Updated: datetime = Field(default=None, default_factory=datetime.utcnow)
    idUser: UUID = Field(foreign_key="user.id")