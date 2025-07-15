"""
Resolvedor de dependencias para el sistema de orquestación
Maneja la resolución de dependencias entre pasos de ejecución
"""

import logging
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import networkx as nx

from .planning_algorithms import TaskStep, ExecutionPlan

logger = logging.getLogger(__name__)

class DependencyType(Enum):
    """Tipos de dependencias"""
    SEQUENTIAL = "sequential"  # Debe ejecutarse después
    RESOURCE = "resource"      # Comparte recursos
    DATA = "data"             # Depende de datos
    CONDITIONAL = "conditional"  # Dependencia condicional
    PARALLEL = "parallel"     # Puede ejecutarse en paralelo

@dataclass
class DependencyRelation:
    """Relación de dependencia entre pasos"""
    source_step: str
    target_step: str
    dependency_type: DependencyType
    required: bool = True
    condition: Optional[str] = None
    resource_name: Optional[str] = None
    metadata: Dict[str, any] = None

class DependencyResolver:
    """Resolvedor de dependencias para pasos de ejecución"""
    
    def __init__(self):
        self.dependency_graph = nx.DiGraph()
        self.resolved_cache = {}
        
    def analyze_dependencies(self, steps: List[TaskStep]) -> Dict[str, List[DependencyRelation]]:
        """Analiza las dependencias entre pasos"""
        
        logger.info(f"Analizando dependencias para {len(steps)} pasos")
        
        # Construir grafo de dependencias
        self._build_dependency_graph(steps)
        
        # Detectar dependencias implícitas
        implicit_deps = self._detect_implicit_dependencies(steps)
        
        # Detectar dependencias de recursos
        resource_deps = self._detect_resource_dependencies(steps)
        
        # Detectar dependencias de datos
        data_deps = self._detect_data_dependencies(steps)
        
        # Consolidar todas las dependencias
        all_dependencies = {}
        
        for step in steps:
            step_deps = []
            
            # Dependencias explícitas
            for dep_id in step.dependencies:
                step_deps.append(DependencyRelation(
                    source_step=dep_id,
                    target_step=step.id,
                    dependency_type=DependencyType.SEQUENTIAL,
                    required=True
                ))
            
            # Agregar dependencias implícitas
            if step.id in implicit_deps:
                step_deps.extend(implicit_deps[step.id])
            
            # Agregar dependencias de recursos
            if step.id in resource_deps:
                step_deps.extend(resource_deps[step.id])
            
            # Agregar dependencias de datos
            if step.id in data_deps:
                step_deps.extend(data_deps[step.id])
            
            all_dependencies[step.id] = step_deps
        
        return all_dependencies
    
    def resolve_execution_order(self, steps: List[TaskStep]) -> List[List[str]]:
        """Resuelve el orden de ejecución considerando dependencias"""
        
        logger.info("Resolviendo orden de ejecución")
        
        # Analizar dependencias
        dependencies = self.analyze_dependencies(steps)
        
        # Construir grafo dirigido
        graph = nx.DiGraph()
        
        # Agregar nodos
        for step in steps:
            graph.add_node(step.id, step=step)
        
        # Agregar aristas (dependencias)
        for step_id, deps in dependencies.items():
            for dep in deps:
                if dep.required:
                    graph.add_edge(dep.source_step, dep.target_step, 
                                 dependency_type=dep.dependency_type)
        
        # Verificar ciclos
        if not nx.is_directed_acyclic_graph(graph):
            cycles = list(nx.simple_cycles(graph))
            logger.error(f"Ciclos detectados en dependencias: {cycles}")
            # Intentar resolver ciclos
            graph = self._resolve_cycles(graph, cycles)
        
        # Ordenamiento topológico por niveles
        try:
            execution_levels = []
            remaining_nodes = set(graph.nodes())
            
            while remaining_nodes:
                # Encontrar nodos sin dependencias pendientes
                current_level = []
                for node in remaining_nodes:
                    if not any(pred in remaining_nodes for pred in graph.predecessors(node)):
                        current_level.append(node)
                
                if not current_level:
                    # Deadlock - remover dependencia más débil
                    weakest_edge = self._find_weakest_dependency(graph, remaining_nodes)
                    if weakest_edge:
                        graph.remove_edge(*weakest_edge)
                        continue
                    else:
                        # Agregar nodos restantes como último nivel
                        current_level = list(remaining_nodes)
                
                execution_levels.append(current_level)
                remaining_nodes -= set(current_level)
            
            logger.info(f"Orden de ejecución resuelto: {len(execution_levels)} niveles")
            return execution_levels
            
        except Exception as e:
            logger.error(f"Error resolviendo orden de ejecución: {e}")
            # Fallback: orden secuencial
            return [[step.id] for step in steps]
    
    def optimize_parallel_execution(self, steps: List[TaskStep]) -> List[List[str]]:
        """Optimiza la ejecución paralela identificando pasos independientes"""
        
        logger.info("Optimizando ejecución paralela")
        
        # Obtener orden base
        execution_levels = self.resolve_execution_order(steps)
        
        # Optimizar cada nivel para paralelización
        optimized_levels = []
        
        for level in execution_levels:
            if len(level) <= 1:
                optimized_levels.append(level)
                continue
            
            # Agrupar pasos compatibles para ejecución paralela
            parallel_groups = self._group_parallel_compatible_steps(level, steps)
            
            # Agregar grupos como sub-niveles
            for group in parallel_groups:
                optimized_levels.append(group)
        
        return optimized_levels
    
    def validate_dependencies(self, steps: List[TaskStep]) -> Dict[str, List[str]]:
        """Valida las dependencias y reporta problemas"""
        
        logger.info("Validando dependencias")
        
        issues = {}
        step_ids = {step.id for step in steps}
        
        for step in steps:
            step_issues = []
            
            # Verificar dependencias existentes
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    step_issues.append(f"Dependencia no encontrada: {dep_id}")
            
            # Verificar dependencias circulares
            if self._has_circular_dependency(step, steps):
                step_issues.append("Dependencia circular detectada")
            
            # Verificar dependencias de recursos
            resource_conflicts = self._check_resource_conflicts(step, steps)
            if resource_conflicts:
                step_issues.extend(resource_conflicts)
            
            if step_issues:
                issues[step.id] = step_issues
        
        return issues
    
    def _build_dependency_graph(self, steps: List[TaskStep]):
        """Construye el grafo de dependencias"""
        
        self.dependency_graph.clear()
        
        # Agregar nodos
        for step in steps:
            self.dependency_graph.add_node(step.id, step=step)
        
        # Agregar aristas
        for step in steps:
            for dep_id in step.dependencies:
                if dep_id in [s.id for s in steps]:
                    self.dependency_graph.add_edge(dep_id, step.id)
    
    def _detect_implicit_dependencies(self, steps: List[TaskStep]) -> Dict[str, List[DependencyRelation]]:
        """Detecta dependencias implícitas entre pasos"""
        
        implicit_deps = {}
        
        for i, step in enumerate(steps):
            step_deps = []
            
            for j, other_step in enumerate(steps):
                if i != j and self._should_have_implicit_dependency(step, other_step):
                    step_deps.append(DependencyRelation(
                        source_step=other_step.id,
                        target_step=step.id,
                        dependency_type=DependencyType.SEQUENTIAL,
                        required=False
                    ))
            
            if step_deps:
                implicit_deps[step.id] = step_deps
        
        return implicit_deps
    
    def _detect_resource_dependencies(self, steps: List[TaskStep]) -> Dict[str, List[DependencyRelation]]:
        """Detecta dependencias de recursos compartidos"""
        
        resource_deps = {}
        
        # Mapear recursos por paso
        step_resources = {}
        for step in steps:
            resources = self._extract_step_resources(step)
            if resources:
                step_resources[step.id] = resources
        
        # Detectar conflictos de recursos
        for step in steps:
            if step.id not in step_resources:
                continue
            
            step_deps = []
            step_resources_set = set(step_resources[step.id])
            
            for other_step in steps:
                if (step.id != other_step.id and 
                    other_step.id in step_resources and
                    step_resources_set.intersection(set(step_resources[other_step.id]))):
                    
                    # Conflicto de recursos - crear dependencia
                    step_deps.append(DependencyRelation(
                        source_step=other_step.id,
                        target_step=step.id,
                        dependency_type=DependencyType.RESOURCE,
                        required=True,
                        resource_name=list(step_resources_set.intersection(
                            set(step_resources[other_step.id])
                        ))[0]
                    ))
            
            if step_deps:
                resource_deps[step.id] = step_deps
        
        return resource_deps
    
    def _detect_data_dependencies(self, steps: List[TaskStep]) -> Dict[str, List[DependencyRelation]]:
        """Detecta dependencias de datos entre pasos"""
        
        data_deps = {}
        
        # Mapear datos de entrada y salida
        step_inputs = {}
        step_outputs = {}
        
        for step in steps:
            inputs = self._extract_step_inputs(step)
            outputs = self._extract_step_outputs(step)
            
            if inputs:
                step_inputs[step.id] = inputs
            if outputs:
                step_outputs[step.id] = outputs
        
        # Detectar dependencias de datos
        for step in steps:
            if step.id not in step_inputs:
                continue
            
            step_deps = []
            
            for input_data in step_inputs[step.id]:
                # Buscar pasos que producen este dato
                for other_step in steps:
                    if (step.id != other_step.id and 
                        other_step.id in step_outputs and
                        input_data in step_outputs[other_step.id]):
                        
                        step_deps.append(DependencyRelation(
                            source_step=other_step.id,
                            target_step=step.id,
                            dependency_type=DependencyType.DATA,
                            required=True,
                            metadata={"data_item": input_data}
                        ))
            
            if step_deps:
                data_deps[step.id] = step_deps
        
        return data_deps
    
    def _should_have_implicit_dependency(self, step1: TaskStep, step2: TaskStep) -> bool:
        """Determina si debe existir una dependencia implícita"""
        
        # Dependencias basadas en herramientas
        tool_dependencies = {
            "file_manager": ["shell"],  # file_manager debe ir antes que shell
            "web_search": ["deep_research"],  # web_search puede ir antes que deep_research
        }
        
        if step1.tool in tool_dependencies:
            return step2.tool in tool_dependencies[step1.tool]
        
        # Dependencias basadas en operaciones
        if ("prepare" in step1.description.lower() and 
            "execute" in step2.description.lower()):
            return True
        
        if ("analyze" in step1.description.lower() and 
            "report" in step2.description.lower()):
            return True
        
        return False
    
    def _extract_step_resources(self, step: TaskStep) -> List[str]:
        """Extrae recursos utilizados por un paso"""
        
        resources = []
        
        # Recursos basados en herramientas
        tool_resources = {
            "file_manager": ["file_system", "storage"],
            "shell": ["cpu", "memory", "file_system"],
            "web_search": ["network", "memory"],
            "deep_research": ["network", "memory", "cpu"],
            "playwright": ["network", "memory", "display"]
        }
        
        if step.tool in tool_resources:
            resources.extend(tool_resources[step.tool])
        
        # Recursos específicos de parámetros
        if "file_path" in step.parameters:
            resources.append(f"file:{step.parameters['file_path']}")
        
        if "database" in step.parameters:
            resources.append("database")
        
        return resources
    
    def _extract_step_inputs(self, step: TaskStep) -> List[str]:
        """Extrae datos de entrada de un paso"""
        
        inputs = []
        
        # Inputs comunes
        if "query" in step.parameters:
            inputs.append("query_data")
        
        if "file_path" in step.parameters:
            inputs.append(f"file_data:{step.parameters['file_path']}")
        
        if "context" in step.parameters:
            inputs.append("context_data")
        
        # Inputs específicos por herramienta
        if step.tool == "deep_research":
            inputs.extend(["research_query", "search_results"])
        elif step.tool == "file_manager":
            inputs.extend(["file_operations", "directory_data"])
        
        return inputs
    
    def _extract_step_outputs(self, step: TaskStep) -> List[str]:
        """Extrae datos de salida de un paso"""
        
        outputs = []
        
        # Outputs basados en herramientas
        tool_outputs = {
            "web_search": ["search_results", "web_data"],
            "deep_research": ["research_report", "analysis_data"],
            "file_manager": ["file_data", "processed_files"],
            "shell": ["command_output", "system_data"],
            "comprehensive_research": ["comprehensive_report", "research_data"]
        }
        
        if step.tool in tool_outputs:
            outputs.extend(tool_outputs[step.tool])
        
        # Outputs específicos
        if "generate" in step.description.lower():
            outputs.append("generated_content")
        
        if "analyze" in step.description.lower():
            outputs.append("analysis_results")
        
        return outputs
    
    def _resolve_cycles(self, graph: nx.DiGraph, cycles: List[List[str]]) -> nx.DiGraph:
        """Resuelve ciclos en el grafo de dependencias"""
        
        logger.info(f"Resolviendo {len(cycles)} ciclos")
        
        for cycle in cycles:
            # Encontrar la arista más débil en el ciclo
            weakest_edge = None
            min_weight = float('inf')
            
            for i in range(len(cycle)):
                source = cycle[i]
                target = cycle[(i + 1) % len(cycle)]
                
                if graph.has_edge(source, target):
                    # Calcular peso de la arista
                    edge_data = graph.get_edge_data(source, target)
                    weight = self._calculate_edge_weight(source, target, edge_data)
                    
                    if weight < min_weight:
                        min_weight = weight
                        weakest_edge = (source, target)
            
            # Remover la arista más débil
            if weakest_edge:
                graph.remove_edge(*weakest_edge)
                logger.info(f"Removida arista débil: {weakest_edge[0]} -> {weakest_edge[1]}")
        
        return graph
    
    def _calculate_edge_weight(self, source: str, target: str, edge_data: Dict) -> float:
        """Calcula el peso de una arista de dependencia"""
        
        # Peso basado en tipo de dependencia
        type_weights = {
            DependencyType.SEQUENTIAL: 1.0,
            DependencyType.RESOURCE: 0.8,
            DependencyType.DATA: 0.9,
            DependencyType.CONDITIONAL: 0.5,
            DependencyType.PARALLEL: 0.3
        }
        
        dep_type = edge_data.get("dependency_type", DependencyType.SEQUENTIAL)
        return type_weights.get(dep_type, 1.0)
    
    def _find_weakest_dependency(self, graph: nx.DiGraph, nodes: Set[str]) -> Optional[Tuple[str, str]]:
        """Encuentra la dependencia más débil en un conjunto de nodos"""
        
        weakest_edge = None
        min_weight = float('inf')
        
        for node in nodes:
            for pred in graph.predecessors(node):
                if pred in nodes:
                    edge_data = graph.get_edge_data(pred, node)
                    weight = self._calculate_edge_weight(pred, node, edge_data)
                    
                    if weight < min_weight:
                        min_weight = weight
                        weakest_edge = (pred, node)
        
        return weakest_edge
    
    def _group_parallel_compatible_steps(self, step_ids: List[str], steps: List[TaskStep]) -> List[List[str]]:
        """Agrupa pasos compatibles para ejecución paralela"""
        
        # Crear diccionario de pasos
        step_dict = {step.id: step for step in steps}
        
        # Verificar qué pasos pueden ejecutarse en paralelo
        parallel_groups = []
        remaining_steps = step_ids.copy()
        
        while remaining_steps:
            # Encontrar grupo de pasos compatibles
            current_group = [remaining_steps[0]]
            remaining_steps.remove(remaining_steps[0])
            
            base_step = step_dict[current_group[0]]
            
            # Agregar pasos compatibles
            compatible_steps = []
            for step_id in remaining_steps:
                step = step_dict[step_id]
                if self._can_execute_in_parallel(base_step, step):
                    compatible_steps.append(step_id)
            
            # Agregar pasos compatibles al grupo
            current_group.extend(compatible_steps)
            for step_id in compatible_steps:
                remaining_steps.remove(step_id)
            
            parallel_groups.append(current_group)
        
        return parallel_groups
    
    def _can_execute_in_parallel(self, step1: TaskStep, step2: TaskStep) -> bool:
        """Determina si dos pasos pueden ejecutarse en paralelo"""
        
        # Verificar si ambos pasos pueden paralelizarse
        if not (step1.can_parallelize and step2.can_parallelize):
            return False
        
        # Verificar conflictos de recursos
        step1_resources = set(self._extract_step_resources(step1))
        step2_resources = set(self._extract_step_resources(step2))
        
        if step1_resources.intersection(step2_resources):
            return False
        
        # Verificar conflictos de herramientas
        if step1.tool == step2.tool:
            # Misma herramienta puede ser problemática
            return False
        
        # Verificar dependencias de datos
        step1_outputs = set(self._extract_step_outputs(step1))
        step2_inputs = set(self._extract_step_inputs(step2))
        
        if step1_outputs.intersection(step2_inputs):
            return False
        
        return True
    
    def _has_circular_dependency(self, step: TaskStep, steps: List[TaskStep]) -> bool:
        """Verifica si un paso tiene dependencias circulares"""
        
        visited = set()
        rec_stack = set()
        
        def dfs(step_id: str) -> bool:
            if step_id in rec_stack:
                return True
            if step_id in visited:
                return False
            
            visited.add(step_id)
            rec_stack.add(step_id)
            
            # Buscar el paso
            current_step = next((s for s in steps if s.id == step_id), None)
            if current_step:
                for dep_id in current_step.dependencies:
                    if dfs(dep_id):
                        return True
            
            rec_stack.remove(step_id)
            return False
        
        return dfs(step.id)
    
    def _check_resource_conflicts(self, step: TaskStep, steps: List[TaskStep]) -> List[str]:
        """Verifica conflictos de recursos"""
        
        conflicts = []
        step_resources = set(self._extract_step_resources(step))
        
        for other_step in steps:
            if step.id != other_step.id:
                other_resources = set(self._extract_step_resources(other_step))
                common_resources = step_resources.intersection(other_resources)
                
                if common_resources:
                    conflicts.append(f"Conflicto de recursos con {other_step.id}: {list(common_resources)}")
        
        return conflicts
    
    def get_dependency_metrics(self, steps: List[TaskStep]) -> Dict[str, any]:
        """Obtiene métricas de dependencias"""
        
        dependencies = self.analyze_dependencies(steps)
        
        # Calcular métricas
        total_dependencies = sum(len(deps) for deps in dependencies.values())
        
        dependency_types = {}
        for deps in dependencies.values():
            for dep in deps:
                dep_type = dep.dependency_type.value
                dependency_types[dep_type] = dependency_types.get(dep_type, 0) + 1
        
        # Calcular complejidad de dependencias
        avg_dependencies = total_dependencies / len(steps) if steps else 0
        
        return {
            "total_steps": len(steps),
            "total_dependencies": total_dependencies,
            "avg_dependencies_per_step": avg_dependencies,
            "dependency_types": dependency_types,
            "complexity_score": min(avg_dependencies / 3, 1.0),  # Normalizado
            "parallelizable_steps": len([s for s in steps if s.can_parallelize])
        }