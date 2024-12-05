from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from .paper import Base

class Citation(Base):
    __tablename__ = 'citations'

    citing_paper_id = Column(Integer, ForeignKey('papers.id'), primary_key=True)
    cited_paper_id = Column(Integer, ForeignKey('papers.id'), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)