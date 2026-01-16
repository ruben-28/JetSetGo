# 🎯 Migration SQLite → SQL Server - Récapitulatif Technique

## ✅ Mission Accomplie

Migration complète du backend FastAPI de **SQLite local** vers **SQL Server cloud (somee)** avec préservation de l'architecture **CQRS + Event Sourcing**.

---

## 📦 Changements par Fichier

### 1. [app/db/config.py](file:///c:/Users/ethan/OneDrive/Bureau/JetSetGo/backend/app/db/config.py) (NOUVEAU)

**Configuration centralisée avec odbc_connect** :

```python
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os

def get_database_url() -> str:
    server = os.getenv("DB_SERVER", "jetsetgo_db.mssql.somee.com")
    database = os.getenv("DB_NAME", "jetsetgo_db")
    username = os.getenv("DB_USER", "ethan5_SQLLogin_1")
    password = os.getenv("DB_PASSWORD", "")
    
    driver = "ODBC Driver 18 for SQL Server"
    
    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"TrustServerCertificate=yes;"
    )
    
    params = quote_plus(connection_string)
    return f"mssql+pyodbc:///?odbc_connect={params}"

DATABASE_URL = get_database_url()
```

**Points clés** :
- ✅ Format `odbc_connect` (pas `user:pass@host`)
- ✅ Support ODBC Driver 18 (ou 17)
- ✅ `TrustServerCertificate=yes` pour somee
- ✅ Gestion automatique des caractères spéciaux

---

### 2. [app/auth/db.py](file:///c:/Users/ethan/OneDrive/Bureau/JetSetGo/backend/app/auth/db.py)

**Changements** :
```diff
- DATABASE_URL = "sqlite:///./jetsetgo_auth.db"
+ from app.db.config import DATABASE_URL

  engine = create_engine(
      DATABASE_URL,
-     connect_args={"check_same_thread": False}  # SQLite
+     echo=False,
+     pool_pre_ping=True,
+     pool_recycle=3600,
  )
```

**Tables gérées** : `users`, `bookings`

---

### 3. [app/db/event_store.py](file:///c:/Users/ethan/OneDrive/Bureau/JetSetGo/backend/app/db/event_store.py)

**Changements** :
```diff
- def __init__(self, db_path: Optional[str] = None):
-     if db_path is None:
-         backend_dir = os.path.dirname(...)
-         db_path = os.path.join(backend_dir, "jetsetgo_events.db")
-     self.engine = create_engine(f"sqlite:///{db_path}", echo=False)

+ def __init__(self):
+     from app.db.config import DATABASE_URL
+     self.engine = create_engine(
+         DATABASE_URL,
+         echo=False,
+         pool_pre_ping=True,
+         pool_recycle=3600,
+     )
```

**Table gérée** : `events`

> [!NOTE]
> Auth et Event Store partagent la **même base de données cloud**.

---

### 4. [requirements.txt](file:///c:/Users/ethan/OneDrive/Bureau/JetSetGo/backend/requirements.txt)

```diff
  fastapi
  uvicorn[standard]
  python-jose[cryptography]
  passlib[bcrypt]
  pydantic
  sqlalchemy
  httpx
  python-dotenv
+ pyodbc
```

---

### 5. [.env.example](file:///c:/Users/ethan/OneDrive/Bureau/JetSetGo/backend/.env.example)

```diff
+ # Database Configuration (SQL Server Cloud)
+ DB_SERVER=jetsetgo_db.mssql.somee.com
+ DB_NAME=jetsetgo_db
+ DB_USER=ethan5_SQLLogin_1
+ DB_PASSWORD=YOUR_PASSWORD_HERE
+
  # Authentication & Security
  JWT_SECRET=CHANGE_ME_SUPER_SECRET
  JWT_EXPIRE_MINUTES=1440
```

---

## 🧪 Scripts de Test Créés

### [test_sql_server.py](file:///c:/Users/ethan/OneDrive/Bureau/JetSetGo/backend/test_sql_server.py)

Tests complets avec SQLAlchemy 2.0 :

```python
# Test 1: Connexion
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1 AS test")).scalar()

# Test 2: Tables auth (users, bookings)
Base.metadata.create_all(bind=engine)

# Test 3: Event Store (events)
event_store = get_event_store()

# Test 4: Vérification schémas
conn.execute(text(
    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
    "WHERE TABLE_NAME = 'users'"
))
```

---

## 🔑 Format DATABASE_URL (odbc_connect)

**Contrairement au format classique** :
```python
# ❌ Format classique (problèmes avec caractères spéciaux)
"mssql+pyodbc://user:p@ss!word@server/db?driver=..."

# ✅ Format odbc_connect (recommandé)
connection_string = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=...;UID=...;PWD=...;TrustServerCertificate=yes;"
params = quote_plus(connection_string)
DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={params}"
```

**Avantages** :
- Gère `@`, `!`, `$`, etc. dans le mot de passe
- Compatible somee.com
- Support certificats auto-signés

---

## 📋 Commandes de Test

### 1. Installation

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configuration

Créer `.env` :
```bash
cp .env.example .env
```

Éditer `.env` et remplir :
```env
DB_PASSWORD=votre_mot_de_passe_ici
JWT_SECRET=generer_avec_python_secrets
```

### 3. Test de Connexion

```bash
python test_sql_server.py
```

**Sortie attendue** :
```
✓ Database connection successful
✓ Auth tables created successfully
✓ Table 'users' exists
✓ Table 'bookings' exists
✓ Event store initialized
✓ Table 'events' exists
✓ Users table schema correct
✓ Events table schema correct
✓ Bookings table schema correct

🎉 All tests passed! SQL Server migration successful!
```

### 4. Démarrer le Serveur

