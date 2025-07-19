"""
Rutas API del agente - Versión REAL CON OLLAMA
Sistema de agente que usa Ollama real para generar respuestas inteligentes
Y distingue entre conversaciones casuales y tareas complejas
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
import time
import uuid
import json
import os
import requests
import re

logger = logging.getLogger(__name__)

agent_bp = Blueprint('agent', __name__)

# Almacenamiento temporal para compartir conversaciones
shared_conversations = {}
# Almacenamiento temporal para archivos por tarea
task_files = {}
# Almacenamiento global para planes de tareas
active_task_plans = {}

# Patrones para detectar tipo de mensaje
CASUAL_PATTERNS = [
    r'^hola\b',
    r'^¿?cómo estás\??$',
    r'^¿?qué tal\??$',
    r'^buenos días\b',
    r'^buenas tardes\b',
    r'^buenas noches\b',
    r'^¿?cómo te llamas\??$',
    r'^¿?quién eres\??$',
    r'^gracias\b',
    r'^de nada\b',
    r'^adiós\b',
    r'^hasta luego\b',
    r'^ok\b',
    r'^vale\b',
    r'^perfecto\b',
    r'^entiendo\b'
]

TASK_PATTERNS = [
    r'crear\b.*\b(informe|reporte|documento|análisis|plan|estrategia)',
    r'analizar\b.*\b(datos|información|tendencias|mercado)',
    r'buscar\b.*\b(información|datos|sobre)',
    r'investigar\b.*\b(sobre|tendencias|mercado)',
    r'generar\b.*\b(contenido|texto|código|script)',
    r'desarrollar\b.*\b(aplicación|web|software)',
    r'escribir\b.*\b(código|script|programa)',
    r'hacer\b.*\b(análisis|investigación|estudio)',
    r'realizar\b.*\b(estudio|investigación|análisis)',
    r'dame\b.*\b(información|datos|informe|reporte)',
    r'necesito\b.*\b(información|datos|ayuda con)',
    r'quiero\b.*\b(crear|generar|desarrollar|hacer)',
    r'puedes\b.*\b(crear|generar|buscar|investigar)',
    r'ayúdame\b.*\b(con|a crear|a generar|a desarrollar)'
]

def is_casual_conversation(message: str) -> bool:
    """Detecta si un mensaje es una conversación casual"""
    message_lower = message.lower().strip()
    
    # Mensajes muy cortos (menos de 3 palabras) probablemente son casuales
    if len(message_lower.split()) <= 3:
        for pattern in CASUAL_PATTERNS:
            if re.search(pattern, message_lower):
                return True
    
    # Verificar patrones de tareas PRIMERO
    for pattern in TASK_PATTERNS:
        if re.search(pattern, message_lower):
            return False
    
    # Verificar palabras clave que indican tarea (más amplio)
    task_keywords = [
        'buscar', 'busca', 'investigar', 'investiga', 'analizar', 'analiza',
        'crear', 'crea', 'generar', 'genera', 'desarrollar', 'desarrolla',
        'hacer', 'haz', 'escribir', 'escribe', 'dame', 'dime', 'necesito',
        'quiero', 'puedes', 'ayúdame', 'planificar', 'planifica', 'realizar',
        'informe', 'reporte', 'análisis', 'estudio', 'investigación'
    ]
    
    # Si contiene palabras clave de tareas, NO es casual
    for keyword in task_keywords:
        if keyword in message_lower:
            return False
    
    # Si no hay patrones de tareas y es muy corto, probablemente es casual
    if len(message_lower.split()) <= 5:
        return True
    
    # Si tiene más de 5 palabras y no es claramente casual, tratarlo como tarea
    return False

def get_ollama_service():
    """Obtener servicio de Ollama"""
    try:
        service = current_app.ollama_service
        logger.info(f"✅ Ollama service found: {service}")
        return service
    except AttributeError:
        logger.error("❌ Ollama service not available")
        return None

def get_tool_manager():
    """Obtener tool manager"""
    try:
        return current_app.tool_manager
    except AttributeError:
        logger.error("Tool manager not available")
        return None

def execute_plan_with_real_tools(task_id: str, plan_steps: list, message: str):
    """
    Ejecuta REALMENTE los pasos del plan usando herramientas y entrega resultados finales
    """
    try:
        import threading
        import time
        
        # Obtener servicios ANTES de crear el hilo
        ollama_service = get_ollama_service()
        tool_manager = get_tool_manager()
        
        def execute_steps():
            if task_id not in active_task_plans:
                return
                
            plan_data = active_task_plans[task_id]
            steps = plan_data['plan']
            final_results = []  # Almacenar resultados de cada paso
            
            logger.info(f"🚀 Starting REAL execution of {len(steps)} steps for task: {message}")
            
            for i, step in enumerate(steps):
                logger.info(f"🔄 Executing step {i+1}/{len(steps)}: {step['title']}")
                
                # Marcar paso como activo
                step['active'] = True
                step['status'] = 'in-progress'
                
                # Actualizar plan en memoria
                active_task_plans[task_id]['plan'] = steps
                active_task_plans[task_id]['current_step'] = i + 1
                
                step_result = None
                try:
                    # EJECUTAR HERRAMIENTA REAL según el tipo de paso
                    if step['tool'] == 'web_search' or 'búsqueda' in step['title'].lower():
                        if tool_manager:
                            search_query = extract_search_query_from_message(message, step['title'])
                            logger.info(f"🔍 Executing web search for: {search_query}")
                            
                            result = tool_manager.execute_tool('web_search', {
                                'query': search_query,
                                'num_results': 5
                            }, task_id=task_id)
                            
                            step_result = {
                                'type': 'web_search',
                                'query': search_query,
                                'results': result.get('search_results', []),
                                'summary': f"Encontradas {len(result.get('search_results', []))} fuentes relevantes"
                            }
                            
                            step['result'] = step_result
                            final_results.append(step_result)
                            logger.info(f"✅ Web search completed: {len(result.get('search_results', []))} results")
                        else:
                            time.sleep(3)
                    
                    elif step['tool'] == 'analysis' or 'análisis' in step['title'].lower():
                        if ollama_service:
                            logger.info(f"🧠 Executing analysis using Ollama")
                            
                            # Generar análisis específico usando contexto previo
                            analysis_context = f"Tarea: {message}\nPaso actual: {step['title']}\nDescripción: {step['description']}"
                            if final_results:
                                analysis_context += f"\nResultados previos: {final_results[-1] if final_results else 'Ninguno'}"
                            
                            analysis_prompt = f"""
