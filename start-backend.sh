#!/bin/bash
echo "========================================"
echo "  Unify - Starting Backend Server"
echo "========================================"
echo ""

cd "$(dirname "$0")/backend"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed."
    echo "Please install Python 3.10+ first."
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create uploads directory
mkdir -p uploads

# Generate test data
echo "Generating test data..."
python generate_test_data.py

# Start the server
echo ""
echo "========================================"
echo "  Backend running at http://localhost:8000"
echo "  API docs at http://localhost:8000/docs"
echo "========================================"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
