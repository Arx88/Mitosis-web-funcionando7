"""
Clase Base para Herramientas - Fase 4: Abstracción de Herramientas
Elimina duplicación de código y establece interfaz común para todas las herramientas
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import time
import logging
from datetime import datetime

# Configurar logging
logger = logging.getLogger(__name__)

class ToolExecutionResult:
    """Resultado estandarizado de ejecución de herramientas"""
    
    def __init__(self, success: bool = True, data: Dict[str, Any] = None, 
                 error: str = None, execution_time: float = 0.0,
                 tool_name: str = "", parameters: Dict[str, Any] = None):
        self.success = success
        self.data = data or {}
        self.error = error
        self.execution_time = execution_time
        self.tool_name = tool_name
        self.parameters = parameters or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir resultado a diccionario"""
        result = {
            'success': self.success,
            'timestamp': self.timestamp,
            'execution_time': self.execution_time,
            'tool_name': self.tool_name,
            'parameters': self.parameters
        }
        
        if self.success:
            result.update(self.data)
        else:
            result['error'] = self.error
            
        return result

class ParameterDefinition:
    """Definición de parámetro estandarizada"""
    
    def __init__(self, name: str, param_type: str, required: bool = True, 
                 description: str = "", default: Any = None, 
                 choices: List[Any] = None, min_value: Any = None, max_value: Any = None):
        self.name = name
        self.type = param_type
        self.required = required
        self.description = description
        self.default = default
        self.choices = choices
        self.min_value = min_value
        self.max_value = max_value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir definición a diccionario"""
        param_def = {
            'name': self.name,
            'type': self.type,
            'required': self.required,
            'description': self.description
        }
        
        if self.default is not None:
            param_def['default'] = self.default
        if self.choices:
            param_def['choices'] = self.choices
        if self.min_value is not None:
            param_def['min_value'] = self.min_value
        if self.max_value is not None:
            param_def['max_value'] = self.max_value
            
        return param_def

class BaseTool(ABC):
    """
    Clase base abstracta para todas las herramientas
    Proporciona funcionalidad común y elimina duplicación de código
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._parameters: List[ParameterDefinition] = []
        self._config: Dict[str, Any] = {}
        self._logger = logging.getLogger(f"tool.{name}")
    
    # ========================================================================
    # MÉTODOS ABSTRACTOS - DEBEN SER IMPLEMENTADOS POR CADA HERRAMIENTA
    # ========================================================================
    
    @abstractmethod
    def _define_parameters(self) -> List[ParameterDefinition]:
        """Definir parámetros específicos de la herramienta"""
        pass
    
    @abstractmethod
    def _execute_tool(self, parameters: Dict[str, Any], config: Dict[str, Any]) -> ToolExecutionResult:
        """Ejecutar la lógica específica de la herramienta"""
        pass
    
    # ========================================================================
    # MÉTODOS PÚBLICOS - INTERFAZ COMÚN
    # ========================================================================
    
    def get_name(self) -> str:
        """Obtener nombre de la herramienta"""
        return self.name
    
    def get_description(self) -> str:
        """Obtener descripción de la herramienta"""
        return self.description
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        """Obtener definiciones de parámetros"""
        if not self._parameters:
            self._parameters = self._define_parameters()
        
        return [param.to_dict() for param in self._parameters]
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validación común de parámetros
        Elimina duplicación de código de validación
        """
        try:
            # Validación básica de tipo
            if not isinstance(parameters, dict):
                return {'valid': False, 'error': 'Parameters must be a dictionary'}
            
            if not self._parameters:
                self._parameters = self._define_parameters()
            
            # Validar cada parámetro definido
            for param_def in self._parameters:
                param_name = param_def.name
                
                # Verificar parámetros requeridos
                if param_def.required and param_name not in parameters:
                    return {
                        'valid': False, 
                        'error': f'Required parameter "{param_name}" is missing'
                    }
                
                # Si el parámetro no está presente pero no es requerido, usar default
                if param_name not in parameters:
                    if param_def.default is not None:
                        parameters[param_name] = param_def.default
                    continue
                
                # Validar tipo de parámetro
                value = parameters[param_name]
                validation_result = self._validate_parameter_type(param_def, value)
                if not validation_result['valid']:
                    return validation_result
                
                # Validar restricciones adicionales
                constraint_result = self._validate_parameter_constraints(param_def, value)
                if not constraint_result['valid']:
                    return constraint_result
            
            return {'valid': True}
            
        except Exception as e:
            self._logger.error(f"Error validating parameters: {e}")
            return {'valid': False, 'error': f'Validation error: {str(e)}'}
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecutar herramienta con manejo de errores común
        Elimina duplicación de error handling
        """
        if config is None:
            config = {}
        
        start_time = time.time()
        
        try:
            # Validar parámetros
            validation_result = self.validate_parameters(parameters)
            if not validation_result['valid']:
                return ToolExecutionResult(
                    success=False,
                    error=f"Parameter validation failed: {validation_result['error']}",
                    execution_time=time.time() - start_time,
                    tool_name=self.name,
                    parameters=parameters
                ).to_dict()
            
            # Log inicio de ejecución
            self._logger.info(f"Executing tool '{self.name}' with parameters: {parameters}")
            
            # Ejecutar herramienta específica
            result = self._execute_tool(parameters, config)
            
            # Asegurar que el resultado tiene la información básica
            result.execution_time = time.time() - start_time
            result.tool_name = self.name
            result.parameters = parameters
            
            # Log resultado
            if result.success:
                self._logger.info(f"Tool '{self.name}' executed successfully in {result.execution_time:.2f}s")
            else:
                self._logger.error(f"Tool '{self.name}' failed: {result.error}")
            
            return result.to_dict()
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Unexpected error in tool '{self.name}': {str(e)}"
            self._logger.error(error_msg, exc_info=True)
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                execution_time=execution_time,
                tool_name=self.name,
                parameters=parameters
            ).to_dict()
    
    # ========================================================================
    # MÉTODOS PRIVADOS - UTILIDADES COMUNES
    # ========================================================================
    
    def _validate_parameter_type(self, param_def: ParameterDefinition, value: Any) -> Dict[str, Any]:
        """Validar tipo de parámetro"""
        expected_type = param_def.type.lower()
        
        type_validators = {
            'string': lambda v: isinstance(v, str),
            'integer': lambda v: isinstance(v, int),
            'float': lambda v: isinstance(v, (int, float)),
            'boolean': lambda v: isinstance(v, bool),
            'list': lambda v: isinstance(v, list),
            'dict': lambda v: isinstance(v, dict),
            'any': lambda v: True
        }
        
        validator = type_validators.get(expected_type)
        if not validator:
            return {'valid': False, 'error': f'Unknown parameter type: {expected_type}'}
        
        if not validator(value):
            return {
                'valid': False, 
                'error': f'Parameter "{param_def.name}" must be of type {expected_type}, got {type(value).__name__}'
            }
        
        return {'valid': True}
    
    def _validate_parameter_constraints(self, param_def: ParameterDefinition, value: Any) -> Dict[str, Any]:
        """Validar restricciones de parámetro"""
        # Validar choices
        if param_def.choices and value not in param_def.choices:
            return {
                'valid': False,
                'error': f'Parameter "{param_def.name}" must be one of {param_def.choices}, got {value}'
            }
        
        # Validar rango para números
        if param_def.type.lower() in ['integer', 'float']:
            if param_def.min_value is not None and value < param_def.min_value:
                return {
                    'valid': False,
                    'error': f'Parameter "{param_def.name}" must be >= {param_def.min_value}, got {value}'
                }
            
            if param_def.max_value is not None and value > param_def.max_value:
                return {
                    'valid': False,
                    'error': f'Parameter "{param_def.name}" must be <= {param_def.max_value}, got {value}'
                }
        
        # Validar longitud para strings
        if param_def.type.lower() == 'string':
            if param_def.min_value is not None and len(value) < param_def.min_value:
                return {
                    'valid': False,
                    'error': f'Parameter "{param_def.name}" must have at least {param_def.min_value} characters'
                }
            
            if param_def.max_value is not None and len(value) > param_def.max_value:
                return {
                    'valid': False,
                    'error': f'Parameter "{param_def.name}" must have at most {param_def.max_value} characters'
                }
            
            # Validar string no vacío si es requerido
            if param_def.required and not value.strip():
                return {
                    'valid': False,
                    'error': f'Parameter "{param_def.name}" cannot be empty'
                }
        
        return {'valid': True}
    
    def _create_success_result(self, data: Dict[str, Any] = None) -> ToolExecutionResult:
        """Crear resultado exitoso"""
        return ToolExecutionResult(success=True, data=data or {})
    
    def _create_error_result(self, error: str) -> ToolExecutionResult:
        """Crear resultado de error"""
        return ToolExecutionResult(success=False, error=error)

# ========================================================================
# DECORADOR PARA REGISTRO AUTOMÁTICO DE HERRAMIENTAS
# ========================================================================

def register_tool(tool_class):
    """Decorador para registro automático de herramientas"""
    if not hasattr(register_tool, 'registry'):
        register_tool.registry = {}
    
    if issubclass(tool_class, BaseTool):
        # Crear instancia para obtener el nombre
        temp_instance = tool_class()
        register_tool.registry[temp_instance.name] = tool_class
        
    return tool_class

def get_registered_tools() -> Dict[str, type]:
    """Obtener todas las herramientas registradas"""
    return getattr(register_tool, 'registry', {})