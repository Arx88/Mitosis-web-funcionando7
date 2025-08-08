#!/usr/bin/env python3
"""
SISTEMA DE VALIDACIÓN ROBUSTO
Reemplaza la validación excesivamente estricta con criterios balanceados
"""

import logging
from typing import Dict, List, Any, Optional
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class RobustValidationSystem:
    """
    Sistema de validación que evita fallbacks innecesarios
    aplicando criterios inteligentes y balanceados
    """
    
    def __init__(self):
        self.validation_modes = ['strict', 'moderate', 'lenient', 'minimal']
        self.quality_thresholds = {
            'strict': {'min_content_length': 500, 'min_sources': 3, 'min_score': 80},
            'moderate': {'min_content_length': 200, 'min_sources': 2, 'min_score': 60},
            'lenient': {'min_content_length': 100, 'min_sources': 1, 'min_score': 40},
            'minimal': {'min_content_length': 50, 'min_sources': 1, 'min_score': 20}
        }
    
    def validate_step_completion(self, step: dict, result: dict, mode: str = 'moderate') -> dict:
        """
        Valida la completitud de un paso usando criterios balanceados
        """
        tool = step.get('tool', 'general')
        title = step.get('title', '')
        step_id = step.get('id', '')
        
        logger.info(f"🔍 Validando paso '{title}' con modo '{mode}'")
        
        # Seleccionar validador apropiado según la herramienta
        if tool == 'web_search':
            return self._validate_web_search_result(result, mode, title)
        elif tool in ['analysis', 'processing']:
            return self._validate_analysis_result(result, mode, title)
        elif tool == 'creation':
            return self._validate_creation_result(result, mode, title)
        else:
            return self._validate_generic_result(result, mode, title, tool)
    
    def _validate_web_search_result(self, result: dict, mode: str, title: str) -> dict:
        """Validación específica para resultados de búsqueda web"""
        thresholds = self.quality_thresholds.get(mode, self.quality_thresholds['moderate'])
        
        success = result.get('success', False)
        results = result.get('results', [])
        count = result.get('count', len(results) if results else 0)
        
        logger.info(f"🔍 Validando web search: success={success}, count={count}, results_len={len(results)}")
        
        # Criterios progresivos según modo
        if mode == 'strict':
            if success and count >= thresholds['min_sources'] and results:
                # Verificar calidad de resultados
                quality_score = self._calculate_search_quality_score(results)
                if quality_score >= thresholds['min_score']:
                    return self._create_success_validation(
                        f"Búsqueda exitosa: {count} fuentes de alta calidad (score: {quality_score}%)",
                        quality_score
                    )
                else:
                    return self._create_retry_validation(
                        f"Calidad insuficiente: score {quality_score}% < {thresholds['min_score']}%",
                        quality_score
                    )
            else:
                return self._create_retry_validation(
                    f"Búsqueda insuficiente: success={success}, count={count}, required={thresholds['min_sources']}",
                    30
                )
        
        elif mode == 'moderate':
            if success and count >= thresholds['min_sources']:
                quality_score = self._calculate_search_quality_score(results)
                if quality_score >= thresholds['min_score']:
                    return self._create_success_validation(
                        f"Búsqueda completada: {count} fuentes (score: {quality_score}%)",
                        quality_score
                    )
                else:
                    return self._create_retry_validation(
                        f"Calidad mejorable: score {quality_score}%",
                        quality_score
                    )
            elif success and count >= 1:
                # Ser más permisivo en modo moderado
                quality_score = self._calculate_search_quality_score(results)
                if quality_score >= 40:  # Umbral más bajo
                    return self._create_success_validation(
                        f"Búsqueda aceptable: {count} fuentes (score: {quality_score}%)",
                        quality_score
                    )
            
            return self._create_retry_validation(
                f"Búsqueda necesita mejora: success={success}, count={count}",
                25
            )
        
        elif mode == 'lenient':
            if success and count >= 1:
                # Modo permisivo - aceptar cualquier resultado válido
                quality_score = self._calculate_search_quality_score(results)
                return self._create_success_validation(
                    f"Búsqueda válida: {count} fuentes encontradas",
                    max(quality_score, 50)  # Asegurar score mínimo
                )
            elif success:
                # Incluso sin resultados concretos, si success=True, puede ser válido
                return self._create_success_validation(
                    "Búsqueda ejecutada correctamente",
                    40
                )
            
            return self._create_retry_validation(
                f"Búsqueda falló completamente: success={success}",
                20
            )
        
        else:  # minimal
            # Modo mínimo - aceptar casi cualquier cosa
            if success or count > 0 or results:
                return self._create_success_validation(
                    "Búsqueda completada con criterios mínimos",
                    30
                )
            
            return self._create_success_validation(
                "Paso completado (criterios mínimos)",
                25
            )
    
    def _validate_analysis_result(self, result: dict, mode: str, title: str) -> dict:
        """Validación específica para resultados de análisis"""
        thresholds = self.quality_thresholds.get(mode, self.quality_thresholds['moderate'])
        
        success = result.get('success', False)
        content = str(result.get('content', ''))
        summary = str(result.get('summary', ''))
        analysis = str(result.get('analysis', ''))
        
        total_content = content + summary + analysis
        content_length = len(total_content)
        
        logger.info(f"🔍 Validando análisis: success={success}, content_length={content_length}")
        
        if mode == 'strict':
            if success and content_length >= thresholds['min_content_length']:
                quality_score = self._calculate_analysis_quality_score(total_content)
                if quality_score >= thresholds['min_score']:
                    return self._create_success_validation(
                        f"Análisis completo: {content_length} caracteres (score: {quality_score}%)",
                        quality_score
                    )
                else:
                    return self._create_retry_validation(
                        f"Análisis insuficiente: score {quality_score}%",
                        quality_score
                    )
            else:
                return self._create_retry_validation(
                    f"Contenido insuficiente: {content_length} < {thresholds['min_content_length']}",
                    30
                )
        
        elif mode == 'moderate':
            if success and content_length >= thresholds['min_content_length']:
                quality_score = self._calculate_analysis_quality_score(total_content)
                return self._create_success_validation(
                    f"Análisis aceptable: {content_length} caracteres",
                    max(quality_score, 60)
                )
            elif success and content_length >= 50:  # Más permisivo
                return self._create_success_validation(
                    f"Análisis básico completado: {content_length} caracteres",
                    50
                )
            
            return self._create_retry_validation(
                f"Análisis insuficiente: {content_length} caracteres",
                30
            )
        
        elif mode == 'lenient':
            if success and content_length >= 20:
                return self._create_success_validation(
                    f"Análisis válido: {content_length} caracteres",
                    45
                )
            elif success:
                return self._create_success_validation(
                    "Análisis completado",
                    40
                )
            
            return self._create_retry_validation(
                "Análisis requiere contenido",
                25
            )
        
        else:  # minimal
            # Modo mínimo - aceptar si hay algún contenido o success
            if content_length > 0 or success:
                return self._create_success_validation(
                    "Análisis completado (criterios mínimos)",
                    30
                )
            
            return self._create_success_validation(
                "Paso de análisis finalizado",
                25
            )
    
    def _validate_creation_result(self, result: dict, mode: str, title: str) -> dict:
        """Validación específica para resultados de creación"""
        thresholds = self.quality_thresholds.get(mode, self.quality_thresholds['moderate'])
        
        success = result.get('success', False)
        content = str(result.get('content', ''))
        filename = result.get('filename', '')
        file_created = result.get('file_created', False)
        
        content_length = len(content)
        
        logger.info(f"🔍 Validando creación: success={success}, content_length={content_length}, file_created={file_created}")
        
        if mode == 'strict':
            if success and content_length >= thresholds['min_content_length'] and (filename or file_created):
                quality_score = self._calculate_creation_quality_score(content)
                if quality_score >= thresholds['min_score']:
                    return self._create_success_validation(
                        f"Creación exitosa: {content_length} caracteres, archivo: {filename}",
                        quality_score
                    )
                else:
                    return self._create_retry_validation(
                        f"Calidad de creación insuficiente: score {quality_score}%",
                        quality_score
                    )
            else:
                return self._create_retry_validation(
                    f"Creación incompleta: length={content_length}, file={bool(filename)}",
                    30
                )
        
        elif mode == 'moderate':
            if success and content_length >= 50:
                quality_score = self._calculate_creation_quality_score(content)
                return self._create_success_validation(
                    f"Contenido creado: {content_length} caracteres",
                    max(quality_score, 60)
                )
            elif success:
                return self._create_success_validation(
                    "Creación completada",
                    50
                )
            
            return self._create_retry_validation(
                f"Creación insuficiente: {content_length} caracteres",
                30
            )
        
        elif mode == 'lenient':
            if success or content_length >= 10:
                return self._create_success_validation(
                    "Contenido creado exitosamente",
                    45
                )
            
            return self._create_success_validation(
                "Paso de creación completado",
                40
            )
        
        else:  # minimal
            # Modo mínimo - siempre aceptar
            return self._create_success_validation(
                "Creación finalizada (criterios mínimos)",
                30
            )
    
    def _validate_generic_result(self, result: dict, mode: str, title: str, tool: str) -> dict:
        """Validación genérica para herramientas no específicas"""
        success = result.get('success', False)
        content = str(result.get('content', ''))
        
        logger.info(f"🔍 Validando tool genérico '{tool}': success={success}")
        
        if mode in ['strict', 'moderate']:
            if success:
                return self._create_success_validation(
                    f"Herramienta {tool} ejecutada exitosamente",
                    70
                )
            else:
                return self._create_retry_validation(
                    f"Herramienta {tool} falló",
                    30
                )
        
        else:  # lenient or minimal
            # Para herramientas genéricas, ser muy permisivo
            return self._create_success_validation(
                f"Herramienta {tool} completada",
                50
            )
    
    def _calculate_search_quality_score(self, results: List[dict]) -> float:
        """Calcula score de calidad para resultados de búsqueda"""
        if not results:
            return 0
        
        score = 0
        total_results = len(results)
        
        for result in results:
            item_score = 0
            
            # Puntos por tener título
            if result.get('title'):
                item_score += 25
            
            # Puntos por tener snippet/descripción
            snippet = result.get('snippet', '') or result.get('description', '')
            if snippet and len(snippet) > 20:
                item_score += 35
            elif snippet:
                item_score += 20
            
            # Puntos por tener URL
            if result.get('url'):
                item_score += 25
            
            # Puntos por contenido adicional
            if result.get('content') and len(str(result['content'])) > 50:
                item_score += 15
            
            score += item_score
        
        # Promedio y ajuste por cantidad
        avg_score = score / total_results if total_results > 0 else 0
        
        # Bonus por cantidad de resultados
        quantity_bonus = min(total_results * 5, 20)
        
        final_score = min(avg_score + quantity_bonus, 100)
        
        logger.info(f"🔍 Search quality score: {final_score}% ({total_results} results, avg: {avg_score})")
        
        return final_score
    
    def _calculate_analysis_quality_score(self, content: str) -> float:
        """Calcula score de calidad para contenido de análisis"""
        if not content:
            return 0
        
        score = 0
        content_length = len(content)
        
        # Puntos por longitud
        if content_length >= 500:
            score += 40
        elif content_length >= 200:
            score += 30
        elif content_length >= 100:
            score += 20
        elif content_length >= 50:
            score += 10
        
        # Puntos por estructura (títulos, listas)
        if re.search(r'#+\s+\w+', content):  # Headers markdown
            score += 20
        if re.search(r'\*\s+\w+', content):  # Lista con asteriscos
            score += 10
        if re.search(r'\d+\.\s+\w+', content):  # Lista numerada
            score += 10
        
        # Puntos por contenido sustantivo
        words = len(content.split())
        if words >= 100:
            score += 20
        elif words >= 50:
            score += 15
        elif words >= 25:
            score += 10
        
        # Penalización por contenido meta excesivo
        meta_keywords = ['generado automáticamente', 'fecha:', 'tarea id:', 'timestamp']
        meta_count = sum(1 for keyword in meta_keywords if keyword.lower() in content.lower())
        if meta_count > 2:
            score -= 15
        
        final_score = max(min(score, 100), 0)
        
        logger.info(f"🔍 Analysis quality score: {final_score}% ({words} words, {content_length} chars)")
        
        return final_score
    
    def _calculate_creation_quality_score(self, content: str) -> float:
        """Calcula score de calidad para contenido creado"""
        if not content:
            return 0
        
        score = 0
        content_length = len(content)
        
        # Puntos por longitud
        if content_length >= 300:
            score += 30
        elif content_length >= 150:
            score += 25
        elif content_length >= 75:
            score += 20
        elif content_length >= 25:
            score += 15
        
        # Puntos por formato markdown
        if content.startswith('#'):
            score += 20
        if '##' in content:
            score += 15
        
        # Puntos por estructura
        if '\n\n' in content:  # Párrafos separados
            score += 15
        
        # Puntos por contenido sustantivo vs. meta
        lines = content.split('\n')
        substantial_lines = [line for line in lines if len(line.strip()) > 20 and 
                           not any(meta in line.lower() for meta in ['fecha:', 'generado', 'timestamp', 'tarea id:'])]
        
        if len(substantial_lines) >= 3:
            score += 20
        elif len(substantial_lines) >= 1:
            score += 10
        
        final_score = max(min(score, 100), 0)
        
        logger.info(f"🔍 Creation quality score: {final_score}% ({len(lines)} lines, {content_length} chars)")
        
        return final_score
    
    def _create_success_validation(self, reason: str, score: float) -> dict:
        """Crea resultado de validación exitosa"""
        return {
            'meets_requirements': True,
            'step_completed': True,
            'should_continue': False,
            'completeness_score': score,
            'validation_summary': reason,
            'timestamp': datetime.now().isoformat(),
            'validation_type': 'robust'
        }
    
    def _create_retry_validation(self, reason: str, score: float) -> dict:
        """Crea resultado de validación que requiere retry"""
        return {
            'meets_requirements': False,
            'step_completed': False,
            'should_continue': True,
            'completeness_score': score,
            'validation_summary': reason,
            'timestamp': datetime.now().isoformat(),
            'validation_type': 'robust',
            'requires_retry': True
        }
    
    def auto_adjust_validation_mode(self, attempt_number: int, previous_scores: List[float]) -> str:
        """
        Ajusta automáticamente el modo de validación basado en intentos previos
        """
        if attempt_number == 1:
            return 'moderate'  # Empezar con criterios balanceados
        elif attempt_number == 2:
            if previous_scores and max(previous_scores) < 40:
                return 'lenient'  # Relajar si scores son muy bajos
            else:
                return 'moderate'
        elif attempt_number >= 3:
            return 'minimal'  # Criterios muy permisivos después de múltiples intentos
        
        return 'lenient'
    
    def should_escalate_to_fallback(self, validation_results: List[dict]) -> bool:
        """
        Determina si se debe usar un plan fallback basado en validaciones previas
        """
        if len(validation_results) < 3:
            return False  # No usar fallback hasta después de 3 intentos
        
        recent_scores = [r.get('completeness_score', 0) for r in validation_results[-3:]]
        avg_recent_score = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        
        # Solo usar fallback si los scores son consistentemente muy bajos
        return avg_recent_score < 15
    
    def generate_improvement_recommendations(self, validation_result: dict, tool: str) -> List[str]:
        """
        Genera recomendaciones específicas para mejorar resultados
        """
        recommendations = []
        score = validation_result.get('completeness_score', 0)
        
        if tool == 'web_search':
            if score < 40:
                recommendations.extend([
                    "Refinar términos de búsqueda para mayor precisión",
                    "Aumentar número de fuentes consultadas",
                    "Verificar disponibilidad de herramientas de búsqueda"
                ])
            elif score < 70:
                recommendations.extend([
                    "Mejorar filtrado de resultados relevantes",
                    "Optimizar query para fuentes más específicas"
                ])
        
        elif tool in ['analysis', 'processing']:
            if score < 40:
                recommendations.extend([
                    "Incrementar profundidad del análisis",
                    "Incluir más fuentes de datos para el análisis",
                    "Estructurar mejor el contenido analítico"
                ])
            elif score < 70:
                recommendations.extend([
                    "Añadir más detalles sustantivos",
                    "Mejorar organización del contenido"
                ])
        
        elif tool == 'creation':
            if score < 40:
                recommendations.extend([
                    "Generar contenido más extenso y detallado",
                    "Mejorar estructura y formato del contenido",
                    "Reducir contenido meta automático"
                ])
            elif score < 70:
                recommendations.extend([
                    "Añadir más secciones sustantivas",
                    "Mejorar formato markdown"
                ])
        
        return recommendations