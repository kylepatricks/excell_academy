# run_windows.py
#!/usr/bin/env python
"""
Windows development server script for Excel Academy
"""
import os
import sys
import socket
from waitress import serve
from django.core.management import execute_from_command_line

def get_ip_address():
    """Get local IP address"""
    try:
        # Connect to a remote server to get local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def run_windows_server():
    """Run Waitress server for Windows"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excell_academy.settings.dev')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Couldn't import Django.") from exc
    
    # Collect static files
    print("Collecting static files...")
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    
    # Run migrations
    print("Running migrations...")
    execute_from_command_line(['manage.py', 'migrate', '--noinput'])
    
    # Start Waitress server
    ip_address = get_ip_address()
    print(f"\n🚀 Starting Excel Academy on Windows...")
    print(f"📍 Local: http://127.0.0.1:8000")
    print(f"📍 Network: http://{ip_address}:8000")
    print("Press Ctrl+C to stop the server\n")
    
    from excell_academy.wsgi import application
    serve(application, host='0.0.0.0', port=8000)

if __name__ == '__main__':
    run_windows_server()