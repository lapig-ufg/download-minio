#!/bin/bash

source .env
ssh -p 2522 -fN root@$SERVER -L 5432:127.0.0.1:5432
cd /APP/pgrass-server
gunicorn -k  uvicorn.workers.UvicornWorker --bind 0.0.0.0:8282 -w 4 -t 0 app.server:app