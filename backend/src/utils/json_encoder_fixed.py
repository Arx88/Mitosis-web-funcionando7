"""
JSON Encoder personalizado para manejar tipos de MongoDB
"""

import json
from bson.objectid import ObjectId
from datetime import datetime

class MongoJSONEncoder(json.JSONEncoder):
    """
    Encoder JSON personalizado para manejar tipos de MongoDB como ObjectId
    """
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(MongoJSONEncoder, self).default(obj)

def mongo_json_serializer(obj):
    """
    Función de serialización para objetos MongoDB
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

