#!/bin/bash

# Pokemon MCP Server - Quick Start Script

echo "🎮 Starting Pokemon MCP Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Check if dependencies are installed
if [ ! -f "venv/lib/python*/site-packages/fastapi/__init__.py" ] && [ ! -f "venv/Lib/site-packages/fastapi/__init__.py" ]; then
    echo "📚 Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the server
echo "🚀 Starting server on http://localhost:8000"
echo "📖 API docs available at http://localhost:8000/docs"
echo "🛑 Press Ctrl+C to stop"
echo ""

python app.py