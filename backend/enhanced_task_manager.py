"""
Sistema de Administración de Tareas Mejorado para el agente Mitosis
Incluye registro de herramientas, re-planificación dinámica y gestión de dependencias
"""

import logging
import time
import json
import uuid
import asyncio
from typing import List, Dict, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading
from datetime import datetime
import networkx as nx

from task_manager import TaskStatus, PhaseStatus, TaskPhase, Task, TaskManager
from memory_manager import MemoryManager

class ToolType(Enum):
    """Tipos de herramientas disponibles"""
    WEB_SEARCH = "web_search"
    CODE_EXECUTION = "code_execution"
    FILE_OPERATION = "file_operation"
    API_CALL = "api_call"
    DATA_ANALYSIS = "data_analysis"
    IMAGE_GENERATION = "image_generation"
    TEXT_PROCESSING = "text_processing"
    CUSTOM = "custom"

@dataclass
class ToolDefinition:
    """Definición de una herramienta"""
    id: str
    name: str
    description: str
    tool_type: ToolType
    parameters: Dict[str, Any]
    capabilities: List[str]
    cost_estimate: float = 0.0
    execution_time_estimate: float = 0.0
    reliability_score: float = 1.0
    callback: Optional[Callable] = None
    
    def __post_init__(self):
        if not self.parameters:
            self.parameters = {}
        if not self.capabilities:
            self.capabilities = []

@dataclass
class ToolExecution:
    """Resultado de la ejecución de una herramienta"""
    tool_id: str
    task_id: str
    phase_id: int
    started_at: float
    completed_at: Optional[float] = None
    success: bool = False
    result: Any = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    
    def __post_init__(self):
        if self.completed_at and self.started_at:
            self.execution_time = self.completed_at - self.started_at

@dataclass
class EnhancedTaskPhase(TaskPhase):
    """Fase de tarea mejorada con dependencias y herramientas"""
    dependencies: List[int] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    parallel_execution: bool = False
    retry_count: int = 0
    max_retries: int = 3
    tool_executions: List[ToolExecution] = field(default_factory=list)

@dataclass
class EnhancedTask(Task):
    """Tarea mejorada con capacidades avanzadas"""
    phases: List[EnhancedTaskPhase] = field(default_factory=list)
    dependency_graph: Optional[Dict[str, Any]] = None
    auto_replan: bool = True
    replan_count: int = 0
    max_replans: int = 2
    estimated_duration: float = 0.0
    actual_duration: float = 0.0

