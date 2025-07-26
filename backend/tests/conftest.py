import pytest
import asyncio
import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_mongo_client():
    """Mock MongoDB client for testing"""
    class MockCollection:
        def __init__(self):
            self.data = []
            
        def insert_one(self, document):
            document['_id'] = f"mock_id_{len(self.data)}"
            self.data.append(document)
            return type('InsertResult', (), {'inserted_id': document['_id']})()
            
        def find_one(self, filter_dict=None):
            if not filter_dict:
                return self.data[0] if self.data else None
            for doc in self.data:
                if all(doc.get(k) == v for k, v in filter_dict.items()):
                    return doc
            return None
            
        def update_one(self, filter_dict, update_dict):
            for doc in self.data:
                if all(doc.get(k) == v for k, v in filter_dict.items()):
                    if '$set' in update_dict:
                        doc.update(update_dict['$set'])
                    return type('UpdateResult', (), {'modified_count': 1})()
            return type('UpdateResult', (), {'modified_count': 0})()
    
    class MockDatabase:
        def __init__(self):
            self.collections = {}
            
        def __getitem__(self, name):
            if name not in self.collections:
                self.collections[name] = MockCollection()
            return self.collections[name]
    
    class MockClient:
        def __init__(self):
            self.databases = {}
            
        def __getitem__(self, name):
            if name not in self.databases:
                self.databases[name] = MockDatabase()
            return self.databases[name]
            
        def close(self):
            pass
    
    return MockClient()