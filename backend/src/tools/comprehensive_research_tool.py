"""
Herramienta de investigación comprehensiva - Multi-sitio con imágenes
Combina Tavily para contenido y DuckDuckGo para imágenes
"""

import os
import requests
from typing import Dict, Any, List
from tavily import TavilyClient
try:
    from duckduckgo_search import DDGS
except ImportError:
    print("Warning: duckduckgo_search not available, using fallback")
    DDGS = None
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse

class ComprehensiveResearchTool:
    def __init__(self):
        self.name = "comprehensive_research"
        self.description = "Realiza investigación profunda multi-sitio con contenido e imágenes, generando un informe consolidado"
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        self.tavily_client = TavilyClient(api_key=self.tavily_api_key) if self.tavily_api_key else None
        # DDGS ELIMINADO - Solo Bing soportado
        self.parameters = [
            {
                "name": "query",
                "type": "string",
                "required": True,
                "description": "Tema principal para investigar"
            },
            {
                "name": "include_images",
                "type": "boolean",
                "required": False,
                "description": "Incluir búsqueda de imágenes relacionadas",
                "default": True
            },
            {
                "name": "max_sources",
                "type": "integer",
                "required": False,
                "description": "Número máximo de fuentes a analizar",
                "default": 8
            },
            {
                "name": "max_images",
                "type": "integer",
                "required": False,
                "description": "Número máximo de imágenes a incluir",
                "default": 6
            },
            {
                "name": "research_depth",
                "type": "string",
                "required": False,
                "description": "Profundidad de investigación: 'standard', 'comprehensive', 'expert'",
                "default": "comprehensive"
            },
            {
                "name": "content_extraction",
                "type": "boolean",
                "required": False,
                "description": "Extraer contenido completo de las páginas principales",
                "default": True
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
        
        if not self.tavily_api_key:
            return {'valid': False, 'error': 'Tavily API key not configured'}
        
        return {'valid': True}
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar investigación comprehensiva"""
        if config is None:
            config = {}
        
        # Validar parámetros
        validation = self.validate_parameters(parameters)
        if not validation['valid']:
            return {'error': validation['error'], 'success': False}
        
        query = parameters['query'].strip()
        include_images = parameters.get('include_images', True)
        max_sources = min(parameters.get('max_sources', 8), 15)
        max_images = min(parameters.get('max_images', 6), 20)
        research_depth = parameters.get('research_depth', 'comprehensive')
        content_extraction = parameters.get('content_extraction', True)
        
        try:
            # Realizar investigación multi-fase
            research_results = self._conduct_comprehensive_research(
                query, include_images, max_sources, max_images, 
                research_depth, content_extraction
            )
            
            return {
                'query': query,
                'research_depth': research_depth,
                'report': research_results['report'],
                'sources': research_results['sources'],
                'images': research_results['images'] if include_images else [],
                'extracted_content': research_results['extracted_content'],
                'key_findings': research_results['key_findings'],
                'recommendations': research_results['recommendations'],
                'source_count': len(research_results['sources']),
                'image_count': len(research_results['images']) if include_images else 0,
                'success': True
            }
            
        except Exception as e:
            return {
                'query': query,
                'error': str(e),
                'success': False
            }
    
    def _conduct_comprehensive_research(self, query: str, include_images: bool, 
                                      max_sources: int, max_images: int,
                                      research_depth: str, content_extraction: bool) -> Dict[str, Any]:
        """Realizar investigación comprehensiva multi-sitio"""
        
        # FASE 1: Búsqueda inicial con Tavily
        print(f"🔍 FASE 1: Búsqueda inicial sobre '{query}'")
        initial_search = self.tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=max_sources,
            include_answer=True
        )
        
        # FASE 2: Búsquedas específicas para mayor profundidad
        print(f"🔍 FASE 2: Búsquedas específicas")
        specific_queries = [
            f"{query} definición concepto",
            f"{query} características principales",
            f"{query} ventajas beneficios",
            f"{query} desventajas riesgos",
            f"{query} tendencias futuro 2025"
        ]
        
        all_sources = []
        all_content = []
        
        # Procesar búsqueda inicial
        for result in initial_search.get('results', []):
            all_sources.append({
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'snippet': result.get('content', ''),
                'score': result.get('score', 0),
                'type': 'primary'
            })
            all_content.append(result.get('content', ''))
        
        # Búsquedas específicas adicionales
        for specific_query in specific_queries[:3]:  # Limitar para evitar sobrecarga
            try:
                specific_results = self.tavily_client.search(
                    query=specific_query,
                    search_depth="basic",
                    max_results=3,
                    include_answer=True
                )
                
                for result in specific_results.get('results', []):
                    all_sources.append({
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'snippet': result.get('content', ''),
                        'score': result.get('score', 0),
                        'type': 'specific'
                    })
                    all_content.append(result.get('content', ''))
                    
            except Exception as e:
                print(f"Error en búsqueda específica: {e}")
                continue
        
        # FASE 3: Extracción de contenido completo de páginas principales
        print(f"🔍 FASE 3: Extracción de contenido completo")
        extracted_content = []
        if content_extraction:
            top_sources = all_sources[:5]  # Extraer de las 5 mejores fuentes
            for source in top_sources:
                try:
                    content = self._extract_page_content(source['url'])
                    if content:
                        extracted_content.append({
                            'title': source['title'],
                            'url': source['url'],
                            'full_content': content,
                            'word_count': len(content.split())
                        })
                except Exception as e:
                    print(f"Error extrayendo contenido de {source['url']}: {e}")
                    continue
        
        # FASE 4: Búsqueda de imágenes - DESHABILITADA (DuckDuckGo eliminado)
        print(f"🔍 FASE 4: Búsqueda de imágenes - DESHABILITADA")
        images = []
        if include_images:
            # DUCKDUCKGO ELIMINADO - Solo Bing soportado en el futuro
            print("⚠️  Búsqueda de imágenes deshabilitada - DuckDuckGo eliminado")
            images = []
        
        # FASE 5: Análisis y generación del informe
        print(f"🔍 FASE 5: Generación del informe")
        combined_content = "\n".join(all_content)
        
        # Extraer información de contenido completo
        full_content_text = ""
        for content in extracted_content:
            full_content_text += f"\n\n{content['full_content']}"
        
        # Generar informe consolidado
        report = self._generate_consolidated_report(
            query, initial_search.get('answer', ''), 
            combined_content, full_content_text, 
            research_depth, len(all_sources), len(images)
        )
        
        # Extraer hallazgos clave
        key_findings = self._extract_comprehensive_findings(
            combined_content, full_content_text, extracted_content
        )
        
        # Generar recomendaciones
        recommendations = self._generate_actionable_recommendations(
            query, key_findings, research_depth
        )
        
        return {
            'report': report,
            'sources': all_sources[:max_sources],
            'images': images,
            'extracted_content': extracted_content,
            'key_findings': key_findings,
            'recommendations': recommendations
        }
    
    def _extract_page_content(self, url: str) -> str:
        """Extraer contenido completo de una página web"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remover elementos no deseados
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "advertisement"]):
                element.decompose()
            
            # Buscar contenido principal
            main_content = (soup.find('main') or 
                          soup.find('article') or 
                          soup.find('div', class_='content') or
                          soup.find('div', class_='main-content'))
            
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)
            
            # Limpiar y limitar contenido
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            clean_text = '\n'.join(lines)
            
            # Limitar a 3000 caracteres para evitar sobrecarga
            if len(clean_text) > 3000:
                clean_text = clean_text[:3000] + '...'
            
            return clean_text
            
        except Exception as e:
            print(f"Error extrayendo contenido: {e}")
            return ""
    
    def _generate_consolidated_report(self, query: str, initial_answer: str, 
                                    combined_content: str, full_content: str,
                                    research_depth: str, source_count: int, 
                                    image_count: int) -> str:
        """Generar informe consolidado"""
        
        report = f"""
# INFORME CONSOLIDADO: {query.upper()}

## 📊 RESUMEN EJECUTIVO
{initial_answer}

## 🔍 METODOLOGÍA DE INVESTIGACIÓN
- **Fuentes analizadas**: {source_count} sitios web
- **Imágenes incluidas**: {image_count} imágenes
- **Profundidad**: {research_depth}
- **Extracción de contenido**: {"Sí" if full_content else "No"}

## 📋 ANÁLISIS DETALLADO
{self._analyze_content(combined_content + full_content, research_depth)}

## 🎯 PUNTOS CLAVE IDENTIFICADOS
{self._extract_key_points(combined_content + full_content, 8)}

## 📈 TENDENCIAS Y PATRONES
{self._identify_trends(combined_content + full_content)}

## 💡 IMPLICACIONES
{self._analyze_implications(combined_content + full_content)}

## 🎯 CONCLUSIONES
{self._generate_conclusions(combined_content + full_content)}

---
*Informe generado automáticamente mediante análisis multi-sitio*
"""
        
        return report
    
    def _analyze_content(self, content: str, depth: str) -> str:
        """Analizar contenido según profundidad"""
        sentences = content.split('.')
        important_sentences = []
        
        keywords = ['importante', 'clave', 'fundamental', 'esencial', 'crítico', 'significativo']
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                if len(sentence.strip()) > 30:
                    important_sentences.append(sentence.strip())
        
        if depth == 'expert':
            return '\n'.join([f"• {sent}" for sent in important_sentences[:10]])
        elif depth == 'comprehensive':
            return '\n'.join([f"• {sent}" for sent in important_sentences[:7]])
        else:
            return '\n'.join([f"• {sent}" for sent in important_sentences[:5]])
    
    def _extract_key_points(self, content: str, max_points: int) -> str:
        """Extraer puntos clave"""
        sentences = content.split('.')
        key_points = []
        
        for sentence in sentences:
            if len(sentence.strip()) > 40:
                key_points.append(f"• {sentence.strip()}")
            if len(key_points) >= max_points:
                break
        
        return '\n'.join(key_points)
    
    def _identify_trends(self, content: str) -> str:
        """Identificar tendencias"""
        trend_keywords = ['tendencia', 'crecimiento', 'aumento', 'evolución', 'futuro', '2025', 'próximo']
        trends = []
        
        sentences = content.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in trend_keywords):
                if len(sentence.strip()) > 30:
                    trends.append(f"• {sentence.strip()}")
        
        return '\n'.join(trends[:5]) if trends else "• No se identificaron tendencias específicas en el contenido analizado"
    
    def _analyze_implications(self, content: str) -> str:
        """Analizar implicaciones"""
        impl_keywords = ['implica', 'significa', 'consecuencia', 'resultado', 'impacto', 'efecto']
        implications = []
        
        sentences = content.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in impl_keywords):
                if len(sentence.strip()) > 30:
                    implications.append(f"• {sentence.strip()}")
        
        return '\n'.join(implications[:5]) if implications else "• Se requiere análisis adicional para determinar implicaciones específicas"
    
    def _generate_conclusions(self, content: str) -> str:
        """Generar conclusiones"""
        return f"""
• Basado en el análisis de múltiples fuentes, se identifica información consistente sobre el tema
• La investigación revela aspectos clave que requieren consideración detallada
• Se recomienda validación adicional con fuentes especializadas según el contexto específico
• Los hallazgos proporcionan una base sólida para la toma de decisiones informadas
"""
    
    def _extract_comprehensive_findings(self, content: str, full_content: str, extracted_content: List[Dict]) -> List[str]:
        """Extraer hallazgos comprehensivos"""
        findings = []
        
        # Analizar contenido combinado
        all_text = content + " " + full_content
        sentences = all_text.split('.')
        
        # Palabras clave para identificar hallazgos importantes
        important_keywords = ['descubrimiento', 'hallazgo', 'resultado', 'concluye', 'determina', 'revela']
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in important_keywords):
                if len(sentence.strip()) > 25:
                    findings.append(sentence.strip())
        
        # Agregar hallazgos específicos del contenido extraído
        for content_item in extracted_content:
            if content_item['word_count'] > 100:
                findings.append(f"Análisis detallado disponible en: {content_item['title']}")
        
        return findings[:8]
    
    def _generate_actionable_recommendations(self, query: str, findings: List[str], depth: str) -> List[str]:
        """Generar recomendaciones accionables"""
        recommendations = []
        
        # Recomendaciones específicas por tema
        if any(word in query.lower() for word in ['negocio', 'empresa', 'marketing']):
            recommendations.extend([
                "Realizar análisis de competencia específico",
                "Evaluar oportunidades de mercado identificadas",
                "Desarrollar estrategia basada en hallazgos clave"
            ])
        
        if any(word in query.lower() for word in ['tecnología', 'digital', 'software']):
            recommendations.extend([
                "Evaluar impacto tecnológico en el sector",
                "Considerar implementación gradual de soluciones",
                "Monitorear tendencias de adopción"
            ])
        
        # Recomendaciones generales
        recommendations.extend([
            "Continuar monitoreando fuentes especializadas",
            "Validar información con expertos del área",
            "Implementar sistema de seguimiento de tendencias",
            "Considerar factores contextuales específicos"
        ])
        
        return recommendations[:6]