class EnhancedTaskManager(TaskManager):
    """Gestor de tareas mejorado con herramientas y re-planificación"""
    
    def __init__(self, memory_manager: MemoryManager):
        super().__init__(memory_manager)
        
        # Registro de herramientas
        self.tool_registry: Dict[str, ToolDefinition] = {}
        self.tool_executions: List[ToolExecution] = []
        
        # Configuración mejorada
        self.enable_parallel_execution = True
        self.enable_dynamic_replanning = True
        self.tool_selection_strategy = "best_fit"  # "best_fit", "fastest", "cheapest"
        
        # Estadísticas de herramientas
        self.tool_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "tool_usage_count": {}
        }
        
        # Inicializar herramientas básicas
        self._register_default_tools()
        
        self.logger.info("Enhanced Task Manager inicializado con capacidades avanzadas")
    
    def _register_default_tools(self):
        """Registra herramientas por defecto"""
        default_tools = [
            ToolDefinition(
                id="web_search",
                name="Búsqueda Web",
                description="Realiza búsquedas en internet",
                tool_type=ToolType.WEB_SEARCH,
                parameters={"query": "string", "max_results": "int"},
                capabilities=["search", "information_retrieval"],
                cost_estimate=0.01,
                execution_time_estimate=2.0,
                reliability_score=0.9
            ),
            ToolDefinition(
                id="code_executor",
                name="Ejecutor de Código",
                description="Ejecuta código Python de forma segura",
                tool_type=ToolType.CODE_EXECUTION,
                parameters={"code": "string", "timeout": "int"},
                capabilities=["programming", "computation", "data_processing"],
                cost_estimate=0.05,
                execution_time_estimate=5.0,
                reliability_score=0.95
            ),
            ToolDefinition(
                id="file_manager",
                name="Gestor de Archivos",
                description="Operaciones de lectura y escritura de archivos",
                tool_type=ToolType.FILE_OPERATION,
                parameters={"operation": "string", "path": "string", "content": "string"},
                capabilities=["file_io", "data_storage"],
                cost_estimate=0.001,
                execution_time_estimate=0.5,
                reliability_score=0.99
            ),
            ToolDefinition(
                id="data_analyzer",
                name="Analizador de Datos",
                description="Análisis estadístico y visualización de datos",
                tool_type=ToolType.DATA_ANALYSIS,
                parameters={"data": "object", "analysis_type": "string"},
                capabilities=["statistics", "visualization", "data_science"],
                cost_estimate=0.02,
                execution_time_estimate=3.0,
                reliability_score=0.85
            )
        ]
        
        for tool in default_tools:
            self.register_tool(tool)
    
    def register_tool(self, tool: ToolDefinition) -> bool:
        """Registra una nueva herramienta"""
        try:
            self.tool_registry[tool.id] = tool
            self.tool_stats["tool_usage_count"][tool.id] = 0
            self.logger.info(f"Herramienta registrada: {tool.name} ({tool.id})")
            return True
        except Exception as e:
            self.logger.error(f"Error al registrar herramienta {tool.id}: {e}")
            return False
    
    def unregister_tool(self, tool_id: str) -> bool:
        """Desregistra una herramienta"""
        if tool_id in self.tool_registry:
            del self.tool_registry[tool_id]
            self.logger.info(f"Herramienta desregistrada: {tool_id}")
            return True
        return False
    
    def get_available_tools(self, capabilities: Optional[List[str]] = None) -> List[ToolDefinition]:
        """Obtiene herramientas disponibles, opcionalmente filtradas por capacidades"""
        if not capabilities:
            return list(self.tool_registry.values())
        
        matching_tools = []
        for tool in self.tool_registry.values():
            if any(cap in tool.capabilities for cap in capabilities):
                matching_tools.append(tool)
        
        return matching_tools
    
    def select_best_tool(self, required_capabilities: List[str], 
                        strategy: str = None) -> Optional[ToolDefinition]:
        """Selecciona la mejor herramienta para las capacidades requeridas"""
        if strategy is None:
            strategy = self.tool_selection_strategy
        
        available_tools = self.get_available_tools(required_capabilities)
        
        if not available_tools:
            return None
        
        if strategy == "best_fit":
            # Seleccionar por mayor coincidencia de capacidades y confiabilidad
            def score_tool(tool):
                capability_match = len(set(required_capabilities) & set(tool.capabilities))
                return capability_match * tool.reliability_score
            
            return max(available_tools, key=score_tool)
        
        elif strategy == "fastest":
            return min(available_tools, key=lambda t: t.execution_time_estimate)
        
        elif strategy == "cheapest":
            return min(available_tools, key=lambda t: t.cost_estimate)
        
        else:
            return available_tools[0]
    
    def create_enhanced_task(self, title: str, description: str, goal: str,
                           phases: List[Dict[str, Any]], priority: int = 1,
                           context: Optional[Dict[str, Any]] = None,
                           auto_replan: bool = True) -> str:
        """Crea una tarea mejorada con capacidades avanzadas"""
        task_id = str(uuid.uuid4())
        
        # Convertir fases a EnhancedTaskPhase
        enhanced_phases = []
        for phase_data in phases:
            phase = EnhancedTaskPhase(
                id=phase_data.get('id'),
                title=phase_data.get('title'),
                description=phase_data.get('description', ''),
                required_capabilities=phase_data.get('required_capabilities', []),
                dependencies=phase_data.get('dependencies', []),
                required_tools=phase_data.get('required_tools', []),
                parallel_execution=phase_data.get('parallel_execution', False),
                max_retries=phase_data.get('max_retries', 3)
            )
            enhanced_phases.append(phase)
        
        # Crear grafo de dependencias
        dependency_graph = self._build_dependency_graph(enhanced_phases)
        
        # Estimar duración
        estimated_duration = self._estimate_task_duration(enhanced_phases)
        
        enhanced_task = EnhancedTask(
            id=task_id,
            title=title,
            description=description,
            goal=goal,
            phases=enhanced_phases,
            priority=priority,
            context=context or {},
            auto_replan=auto_replan,
            dependency_graph=dependency_graph,
            estimated_duration=estimated_duration
        )
        
        self.active_tasks[task_id] = enhanced_task
        self.task_queue.append(task_id)
        
        # Guardar en memoria
        self._save_enhanced_task_to_memory(enhanced_task)
        
        self.logger.info(f"Tarea mejorada creada: {task_id} - {title}")
        return task_id
    
    def _build_dependency_graph(self, phases: List[EnhancedTaskPhase]) -> Dict[str, Any]:
        """Construye un grafo de dependencias entre fases"""
        graph = nx.DiGraph()
        
        # Añadir nodos (fases)
        for phase in phases:
            graph.add_node(phase.id, phase=phase)
        
        # Añadir aristas (dependencias)
        for phase in phases:
            for dependency in phase.dependencies:
                if dependency in [p.id for p in phases]:
                    graph.add_edge(dependency, phase.id)
        
        # Verificar ciclos
        if not nx.is_directed_acyclic_graph(graph):
            self.logger.warning("Se detectaron dependencias circulares en las fases")
        
        return {
            "nodes": list(graph.nodes()),
            "edges": list(graph.edges()),
            "topological_order": list(nx.topological_sort(graph)) if nx.is_directed_acyclic_graph(graph) else []
        }
    
    def _estimate_task_duration(self, phases: List[EnhancedTaskPhase]) -> float:
        """Estima la duración total de una tarea"""
        total_duration = 0.0
        
        for phase in phases:
            phase_duration = 60.0  # Duración base por fase (1 minuto)
            
            # Añadir tiempo estimado de herramientas
            for tool_id in phase.required_tools:
                if tool_id in self.tool_registry:
                    tool = self.tool_registry[tool_id]
                    phase_duration += tool.execution_time_estimate
            
            total_duration += phase_duration
        
        return total_duration
    
    def execute_phase_with_tools(self, task_id: str, phase_id: int) -> bool:
        """Ejecuta una fase utilizando las herramientas requeridas"""
        task = self.active_tasks.get(task_id)
        if not task:
            return False
        
        phase = next((p for p in task.phases if p.id == phase_id), None)
        if not phase:
            return False
        
        try:
            phase.status = PhaseStatus.ACTIVE
            phase.started_at = time.time()
            
            # Ejecutar herramientas requeridas
            for tool_id in phase.required_tools:
                if tool_id in self.tool_registry:
                    tool = self.tool_registry[tool_id]
                    execution_result = self._execute_tool(tool, task_id, phase_id)
                    phase.tool_executions.append(execution_result)
                    
                    if not execution_result.success:
                        self.logger.error(f"Herramienta {tool_id} falló en fase {phase_id}")
                        if phase.retry_count < phase.max_retries:
                            phase.retry_count += 1
                            return self.execute_phase_with_tools(task_id, phase_id)
                        else:
                            phase.status = PhaseStatus.FAILED
                            phase.error_message = execution_result.error_message
                            return False
            
            # Simular ejecución de la fase
            time.sleep(0.1)  # Simular trabajo
            
            phase.status = PhaseStatus.COMPLETED
            phase.completed_at = time.time()
            
            self._save_enhanced_task_to_memory(task)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al ejecutar fase {phase_id}: {e}")
            phase.status = PhaseStatus.FAILED
            phase.error_message = str(e)
            return False
    
    def _execute_tool(self, tool: ToolDefinition, task_id: str, phase_id: int) -> ToolExecution:
        """Ejecuta una herramienta específica"""
        execution = ToolExecution(
            tool_id=tool.id,
            task_id=task_id,
            phase_id=phase_id,
            started_at=time.time()
        )
        
        try:
            self.tool_stats["total_executions"] += 1
            self.tool_stats["tool_usage_count"][tool.id] += 1
            
            # Simular ejecución de herramienta
            if tool.callback:
                result = tool.callback()
            else:
                # Simulación básica
                time.sleep(tool.execution_time_estimate / 10)  # Simulación rápida
                result = f"Resultado simulado de {tool.name}"
            
            execution.success = True
            execution.result = result
            execution.completed_at = time.time()
            
            self.tool_stats["successful_executions"] += 1
            
            self.logger.info(f"Herramienta {tool.id} ejecutada exitosamente")
            
        except Exception as e:
            execution.success = False
            execution.error_message = str(e)
            execution.completed_at = time.time()
            
            self.tool_stats["failed_executions"] += 1
            
            self.logger.error(f"Error al ejecutar herramienta {tool.id}: {e}")
        
        self.tool_executions.append(execution)
        self._update_tool_stats()
        
        return execution
    
    def _update_tool_stats(self):
        """Actualiza las estadísticas de herramientas"""
        if self.tool_stats["total_executions"] > 0:
            total_time = sum(exec.execution_time for exec in self.tool_executions)
            self.tool_stats["average_execution_time"] = total_time / len(self.tool_executions)
    
    def replan_task(self, task_id: str, reason: str = "") -> bool:
        """Re-planifica una tarea dinámicamente"""
        if not self.enable_dynamic_replanning:
            return False
        
        task = self.active_tasks.get(task_id)
        if not task or not isinstance(task, EnhancedTask):
            return False
        
        if task.replan_count >= task.max_replans:
            self.logger.warning(f"Tarea {task_id} ha alcanzado el límite de re-planificaciones")
            return False
        
        try:
            self.logger.info(f"Re-planificando tarea {task_id}. Razón: {reason}")
            
            # Analizar fases fallidas
            failed_phases = [p for p in task.phases if p.status == PhaseStatus.FAILED]
            
            # Generar nuevo plan (simplificado)
            for failed_phase in failed_phases:
                # Resetear fase fallida
                failed_phase.status = PhaseStatus.PENDING
                failed_phase.retry_count = 0
                failed_phase.error_message = None
                
                # Seleccionar herramientas alternativas
                if failed_phase.required_capabilities:
                    alternative_tools = self.get_available_tools(failed_phase.required_capabilities)
                    if alternative_tools:
                        # Cambiar a herramienta más confiable
                        best_tool = max(alternative_tools, key=lambda t: t.reliability_score)
                        failed_phase.required_tools = [best_tool.id]
            
            task.replan_count += 1
            
            # Reconstruir grafo de dependencias
            task.dependency_graph = self._build_dependency_graph(task.phases)
            
            self._save_enhanced_task_to_memory(task)
            
            self.logger.info(f"Tarea {task_id} re-planificada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al re-planificar tarea {task_id}: {e}")
            return False
    
    def get_next_executable_phases(self, task_id: str) -> List[EnhancedTaskPhase]:
        """Obtiene las siguientes fases ejecutables considerando dependencias"""
        task = self.active_tasks.get(task_id)
        if not task or not isinstance(task, EnhancedTask):
            return []
        
        executable_phases = []
        
        for phase in task.phases:
            if phase.status == PhaseStatus.PENDING:
                # Verificar si todas las dependencias están completadas
                dependencies_met = all(
                    any(p.id == dep_id and p.status == PhaseStatus.COMPLETED 
                        for p in task.phases)
                    for dep_id in phase.dependencies
                )
                
                if dependencies_met or not phase.dependencies:
                    executable_phases.append(phase)
        
        return executable_phases
    
    def execute_parallel_phases(self, task_id: str) -> bool:
        """Ejecuta fases en paralelo cuando es posible"""
        if not self.enable_parallel_execution:
            return False
        
        executable_phases = self.get_next_executable_phases(task_id)
        parallel_phases = [p for p in executable_phases if p.parallel_execution]
        
        if not parallel_phases:
            return False
        
        try:
            # Ejecutar fases en paralelo usando threading
            threads = []
            for phase in parallel_phases:
                thread = threading.Thread(
                    target=self.execute_phase_with_tools,
                    args=(task_id, phase.id)
                )
                threads.append(thread)
                thread.start()
            
            # Esperar a que todas las fases terminen
            for thread in threads:
                thread.join()
            
            self.logger.info(f"Ejecutadas {len(parallel_phases)} fases en paralelo para tarea {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error en ejecución paralela: {e}")
            return False
    
    def _save_enhanced_task_to_memory(self, task: EnhancedTask):
        """Guarda una tarea mejorada en la memoria"""
        # Convertir fases mejoradas a formato serializable
        phases_data = []
        for phase in task.phases:
            phase_data = asdict(phase)
            # Convertir tool_executions a formato serializable
            phase_data['tool_executions'] = [asdict(exec) for exec in phase.tool_executions]
            phases_data.append(phase_data)
        
        task_memory = {
            "task_id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "created_at": task.created_at,
            "updated_at": time.time(),
            "phases": phases_data,
            "results": task.results,
            "dependency_graph": task.dependency_graph,
            "estimated_duration": task.estimated_duration,
            "replan_count": task.replan_count
        }
        
        # Guardar en memoria usando el método base
        from memory_manager import TaskMemory
        base_task_memory = TaskMemory(
            task_id=task.id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            created_at=task.created_at,
            updated_at=time.time(),
            phases=phases_data,
            results=task.results,
            tools_used=[exec.tool_id for phase in task.phases for exec in phase.tool_executions]
        )
        
        self.memory_manager.save_task_memory(base_task_memory)
    
    def get_enhanced_manager_status(self) -> Dict[str, Any]:
        """Obtiene el estado mejorado del gestor de tareas"""
        base_status = self.get_manager_status()
        
        enhanced_status = {
            **base_status,
            "tools": {
                "registered_tools": len(self.tool_registry),
                "tool_types": list(set(tool.tool_type.value for tool in self.tool_registry.values())),
                "total_executions": self.tool_stats["total_executions"],
                "success_rate": (self.tool_stats["successful_executions"] / 
                               max(1, self.tool_stats["total_executions"])) * 100,
                "average_execution_time": self.tool_stats["average_execution_time"]
            },
            "capabilities": {
                "parallel_execution": self.enable_parallel_execution,
                "dynamic_replanning": self.enable_dynamic_replanning,
                "tool_selection_strategy": self.tool_selection_strategy
            }
        }
        
        return enhanced_status

# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Crear gestor de memoria y tareas mejorado
    from memory_manager import MemoryManager
    memory = MemoryManager()
    enhanced_task_manager = EnhancedTaskManager(memory)
    
    print("🚀 Probando Enhanced Task Manager...")
    
    # Crear una tarea mejorada con dependencias
    phases = [
        {
            "id": 1, 
            "title": "Investigación", 
            "required_capabilities": ["search"],
            "required_tools": ["web_search"],
            "dependencies": []
        },
        {
            "id": 2, 
            "title": "Análisis", 
            "required_capabilities": ["data_science"],
            "required_tools": ["data_analyzer"],
            "dependencies": [1]
        },
        {
            "id": 3, 
            "title": "Implementación", 
            "required_capabilities": ["programming"],
            "required_tools": ["code_executor"],
            "dependencies": [2],
            "parallel_execution": True
        },
        {
            "id": 4, 
            "title": "Documentación", 
            "required_capabilities": ["file_io"],
            "required_tools": ["file_manager"],
            "dependencies": [2],
            "parallel_execution": True
        }
    ]
    
    task_id = enhanced_task_manager.create_enhanced_task(
        title="Proyecto de Análisis de Datos",
        description="Investigar, analizar e implementar una solución de datos",
        goal="Crear una solución completa de análisis de datos",
        phases=phases,
        auto_replan=True
    )
    
    print(f"✅ Tarea mejorada creada: {task_id}")
    
    # Mostrar herramientas disponibles
    tools = enhanced_task_manager.get_available_tools()
    print(f"🛠️ Herramientas disponibles: {len(tools)}")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Obtener fases ejecutables
    executable_phases = enhanced_task_manager.get_next_executable_phases(task_id)
    print(f"▶️ Fases ejecutables: {[p.title for p in executable_phases]}")
    
    # Mostrar estado del gestor
    status = enhanced_task_manager.get_enhanced_manager_status()
    print(f"📊 Estado del gestor mejorado:")
    print(f"  Herramientas registradas: {status['tools']['registered_tools']}")
    print(f"  Ejecución paralela: {status['capabilities']['parallel_execution']}")
    print(f"  Re-planificación dinámica: {status['capabilities']['dynamic_replanning']}")
    
    print("✅ Pruebas completadas")

