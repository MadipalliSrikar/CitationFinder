# Desc: Import all models from shared/shared/models
from .paper import Paper, Base, paper_authors  # Remove citations
from .author import Author

__all__ = ['Paper', 'Author', 'Base', 'paper_authors']