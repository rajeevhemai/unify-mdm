#!/bin/bash
echo "========================================"
echo "  Unify - Starting Frontend"
echo "========================================"
echo ""

cd "$(dirname "$0")/frontend"

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed."
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start dev server
echo ""
echo "========================================"
echo "  Frontend running at http://localhost:5173"
echo "========================================"
echo ""
npm run dev
