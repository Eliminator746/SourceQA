#!/usr/bin/env bash
set -o errexit

# 1. System dependency required by python-magic
apt-get update && apt-get install -y libmagic1

# 2. Backend/Python dependencies
pip install -r requirements.txt

# 3. Frontend environment variables
cp /etc/secrets/.env.production frontend/.env.production

# 4. Build React frontend
cd frontend
npm install
npm run build