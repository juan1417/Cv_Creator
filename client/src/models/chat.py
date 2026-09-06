from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_session"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(default="Nueva conversación")
    target_job: Optional[str] = None
    at_Created: datetime = Field(default_factory=datetime.utcnow)
    at_Updated: datetime = Field(default_factory=datetime.utcnow)
    idUser: UUID = Field(foreign_key="user.id")

class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_message"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="chat_session.id")
    role: str = Field(...)
    content: str = Field(...)
    at_Created: datetime = Field(default_factory=datetime.utcnow)
    idUser: UUID = Field(foreign_key="user.id")
