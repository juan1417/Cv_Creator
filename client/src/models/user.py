from sqlmodel import Model, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4

class User(Model, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    at_Created: datetime = Field(default=None, default_factory=datetime.utcnow)
    at_Updated: datetime = Field(default=None, default_factory=datetime.utcnow)