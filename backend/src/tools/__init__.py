"""
Tools package - Fase 4 Refactorizada
Arquitectura simplificada con BaseTool y ToolRegistry
"""

# Importar arquitectura base
from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult, register_tool
from .tool_registry import (
    ToolRegistry, 
    get_tool_registry, 
    initialize_tool_registry,
    get_tool,
    execute_tool,
    get_available_tools,
    get_all_tools_info
)
from .tool_manager import (
    ToolManager,
    get_tool_manager,
    initialize_tools
)

# Auto-importar herramientas refactorizadas (para que se registren)
try:
    from .shell_tool_refactored import ShellTool
except ImportError:
    pass

try:
    from .web_search_tool_refactored import WebSearchTool
except ImportError:
    pass

# Importar herramientas originales para compatibilidad
try:
    from .shell_tool import ShellTool as OriginalShellTool
except ImportError:
    pass

try:
    from .file_manager_tool import FileManagerTool
except ImportError:
    pass

try:
    from .web_search_tool import WebSearchTool as OriginalWebSearchTool
except ImportError:
    pass

# Herramientas adicionales
try:
    from .tavily_search_tool import TavilySearchTool
except ImportError:
    pass

try:
    from .comprehensive_research_tool import ComprehensiveResearchTool
except ImportError:
    pass

try:
    from .firecrawl_tool import FirecrawlTool
except ImportError:
    pass

try:
    from .playwright_tool import PlaywrightTool
except ImportError:
    pass

# Exportar interfaz principal
__all__ = [
    # Arquitectura base
    'BaseTool',
    'ParameterDefinition', 
    'ToolExecutionResult',
    'register_tool',
    
    # Registry
    'ToolRegistry',
    'get_tool_registry',
    'initialize_tool_registry',
    'get_tool',
    'execute_tool',
    'get_available_tools',
    'get_all_tools_info',
    
    # Manager
    'ToolManager',
    'get_tool_manager',
    'initialize_tools'
]