from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Association table for paper-author relationship
paper_authors = Table(
    'paper_authors',
    Base.metadata,
    Column('paper_id', Integer, ForeignKey('papers.id')),
    Column('author_id', Integer, ForeignKey('authors.id'))
)

class Paper(Base):
    __tablename__ = 'papers'

    id = Column(Integer, primary_key=True)
    pmid = Column(String(20), unique=True, index=True)
    title = Column(Text, nullable=False)
    abstract = Column(Text)
    publication_date = Column(DateTime)
    journal = Column(String(255))
    full_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    authors = relationship("Author", secondary=paper_authors, back_populates="papers")
    citations = relationship(
        "Paper",
        secondary="citations",
        primaryjoin="Paper.id==citations.c.citing_paper_id",
        secondaryjoin="Paper.id==citations.c.cited_paper_id",
        backref="cited_by"
    )