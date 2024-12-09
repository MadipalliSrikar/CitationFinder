# Description: Define the Paper model
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# Define tables first
paper_authors = Table(
    'paper_authors', Base.metadata,
    Column('paper_id', Integer, ForeignKey('papers.id')),
    Column('author_id', Integer, ForeignKey('authors.id'))
)

paper_citations = Table(
    'paper_citations', Base.metadata,
    Column('citing_paper_id', Integer, ForeignKey('papers.id', ondelete='CASCADE')),
    Column('cited_paper_id', Integer, ForeignKey('papers.id', ondelete='CASCADE'))
)

class Paper(Base):
    __tablename__ = 'papers'
    __table_args__ = {'extend_existing': True}
    
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
    
    # Citation relationships
    citing_papers = relationship(
        'Paper',
        secondary=paper_citations,
        primaryjoin=id==paper_citations.c.citing_paper_id,
        secondaryjoin=id==paper_citations.c.cited_paper_id,
        backref='cited_by'
    )