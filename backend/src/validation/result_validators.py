"""
Result Validators - Sistema de Validación de Resultados por Herramienta
PROBLEMA 2: Implementación de validación rigurosa de resultados antes de marcar como exitoso
+ CORRECCIÓN CRÍTICA: Validación de relevancia temática
"""

import os
import logging
import re
from typing import Dict, Tuple, Any, List
import json

logger = logging.getLogger(__name__)

def extract_key_terms_from_query(query: str) -> List[str]:
    """
    🎯 NUEVA FUNCIÓN: Extraer términos clave de la consulta original para validación de relevancia
    
    Args:
        query: Query original de la tarea
        
    Returns:
        Lista de términos clave que deberían aparecer en el contenido
    """
    if not query:
        return []
    
    # Extraer términos importantes
    key_terms = []
    
    # 1. Nombres propios y entidades importantes
    proper_nouns = re.findall(r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\b', query)
    key_terms.extend([noun.lower() for noun in proper_nouns])
    
    # 2. Productos, marcas y tecnologías específicas
    tech_terms = re.findall(r'\b(?:iphone|android|tesla|apple|google|microsoft|bitcoin|blockchain)\b', query, re.IGNORECASE)
    key_terms.extend([term.lower() for term in tech_terms])
    
    # 3. Palabras significativas de 4+ caracteres que no sean meta
    meta_words = {'buscar', 'información', 'sobre', 'utilizar', 'herramienta', 'análisis', 'crear', 'generar', 'obtener', 'datos'}
    significant_words = re.findall(r'\b[a-záéíóúñA-ZÁÉÍÓÚÑ]{4,}\b', query)
    for word in significant_words:
        word_lower = word.lower()
        if word_lower not in meta_words and len(word_lower) >= 4:
            key_terms.append(word_lower)
    
    # 4. Números de modelo y versiones
    model_numbers = re.findall(r'\b\w*\d+\w*\b', query)
    key_terms.extend([model for model in model_numbers if len(model) > 1])
    
    # Eliminar duplicados manteniendo orden
    unique_terms = []
    seen = set()
    for term in key_terms:
        if term not in seen and len(term) > 2:
            seen.add(term)
            unique_terms.append(term)
    
    return unique_terms[:8]  # Máximo 8 términos más relevantes

def check_content_relevance(content: str, original_query: str, step_title: str = "") -> Tuple[bool, float, str]:
    """
    🎯 NUEVA FUNCIÓN: Verificar si el contenido es relevante a la consulta original
    
    Args:
        content: Contenido recopilado por la herramienta
        original_query: Query original de la tarea 
        step_title: Título del paso (opcional)
        
    Returns:
        Tuple[bool, float, str]: (es_relevante, puntuación_relevancia, mensaje_detalle)
    """
    if not content or not original_query:
        return False, 0.0, "Contenido o query vacío"
    
    # Extraer términos clave del query original
    key_terms = extract_key_terms_from_query(original_query)
    
    if not key_terms:
        return True, 0.5, "No se pudieron extraer términos clave, asumiendo relevancia"
    
    content_lower = content.lower()
    found_terms = []
    
    # Verificar cuántos términos clave aparecen en el contenido
    for term in key_terms:
        if term in content_lower:
            found_terms.append(term)
    
    # Calcular puntuación de relevancia
    relevance_score = len(found_terms) / len(key_terms) if key_terms else 0.0
    
    # Determinar si es relevante
    is_relevant = relevance_score >= 0.3  # Al menos 30% de términos clave deben aparecer
    
    # Mensaje detallado
    if is_relevant:
        detail_msg = f"Contenido relevante: {len(found_terms)}/{len(key_terms)} términos clave encontrados ({relevance_score:.1%}). Términos: {', '.join(found_terms[:5])}"
    else:
        detail_msg = f"Contenido NO relevante: solo {len(found_terms)}/{len(key_terms)} términos clave encontrados ({relevance_score:.1%}). Esperados: {', '.join(key_terms[:5])}"
    
    return is_relevant, relevance_score, detail_msg

def validate_web_search_result(result: dict, original_query: str = "", step_title: str = "") -> Tuple[str, str]:
    """
    Valida el resultado de una búsqueda web CON VALIDACIÓN DE RELEVANCIA.
    
    Args:
        result: Resultado de la búsqueda web
        original_query: Query original de la tarea (NUEVO)
        step_title: Título del paso (NUEVO)
    
    Returns:
        Tuple[str, str]: (estado, mensaje)
        Estados: 'success', 'warning', 'failure'
    """
    try:
        if not result or not isinstance(result, dict):
            return 'failure', 'Resultado de búsqueda inválido o nulo.'
        
        # Verificar que no haya errores explícitos
        if result.get('error'):
            return 'failure', f'Error en búsqueda: {result["error"]}'
        
        # CORREGIDO: Verificar tanto estructura nueva como legacy
        search_results = result.get('search_results', [])
        results_count = result.get('results_count', 0) 
        content = result.get('content', '')
        data = result.get('data', {})
        
        # Obtener contenido para validar (múltiples fuentes posibles)
        content_to_validate = content
        if not content_to_validate and data:
            if isinstance(data, dict):
                # Buscar contenido en diferentes estructuras
                content_to_validate = data.get('content', '')
                if not content_to_validate and 'results' in data:
                    results = data.get('results', [])
                    if results and isinstance(results, list):
                        # Combinar snippets de resultados
                        snippets = [r.get('snippet', '') for r in results if isinstance(r, dict)]
                        content_to_validate = ' '.join(snippets)
        
        # Si results_count es 0 y no hay content real, es un fallo
        if results_count == 0 and not content_to_validate.strip():
            return 'failure', 'La búsqueda no arrojó resultados reales. El sistema reportó éxito pero no recopiló información.'
        
        # Si data está vacío y content está vacío, es un fallo
        if not data and not content_to_validate.strip():
            return 'failure', 'La búsqueda no recopiló información real. Datos y contenido están vacíos.'
        
        # Verificar el contenido si existe
        if content_to_validate and len(content_to_validate.strip()) < 50:
            return 'warning', 'La búsqueda recopiló muy poca información (menos de 50 caracteres).'
        
        # 🚀 NUEVA VALIDACIÓN CRÍTICA: Verificar relevancia del contenido
        if original_query and content_to_validate:
            is_relevant, relevance_score, relevance_detail = check_content_relevance(
                content_to_validate, original_query, step_title
            )
            
            if not is_relevant:
                return 'failure', f'CONTENIDO NO RELEVANTE: {relevance_detail}. La búsqueda no encontró información relacionada con la tarea solicitada.'
            elif relevance_score < 0.5:
                return 'warning', f'CONTENIDO PARCIALMENTE RELEVANTE: {relevance_detail}. Puede necesitar búsquedas adicionales.'
        
        # Verificar search_results si existen (estructura legacy)
        if search_results:
            valid_results = 0
            for res in search_results:
                if isinstance(res, dict) and all(k in res for k in ['title', 'link']):
                    valid_results += 1
            
            if valid_results == 0:
                return 'failure', 'Los resultados de búsqueda no tienen formato válido.'
            
            success_msg = f'Búsqueda exitosa, {valid_results} resultados válidos encontrados.'
            if original_query:
                success_msg += f' Contenido relevante verificado para: "{original_query[:50]}..."'
            
            return 'success', success_msg
        
        # Si llegamos aquí, verificamos si tenemos contenido real
        if content_to_validate and len(content_to_validate.strip()) >= 50:
            success_msg = f'Búsqueda completada con contenido válido ({len(content_to_validate)} caracteres).'
            if original_query:
                success_msg += f' Relevancia verificada para: "{original_query[:50]}..."'
            return 'success', success_msg
        
        # Si no hay resultados válidos en ningún formato
        return 'failure', 'La búsqueda no produjo resultados válidos en ningún formato esperado.'
        
    except Exception as e:
        logger.error(f"Error validating web search result: {str(e)}")
        return 'failure', f'Error en validación de búsqueda: {str(e)}'

def validate_file_creation_result(result: dict) -> Tuple[str, str]:
    """
    Valida el resultado de una creación de archivo.
    
    Args:
        result: Resultado de la creación de archivo
    
    Returns:
        Tuple[str, str]: (estado, mensaje)
    """
    try:
        if not result or not isinstance(result, dict):
            return 'failure', 'Resultado de creación de archivo inválido o nulo.'
        
        # Verificar que se indica que se creó archivo
        if not result.get('file_created', False):
            return 'failure', 'No se indica que se haya creado archivo.'
        
        file_path = result.get('file_path')
        if not file_path:
            return 'failure', 'No se proporcionó la ruta del archivo creado.'
        
        # Verificar existencia física del archivo
        if not os.path.exists(file_path):
            return 'failure', f'El archivo no fue encontrado en la ruta especificada: {file_path}'
        
        # Verificar tamaño del archivo
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return 'warning', f'El archivo fue creado pero está vacío: {file_path}'
        
        # Verificar que el tamaño reportado coincida con el real
        reported_size = result.get('file_size', 0)
        if reported_size != file_size:
            return 'warning', f'Discrepancia en tamaño de archivo: reportado {reported_size}, real {file_size}'
        
        # Validar contenido mínimo
        if file_size < 50:  # Menos de 50 bytes es muy poco para ser útil
            return 'warning', f'El archivo es muy pequeño ({file_size} bytes), puede tener contenido insuficiente.'
        
        # Verificar que tenga download_url
        if not result.get('download_url'):
            return 'warning', 'Archivo creado pero sin URL de descarga.'
        
        return 'success', f'Archivo creado y validado exitosamente: {result.get("file_name")} ({file_size} bytes)'
        
    except Exception as e:
        logger.error(f"Error validating file creation result: {str(e)}")
        return 'failure', f'Error en validación de archivo: {str(e)}'

def validate_ollama_analysis_result(result: dict) -> Tuple[str, str]:
    """
    Valida el resultado de un análisis de Ollama.
    
    Args:
        result: Resultado del análisis de Ollama
    
    Returns:
        Tuple[str, str]: (estado, mensaje)
    """
    try:
        if not result or not isinstance(result, dict):
            return 'failure', 'Resultado de análisis inválido o nulo.'
        
        # Verificar que no haya errores explícitos
        if result.get('error'):
            return 'failure', f'Error en análisis: {result["error"]}'
        
        # CORREGIDO: Verificar tanto 'response' como 'content' (estructura real)
        content = result.get('response', '') or result.get('content', '')
        
        if not content:
            return 'failure', 'El análisis no generó contenido real. Campo response y content están vacíos.'
        
        # Verificar longitud mínima de contenido
        if len(content.strip()) < 50:
            return 'failure', 'El análisis generado es muy corto (menos de 50 caracteres). No constituye un análisis real.'
        
        # Verificar que no sea solo texto genérico o de error
        error_indicators = [
            'no puedo', 'cannot', 'unable to', 'error', 'problema',
            'disculpa', 'sorry', 'lo siento', 'no es posible', 'paso completado',
            'generic', 'genérico', 'no hay información'
        ]
        
        content_lower = content.lower()
        error_count = sum(1 for indicator in error_indicators if indicator in content_lower)
        
        if error_count > 2:  # Demasiadas palabras de error
            return 'failure', 'El análisis de Ollama indica errores, falta de capacidad o es demasiado genérico.'
        
        # Verificar que no sea solo "Paso completado" u otro texto genérico
        generic_phrases = ['paso completado', 'task completed', 'generic response', 'default response']
        if any(phrase in content_lower for phrase in generic_phrases):
            return 'failure', 'El análisis es solo un mensaje genérico, no contiene análisis real.'
        
        # Verificar que tenga estructura de análisis (párrafos, puntos, etc.)
        has_structure = any([
            '\n\n' in content,  # Párrafos
            '1.' in content or '2.' in content,  # Listas numeradas
            '•' in content or '-' in content,  # Listas con viñetas
            '**' in content or '*' in content,  # Texto con formato
        ])
        
        if not has_structure and len(content) < 200:
            return 'warning', 'El análisis parece carecer de estructura detallada.'
        
        return 'success', f'Análisis generado y validado exitosamente ({len(content)} caracteres).'
        
    except Exception as e:
        logger.error(f"Error validating Ollama analysis result: {str(e)}")
        return 'failure', f'Error en validación de análisis: {str(e)}'

def validate_planning_result(result: dict) -> Tuple[str, str]:
    """
    Valida el resultado de una planificación.
    
    Args:
        result: Resultado de la planificación
    
    Returns:
        Tuple[str, str]: (estado, mensaje)
    """
    try:
        if not result or not isinstance(result, dict):
            return 'failure', 'Resultado de planificación inválido o nulo.'
        
        # Verificar que no haya errores explícitos
        if result.get('error'):
            return 'failure', f'Error en planificación: {result["error"]}'
        
        content = result.get('response', '')
        if not content:
            return 'failure', 'La planificación no generó contenido.'
        
        # Verificar longitud mínima para un plan útil
        if len(content.strip()) < 100:
            return 'warning', 'El plan generado es muy corto (menos de 100 caracteres).'
        
        # Verificar elementos típicos de un plan
        plan_indicators = [
            'objetivo', 'meta', 'paso', 'estrategia', 'cronograma',
            'recurso', 'timeline', 'plan', 'fase', 'etapa'
        ]
        
        content_lower = content.lower()
        plan_elements = sum(1 for indicator in plan_indicators if indicator in content_lower)
        
        if plan_elements < 2:
            return 'warning', 'El plan no parece contener elementos estructurales típicos de planificación.'
        
        return 'success', f'Plan generado y validado exitosamente ({len(content)} caracteres, {plan_elements} elementos de planificación detectados).'
        
    except Exception as e:
        logger.error(f"Error validating planning result: {str(e)}")
        return 'failure', f'Error en validación de planificación: {str(e)}'

def validate_delivery_result(result: dict) -> Tuple[str, str]:
    """
    Valida el resultado de una entrega final.
    
    Args:
        result: Resultado de la entrega
    
    Returns:
        Tuple[str, str]: (estado, mensaje)
    """
    try:
        if not result or not isinstance(result, dict):
            return 'failure', 'Resultado de entrega inválido o nulo.'
        
        # Para entregas, aplicar validación de archivo si se creó uno
        if result.get('file_created', False):
            file_validation = validate_file_creation_result(result)
            if file_validation[0] == 'failure':
                return file_validation
        
        # Verificar que tenga resumen ejecutivo
        if not result.get('executive_summary', False):
            return 'warning', 'La entrega no incluye resumen ejecutivo marcado.'
        
        # Verificar contenido del resumen
        content = result.get('content', '')
        if len(content.strip()) < 200:
            return 'warning', 'El resumen ejecutivo es muy corto (menos de 200 caracteres).'
        
        # Verificar elementos de resumen ejecutivo
        executive_elements = [
            'resumen ejecutivo', 'objetivos', 'resultados', 'conclusiones',
            'deliverables', 'hallazgos', 'recomendaciones'
        ]
        
        content_lower = content.lower()
        executive_count = sum(1 for element in executive_elements if element in content_lower)
        
        if executive_count < 3:
            return 'warning', 'El resumen ejecutivo no parece tener estructura completa.'
        
        return 'success', f'Entrega final validada exitosamente con resumen ejecutivo completo.'
        
    except Exception as e:
        logger.error(f"Error validating delivery result: {str(e)}")
        return 'failure', f'Error en validación de entrega: {str(e)}'

def validate_generic_processing_result(result: dict) -> Tuple[str, str]:
    """
    Valida el resultado de procesamiento genérico.
    
    Args:
        result: Resultado del procesamiento genérico
    
    Returns:
        Tuple[str, str]: (estado, mensaje)
    """
    try:
        if not result or not isinstance(result, dict):
            return 'failure', 'Resultado de procesamiento inválido o nulo.'
        
        # Verificar que no haya errores explícitos
        if result.get('error'):
            return 'failure', f'Error en procesamiento: {result["error"]}'
        
        content = result.get('response', '')
        if not content:
            return 'failure', 'El procesamiento no generó contenido.'
        
        # Para procesamiento genérico, validar contenido mínimo
        if len(content.strip()) < 30:
            return 'warning', 'El resultado del procesamiento es muy corto.'
        
        return 'success', f'Procesamiento genérico completado exitosamente ({len(content)} caracteres).'
        
    except Exception as e:
        logger.error(f"Error validating generic processing result: {str(e)}")
        return 'failure', f'Error en validación de procesamiento: {str(e)}'

# Mapeo de herramientas a sus validadores
RESULT_VALIDATORS = {
    'web_search': validate_web_search_result,
    'creation': validate_file_creation_result,
    'delivery': validate_delivery_result,
    'analysis': validate_ollama_analysis_result,
    'planning': validate_planning_result,
    'processing': validate_generic_processing_result,
    'synthesis': validate_ollama_analysis_result,  # Reutilizable
    'search_definition': validate_ollama_analysis_result,  # Reutilizable
    'data_analysis': validate_ollama_analysis_result,  # Reutilizable
    'generic': validate_generic_processing_result
}

def validate_step_result(tool_name: str, result: dict, original_query: str = "", step_title: str = "") -> Tuple[str, str]:
    """
    Valida el resultado de un paso usando el validador apropiado CON VALIDACIÓN DE RELEVANCIA MEJORADA.
    
    Args:
        tool_name: Nombre de la herramienta/paso
        result: Resultado a validar
        original_query: Query original de la tarea (NUEVO - opcional para compatibilidad)
        step_title: Título del paso (NUEVO - opcional para compatibilidad)
    
    Returns:
        Tuple[str, str]: (estado, mensaje) donde estado es 'success', 'warning', o 'failure'
    """
    try:
        # 🚀 VALIDACIÓN ESPECIAL PARA WEB_SEARCH CON RELEVANCIA
        if tool_name == 'web_search' and original_query:
            return validate_web_search_result(result, original_query, step_title)
        elif tool_name == 'web_search':
            # Fallback sin query original
            return validate_web_search_result(result)
        
        # Para otras herramientas, usar validador específico
        validator = RESULT_VALIDATORS.get(tool_name)
        if validator:
            return validator(result)
        else:
            # Fallback a validador genérico
            logger.warning(f"No specific validator for tool '{tool_name}', using generic validator")
            return validate_generic_processing_result(result)
            
    except Exception as e:
        logger.error(f"Error in step result validation for tool '{tool_name}': {str(e)}")
        return 'failure', f'Error en validación: {str(e)}'

# Definición de estados granulares
class StepStatus:
    PENDING = 'pending'
    IN_PROGRESS = 'in-progress'
    COMPLETED_SUCCESS = 'completed_success'
    COMPLETED_WITH_WARNINGS = 'completed_with_warnings'
    FAILED = 'failed'
    SKIPPED = 'skipped'

class TaskStatus:
    PLAN_GENERATED = 'plan_generated'
    EXECUTING = 'executing'
    COMPLETED_SUCCESS = 'completed_success'
    COMPLETED_WITH_WARNINGS = 'completed_with_warnings'
    FAILED = 'failed'

def determine_task_status_from_steps(steps: list) -> str:
    """
    Determina el estado final de la tarea basado en los estados de sus pasos.
    
    Args:
        steps: Lista de pasos con sus estados
    
    Returns:
        str: Estado final de la tarea
    """
    try:
        if not steps:
            return TaskStatus.FAILED
        
        step_statuses = [step.get('status', StepStatus.PENDING) for step in steps]
        
        # Si algún paso crítico falló, la tarea falló
        failed_steps = [s for s in step_statuses if s == StepStatus.FAILED]
        if failed_steps:
            return TaskStatus.FAILED
        
        # Si todos son exitosos, la tarea es exitosa
        success_steps = [s for s in step_statuses if s == StepStatus.COMPLETED_SUCCESS]
        warning_steps = [s for s in step_statuses if s == StepStatus.COMPLETED_WITH_WARNINGS]
        
        if len(success_steps) == len(steps):
            return TaskStatus.COMPLETED_SUCCESS
        
        if len(success_steps) + len(warning_steps) == len(steps):
            return TaskStatus.COMPLETED_WITH_WARNINGS
        
        # Si hay pasos pendientes o en progreso, la tarea está ejecutándose
        pending_or_progress = [s for s in step_statuses if s in [StepStatus.PENDING, StepStatus.IN_PROGRESS]]
        if pending_or_progress:
            return TaskStatus.EXECUTING
        
        # Por defecto, si no encaja en otras categorías
        return TaskStatus.COMPLETED_WITH_WARNINGS
        
    except Exception as e:
        logger.error(f"Error determining task status from steps: {str(e)}")
        return TaskStatus.FAILED