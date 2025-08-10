"""
Sistema de Planificación Inteligente y Adaptativo
==================================================

Este módulo reemplaza el sistema de templates rígidos con un planificador
inteligente que genera planes adaptativos basados en el contexto de la tarea.

Características:
- Análisis dinámico de tareas sin templates predefinidos
- Generación de prompts adaptativos
- Planificación contextual inteligente
- Feedback en tiempo real durante la ejecución
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from ..config.ollama_config import get_ollama_config
from ..services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

class IntelligentPlanner:
    """
    Planificador Inteligente que genera planes dinámicos sin depender de templates.
    """
    
    def __init__(self, ollama_service: OllamaService = None):
        self.ollama_service = ollama_service
        self.planning_memory = []  # Memoria de planificaciones anteriores para aprendizaje
        
    def analyze_task_context(self, message: str) -> Dict[str, Any]:
        """
        Analiza el contexto de la tarea de manera inteligente sin usar categorías predefinidas.
        
        Args:
            message: Mensaje del usuario describiendo la tarea
            
        Returns:
            Dict con análisis contextual de la tarea
        """
        context = {
            'original_message': message,
            'task_intent': self._extract_task_intent(message),
            'domain_indicators': self._identify_domain_indicators(message),
            'complexity_signals': self._assess_complexity_signals(message),
            'temporal_requirements': self._detect_temporal_requirements(message),
            'output_expectations': self._analyze_output_expectations(message),
            'research_depth_needed': self._assess_research_depth(message),
            'execution_style': self._determine_execution_style(message)
        }
        
        logger.info(f"🧠 Task context analyzed: intent={context['task_intent']}, complexity={context['complexity_signals']['level']}")
        return context
    
    def _extract_task_intent(self, message: str) -> Dict[str, Any]:
        """Extrae la intención principal de la tarea."""
        message_lower = message.lower()
        
        # Verbos de acción que indican intención
        action_patterns = {
            'research': ['investiga', 'busca', 'encuentra', 'explora', 'analiza', 'estudia', 'examina'],
            'create': ['crea', 'genera', 'desarrolla', 'escribe', 'diseña', 'produce', 'construye'],
            'compare': ['compara', 'contrasta', 'evalúa', 'diferencia', 'relaciona'],
            'explain': ['explica', 'describe', 'detalla', 'cuenta', 'resume'],
            'solve': ['soluciona', 'resuelve', 'calcula', 'determina', 'encuentra solución'],
            'plan': ['planifica', 'organiza', 'estructura', 'programa', 'diseña plan']
        }
        
        detected_actions = []
        for action_type, verbs in action_patterns.items():
            for verb in verbs:
                if verb in message_lower:
                    detected_actions.append(action_type)
                    break
        
        # Determinar intención primaria
        primary_intent = detected_actions[0] if detected_actions else 'research'
        
        return {
            'primary': primary_intent,
            'secondary': detected_actions[1:],
            'confidence': 0.8 if detected_actions else 0.5
        }
    
    def _identify_domain_indicators(self, message: str) -> Dict[str, Any]:
        """Identifica indicadores del dominio de conocimiento."""
        message_lower = message.lower()
        
        domain_keywords = {
            'technology': ['ia', 'inteligencia artificial', 'tecnología', 'software', 'programación', 'app', 'sistema'],
            'science': ['científico', 'investigación', 'experimento', 'datos', 'análisis', 'método'],
            'business': ['empresa', 'negocio', 'mercado', 'estrategia', 'competencia', 'ventas'],
            'health': ['salud', 'medicina', 'médico', 'tratamiento', 'enfermedad', 'síntoma'],
            'education': ['educación', 'enseñanza', 'aprendizaje', 'estudiante', 'curso', 'lección'],
            'politics': ['político', 'gobierno', 'política', 'elecciones', 'partido', 'legislación'],
            'sports': ['deporte', 'fútbol', 'equipo', 'jugador', 'campeonato', 'torneo'],
            'entertainment': ['entretenimiento', 'película', 'música', 'arte', 'cultura'],
            'current_events': ['noticias', 'actualidad', '2024', '2025', 'reciente', 'último']
        }
        
        detected_domains = []
        domain_scores = {}
        
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                detected_domains.append(domain)
                domain_scores[domain] = score
        
        # Ordenar por relevancia
        sorted_domains = sorted(detected_domains, key=lambda d: domain_scores[d], reverse=True)
        
        return {
            'primary_domain': sorted_domains[0] if sorted_domains else 'general',
            'secondary_domains': sorted_domains[1:3],
            'confidence': min(max(domain_scores.get(sorted_domains[0], 0) / 3, 0.3), 1.0) if sorted_domains else 0.3
        }
    
    def _assess_complexity_signals(self, message: str) -> Dict[str, Any]:
        """Evalúa señales de complejidad en la tarea."""
        message_lower = message.lower()
        
        complexity_indicators = {
            'high': ['detallado', 'completo', 'exhaustivo', 'profundo', 'comprensivo', 'múltiples fuentes', 'análisis completo'],
            'medium': ['análisis', 'investigación', 'compara', 'evalúa', 'desarrolla'],
            'low': ['simple', 'básico', 'rápido', 'resumen', 'lista']
        }
        
        complexity_score = 0
        detected_indicators = []
        
        for level, indicators in complexity_indicators.items():
            for indicator in indicators:
                if indicator in message_lower:
                    detected_indicators.append((level, indicator))
                    if level == 'high':
                        complexity_score += 3
                    elif level == 'medium':
                        complexity_score += 2
                    else:
                        complexity_score += 1
        
        # Determinar nivel de complejidad
        if complexity_score >= 5:
            level = 'alta'
        elif complexity_score >= 2:
            level = 'media'
        else:
            level = 'baja'
        
        return {
            'level': level,
            'score': complexity_score,
            'indicators': detected_indicators,
            'estimated_steps': min(max(complexity_score + 2, 3), 6)
        }
    
    def _detect_temporal_requirements(self, message: str) -> Dict[str, Any]:
        """Detecta requirements temporales."""
        message_lower = message.lower()
        
        temporal_indicators = {
            'urgent': ['urgente', 'rápido', 'inmediato', 'ya', 'ahora'],
            'current': ['actual', 'reciente', '2024', '2025', 'último', 'nueva'],
            'historical': ['historia', 'pasado', 'evolución', 'desarrollo histórico'],
            'future': ['futuro', 'proyección', 'predicción', 'tendencias']
        }
        
        detected_temporal = []
        for category, indicators in temporal_indicators.items():
            for indicator in indicators:
                if indicator in message_lower:
                    detected_temporal.append(category)
                    break
        
        return {
            'urgency': 'urgent' in detected_temporal,
            'current_focus': 'current' in detected_temporal,
            'temporal_scope': detected_temporal,
            'needs_real_time_data': 'current' in detected_temporal or 'urgent' in detected_temporal
        }
    
    def _analyze_output_expectations(self, message: str) -> Dict[str, Any]:
        """Analiza qué tipo de output espera el usuario."""
        message_lower = message.lower()
        
        output_patterns = {
            'document': ['informe', 'documento', 'reporte', 'ensayo', 'artículo'],
            'list': ['lista', 'listado', 'enumera', 'puntos'],
            'analysis': ['análisis', 'evaluación', 'estudio', 'investigación'],
            'comparison': ['comparación', 'diferencias', 'similitudes', 'contraste'],
            'summary': ['resumen', 'síntesis', 'resumen ejecutivo'],
            'data': ['datos', 'estadísticas', 'números', 'métricas', 'cifras']
        }
        
        expected_outputs = []
        for output_type, patterns in output_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    expected_outputs.append(output_type)
                    break
        
        return {
            'primary_output': expected_outputs[0] if expected_outputs else 'analysis',
            'multiple_outputs': len(expected_outputs) > 1,
            'output_types': expected_outputs,
            'requires_structured_data': 'data' in expected_outputs or 'list' in expected_outputs
        }
    
    def _assess_research_depth(self, message: str) -> Dict[str, Any]:
        """Evalúa la profundidad de investigación necesaria."""
        message_lower = message.lower()
        
        depth_indicators = {
            'surface': ['rápido', 'básico', 'simple', 'general'],
            'moderate': ['investigación', 'análisis', 'información'],
            'deep': ['exhaustivo', 'detallado', 'profundo', 'completo', 'comprensivo', 'múltiples fuentes']
        }
        
        depth_score = 0
        for depth, indicators in depth_indicators.items():
            for indicator in indicators:
                if indicator in message_lower:
                    if depth == 'deep':
                        depth_score += 3
                    elif depth == 'moderate':
                        depth_score += 2
                    else:
                        depth_score += 1
        
        if depth_score >= 4:
            research_depth = 'profunda'
        elif depth_score >= 2:
            research_depth = 'moderada'
        else:
            research_depth = 'superficial'
        
        return {
            'depth': research_depth,
            'requires_multiple_sources': depth_score >= 3,
            'needs_verification': depth_score >= 2,
            'estimated_research_time': min(depth_score * 5 + 5, 25)  # minutos
        }
    
    def _determine_execution_style(self, message: str) -> Dict[str, Any]:
        """Determina el estilo de ejecución más apropiado."""
        context_analysis = {
            'collaborative': False,  # Por ahora single-agent
            'iterative': 'paso a paso' in message.lower() or 'iterativo' in message.lower(),
            'parallel': 'simultáneo' in message.lower() or 'paralelo' in message.lower(),
            'sequential': True,  # Por defecto secuencial
            'adaptive': True   # Siempre adaptativo
        }
        
        return context_analysis
    
    def generate_intelligent_plan(self, message: str, task_id: str) -> Dict[str, Any]:
        """
        Genera un plan inteligente y adaptativo basado en el análisis contextual.
        
        Args:
            message: Mensaje del usuario
            task_id: ID de la tarea
            
        Returns:
            Dict con el plan generado
        """
        logger.info(f"🧠 Generating intelligent adaptive plan for: {message[:50]}...")
        
        # Analizar contexto de la tarea
        context = self.analyze_task_context(message)
        
        # Generar prompt adaptativo
        adaptive_prompt = self._create_adaptive_prompt(message, context)
        
        # Usar IA para generar plan inteligente
        if self.ollama_service and self.ollama_service.is_healthy():
            plan = self._generate_ai_plan(adaptive_prompt, task_id, context)
        else:
            plan = self._generate_fallback_plan(message, context)
        
        # Enriquecer plan con contexto
        plan = self._enrich_plan_with_context(plan, context)
        
        logger.info(f"✅ Intelligent plan generated: {len(plan.get('steps', []))} steps")
        return plan
    
    def _create_adaptive_prompt(self, message: str, context: Dict[str, Any]) -> str:
        """
        Crea un prompt adaptativo basado en el contexto analizado.
        """
        intent = context['task_intent']['primary']
        domain = context['domain_indicators']['primary_domain']
        complexity = context['complexity_signals']['level']
        output_type = context['output_expectations']['primary_output']
        research_depth = context['research_depth']['depth']
        
        # Prompt base adaptativo
        base_prompt = f"""SISTEMA DE PLANIFICACIÓN INTELIGENTE

