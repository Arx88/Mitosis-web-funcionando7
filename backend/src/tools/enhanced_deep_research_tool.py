"""
Enhanced Deep Research Tool - Investigación profunda con progreso detallado
Incluye barra de progreso, tracking detallado y generación de informe.md
"""

import os
import json
import time
import requests
from typing import Dict, Any, List, Callable
from tavily import TavilyClient
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from datetime import datetime
import markdown
import uuid
import threading
import queue

class ProgressTracker:
    """Manejador de progreso en tiempo real"""
    def __init__(self):
        self.progress_queue = queue.Queue()
        self.current_progress = 0
        self.current_step = -1
        self.steps = []
        self.is_active = False
    
    def update_progress(self, percentage: int, step_index: int, action: str, details: List[str] = None):
        """Actualizar progreso y agregar a la cola"""
        self.current_progress = percentage
        self.current_step = step_index
        
        progress_data = {
            'percentage': percentage,
            'step_index': step_index,
            'action': action,
            'details': details or [],
            'timestamp': datetime.now().isoformat()
        }
        
        self.progress_queue.put(progress_data)
        
        # También imprimir en consola
        print(f"[{percentage}%] PASO {step_index + 1}: {action}")
        if details:
            for detail in details:
                print(f"    • {detail}")
    
    def get_latest_progress(self):
        """Obtener el último progreso disponible"""
        latest = None
        while not self.progress_queue.empty():
            try:
                latest = self.progress_queue.get_nowait()
            except queue.Empty:
                break
        return latest

