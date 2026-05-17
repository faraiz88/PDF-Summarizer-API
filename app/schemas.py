from pydantic import BaseModel
from datetime import datetime


class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    stored_filename: str
    status: str
    summary: str | None = None
    created_at: datetime
    class Config:
        from_attributes = True