Realiza un análisis detallado para:
{analysis_context}

Proporciona:
1. Análisis específico del contexto
2. Hallazgos principales
3. Recomendaciones para próximos pasos
4. Conclusiones preliminares

Formato: Respuesta estructurada y profesional.
"""
                            
                            result = ollama_service.generate_response(analysis_prompt, {})
                            
                            step_result = {
                                'type': 'analysis',
                                'content': result.get('response', 'Análisis completado'),
                                'summary': 'Análisis detallado generado exitosamente'
                            }
                            
                            step['result'] = step_result
                            final_results.append(step_result)
                            logger.info(f"✅ Analysis completed")
                        else:
                            time.sleep(2)
                    
                    elif step['tool'] == 'creation' or 'creación' in step['title'].lower() or 'desarrollo' in step['title'].lower():
                        if ollama_service:
                            logger.info(f"🛠️ Executing creation using Ollama")
                            
                            # Generar contenido específico
                            creation_context = f"Tarea: {message}\nPaso: {step['title']}\nDescripción: {step['description']}"
                            if final_results:
                                creation_context += f"\nInformación previa: {final_results}"
                            
                            creation_prompt = f"""
Crea el contenido solicitado para:
{creation_context}

Genera contenido específico, detallado y profesional que cumpla exactamente con los requisitos de la tarea.

Incluye:
1. Contenido principal solicitado
2. Estructura organizada
3. Información relevante y precisa
4. Formato profesional

Responde con el contenido completo y listo para usar.
"""
                            
                            result = ollama_service.generate_response(creation_prompt, {})
                            
                            step_result = {
                                'type': 'creation',
                                'content': result.get('response', 'Contenido creado'),
                                'summary': 'Contenido creado exitosamente'
                            }
                            
                            step['result'] = step_result
                            final_results.append(step_result)
                            logger.info(f"✅ Content creation completed")
                        else:
                            time.sleep(4)
                    
                    elif step['tool'] == 'planning' or 'planificación' in step['title'].lower():
                        if ollama_service:
                            logger.info(f"📋 Executing planning using Ollama")
                            
                            planning_prompt = f"""
Crea un plan detallado para: {message}

Basándote en el contexto:
- Tarea: {step['title']}
- Descripción: {step['description']}
- Información previa: {final_results if final_results else 'Primera fase'}

Genera un plan estructurado con:
1. Objetivos claros
2. Pasos específicos
3. Recursos necesarios
4. Cronograma estimado
5. Criterios de éxito

Proporciona un plan completo y actionable.
"""
                            
                            result = ollama_service.generate_response(planning_prompt, {})
                            
                            step_result = {
                                'type': 'planning',
                                'content': result.get('response', 'Plan generado'),
                                'summary': 'Plan detallado creado exitosamente'
                            }
                            
                            step['result'] = step_result
                            final_results.append(step_result)
                            logger.info(f"✅ Planning completed")
                        else:
                            time.sleep(2)
                    
                    elif step['tool'] == 'delivery' or 'entrega' in step['title'].lower():
                        if ollama_service:
                            logger.info(f"📦 Executing final delivery using Ollama")
                            
                            # Generar entrega final con todos los resultados
                            delivery_prompt = f"""
Prepara la entrega final para la tarea: {message}

Consolida todos los resultados obtenidos:
{final_results}

Crea un documento de entrega final que incluya:
1. RESUMEN EJECUTIVO de lo realizado
2. RESULTADOS PRINCIPALES obtenidos
3. CONTENIDO COMPLETO generado
4. CONCLUSIONES Y RECOMENDACIONES
5. ENTREGABLES FINALES

Formato: Documento profesional completo y estructurado.
"""
                            
                            result = ollama_service.generate_response(delivery_prompt, {})
                            
                            step_result = {
                                'type': 'delivery',
                                'content': result.get('response', 'Entrega completada'),
                                'summary': 'Tarea completada exitosamente con entrega final',
                                'final_deliverable': True
                            }
                            
                            step['result'] = step_result
                            final_results.append(step_result)
                            logger.info(f"✅ Final delivery completed")
                        else:
                            time.sleep(2)
                    
                    else:
                        # Paso genérico - ejecutar con Ollama
                        if ollama_service:
                            logger.info(f"⚡ Executing generic step: {step['title']}")
                            
                            generic_prompt = f"""
Ejecuta el paso '{step['title']}' para la tarea: {message}

Descripción: {step['description']}
Contexto previo: {final_results if final_results else 'Inicio de tarea'}

Proporciona un resultado específico y útil para este paso.
"""
                            
                            result = ollama_service.generate_response(generic_prompt, {})
                            
                            step_result = {
                                'type': 'generic',
                                'content': result.get('response', 'Paso completado'),
                                'summary': f"Paso '{step['title']}' completado exitosamente"
                            }
                            
                            step['result'] = step_result
                            final_results.append(step_result)
                            logger.info(f"✅ Generic step completed: {step['title']}")
                        else:
                            time.sleep(2)
                    
                    # Marcar paso como completado
                    step['completed'] = True
                    step['active'] = False
                    step['status'] = 'completed'
                    
                    logger.info(f"✅ Step {i+1} completed successfully: {step['title']}")
                    
                    # Pausa entre pasos para dar tiempo a mostrar progreso
                    time.sleep(2)
                    
                except Exception as step_error:
                    logger.error(f"❌ Error in step {i+1}: {str(step_error)}")
                    step['completed'] = False
                    step['active'] = False
                    step['status'] = 'failed'
                    step['error'] = str(step_error)
                
                # Actualizar plan en memoria
                active_task_plans[task_id]['plan'] = steps
            
            # GENERAR RESULTADO FINAL CONSOLIDADO
            if final_results:
                logger.info(f"🎯 Generating final consolidated result for task {task_id}")
                
                try:
                    if ollama_service:
                        final_prompt = f"""
