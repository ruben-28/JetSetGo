"""
Module de Configuration Base de Données
Configuration centralisée pour la connexion SQL Server via pyodbc.
"""

import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()


def get_database_url() -> str:
    """
    Génère l'URL DATABASE_URL SQL Server utilisant le format odbc_connect.
    
    Ce format évite les problèmes avec les caractères spéciaux dans les mots de passe.
    Supporte ODBC Driver 18 (préféré) ou se replie sur 17.
    
    Returns:
        str: Chaîne de connexion SQLAlchemy pour SQL Server
        
    Environment Variables Required:
        - DB_SERVER: Hôte SQL Server (ex: jetsetgo_db.mssql.somee.com)
        - DB_NAME: Nom de la base (ex: jetsetgo_db)
        - DB_USER: Login SQL Server (ex: ethan5_SQLLogin_1)
        - DB_PASSWORD: Mot de passe SQL Server
    """
    server = os.getenv("DB_SERVER", "jetsetgo_db.mssql.somee.com")
    database = os.getenv("DB_NAME", "jetsetgo_db")
    username = os.getenv("DB_USER", "ethan5_SQLLogin_1")
    password = os.getenv("DB_PASSWORD", "")
    
    if not password:
        raise ValueError(
            "La variable d'environnement DB_PASSWORD est requise. "
            "Veuillez la définir dans votre fichier .env."
        )
    
    # Essayer ODBC Driver 18 d'abord (plus récent), repli sur 17
    # TrustServerCertificate=yes est requis pour les certificats auto-signés (commun sur somee)
    driver = "ODBC Driver 18 for SQL Server"
    
    # Construire la chaîne de connexion avec le format odbc_connect
    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
    )
    
    # Encoder la chaîne de connexion pour l'URL
    params = quote_plus(connection_string)
    
    # Retourner l'URL compatible SQLAlchemy
    return f"mssql+pyodbc:///?odbc_connect={params}"


# DATABASE_URL globale
DATABASE_URL = get_database_url()
