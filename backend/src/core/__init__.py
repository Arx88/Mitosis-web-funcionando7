"""
Módulo Core Unificado de Mitosis
Contiene las clases principales del agente consolidado
"""

from .agent_unified import (
    MitosisUnifiedAgent,
    AgentConfig,
    AgentMode,
    TaskStatus,
    TaskStep,
    AgentTask,
    create_unified_agent,
    create_agent_from_env,
    # Aliases para compatibilidad
    MitosisAgent,
    MitosisRealAgent,
    MitosisEnhancedAgent
)

__all__ = [
    'MitosisUnifiedAgent',
    'AgentConfig', 
    'AgentMode',
    'TaskStatus',
    'TaskStep',
    'AgentTask',
    'create_unified_agent',
    'create_agent_from_env',
    'MitosisAgent',
    'MitosisRealAgent', 
    'MitosisEnhancedAgent'
]