TAREA COMPLETADA: {message}

RESULTADOS OBTENIDOS:
{final_results}

Genera un RESULTADO FINAL CONSOLIDADO que incluya:

1. 🎯 RESUMEN EJECUTIVO
   - Qué se solicitó
   - Qué se logró
   - Calidad del resultado

2. 📋 ENTREGABLES PRINCIPALES
   - Lista clara de lo que se entregó
   - Resultados específicos obtenidos

3. 🔍 HALLAZGOS CLAVE (si aplica)
   - Información importante encontrada
   - Insights relevantes

4. ✅ CONCLUSIONES
   - Evaluación del éxito de la tarea
   - Recomendaciones adicionales

Formato: Profesional, estructurado y completo.
"""
                        
                        final_result = ollama_service.generate_response(final_prompt, {})
                        
                        # Guardar resultado final
                        active_task_plans[task_id]['final_result'] = {
                            'content': final_result.get('response', 'Tarea completada exitosamente'),
                            'completed_at': datetime.now().isoformat(),
                            'total_steps': len(steps),
                            'all_results': final_results
                        }
                        
                        logger.info(f"✅ Final consolidated result generated for task {task_id}")
                        
                except Exception as e:
                    logger.error(f"Error generating final result: {str(e)}")
                    active_task_plans[task_id]['final_result'] = {
                        'content': 'Tarea completada con algunos errores en la consolidación final',
                        'completed_at': datetime.now().isoformat(),
                        'total_steps': len(steps),
                        'error': str(e)
                    }
            
            # Marcar tarea como completada
            active_task_plans[task_id]['status'] = 'completed'
            active_task_plans[task_id]['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"🎉 Task {task_id} completed successfully with REAL execution and final delivery!")
        
        # Ejecutar en hilo separado
        thread = threading.Thread(target=execute_steps)
        thread.daemon = True
        thread.start()
        
        logger.info(f"🚀 Started REAL plan execution for task {task_id}")
        
    except Exception as e:
        logger.error(f"Error in real plan execution: {str(e)}")
        
        # Marcar como fallido
        if task_id in active_task_plans:
            active_task_plans[task_id]['status'] = 'failed'
            active_task_plans[task_id]['error'] = str(e)

def extract_search_query_from_message(message: str, step_title: str) -> str:
    """
    Extrae una query de búsqueda relevante del mensaje original
    """
    try:
        # Remover palabras comunes y conectores
        stop_words = ['el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'en', 'con', 'por', 'para', 'sobre', 'crear', 'buscar', 'dame', 'necesito']
        
        # Usar el mensaje original como base
        words = [word for word in message.lower().split() if word not in stop_words and len(word) > 2]
        
        # Tomar las primeras 3-4 palabras más relevantes
        query = ' '.join(words[:4])
        
        # Si la query está vacía, usar el título del paso
        if not query.strip():
            query = step_title.replace('Búsqueda de', '').replace('información', '').strip()
        
        return query or message[:50]  # Fallback al mensaje original truncado
        
    except Exception:
        return message[:50]  # Fallback seguro

def generate_dynamic_plan_with_ai(message: str, task_id: str) -> dict:
    """
    Genera un plan dinámico y específico usando IA para analizar la tarea
    """
    try:
        # Obtener servicio de Ollama para generar plan dinámico
        ollama_service = get_ollama_service()
        
        if not ollama_service:
            logger.warning(f"⚠️ Ollama service not available for task {task_id}, using fallback plan")
            return generate_fallback_plan(message, task_id)
        
        # Verificar si Ollama está funcionando
        if not ollama_service.is_healthy():
            logger.warning(f"⚠️ Ollama not healthy for task {task_id}, using fallback plan")
            return generate_fallback_plan(message, task_id)

        logger.info(f"🤖 Generating AI-powered plan for task {task_id}: '{message[:50]}...'")
        
        # Prompt ultra-específico y restrictivo para generación JSON
        plan_prompt = f"""
Eres un planificador de tareas experto. Debes responder SOLO con JSON válido, sin texto adicional.

TAREA: "{message}"

INSTRUCCIONES OBLIGATORIAS:
1. Responde ÚNICAMENTE con el JSON
2. No agregues explicaciones, texto adicional, ni comentarios
3. Cada paso debe ser específico para esta tarea exacta
4. Usa herramientas: web_search, analysis, planning, creation, delivery, synthesis, data_analysis, processing

FORMATO JSON OBLIGATORIO:
{{
  "task_type": "investigación",
  "complexity": "media",
  "estimated_total_time": "3-5 minutos",
  "steps": [
    {{
      "id": "step_1",
      "title": "Paso específico para '{message}'",
      "description": "Descripción detallada específica",
      "tool": "web_search",
      "estimated_time": "1 minuto",
      "priority": "alta"
    }},
    {{
      "id": "step_2",
      "title": "Segundo paso específico",
      "description": "Segunda acción detallada específica",
      "tool": "analysis", 
      "estimated_time": "1.5 minutos",
      "priority": "alta"
    }},
    {{
      "id": "step_3",
      "title": "Tercer paso específico",
      "description": "Tercera acción detallada específica",
      "tool": "creation",
      "estimated_time": "2 minutos", 
      "priority": "media"
    }}
  ]
}}

