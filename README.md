# ✈️ JetSetGo - Travel with AI

![JetSetGo Banner](desktop\assets\logo.jpeg)

**JetSetGo** is a modern travel application integrating Artificial Intelligence to offer a personalized booking experience (Flights, Hotels, Activities).

This project was developed as part of the end-of-semester project for the "Windows Systems" course (Winter 2026).

---

## 🏛️ Academic Architecture

The project strictly follows these architectural specifications:

### 1. Multi-Tier Distributed Architecture
- **Desktop Frontend (PySide6)**: A rich application implementing the **MVP (Model-View-Presenter)** pattern and a **Microfrontends** architecture.
- **Backend (FastAPI)**: RESTful API structured according to the **CQRS (Command-Query Responsibility Segregation)** pattern.
- **Event Sourcing**: Event-based persistence (events are the single source of truth, which are then projected into a Read Model).
- **API Gateway**: Centralized access point to external services (Amadeus, Hugging Face).

### 2. AI & Cloud Integration
- **Sentiment Analysis**: Use of **Hugging Face** models to analyze user preferences.
- **Intelligent Agent**: A virtual assistant capable of navigating the interface and pre-filling forms (LLM/Ollama).
- **Travel Provider**: Full integration of the **Amadeus** API for real-time flight and hotel data.

---

## 🚀 Installation & Getting Started

### Prerequisites
- Python 3.10+
- API Keys (Amadeus, Hugging Face - see `.env.example`)
- (Optional) Ollama for the local assistant

### 1. Environment Setup

Clone the project and configure the environment variables:

```powershell
# Clone the repository
git clone <url-repo>
cd JetSetGo

# Create a virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
copy .env.example .env
# EDIT THE .env FILE WITH YOUR KEYS!
```

### 2. Start the Backend (API)

```powershell
# From the project root
uvicorn backend.app.main:app --reload
```
*The API will be accessible at http://127.0.0.1:8000/docs*

### 3. Start the Desktop Application

```powershell
# In a new terminal (still with venv activated)
python desktop/app/main.py
```

---

## 📚 Features

1.  **Flight Search**: Autocompletion, dates, filters (Amadeus API).
2.  **Hotel Booking**: Search by city and booking.
3.  **Packages**: Combined Flight + Hotel offers.
4.  **History (Event Sourcing)**: Visualization of past trips and expense charts.
5.  **AI Assistant**: Contextual chatbot capable of controlling the application.

---

## 🛠️ Technical Stack

- **Language**: Python 3.10+
- **Frontend**: PySide6 (Qt for Python), QtCharts
- **Backend**: FastAPI, SQLAlchemy, SQLite (Event Store)
- **AI**: Hugging Face Inference API, Ollama (LangChain compatible)
- **Services**: Amadeus for Developers

---

## 👥 Authors

Project created by **Ethan Sarfati** and **Ruben Bensimon** for the Windows Systems course.
