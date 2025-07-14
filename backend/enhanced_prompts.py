"""
Sistema de Gestión de Prompts Mejorado para el agente Mitosis
Incluye auto-optimización y plantillas adaptativas
"""

import logging
import json
import time
import hashlib
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re

from enhanced_prompts import PromptType

@dataclass
class PromptPerformance:
    """Métricas de rendimiento de un prompt"""
    prompt_id: str
    usage_count: int = 0
    success_count: int = 0
    average_response_time: float = 0.0
    average_quality_score: float = 0.0
    last_used: float = 0.0
    optimization_count: int = 0

class PromptOptimizationStrategy(Enum):
    """Estrategias de optimización de prompts"""
    CLARITY = "clarity"
    SPECIFICITY = "specificity"
    CONTEXT = "context"
    STRUCTURE = "structure"
    EXAMPLES = "examples"

class EnhancedPromptManager:
    """Gestor de prompts mejorado con capacidades de auto-optimización"""
    
    def __init__(self, memory_manager, task_manager):
        self.memory_manager = memory_manager
        self.task_manager = task_manager
        self.logger = logging.getLogger(__name__)
        
        # Configuración
        self.max_context_tokens = 4000
        self.include_memory_context = True
        self.auto_optimization_enabled = True
        self.optimization_threshold = 0.6  # Umbral de éxito para optimización
        
        # Almacenamiento de prompts y rendimiento
        self.prompt_templates: Dict[str, str] = {}
        self.prompt_performance: Dict[str, PromptPerformance] = {}
        self.optimization_history: List[Dict[str, Any]] = []
        
        # Patrones de optimización
        self.optimization_patterns = {
            PromptOptimizationStrategy.CLARITY: [
                "Sé más específico y claro en las instrucciones",
                "Usa lenguaje directo y evita ambigüedades",
                "Define términos técnicos cuando sea necesario"
            ],
            PromptOptimizationStrategy.SPECIFICITY: [
                "Proporciona ejemplos concretos",
                "Especifica el formato de salida deseado",
                "Incluye criterios de éxito específicos"
            ],
            PromptOptimizationStrategy.CONTEXT: [
                "Añade más contexto relevante",
                "Incluye información de fondo necesaria",
                "Relaciona con experiencias previas"
            ],
            PromptOptimizationStrategy.STRUCTURE: [
                "Organiza las instrucciones en pasos numerados",
                "Usa viñetas para listar requisitos",
                "Separa claramente las secciones"
            ],
            PromptOptimizationStrategy.EXAMPLES: [
                "Incluye ejemplos de entrada y salida",
                "Muestra casos de uso específicos",
                "Proporciona contraejemplos cuando sea útil"
            ]
        }
        
        # Inicializar plantillas base
        self._initialize_base_templates()
        
        self.logger.info("Enhanced Prompt Manager inicializado")
    
    def _initialize_base_templates(self):
        """Inicializa plantillas base de prompts"""
        base_templates = {
            "system_prompt": """Eres un agente inteligente llamado Mitosis, diseñado para ayudar a los usuarios de manera eficiente y precisa.

Características principales:
- Analítico y reflexivo
- Capaz de aprender de la experiencia
- Orientado a resultados
- Transparente en tu proceso de pensamiento

Contexto actual: {context}
Modo cognitivo: {cognitive_mode}

Responde de manera útil, precisa y adaptada al contexto del usuario.""",

            "task_planning": """Como agente especializado en planificación, necesito crear un plan detallado para la siguiente tarea:

**Objetivo:** {goal}
**Descripción:** {description}
**Contexto disponible:** {context}
**Recursos:** {resources}

Crea un plan estructurado que incluya:
1. **Análisis del objetivo** - Descompón el objetivo en componentes clave
2. **Fases de ejecución** - Lista las fases en orden lógico
3. **Dependencias** - Identifica qué fases dependen de otras
4. **Herramientas necesarias** - Especifica qué herramientas se requieren
5. **Criterios de éxito** - Define cómo medir el éxito de cada fase
6. **Estimación de tiempo** - Proporciona estimaciones realistas

Formato de respuesta en JSON:
```json
{
  "goal": "objetivo reformulado",
  "phases": [
    {
      "id": 1,
      "title": "nombre de la fase",
      "description": "descripción detallada",
      "required_capabilities": ["capacidad1", "capacidad2"],
      "dependencies": [],
      "estimated_duration": "tiempo estimado",
      "success_criteria": "criterios específicos"
    }
  ]
}
```""",

            "phase_execution": """Ejecutando la fase actual de la tarea:

**Tarea:** {task_title}
**Fase actual:** {phase_title}
**Descripción:** {phase_description}
**Capacidades requeridas:** {required_capabilities}
**Contexto de la tarea:** {task_context}

**Progreso previo:**
{previous_results}

**Instrucciones específicas:**
1. Analiza los requisitos de esta fase
2. Utiliza las capacidades disponibles de manera eficiente
3. Documenta tu proceso de pensamiento
4. Proporciona resultados claros y verificables
5. Identifica cualquier problema o limitación

Ejecuta esta fase paso a paso y proporciona un resultado detallado.""",

            "reflection_prompt": """Reflexiona sobre la siguiente acción y su resultado:

**Acción realizada:** {action_taken}
**Resultado obtenido:** {result}
**Resultado esperado:** {expected_outcome}
**Contexto de la tarea:** {task_context}

**Análisis requerido:**
1. **Evaluación de éxito:** ¿Se logró el objetivo? (Sí/No y por qué)
2. **Análisis de proceso:** ¿Qué funcionó bien y qué no?
3. **Patrones identificados:** ¿Qué patrones puedes observar?
4. **Lecciones aprendidas:** ¿Qué insights específicos obtuviste?
5. **Mejoras futuras:** ¿Cómo abordarías esto diferente la próxima vez?

Proporciona una reflexión honesta y constructiva que ayude al aprendizaje futuro.""",

            "error_handling": """Se ha producido un error que requiere análisis y estrategia de recuperación:

**Error:** {error_message}
**Acción que falló:** {failed_action}
**Contexto:** {context}
**Información adicional:** {additional_info}

**Análisis requerido:**
1. **Diagnóstico:** ¿Cuál es la causa raíz del error?
2. **Impacto:** ¿Qué tan crítico es este error?
3. **Opciones de recuperación:** ¿Qué alternativas existen?
4. **Estrategia recomendada:** ¿Cuál es el mejor curso de acción?
5. **Prevención futura:** ¿Cómo evitar este error en el futuro?

Proporciona una estrategia de recuperación clara y accionable."""
        }
        
        for template_id, template in base_templates.items():
            self.prompt_templates[template_id] = template
            self.prompt_performance[template_id] = PromptPerformance(prompt_id=template_id)
    
    def generate_system_prompt(self, context: str = "", cognitive_mode: str = "adaptive") -> str:
        """Genera un prompt del sistema optimizado"""
        template = self.prompt_templates.get("system_prompt", "")
        
        # Aplicar optimizaciones si están disponibles
        optimized_template = self._apply_optimizations("system_prompt", template)
        
        return optimized_template.format(
            context=context,
            cognitive_mode=cognitive_mode
        )
    
    def generate_task_planning_prompt(self, goal: str, description: str = "", 
                                    context: str = "", resources: str = "") -> str:
        """Genera un prompt optimizado para planificación de tareas"""
        template = self.prompt_templates.get("task_planning", "")
        optimized_template = self._apply_optimizations("task_planning", template)
        
        return optimized_template.format(
            goal=goal,
            description=description,
            context=context,
            resources=resources
        )
    
    def generate_phase_execution_prompt(self, task, phase) -> str:
        """Genera un prompt optimizado para ejecución de fases"""
        template = self.prompt_templates.get("phase_execution", "")
        optimized_template = self._apply_optimizations("phase_execution", template)
        
        # Obtener resultados previos
        previous_results = ""
        for prev_phase in task.phases:
            if prev_phase.id < phase.id and prev_phase.results:
                previous_results += f"Fase {prev_phase.id}: {prev_phase.results}\n"
        
        return optimized_template.format(
            task_title=task.title,
            phase_title=phase.title,
            phase_description=phase.description,
            required_capabilities=", ".join(phase.required_capabilities),
            task_context=json.dumps(task.context, indent=2),
            previous_results=previous_results or "No hay resultados previos"
        )
    
    def generate_reflection_prompt(self, action_taken: str, result: str, 
                                 expected_outcome: str, task_context: str = "") -> str:
        """Genera un prompt optimizado para reflexión"""
        template = self.prompt_templates.get("reflection_prompt", "")
        optimized_template = self._apply_optimizations("reflection_prompt", template)
        
        return optimized_template.format(
            action_taken=action_taken,
            result=result,
            expected_outcome=expected_outcome,
            task_context=task_context
        )
    
    def generate_error_handling_prompt(self, error_message: str, failed_action: str,
                                     context: str = "", additional_info: str = "") -> str:
        """Genera un prompt optimizado para manejo de errores"""
        template = self.prompt_templates.get("error_handling", "")
        optimized_template = self._apply_optimizations("error_handling", template)
        
        return optimized_template.format(
            error_message=error_message,
            failed_action=failed_action,
            context=context,
            additional_info=additional_info
        )
    
    def _apply_optimizations(self, prompt_id: str, template: str) -> str:
        """Aplica optimizaciones a una plantilla de prompt"""
        if not self.auto_optimization_enabled:
            return template
        
        performance = self.prompt_performance.get(prompt_id)
        if not performance:
            return template
        
        # Si el rendimiento es bajo, aplicar optimizaciones
        if (performance.usage_count > 5 and 
            performance.success_count / performance.usage_count < self.optimization_threshold):
            
            return self._optimize_prompt_template(prompt_id, template)
        
        return template
    
    def _optimize_prompt_template(self, prompt_id: str, template: str) -> str:
        """Optimiza una plantilla de prompt"""
        performance = self.prompt_performance[prompt_id]
        
        # Determinar estrategia de optimización basada en el rendimiento
        if performance.average_quality_score < 0.5:
            strategy = PromptOptimizationStrategy.CLARITY
        elif performance.average_response_time > 10.0:
            strategy = PromptOptimizationStrategy.SPECIFICITY
        else:
            strategy = PromptOptimizationStrategy.STRUCTURE
        
        # Aplicar optimización
        optimized_template = self._apply_optimization_strategy(template, strategy)
        
        # Registrar optimización
        optimization_record = {
            "prompt_id": prompt_id,
            "strategy": strategy.value,
            "timestamp": time.time(),
            "original_performance": asdict(performance),
            "optimization_count": performance.optimization_count + 1
        }
        
        self.optimization_history.append(optimization_record)
        performance.optimization_count += 1
        
        self.logger.info(f"Prompt {prompt_id} optimizado usando estrategia: {strategy.value}")
        
        return optimized_template
    
    def _apply_optimization_strategy(self, template: str, 
                                   strategy: PromptOptimizationStrategy) -> str:
        """Aplica una estrategia específica de optimización"""
        patterns = self.optimization_patterns[strategy]
        
        if strategy == PromptOptimizationStrategy.CLARITY:
            # Hacer el prompt más claro
            template = re.sub(r'(?i)\b(puede|podría|tal vez)\b', 'debe', template)
            template = template.replace('si es posible', 'específicamente')
            
        elif strategy == PromptOptimizationStrategy.SPECIFICITY:
            # Añadir más especificidad
            if "Proporciona" in template and "específico" not in template:
                template = template.replace("Proporciona", "Proporciona específicamente")
            
        elif strategy == PromptOptimizationStrategy.STRUCTURE:
            # Mejorar estructura
            if "1." not in template and "Instrucciones" in template:
                # Añadir numeración si no existe
                lines = template.split('\n')
                for i, line in enumerate(lines):
                    if line.strip().startswith('-'):
                        lines[i] = line.replace('-', f"{i}.")
                template = '\n'.join(lines)
        
        elif strategy == PromptOptimizationStrategy.CONTEXT:
            # Añadir más contexto
            if "{context}" not in template:
                template = f"Contexto adicional: {{context}}\n\n{template}"
        
        elif strategy == PromptOptimizationStrategy.EXAMPLES:
            # Añadir ejemplos
            if "Ejemplo:" not in template and "ejemplo" not in template.lower():
                template += "\n\nEjemplo de respuesta esperada: [Proporciona un ejemplo relevante]"
        
        return template
    
    def record_prompt_performance(self, prompt_id: str, success: bool, 
                                response_time: float = 0.0, quality_score: float = 0.5):
        """Registra el rendimiento de un prompt"""
        if prompt_id not in self.prompt_performance:
            self.prompt_performance[prompt_id] = PromptPerformance(prompt_id=prompt_id)
        
        performance = self.prompt_performance[prompt_id]
        performance.usage_count += 1
        performance.last_used = time.time()
        
        if success:
            performance.success_count += 1
        
        # Actualizar promedio de tiempo de respuesta
        if response_time > 0:
            if performance.usage_count == 1:
                performance.average_response_time = response_time
            else:
                alpha = 0.1  # Factor de aprendizaje
                performance.average_response_time = (
                    (1 - alpha) * performance.average_response_time + alpha * response_time
                )
        
        # Actualizar puntuación de calidad
        if performance.usage_count == 1:
            performance.average_quality_score = quality_score
        else:
            alpha = 0.1
            performance.average_quality_score = (
                (1 - alpha) * performance.average_quality_score + alpha * quality_score
            )
    
    def get_prompt_analytics(self) -> Dict[str, Any]:
        """Obtiene analíticas de los prompts"""
        analytics = {
            "total_prompts": len(self.prompt_templates),
            "total_optimizations": len(self.optimization_history),
            "prompt_performance": {}
        }
        
        for prompt_id, performance in self.prompt_performance.items():
            if performance.usage_count > 0:
                success_rate = performance.success_count / performance.usage_count
                analytics["prompt_performance"][prompt_id] = {
                    "usage_count": performance.usage_count,
                    "success_rate": success_rate,
                    "average_response_time": performance.average_response_time,
                    "average_quality_score": performance.average_quality_score,
                    "optimization_count": performance.optimization_count
                }
        
        return analytics
    
    def export_optimized_prompts(self) -> Dict[str, str]:
        """Exporta las plantillas de prompts optimizadas"""
        return self.prompt_templates.copy()
    
    def import_prompt_templates(self, templates: Dict[str, str]):
        """Importa plantillas de prompts"""
        for template_id, template in templates.items():
            self.prompt_templates[template_id] = template
            if template_id not in self.prompt_performance:
                self.prompt_performance[template_id] = PromptPerformance(prompt_id=template_id)
        
        self.logger.info(f"Importadas {len(templates)} plantillas de prompts")

# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Crear gestor de prompts mejorado (mock de dependencias)
    class MockMemoryManager:
        pass
    
    class MockTaskManager:
        pass
    
    enhanced_prompt_manager = EnhancedPromptManager(
        MockMemoryManager(), MockTaskManager()
    )
    
    print("📝 Probando Enhanced Prompt Manager...")
    
    # Generar prompt del sistema
    system_prompt = enhanced_prompt_manager.generate_system_prompt(
        context="Usuario trabajando en análisis de datos",
        cognitive_mode="analytical"
    )
    print(f"🤖 System prompt generado: {len(system_prompt)} caracteres")
    
    # Generar prompt de planificación
    planning_prompt = enhanced_prompt_manager.generate_task_planning_prompt(
        goal="Crear un dashboard de ventas",
        description="Dashboard interactivo para visualizar métricas de ventas",
        context="Empresa de e-commerce con datos en SQL",
        resources="Python, Plotly, base de datos SQL"
    )
    print(f"📋 Planning prompt generado: {len(planning_prompt)} caracteres")
    
    # Simular uso y rendimiento
    enhanced_prompt_manager.record_prompt_performance(
        "task_planning", success=True, response_time=5.2, quality_score=0.8
    )
    enhanced_prompt_manager.record_prompt_performance(
        "task_planning", success=False, response_time=8.1, quality_score=0.4
    )
    
    # Obtener analíticas
    analytics = enhanced_prompt_manager.get_prompt_analytics()
    print(f"📊 Analíticas de prompts:")
    print(f"  Total de prompts: {analytics['total_prompts']}")
    print(f"  Optimizaciones realizadas: {analytics['total_optimizations']}")
    
    for prompt_id, perf in analytics["prompt_performance"].items():
        print(f"  {prompt_id}: {perf['success_rate']:.2f} éxito, {perf['usage_count']} usos")
    
    print("✅ Pruebas completadas")

