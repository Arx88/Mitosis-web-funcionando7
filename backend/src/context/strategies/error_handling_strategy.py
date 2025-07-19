"""
Estrategia de Contexto para Manejo de Errores
"""

from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorHandlingContextStrategy:
    """Estrategia para contexto de manejo de errores"""
    
    async def build_context(self, query: str, memory_manager, task_manager, max_tokens: int) -> Dict[str, Any]:
        context = {
            'type': 'error_handling',
            'query': query,
            'error_patterns': [],
            'successful_recoveries': [],
            'available_fixes': [],
            'escalation_options': [],
            'error_type': None,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Analizar tipo de error en la consulta
            context['error_type'] = self._analyze_error_type(query)
            
            # Obtener patrones de error similares
            if memory_manager:
                context['error_patterns'] = await self._get_error_patterns(memory_manager, query)
                context['successful_recoveries'] = await self._get_successful_recoveries(memory_manager, query)
            
            # Generar posibles soluciones
            context['available_fixes'] = self._generate_available_fixes(query, context['error_type'])
            
            # Definir opciones de escalación
            context['escalation_options'] = self._get_escalation_options(context['error_type'])
                
        except Exception as e:
            logger.error(f"Error building error handling context: {e}")
            
        return context
    
    def _analyze_error_type(self, query: str) -> str:
        """Analiza el tipo de error basado en la consulta"""
        query_lower = query.lower()
        
        error_patterns = {
            'connection_error': ['conexión', 'conectar', 'red', 'internet', 'timeout'],
            'execution_error': ['error', 'fallo', 'falló', 'no funciona', 'problema'],
            'validation_error': ['validación', 'formato', 'incorrecto', 'inválido'],
            'timeout_error': ['timeout', 'tiempo', 'demora', 'lento', 'tardando'],
            'resource_error': ['memoria', 'espacio', 'recursos', 'límite'],
            'permission_error': ['permiso', 'acceso', 'autorización', 'prohibido'],
            'data_error': ['datos', 'información', 'contenido', 'vacío', 'nulo']
        }
        
        for error_type, keywords in error_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                return error_type
        
        return 'general_error'
    
    async def _get_error_patterns(self, memory_manager, query: str) -> List[Dict[str, Any]]:
        """Obtiene patrones de error similares"""
        patterns = []
        try:
            if hasattr(memory_manager, 'get_error_patterns'):
                similar_patterns = await memory_manager.get_error_patterns(query)
                patterns = similar_patterns
            else:
                # Patrones básicos por defecto
                patterns = [
                    {
                        'pattern': 'tool_execution_failure',
                        'frequency': 'medium',
                        'typical_cause': 'Parámetros incorrectos o servicio no disponible',
                        'success_recovery_rate': 0.8
                    },
                    {
                        'pattern': 'context_building_failure',
                        'frequency': 'low',
                        'typical_cause': 'Error en acceso a memoria o datos corruptos',
                        'success_recovery_rate': 0.9
                    }
                ]
        except Exception as e:
            logger.error(f"Error getting error patterns: {e}")
        return patterns
    
    async def _get_successful_recoveries(self, memory_manager, query: str) -> List[Dict[str, Any]]:
        """Obtiene recuperaciones exitosas anteriores"""
        recoveries = []
        try:
            if hasattr(memory_manager, 'get_successful_error_recoveries'):
                recoveries = await memory_manager.get_successful_error_recoveries(query)
            else:
                # Recuperaciones básicas por defecto
                recoveries = [
                    {
                        'scenario': 'Tool execution timeout',
                        'solution': 'Retry with reduced parameters and increased timeout',
                        'success_rate': 0.85,
                        'execution_time': 'avg 30s'
                    },
                    {
                        'scenario': 'Memory access error',
                        'solution': 'Fallback to basic context without memory integration',
                        'success_rate': 0.95,
                        'execution_time': 'avg 5s'
                    }
                ]
        except Exception as e:
            logger.error(f"Error getting successful recoveries: {e}")
        return recoveries
    
    def _generate_available_fixes(self, query: str, error_type: str) -> List[Dict[str, Any]]:
        """Genera posibles soluciones basadas en el tipo de error"""
        fixes = []
        
        fix_strategies = {
            'connection_error': [
                {'fix': 'Retry connection', 'priority': 'high', 'estimated_time': '10s'},
                {'fix': 'Use alternative endpoint', 'priority': 'medium', 'estimated_time': '30s'},
                {'fix': 'Switch to offline mode', 'priority': 'low', 'estimated_time': '5s'}
            ],
            'execution_error': [
                {'fix': 'Retry with different parameters', 'priority': 'high', 'estimated_time': '20s'},
                {'fix': 'Use alternative tool', 'priority': 'medium', 'estimated_time': '45s'},
                {'fix': 'Manual fallback', 'priority': 'low', 'estimated_time': '60s'}
            ],
            'validation_error': [
                {'fix': 'Validate and correct input', 'priority': 'high', 'estimated_time': '15s'},
                {'fix': 'Use default parameters', 'priority': 'medium', 'estimated_time': '5s'}
            ],
            'timeout_error': [
                {'fix': 'Increase timeout and retry', 'priority': 'high', 'estimated_time': '60s'},
                {'fix': 'Break into smaller tasks', 'priority': 'medium', 'estimated_time': '120s'}
            ],
            'general_error': [
                {'fix': 'Restart process', 'priority': 'high', 'estimated_time': '30s'},
                {'fix': 'Use basic fallback', 'priority': 'medium', 'estimated_time': '10s'}
            ]
        }
        
        fixes = fix_strategies.get(error_type, fix_strategies['general_error'])
        return fixes
    
    def _get_escalation_options(self, error_type: str) -> List[Dict[str, Any]]:
        """Define opciones de escalación"""
        escalation_levels = [
            {
                'level': 1,
                'action': 'Automatic retry with modified parameters',
                'trigger': 'First attempt fails',
                'automated': True
            },
            {
                'level': 2,
                'action': 'Switch to alternative approach',
                'trigger': 'Multiple retries fail',
                'automated': True
            },
            {
                'level': 3,
                'action': 'Fallback to basic functionality',
                'trigger': 'All automated options exhausted',
                'automated': True
            },
            {
                'level': 4,
                'action': 'Request user intervention',
                'trigger': 'Critical system error',
                'automated': False
            }
        ]
        
        return escalation_levels