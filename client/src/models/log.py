from sqlmodel import Model, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4


class LogEntry(Model, table=True):
    __tablename__ = "log_entries"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = Field(default="INFO", index=True)
    module: str = Field(default="", index=True)
    function: str = Field(default="")
    message: str = Field(default="")
    user_id: Optional[str] = Field(default=None, index=True)
    extra_data: Optional[str] = None
