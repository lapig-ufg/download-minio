from multiprocessing import cpu_count

# Socket Path
bind = 'unix:./gunicorn.sock'

# Worker Options
workers = int(cpu_count() / 2)
worker_class = 'uvicorn.workers.UvicornWorker'

# Logging Options
timeout = 0
host = '0.0.0.0'
port = 8080
loglevel = 'info'
accesslog = './access.log'
errorlog = './error.log'