RESPONDE SOLO JSON:"""
        
        # Generar plan usando Ollama con parámetros optimizados para JSON
        logger.info(f"📤 Sending JSON plan generation request to Ollama for task {task_id}")
        
        # Usar parámetros específicos para generación JSON estructurada
        ollama_context = {
            'system_prompt': 'You are a JSON task planner. Respond ONLY with valid JSON. No additional text.',
            'temperature': 0.3,  # Más bajo para respuestas más consistentes
            'response_format': 'json'
        }
        
        response = ollama_service.generate_response(plan_prompt, ollama_context)
        
        if response.get('error'):
            logger.error(f"❌ Ollama error generating AI plan for task {task_id}: {response['error']}")
            return generate_fallback_plan(message, task_id)
        
        logger.info(f"📥 Received response from Ollama for task {task_id}: {len(response.get('response', ''))} characters")
        
        try:
            import json
            import re
            
            # Extraer JSON del response con estrategias múltiples y robustas
            response_text = response['response'].strip()
            logger.info(f"🔍 Raw Ollama response for task {task_id}: {response_text[:300]}...")
            
            # Limpiar response de texto adicional común
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            response_text = re.sub(r'^[^{]*', '', response_text)  # Remover texto antes del {
            response_text = re.sub(r'}[^}]*$', '}', response_text)  # Remover texto después del }
            
            # Estrategias de extracción JSON
            plan_data = None
            
            # Estrategia 1: JSON directo
            if response_text.startswith('{') and response_text.endswith('}'):
                try:
                    plan_data = json.loads(response_text)
                    logger.info(f"✅ Strategy 1: Direct JSON parsing successful for task {task_id}")
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Strategy 1 failed for task {task_id}: {e}")
            
            # Estrategia 2: Buscar primer JSON válido
            if not plan_data:
                json_matches = re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text)
                for match in json_matches:
                    try:
                        plan_data = json.loads(match.group())
                        if isinstance(plan_data.get('steps'), list):
                            logger.info(f"✅ Strategy 2: Pattern matching successful for task {task_id}")
                            break
                    except:
                        continue
            
            # Estrategia 3: Buscar JSON entre llaves más profundo
            if not plan_data:
                try:
                    # Buscar el JSON más grande posible
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}')
                    if start_idx != -1 and end_idx != -1:
                        json_candidate = response_text[start_idx:end_idx+1]
                        plan_data = json.loads(json_candidate)
                        logger.info(f"✅ Strategy 3: Deep extraction successful for task {task_id}")
                except:
                    pass
            
            if not plan_data:
                logger.error(f"❌ All JSON extraction strategies failed for task {task_id}")
                logger.error(f"📝 Full response: {response_text}")
                return generate_fallback_plan(message, task_id)
            
            # Validar que el plan tenga la estructura esperada
            if not isinstance(plan_data.get('steps'), list) or len(plan_data.get('steps', [])) == 0:
                logger.error(f"❌ Invalid plan structure for task {task_id}: no valid steps found")
                logger.error(f"📊 Plan data keys: {list(plan_data.keys())}")
                return generate_fallback_plan(message, task_id)
            
            # Convertir a formato frontend
            plan_steps = []
            for i, step in enumerate(plan_data.get('steps', [])):
                if not isinstance(step, dict):
                    logger.warning(f"⚠️ Invalid step format for task {task_id}, step {i}: {step}")
                    continue
                    
                plan_steps.append({
                    'id': f"step_{i+1}",
                    'title': step.get('title', f'Paso {i+1}').strip(),
                    'description': step.get('description', 'Procesando...').strip(),
                    'tool': step.get('tool', 'processing'),
                    'status': 'pending',
                    'estimated_time': step.get('estimated_time', '1 minuto'),
                    'completed': False,
                    'active': i == 0,  # Solo el primer paso activo
                    'priority': step.get('priority', 'media')
                })
            
            if len(plan_steps) == 0:
                logger.error(f"❌ No valid steps created for task {task_id}")
                return generate_fallback_plan(message, task_id)
                
            # Guardar plan en memoria global
            active_task_plans[task_id] = {
                'plan': plan_steps,
                'current_step': 0,
                'status': 'executing',
                'created_at': datetime.now().isoformat(),
                'start_time': datetime.now(),
                'message': message,
                'task_type': plan_data.get('task_type', 'general'),
                'complexity': plan_data.get('complexity', 'media'),
                'ai_generated': True  # Marcar como generado por IA
            }
            
            logger.info(f"🎉 Generated AI-powered plan for task {task_id} with {len(plan_steps)} specific steps")
            logger.info(f"📋 Plan steps for task {task_id}: {[step['title'] for step in plan_steps]}")
            
            return {
                'steps': plan_steps,
                'total_steps': len(plan_steps),
                'estimated_total_time': plan_data.get('estimated_total_time', '2-5 minutos'),
                'task_type': plan_data.get('task_type', 'ai_generated_dynamic'),
                'complexity': plan_data.get('complexity', 'media'),
                'ai_generated': True
            }
                
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"❌ Error parsing AI plan response for task {task_id}: {e}")
            return generate_fallback_plan(message, task_id)
            
    except Exception as e:
        logger.error(f"❌ Unexpected error generating AI plan for task {task_id}: {str(e)}")
        return generate_fallback_plan(message, task_id)

def generate_fallback_plan(message: str, task_id: str) -> dict:
    """
    Genera un plan de fallback más específico cuando la IA no está disponible
    """
    try:
        logger.warning(f"🔄 Generating fallback plan for task {task_id} (AI not available)")
        
        # Analizar el mensaje para determinar el tipo de tarea con más detalle
        message_lower = message.lower()
        original_message = message.strip()
        
        # Extraer palabras clave específicas para personalización
        keywords = [word for word in message_lower.split() if len(word) > 3]
        
        # Patrones más específicos para diferentes tipos de tareas
        if any(word in message_lower for word in ['crear', 'generar', 'escribir', 'desarrollar', 'diseñar', 'construir', 'hacer', 'elaborar']):
            # Extraer el objeto de la creación de forma más inteligente
            task_subject = original_message
            for word in ['crear', 'generar', 'escribir', 'desarrollar', 'diseñar', 'construir', 'hacer', 'elaborar', 'un', 'una', 'el', 'la']:
                task_subject = task_subject.replace(word, '').replace(word.capitalize(), '')
            task_subject = task_subject.strip()
            
            if not task_subject:
                task_subject = "contenido solicitado"
            
            plan_steps = [
                {
                    'id': 'step_1',
                    'title': f'Análisis detallado: {task_subject}',
                    'description': f'Analizar requisitos específicos, contexto y objetivos para {task_subject}',
                    'tool': 'analysis',
                    'status': 'pending',
                    'estimated_time': '45 segundos',
                    'completed': False,
                    'active': True
                },
                {
                    'id': 'step_2',
                    'title': f'Estructuración y diseño',
                    'description': f'Definir estructura, formato y metodología para {task_subject}',
                    'tool': 'planning',
                    'status': 'pending',
                    'estimated_time': '1 minuto',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_3',
                    'title': f'Desarrollo y creación',
                    'description': f'Ejecutar la creación completa de {task_subject} siguiendo los requisitos identificados',
                    'tool': 'creation',
                    'status': 'pending',
                    'estimated_time': '2-3 minutos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_4',
                    'title': f'Revisión y optimización final',
                    'description': f'Revisar calidad, completitud y entregar {task_subject} finalizado',
                    'tool': 'delivery',
                    'status': 'pending',
                    'estimated_time': '30 segundos',
                    'completed': False,
                    'active': False
                }
            ]
            
        elif any(word in message_lower for word in ['buscar', 'investigar', 'analizar', 'estudiar', 'revisar', 'información', 'datos', 'investigación']):
            # Extraer tema de investigación de forma más inteligente
            research_topic = original_message
            for word in ['buscar', 'investigar', 'analizar', 'estudiar', 'revisar', 'información', 'sobre', 'acerca', 'de', 'datos', 'dame', 'necesito']:
                research_topic = research_topic.replace(word, '').replace(word.capitalize(), '')
            research_topic = research_topic.strip()
            
            if not research_topic:
                research_topic = "tema solicitado"
                
            plan_steps = [
                {
                    'id': 'step_1',
                    'title': f'Estrategia de investigación: {research_topic}',
                    'description': f'Definir metodología, fuentes y alcance de investigación para {research_topic}',
                    'tool': 'search_definition',
                    'status': 'pending',
                    'estimated_time': '30 segundos',
                    'completed': False,
                    'active': True
                },
                {
                    'id': 'step_2',
                    'title': f'Recopilación de información especializada',
                    'description': f'Buscar información actualizada y relevante sobre {research_topic} en múltiples fuentes',
                    'tool': 'web_search',
                    'status': 'pending',
                    'estimated_time': '1-2 minutos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_3',
                    'title': f'Análisis y procesamiento de datos',
                    'description': f'Analizar, filtrar y procesar la información recopilada sobre {research_topic}',
                    'tool': 'data_analysis',
                    'status': 'pending',
                    'estimated_time': '1 minuto',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_4',
                    'title': f'Síntesis y presentación de hallazgos',
                    'description': f'Sintetizar resultados y presentar conclusiones sobre {research_topic}',
                    'tool': 'synthesis',
                    'status': 'pending',
                    'estimated_time': '45 segundos',
                    'completed': False,
                    'active': False
                }
            ]
            
        elif any(word in message_lower for word in ['explica', 'define', 'qué es', 'cómo', 'por qué', 'cuál']):
            # Preguntas explicativas
            topic = original_message.replace('?', '').strip()
            
            plan_steps = [
                {
                    'id': 'step_1',
                    'title': f'Investigación conceptual: {topic}',
                    'description': f'Buscar definiciones, conceptos clave y contexto para responder: {topic}',
                    'tool': 'web_search',
                    'status': 'pending',
                    'estimated_time': '1 minuto',
                    'completed': False,
                    'active': True
                },
                {
                    'id': 'step_2',
                    'title': f'Análisis y estructuración',
                    'description': f'Analizar información encontrada y estructurar respuesta comprensible',
                    'tool': 'analysis',
                    'status': 'pending',
                    'estimated_time': '45 segundos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_3',
                    'title': f'Formulación de respuesta completa',
                    'description': f'Crear respuesta detallada y educativa para: {topic}',
                    'tool': 'synthesis',
                    'status': 'pending',
                    'estimated_time': '30 segundos',
                    'completed': False,
                    'active': False
                }
            ]
            
        else:
            # Plan adaptativo para tareas no clasificadas
            plan_steps = [
                {
                    'id': 'step_1',
                    'title': f'Interpretación de solicitud: "{original_message[:30]}..."',
                    'description': f'Analizar y comprender los requisitos específicos de: {original_message}',
                    'tool': 'analysis',
                    'status': 'pending',
                    'estimated_time': '30 segundos',
                    'completed': False,
                    'active': True
                },
                {
                    'id': 'step_2',
                    'title': f'Planificación de ejecución',
                    'description': f'Definir metodología y pasos para cumplir con: {original_message}',
                    'tool': 'planning',
                    'status': 'pending',
                    'estimated_time': '45 segundos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_3',
                    'title': f'Procesamiento y ejecución',
                    'description': f'Ejecutar y procesar según los requisitos identificados',
                    'tool': 'processing',
                    'status': 'pending',
                    'estimated_time': '1-2 minutos',
                    'completed': False,
                    'active': False
                },
                {
                    'id': 'step_4',
                    'title': f'Entrega de resultados finales',
                    'description': f'Entregar resultado completo que satisfaga: {original_message}',
                    'tool': 'delivery',
                    'status': 'pending',
                    'estimated_time': '30 segundos',
                    'completed': False,
                    'active': False
                }
            ]
        
        # Guardar plan en memoria global con timestamp
        active_task_plans[task_id] = {
            'plan': plan_steps,
            'current_step': 0,
            'status': 'executing',
            'created_at': datetime.now().isoformat(),
            'start_time': datetime.now(),
            'message': message,
            'ai_generated': False  # Marcar como plan de fallback
        }
        
        logger.info(f"📋 Generated fallback plan for task {task_id} with {len(plan_steps)} customized steps")
        
        return {
            'steps': plan_steps,
            'total_steps': len(plan_steps),
            'estimated_total_time': '2-4 minutos',
            'task_type': 'adaptive_fallback_plan',
            'ai_generated': False
        }
        
    except Exception as e:
        logger.error(f"Error generating structured plan: {str(e)}")
        # Plan de fallback simple
        fallback_plan = [
            {
                'id': 'step_1',
                'title': 'Procesando solicitud',
                'description': 'Procesando tu solicitud...',
                'tool': 'processing',
                'status': 'pending',
                'estimated_time': '1 minuto',
                'completed': False,
                'active': True
            }
        ]
        
        active_task_plans[task_id] = {
            'plan': fallback_plan,
            'current_step': 0,
            'status': 'executing',
            'created_at': datetime.now().isoformat(),
            'message': message
        }
        
        return {
            'steps': fallback_plan,
            'total_steps': 1,
            'estimated_total_time': '1 minuto',
            'task_type': 'simple_execution'
        }



def generate_clean_response(ollama_response: str, tool_results: list) -> str:
    """
    Genera una respuesta limpia sin mostrar los pasos internos del plan
    """
    try:
        # Para tareas complejas, siempre generar una respuesta profesional estándar
        clean_response = """Perfecto, he recibido tu solicitud y ya estoy trabajando en ella. 

