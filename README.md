# ✈️ JetSetGo - Travel with AI

![JetSetGo Banner](desktop/app/assets/logo.jpg)

**JetSetGo** est une application de voyage moderne intégrant l'Intelligence Artificielle pour offrir une expérience de réservation personnalisée (Vols, Hôtels, Activités). 

Ce projet a été réalisé dans le cadre du projet de fin de semestre "Systèmes Windows" (Hiver 2026).

---

## 🏛️ Architecture Académique

Le projet respecte scrupuleusement les spécifications architecturales suivantes :

### 1. Architecture Distribuée Multi-Tiers
- **Frontend Desktop (PySide6)** : Application riche implémentant le pattern **MVP (Model-View-Presenter)** et une architecture **Microfrontends**.
- **Backend (FastAPI)** : API RESTful structurée selon le pattern **CQRS (Command-Query Responsibility Segregation)**.
- **Event Sourcing** : Persistance basée sur les événements (les événements sont la source de vérité, projetés ensuite dans un Read Model).
- **API Gateway** : Point d'accès centralisé vers les services externes (Amadeus, Hugging Face).

### 2. Intégration IA & Cloud
- **Analyse de Sentiment** : Utilisation de modèles **Hugging Face** pour analyser les préférences utilisateur.
- **Agent Intelligent** : Assistant virtuel capable de naviguer dans l'interface et de pré-remplir les formulaires (LLM/Ollama).
- **Fournisseur de Voyage** : Intégration complète de l'API **Amadeus** pour les données de vol et d'hôtel en temps réel.

---

## 🚀 Installation & Démarrage

### Prérequis
- Python 3.10+
- Clés API (Amadeus, Hugging Face - voir `.env.example`)
- (Optionnel) Ollama pour l'assistant local

### 1. Configuration de l'Environnement

Clonez le projet et configurez les variables d'environnement :

```powershell
# Cloner le dépôt
git clone <url-repo>
cd JetSetGo

# Créer un environnement virtuel
python -m venv venv
.\venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les clés API
copy .env.example .env
# ÉDITER LE FICHIER .env AVEC VOS CLÉS !
```

### 2. Démarrer le Backend (API)

```powershell
# Depuis la racine du projet
uvicorn backend.app.main:app --reload
```
*L'API sera accessible sur http://127.0.0.1:8000/docs*

### 3. Démarrer l'Application Desktop

```powershell
# Dans un nouveau terminal (toujours avec venv activé)
python desktop/app/main.py
```

---

## 📚 Fonctionnalités

1.  **Recherche de Vols** : Autocomplétion, dates, filtres (Amadeus API).
2.  **Réservation d'Hôtels** : Recherche par ville et réservation.
3.  **Packages** : Offres combinées Vol + Hôtel.
4.  **Historique (Event Sourcing)** : Visualisation des voyages passés et graphiques de dépenses.
5.  **Assistant IA** : Chatbot contextuel capable de piloter l'application.

---

## 🛠️ Stack Technique

- **Langage** : Python 3.10+
- **Frontend** : PySide6 (Qt for Python), QtCharts
- **Backend** : FastAPI, SQLAlchemy, SQLite (Event Store)
- **IA** : Hugging Face Inference API, Ollama (LangChain compatible)
- **Services** : Amadeus for Developers

---

## 👥 Auteur

Projet réalisé par **Ruben** pour le cours de Systèmes Windows.
