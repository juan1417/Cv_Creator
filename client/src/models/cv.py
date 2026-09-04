from sqlmodel import Model, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

class CV(Model, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(default="")
    email: str = Field(default="")
    phone: str = Field(default="")
    address: str = Field(default="")
    about: str = Field(default="")
    porfolio: str = Field(default="")
    linkedin: Optional[str] = None
    at_Created: datetime = Field(default=None, default_factory=datetime.utcnow)
    at_Updated: datetime = Field(default=None, default_factory=datetime.utcnow)
    idUser: UUID = Field(foreign_key="user.id")
