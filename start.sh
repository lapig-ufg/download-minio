#!/usr/bin/env sh
gunicorn -k  uvicorn.workers.UvicornWorker --bind 0.0.0.0:8485 -w 4 -t 0 app.server:app