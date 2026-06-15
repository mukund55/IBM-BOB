#!/bin/bash

echo "========================================"
echo " Data Quality Web Application Launcher"
echo "========================================"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org/downloads/"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "[1/5] Checking virtual environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo "Virtual environment created successfully!"
else
    echo "Virtual environment already exists."
fi

echo ""
echo "[2/5] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "[3/5] Checking dependencies..."
if [ ! -d "venv/lib/python"*"/site-packages/flask" ]; then
    echo "Installing dependencies (this may take 5-10 minutes)..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo "Dependencies installed successfully!"
else
    echo "Dependencies already installed."
fi

echo ""
echo "[4/5] Checking database..."
if [ ! -f "dq_webapp.db" ]; then
    echo "Initializing database..."
    python init_db.py
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to initialize database"
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo "Database initialized successfully!"
    echo ""
    echo "DEFAULT LOGIN CREDENTIALS:"
    echo "Username: admin"
    echo "Password: admin123"
    echo ""
else
    echo "Database already exists."
fi

echo ""
echo "[5/5] Starting Flask application..."
echo ""
echo "========================================"
echo " Application is starting..."
echo " URL: http://localhost:5000/dashboard"
echo " Press Ctrl+C to stop the server"
echo "========================================"
echo ""

python app.py

# Made with Bob
