#!/bin/bash

# ============================================================================
# JetSetGo - SQL Server Migration Test Commands
# ============================================================================
# This file contains all commands to test the SQL Server migration.
# Windows users: Run these in cmd or PowerShell

echo "================================================"
echo "SQL Server Migration - Test Commands"
echo "================================================"

# ----------------------------------------------------------------------------
# 1. Install Dependencies
# ----------------------------------------------------------------------------
echo ""
echo "1. Installing dependencies..."
cd backend
pip install -r requirements.txt

# ----------------------------------------------------------------------------
# 2. Setup Environment Variables
# ----------------------------------------------------------------------------
echo ""
echo "2. Environment setup:"
echo "   Copy .env.example to .env and fill in DB_PASSWORD"
echo "   "
echo "   Example .env file:"
echo "   DB_SERVER=jetsetgo_db.mssql.somee.com"
echo "   DB_NAME=jetsetgo_db"
echo "   DB_USER=ethan5_SQLLogin_1"
echo "   DB_PASSWORD=your_actual_password_here"
echo "   JWT_SECRET=your_jwt_secret_here"

# Wait for user confirmation
read -p "Press Enter once .env is configured..."

# ----------------------------------------------------------------------------
# 3. Run Database Tests
# ----------------------------------------------------------------------------
echo ""
echo "3. Running database tests..."
python test_sql_server.py

# ----------------------------------------------------------------------------
# 4. Start Server
# ----------------------------------------------------------------------------
echo ""
echo "4. Starting FastAPI server..."
echo "   Server will run on http://localhost:8000"
echo "   Docs available at http://localhost:8000/docs"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
