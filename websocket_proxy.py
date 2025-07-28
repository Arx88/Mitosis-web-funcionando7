#!/usr/bin/env python3
"""
WebSocket Proxy para routing correcto
"""
import asyncio
import websockets
import requests
from flask import Flask, request, Response
import threading

app = Flask(__name__)

@app.route('/socket.io/<path:path>', methods=['GET', 'POST'])
def proxy_websocket(path):
    """Proxy WebSocket requests to backend"""
    url = f"http://localhost:8001/socket.io/{path}"
    
    # Forward query parameters
    if request.query_string:
        url += "?" + request.query_string.decode()
    
    # Forward headers
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'connection']}
    
    # Forward request to backend
    if request.method == 'GET':
        response = requests.get(url, headers=headers)
    else:
        response = requests.post(url, headers=headers, data=request.data)
    
    # Return response with proper headers
    return Response(
        response.content,
        status=response.status_code,
        headers=dict(response.headers)
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002, debug=False)