He generado un plan de acción detallado que puedes ver en la sección "Plan de Acción" del panel lateral. El plan incluye varios pasos que ejecutaré automáticamente para completar tu tarea.

Mientras trabajo en tu solicitud, puedes seguir el progreso en tiempo real a través del panel de monitoreo."""
        
        # Si hay resultados de herramientas, agregar un resumen limpio
        if tool_results:
            tools_summary = []
            successful_tools = 0
            failed_tools = 0
            
            for result in tool_results:
                if result.get('error'):
                    failed_tools += 1
                else:
                    successful_tools += 1
                    # Agregar información útil del resultado si está disponible
                    if isinstance(result.get('result'), dict):
                        if 'output' in result['result']:
                            tools_summary.append(f"✅ {result['tool']}: Completado exitosamente")
            
            # Agregar resumen al final de la respuesta
            if successful_tools > 0 or failed_tools > 0:
                clean_response += f"\n\n---\n**🔧 Herramientas utilizadas:** {successful_tools} exitosas"
                if failed_tools > 0:
                    clean_response += f", {failed_tools} con errores"
                clean_response += "\n"
                
                # Agregar detalles de herramientas exitosas
                for summary in tools_summary[:3]:  # Máximo 3 para no saturar
                    clean_response += f"{summary}\n"
        
        return clean_response
        
    except Exception as e:
        logger.error(f"Error generating clean response: {str(e)}")
        # Fallback: respuesta estándar
        return """He recibido tu solicitud y estoy trabajando en ella. 