TAREA DEL USUARIO: {message}

ANÁLISIS CONTEXTUAL:
- Intención principal: {intent}
- Dominio: {domain}
- Complejidad: {complexity}
- Tipo de output esperado: {output_type}
- Profundidad de investigación: {research_depth}

INSTRUCCIONES PARA GENERAR PLAN INTELIGENTE:

1. ADAPTA los pasos según el contexto específico analizado
2. NO uses templates genéricos - cada paso debe ser específico para "{message}"
3. CONSIDERA la complejidad {complexity} para determinar el número de pasos
4. INCLUYE pasos de investigación real si se requiere información actualizada
5. ASEGÚRATE de que el resultado final coincida exactamente con lo solicitado

"""
        
        # Agregar instrucciones específicas según el contexto
        if context['temporal_requirements']['needs_real_time_data']:
            base_prompt += """
REQUERIMIENTO CRÍTICO: La tarea requiere información actualizada y en tiempo real.
- Incluir búsqueda web activa
- Priorizar fuentes recientes (2024-2025)
- Verificar datos actuales
"""
        
        if research_depth == 'profunda':
            base_prompt += """
INVESTIGACIÓN PROFUNDA REQUERIDA:
- Múltiples fuentes de información
- Análisis detallado de datos
- Verificación cruzada de información
- Síntesis comprehensiva
"""
        
        if output_type == 'document':
            base_prompt += """
