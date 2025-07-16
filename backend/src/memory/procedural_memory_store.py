"""
Almacén de memoria procedimental
Gestiona habilidades, procedimientos y estrategias aprendidas
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class Procedure:
    """Representa un procedimiento aprendido"""
    id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    context_conditions: Dict[str, Any]  # Condiciones donde aplicar el procedimiento
    success_rate: float = 0.0
    usage_count: int = 0
    created_at: datetime = None
    last_used: datetime = None
    effectiveness_score: float = 0.5
    category: str = "general"  # Agregado para compatibilidad con rutas
    effectiveness: float = None  # Alias para effectiveness_score
    metadata: Dict[str, Any] = None  # Metadatos adicionales
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
        
        # Auto-generar ID si no se proporciona
        if not self.id:
            self.id = f"proc_{datetime.now().timestamp()}"
            
        # Si se proporciona effectiveness, usarlo para effectiveness_score
        if self.effectiveness is not None:
            self.effectiveness_score = self.effectiveness
        
        # Agregar categoría a context_conditions si no existe
        if 'category' not in self.context_conditions:
            self.context_conditions['category'] = self.category

@dataclass
class ToolStrategy:
    """Representa una estrategia de uso de herramientas"""
    id: str
    tool_name: str
    strategy_name: str
    parameters: Dict[str, Any]
    context_pattern: str
    success_rate: float = 0.0
    avg_execution_time: float = 0.0
    usage_count: int = 0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class ProceduralMemoryStore:
    """Almacén de memoria procedimental para habilidades y procedimientos"""
    
    def __init__(self, max_procedures: int = 1000, max_strategies: int = 5000):
        """
        Inicializa el almacén de memoria procedimental
        
        Args:
            max_procedures: Número máximo de procedimientos
            max_strategies: Número máximo de estrategias de herramientas
        """
        self.max_procedures = max_procedures
        self.max_strategies = max_strategies
        self.procedures: Dict[str, Procedure] = {}
        self.tool_strategies: Dict[str, ToolStrategy] = {}
        self.procedure_index: Dict[str, List[str]] = defaultdict(list)  # contexto -> procedimientos
        self.strategy_index: Dict[str, List[str]] = defaultdict(list)  # herramienta -> estrategias
        
    def store_procedure(self, procedure: Procedure):
        """
        Almacena un procedimiento aprendido
        
        Args:
            procedure: Procedimiento a almacenar
        """
        try:
            # Aplicar límite de capacidad
            if len(self.procedures) >= self.max_procedures:
                self._remove_least_effective_procedure()
            
            # Almacenar procedimiento
            self.procedures[procedure.id] = procedure
            
            # Actualizar índices por contexto
            for context_key, context_value in procedure.context_conditions.items():
                index_key = f"{context_key}:{context_value}"
                self.procedure_index[index_key].append(procedure.id)
            
            logger.debug(f"Procedimiento {procedure.id} almacenado en memoria procedimental")
            
        except Exception as e:
            logger.error(f"Error almacenando procedimiento {procedure.id}: {e}")
    
    def store_tool_strategy(self, strategy: ToolStrategy):
        """
        Almacena una estrategia de uso de herramientas
        
        Args:
            strategy: Estrategia a almacenar
        """
        try:
            # Aplicar límite de capacidad
            if len(self.tool_strategies) >= self.max_strategies:
                self._remove_least_effective_strategy()
            
            # Almacenar estrategia
            self.tool_strategies[strategy.id] = strategy
            
            # Actualizar índices por herramienta
            self.strategy_index[strategy.tool_name].append(strategy.id)
            
            logger.debug(f"Estrategia {strategy.id} almacenada en memoria procedimental")
            
        except Exception as e:
            logger.error(f"Error almacenando estrategia {strategy.id}: {e}")
    
    def find_applicable_procedures(self, context: Dict[str, Any], limit: int = 5) -> List[Procedure]:
        """
        Encuentra procedimientos aplicables para un contexto
        
        Args:
            context: Contexto actual
            limit: Número máximo de procedimientos
            
        Returns:
            Lista de procedimientos aplicables
        """
        try:
            applicable_procedures = []
            
            # Buscar procedimientos por contexto
            for context_key, context_value in context.items():
                index_key = f"{context_key}:{context_value}"
                if index_key in self.procedure_index:
                    for proc_id in self.procedure_index[index_key]:
                        if proc_id in self.procedures:
                            procedure = self.procedures[proc_id]
                            if self._matches_context(procedure.context_conditions, context):
                                applicable_procedures.append(procedure)
            
            # Eliminar duplicados y ordenar por efectividad
            unique_procedures = list({p.id: p for p in applicable_procedures}.values())
            unique_procedures.sort(key=lambda x: (x.effectiveness_score, x.success_rate), reverse=True)
            
            return unique_procedures[:limit]
            
        except Exception as e:
            logger.error(f"Error encontrando procedimientos aplicables: {e}")
            return []
    
    def get_best_tool_strategy(self, tool_name: str, context_pattern: str = None) -> Optional[ToolStrategy]:
        """
        Obtiene la mejor estrategia para una herramienta
        
        Args:
            tool_name: Nombre de la herramienta
            context_pattern: Patrón de contexto específico
            
        Returns:
            Mejor estrategia o None si no existe
        """
        try:
            if tool_name not in self.strategy_index:
                return None
            
            strategies = []
            for strategy_id in self.strategy_index[tool_name]:
                if strategy_id in self.tool_strategies:
                    strategy = self.tool_strategies[strategy_id]
                    
                    # Filtrar por patrón de contexto si se especifica
                    if context_pattern is None or context_pattern in strategy.context_pattern:
                        strategies.append(strategy)
            
            if not strategies:
                return None
            
            # Ordenar por tasa de éxito y uso reciente
            strategies.sort(key=lambda x: (x.success_rate, x.usage_count), reverse=True)
            
            return strategies[0]
            
        except Exception as e:
            logger.error(f"Error obteniendo estrategia para {tool_name}: {e}")
            return None
    
    def update_procedure_effectiveness(self, procedure_id: str, success: bool, execution_time: float):
        """
        Actualiza la efectividad de un procedimiento
        
        Args:
            procedure_id: ID del procedimiento
            success: Si la ejecución fue exitosa
            execution_time: Tiempo de ejecución
        """
        try:
            if procedure_id in self.procedures:
                procedure = self.procedures[procedure_id]
                
                # Actualizar estadísticas
                procedure.usage_count += 1
                procedure.last_used = datetime.now()
                
                # Calcular nueva tasa de éxito
                if success:
                    procedure.success_rate = (
                        (procedure.success_rate * (procedure.usage_count - 1) + 1.0) / 
                        procedure.usage_count
                    )
                else:
                    procedure.success_rate = (
                        (procedure.success_rate * (procedure.usage_count - 1) + 0.0) / 
                        procedure.usage_count
                    )
                
                # Actualizar score de efectividad (combina éxito y velocidad)
                time_factor = max(0.1, 1.0 - (execution_time / 300.0))  # 5 minutos como referencia
                procedure.effectiveness_score = (procedure.success_rate * 0.7) + (time_factor * 0.3)
                
                logger.debug(f"Procedimiento {procedure_id} actualizado: éxito={success}, efectividad={procedure.effectiveness_score:.2f}")
                
        except Exception as e:
            logger.error(f"Error actualizando efectividad del procedimiento {procedure_id}: {e}")
    
    def update_strategy_effectiveness(self, strategy_id: str, success: bool, execution_time: float):
        """
        Actualiza la efectividad de una estrategia
        
        Args:
            strategy_id: ID de la estrategia
            success: Si la ejecución fue exitosa
            execution_time: Tiempo de ejecución
        """
        try:
            if strategy_id in self.tool_strategies:
                strategy = self.tool_strategies[strategy_id]
                
                # Actualizar estadísticas
                strategy.usage_count += 1
                
                # Calcular nueva tasa de éxito
                if success:
                    strategy.success_rate = (
                        (strategy.success_rate * (strategy.usage_count - 1) + 1.0) / 
                        strategy.usage_count
                    )
                else:
                    strategy.success_rate = (
                        (strategy.success_rate * (strategy.usage_count - 1) + 0.0) / 
                        strategy.usage_count
                    )
                
                # Actualizar tiempo promedio de ejecución
                strategy.avg_execution_time = (
                    (strategy.avg_execution_time * (strategy.usage_count - 1) + execution_time) / 
                    strategy.usage_count
                )
                
                logger.debug(f"Estrategia {strategy_id} actualizada: éxito={success}, tiempo_promedio={strategy.avg_execution_time:.2f}s")
                
        except Exception as e:
            logger.error(f"Error actualizando efectividad de la estrategia {strategy_id}: {e}")
    
    def learn_from_execution(self, task_context: Dict[str, Any], execution_steps: List[Dict[str, Any]], 
                           success: bool, execution_time: float):
        """
        Aprende de una ejecución para crear o mejorar procedimientos
        
        Args:
            task_context: Contexto de la tarea
            execution_steps: Pasos ejecutados
            success: Si la ejecución fue exitosa
            execution_time: Tiempo total de ejecución
        """
        try:
            if success and execution_steps:
                # Crear nuevo procedimiento si la ejecución fue exitosa
                procedure_id = f"proc_{datetime.now().timestamp()}_{hash(str(execution_steps))}"
                
                new_procedure = Procedure(
                    id=procedure_id,
                    name=f"Procedimiento para {task_context.get('task_type', 'tarea')}",
                    description=f"Procedimiento aprendido de ejecución exitosa",
                    steps=execution_steps,
                    context_conditions=task_context,
                    success_rate=1.0,
                    usage_count=1,
                    effectiveness_score=0.8,
                    last_used=datetime.now()
                )
                
                self.store_procedure(new_procedure)
                
                # Aprender estrategias de herramientas utilizadas
                for step in execution_steps:
                    if step.get('tool_name') and step.get('parameters'):
                        self._learn_tool_strategy(step, task_context, success, execution_time)
                        
            logger.debug(f"Aprendizaje completado: éxito={success}, pasos={len(execution_steps)}")
            
        except Exception as e:
            logger.error(f"Error aprendiendo de ejecución: {e}")
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """
        Obtiene insights sobre el aprendizaje del agente
        
        Returns:
            Diccionario con insights de aprendizaje
        """
        try:
            # Procedimientos más efectivos
            best_procedures = sorted(
                self.procedures.values(),
                key=lambda x: x.effectiveness_score,
                reverse=True
            )[:5]
            
            # Herramientas más utilizadas
            tool_usage = defaultdict(int)
            for strategy in self.tool_strategies.values():
                tool_usage[strategy.tool_name] += strategy.usage_count
            
            # Patrones de contexto más exitosos
            context_success = defaultdict(list)
            for procedure in self.procedures.values():
                for context_key, context_value in procedure.context_conditions.items():
                    context_success[f"{context_key}:{context_value}"].append(procedure.success_rate)
            
            context_patterns = {}
            for pattern, success_rates in context_success.items():
                context_patterns[pattern] = sum(success_rates) / len(success_rates)
            
            return {
                'best_procedures': [
                    {
                        'name': proc.name,
                        'effectiveness': proc.effectiveness_score,
                        'success_rate': proc.success_rate,
                        'usage_count': proc.usage_count
                    }
                    for proc in best_procedures
                ],
                'tool_usage': dict(sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)),
                'successful_context_patterns': dict(sorted(context_patterns.items(), key=lambda x: x[1], reverse=True)[:10]),
                'total_procedures': len(self.procedures),
                'total_strategies': len(self.tool_strategies)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo insights de aprendizaje: {e}")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la memoria procedimental
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            if not self.procedures and not self.tool_strategies:
                return {
                    'total_procedures': 0,
                    'total_strategies': 0,
                    'average_procedure_effectiveness': 0,
                    'average_strategy_success': 0
                }
            
            avg_proc_effectiveness = (
                sum(p.effectiveness_score for p in self.procedures.values()) / len(self.procedures)
                if self.procedures else 0
            )
            
            avg_strategy_success = (
                sum(s.success_rate for s in self.tool_strategies.values()) / len(self.tool_strategies)
                if self.tool_strategies else 0
            )
            
            return {
                'total_procedures': len(self.procedures),
                'total_strategies': len(self.tool_strategies),
                'average_procedure_effectiveness': avg_proc_effectiveness,
                'average_strategy_success': avg_strategy_success,
                'most_used_procedures': [
                    {'name': p.name, 'usage_count': p.usage_count}
                    for p in sorted(self.procedures.values(), key=lambda x: x.usage_count, reverse=True)[:5]
                ],
                'best_performing_tools': [
                    {'tool': s.tool_name, 'success_rate': s.success_rate}
                    for s in sorted(self.tool_strategies.values(), key=lambda x: x.success_rate, reverse=True)[:5]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def _matches_context(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Verifica si las condiciones coinciden con el contexto
        
        Args:
            conditions: Condiciones del procedimiento
            context: Contexto actual
            
        Returns:
            True si coinciden
        """
        try:
            for key, value in conditions.items():
                if key not in context or context[key] != value:
                    return False
            return True
            
        except Exception as e:
            logger.error(f"Error verificando contexto: {e}")
            return False
    
    def _learn_tool_strategy(self, step: Dict[str, Any], context: Dict[str, Any], 
                           success: bool, execution_time: float):
        """
        Aprende una estrategia de herramienta de un paso de ejecución
        
        Args:
            step: Paso de ejecución
            context: Contexto de la tarea
            success: Si fue exitoso
            execution_time: Tiempo de ejecución
        """
        try:
            tool_name = step.get('tool_name')
            parameters = step.get('parameters', {})
            
            if not tool_name:
                return
            
            # Crear ID único para la estrategia
            strategy_id = f"strat_{tool_name}_{hash(str(parameters))}"
            
            # Crear patrón de contexto
            context_pattern = f"{context.get('task_type', 'general')}_{context.get('complexity', 'medium')}"
            
            if strategy_id in self.tool_strategies:
                # Actualizar estrategia existente
                self.update_strategy_effectiveness(strategy_id, success, execution_time)
            else:
                # Crear nueva estrategia
                new_strategy = ToolStrategy(
                    id=strategy_id,
                    tool_name=tool_name,
                    strategy_name=f"Estrategia para {tool_name}",
                    parameters=parameters,
                    context_pattern=context_pattern,
                    success_rate=1.0 if success else 0.0,
                    avg_execution_time=execution_time,
                    usage_count=1
                )
                
                self.store_tool_strategy(new_strategy)
                
        except Exception as e:
            logger.error(f"Error aprendiendo estrategia de herramienta: {e}")
    
    def _remove_least_effective_procedure(self):
        """Elimina el procedimiento menos efectivo"""
        if not self.procedures:
            return
            
        least_effective = min(self.procedures.items(), key=lambda x: x[1].effectiveness_score)
        procedure_id = least_effective[0]
        
        del self.procedures[procedure_id]
        
        # Limpiar índices
        for index_list in self.procedure_index.values():
            if procedure_id in index_list:
                index_list.remove(procedure_id)
    
    def _remove_least_effective_strategy(self):
        """Elimina la estrategia menos efectiva"""
        if not self.tool_strategies:
            return
            
        least_effective = min(self.tool_strategies.items(), key=lambda x: x[1].success_rate)
        strategy_id = least_effective[0]
        strategy = least_effective[1]
        
        del self.tool_strategies[strategy_id]
        
        # Limpiar índices
        if strategy.tool_name in self.strategy_index:
            if strategy_id in self.strategy_index[strategy.tool_name]:
                self.strategy_index[strategy.tool_name].remove(strategy_id)