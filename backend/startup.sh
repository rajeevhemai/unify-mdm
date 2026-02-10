#!/bin/bash
# Azure App Service startup script
pip install -r requirements.txt
gunicorn startup:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120