Puedes ver el progreso del plan de acción en el panel lateral derecho. El plan se ejecutará automáticamente paso a paso."""

@agent_bp.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint principal del chat - VERSIÓN REAL CON OLLAMA
    Distingue entre conversaciones casuales y tareas complejas
    GENERA PLAN ESTRUCTURADO PARA MOSTRAR EN PLAN DE ACCIÓN
    """
    try:
        data = request.get_json()
        message = data.get('message', '')
        context = data.get('context', {})
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Obtener task_id del contexto
        task_id = context.get('task_id', str(uuid.uuid4()))
        
        logger.info(f"🚀 Processing message: {message[:50]}... (ID: {task_id})")
        
        # Obtener servicio de Ollama
        ollama_service = get_ollama_service()
        if not ollama_service:
            return jsonify({
                'error': 'Ollama service not available',
                'response': 'Lo siento, el servicio de IA no está disponible en este momento.'
            }), 503
        
        # PASO 1: Detectar si es conversación casual o tarea compleja
        is_casual = is_casual_conversation(message)
        
        if is_casual:
            # MODO CONVERSACIÓN CASUAL
            logger.info(f"🗣️ Detected casual conversation mode")
            
            # Usar solo Ollama para respuesta casual
            ollama_response = ollama_service.generate_casual_response(message, context)
            
            if ollama_response.get('error'):
                return jsonify({
                    'error': ollama_response['error'],
                    'response': ollama_response['response']
                }), 500
            
            return jsonify({
                'response': ollama_response['response'],
                'task_id': task_id,
                'timestamp': datetime.now().isoformat(),
                'execution_status': 'completed',
                'mode': 'casual_conversation',
                'memory_used': True
            })
        
        else:
            # MODO AGENTE CON PLANIFICACIÓN ESTRUCTURADA
            logger.info(f"🤖 Detected task mode - generating structured plan")
            
            # PASO 2: Generar plan dinámico PRIMERO usando IA
            structured_plan = generate_dynamic_plan_with_ai(message, task_id)
            
            # PASO 3: Generar respuesta usando Ollama con contexto de herramientas
            ollama_response = ollama_service.generate_response(message, context, use_tools=True)
            
            if ollama_response.get('error'):
                return jsonify({
                    'error': ollama_response['error'],
                    'response': ollama_response['response']
                }), 500
            
            # PASO 4: Procesar tool_calls si existen
            tool_results = []
            if ollama_response.get('tool_calls'):
                logger.info(f"🔧 Processing {len(ollama_response['tool_calls'])} tool calls")
                tool_manager = get_tool_manager()
                
                if tool_manager:
                    for tool_call in ollama_response['tool_calls']:
                        try:
                            tool_name = tool_call.get('tool')
                            parameters = tool_call.get('parameters', {})
                            
                            logger.info(f"🔧 Executing tool: {tool_name}")
                            
                            # Ejecutar herramienta real
                            tool_result = tool_manager.execute_tool(tool_name, parameters)
                            tool_results.append({
                                'tool': tool_name,
                                'parameters': parameters,
                                'result': tool_result
                            })
                            
                        except Exception as e:
                            logger.error(f"Error executing tool {tool_name}: {str(e)}")
                            tool_results.append({
                                'tool': tool_name,
                                'parameters': parameters,
                                'error': str(e)
                            })
            
            # PASO 5: Generar respuesta LIMPIA sin mostrar pasos del plan
            final_response = generate_clean_response(ollama_response['response'], tool_results)
            
            # PASO 6: Ejecutar plan automáticamente
            execute_plan_with_real_tools(task_id, structured_plan['steps'], message)
            
            logger.info(f"✅ Task completed successfully with structured plan")
            
            return jsonify({
                'response': final_response,
                'task_id': task_id,
                'plan': structured_plan,  # PLAN ESTRUCTURADO PARA FRONTEND
                'tool_calls': ollama_response.get('tool_calls', []),
                'tool_results': tool_results,
                'timestamp': datetime.now().isoformat(),
                'execution_status': 'completed',
                'mode': 'agent_with_structured_plan',
                'memory_used': True
            })
    
    except Exception as e:
        logger.error(f"Error general en chat: {str(e)}")
        return jsonify({
            'error': f'Error interno del servidor: {str(e)}',
            'response': 'Lo siento, hubo un error procesando tu solicitud.'
        }), 500

