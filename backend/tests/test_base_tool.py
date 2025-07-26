import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Agregar path del backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.base_tool import BaseTool, ToolExecutionResult, ParameterDefinition

class TestShellTool(BaseTool):
    """Test implementation of BaseTool for testing"""
    
    def __init__(self):
        super().__init__()
        self.name = "test_shell"
        self.description = "Test shell tool"
        self.parameters = [
            ParameterDefinition(
                name="command",
                description="Test command",
                required=True,
                type="string"
            )
        ]

    def execute(self, params: dict, config: dict = None) -> ToolExecutionResult:
        command = params.get('command', '')
        return ToolExecutionResult(
            success=True,
            output=f"Executed: {command}",
            execution_time=0.1
        )

class TestBaseTool:
    """Test suite for BaseTool abstraction"""
    
    def test_base_tool_initialization(self):
        """Test that BaseTool can be properly initialized"""
        tool = TestShellTool()
        assert tool.name == "test_shell"
        assert tool.description == "Test shell tool"
        assert len(tool.parameters) == 1
        assert tool.parameters[0].name == "command"

    def test_parameter_validation_success(self):
        """Test successful parameter validation"""
        tool = TestShellTool()
        params = {"command": "echo hello"}
        
        validated = tool.validate_parameters(params)
        assert validated["command"] == "echo hello"

    def test_parameter_validation_missing_required(self):
        """Test parameter validation with missing required parameter"""
        tool = TestShellTool()
        params = {}
        
        with pytest.raises(ValueError) as exc_info:
            tool.validate_parameters(params)
        assert "Required parameter 'command' is missing" in str(exc_info.value)

    def test_tool_execution(self):
        """Test tool execution"""
        tool = TestShellTool()
        params = {"command": "echo test"}
        
        result = tool.execute(params)
        assert isinstance(result, ToolExecutionResult)
        assert result.success is True
        assert "Executed: echo test" in result.output
        assert result.execution_time == 0.1

    def test_tool_execution_with_timing(self):
        """Test that tool execution includes timing"""
        tool = TestShellTool()
        params = {"command": "sleep 0.1"}
        
        with patch('time.time', side_effect=[0, 0.15]):
            result = tool.execute_with_timing(params)
            assert result.execution_time == 0.15