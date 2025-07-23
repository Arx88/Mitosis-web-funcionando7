#!/usr/bin/env python3
"""
Test with log monitoring to see if override logic executes
"""

import requests
import json
import subprocess
import time
import threading

BACKEND_URL = "http://localhost:8001"

def monitor_logs():
    """Monitor logs in background"""
    try:
        # Monitor logs for our specific messages  
        proc = subprocess.Popen(
            ['tail', '-f', '/var/log/supervisor/backend.out.log'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        for line in iter(proc.stdout.readline, ''):
            if any(keyword in line for keyword in ['🎯', '🔄', '🗺️', 'Overriding', 'Forcing', 'Corrected']):
                print(f"[LOG] {line.strip()}")
                
    except Exception as e:
        print(f"Log monitoring error: {e}")

def test_with_logs():
    """Test with log monitoring"""
    
    # Start log monitoring in background
    log_thread = threading.Thread(target=monitor_logs, daemon=True)
    log_thread.start()
    
    time.sleep(1)  # Give time for log monitoring to start
    
    print("🧪 Testing with Log Monitoring")
    print("=" * 40)
    
    task = "Buscar restaurantes en Valencia"
    print(f"Testing: {task}")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/agent/chat",
            json={"message": task},
            headers={"Content-Type": "application/json"},
            timeout=25
        )
        
        if response.status_code == 200:
            data = response.json()
            icon = data.get('plan', {}).get('suggested_icon', 'NOT_FOUND')
            print(f"Final icon: {icon}")
        else:
            print(f"Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    
    time.sleep(2)  # Give time for logs to flush

if __name__ == "__main__":
    test_with_logs()