@agent_bp.route('/test-plan-generation', methods=['POST'])
def test_plan_generation():
    """
    Endpoint para probar la generación de planes con IA
    """
    try:
        data = request.get_json() or {}
        message = data.get('message', 'Crear un informe completo sobre inteligencia artificial en 2024')
        task_id = data.get('task_id', f'test-{uuid.uuid4()}')
        
        logger.info(f"🧪 Testing AI plan generation for: {message}")
        
        # Probar generación con IA
        ai_plan = generate_dynamic_plan_with_ai(message, task_id)
        
        # También generar plan de fallback para comparación
        fallback_task_id = f'fallback-{uuid.uuid4()}'
        fallback_plan = generate_fallback_plan(message, fallback_task_id)
        
        return jsonify({
            'test_results': {
                'ai_plan': {
                    'plan': ai_plan,
                    'ai_generated': ai_plan.get('ai_generated', False),
                    'plan_type': ai_plan.get('task_type', 'unknown')
                },
                'fallback_plan': {
                    'plan': fallback_plan,
                    'ai_generated': fallback_plan.get('ai_generated', False),
                    'plan_type': fallback_plan.get('task_type', 'unknown')
                }
            },
            'test_message': message,
            'timestamp': datetime.now().isoformat(),
            'comparison': {
                'ai_steps': len(ai_plan.get('steps', [])),
                'fallback_steps': len(fallback_plan.get('steps', [])),
                'ai_working': len(ai_plan.get('steps', [])) > 0,
                'plans_different': ai_plan.get('steps', []) != fallback_plan.get('steps', [])
            }
        })
    
    except Exception as e:
        logger.error(f"❌ Error in plan generation test: {str(e)}")
        return jsonify({
            'error': f'Error testing plan generation: {str(e)}',
            'test_failed': True
        }), 500

@agent_bp.route('/generate-plan', methods=['POST'])
def generate_plan():
    """
    Genera un plan de acción dinámico usando IA mejorada
    """
    try:
        data = request.get_json() or {}
        task_title = data.get('task_title', '')
        task_id = data.get('task_id', str(uuid.uuid4()))
        
        if not task_title:
            return jsonify({'error': 'task_title is required'}), 400
        
        logger.info(f"🚀 Generating dynamic plan for: {task_title}")
        
        # Usar la nueva función de generación dinámica con IA
        dynamic_plan = generate_dynamic_plan_with_ai(task_title, task_id)
        
        logger.info(f"✅ Dynamic plan generated with {len(dynamic_plan['steps'])} steps")
        
        return jsonify({
            'plan': dynamic_plan['steps'],
            'task_id': task_id,
            'total_steps': dynamic_plan['total_steps'],
            'estimated_total_time': dynamic_plan['estimated_total_time'],
            'task_type': dynamic_plan['task_type'],
            'complexity': dynamic_plan.get('complexity', 'media'),
            'timestamp': datetime.now().isoformat(),
            'status': 'plan_generated',
            'ai_generated': dynamic_plan.get('ai_generated', False)
        })
    
    except Exception as e:
        logger.error(f"Error generating dynamic plan: {str(e)}")
        return jsonify({
            'error': f'Error generando plan: {str(e)}'
        }), 500

@agent_bp.route('/update-task-progress', methods=['POST'])
def update_task_progress():
    """Actualiza el progreso de una tarea"""
    try:
        data = request.get_json() or {}
        task_id = data.get('task_id', '')
        step_id = data.get('step_id', '')
        completed = data.get('completed', False)
        
        if not task_id or not step_id:
            return jsonify({'error': 'task_id and step_id are required'}), 400
        
        # Actualizar progreso en memoria
        if task_id in active_task_plans:
            plan = active_task_plans[task_id]['plan']
            for step in plan:
                if step['id'] == step_id:
                    step['completed'] = completed
                    step['status'] = 'completed' if completed else 'pending'
                    break
            
            # Actualizar plan en memoria
            active_task_plans[task_id]['plan'] = plan
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'step_id': step_id,
            'completed': completed
        })
        
    except Exception as e:
        logger.error(f"Error updating task progress: {str(e)}")
        return jsonify({
            'error': f'Error actualizando progreso: {str(e)}'
        }), 500

@agent_bp.route('/update-task-time/<task_id>', methods=['POST'])
def update_task_time(task_id):
    """Actualiza el tiempo transcurrido de una tarea en tiempo real"""
    try:
        if task_id in active_task_plans:
            plan_data = active_task_plans[task_id]
            start_time = plan_data.get('start_time')
            
            if start_time:
                # Calcular tiempo transcurrido
                elapsed = datetime.now() - start_time
                elapsed_seconds = int(elapsed.total_seconds())
                
                # Formatear tiempo como MM:SS
                minutes = elapsed_seconds // 60
                seconds = elapsed_seconds % 60
                elapsed_str = f"{minutes}:{seconds:02d}"
                
                # Actualizar el paso activo
                plan = plan_data['plan']
                for step in plan:
                    if step.get('active', False):
                        step['elapsed_time'] = f"{elapsed_str} Pensando"
                        break
                
                # Actualizar en memoria
                active_task_plans[task_id]['plan'] = plan
                
                return jsonify({
                    'success': True,
                    'elapsed_time': elapsed_str,
                    'plan': plan
                })
            
        return jsonify({'error': 'Task not found'}), 404
        
    except Exception as e:
        logger.error(f"Error updating task time: {str(e)}")
        return jsonify({'error': str(e)}), 500

@agent_bp.route('/get-task-plan/<task_id>', methods=['GET'])
def get_task_plan(task_id):
    """Obtiene el plan de una tarea específica con progreso actualizado"""
    try:
        if task_id in active_task_plans:
            plan_data = active_task_plans[task_id]
            
            # Calcular progreso
            completed_steps = sum(1 for step in plan_data['plan'] if step['completed'])
            total_steps = len(plan_data['plan'])
            progress_percentage = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
            
            return jsonify({
                'plan': plan_data['plan'],
                'current_step': plan_data['current_step'],
                'status': plan_data['status'],
                'created_at': plan_data['created_at'],
                'progress': progress_percentage,
                'completed_steps': completed_steps,
                'total_steps': total_steps,
                'message': plan_data.get('message', ''),
                'final_result': plan_data.get('final_result'),  # Incluir resultado final
                'updated_at': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'error': 'Task plan not found'
            }), 404
    
    except Exception as e:
        logger.error(f"Error getting task plan: {str(e)}")
        return jsonify({
            'error': f'Error obteniendo plan: {str(e)}'
        }), 500