OUTPUT TIPO DOCUMENTO:
- Estructura clara y profesional
- Contenido detallado y bien organizado
- Formato listo para entrega
"""
        
        # Formato de respuesta JSON
        base_prompt += f"""
GENERA PLAN EN FORMATO JSON (sin texto adicional):
{{
  "steps": [
    // Entre {context['complexity_signals']['estimated_steps']} pasos específicos para "{message}"
    {{
      "id": "step-1",
      "title": "Título específico para {message}",
      "description": "Descripción detallada de qué hará este paso para completar {message}",
      "tool": "web_search|analysis|creation|processing",
      "estimated_time": "X-Y minutos",
      "complexity": "baja|media|alta",
      "expected_output": "Qué información o resultado específico producirá este paso"
    }}
  ],
  "task_type": "{domain}",
  "complexity": "{complexity}",
  "estimated_total_time": "X-Y minutos",
  "adaptation_notes": "Cómo se adaptó el plan al contexto específico"
}}

IMPORTANTE: Cada paso debe tener un propósito único y específico para completar "{message}".
"""
        
        return base_prompt
    
    def _generate_ai_plan(self, adaptive_prompt: str, task_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Genera plan usando IA con prompt adaptativo."""
        try:
            logger.info("🤖 Generating plan with AI using adaptive prompt")
            
            result = self.ollama_service.generate_response(
                adaptive_prompt,
                {
                    'temperature': 0.7,
                    'max_tokens': 1500,
                    'top_p': 0.9
                },
                False,  # No usar herramientas para generar JSON limpio
                task_id,
                "intelligent_planning"
            )
            
            if result.get('error'):
                logger.error(f"❌ AI plan generation error: {result['error']}")
                return self._generate_fallback_plan(context['original_message'], context)
            
            # Parsear respuesta JSON
            response_text = result.get('response', '').strip()
            plan_data = self._parse_ai_response(response_text)
            
            if plan_data:
                logger.info("✅ AI plan generated successfully")
                return plan_data
            else:
                logger.warning("⚠️ Failed to parse AI response, using fallback")
                return self._generate_fallback_plan(context['original_message'], context)
        
        except Exception as e:
            logger.error(f"❌ Error in AI plan generation: {str(e)}")
            return self._generate_fallback_plan(context['original_message'], context)
    
    def _parse_ai_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parsea la respuesta de IA para extraer JSON."""
        try:
            # Limpieza de texto
            cleaned_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Buscar JSON en el texto
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                plan_data = json.loads(json_str)
                
                # Validar estructura básica
                if 'steps' in plan_data and isinstance(plan_data['steps'], list):
                    # Asegurar IDs únicos
                    for i, step in enumerate(plan_data['steps']):
                        if 'id' not in step:
                            step['id'] = f"step-{i+1}"
                    
                    return plan_data
            
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Error parsing AI response: {str(e)}")
            return None
    
    def _generate_fallback_plan(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Genera plan de respaldo inteligente sin IA."""
        logger.info("🔄 Generating intelligent fallback plan")
        
        intent = context['task_intent']['primary']
        complexity = context['complexity_signals']['level']
        num_steps = context['complexity_signals']['estimated_steps']
        
        # Generar pasos basados en intención
        steps = []
        
        if intent in ['research', 'explain']:
            steps = [
                {
                    "id": "step-1",
                    "title": f"Investigar información específica para {message}",
                    "description": f"Buscar y recopilar datos actualizados y relevantes necesarios para completar: {message}",
                    "tool": "web_search",
                    "estimated_time": "8-12 minutos",
                    "complexity": "media",
                    "expected_output": "Información específica y actualizada sobre el tema solicitado"
                },
                {
                    "id": "step-2", 
                    "title": "Analizar y procesar información recopilada",
                    "description": f"Procesar, estructurar y analizar la información encontrada para su uso en: {message}",
                    "tool": "analysis",
                    "estimated_time": "10-15 minutos",
                    "complexity": "alta",
                    "expected_output": "Análisis estructurado de la información"
                },
                {
                    "id": "step-3",
                    "title": f"Completar: {message}",
                    "description": f"Desarrollar y entregar exactamente lo solicitado: {message}",
                    "tool": "creation",
                    "estimated_time": "12-18 minutos",
                    "complexity": "alta",
                    "expected_output": "Resultado final completado según los requerimientos"
                }
            ]
        
        elif intent in ['create', 'solve']:
            steps = [
                {
                    "id": "step-1",
                    "title": f"Planificar desarrollo de: {message}",
                    "description": f"Estructurar el enfoque y metodología para completar: {message}",
                    "tool": "planning",
                    "estimated_time": "5-8 minutos",
                    "complexity": "media",
                    "expected_output": "Plan estructurado de desarrollo"
                },
                {
                    "id": "step-2",
                    "title": f"Desarrollar contenido para: {message}",
                    "description": f"Crear el contenido base necesario para: {message}",
                    "tool": "creation",
                    "estimated_time": "15-20 minutos",
                    "complexity": "alta",
                    "expected_output": "Contenido desarrollado según especificaciones"
                },
                {
                    "id": "step-3",
                    "title": f"Finalizar y entregar: {message}",
                    "description": f"Revisar, refinar y completar la entrega final de: {message}",
                    "tool": "processing",
                    "estimated_time": "8-12 minutos",
                    "complexity": "media",
                    "expected_output": "Resultado final revisado y completo"
                }
            ]
        
        # Ajustar según complejidad
        if complexity == 'alta' and len(steps) < 4:
            steps.insert(1, {
                "id": "step-research",
                "title": "Investigación complementaria detallada",
                "description": f"Búsqueda exhaustiva de información adicional para enriquecer: {message}",
                "tool": "web_search",
                "estimated_time": "10-15 minutos",
                "complexity": "alta",
                "expected_output": "Información complementaria detallada"
            })
        
        # Recalcular IDs
        for i, step in enumerate(steps):
            step['id'] = f"step-{i+1}"
        
        total_time = sum(int(step['estimated_time'].split('-')[1].replace(' minutos', '')) for step in steps)
        
        return {
            "steps": steps,
            "task_type": context['domain_indicators']['primary_domain'],
            "complexity": complexity,
            "estimated_total_time": f"{total_time-10}-{total_time} minutos",
            "adaptation_notes": f"Plan adaptado para {intent} en dominio {context['domain_indicators']['primary_domain']}",
            "intelligent_planning": True,
            "fallback_plan": True
        }
    
    def _enrich_plan_with_context(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Enriquece el plan con información contextual."""
        plan['context_analysis'] = {
            'task_intent': context['task_intent']['primary'],
            'domain': context['domain_indicators']['primary_domain'],
            'complexity_assessed': context['complexity_signals']['level'],
            'research_depth': context['research_depth']['depth'],
            'requires_real_time_data': context['temporal_requirements']['needs_real_time_data'],
            'output_type': context['output_expectations']['primary_output']
        }
        
        plan['intelligent_features'] = {
            'adaptive_prompts': True,
            'context_aware': True,
            'template_free': True,
            'real_time_feedback': True
        }
        
        return plan

# Instancia global del planificador inteligente
_intelligent_planner_instance = None

def get_intelligent_planner(ollama_service: OllamaService = None) -> IntelligentPlanner:
    """Obtiene la instancia del planificador inteligente."""
    global _intelligent_planner_instance
    if _intelligent_planner_instance is None:
        _intelligent_planner_instance = IntelligentPlanner(ollama_service)
    return _intelligent_planner_instance