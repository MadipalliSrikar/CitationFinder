# Desc: Author model for the shared service
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from .paper import paper_authors, Base

class Author(Base):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    papers = relationship(
        "Paper",
        secondary=paper_authors,
        back_populates="authors",
        cascade="all, delete"
    )
