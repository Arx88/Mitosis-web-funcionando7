"""
ENHANCED STEP VALIDATION SYSTEM - CORRECCIÓN CRÍTICA
Sistema mejorado para asegurar que Paso 1 recolecte información REAL de múltiples fuentes
"""

import re
import logging
from typing import Dict, List, Any, Set
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class EnhancedStepValidator:
    """
    🔥 VALIDADOR SUPER ESTRICTO PARA PASO 1 
    
    NO PERMITE AVANZAR hasta que se haya recolectado información REAL y SUSTANCIAL
    de MÚLTIPLES sitios web diferentes con contenido verificable
    """
    
    def __init__(self):
        self.required_sources_minimum = 3  # Mínimo 3 sitios diferentes
        self.minimum_content_per_source = 300  # Mínimo 300 chars por fuente
        self.total_content_minimum = 2000  # Mínimo 2000 chars total
        
        # Patrones específicos reforzados para información política
        self.critical_patterns = {
            'biografia_personal': {
                'patterns': [
                    r'\bnació\s+(en|el)', r'\bfecha\s+de\s+nacimiento', r'\bnacimiento',
                    r'\bedad\s+de\s+\d+', r'\baños', r'\bformación\s+académica', 
                    r'\buniversidad', r'\bestudios', r'\btítulo', r'\bcarrera',
                    r'\bfamilia', r'\bpadres', r'\besposa', r'\bhijos',
                    r'\binfancia', r'\borígenes', r'\bprimer\s+trabajo'
                ],
                'required_indicators': ['datos personales verificables', 'fechas específicas', 'formación'],
                'weight': 25
            },
            'trayectoria_politica_detallada': {
                'patterns': [
                    r'\bcargo\s+político', r'\bdiputado', r'\bsenador', r'\bministro',
                    r'\bpresidente', r'\bcandidato', r'\belección\s+\d{4}',
                    r'\bpartido\s+político', r'\bmovimiento\s+político', r'\bfuerza\s+política',
                    r'\bcampaña\s+electoral', r'\bvotación', r'\bpropuesta\s+política',
                    r'\bgobierno\s+de', r'\badministración\s+de'
                ],
                'required_indicators': ['cargos específicos', 'fechas de elecciones', 'partidos políticos'],
                'weight': 25
            },
            'ideologia_especifica': {
                'patterns': [
                    r'\bliberal\s+económico', r'\bconservador\s+social', r'\blibertario',
                    r'\bderecha\s+política', r'\bcentro\s+derecha', r'\bizquierda',
                    r'\bposición\s+ideológica', r'\bprincipios\s+políticos', r'\bvisión\s+económica',
                    r'\bpolíticas\s+públicas', r'\bmodelo\s+económico', r'\bestado\s+mínimo'
                ],
                'required_indicators': ['posición ideológica clara', 'principios específicos'],
                'weight': 20
            },
            'declaraciones_recientes': {
                'patterns': [
                    r'\bdeclaró\s+(que|ayer|hoy)', r'\bafirmó\s+en', r'\bmanifestó\s+que',
                    r'\bentrevista\s+(con|en)', r'\brueda\s+de\s+prensa', r'\bdiscurso\s+en',
                    r'\bconferencia\s+de\s+prensa', r'\bmedio\s+de\s+comunicación',
                    r'\bperiodista', r'\bopinión\s+sobre', r'\bpostura\s+ante'
                ],
                'required_indicators': ['declaraciones literales', 'contexto específico'],
                'weight': 15
            },
            'cobertura_mediatica': {
                'patterns': [
                    r'\bnoticia\s+(sobre|de)', r'\bmedio\s+publicó', r'\bdiario\s+[A-Z]',
                    r'\bcanal\s+de\s+televisión', r'\bperiódico', r'\brevista',
                    r'\bcorrespondencia', r'\breportaje', r'\bcobertura\s+mediática'
                ],
                'required_indicators': ['fuentes periodísticas', 'medios específicos'],
                'weight': 15
            }
        }
        
        # Patrones que indican meta-contenido (PROHIBIDOS)
        self.forbidden_meta_patterns = [
            r'se\s+(realizará|procederá|analizará|evaluará|estudiará)',
            r'este\s+(análisis|documento|informe)\s+(se|tiene)',
            r'los\s+objetivos\s+(son|del\s+análisis)',
            r'la\s+metodología\s+(será|utilizada)',
            r'el\s+(siguiente\s+paso|proceso\s+de\s+análisis)',
            r'marco\s+(teórico|conceptual|de\s+referencia)',
            r'revisión\s+bibliográfica',
            r'el\s+presente\s+(estudio|trabajo|documento)',
            r'información\s+general\s+sobre',
            r'datos\s+básicos\s+(de|sobre)',
            r'introducción\s+al\s+tema'
        ]

    def validate_step_1_completion(self, step_description: str, step_title: str, 
                                   collected_results: List[Dict[str, Any]], 
                                   task_id: str) -> Dict[str, Any]:
        """
        🔥 VALIDACIÓN SUPER ESTRICTA PARA PASO 1
        
        NO permite avanzar hasta que haya información REAL de múltiples fuentes
        """
        try:
            logger.info(f"🔍 INICIANDO VALIDACIÓN SUPER ESTRICTA PARA PASO 1: {step_title}")
            
            # 1. ANÁLISIS DE FUENTES - Verificar múltiples sitios web
            sources_analysis = self._analyze_multiple_sources(collected_results)
            logger.info(f"📊 Fuentes analizadas: {sources_analysis['unique_sources']} sitios únicos")
            
            # 2. ANÁLISIS DE CONTENIDO - Verificar información real vs metadata
            content_analysis = self._analyze_real_content_quality(collected_results)
            logger.info(f"📝 Contenido real: {content_analysis['total_real_content']} caracteres")
            
            # 3. VALIDACIÓN DE PATRONES CRÍTICOS - Verificar elementos específicos
            pattern_validation = self._validate_critical_patterns(collected_results)
            logger.info(f"🎯 Patrones encontrados: {len(pattern_validation['found_patterns'])} de {len(self.critical_patterns)}")
            
            # 4. DETECCIÓN DE META-CONTENIDO - Rechazar contenido genérico
            meta_content_check = self._detect_forbidden_meta_content(collected_results)
            
            # 5. CÁLCULO DE SCORE FINAL
            final_score = self._calculate_comprehensive_score(
                sources_analysis, content_analysis, pattern_validation, meta_content_check
            )
            
            # 6. DECISIÓN ESTRICTA DE COMPLETITUD
            is_complete = self._make_strict_completion_decision(
                final_score, sources_analysis, content_analysis, pattern_validation, meta_content_check
            )
            
            # 7. GENERAR RECOMENDACIONES ESPECÍFICAS
            specific_recommendations = self._generate_targeted_search_recommendations(
                pattern_validation, sources_analysis, content_analysis
            )
            
            result = {
                'meets_requirements': is_complete,
                'completeness_score': final_score,
                'sources_analysis': sources_analysis,
                'content_analysis': content_analysis,
                'pattern_validation': pattern_validation,
                'meta_content_detected': meta_content_check['has_meta_content'],
                'validation_summary': self._generate_detailed_summary(
                    is_complete, final_score, sources_analysis, pattern_validation
                ),
                'specific_recommendations': specific_recommendations,
                'strict_requirements_status': {
                    'minimum_sources': sources_analysis['unique_sources'] >= self.required_sources_minimum,
                    'minimum_content': content_analysis['total_real_content'] >= self.total_content_minimum,
                    'no_meta_content': not meta_content_check['has_meta_content'],
                    'critical_patterns_found': len(pattern_validation['found_patterns']) >= 3
                },
                'timestamp': datetime.now().isoformat()
            }
            
            if is_complete:
                logger.info(f"✅ PASO 1 APROBADO - Score: {final_score}% - Fuentes: {sources_analysis['unique_sources']}")
            else:
                logger.warning(f"❌ PASO 1 RECHAZADO - Score: {final_score}% - Requisitos no cumplidos")
                logger.warning(f"❌ Necesita más información específica de múltiples fuentes")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en validación estricta: {str(e)}")
            return {
                'meets_requirements': False,
                'completeness_score': 0,
                'error': str(e),
                'validation_summary': f'Error en validación: {str(e)}'
            }

    def _analyze_multiple_sources(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza si los resultados vienen de múltiples fuentes reales"""
        unique_domains = set()
        valid_sources = []
        
        for result in results:
            url = result.get('url', '')
            if url and url.startswith('http'):
                try:
                    domain = urlparse(url).netloc.lower()
                    if domain and 'bing.com' not in domain:  # Excluir páginas de búsqueda
                        unique_domains.add(domain)
                        valid_sources.append({
                            'domain': domain,
                            'url': url,
                            'title': result.get('title', ''),
                            'content_length': len(result.get('snippet', '') or result.get('content', ''))
                        })
                except:
                    pass
        
        return {
            'unique_sources': len(unique_domains),
            'total_results': len(results),
            'valid_sources': valid_sources,
            'domains': list(unique_domains),
            'meets_minimum': len(unique_domains) >= self.required_sources_minimum,
            'sources_with_substantial_content': len([s for s in valid_sources if s['content_length'] > 200])
        }

    def _analyze_real_content_quality(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza la calidad del contenido real recolectado"""
        total_content = ""
        content_pieces = []
        
        for result in results:
            content = result.get('snippet', '') or result.get('content', '') or result.get('description', '')
            if content and len(content.strip()) > 50:
                total_content += f" {content}"
                content_pieces.append({
                    'length': len(content),
                    'preview': content[:100] + "..." if len(content) > 100 else content,
                    'source': result.get('url', 'unknown')
                })
        
        # Análisis de indicadores de contenido real
        real_data_indicators = [
            r'\d{4}',  # Años (2023, 2024, etc)
            r'\d+\s*años',  # Edades
            r'nació\s+en',  # Datos biográficos
            r'presidente\s+de',  # Cargos específicos
            r'declaró\s+que',  # Declaraciones
            r'según\s+fuentes',  # Referencias
            r'en\s+una\s+entrevista',  # Contexto específico
            r'candidato\s+a',  # Posiciones políticas
        ]
        
        real_indicators_found = []
        for pattern in real_data_indicators:
            matches = re.findall(pattern, total_content.lower())
            if matches:
                real_indicators_found.extend(matches[:3])  # Máximo 3 por patrón
        
        return {
            'total_real_content': len(total_content),
            'content_pieces_count': len(content_pieces),
            'content_pieces': content_pieces[:5],  # Mostrar solo primeros 5
            'real_indicators_found': len(real_indicators_found),
            'real_indicators_examples': real_indicators_found[:10],
            'meets_minimum_content': len(total_content) >= self.total_content_minimum,
            'average_content_per_piece': len(total_content) // max(len(content_pieces), 1)
        }

    def _validate_critical_patterns(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Valida patrones críticos específicos para información política"""
        all_content = ""
        for result in results:
            content = result.get('snippet', '') or result.get('content', '') or result.get('description', '')
            if content:
                all_content += f" {content}"
        
        all_content_lower = all_content.lower()
        found_patterns = {}
        total_weight = 0
        found_weight = 0
        
        for pattern_name, config in self.critical_patterns.items():
            patterns = config['patterns']
            weight = config['weight']
            total_weight += weight
            
            matches = []
            for pattern in patterns:
                pattern_matches = re.findall(pattern, all_content_lower)
                matches.extend(pattern_matches)
            
            if matches:
                found_patterns[pattern_name] = {
                    'matches_count': len(matches),
                    'evidence': matches[:3],  # Primeros 3 matches como evidencia
                    'weight': weight,
                    'quality': 'high' if len(matches) >= 3 else 'medium' if len(matches) >= 2 else 'low'
                }
                found_weight += weight
            else:
                found_patterns[pattern_name] = {
                    'matches_count': 0,
                    'evidence': [],
                    'weight': weight,
                    'quality': 'none'
                }
        
        pattern_coverage = (found_weight / total_weight * 100) if total_weight > 0 else 0
        
        return {
            'found_patterns': {k: v for k, v in found_patterns.items() if v['matches_count'] > 0},
            'missing_patterns': {k: v for k, v in found_patterns.items() if v['matches_count'] == 0},
            'pattern_coverage_score': int(pattern_coverage),
            'total_patterns_available': len(self.critical_patterns),
            'patterns_found_count': len([p for p in found_patterns.values() if p['matches_count'] > 0]),
            'high_quality_patterns': len([p for p in found_patterns.values() if p['quality'] == 'high'])
        }

    def _detect_forbidden_meta_content(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detecta contenido meta-genérico que debe ser rechazado"""
        all_content = ""
        for result in results:
            content = result.get('snippet', '') or result.get('content', '') or result.get('description', '')
            if content:
                all_content += f" {content}"
        
        all_content_lower = all_content.lower()
        meta_patterns_found = []
        
        for pattern in self.forbidden_meta_patterns:
            matches = re.findall(pattern, all_content_lower)
            if matches:
                meta_patterns_found.extend([{
                    'pattern': pattern,
                    'matches': matches[:2]  # Primeros 2 matches
                }])
        
        has_meta_content = len(meta_patterns_found) > 0
        
        if has_meta_content:
            logger.warning(f"🚫 META-CONTENIDO DETECTADO: {len(meta_patterns_found)} patrones prohibidos encontrados")
        
        return {
            'has_meta_content': has_meta_content,
            'meta_patterns_found': meta_patterns_found,
            'meta_patterns_count': len(meta_patterns_found)
        }

    def _calculate_comprehensive_score(self, sources_analysis: Dict, content_analysis: Dict, 
                                     pattern_validation: Dict, meta_content_check: Dict) -> int:
        """Calcula score comprehensivo basado en múltiples factores"""
        score = 0
        
        # 1. Score por fuentes múltiples (25 puntos)
        sources_score = min(25, (sources_analysis['unique_sources'] / self.required_sources_minimum) * 25)
        score += sources_score
        
        # 2. Score por contenido real (25 puntos)
        content_score = min(25, (content_analysis['total_real_content'] / self.total_content_minimum) * 25)
        score += content_score
        
        # 3. Score por patrones críticos encontrados (30 puntos)
        patterns_score = pattern_validation['pattern_coverage_score'] * 0.3
        score += patterns_score
        
        # 4. Score por indicadores de datos reales (20 puntos)
        real_data_score = min(20, content_analysis['real_indicators_found'] * 2)
        score += real_data_score
        
        # 5. Penalización severa por meta-contenido (-50 puntos)
        if meta_content_check['has_meta_content']:
            score -= 50
            logger.warning("🚫 PENALIZACIÓN APLICADA: -50 puntos por meta-contenido")
        
        return max(0, min(100, int(score)))

    def _make_strict_completion_decision(self, final_score: int, sources_analysis: Dict, 
                                       content_analysis: Dict, pattern_validation: Dict, 
                                       meta_content_check: Dict) -> bool:
        """Decisión estricta de si el paso está realmente completo"""
        
        # Criterios OBLIGATORIOS (todos deben cumplirse)
        mandatory_criteria = {
            'minimum_score': final_score >= 75,
            'minimum_sources': sources_analysis['unique_sources'] >= self.required_sources_minimum,
            'minimum_content': content_analysis['total_real_content'] >= self.total_content_minimum,
            'no_meta_content': not meta_content_check['has_meta_content'],
            'minimum_patterns': pattern_validation['patterns_found_count'] >= 3
        }
        
        # Log de cada criterio
        for criterion, meets in mandatory_criteria.items():
            status = "✅" if meets else "❌"
            logger.info(f"{status} {criterion}: {meets}")
        
        # TODOS los criterios deben cumplirse
        all_criteria_met = all(mandatory_criteria.values())
        
        if not all_criteria_met:
            failed_criteria = [criterion for criterion, meets in mandatory_criteria.items() if not meets]
            logger.warning(f"❌ Criterios no cumplidos: {failed_criteria}")
        
        return all_criteria_met

    def _generate_targeted_search_recommendations(self, pattern_validation: Dict, 
                                                sources_analysis: Dict, 
                                                content_analysis: Dict) -> List[str]:
        """Genera recomendaciones específicas basadas en elementos faltantes"""
        recommendations = []
        
        missing_patterns = pattern_validation.get('missing_patterns', {})
        
        for pattern_name, info in missing_patterns.items():
            if pattern_name == 'biografia_personal':
                recommendations.append(
                    "Buscar biografía específica: 'nombre completo fecha nacimiento lugar formación académica universidad carrera familia'"
                )
            elif pattern_name == 'trayectoria_politica_detallada':
                recommendations.append(
                    "Buscar trayectoria política: 'cargos específicos diputado senador ministro elecciones años partidos políticos gobierno'"
                )
            elif pattern_name == 'ideologia_especifica':
                recommendations.append(
                    "Buscar ideología política: 'posición ideológica liberal conservador principios políticos modelo económico estado'"
                )
            elif pattern_name == 'declaraciones_recientes':
                recommendations.append(
                    "Buscar declaraciones: 'entrevistas recientes rueda prensa declaraciones opiniones postura ante'"
                )
            elif pattern_name == 'cobertura_mediatica':
                recommendations.append(
                    "Buscar cobertura mediática: 'noticias diarios medios periodísticos reportajes cobertura prensa'"
                )
        
        # Si necesita más fuentes
        if sources_analysis['unique_sources'] < self.required_sources_minimum:
            recommendations.append(
                f"Buscar en {self.required_sources_minimum - sources_analysis['unique_sources']} fuentes adicionales: Wikipedia, biografías oficiales, medios argentinos específicos"
            )
        
        # Si necesita más contenido sustancial
        if content_analysis['total_real_content'] < self.total_content_minimum:
            recommendations.append(
                "Buscar fuentes con información más detallada: biografías completas, perfiles extensos, análisis en profundidad"
            )
        
        return recommendations[:5]  # Máximo 5 recomendaciones

    def _generate_detailed_summary(self, is_complete: bool, final_score: int, 
                                 sources_analysis: Dict, pattern_validation: Dict) -> str:
        """Genera un resumen detallado de la validación"""
        if is_complete:
            return (f"✅ PASO 1 COMPLETAMENTE APROBADO - Score: {final_score}% | "
                   f"Fuentes: {sources_analysis['unique_sources']} sitios únicos | "
                   f"Patrones: {pattern_validation['patterns_found_count']} elementos encontrados")
        else:
            return (f"❌ PASO 1 RECHAZADO - Score: {final_score}% | "
                   f"Fuentes: {sources_analysis['unique_sources']}/{self.required_sources_minimum} requeridas | "
                   f"Patrones: {pattern_validation['patterns_found_count']} de {len(self.critical_patterns)} elementos | "
                   f"NECESITA MÁS INFORMACIÓN ESPECÍFICA")

    def validate_final_content_quality(self, step_title: str, content: str, task_context: str = "") -> Dict[str, Any]:
        """
        🔥 VALIDACIÓN SUPER ESTRICTA PARA PASOS FINALES (creation, processing)
        
        Asegura que el contenido final sea REAL y específico, no metadata genérica
        """
        try:
            logger.info(f"🔍 INICIANDO VALIDACIÓN DE CONTENIDO FINAL: {step_title}")
            
            # 1. Detectar metadata genérica y frases prohibidas
            meta_content_detected = self._detect_forbidden_meta_content_in_text(content)
            
            # 2. Análizar calidad del contenido
            content_quality = self._analyze_final_content_quality(content, task_context)
            
            # 3. Verificar especificidad vs genericidad
            specificity_check = self._check_content_specificity(content, step_title)
            
            # 4. Calcular score final
            final_score = self._calculate_final_content_score(
                meta_content_detected, content_quality, specificity_check
            )
            
            # 5. Decisión de completitud
            is_acceptable = (
                not meta_content_detected['has_meta_content'] and
                content_quality['is_substantial'] and
                specificity_check['is_specific'] and
                final_score >= 70
            )
            
            result = {
                'meets_requirements': is_acceptable,
                'completeness_score': final_score,
                'meta_content_detected': meta_content_detected,
                'content_quality': content_quality,
                'specificity_check': specificity_check,
                'validation_summary': self._generate_final_content_summary(
                    is_acceptable, final_score, meta_content_detected, content_quality
                ),
                'recommendations': self._generate_content_improvement_recommendations(
                    meta_content_detected, content_quality, specificity_check
                ),
                'timestamp': datetime.now().isoformat()
            }
            
            if is_acceptable:
                logger.info(f"✅ CONTENIDO FINAL APROBADO - Score: {final_score}%")
            else:
                logger.warning(f"❌ CONTENIDO FINAL RECHAZADO - Score: {final_score}% - Contiene metadata genérica")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en validación de contenido final: {str(e)}")
            return {
                'meets_requirements': False,
                'completeness_score': 0,
                'error': str(e),
                'validation_summary': f'Error en validación: {str(e)}'
            }

    def _detect_forbidden_meta_content_in_text(self, content: str) -> Dict[str, Any]:
        """Detecta contenido meta genérico en texto final"""
        forbidden_phrases = [
            r'\bse realizará\b', r'\bse analizará\b', r'\bse estudiará\b',
            r'\bel presente\s+(estudio|análisis|trabajo|documento)\b',
            r'\bse llevará\s+a\s+cabo\b', r'\bse procederá\s+a\b',
            r'\ba continuación\s+se\b', r'\bse expondrá\b', r'\bse detallará\b',
            r'\bse mostrará\b', r'\bse presentará\b', r'\bse desarrollará\b',
            r'\bpróximamente\b', r'\ben\s+el\s+siguiente\s+(capítulo|apartado)\b',
            r'\bse incluirán?\b', r'\bse abordarán?\b', r'\bse tratarán?\b',
            r'\*Este\s+es\s+un\b', r'\*Esto\s+es\s+un\b',
            r'\bFecha:\s+\d{4}-\d{2}-\d{2}\b', r'\bGenerado\s+automáticamente\b'
        ]
        
        meta_phrases_found = []
        content_lower = content.lower()
        
        for pattern in forbidden_phrases:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            if matches:
                meta_phrases_found.extend(matches)
        
        return {
            'has_meta_content': len(meta_phrases_found) > 0,
            'meta_phrases_found': meta_phrases_found,
            'meta_phrase_count': len(meta_phrases_found)
        }

    def _analyze_final_content_quality(self, content: str, task_context: str = "") -> Dict[str, Any]:
        """Analiza la calidad del contenido final"""
        content_length = len(content.strip())
        
        # Contar elementos sustanciales
        sentences = len(re.findall(r'[.!?]+', content))
        paragraphs = len([p for p in content.split('\n\n') if p.strip()])
        specific_data = len(re.findall(r'\d+|[A-Z][a-z]+\s+[A-Z][a-z]+', content))  # Números o nombres propios
        
        return {
            'is_substantial': content_length >= 500 and sentences >= 5,
            'content_length': content_length,
            'sentence_count': sentences,
            'paragraph_count': paragraphs,
            'specific_data_count': specific_data,
            'has_real_information': specific_data >= 3
        }

    def _check_content_specificity(self, content: str, step_title: str) -> Dict[str, Any]:
        """Verifica que el contenido sea específico al tema solicitado"""
        # Extraer palabras clave del título
        title_keywords = re.findall(r'\b[a-záéíóú]{3,}\b', step_title.lower())
        
        # Contar cuántas palabras clave aparecen en el contenido
        content_lower = content.lower()
        keywords_found = [kw for kw in title_keywords if kw in content_lower]
        
        specificity_score = (len(keywords_found) / max(len(title_keywords), 1)) * 100
        
        return {
            'is_specific': specificity_score >= 50,
            'specificity_score': specificity_score,
            'title_keywords': title_keywords,
            'keywords_found': keywords_found,
            'keyword_coverage': len(keywords_found)
        }

    def _calculate_final_content_score(self, meta_content: Dict, content_quality: Dict, 
                                     specificity: Dict) -> int:
        """Calcula score final para contenido"""
        score = 100
        
        # Penalizaciones por metadata
        if meta_content['has_meta_content']:
            score -= 50  # Penalización severa por metadata
        
        # Penalizaciones por baja calidad
        if not content_quality['is_substantial']:
            score -= 30
        
        if not content_quality['has_real_information']:
            score -= 20
        
        # Penalizaciones por falta de especificidad
        if not specificity['is_specific']:
            score -= 25
        
        return max(0, score)

    def _generate_final_content_summary(self, is_acceptable: bool, score: int, 
                                      meta_content: Dict, content_quality: Dict) -> str:
        """Genera resumen de validación de contenido final"""
        if is_acceptable:
            return f"✅ CONTENIDO FINAL APROBADO - Score: {score}% - Sin metadata genérica, información específica presente"
        else:
            issues = []
            if meta_content['has_meta_content']:
                issues.append(f"metadata genérica detectada ({meta_content['meta_phrase_count']} frases)")
            if not content_quality['is_substantial']:
                issues.append(f"contenido insuficiente ({content_quality['content_length']} chars)")
            if not content_quality['has_real_information']:
                issues.append("falta información específica")
            
            return f"❌ CONTENIDO FINAL RECHAZADO - Score: {score}% - Problemas: {', '.join(issues)}"

    def _generate_content_improvement_recommendations(self, meta_content: Dict, 
                                                    content_quality: Dict, 
                                                    specificity: Dict) -> List[str]:
        """Genera recomendaciones específicas para mejorar el contenido"""
        recommendations = []
        
        if meta_content['has_meta_content']:
            recommendations.append(
                "Eliminar frases genéricas como 'se realizará', 'se analizará' y reemplazar con contenido específico"
            )
        
        if not content_quality['is_substantial']:
            recommendations.append(
                f"Expandir contenido a mínimo 500 caracteres (actual: {content_quality['content_length']})"
            )
        
        if not content_quality['has_real_information']:
            recommendations.append(
                "Incluir datos específicos: nombres, fechas, números, hechos concretos"
            )
        
        if not specificity['is_specific']:
            recommendations.append(
                f"Incluir más información específica sobre: {', '.join(specificity['title_keywords'][:3])}"
            )
        
        return recommendations[:3]  # Máximo 3 recomendaciones


# Función de wrapper para integración
def validate_step_1_with_enhanced_validator(step_description: str, step_title: str, 
                                          collected_results: List[Dict[str, Any]], 
                                          task_id: str) -> Dict[str, Any]:
    """
    🔥 FUNCIÓN PRINCIPAL DE VALIDACIÓN MEJORADA PARA PASO 1
    """
    validator = EnhancedStepValidator()
    return validator.validate_step_1_completion(step_description, step_title, collected_results, task_id)