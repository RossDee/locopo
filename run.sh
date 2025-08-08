#!/bin/bash
# Locopon - Swedish Retail Deals Intelligence System  
# Linux/macOS startup script

echo "Starting Locopon..."

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run Locopon
python main.py "$@"
