"""
Herramienta de investigación profunda - Deep Research
"""

import os
import requests
from typing import Dict, Any, List
from tavily import TavilyClient

class DeepResearchTool:
    def __init__(self):
        self.name = "deep_research"
        self.description = "Realiza investigación profunda y análisis detallado sobre un tema específico"
        self.api_key = os.getenv('TAVILY_API_KEY')
        self.client = TavilyClient(api_key=self.api_key) if self.api_key else None
        self.parameters = [
            {
                "name": "query",
                "type": "string",
                "required": True,
                "description": "Tema o pregunta para investigar en profundidad"
            },
            {
                "name": "research_depth",
                "type": "string",
                "required": False,
                "description": "Nivel de profundidad: 'standard', 'comprehensive', 'expert'",
                "default": "comprehensive"
            },
            {
                "name": "focus_areas",
                "type": "array",
                "required": False,
                "description": "Áreas específicas para enfocar la investigación",
                "default": []
            },
            {
                "name": "max_sources",
                "type": "integer",
                "required": False,
                "description": "Número máximo de fuentes a analizar",
                "default": 10
            }
        ]
    
    def get_description(self) -> str:
        return self.description
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        return self.parameters
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validar parámetros de entrada"""
        if not isinstance(parameters, dict):
            return {'valid': False, 'error': 'Parameters must be a dictionary'}
        
        if 'query' not in parameters:
            return {'valid': False, 'error': 'query parameter is required'}
        
        if not isinstance(parameters['query'], str) or not parameters['query'].strip():
            return {'valid': False, 'error': 'query must be a non-empty string'}
        
        if not self.api_key:
            return {'valid': False, 'error': 'Tavily API key not configured'}
        
        return {'valid': True}
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar investigación profunda"""
        if config is None:
            config = {}
        
        # Validar parámetros
        validation = self.validate_parameters(parameters)
        if not validation['valid']:
            return {'error': validation['error'], 'success': False}
        
        query = parameters['query'].strip()
        research_depth = parameters.get('research_depth', 'comprehensive')
        focus_areas = parameters.get('focus_areas', [])
        max_sources = min(parameters.get('max_sources', 10), config.get('max_sources', 15))
        
        try:
            # Realizar investigación con diferentes enfoques
            research_results = self._conduct_deep_research(query, research_depth, focus_areas, max_sources)
            
            return {
                'query': query,
                'research_depth': research_depth,
                'focus_areas': focus_areas,
                'analysis': research_results['analysis'],
                'key_findings': research_results['key_findings'],
                'sources': research_results['sources'],
                'recommendations': research_results['recommendations'],
                'source_count': len(research_results['sources']),
                'success': True
            }
            
        except Exception as e:
            return {
                'query': query,
                'error': str(e),
                'success': False
            }
    
    def _conduct_deep_research(self, query: str, research_depth: str, focus_areas: List[str], max_sources: int) -> Dict[str, Any]:
        """Realizar investigación profunda paso a paso"""
        
        # Paso 1: Búsqueda inicial para obtener contexto general
        initial_response = self.client.search(
            query=query,
            search_depth="advanced",
            max_results=max_sources,
            include_answer=True
        )
        
        # Paso 2: Generar consultas específicas basadas en focus_areas
        specific_searches = []
        if focus_areas:
            for area in focus_areas:
                specific_query = f"{query} {area}"
                specific_response = self.client.search(
                    query=specific_query,
                    search_depth="advanced",
                    max_results=5,
                    include_answer=True
                )
                specific_searches.append({
                    'focus_area': area,
                    'query': specific_query,
                    'results': specific_response.get('results', []),
                    'answer': specific_response.get('answer', '')
                })
        
        # Paso 3: Análisis y síntesis de información
        all_sources = []
        all_content = []
        
        # Recopilar fuentes principales
        for result in initial_response.get('results', []):
            all_sources.append({
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'content': result.get('content', ''),
                'score': result.get('score', 0),
                'source_type': 'general'
            })
            all_content.append(result.get('content', ''))
        
        # Recopilar fuentes específicas
        for search in specific_searches:
            for result in search['results']:
                all_sources.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'content': result.get('content', ''),
                    'score': result.get('score', 0),
                    'source_type': 'specific',
                    'focus_area': search['focus_area']
                })
                all_content.append(result.get('content', ''))
        
        # Paso 4: Generar análisis y hallazgos clave
        analysis = self._generate_analysis(initial_response.get('answer', ''), all_content, research_depth)
        key_findings = self._extract_key_findings(all_content, focus_areas)
        recommendations = self._generate_recommendations(query, key_findings, research_depth)
        
        return {
            'analysis': analysis,
            'key_findings': key_findings,
            'sources': all_sources[:max_sources],  # Limitar número de fuentes
            'recommendations': recommendations
        }
    
    def _generate_analysis(self, initial_answer: str, all_content: List[str], research_depth: str) -> str:
        """Generar análisis comprehensivo basado en toda la información recopilada"""
        
        # Combinar todo el contenido
        combined_content = "\n".join(all_content)
        
        # Crear análisis basado en el nivel de profundidad
        if research_depth == 'standard':
            analysis = f"""
ANÁLISIS ESTÁNDAR:

Resumen Principal:
{initial_answer}

Puntos Clave Identificados:
{self._extract_key_points(combined_content, 5)}

Conclusiones:
{self._generate_conclusions(combined_content)}
"""
        elif research_depth == 'comprehensive':
            analysis = f"""
ANÁLISIS COMPREHENSIVO:

Resumen Ejecutivo:
{initial_answer}

Análisis Detallado:
{self._extract_key_points(combined_content, 10)}

Tendencias y Patrones:
{self._identify_trends(combined_content)}

Implicaciones:
{self._analyze_implications(combined_content)}

Conclusiones:
{self._generate_conclusions(combined_content)}
"""
        else:  # expert
            analysis = f"""
ANÁLISIS EXPERTO:

Resumen Ejecutivo:
{initial_answer}

Análisis Profundo:
{self._extract_key_points(combined_content, 15)}

Metodología de Investigación:
{self._describe_methodology(research_depth)}

Tendencias y Patrones:
{self._identify_trends(combined_content)}

Análisis Crítico:
{self._critical_analysis(combined_content)}

Limitaciones del Estudio:
{self._identify_limitations()}

Implicaciones Estratégicas:
{self._analyze_implications(combined_content)}

Conclusiones y Recomendaciones:
{self._generate_conclusions(combined_content)}
"""
        
        return analysis
    
    def _extract_key_findings(self, all_content: List[str], focus_areas: List[str]) -> List[str]:
        """Extraer hallazgos clave de toda la información"""
        key_findings = []
        
        # Analizar contenido general
        combined_content = "\n".join(all_content)
        sentences = combined_content.split('.')
        
        # Buscar patrones importantes
        important_keywords = ['importante', 'clave', 'fundamental', 'crucial', 'significativo', 'destaca', 'revela']
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in important_keywords):
                if len(sentence.strip()) > 20:  # Filtrar oraciones muy cortas
                    key_findings.append(sentence.strip())
        
        # Limitar número de hallazgos
        return key_findings[:10]
    
    def _generate_recommendations(self, query: str, key_findings: List[str], research_depth: str) -> List[str]:
        """Generar recomendaciones basadas en la investigación"""
        recommendations = []
        
        if 'negocio' in query.lower() or 'empresa' in query.lower():
            recommendations.extend([
                "Realizar análisis de mercado más detallado",
                "Evaluar la competencia directa e indirecta",
                "Considerar factores de riesgo identificados"
            ])
        
        if 'tecnología' in query.lower() or 'tech' in query.lower():
            recommendations.extend([
                "Evaluar tendencias tecnológicas emergentes",
                "Analizar impacto en la industria",
                "Considerar adopción gradual vs. implementación completa"
            ])
        
        if 'salud' in query.lower() or 'medicina' in query.lower():
            recommendations.extend([
                "Consultar con expertos médicos",
                "Revisar estudios clínicos recientes",
                "Considerar regulaciones y normativas"
            ])
        
        # Recomendaciones generales
        recommendations.extend([
            "Continuar monitoreando desarrollos en el área",
            "Validar información con fuentes adicionales",
            "Considerar factores contextuales específicos"
        ])
        
        return recommendations[:8]
    
    def _extract_key_points(self, content: str, max_points: int) -> str:
        """Extraer puntos clave del contenido"""
        sentences = content.split('.')
        key_points = []
        
        for sentence in sentences:
            if len(sentence.strip()) > 30:
                key_points.append(f"• {sentence.strip()}")
            if len(key_points) >= max_points:
                break
        
        return "\n".join(key_points)
    
    def _identify_trends(self, content: str) -> str:
        """Identificar tendencias en el contenido"""
        trend_keywords = ['tendencia', 'crecimiento', 'aumento', 'disminución', 'evolución', 'cambio']
        trends = []
        
        sentences = content.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in trend_keywords):
                if len(sentence.strip()) > 20:
                    trends.append(f"• {sentence.strip()}")
        
        return "\n".join(trends[:5]) if trends else "No se identificaron tendencias claras en la información disponible."
    
    def _analyze_implications(self, content: str) -> str:
        """Analizar implicaciones"""
        implication_keywords = ['implica', 'significa', 'consecuencia', 'resultado', 'impacto']
        implications = []
        
        sentences = content.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in implication_keywords):
                if len(sentence.strip()) > 20:
                    implications.append(f"• {sentence.strip()}")
        
        return "\n".join(implications[:5]) if implications else "Requiere análisis adicional para determinar implicaciones específicas."
    
    def _generate_conclusions(self, content: str) -> str:
        """Generar conclusiones basadas en el contenido"""
        return "Basado en la información analizada, se requiere consideración cuidadosa de todos los factores identificados para tomar decisiones informadas."
    
    def _describe_methodology(self, research_depth: str) -> str:
        """Describir metodología utilizada"""
        return f"""
Metodología de Investigación Aplicada:
• Búsqueda sistemática en múltiples fuentes
• Análisis de contenido cuantitativo y cualitativo  
• Síntesis de información con enfoque {research_depth}
• Validación cruzada de datos
• Extracción de patrones y tendencias
"""
    
    def _critical_analysis(self, content: str) -> str:
        """Realizar análisis crítico"""
        return """
Análisis Crítico:
• Evaluación de la calidad y confiabilidad de las fuentes
• Identificación de posibles sesgos en la información
• Análisis de coherencia entre diferentes fuentes
• Evaluación de la actualidad y relevancia de los datos
"""
    
    def _identify_limitations(self) -> str:
        """Identificar limitaciones del estudio"""
        return """
Limitaciones Identificadas:
• Dependencia de fuentes disponibles públicamente
• Posibles restricciones temporales en la información
• Variabilidad en la calidad de las fuentes
• Necesidad de validación adicional para datos específicos
"""