class EnhancedDeepResearchTool:
    def __init__(self):
        self.name = "enhanced_deep_research"
        self.description = "Investigación profunda avanzada con progreso detallado y generación de informe.md"
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        self.tavily_client = TavilyClient(api_key=self.tavily_api_key) if self.tavily_api_key else None
        self.ddgs = None
        self.progress_tracker = ProgressTracker()
        self.parameters = [
            {
                "name": "query",
                "type": "string",
                "required": True,
                "description": "Tema principal para investigar en profundidad"
            },
            {
                "name": "max_sources",
                "type": "integer",
                "required": False,
                "description": "Número máximo de fuentes a investigar (mínimo 5, máximo 20)",
                "default": 20
            },
            {
                "name": "max_images",
                "type": "integer",
                "required": False,
                "description": "Número máximo de imágenes a recopilar",
                "default": 10
            },
            {
                "name": "generate_report",
                "type": "boolean",
                "required": False,
                "description": "Generar archivo de informe.md",
                "default": True
            },
            {
                "name": "task_id",
                "type": "string",
                "required": False,
                "description": "ID de la tarea para guardar el informe",
                "default": None
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
    
    def set_progress_callback(self, callback: Callable[[int, str, List[str]], None]):
        """Establecer callback para progreso (mantenido por compatibilidad)"""
        pass  # Ahora usamos el tracker interno
    
    def _update_progress(self, percentage: int, action: str, details: List[str] = None, step_index: int = -1):
        """Actualizar progreso con detalles usando el tracker"""
        if step_index == -1:
            # Inferir step_index basado en percentage
            if percentage <= 10:
                step_index = 0
            elif percentage <= 45:
                step_index = 1
            elif percentage <= 75:
                step_index = 2
            elif percentage <= 80:
                step_index = 3
            elif percentage <= 85:
                step_index = 4
            else:
                step_index = 5
        
        self.progress_tracker.update_progress(percentage, step_index, action, details)
    
    def get_progress_status(self):
        """Obtener estado actual del progreso"""
        return {
            'is_active': self.progress_tracker.is_active,
            'current_progress': self.progress_tracker.current_progress,
            'current_step': self.progress_tracker.current_step,
            'latest_update': self.progress_tracker.get_latest_progress()
        }
    
    def get_progress_steps(self) -> List[Dict[str, Any]]:
        """Obtener los pasos de progreso predefinidos"""
        return [
            {
                'id': 'search_initial',
                'title': 'Búsqueda inicial',
                'description': 'Recolectando datos iniciales...',
                'status': 'pending',
                'details': [],
                'progress': 0
            },
            {
                'id': 'search_specific',
                'title': 'Búsquedas específicas',
                'description': 'Realizando búsquedas especializadas...',
                'status': 'pending',
                'details': [],
                'progress': 0
            },
            {
                'id': 'content_extraction',
                'title': 'Extracción de contenido',
                'description': 'Extrayendo contenido completo...',
                'status': 'pending',
                'details': [],
                'progress': 0
            },
            {
                'id': 'image_collection',
                'title': 'Recopilación de imágenes',
                'description': 'Juntando imágenes relacionadas...',
                'status': 'pending',
                'details': [],
                'progress': 0
            },
            {
                'id': 'analysis_comparison',
                'title': 'Análisis comparativo',
                'description': 'Comparando artículos y analizando...',
                'status': 'pending',
                'details': [],
                'progress': 0
            },
            {
                'id': 'report_generation',
                'title': 'Generación de informe',
                'description': 'Generando informe completo...',
                'status': 'pending',
                'details': [],
                'progress': 0
            }
        ]
    
    def execute(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar investigación profunda mejorada"""
        if config is None:
            config = {}
        
        # Validar parámetros
        validation = self.validate_parameters(parameters)
        if not validation['valid']:
            return {'error': validation['error'], 'success': False}
        
        query = parameters['query'].strip()
        max_sources = max(5, min(parameters.get('max_sources', 20), 20))
        max_images = min(parameters.get('max_images', 10), 15)
        generate_report = parameters.get('generate_report', True)
        task_id = parameters.get('task_id', str(uuid.uuid4()))
        
        # Activar el tracker de progreso
        self.progress_tracker.is_active = True
        
        try:
            # Iniciar investigación profunda
            self._update_progress(0, "🔍 Iniciando investigación profunda...", [f"Tema: {query}"], 0)
            
            research_results = self._conduct_enhanced_deep_research(
                query, max_sources, max_images, generate_report, task_id
            )
            
            # Generar informe final
            self._update_progress(95, "📊 Finalizando informe...", ["Compilando resultados finales"], 5)
            
            # Mostrar informe en consola si está disponible
            if research_results.get('console_report'):
                self._display_console_report(research_results['console_report'])
            
            self._update_progress(100, "✅ Investigación completada exitosamente", [
                f"Fuentes analizadas: {len(research_results.get('sources', []))}",
                f"Imágenes recopiladas: {len(research_results.get('images', []))}",
                f"Informe generado: {'Sí' if research_results.get('report_file') else 'No'}"
            ], 5)
            
            # Agregar datos de progreso a la respuesta
            final_result = {
                'query': query,
                'sources_analyzed': len(research_results.get('sources', [])),
                'images_collected': len(research_results.get('images', [])),
                'report_file': research_results.get('report_file'),
                'console_report': research_results.get('console_report'),
                'executive_summary': research_results.get('executive_summary'),
                'key_findings': research_results.get('key_findings'),
                'recommendations': research_results.get('recommendations'),
                'sources': research_results.get('sources', []),
                'images': research_results.get('images', []),
                'progress_data': {
                    'final_percentage': 100,
                    'total_steps': 6,
                    'completion_time': datetime.now().isoformat()
                },
                'success': True
            }
            
            return final_result
            
        except Exception as e:
            self._update_progress(0, f"❌ Error: {str(e)}", [], -1)
            return {
                'query': query,
                'error': str(e),
                'success': False
            }
        finally:
            # Desactivar el tracker
            self.progress_tracker.is_active = False
    
    def _conduct_enhanced_deep_research(self, query: str, max_sources: int, 
                                      max_images: int, generate_report: bool,
                                      task_id: str) -> Dict[str, Any]:
        """Realizar investigación profunda mejorada con progreso detallado"""
        
        # FASE 1: Búsqueda inicial
        self._update_progress(5, "🔍 Realizando búsqueda inicial...", [f"Consultando Tavily para: {query}"], 0)
        
        initial_search = self.tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=max_sources,
            include_answer=True
        )
        
        all_sources = []
        all_urls = []
        
        # Procesar resultados iniciales
        for result in initial_search.get('results', []):
            source_info = {
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'snippet': result.get('content', ''),
                'score': result.get('score', 0),
                'type': 'primary'
            }
            all_sources.append(source_info)
            all_urls.append(result.get('url', ''))
        
        self._update_progress(10, "📋 Búsqueda inicial completada", [
            f"Encontradas {len(all_sources)} fuentes iniciales",
            f"URLs: {', '.join(all_urls[:3])}..." if len(all_urls) > 3 else f"URLs: {', '.join(all_urls)}"
        ], 0)
        
        # FASE 2: Búsquedas específicas
        self._update_progress(15, "🔍 Realizando búsquedas específicas...", [], 1)
        
        specific_queries = [
            f"{query} definición concepto",
            f"{query} características principales",
            f"{query} ventajas beneficios",
            f"{query} desventajas riesgos limitaciones",
            f"{query} tendencias futuro 2025",
            f"{query} casos estudio ejemplos",
            f"{query} comparación alternativas"
        ]
        
        sources_needed = max_sources - len(all_sources)
        queries_to_use = specific_queries[:max(3, sources_needed // 2)]
        
        for i, specific_query in enumerate(queries_to_use):
            progress = 15 + (i * 10)
            self._update_progress(progress, f"🔍 Búsqueda específica {i+1}/{len(queries_to_use)}", [
                f"Consultando: {specific_query}"
            ], 1)
            
            try:
                specific_results = self.tavily_client.search(
                    query=specific_query,
                    search_depth="basic",
                    max_results=3,
                    include_answer=True
                )
                
                new_urls = []
                for result in specific_results.get('results', []):
                    url = result.get('url', '')
                    if url not in all_urls:  # Evitar duplicados
                        source_info = {
                            'title': result.get('title', ''),
                            'url': url,
                            'snippet': result.get('content', ''),
                            'score': result.get('score', 0),
                            'type': 'specific'
                        }
                        all_sources.append(source_info)
                        all_urls.append(url)
                        new_urls.append(url)
                
                if new_urls:
                    self._update_progress(progress + 2, f"✅ Nuevas fuentes encontradas", new_urls[:2], 1)
                    
            except Exception as e:
                print(f"Error en búsqueda específica: {e}")
                continue
        
        # FASE 3: Extracción de contenido completo
        self._update_progress(45, "📄 Extrayendo contenido completo...", [
            f"Procesando {len(all_sources[:10])} fuentes principales"
        ], 2)
        
        extracted_content = []
        for i, source in enumerate(all_sources[:10]):  # Limitar a 10 para no sobrecargar
            progress = 45 + (i * 3)
            self._update_progress(progress, f"📄 Extrayendo contenido {i+1}/10", [
                f"Procesando: {source['title'][:50]}..."
            ], 2)
            
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
        
        # FASE 4: Recopilación de imágenes
        self._update_progress(75, "🖼️ Recopilando imágenes relacionadas...", [
            f"Buscando {max_images} imágenes sobre: {query}"
        ], 3)
        
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
            
            self._update_progress(80, "🖼️ Imágenes recopiladas", [
                f"Encontradas {len(images)} imágenes",
                f"Fuentes: {', '.join(set([img['source'] for img in images[:3]]))}"
            ])
            
        except Exception as e:
            print(f"Error recopilando imágenes: {e}")
            images = []
        
        # FASE 5: Análisis comparativo
        self._update_progress(85, "🔍 Comparando artículos y analizando...", [
            "Identificando patrones y tendencias",
            "Extrayendo hallazgos clave"
        ])
        
        # Combinar todo el contenido
        all_content = []
        for source in all_sources:
            all_content.append(source['snippet'])
        
        for content in extracted_content:
            all_content.append(content['full_content'])
        
        combined_content = "\n".join(all_content)
        
        # Generar análisis
        executive_summary = self._generate_executive_summary(query, combined_content, len(all_sources))
        key_findings = self._extract_comprehensive_findings(combined_content, extracted_content)
        recommendations = self._generate_actionable_recommendations(query, key_findings)
        
        # FASE 6: Generación de informe
        self._update_progress(90, "📊 Generando informe completo...", [
            "Compilando resultados",
            "Creando informe.md"
        ])
        
        report_file = None
        console_report = None
        
        if generate_report:
            report_content = self._generate_markdown_report(
                query, executive_summary, key_findings, recommendations,
                all_sources, images, extracted_content
            )
            
            # Guardar archivo
            report_file = self._save_report_file(report_content, task_id, query)
            
            # Generar reporte para consola
            console_report = self._generate_console_report(
                query, executive_summary, key_findings, recommendations,
                len(all_sources), len(images)
            )
        
        return {
            'sources': all_sources,
            'images': images,
            'extracted_content': extracted_content,
            'executive_summary': executive_summary,
            'key_findings': key_findings,
            'recommendations': recommendations,
            'report_file': report_file,
            'console_report': console_report
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
            
            # Limitar a 5000 caracteres para evitar sobrecarga
            if len(clean_text) > 5000:
                clean_text = clean_text[:5000] + '...'
            
            return clean_text
            
        except Exception as e:
            print(f"Error extrayendo contenido: {e}")
            return ""
    
    def _generate_executive_summary(self, query: str, content: str, source_count: int) -> str:
        """Generar resumen ejecutivo"""
        sentences = content.split('.')
        important_sentences = []
        
        keywords = ['importante', 'clave', 'fundamental', 'esencial', 'crítico', 'significativo', 'principal']
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                if len(sentence.strip()) > 30:
                    important_sentences.append(sentence.strip())
        
        summary = f"""
Basado en el análisis de {source_count} fuentes especializadas, {query} representa un tema de gran relevancia actual. 
Las fuentes consultadas proporcionan una visión comprehensiva que incluye aspectos fundamentales, tendencias emergentes y consideraciones prácticas.

Principales hallazgos:
""" + '\n'.join([f"• {sent}" for sent in important_sentences[:5]])
        
        return summary.strip()
    
    def _extract_comprehensive_findings(self, content: str, extracted_content: List[Dict]) -> List[str]:
        """Extraer hallazgos comprehensivos"""
        findings = []
        
        # Analizar contenido combinado
        sentences = content.split('.')
        
        # Palabras clave para identificar hallazgos importantes
        finding_keywords = ['descubrimiento', 'hallazgo', 'resultado', 'concluye', 'determina', 'revela', 'demuestra']
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in finding_keywords):
                if len(sentence.strip()) > 25:
                    findings.append(sentence.strip())
        
        # Agregar hallazgos específicos del contenido extraído
        for content_item in extracted_content:
            if content_item['word_count'] > 100:
                findings.append(f"Análisis detallado disponible en: {content_item['title']}")
        
        return findings[:10]
    
    def _generate_actionable_recommendations(self, query: str, findings: List[str]) -> List[str]:
        """Generar recomendaciones accionables"""
        recommendations = [
            "Continuar monitoreando fuentes especializadas para actualizaciones",
            "Validar información con expertos del área específica",
            "Implementar sistema de seguimiento de tendencias identificadas",
            "Considerar factores contextuales específicos para la aplicación",
            "Evaluar impacto potencial en diferentes escenarios"
        ]
        
        # Recomendaciones específicas por tema
        if any(word in query.lower() for word in ['negocio', 'empresa', 'marketing', 'comercial']):
            recommendations.extend([
                "Realizar análisis de competencia específico",
                "Evaluar oportunidades de mercado identificadas",
                "Desarrollar estrategia basada en hallazgos clave"
            ])
        
        if any(word in query.lower() for word in ['tecnología', 'digital', 'software', 'AI', 'artificial']):
            recommendations.extend([
                "Evaluar impacto tecnológico en el sector",
                "Considerar implementación gradual de soluciones",
                "Monitorear adoption rates y user feedback"
            ])
        
        return recommendations[:8]
    
    def _generate_markdown_report(self, query: str, executive_summary: str, 
                                key_findings: List[str], recommendations: List[str],
                                sources: List[Dict], images: List[Dict], 
                                extracted_content: List[Dict]) -> str:
        """Generar informe completo en formato Markdown"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# 📊 INFORME DE INVESTIGACIÓN PROFUNDA: {query.upper()}

**Fecha de generación:** {timestamp}  
**Fuentes analizadas:** {len(sources)}  
**Imágenes recopiladas:** {len(images)}  
**Contenido extraído:** {len(extracted_content)} páginas completas

---

## 🎯 RESUMEN EJECUTIVO

{executive_summary}

---

## 🔍 HALLAZGOS CLAVE

"""
        
        for i, finding in enumerate(key_findings, 1):
            report += f"{i}. {finding}\n\n"
        
        report += f"""---

## 💡 RECOMENDACIONES

"""
        
        for i, recommendation in enumerate(recommendations, 1):
            report += f"{i}. {recommendation}\n\n"
        
        report += f"""---

## 📚 FUENTES CONSULTADAS

"""
        
        for i, source in enumerate(sources, 1):
            report += f"### {i}. {source['title']}\n"
            report += f"**URL:** {source['url']}\n"
            report += f"**Tipo:** {source['type']}\n"
            report += f"**Resumen:** {source['snippet'][:200]}...\n\n"
        
        if images:
            report += f"""---

## 🖼️ IMÁGENES RELACIONADAS

"""
            
            for i, image in enumerate(images, 1):
                report += f"### {i}. {image['title']}\n"
                report += f"**URL:** {image['url']}\n"
                report += f"**Fuente:** {image['source']}\n"
                report += f"**Dimensiones:** {image['width']}x{image['height']}\n\n"
        
        if extracted_content:
            report += f"""---

## 📄 CONTENIDO EXTRAÍDO COMPLETO

"""
            
            for i, content in enumerate(extracted_content, 1):
                report += f"### {i}. {content['title']}\n"
                report += f"**URL:** {content['url']}\n"
                report += f"**Palabras:** {content['word_count']}\n\n"
                report += f"**Contenido:**\n{content['full_content'][:1000]}...\n\n"
        
        report += f"""---

## 📊 METODOLOGÍA

- **Búsqueda inicial:** Tavily API con profundidad avanzada
- **Búsquedas específicas:** Múltiples queries especializadas
- **Extracción de contenido:** Análisis completo de páginas principales
- **Recopilación de imágenes:** DuckDuckGo Image Search
- **Análisis comparativo:** Identificación de patrones y tendencias
- **Generación de informe:** Compilación automatizada de resultados

---

*Informe generado automáticamente por Enhanced Deep Research Tool*
"""
        
        return report
    
    def _save_report_file(self, content: str, task_id: str, query: str) -> str:
        """Guardar archivo de informe"""
        try:
            # Crear directorio si no existe
            reports_dir = f"/app/backend/reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            # Nombre de archivo
            safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"informe_{safe_query.replace(' ', '_')[:30]}_{task_id[:8]}.md"
            filepath = os.path.join(reports_dir, filename)
            
            # Guardar archivo
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return filepath
            
        except Exception as e:
            print(f"Error guardando informe: {e}")
            return None
    
    def _generate_console_report(self, query: str, executive_summary: str,
                               key_findings: List[str], recommendations: List[str],
                               source_count: int, image_count: int) -> str:
        """Generar informe formateado para consola"""
        
        report = f"""
{'='*80}
🔬 INFORME DE INVESTIGACIÓN PROFUNDA - {query.upper()}
{'='*80}

📊 ESTADÍSTICAS:
  • Fuentes analizadas: {source_count}
  • Imágenes recopiladas: {image_count}
  • Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{'='*80}
🎯 RESUMEN EJECUTIVO
{'='*80}

{executive_summary}

{'='*80}
🔍 HALLAZGOS CLAVE
{'='*80}

"""
        
        for i, finding in enumerate(key_findings, 1):
            report += f"{i:2d}. {finding}\n\n"
        
        report += f"""{'='*80}
💡 RECOMENDACIONES
{'='*80}

"""
        
        for i, recommendation in enumerate(recommendations, 1):
            report += f"{i:2d}. {recommendation}\n\n"
        
        report += f"""{'='*80}
✅ INVESTIGACIÓN COMPLETADA EXITOSAMENTE
{'='*80}
"""
        
        return report
    
    def _display_console_report(self, report: str):
        """Mostrar informe en consola con formato atractivo"""
        print("\n" + "🔬" * 40)
        print(report)
        print("🔬" * 40 + "\n")