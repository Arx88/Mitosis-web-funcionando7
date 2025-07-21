#!/usr/bin/env python3

from flask import Flask, jsonify
from datetime import datetime
import json

app = Flask(__name__)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "working", "timestamp": datetime.now().isoformat()})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8002, debug=False)