```bash
uvicorn app.main:app --reload
```

### 5. Tester l'API

**Inscription** (SANS champ `phone`) :
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"Test123!"}'
```

**Connexion** :
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Test123!"}'
```

**Réponse** :
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "username": "testuser"
}
```

---

## 🏗️ Vérification create_all()

### Deux declarative_base() distincts

**Base 1 : Auth** ([app/auth/db.py](file:///c:/Users/ethan/OneDrive/Bureau/JetSetGo/backend/app/auth/db.py#L20))
```python
Base = declarative_base()
```
→ Crée `users` + `bookings` via [app/main.py:43](file:///c:/Users/ethan/OneDrive/Bureau/JetSetGo/backend/app/main.py#L43)

**Base 2 : Events** ([app/db/event_store.py](file:///c:/Users/ethan/OneDrive/Bureau/JetSetGo/backend/app/db/event_store.py#L21))
```python
Base = declarative_base()
```
→ Crée `events` via [event_store.py:71](file:///c:/Users/ethan/OneDrive/Bureau/JetSetGo/backend/app/db/event_store.py#L71)

✅ **Toutes les tables sont créées automatiquement au démarrage**

---

## 🎯 Architecture Préservée

### CQRS + Event Sourcing Intact

```
┌─────────────┐
│   Command   │ → Génère événement
└─────────────┘
       ↓
┌─────────────┐
│ Event Store │ → Table `events` (source of truth)
└─────────────┘
       ↓
┌─────────────┐
│ Projection  │ → Met à jour `bookings` (read model)
└─────────────┘
       ↓
┌─────────────┐
│   Query     │ → Lit depuis `bookings`
└─────────────┘
```

**Aucune modification de la logique métier** ✅

---

## 🗄️ Tables SQL Server

### Schéma Cloud (jetsetgo_db)

**users** (Auth)
- `id` INT PRIMARY KEY IDENTITY
- `username` VARCHAR(50) UNIQUE
- `email` VARCHAR(120) UNIQUE
- `password_hash` VARCHAR(255)
- `created_at` DATETIME DEFAULT GETDATE()

**bookings** (Read Model)
- `id` VARCHAR(36) PRIMARY KEY (UUID)
- `user_id` INT
- `offer_id` VARCHAR(100)
- `departure`, `destination` VARCHAR(100)
- `depart_date`, `return_date` VARCHAR(10)
- `price` FLOAT
- `adults` INT
- `status` VARCHAR(20)
- `created_at` DATETIME
- `event_id` VARCHAR(36)

**events** (Event Store)
- `id` INT PRIMARY KEY IDENTITY
- `event_id` VARCHAR(36) UNIQUE
- `aggregate_id` VARCHAR(36)
- `event_type` VARCHAR(100)
- `timestamp` DATETIME
- `data` TEXT (JSON)
- `version` INT

---

## 📝 Dépendances

### Python Packages

Fichier [requirements.txt](file:///c:/Users/ethan/OneDrive/Bureau/JetSetGo/backend/requirements.txt) :
```txt
fastapi
uvicorn[standard]
python-jose[cryptography]
passlib[bcrypt]
pydantic
sqlalchemy
httpx
python-dotenv
pyodbc              # ← NOUVEAU
```

### Driver ODBC

**Windows** :
- **ODBC Driver 18 for SQL Server** (recommandé)
- OU ODBC Driver 17 for SQL Server

Téléchargement : [Microsoft ODBC Driver](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

---

## 🚀 Prochaines Étapes

### Checklist Utilisateur

- [ ] Copier `.env.example` → `.env`
- [ ] Remplir `DB_PASSWORD` dans `.env`
- [ ] Générer `JWT_SECRET` (ex: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] Installer : `pip install -r requirements.txt`
- [ ] Tester : `python test_sql_server.py`
- [ ] Démarrer : `uvicorn app.main:app --reload`
- [ ] Tester API : curl register/login
- [ ] Tester Desktop App PySide6
- [ ] Vérifier Event Store (créer une réservation)

---

## 📚 Documentation Créée

| Fichier | Description |
|---------|-------------|
| [MIGRATION_GUIDE.md](file:///c:/Users/ethan/OneDrive/Bureau/JetSetGo/backend/MIGRATION_GUIDE.md) | Guide complet utilisateur |
| [test_sql_server.py](file:///c:/Users/ethan/OneDrive/Bureau/JetSetGo/backend/test_sql_server.py) | Script de test automatisé |
| [test_migration.sh](file:///c:/Users/ethan/OneDrive/Bureau/JetSetGo/backend/test_migration.sh) | Commandes shell (Linux/Mac) |

---

## ✨ Points Techniques Importants

> [!IMPORTANT]
> **odbc_connect obligatoire** : Format `user:pass@host` ne fonctionne pas avec caractères spéciaux dans le mot de passe.

> [!WARNING]
> **TrustServerCertificate=yes** : Requis pour somee.com (certificat auto-signé). Sans cela, erreur SSL.

> [!NOTE]
> **pool_pre_ping=True** : Vérifie que la connexion est vivante avant utilisation. Évite les erreurs "connection lost".

> [!TIP]
> **Debugging SQL** : Mettez `echo=True` dans `config.py` pour voir toutes les requêtes SQL en temps réel.

---

## 🎉 Résultat Final

✅ **SQLite local** → **SQL Server cloud (somee)**  
✅ **Format odbc_connect** avec gestion caractères spéciaux  
✅ **Auth + Event Store** sur même DB cloud  
✅ **CQRS + Event Sourcing** préservés  
✅ **Tests automatisés** SQLAlchemy 2.0  
✅ **Sécurité** : Mot de passe via `.env`  
✅ **Documentation complète** avec exemples curl

**Migration terminée avec succès ! 🚀**
