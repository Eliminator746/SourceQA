#!/usr/bin/env bash
set -o errexit

# Install system dependency required by python-magic
apt-get update && apt-get install -y libmagic1

# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies and production build
cd frontend
npm install
npm run build