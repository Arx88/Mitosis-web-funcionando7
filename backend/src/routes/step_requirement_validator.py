"""
Sistema de Validación de Completitud de Pasos
Valida que la información recolectada cumpla con los requisitos específicos del paso
"""

import re
import logging
from typing import Dict, List, Any, Set
from datetime import datetime

logger = logging.getLogger(__name__)

class StepRequirementValidator:
    """
    🎯 VALIDADOR INTELIGENTE DE COMPLETITUD DE PASOS
    
    Analiza si la información recolectada cumple con TODOS los requisitos específicos
    mencionados en la descripción del paso. NO permite avanzar hasta que esté completo.
    """
    
    def __init__(self):
        self.requirement_patterns = {
            # Patrones específicos para biografía política
            'biografia': {
                'patterns': [
                    r'\bbio\w*', r'\bnacimiento', r'\bnació', r'\bedad', r'\bfecha',
                    r'\bformación', r'\beducación', r'\buniversidad', r'\bcarrera',
                    r'\bfamilia', r'\besposa', r'\bhijos', r'\bpadres',
                    r'\binfancia', r'\bjuventud', r'\borgenes'
                ],
                'required_elements': ['datos personales', 'formación académica', 'historia personal']
            },
            'trayectoria_politica': {
                'patterns': [
                    r'\bpolítico', r'\bpolítica', r'\bcargos?', r'\bgobierno',
                    r'\bdiputado', r'\bsenador', r'\bministro', r'\bpresidente',
                    r'\bcandidato', r'\belecciones?', r'\bpartido',
                    r'\bcampaña', r'\btrayectoria', r'\bcarrera\s+política'
                ],
                'required_elements': ['cargos políticos', 'elecciones', 'historial político']
            },
            'ideologia': {
                'patterns': [
                    r'\bideolog\w+', r'\bconservador', r'\bliberal', r'\bprogresista',
                    r'\bderecha', r'\bizquierda', r'\bcentro', r'\bposición\s+política',
                    r'\bfilosofía\s+política', r'\bvalores', r'\bprincipios',
                    r'\bentendimiento\s+político', r'\bvisión\s+política'
                ],
                'required_elements': ['posición política', 'principios ideológicos', 'visión política']
            },
            'declaraciones_publicas': {
                'patterns': [
                    r'\bdeclar\w+', r'\bmanifestó', r'\bafirmó', r'\bdijo',
                    r'\bopinión', r'\bpostura', r'\bcomentarios?', r'\bpalabras',
                    r'\bentrevista', r'\bdiscurso', r'\brueda\s+de\s+prensa',
                    r'\bmedio\s+de\s+comunicación', r'\bperiodista'
                ],
                'required_elements': ['declaraciones recientes', 'entrevistas', 'posiciones públicas']
            },
            'noticias': {
                'patterns': [
                    r'\bnoticia', r'\bmedio\s+de\s+comunicación', r'\bperiódico',
                    r'\bdiario', r'\brevista', r'\bcanal', r'\btelevisión',
                    r'\bradio', r'\bobjetivo\s+de\s+prensa', r'\bcobertura'
                ],
                'required_elements': ['cobertura mediática', 'noticias recientes']
            },
            'entrevistas': {
                'patterns': [
                    r'\bentrevista', r'\bentrevistado', r'\bconversación',
                    r'\bdiálogo', r'\bcharla', r'\bprograma', r'\bmesa\s+redonda'
                ],
                'required_elements': ['entrevistas en medios', 'declaraciones directas']
            },
            'perfiles_academicos': {
                'patterns': [
                    r'\bacadémico', r'\buniversidad', r'\binvestigación',
                    r'\bestudio', r'\banálisis\s+académico', r'\bpublicación',
                    r'\bartículo\s+académico', r'\btesis', r'\bmonografía'
                ],
                'required_elements': ['estudios académicos', 'investigaciones']
            }
        }
    
    def validate_step_requirements(self, step_description: str, step_title: str, 
                                  collected_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        🔍 VALIDADOR PRINCIPAL DE COMPLETITUD
        
        Analiza si los datos recolectados cumplen con TODOS los requisitos del paso
        
        Args:
            step_description: Descripción completa del paso
            step_title: Título del paso
            collected_data: Lista de resultados/datos recolectados
            
        Returns:
            dict: Resultado de la validación con detalles específicos
        """
        try:
            logger.info(f"🔍 Iniciando validación de completitud para: {step_title}")
            
            # 1. Identificar requisitos específicos en la descripción
            required_elements = self._extract_required_elements(step_description, step_title)
            logger.info(f"📋 Elementos requeridos identificados: {list(required_elements.keys())}")
            
            # 2. Analizar contenido recolectado
            content_analysis = self._analyze_collected_content(collected_data)
            logger.info(f"📊 Contenido analizado: {content_analysis['total_chars']} caracteres de {len(collected_data)} fuentes")
            
            # 3. Verificar cobertura de cada elemento requerido
            coverage_results = self._verify_coverage(required_elements, content_analysis, collected_data)
            
            # 4. Calcular score de completitud
            completeness_score = self._calculate_completeness_score(coverage_results, required_elements)
            
            # 5. Determinar si cumple requisitos para avanzar
            meets_requirements = self._evaluate_final_completeness(
                completeness_score, coverage_results, required_elements
            )
            
            # 6. Generar recomendaciones específicas si no está completo
            recommendations = self._generate_specific_recommendations(
                coverage_results, required_elements, meets_requirements
            )
            
            result = {
                'meets_requirements': meets_requirements,
                'completeness_score': completeness_score,
                'required_elements': list(required_elements.keys()),
                'coverage_results': coverage_results,
                'content_analysis': content_analysis,
                'recommendations': recommendations,
                'validation_summary': self._generate_validation_summary(
                    meets_requirements, completeness_score, coverage_results
                ),
                'missing_elements': [elem for elem, result in coverage_results.items() 
                                   if not result['found']],
                'timestamp': datetime.now().isoformat()
            }
            
            if meets_requirements:
                logger.info(f"✅ VALIDACIÓN EXITOSA - Completitud: {completeness_score}%")
            else:
                logger.warning(f"❌ VALIDACIÓN FALLIDA - Completitud: {completeness_score}% - Faltan elementos")
                logger.warning(f"❌ Elementos faltantes: {result['missing_elements']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en validación de completitud: {str(e)}")
            return {
                'meets_requirements': False,
                'completeness_score': 0,
                'error': str(e),
                'validation_summary': f'Error en validación: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _extract_required_elements(self, description: str, title: str) -> Dict[str, Dict]:
        """Extrae elementos específicamente requeridos de la descripción del paso"""
        combined_text = f"{title} {description}".lower()
        required_elements = {}
        
        # Buscar patrones específicos en la descripción
        for element_type, config in self.requirement_patterns.items():
            patterns = config['patterns']
            
            # Si algún patrón coincide, este elemento es requerido
            if any(re.search(pattern, combined_text) for pattern in patterns):
                required_elements[element_type] = {
                    'patterns': config['patterns'],
                    'required_elements': config['required_elements'],
                    'priority': 'high' if element_type in ['biografia', 'trayectoria_politica'] else 'medium'
                }
        
        # Si no encuentra elementos específicos, buscar términos generales
        if not required_elements:
            general_info_patterns = [
                r'\binformación', r'\bdatos', r'\bdetalles', r'\banálisis',
                r'\brecopilar', r'\bbuscar', r'\bencontrar'
            ]
            if any(re.search(pattern, combined_text) for pattern in general_info_patterns):
                required_elements['informacion_general'] = {
                    'patterns': general_info_patterns,
                    'required_elements': ['información básica', 'datos relevantes'],
                    'priority': 'medium'
                }
        
        return required_elements
    
    def _analyze_collected_content(self, collected_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza el contenido recolectado para extraer información útil"""
        analysis = {
            'total_sources': len(collected_data),
            'total_chars': 0,
            'content_by_type': {},
            'urls_analyzed': [],
            'content_snippets': [],
            'has_substantial_content': False
        }
        
        for item in collected_data:
            # Extraer contenido de diferentes formatos
            content = ""
            if isinstance(item, dict):
                content = (item.get('content', '') or 
                          item.get('snippet', '') or 
                          item.get('description', '') or 
                          item.get('title', '') or 
                          str(item.get('text', '')))
                
                # Registrar URL si existe
                if 'url' in item:
                    analysis['urls_analyzed'].append(item['url'])
            elif isinstance(item, str):
                content = item
            
            if content and len(content.strip()) > 50:  # Contenido sustancial
                analysis['total_chars'] += len(content)
                analysis['content_snippets'].append(content[:200])
                analysis['has_substantial_content'] = True
        
        return analysis
    
    def _verify_coverage(self, required_elements: Dict[str, Dict], 
                        content_analysis: Dict[str, Any], 
                        collected_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verifica si cada elemento requerido está cubierto en el contenido"""
        coverage_results = {}
        
        # Combinar todo el contenido en un texto grande para análisis
        all_content = ""
        for item in collected_data:
            if isinstance(item, dict):
                content = (item.get('content', '') or 
                          item.get('snippet', '') or 
                          item.get('description', '') or 
                          item.get('title', ''))
                all_content += f" {content}"
            elif isinstance(item, str):
                all_content += f" {item}"
        
        all_content_lower = all_content.lower()
        
        for element_type, element_config in required_elements.items():
            patterns = element_config['patterns']
            required_subelements = element_config['required_elements']
            
            # Buscar evidencia de este elemento en el contenido
            matches = []
            for pattern in patterns:
                pattern_matches = re.findall(pattern, all_content_lower)
                matches.extend(pattern_matches)
            
            # Evaluar cobertura
            found = len(matches) > 0
            coverage_quality = self._evaluate_coverage_quality(
                matches, all_content_lower, required_subelements
            )
            
            coverage_results[element_type] = {
                'found': found,
                'matches_count': len(matches),
                'coverage_quality': coverage_quality,
                'evidence_snippets': self._extract_evidence_snippets(
                    all_content, patterns, max_snippets=3
                ),
                'required_subelements': required_subelements,
                'priority': element_config['priority']
            }
        
        return coverage_results
    
    def _evaluate_coverage_quality(self, matches: List[str], 
                                  full_content: str, 
                                  required_subelements: List[str]) -> str:
        """Evalúa la calidad de la cobertura encontrada"""
        if not matches:
            return 'none'
        
        match_count = len(matches)
        content_length = len(full_content)
        
        if match_count >= 5 and content_length > 1000:
            return 'excellent'
        elif match_count >= 3 and content_length > 500:
            return 'good'  
        elif match_count >= 1 and content_length > 200:
            return 'basic'
        else:
            return 'minimal'
    
    def _extract_evidence_snippets(self, content: str, patterns: List[str], 
                                  max_snippets: int = 3) -> List[str]:
        """Extrae fragmentos de evidencia del contenido"""
        snippets = []
        
        for pattern in patterns[:max_snippets]:  # Limitar patrones
            matches = list(re.finditer(pattern, content.lower()))
            for match in matches[:1]:  # Solo primer match por patrón
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                snippet = content[start:end].strip()
                if snippet not in snippets:
                    snippets.append(snippet)
                if len(snippets) >= max_snippets:
                    break
            if len(snippets) >= max_snippets:
                break
        
        return snippets
    
    def _calculate_completeness_score(self, coverage_results: Dict[str, Any], 
                                    required_elements: Dict[str, Dict]) -> int:
        """Calcula score de completitud basado en cobertura"""
        if not required_elements:
            return 100  # Si no hay requisitos específicos, está completo
        
        total_points = 0
        max_points = 0
        
        for element_type, coverage in coverage_results.items():
            element_config = required_elements[element_type]
            priority = element_config['priority']
            
            # Puntos por prioridad
            max_element_points = 100 if priority == 'high' else 50 if priority == 'medium' else 25
            max_points += max_element_points
            
            if coverage['found']:
                quality = coverage['coverage_quality']
                if quality == 'excellent':
                    total_points += max_element_points
                elif quality == 'good':
                    total_points += int(max_element_points * 0.8)
                elif quality == 'basic':
                    total_points += int(max_element_points * 0.6)
                elif quality == 'minimal':
                    total_points += int(max_element_points * 0.3)
        
        return int((total_points / max_points) * 100) if max_points > 0 else 0
    
    def _evaluate_final_completeness(self, completeness_score: int, 
                                   coverage_results: Dict[str, Any],
                                   required_elements: Dict[str, Dict]) -> bool:
        """Evalúa si cumple los requisitos para considerar el paso completo"""
        
        # Criterio 1: Score mínimo
        if completeness_score < 70:
            return False
        
        # Criterio 2: Todos los elementos de alta prioridad deben estar presentes
        high_priority_missing = []
        for element_type, element_config in required_elements.items():
            if element_config['priority'] == 'high':
                if not coverage_results.get(element_type, {}).get('found', False):
                    high_priority_missing.append(element_type)
        
        if high_priority_missing:
            logger.warning(f"❌ Elementos de alta prioridad faltantes: {high_priority_missing}")
            return False
        
        # Criterio 3: Al menos 60% de elementos encontrados
        found_elements = sum(1 for coverage in coverage_results.values() if coverage['found'])
        required_count = len(required_elements)
        
        if required_count > 0 and (found_elements / required_count) < 0.6:
            return False
        
        return True
    
    def _generate_specific_recommendations(self, coverage_results: Dict[str, Any],
                                         required_elements: Dict[str, Dict],
                                         meets_requirements: bool) -> List[str]:
        """Genera recomendaciones específicas para búsquedas adicionales"""
        recommendations = []
        
        if meets_requirements:
            return ["El paso está completo y cumple con todos los requisitos."]
        
        # Recomendar búsquedas específicas para elementos faltantes
        for element_type, coverage in coverage_results.items():
            if not coverage['found'] or coverage['coverage_quality'] in ['minimal', 'basic']:
                element_config = required_elements[element_type]
                
                if element_type == 'biografia':
                    recommendations.append(
                        "Buscar específicamente biografía personal: 'nombre completo biografía fecha nacimiento formación académica'"
                    )
                elif element_type == 'trayectoria_politica':
                    recommendations.append(
                        "Buscar trayectoria política: 'cargos políticos historial elecciones partidos políticos'"
                    )
                elif element_type == 'ideologia':
                    recommendations.append(
                        "Buscar posición ideológica: 'ideología política posición derecha izquierda principios'"
                    )
                elif element_type == 'declaraciones_publicas':
                    recommendations.append(
                        "Buscar declaraciones recientes: 'últimas declaraciones entrevistas opiniones públicas'"
                    )
                else:
                    recommendations.append(
                        f"Buscar más información sobre {element_type.replace('_', ' ')}"
                    )
        
        # Si tiene contenido muy poco, recomendar fuentes más específicas
        if sum(1 for c in coverage_results.values() if c['found']) < 2:
            recommendations.append(
                "Buscar en fuentes más específicas: sitios de noticias, Wikipedia, biografías oficiales"
            )
        
        return recommendations
    
    def _generate_validation_summary(self, meets_requirements: bool, 
                                   completeness_score: int,
                                   coverage_results: Dict[str, Any]) -> str:
        """Genera un resumen textual de la validación"""
        if meets_requirements:
            return f"✅ PASO COMPLETO - Completitud {completeness_score}% - Todos los elementos requeridos están presentes"
        
        found_elements = [elem for elem, result in coverage_results.items() if result['found']]
        missing_elements = [elem for elem, result in coverage_results.items() if not result['found']]
        
        summary_parts = [
            f"❌ PASO INCOMPLETO - Completitud {completeness_score}%",
            f"Encontrado: {', '.join(found_elements) if found_elements else 'Ninguno'}",
            f"Faltante: {', '.join(missing_elements) if missing_elements else 'Ninguno'}"
        ]
        
        return " | ".join(summary_parts)

# Instancia global
_step_validator = None

def get_step_requirement_validator() -> StepRequirementValidator:
    """Obtener instancia global del validador"""
    global _step_validator
    if _step_validator is None:
        _step_validator = StepRequirementValidator()
    return _step_validator

def validate_step_completeness(step_description: str, step_title: str, 
                              collected_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    🎯 FUNCIÓN PRINCIPAL DE VALIDACIÓN DE COMPLETITUD
    
    Wrapper function para facilitar el uso desde otras partes del código
    """
    validator = get_step_requirement_validator()
    return validator.validate_step_requirements(step_description, step_title, collected_data)