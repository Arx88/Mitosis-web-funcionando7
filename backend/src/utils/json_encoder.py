"""
JSON Encoder personalizado para manejar tipos de MongoDB
"""

import json
from datetime import datetime

try:
    from pymongo.bson import ObjectId
except ImportError:
    try:
        from bson import ObjectId
    except ImportError:
        # Fallback si no hay MongoDB disponible
        class ObjectId:
            def __init__(self, *args, **kwargs):
                pass

class MongoJSONEncoder(json.JSONEncoder):
    """
    Encoder JSON personalizado para manejar tipos de MongoDB como ObjectId
    """
    def default(self, obj):
        if hasattr(obj, '__class__') and obj.__class__.__name__ == 'ObjectId':
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(MongoJSONEncoder, self).default(obj)

def mongo_json_serializer(obj):
    """
    Función de serialización para objetos MongoDB
    """
    if hasattr(obj, '__class__') and obj.__class__.__name__ == 'ObjectId':
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

