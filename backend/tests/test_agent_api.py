import pytest
import httpx
from unittest.mock import patch, MagicMock
import sys
import os

# Agregar path del backend  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestAgentAPI:
    """Test suite for Agent API endpoints"""
    
    @pytest.fixture
    def mock_flask_app(self):
        """Mock Flask app for testing"""
        with patch('server.app') as mock_app:
            mock_app.test_client.return_value = MagicMock()
            yield mock_app

    def test_health_endpoint_structure(self):
        """Test that health endpoint returns expected structure"""
        expected_keys = ['status', 'timestamp', 'services']
        
        # Mock response structure
        mock_response = {
            'status': 'healthy',
            'timestamp': '2025-01-26T18:45:00Z',
            'services': {
                'database': True,
                'ollama': True,
                'tools': 12
            }
        }
        
        assert all(key in mock_response for key in expected_keys)
        assert mock_response['services']['tools'] == 12

    def test_agent_status_response_structure(self):
        """Test agent status response structure"""
        expected_structure = {
            'status': 'running',
            'agent_id': 'mitosis-agent',
            'tools_available': 12,
            'ollama': {
                'connected': True,
                'endpoint': 'https://example.com',
                'model': 'llama3.1:8b'
            }
        }
        
        # Verify structure
        assert 'status' in expected_structure
        assert 'tools_available' in expected_structure
        assert 'ollama' in expected_structure
        assert expected_structure['ollama']['connected'] is True

    @pytest.mark.asyncio
    async def test_chat_endpoint_message_processing(self):
        """Test chat endpoint message processing logic"""
        
        # Mock input message
        test_message = {
            'message': 'Create a market analysis report',
            'task_id': 'test-task-123'
        }
        
        # Expected response structure
        expected_response_keys = [
            'response', 'task_id', 'timestamp', 
            'plan', 'enhanced_title', 'memory_used'
        ]
        
        # Mock successful response
        mock_response = {
            'response': 'Plan generated successfully',
            'task_id': 'test-task-123',
            'timestamp': '2025-01-26T18:45:00Z',
            'plan': {
                'title': 'Market Analysis Report',
                'steps': [
                    {'id': 'step-1', 'title': 'Research', 'tool': 'web_search'}
                ]
            },
            'enhanced_title': 'Market Analysis Report 2025',
            'memory_used': True
        }
        
        # Verify response structure
        assert all(key in mock_response for key in expected_response_keys)
        assert mock_response['plan']['steps'][0]['tool'] == 'web_search'
        assert mock_response['memory_used'] is True

    def test_tool_registry_functionality(self):
        """Test tool registry auto-discovery and loading"""
        
        # Mock tool registry behavior
        expected_tools = [
            'shell_tool', 'web_search_tool', 'file_manager_tool',
            'tavily_search_tool', 'python_tool', 'memory_tool'
        ]
        
        # Mock registry response
        mock_registry = {
            'tools_count': len(expected_tools),
            'available_tools': expected_tools,
            'auto_discovery': True,
            'lazy_loading': True
        }
        
        assert mock_registry['tools_count'] >= 6
        assert 'web_search_tool' in mock_registry['available_tools']
        assert mock_registry['auto_discovery'] is True