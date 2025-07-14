"""
Herramienta de Web Scraping Avanzado con Firecrawl
Mejora significativa sobre BeautifulSoup para extracción de contenido
"""

import os
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import time

class FirecrawlTool:
    def __init__(self):
        self.name = "firecrawl_scraper"
        self.description = "Herramienta avanzada de web scraping usando Firecrawl API"
        self.api_key = os.getenv('FIRECRAWL_API_KEY')
        self.base_url = "https://api.firecrawl.dev/v0"
        
        if not self.api_key:
            print("⚠️  FIRECRAWL_API_KEY not found in environment variables")
    
    def get_description(self) -> str:
        return self.description
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "url",
                "type": "string",
                "description": "URL del sitio web a scrapear",
                "required": True
            },
            {
                "name": "mode",
                "type": "string",
                "description": "Modo de scraping: 'single' para una página, 'crawl' para múltiples páginas",
                "default": "single",
                "enum": ["single", "crawl"]
            },
            {
                "name": "include_links",
                "type": "boolean",
                "description": "Incluir enlaces encontrados en la página",
                "default": True
            },
            {
                "name": "include_images",
                "type": "boolean",
                "description": "Incluir imágenes encontradas en la página",
                "default": True
            },
            {
                "name": "extract_schema",
                "type": "boolean",
                "description": "Extraer datos estructurados (JSON-LD, microdata)",
                "default": True
            },
            {
                "name": "wait_for_selector",
                "type": "string",
                "description": "Selector CSS para esperar antes de scrapear (útil para contenido dinámico)",
                "default": None
            },
            {
                "name": "timeout",
                "type": "integer",
                "description": "Tiempo límite en segundos",
                "default": 30
            }
        ]
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecutar scraping con Firecrawl
        
        Args:
            parameters: Parámetros de la herramienta
            config: Configuración adicional
            
        Returns:
            Resultado del scraping
        """
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'Firecrawl API key not configured',
                    'suggestion': 'Configure FIRECRAWL_API_KEY in environment variables'
                }
            
            url = parameters.get('url')
            mode = parameters.get('mode', 'single')
            
            if not url:
                return {
                    'success': False,
                    'error': 'URL is required'
                }
            
            # Validar URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            if mode == 'single':
                return self._scrape_single_page(url, parameters)
            elif mode == 'crawl':
                return self._crawl_multiple_pages(url, parameters)
            else:
                return {
                    'success': False,
                    'error': f'Invalid mode: {mode}. Use "single" or "crawl"'
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _scrape_single_page(self, url: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Scrapear una sola página"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Preparar payload
            payload = {
                'url': url,
                'formats': ['markdown', 'html'],
                'includeTags': parameters.get('include_links', True),
                'includeImages': parameters.get('include_images', True),
                'extractSchema': parameters.get('extract_schema', True),
                'waitFor': parameters.get('wait_for_selector'),
                'timeout': parameters.get('timeout', 30) * 1000  # Convertir a milisegundos
            }
            
            # Filtrar valores None
            payload = {k: v for k, v in payload.items() if v is not None}
            
            # Hacer request a Firecrawl
            response = requests.post(
                f'{self.base_url}/scrape',
                headers=headers,
                json=payload,
                timeout=parameters.get('timeout', 30)
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extraer información útil
                result = {
                    'success': True,
                    'url': url,
                    'title': data.get('data', {}).get('title', ''),
                    'content': data.get('data', {}).get('markdown', ''),
                    'html': data.get('data', {}).get('html', ''),
                    'links': self._extract_links(data.get('data', {})),
                    'images': self._extract_images(data.get('data', {})),
                    'schema': data.get('data', {}).get('schema', {}),
                    'metadata': {
                        'description': data.get('data', {}).get('description', ''),
                        'keywords': data.get('data', {}).get('keywords', []),
                        'author': data.get('data', {}).get('author', ''),
                        'language': data.get('data', {}).get('language', ''),
                        'scraped_at': datetime.now().isoformat()
                    },
                    'stats': {
                        'content_length': len(data.get('data', {}).get('markdown', '')),
                        'html_length': len(data.get('data', {}).get('html', '')),
                        'links_found': len(self._extract_links(data.get('data', {}))),
                        'images_found': len(self._extract_images(data.get('data', {})))
                    }
                }
                
                return result
            
            else:
                return {
                    'success': False,
                    'error': f'Firecrawl API error: {response.status_code}',
                    'details': response.text
                }
        
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout',
                'suggestion': 'Try increasing the timeout parameter'
            }
        
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Request error: {str(e)}'
            }
    
    def _crawl_multiple_pages(self, url: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Crawlear múltiples páginas"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Preparar payload para crawling
            payload = {
                'url': url,
                'crawlerOptions': {
                    'includes': [f"{url}/*"],
                    'excludes': [],
                    'limit': parameters.get('page_limit', 10)
                },
                'pageOptions': {
                    'formats': ['markdown'],
                    'includeTags': parameters.get('include_links', True),
                    'includeImages': parameters.get('include_images', True),
                    'extractSchema': parameters.get('extract_schema', True)
                }
            }
            
            # Iniciar crawling
            response = requests.post(
                f'{self.base_url}/crawl',
                headers=headers,
                json=payload,
                timeout=parameters.get('timeout', 30)
            )
            
            if response.status_code == 200:
                data = response.json()
                job_id = data.get('jobId')
                
                if not job_id:
                    return {
                        'success': False,
                        'error': 'No job ID received from Firecrawl'
                    }
                
                # Polling para obtener resultados
                return self._poll_crawl_results(job_id, parameters.get('timeout', 30))
            
            else:
                return {
                    'success': False,
                    'error': f'Firecrawl crawl error: {response.status_code}',
                    'details': response.text
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Crawl error: {str(e)}'
            }
    
    def _poll_crawl_results(self, job_id: str, timeout: int) -> Dict[str, Any]:
        """Obtener resultados del crawling"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }
            
            start_time = time.time()
            
            while (time.time() - start_time) < timeout:
                response = requests.get(
                    f'{self.base_url}/crawl/status/{job_id}',
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    
                    if status == 'completed':
                        # Procesar resultados
                        results = data.get('data', [])
                        
                        return {
                            'success': True,
                            'job_id': job_id,
                            'status': status,
                            'pages_crawled': len(results),
                            'results': self._process_crawl_results(results),
                            'summary': self._generate_crawl_summary(results)
                        }
                    
                    elif status == 'failed':
                        return {
                            'success': False,
                            'error': 'Crawl job failed',
                            'details': data.get('error', 'Unknown error')
                        }
                    
                    # Si está en progreso, esperar
                    time.sleep(2)
                
                else:
                    return {
                        'success': False,
                        'error': f'Status check error: {response.status_code}'
                    }
            
            return {
                'success': False,
                'error': 'Crawl timeout',
                'suggestion': 'Try increasing the timeout or reducing the page limit'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Polling error: {str(e)}'
            }
    
    def _extract_links(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extraer enlaces de los datos"""
        links = []
        
        # Extraer de linksOnPage si está disponible
        if 'linksOnPage' in data:
            for link in data['linksOnPage']:
                links.append({
                    'url': link.get('url', ''),
                    'text': link.get('text', ''),
                    'type': 'internal' if link.get('url', '').startswith(data.get('url', '')) else 'external'
                })
        
        return links
    
    def _extract_images(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extraer imágenes de los datos"""
        images = []
        
        # Extraer de imagesOnPage si está disponible
        if 'imagesOnPage' in data:
            for image in data['imagesOnPage']:
                images.append({
                    'url': image.get('url', ''),
                    'alt': image.get('alt', ''),
                    'title': image.get('title', '')
                })
        
        return images
    
    def _process_crawl_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Procesar resultados del crawling"""
        processed = []
        
        for result in results:
            processed.append({
                'url': result.get('url', ''),
                'title': result.get('title', ''),
                'content': result.get('markdown', ''),
                'content_length': len(result.get('markdown', '')),
                'links_count': len(result.get('linksOnPage', [])),
                'images_count': len(result.get('imagesOnPage', []))
            })
        
        return processed
    
    def _generate_crawl_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generar resumen del crawling"""
        total_content = sum(len(result.get('markdown', '')) for result in results)
        total_links = sum(len(result.get('linksOnPage', [])) for result in results)
        total_images = sum(len(result.get('imagesOnPage', [])) for result in results)
        
        return {
            'total_pages': len(results),
            'total_content_length': total_content,
            'total_links_found': total_links,
            'total_images_found': total_images,
            'average_content_length': total_content // len(results) if results else 0,
            'crawled_at': datetime.now().isoformat()
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validar parámetros de entrada"""
        errors = []
        
        # Validar URL
        url = parameters.get('url')
        if not url:
            errors.append("URL is required")
        elif not isinstance(url, str):
            errors.append("URL must be a string")
        elif not url.startswith(('http://', 'https://', 'www.')):
            errors.append("URL must start with http://, https://, or www.")
        
        # Validar modo
        mode = parameters.get('mode', 'single')
        if mode not in ['single', 'crawl']:
            errors.append("Mode must be 'single' or 'crawl'")
        
        # Validar timeout
        timeout = parameters.get('timeout', 30)
        if not isinstance(timeout, int) or timeout <= 0:
            errors.append("Timeout must be a positive integer")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Información adicional de la herramienta"""
        return {
            'category': 'web_scraping',
            'version': '1.0.0',
            'capabilities': [
                'Advanced web scraping',
                'JavaScript rendering',
                'Structured data extraction',
                'Multiple format output',
                'Crawling multiple pages'
            ],
            'advantages_over_beautifulsoup': [
                'Handles JavaScript-rendered content',
                'Better structured data extraction',
                'Built-in link and image extraction',
                'Timeout and error handling',
                'Multiple output formats'
            ],
            'api_status': 'configured' if self.api_key else 'not_configured'
        }