from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, nullable=False)

    extracted_text = Column(Text)
    summary = Column(Text)

    status = Column(String, default="processing")
    created_at = Column(DateTime(timezone=True), server_default=func.now())