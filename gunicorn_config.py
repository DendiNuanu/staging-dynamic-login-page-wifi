# Gunicorn configuration for zero-downtime deployments
# This file should be used with: gunicorn -c gunicorn_config.py app:app

import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Optimal worker count
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "wifi-hotspot-app"

# Server mechanics
daemon = False
pidfile = "/var/run/gunicorn/wifi-hotspot.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# Graceful timeout for zero-downtime reloads
graceful_timeout = 30  # Time to wait for workers to finish requests before killing them

# Preload app for faster worker spawn
preload_app = True

# Worker lifecycle
max_requests = 1000  # Restart workers after this many requests (prevents memory leaks)
max_requests_jitter = 50  # Add randomness to max_requests

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