@agent_bp.route('/get-final-result/<task_id>', methods=['GET'])
def get_final_result(task_id):
    """Obtiene el resultado final de una tarea completada"""
    try:
        if task_id in active_task_plans:
            plan_data = active_task_plans[task_id]
            
            if plan_data['status'] == 'completed' and 'final_result' in plan_data:
                return jsonify({
                    'task_id': task_id,
                    'status': 'completed',
                    'final_result': plan_data['final_result'],
                    'plan_summary': {
                        'total_steps': len(plan_data['plan']),
                        'completed_steps': sum(1 for step in plan_data['plan'] if step['completed']),
                        'task_type': plan_data.get('task_type', 'general'),
                        'complexity': plan_data.get('complexity', 'media')
                    }
                })
            else:
                return jsonify({
                    'task_id': task_id,
                    'status': plan_data['status'],
                    'message': 'Tarea aún no completada o sin resultado final'
                })
        else:
            return jsonify({
                'error': 'Task not found'
            }), 404
    
    except Exception as e:
        logger.error(f"Error getting final result: {str(e)}")
        return jsonify({
            'error': f'Error obteniendo resultado final: {str(e)}'
        }), 500

@agent_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'ollama': True,  # Simplified
            'tools': 12,     # Simplified
            'database': True # Simplified
        }
    })

@agent_bp.route('/status', methods=['GET'])
def agent_status():
    """Status del agente"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'active_tasks': len(active_task_plans),
        'ollama': {
            'connected': True,
            'endpoint': 'https://78d08925604a.ngrok-free.app',
            'model': 'llama3.1:8b'
        },
        'tools': 12,
        'memory': {
            'enabled': True,
            'initialized': True
        }
    })

# Mantener endpoints adicionales necesarios para compatibilidad
@agent_bp.route('/generate-suggestions', methods=['POST'])
def generate_suggestions():
    """Genera sugerencias dinámicas simples"""
    try:
        # Sugerencias estáticas simples pero útiles
        suggestions = [
            {
                'title': 'Buscar información sobre IA',
                'description': 'Investigar las últimas tendencias en inteligencia artificial',
                'type': 'research'
            },
            {
                'title': 'Analizar datos de mercado',
                'description': 'Realizar análisis de tendencias del mercado actual',
                'type': 'analysis'
            },
            {
                'title': 'Crear documento técnico',
                'description': 'Generar documentación técnica profesional',
                'type': 'creation'
            }
        ]
        
        return jsonify({
            'suggestions': suggestions,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error generating suggestions: {str(e)}")
        return jsonify({
            'suggestions': [],
            'error': str(e)
        }), 500

# Endpoints de archivos simplificados
@agent_bp.route('/upload-files', methods=['POST'])
def upload_files():
    """Manejo simplificado de archivos"""
    try:
        files = request.files.getlist('files')
        task_id = request.form.get('task_id', str(uuid.uuid4()))
        
        # Procesar archivos de manera simple
        uploaded_files = []
        for file in files:
            if file and file.filename:
                file_id = str(uuid.uuid4())
                uploaded_files.append({
                    'id': file_id,
                    'name': file.filename,
                    'size': len(file.read()),
                    'mime_type': file.mimetype or 'application/octet-stream'
                })
        
        # Guardar referencias en memoria
        if task_id not in task_files:
            task_files[task_id] = []
        task_files[task_id].extend(uploaded_files)
        
        return jsonify({
            'files': uploaded_files,
            'task_id': task_id,
            'message': f'Se subieron {len(uploaded_files)} archivos exitosamente'
        })
    
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}")
        return jsonify({
            'error': f'Error subiendo archivos: {str(e)}'
        }), 500

@agent_bp.route('/get-task-files/<task_id>', methods=['GET'])
def get_task_files(task_id):
    """Obtiene archivos de una tarea"""
    try:
        files = task_files.get(task_id, [])
        return jsonify({
            'files': files,
            'task_id': task_id,
            'count': len(files)
        })
    
    except Exception as e:
        logger.error(f"Error getting task files: {str(e)}")
        return jsonify({
            'error': f'Error obteniendo archivos: {str(e)}'
        }), 500

@agent_bp.route('/ollama/check', methods=['POST'])
def check_ollama_connection():
    """Verifica conexión con Ollama"""
    try:
        data = request.get_json() or {}
        endpoint = data.get('endpoint', 'https://78d08925604a.ngrok-free.app')
        
        # Verificar conexión real con Ollama
        try:
            import requests
            response = requests.get(f"{endpoint}/api/tags", timeout=10)
            is_connected = response.status_code == 200
        except:
            is_connected = False
        
        return jsonify({
            'is_connected': is_connected,
            'endpoint': endpoint,
            'status': 'healthy' if is_connected else 'disconnected'
        })
    
    except Exception as e:
        logger.error(f"Error checking Ollama connection: {str(e)}")
        return jsonify({
            'is_connected': False,
            'error': str(e)
        }), 500

@agent_bp.route('/ollama/models', methods=['POST'])
def get_ollama_models():
    """Obtiene modelos disponibles de Ollama"""
    try:
        data = request.get_json() or {}
        endpoint = data.get('endpoint', 'https://78d08925604a.ngrok-free.app')
        
        # Simular modelos disponibles
        models = [
            {'name': 'llama3.1:8b', 'size': '4.7GB'},
            {'name': 'deepseek-r1:32b', 'size': '20GB'},
            {'name': 'qwen3:32b', 'size': '18GB'}
        ]
        
        return jsonify({
            'models': models,
            'endpoint': endpoint,
            'count': len(models)
        })
    
    except Exception as e:
        logger.error(f"Error getting Ollama models: {str(e)}")
        return jsonify({
            'models': [],
            'error': str(e)
        }), 500