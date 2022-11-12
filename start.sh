#!/usr/bin/env sh
gunicorn -k  uvicorn.workers.UvicornWorker --bind 0.0.0.0:8282 -w 8 -t 0 app.server:app