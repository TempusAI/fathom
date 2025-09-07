#!/bin/bash

# Install dependencies if not already installed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

# Set the LUSID secrets path environment variable
export FBN_SECRETS_PATH="$(pwd)/../secrets.json"
echo "Set FBN_SECRETS_PATH to: $FBN_SECRETS_PATH"

# Verify the secrets file exists
if [ ! -f "$FBN_SECRETS_PATH" ]; then
    echo "ERROR: Secrets file not found at $FBN_SECRETS_PATH"
    exit 1
fi

echo "Starting Fathom backend server..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
