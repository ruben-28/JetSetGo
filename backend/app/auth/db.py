"""
Fichier: backend/app/auth/db.py
Objectif: Configuration de la base de données SQL Server.
Responsabilités:
- Création du moteur SQLAlchemy (Engine).
- Gestion des sessions (SessionLocal).
- Dépendance `get_db` pour FastAPI.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.db.config import DATABASE_URL

# Configuration du moteur SQL Server
# L'argument `connect_args` n'est pas nécessaire (spécifique à SQLite)
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Mettre à True pour déboguer les requêtes SQL
    pool_pre_ping=True,  # Vérifie les connexions avant utilisation
    pool_recycle=3600,  # Recycle les connexions après 1 heure
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dépendance FastAPI pour les sessions de base de données.
    Fournit une session DB et s'assure qu'elle est fermée après utilisation.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
