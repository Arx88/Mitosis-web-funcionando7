"""
Enhanced Web Search Tool - Búsqueda web mejorada con imágenes y presentación elegante
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from tavily import TavilyClient
from duckduckgo_search import DDGS
from datetime import datetime

class EnhancedWebSearchTool:
    def __init__(self):
        self.name = "enhanced_web_search"
        self.description = "Búsqueda web avanzada con múltiples fuentes, imágenes y presentación elegante"
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        self.tavily_client = TavilyClient(api_key=self.tavily_api_key) if self.tavily_api_key else None
        self.ddgs = None
        self.parameters = [
            {
                "name": "query",
                "type": "string",
                "required": True,
                "description": "Términos de búsqueda"
            },
            {
                "name": "max_results",
                "type": "integer",
                "required": False,
                "description": "Número máximo de resultados web",
                "default": 10
            },
            {
                "name": "max_images",
                "type": "integer",
                "required": False,
                "description": "Número máximo de imágenes",
                "default": 5
            },
            {
                "name": "include_summary",
                "type": "boolean",
                "required": False,
                "description": "Incluir resumen ejecutivo",
                "default": True
            },
            {
                "name": "search_depth",
                "type": "string",
                "required": False,
                "description": "Profundidad de búsqueda: 'basic' o 'advanced'",
                "default": "basic"
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
        """Ejecutar búsqueda web mejorada"""
        if config is None:
            config = {}
        
        # Validar parámetros
        validation = self.validate_parameters(parameters)
        if not validation['valid']:
            return {'error': validation['error'], 'success': False}
        
        query = parameters['query'].strip()
        max_results = min(parameters.get('max_results', 10), 15)
        max_images = min(parameters.get('max_images', 5), 10)
        include_summary = parameters.get('include_summary', True)
        search_depth = parameters.get('search_depth', 'basic')
        
        try:
            # Ejecutar búsqueda principal con Tavily
            search_results = self._execute_tavily_search(query, max_results, search_depth)
            
            # Buscar imágenes relacionadas
            images = self._search_images(query, max_images)
            
            # Generar resumen ejecutivo
            summary = self._generate_summary(query, search_results, include_summary)
            
            # Preparar respuesta estructurada
            response = {
                'query': query,
                'direct_answer': search_results.get('answer', ''),
                'sources': self._format_sources(search_results.get('results', [])),
                'images': images,
                'summary': summary,
                'search_stats': {
                    'total_sources': len(search_results.get('results', [])),
                    'total_images': len(images),
                    'search_depth': search_depth,
                    'timestamp': datetime.now().isoformat()
                },
                'console_display': self._generate_console_display(query, search_results, images, summary),
                'success': True
            }
            
            return response
            
        except Exception as e:
            return {
                'query': query,
                'error': str(e),
                'success': False
            }
    
    def _execute_tavily_search(self, query: str, max_results: int, search_depth: str) -> Dict[str, Any]:
        """Ejecutar búsqueda principal con Tavily"""
        try:
            return self.tavily_client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=True
            )
        except Exception as e:
            print(f"Error en búsqueda Tavily: {e}")
            return {'results': [], 'answer': ''}
    
    def _search_images(self, query: str, max_images: int) -> List[Dict[str, Any]]:
        """Buscar imágenes relacionadas"""
        images = []
        try:
            if self.ddgs is None:
                self.ddgs = DDGS()
            
            image_results = list(self.ddgs.images(
                keywords=query,
                max_results=max_images,
                safesearch="moderate"
            ))
            
            for img in image_results:
                images.append({
                    'title': img.get('title', ''),
                    'url': img.get('image', ''),
                    'thumbnail': img.get('thumbnail', ''),
                    'source': img.get('source', ''),
                    'width': img.get('width', 0),
                    'height': img.get('height', 0)
                })
                
        except Exception as e:
            print(f"Error buscando imágenes: {e}")
        
        return images
    
    def _format_sources(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Formatear fuentes para el frontend"""
        formatted_sources = []
        for result in results:
            formatted_sources.append({
                'title': result.get('title', 'Sin título'),
                'content': result.get('content', 'Sin descripción'),
                'url': result.get('url', ''),
                'score': result.get('score', 0),
                'published_date': result.get('published_date', ''),
                'domain': self._extract_domain(result.get('url', ''))
            })
        return formatted_sources
    
    def _extract_domain(self, url: str) -> str:
        """Extraer dominio de una URL"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ''
    
    def _generate_summary(self, query: str, search_results: Dict[str, Any], include_summary: bool) -> str:
        """Generar resumen ejecutivo"""
        if not include_summary:
            return ""
        
        results = search_results.get('results', [])
        answer = search_results.get('answer', '')
        
        if not results:
            return "No se encontraron resultados para procesar."
        
        # Extraer información clave
        top_sources = results[:3]
        key_domains = list(set([self._extract_domain(r.get('url', '')) for r in top_sources]))
        
        summary = f"""
📊 **Resumen de la búsqueda: {query}**

🎯 **Respuesta directa:** {answer}

🔍 **Fuentes principales:** {', '.join(key_domains[:3])}

📈 **Estadísticas:**
• Total de fuentes encontradas: {len(results)}
• Fuentes principales analizadas: {len(top_sources)}
• Dominios únicos consultados: {len(key_domains)}

💡 **Hallazgos clave:**
""".strip()
        
        # Agregar puntos clave de las fuentes principales
        for i, result in enumerate(top_sources, 1):
            content = result.get('content', '')
            if content:
                # Extraer la primera oración o 100 caracteres
                first_sentence = content.split('.')[0][:100] + '...' if len(content) > 100 else content
                summary += f"\n{i}. {first_sentence}"
        
        return summary
    
    def _generate_console_display(self, query: str, search_results: Dict[str, Any], 
                                images: List[Dict[str, Any]], summary: str) -> str:
        """Generar display formateado para consola"""
        
        results = search_results.get('results', [])
        answer = search_results.get('answer', '')
        
        display = f"""
{'='*80}
🌐 BÚSQUEDA WEB MEJORADA - {query.upper()}
{'='*80}

🎯 RESPUESTA DIRECTA:
{answer}

{'='*80}
📊 ESTADÍSTICAS DE BÚSQUEDA
{'='*80}

🔍 Fuentes encontradas: {len(results)}
🖼️ Imágenes recopiladas: {len(images)}
📅 Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{'='*80}
📚 FUENTES PRINCIPALES
{'='*80}

"""
        
        # Agregar fuentes principales
        for i, result in enumerate(results[:5], 1):
            display += f"""
{i}. {result.get('title', 'Sin título')}
   🔗 {result.get('url', '')}
   📄 {result.get('content', 'Sin descripción')[:200]}...
   
"""
        
        if images:
            display += f"""{'='*80}
🖼️ IMÁGENES RELACIONADAS
{'='*80}

"""
            for i, img in enumerate(images, 1):
                display += f"{i}. {img.get('title', 'Sin título')}\n"
                display += f"   🔗 {img.get('url', '')}\n"
                display += f"   📐 {img.get('width', 0)}x{img.get('height', 0)}\n\n"
        
        if summary:
            display += f"""{'='*80}
📋 RESUMEN EJECUTIVO
{'='*80}

{summary}

"""
        
        display += f"""{'='*80}
✅ BÚSQUEDA COMPLETADA EXITOSAMENTE
{'='*80}
"""
        
        return display