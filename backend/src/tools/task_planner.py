"""
Task Planner - Planificador inteligente de tareas
Analiza tareas y genera planes de ejecución automáticos
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

@dataclass
class TaskStep:
    id: str
    title: str
    description: str
    tool: str
    parameters: Dict[str, Any]
    dependencies: List[str]
    estimated_duration: int  # segundos
    complexity: str  # 'low', 'medium', 'high'
    required_skills: List[str]

@dataclass
class ExecutionPlan:
    task_id: str
    title: str
    steps: List[TaskStep]
    total_estimated_duration: int
    complexity_score: float
    required_tools: List[str]
    success_probability: float
    risk_factors: List[str]
    prerequisites: List[str]

class TaskPlanner:
    def __init__(self):
        self.name = "task_planner"
        self.description = "Planificador inteligente de tareas y generador de planes de ejecución"
        
        # Patrones de reconocimiento de tareas
        self.task_patterns = {
            'web_development': [
                r'crear.*web|website|página.*web|sitio.*web',
                r'html|css|javascript|react|vue|angular',
                r'frontend|backend|fullstack',
                r'aplicación.*web|app.*web'
            ],
            'data_analysis': [
                r'analizar.*datos|análisis.*datos|data.*analysis',
                r'csv|excel|json|base.*datos|database',
                r'gráfico|chart|visualización|estadística',
                r'pandas|numpy|machine.*learning|ml|ai'
            ],
            'file_processing': [
                r'procesar.*archivo|process.*file',
                r'descomprimir|unzip|extraer|extract',
                r'convertir|convert|transform',
                r'organizar.*archivo|organize.*file'
            ],
            'system_administration': [
                r'instalar|install|configurar|configure',
                r'servidor|server|sistema|system',
                r'administración|administration|admin',
                r'monitoreo|monitoring|security|seguridad'
            ],
            'research': [
                r'investigar|research|buscar.*información',
                r'recopilar.*datos|gather.*data',
                r'estudio|study|análisis.*mercado',
                r'comparar|compare|evaluar|evaluate'
            ],
            'automation': [
                r'automatizar|automate|script',
                r'bot|crawler|scraping',
                r'workflow|proceso.*automático',
                r'integración|integration'
            ]
        }
        
        # Templates de planes por tipo de tarea
        self.plan_templates = {
            'web_development': self._get_web_development_template,
            'data_analysis': self._get_data_analysis_template,
            'file_processing': self._get_file_processing_template,
            'system_administration': self._get_system_admin_template,
            'research': self._get_research_template,
            'automation': self._get_automation_template,
            'general': self._get_general_template
        }
    
    def analyze_task(self, task_title: str, task_description: str = "") -> Dict[str, Any]:
        """Analizar una tarea y determinar su tipo y complejidad"""
        
        combined_text = f"{task_title} {task_description}".lower()
        
        # Detectar tipo de tarea
        task_type = self._detect_task_type(combined_text)
        
        # Calcular complejidad
        complexity = self._calculate_complexity(combined_text)
        
        # Identificar herramientas necesarias
        required_tools = self._identify_required_tools(combined_text, task_type)
        
        # Estimar duración
        estimated_duration = self._estimate_duration(complexity, required_tools, task_type)
        
        # Identificar factores de riesgo
        risk_factors = self._identify_risk_factors(combined_text, task_type)
        
        # Calcular probabilidad de éxito
        success_probability = self._calculate_success_probability(complexity, risk_factors, required_tools)
        
        return {
            'task_type': task_type,
            'complexity': complexity,
            'estimated_duration': estimated_duration,
            'required_tools': required_tools,
            'risk_factors': risk_factors,
            'success_probability': success_probability,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def generate_execution_plan(self, task_id: str, task_title: str, 
                              task_description: str = "") -> ExecutionPlan:
        """Generar plan de ejecución detallado para una tarea"""
        
        # Analizar tarea
        analysis = self.analyze_task(task_title, task_description)
        
        # Obtener template de plan
        task_type = analysis['task_type']
        plan_generator = self.plan_templates.get(task_type, self.plan_templates['general'])
        
        # Generar pasos del plan
        steps = plan_generator(task_title, task_description, analysis)
        
        # Calcular métricas totales
        total_duration = sum(step.estimated_duration for step in steps)
        complexity_score = self._calculate_complexity_score(analysis['complexity'], len(steps))
        
        # Crear plan de ejecución
        plan = ExecutionPlan(
            task_id=task_id,
            title=task_title,
            steps=steps,
            total_estimated_duration=total_duration,
            complexity_score=complexity_score,
            required_tools=analysis['required_tools'],
            success_probability=analysis['success_probability'],
            risk_factors=analysis['risk_factors'],
            prerequisites=self._identify_prerequisites(task_type, analysis)
        )
        
        return plan
    
    def _detect_task_type(self, text: str) -> str:
        """Detectar el tipo de tarea basado en patrones"""
        
        scores = {}
        
        for task_type, patterns in self.task_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 1
            scores[task_type] = score
        
        # Retornar el tipo con mayor score
        if scores:
            best_type = max(scores.items(), key=lambda x: x[1])
            if best_type[1] > 0:
                return best_type[0]
        
        return 'general'
    
    def _calculate_complexity(self, text: str) -> str:
        """Calcular complejidad basada en indicadores en el texto"""
        
        complexity_indicators = {
            'high': [
                r'completo|complete|full|integral',
                r'múltiple|multiple|varios|various',
                r'integración|integration|API',
                r'base.*datos|database|backend',
                r'seguridad|security|authentication',
                r'real.*time|tiempo.*real|streaming'
            ],
            'medium': [
                r'crear|create|desarrollar|develop',
                r'procesar|process|analizar|analyze',
                r'automatizar|automate|script',
                r'reportar|report|dashboard'
            ],
            'low': [
                r'simple|básico|basic|pequeño|small',
                r'listar|list|mostrar|show',
                r'buscar|search|find'
            ]
        }
        
        scores = {'high': 0, 'medium': 0, 'low': 0}
        
        for complexity_level, patterns in complexity_indicators.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    scores[complexity_level] += 1
        
        # Determinar complejidad
        if scores['high'] >= 2:
            return 'high'
        elif scores['medium'] >= 1 or scores['high'] >= 1:
            return 'medium'
        else:
            return 'low'
    
    def _identify_required_tools(self, text: str, task_type: str) -> List[str]:
        """Identificar herramientas necesarias"""
        
        tools = set()
        
        # Herramientas por tipo de tarea
        type_tools = {
            'web_development': ['file_manager', 'shell', 'web_search'],
            'data_analysis': ['file_manager', 'shell', 'web_search', 'enhanced_deep_research'],
            'file_processing': ['file_manager', 'shell'],
            'system_administration': ['shell', 'file_manager'],
            'research': ['web_search', 'enhanced_deep_research', 'tavily_search'],
            'automation': ['shell', 'file_manager', 'playwright']
        }
        
        # Agregar herramientas base por tipo
        if task_type in type_tools:
            tools.update(type_tools[task_type])
        
        # Detectar herramientas específicas en el texto
        tool_patterns = {
            'playwright': r'browser|navegador|web.*scraping|automation',
            'firecrawl': r'scraping|crawling|extract.*content',
            'comprehensive_research': r'investigación.*profunda|comprehensive.*research',
            'enhanced_web_search': r'búsqueda.*web|web.*search',
            'shell': r'comando|command|terminal|bash|script',
            'file_manager': r'archivo|file|directorio|folder|crear.*archivo'
        }
        
        for tool, pattern in tool_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                tools.add(tool)
        
        return list(tools)
    
    def _estimate_duration(self, complexity: str, tools: List[str], task_type: str) -> int:
        """Estimar duración en segundos"""
        
        base_duration = {
            'low': 120,     # 2 minutos
            'medium': 300,  # 5 minutos
            'high': 600     # 10 minutos
        }
        
        duration = base_duration.get(complexity, 300)
        
        # Ajustar por número de herramientas
        duration += len(tools) * 30
        
        # Ajustar por tipo de tarea
        type_multipliers = {
            'web_development': 1.5,
            'data_analysis': 1.3,
            'system_administration': 1.2,
            'research': 1.4,
            'automation': 1.6
        }
        
        multiplier = type_multipliers.get(task_type, 1.0)
        duration = int(duration * multiplier)
        
        return duration
    
    def _identify_risk_factors(self, text: str, task_type: str) -> List[str]:
        """Identificar factores de riesgo"""
        
        risks = []
        
        # Riesgos por patrones en texto
        risk_patterns = {
            'Requiere acceso externo': r'API|external|externo|integración',
            'Operación con archivos críticos': r'delete|eliminar|remove|critical',
            'Procesamiento intensivo': r'large|grande|massive|intensivo',
            'Configuración compleja': r'complex|complejo|advanced|avanzado',
            'Dependencias externas': r'install|dependency|dependencia|library'
        }
        
        for risk, pattern in risk_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                risks.append(risk)
        
        # Riesgos por tipo de tarea
        type_risks = {
            'system_administration': ['Cambios en configuración del sistema'],
            'file_processing': ['Posible pérdida de datos'],
            'web_development': ['Dependencias de frameworks externos'],
            'automation': ['Comportamiento impredecible']
        }
        
        if task_type in type_risks:
            risks.extend(type_risks[task_type])
        
        return risks
    
    def _calculate_success_probability(self, complexity: str, risk_factors: List[str], 
                                     tools: List[str]) -> float:
        """Calcular probabilidad de éxito (0.0 - 1.0)"""
        
        base_probability = {
            'low': 0.95,
            'medium': 0.85,
            'high': 0.75
        }
        
        probability = base_probability.get(complexity, 0.85)
        
        # Reducir por factores de riesgo
        probability -= len(risk_factors) * 0.05
        
        # Ajustar por disponibilidad de herramientas
        # (En un sistema real, verificaríamos si las herramientas están disponibles)
        if len(tools) > 5:
            probability -= 0.1  # Muchas herramientas = más complejidad
        
        return max(0.1, min(1.0, probability))
    
    def _calculate_complexity_score(self, complexity: str, num_steps: int) -> float:
        """Calcular score de complejidad (0.0 - 10.0)"""
        
        base_scores = {
            'low': 2.0,
            'medium': 5.0,
            'high': 8.0
        }
        
        score = base_scores.get(complexity, 5.0)
        
        # Ajustar por número de pasos
        score += (num_steps - 3) * 0.5
        
        return max(1.0, min(10.0, score))
    
    def _identify_prerequisites(self, task_type: str, analysis: Dict[str, Any]) -> List[str]:
        """Identificar prerequisitos para la tarea"""
        
        prerequisites = []
        
        # Prerequisites por tipo
        type_prerequisites = {
            'web_development': ['Node.js environment', 'Package manager (npm/yarn)'],
            'data_analysis': ['Python environment', 'Data science libraries'],
            'system_administration': ['System access permissions', 'Admin privileges'],
            'automation': ['Script execution permissions']
        }
        
        if task_type in type_prerequisites:
            prerequisites.extend(type_prerequisites[task_type])
        
        # Prerequisites por complejidad
        if analysis['complexity'] == 'high':
            prerequisites.append('Extended execution time allocated')
        
        if len(analysis['required_tools']) > 3:
            prerequisites.append('Multiple tool dependencies verified')
        
        return prerequisites

    # Templates de planes por tipo de tarea
    
    def _get_web_development_template(self, title: str, description: str, 
                                    analysis: Dict[str, Any]) -> List[TaskStep]:
        """Template para desarrollo web"""
        
        steps = [
            TaskStep(
                id="web-1",
                title="Analizar requisitos",
                description="Analizar requisitos del proyecto web y tecnologías necesarias",
                tool="enhanced_web_search",
                parameters={"query": f"best practices {title} web development"},
                dependencies=[],
                estimated_duration=60,
                complexity="low",
                required_skills=["analysis"]
            ),
            TaskStep(
                id="web-2",
                title="Configurar estructura",
                description="Crear estructura de directorios y archivos base",
                tool="file_manager",
                parameters={"action": "mkdir", "path": "src"},
                dependencies=["web-1"],
                estimated_duration=30,
                complexity="low",
                required_skills=["file_management"]
            ),
            TaskStep(
                id="web-3",
                title="Crear archivos HTML base",
                description="Generar estructura HTML inicial",
                tool="file_manager",
                parameters={"action": "create", "path": "index.html"},
                dependencies=["web-2"],
                estimated_duration=90,
                complexity="medium",
                required_skills=["html", "web_development"]
            ),
            TaskStep(
                id="web-4",
                title="Implementar estilos CSS",
                description="Crear estilos y layout responsivo",
                tool="file_manager",
                parameters={"action": "create", "path": "styles.css"},
                dependencies=["web-3"],
                estimated_duration=120,
                complexity="medium",
                required_skills=["css", "design"]
            ),
            TaskStep(
                id="web-5",
                title="Agregar JavaScript",
                description="Implementar funcionalidad interactiva",
                tool="file_manager",
                parameters={"action": "create", "path": "script.js"},
                dependencies=["web-4"],
                estimated_duration=150,
                complexity="medium",
                required_skills=["javascript", "programming"]
            )
        ]
        
        return steps
    
    def _get_data_analysis_template(self, title: str, description: str, 
                                  analysis: Dict[str, Any]) -> List[TaskStep]:
        """Template para análisis de datos"""
        
        steps = [
            TaskStep(
                id="data-1",
                title="Investigar datasets",
                description="Buscar y evaluar fuentes de datos relevantes",
                tool="enhanced_deep_research",
                parameters={"query": f"{title} dataset sources", "max_sources": 10},
                dependencies=[],
                estimated_duration=120,
                complexity="medium",
                required_skills=["research", "data_science"]
            ),
            TaskStep(
                id="data-2",
                title="Preparar entorno",
                description="Configurar herramientas de análisis de datos",
                tool="shell",
                parameters={"command": "pip install pandas numpy matplotlib seaborn"},
                dependencies=["data-1"],
                estimated_duration=60,
                complexity="low",
                required_skills=["python", "package_management"]
            ),
            TaskStep(
                id="data-3",
                title="Cargar y explorar datos",
                description="Importar datos y realizar análisis exploratorio",
                tool="file_manager",
                parameters={"action": "create", "path": "data_analysis.py"},
                dependencies=["data-2"],
                estimated_duration=180,
                complexity="high",
                required_skills=["python", "pandas", "data_analysis"]
            ),
            TaskStep(
                id="data-4",
                title="Generar visualizaciones",
                description="Crear gráficos y visualizaciones de los datos",
                tool="file_manager",
                parameters={"action": "create", "path": "visualizations.py"},
                dependencies=["data-3"],
                estimated_duration=120,
                complexity="medium",
                required_skills=["matplotlib", "data_visualization"]
            ),
            TaskStep(
                id="data-5",
                title="Crear reporte",
                description="Generar reporte con conclusiones y recomendaciones",
                tool="file_manager",
                parameters={"action": "create", "path": "report.md"},
                dependencies=["data-4"],
                estimated_duration=90,
                complexity="medium",
                required_skills=["reporting", "analysis"]
            )
        ]
        
        return steps
    
    def _get_file_processing_template(self, title: str, description: str, 
                                    analysis: Dict[str, Any]) -> List[TaskStep]:
        """Template para procesamiento de archivos"""
        
        steps = [
            TaskStep(
                id="file-1",
                title="Analizar archivos",
                description="Examinar estructura y formato de archivos",
                tool="shell",
                parameters={"command": "ls -la"},
                dependencies=[],
                estimated_duration=30,
                complexity="low",
                required_skills=["file_management"]
            ),
            TaskStep(
                id="file-2",
                title="Procesar archivos",
                description="Aplicar transformaciones o extracciones necesarias",
                tool="shell",
                parameters={"command": "unzip *.zip"},
                dependencies=["file-1"],
                estimated_duration=90,
                complexity="medium",
                required_skills=["file_processing", "shell_commands"]
            ),
            TaskStep(
                id="file-3",
                title="Organizar resultados",
                description="Estructurar archivos procesados en directorios apropiados",
                tool="file_manager",
                parameters={"action": "mkdir", "path": "processed"},
                dependencies=["file-2"],
                estimated_duration=45,
                complexity="low",
                required_skills=["file_organization"]
            )
        ]
        
        return steps
    
    def _get_system_admin_template(self, title: str, description: str, 
                                 analysis: Dict[str, Any]) -> List[TaskStep]:
        """Template para administración de sistemas"""
        
        steps = [
            TaskStep(
                id="sys-1",
                title="Evaluar sistema",
                description="Revisar estado actual del sistema",
                tool="shell",
                parameters={"command": "systemctl status"},
                dependencies=[],
                estimated_duration=60,
                complexity="medium",
                required_skills=["system_administration"]
            ),
            TaskStep(
                id="sys-2",
                title="Instalar dependencias",
                description="Instalar paquetes y dependencias necesarias",
                tool="shell",
                parameters={"command": "apt update && apt install -y"},
                dependencies=["sys-1"],
                estimated_duration=120,
                complexity="medium",
                required_skills=["package_management", "linux"]
            ),
            TaskStep(
                id="sys-3",
                title="Configurar servicios",
                description="Configurar y activar servicios del sistema",
                tool="file_manager",
                parameters={"action": "write", "path": "/etc/config"},
                dependencies=["sys-2"],
                estimated_duration=90,
                complexity="high",
                required_skills=["configuration", "services"]
            )
        ]
        
        return steps
    
    def _get_research_template(self, title: str, description: str, 
                             analysis: Dict[str, Any]) -> List[TaskStep]:
        """Template para investigación"""
        
        steps = [
            TaskStep(
                id="research-1",
                title="Búsqueda inicial",
                description="Realizar búsqueda web inicial sobre el tema",
                tool="enhanced_web_search",
                parameters={"query": title, "max_results": 15},
                dependencies=[],
                estimated_duration=90,
                complexity="low",
                required_skills=["research", "web_search"]
            ),
            TaskStep(
                id="research-2",
                title="Investigación profunda",
                description="Realizar investigación detallada con múltiples fuentes",
                tool="enhanced_deep_research",
                parameters={"query": title, "max_sources": 20, "research_depth": "comprehensive"},
                dependencies=["research-1"],
                estimated_duration=240,
                complexity="high",
                required_skills=["deep_research", "analysis"]
            ),
            TaskStep(
                id="research-3",
                title="Síntesis de información",
                description="Compilar y sintetizar hallazgos en un reporte",
                tool="file_manager",
                parameters={"action": "create", "path": "research_report.md"},
                dependencies=["research-2"],
                estimated_duration=120,
                complexity="medium",
                required_skills=["writing", "synthesis"]
            )
        ]
        
        return steps
    
    def _get_automation_template(self, title: str, description: str, 
                               analysis: Dict[str, Any]) -> List[TaskStep]:
        """Template para automatización"""
        
        steps = [
            TaskStep(
                id="auto-1",
                title="Diseñar workflow",
                description="Planificar flujo de automatización",
                tool="file_manager",
                parameters={"action": "create", "path": "workflow_design.md"},
                dependencies=[],
                estimated_duration=90,
                complexity="medium",
                required_skills=["planning", "automation_design"]
            ),
            TaskStep(
                id="auto-2",
                title="Crear script",
                description="Desarrollar script de automatización",
                tool="file_manager",
                parameters={"action": "create", "path": "automation_script.py"},
                dependencies=["auto-1"],
                estimated_duration=180,
                complexity="high",
                required_skills=["programming", "scripting"]
            ),
            TaskStep(
                id="auto-3",
                title="Probar automatización",
                description="Ejecutar y validar el script",
                tool="shell",
                parameters={"command": "python automation_script.py"},
                dependencies=["auto-2"],
                estimated_duration=60,
                complexity="medium",
                required_skills=["testing", "debugging"]
            )
        ]
        
        return steps
    
    def _get_general_template(self, title: str, description: str, 
                            analysis: Dict[str, Any]) -> List[TaskStep]:
        """Template genérico para tareas no clasificadas"""
        
        steps = [
            TaskStep(
                id="gen-1",
                title="Analizar la tarea",
                description="Entender requisitos y planificar aproximación",
                tool="enhanced_web_search",
                parameters={"query": f"how to {title}"},
                dependencies=[],
                estimated_duration=60,
                complexity="low",
                required_skills=["analysis"]
            ),
            TaskStep(
                id="gen-2",
                title="Investigar soluciones",
                description="Buscar métodos y herramientas apropiadas",
                tool="enhanced_deep_research",
                parameters={"query": title, "max_sources": 10},
                dependencies=["gen-1"],
                estimated_duration=120,
                complexity="medium",
                required_skills=["research"]
            ),
            TaskStep(
                id="gen-3",
                title="Implementar solución",
                description="Ejecutar la solución identificada",
                tool="file_manager",
                parameters={"action": "create", "path": "solution.txt"},
                dependencies=["gen-2"],
                estimated_duration=90,
                complexity="medium",
                required_skills=["implementation"]
            ),
            TaskStep(
                id="gen-4",
                title="Verificar resultados",
                description="Validar que la solución cumple los requisitos",
                tool="shell",
                parameters={"command": "ls -la"},
                dependencies=["gen-3"],
                estimated_duration=30,
                complexity="low",
                required_skills=["validation"]
            )
        ]
        
        return steps