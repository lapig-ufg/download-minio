from multiprocessing import cpu_count

# Socket Path
bind = 'unix:./gunicorn.sock'

# Worker Options
workers = cpu_count() + 1
worker_class = 'uvicorn.workers.UvicornWorker'

# Logging Options
timeout = 0
host = '0.0.0.0'
port = 8888
loglevel = 'debug'
accesslog = './access.log'
errorlog = './error.log'
