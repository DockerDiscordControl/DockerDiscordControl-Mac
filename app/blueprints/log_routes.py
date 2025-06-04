# -*- coding: utf-8 -*-
from flask import Blueprint, Response, current_app, redirect, url_for, request
import os
import subprocess
import logging
import time
from functools import wraps
# Import auth from app.auth
from app.auth import auth 

log_bp = Blueprint('log_bp', __name__)

# Simple rate limiting for log requests
_last_log_request = {}  # IP -> timestamp
_min_request_interval = 60.0  # Increased to 60 seconds to match client-side auto-refresh interval

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get client IP (simplified)
        client_ip = request.remote_addr if 'request' in globals() else 'unknown'
        
        # Check if the last request from this IP was too recent
        current_time = time.time()
        if client_ip in _last_log_request:
            elapsed = current_time - _last_log_request[client_ip]
            if elapsed < _min_request_interval:
                return Response(
                    "TOO MANY REQUESTS: Please wait before requesting logs again.", 
                    status=429, 
                    mimetype='text/plain'
                )
        
        # Update the timestamp of the last request
        _last_log_request[client_ip] = current_time
        
        # Limit the size of the dictionary
        if len(_last_log_request) > 1000:  # Maximum number of IPs in cache
            # Remove oldest entries
            sorted_ips = sorted(_last_log_request.items(), key=lambda x: x[1])
            _last_log_request.clear()
            _last_log_request.update(dict(sorted_ips[-500:]))  # Keep only the newest 500
        
        return f(*args, **kwargs)
    return decorated_function

@log_bp.route('/logs')
# Use direct auth decorator
@auth.login_required
@rate_limit 
def get_logs():
    logger = current_app.logger
    # Alternative approach: Retrieve Docker container logs instead of action log
    try:
        # Limit number of lines (increased to 500)
        max_lines = 500
        
        # Option 1: Direct access to Docker log file (if known and accessible)
        docker_log_path = "/var/log/supervisor/discordbot-stdout.log"
        logs = ""
        
        if os.path.exists(docker_log_path):
            # If the log file exists, read it directly
            with open(docker_log_path, 'r', encoding='utf-8', errors='replace') as f:
                # Implement tail functionality
                lines = f.readlines()
                logs = ''.join(lines[-max_lines:]) if lines else "No logs available."
        else:
            # Option 2: If direct access isn't possible, try via Docker command
            try:
                # Run 'docker logs ddc --tail=500' to get the last 500 log lines
                result = subprocess.run(
                    ['docker', 'logs', 'ddc', f'--tail={max_lines}'], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                logs = result.stdout
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                logger.error(f"Failed to run docker command: {str(e)}")
                logs = "Could not retrieve container logs. Please check the logs for details."
    except Exception as e:
        logs = "Error accessing container logs. Please check the logs for details."
        logger.error(f"Error accessing container logs: {str(e)}", exc_info=True)
    
    return Response(logs, mimetype='text/plain')

@log_bp.route('/get_logs') # Old route, redirects to /logs
# Use direct auth decorator
@auth.login_required
def get_logs_old():
    return redirect(url_for('.get_logs')) # Use relative endpoint for blueprint 