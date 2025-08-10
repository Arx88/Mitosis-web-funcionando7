"""
🔍 NAVEGACIÓN WEB CON RECOLECCIÓN EN TIEMPO REAL
===============================================

Herramienta mejorada que combina navegación web with documentación en vivo
de toda la información recolectada, mostrando en tiempo real en el terminal
del taskview lo que el agente va encontrando.

Funcionalidades:
- ✅ Navegación web inteligente
- ✅ Documento .md que se actualiza en tiempo real
- ✅ Eventos de terminal para cada información recolectada
- ✅ Contenido completo de cada sitio visitado
"""

import asyncio
import time
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse

from .base_tool import BaseTool, ParameterDefinition, ToolExecutionResult, register_tool

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Importar sistema de documento en vivo
try:
    from ..services.documento_en_vivo import obtener_documento_en_vivo
    DOCUMENTO_EN_VIVO_AVAILABLE = True
except ImportError:
    DOCUMENTO_EN_VIVO_AVAILABLE = False

# Importar WebSocket manager
try:
    from ..websocket.websocket_manager import get_websocket_manager
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

logger = logging.getLogger(__name__)

@register_tool
class WebSearchConRecoleccionEnVivo(BaseTool):
    """
    🔍 BÚSQUEDA WEB CON RECOLECCIÓN DOCUMENTADA EN TIEMPO REAL
    
    Esta herramienta navega la web y documenta en tiempo real TODA la información
    que va recolectando, mostrando en el terminal del taskview cada sitio visitado
    y el contenido extraído.
    """
    
    def __init__(self):
        super().__init__(
            name="web_search_con_recoleccion",
            description="Búsqueda web inteligente con documentación en tiempo real de toda la información recolectada"
        )
        self.websocket_manager = None
        self.documento_en_vivo = None
        self.task_id = None
        self.max_sitios_config = 5
        
    def _define_parameters(self) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(
                name="query",
                param_type="string",
                required=True,
                description="Términos de búsqueda o consulta a investigar",
                min_value=3,
                max_value=200
            ),
            ParameterDefinition(
                name="max_sitios",
                param_type="integer",
                required=False,
                description="Máximo número de sitios a explorar y documentar",
                default=5,
                min_value=1,
                max_value=10
            ),
            ParameterDefinition(
                name="profundidad_contenido",
                param_type="string",
                required=False,
                description="Nivel de detalle en extracción",
                default="completo",
                enum=["basico", "completo", "exhaustivo"]
            )
        ]
    
    def _execute_tool(self, parameters: Dict[str, Any], config: Dict[str, Any] = None) -> ToolExecutionResult:
        """🚀 EJECUTAR BÚSQUEDA CON RECOLECCIÓN DOCUMENTADA EN TIEMPO REAL"""
        
        if not PLAYWRIGHT_AVAILABLE:
            return ToolExecutionResult(
                success=False,
                error="Playwright no está disponible. Se requiere para navegación web."
            )
        
        # Extraer parámetros
        query = parameters.get('query', '').strip()
        max_sitios = int(parameters.get('max_sitios', 5))
        profundidad = parameters.get('profundidad_contenido', 'completo')
        
        # Obtener task_id del config
        self.task_id = config.get('task_id') if config else f"search-{int(time.time())}"
        self.max_sitios_config = max_sitios
        
        # Inicializar sistemas
        self._inicializar_sistemas()
        
        try:
            # Ejecutar búsqueda con recolección documentada
            resultados = self._ejecutar_busqueda_con_documentacion(query, max_sitios, profundidad)
            
            # Finalizar documento
            if self.documento_en_vivo:
                resumen = self._generar_resumen_final(resultados)
                self.documento_en_vivo.finalizar_documento(resumen)
            
            return ToolExecutionResult(
                success=True,
                data={
                    'query': query,
                    'sitios_explorados': len(resultados.get('sitios_visitados', [])),
                    'contenido_total_caracteres': resultados.get('contenido_total_caracteres', 0),
                    'documento_path': self.documento_en_vivo.documento_path if self.documento_en_vivo else None,
                    'resultados_detallados': resultados,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda web con recolección: {e}")
            return ToolExecutionResult(
                success=False,
                error=f"Error en búsqueda web: {str(e)}"
            )
    
    def _inicializar_sistemas(self):
        """🔄 Inicializar WebSocket y documento en vivo."""
        try:
            # Inicializar WebSocket manager
            if WEBSOCKET_AVAILABLE:
                self.websocket_manager = get_websocket_manager()
                if self.websocket_manager:
                    logger.info("✅ WebSocket manager inicializado para recolección en vivo")
            
            # Inicializar documento en vivo
            if DOCUMENTO_EN_VIVO_AVAILABLE and self.task_id:
                self.documento_en_vivo = obtener_documento_en_vivo(self.task_id, self.websocket_manager)
                if self.documento_en_vivo:
                    logger.info(f"✅ Documento en vivo inicializado: {self.documento_en_vivo.documento_path}")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando sistemas: {e}")
    
    def _ejecutar_busqueda_con_documentacion(self, query: str, max_sitios: int, profundidad: str) -> Dict[str, Any]:
        """🌐 EJECUTAR BÚSQUEDA COMPLETA CON DOCUMENTACIÓN EN TIEMPO REAL"""
        
        # Actualizar estado inicial
        if self.documento_en_vivo:
            self.documento_en_vivo.actualizar_estado_navegacion(
                "Iniciando búsqueda web",
                f"Búsqueda: '{query}' | Sitios objetivo: {max_sitios} | Profundidad: {profundidad}"
            )
        
        # Crear nuevo event loop para evitar conflictos
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(
                self._busqueda_asincrona_con_documentacion(query, max_sitios, profundidad)
            )
        finally:
            loop.close()
    
    async def _busqueda_asincrona_con_documentacion(self, query: str, max_sitios: int, profundidad: str) -> Dict[str, Any]:
        """🎭 BÚSQUEDA ASÍNCRONA CON PLAYWRIGHT Y DOCUMENTACIÓN COMPLETA"""
        
        resultados = {
            'query': query,
            'sitios_visitados': [],
            'contenido_total_caracteres': 0,
            'timestamp_inicio': datetime.now().isoformat(),
            'timestamp_fin': None
        }
        
        async with async_playwright() as p:
            # Configurar navegador
            browser = await p.chromium.launch(
                headless=False,  # Navegación visible
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    f'--display={os.environ.get("DISPLAY", ":99")}',
                    '--window-size=1920,1080'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # Actualizar estado: navegando a Google
                if self.documento_en_vivo:
                    self.documento_en_vivo.actualizar_estado_navegacion(
                        "Navegando a Google",
                        "Preparando búsqueda inicial"
                    )
                
                # 1. Navegar a Google
                await page.goto('https://www.google.com', wait_until='networkidle')
                await asyncio.sleep(1)
                
                # 2. Realizar búsqueda
                await self._realizar_busqueda_google(page, query)
                
                # 3. Obtener enlaces de resultados
                enlaces_resultados = await self._obtener_enlaces_resultados(page)
                
                # 4. Explorar cada sitio y documentar contenido
                sitios_explorados = 0
                for i, enlace in enumerate(enlaces_resultados[:max_sitios]):
                    try:
                        if sitios_explorados >= max_sitios:
                            break
                        
                        sitio_info = await self._explorar_sitio_con_documentacion(
                            page, enlace, i + 1, profundidad
                        )
                        
                        if sitio_info:
                            resultados['sitios_visitados'].append(sitio_info)
                            resultados['contenido_total_caracteres'] += len(sitio_info.get('contenido', ''))
                            sitios_explorados += 1
                            
                            # Pequeña pausa entre sitios
                            await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"❌ Error explorando sitio {i+1}: {e}")
                        continue
                
                # Actualizar estado final
                if self.documento_en_vivo:
                    self.documento_en_vivo.actualizar_estado_navegacion(
                        "Búsqueda completada",
                        f"Se exploraron {sitios_explorados} sitios exitosamente"
                    )
                
                resultados['timestamp_fin'] = datetime.now().isoformat()
                return resultados
                
            finally:
                await context.close()
                await browser.close()
    
    async def _realizar_busqueda_google(self, page, query: str):
        """🔍 Realizar búsqueda en Google con documentación."""
        
        try:
            # Buscar campo de búsqueda
            search_input = await page.wait_for_selector('textarea[name="q"], input[name="q"]', timeout=5000)
            
            if self.documento_en_vivo:
                self.documento_en_vivo.actualizar_estado_navegacion(
                    "Escribiendo búsqueda",
                    f"Introduciendo términos: '{query}'"
                )
            
            # Escribir búsqueda
            await search_input.fill(query)
            await asyncio.sleep(1)
            await search_input.press('Enter')
            
            # Esperar resultados
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            logger.info(f"🔍 Búsqueda realizada para: {query}")
            
        except Exception as e:
            logger.error(f"❌ Error realizando búsqueda: {e}")
            raise
    
    async def _obtener_enlaces_resultados(self, page) -> List[Dict[str, str]]:
        """🔗 Obtener enlaces de resultados de búsqueda."""
        
        enlaces = []
        
        try:
            # Selectores para diferentes motores de búsqueda
            selectores_enlaces = [
                'h3 a',  # Google estándar
                '.g h3 a',  # Google específico
                '.b_algo h2 a',  # Bing
                '.result h3 a',  # Genérico
                'a[href*="http"]:has(h3)',  # Fallback
            ]
            
            for selector in selectores_enlaces:
                try:
                    elementos = await page.query_selector_all(selector)
                    if elementos:
                        for elemento in elementos[:15]:  # Máximo 15 enlaces
                            try:
                                href = await elemento.get_attribute('href')
                                texto = await elemento.text_content()
                                
                                if href and texto and 'google.com' not in href:
                                    enlaces.append({
                                        'url': href,
                                        'titulo': texto.strip(),
                                        'fuente': urlparse(href).netloc
                                    })
                            except:
                                continue
                        break  # Si encontramos enlaces con este selector, usar estos
                except:
                    continue
            
            if self.documento_en_vivo:
                self.documento_en_vivo.actualizar_estado_navegacion(
                    "Enlaces encontrados",
                    f"Se encontraron {len(enlaces)} enlaces para explorar"
                )
            
            logger.info(f"🔗 Se encontraron {len(enlaces)} enlaces de resultados")
            return enlaces
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo enlaces: {e}")
            return []
    
    async def _explorar_sitio_con_documentacion(self, page, enlace: Dict[str, str], 
                                               numero_sitio: int, profundidad: str) -> Optional[Dict[str, Any]]:
        """
        🌐 EXPLORAR SITIO INDIVIDUAL CON DOCUMENTACIÓN COMPLETA EN TIEMPO REAL
        
        Args:
            page: Página de Playwright
            enlace: Información del enlace (url, titulo, fuente)
            numero_sitio: Número del sitio en la secuencia
            profundidad: Nivel de extracción de contenido
            
        Returns:
            Información completa del sitio explorado
        """
        
        url = enlace['url']
        titulo_enlace = enlace['titulo']
        fuente = enlace['fuente']
        
        try:
            # Actualizar estado: navegando a sitio específico
            if self.documento_en_vivo:
                self.documento_en_vivo.actualizar_estado_navegacion(
                    f"Navegando a sitio {numero_sitio}/{self.max_sitios_config}",
                    f"🌐 Accediendo a: {fuente}"
                )
            
            logger.info(f"🌐 Navegando a sitio {numero_sitio}: {url}")
            
            # Navegar al sitio
            await page.goto(url, wait_until='networkidle', timeout=15000)
            await asyncio.sleep(2)
            
            # Obtener información básica del sitio
            titulo_pagina = await page.title()
            url_final = page.url  # Por si hubo redirects
            
            # Actualizar estado: extrayendo contenido
            if self.documento_en_vivo:
                self.documento_en_vivo.actualizar_estado_navegacion(
                    f"Extrayendo contenido de sitio {numero_sitio}",
                    f"📄 Procesando: {titulo_pagina[:50]}..."
                )
            
            # Extraer contenido según profundidad
            contenido_extraido = await self._extraer_contenido_completo(page, profundidad)
            
            # Obtener metadatos adicionales
            metadatos = await self._obtener_metadatos_sitio(page)
            
            # Crear información completa del sitio
            sitio_info = {
                'numero': numero_sitio,
                'url': url_final,
                'url_original': url,
                'titulo': titulo_pagina,
                'titulo_enlace': titulo_enlace,
                'fuente': fuente,
                'contenido': contenido_extraido,
                'caracteres': len(contenido_extraido),
                'timestamp': datetime.now().isoformat(),
                'metadatos': metadatos
            }
            
            # 🔥 PUNTO CLAVE: AGREGAR AL DOCUMENTO EN VIVO INMEDIATAMENTE
            if self.documento_en_vivo:
                self.documento_en_vivo.agregar_sitio_visitado(
                    url=url_final,
                    titulo=titulo_pagina,
                    contenido=contenido_extraido,
                    metadatos={
                        'numero_sitio': numero_sitio,
                        'fuente_dominio': fuente,
                        'url_original': url,
                        'titulo_enlace': titulo_enlace,
                        'metodo_extraccion': metadatos.get('metodo_extraccion', 'unknown'),
                        'tiempo_carga': metadatos.get('tiempo_carga', 0),
                        'profundidad': profundidad
                    }
                )
            
            logger.info(f"✅ Sitio {numero_sitio} documentado: {titulo_pagina} ({len(contenido_extraido)} chars)")
            
            return sitio_info
            
        except Exception as e:
            logger.error(f"❌ Error explorando sitio {numero_sitio} ({url}): {e}")
            
            # Documentar error también
            if self.documento_en_vivo:
                self.documento_en_vivo.agregar_sitio_visitado(
                    url=url,
                    titulo=f"ERROR: {titulo_enlace}",
                    contenido=f"No se pudo acceder al sitio debido a: {str(e)}",
                    metadatos={
                        'numero_sitio': numero_sitio,
                        'error': True,
                        'error_message': str(e),
                        'url_original': url
                    }
                )
            
            return None
    
    async def _extraer_contenido_completo(self, page, profundidad: str) -> str:
        """
        📄 EXTRAER CONTENIDO COMPLETO DE LA PÁGINA
        
        Args:
            page: Página de Playwright
            profundidad: Nivel de detalle ('basico', 'completo', 'exhaustivo')
            
        Returns:
            Contenido completo extraído de la página
        """
        
        try:
            # Script de extracción inteligente según profundidad
            if profundidad == "exhaustivo":
                max_chars = 8000
                selectors_extra = ['.abstract', '.intro', '.summary', '.conclusion']
            elif profundidad == "completo":
                max_chars = 5000
                selectors_extra = ['.summary', '.intro']
            else:  # basico
                max_chars = 2000
                selectors_extra = []
            
            contenido = await page.evaluate(f'''
                () => {{
                    let contenido = '';
                    let seccionesExtraidas = [];
                    
                    // 1. BUSCAR CONTENIDO PRINCIPAL DE ARTÍCULO
                    const selectoresPrincipales = [
                        'article', 'main', '[role="main"]', '.article', '.post',
                        '.content', '.entry-content', '.post-content', '.article-content',
                        '#content', '#main', '.main-content', '.page-content'
                    ];
                    
                    for (let selector of selectoresPrincipales) {{
                        const elemento = document.querySelector(selector);
                        if (elemento && elemento.innerText && elemento.innerText.length > 300) {{
                            contenido = elemento.innerText || elemento.textContent || '';
                            seccionesExtraidas.push(selector);
                            break;
                        }}
                    }}
                    
                    // 2. AGREGAR SECCIONES ESPECÍFICAS SEGÚN PROFUNDIDAD
                    const selectoresExtra = {json.dumps(selectors_extra)};
                    for (let selector of selectoresExtra) {{
                        const elemento = document.querySelector(selector);
                        if (elemento && elemento.innerText) {{
                            contenido += '\\n\\n=== ' + selector.toUpperCase() + ' ===\\n';
                            contenido += elemento.innerText;
                            seccionesExtraidas.push(selector);
                        }}
                    }}
                    
                    // 3. SI NO HAY CONTENIDO SUFICIENTE, EXTRAER PÁRRAFOS
                    if (!contenido || contenido.length < 500) {{
                        const parrafos = document.querySelectorAll('p, .paragraph, .text');
                        let contenidoParrafos = '';
                        for (let p of parrafos) {{
                            if (p.innerText && p.innerText.length > 50) {{
                                contenidoParrafos += p.innerText + '\\n\\n';
                                if (contenidoParrafos.length > 3000) break;
                            }}
                        }}
                        if (contenidoParrafos.length > contenido.length) {{
                            contenido = contenidoParrafos;
                            seccionesExtraidas.push('paragraphs');
                        }}
                    }}
                    
                    // 4. ÚLTIMO RECURSO: BODY COMPLETO FILTRADO
                    if (!contenido || contenido.length < 300) {{
                        contenido = document.body.innerText || document.body.textContent || '';
                        seccionesExtraidas.push('body-fallback');
                    }}
                    
                    // 5. LIMPIAR CONTENIDO
                    contenido = contenido.replace(/\\s+/g, ' ').trim();
                    
                    // Remover texto de navegación común
                    const textoNavegacion = [
                        'Skip to content', 'Menu', 'Navigation', 'Home', 'About', 'Contact',
                        'Privacy Policy', 'Terms', 'Cookie', 'Subscribe', 'Newsletter',
                        'Aceptar cookies', 'Política de privacidad', 'Menú', 'Inicio'
                    ];
                    
                    for (let navText of textoNavegacion) {{
                        contenido = contenido.replace(new RegExp(navText, 'gi'), '');
                    }}
                    
                    // 6. LIMITAR SEGÚN PROFUNDIDAD
                    const maxChars = {max_chars};
                    if (contenido.length > maxChars) {{
                        contenido = contenido.substring(0, maxChars) + '\\n\\n[CONTENIDO TRUNCADO - LÍMITE DE CARACTERES ALCANZADO]';
                    }}
                    
                    return {{
                        contenido: contenido,
                        longitud: contenido.length,
                        metodosExtraccion: seccionesExtraidas.join(', '),
                        calidad: contenido.length > 2000 ? 'alta' : contenido.length > 1000 ? 'media' : 'baja'
                    }};
                }}
            ''')
            
            # Extraer datos del resultado
            if isinstance(contenido, dict):
                texto_contenido = contenido.get('contenido', '')
            else:
                texto_contenido = contenido or ''
            
            logger.info(f"📄 Contenido extraído: {len(texto_contenido)} caracteres")
            return texto_contenido
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo contenido: {e}")
            return f"Error extrayendo contenido: {str(e)}"
    
    async def _obtener_metadatos_sitio(self, page) -> Dict[str, Any]:
        """📋 Obtener metadatos adicionales del sitio."""
        
        try:
            # Obtener metadatos básicos
            metadatos = await page.evaluate('''
                () => {
                    const meta = {};
                    
                    // Meta tags
                    const metaTags = document.querySelectorAll('meta');
                    for (let tag of metaTags) {
                        const name = tag.getAttribute('name') || tag.getAttribute('property');
                        const content = tag.getAttribute('content');
                        if (name && content) {
                            meta[name] = content;
                        }
                    }
                    
                    // Información adicional
                    return {
                        titulo: document.title,
                        descripcion: meta['description'] || meta['og:description'] || '',
                        autor: meta['author'] || meta['article:author'] || '',
                        fecha_publicacion: meta['article:published_time'] || meta['date'] || '',
                        idioma: document.documentElement.lang || 'unknown',
                        tipo_contenido: meta['og:type'] || 'website',
                        imagen_destacada: meta['og:image'] || '',
                        palabras_clave: meta['keywords'] || '',
                        url_canonica: document.querySelector('link[rel="canonical"]')?.href || window.location.href
                    };
                }
            ''')
            
            # Agregar timestamp y información técnica
            metadatos.update({
                'timestamp_extraccion': datetime.now().isoformat(),
                'tiempo_carga': time.time()
            })
            
            return metadatos
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo metadatos: {e}")
            return {
                'error': str(e),
                'timestamp_extraccion': datetime.now().isoformat()
            }
    
    def _generar_resumen_final(self, resultados: Dict[str, Any]) -> str:
        """📊 Generar resumen final de la recolección."""
        
        sitios_exitosos = len(resultados.get('sitios_visitados', []))
        total_caracteres = resultados.get('contenido_total_caracteres', 0)
        
        if sitios_exitosos == 0:
            return "❌ No se pudo recolectar información de ningún sitio web."
        
        promedio_caracteres = total_caracteres // sitios_exitosos if sitios_exitosos > 0 else 0
        
        # Obtener estadísticas de fuentes
        fuentes_unicas = set()
        for sitio in resultados.get('sitios_visitados', []):
            if sitio.get('fuente'):
                fuentes_unicas.add(sitio['fuente'])
        
        resumen = f"""
## 📊 ESTADÍSTICAS FINALES DE RECOLECCIÓN

### Resultados Generales
- ✅ **Sitios explorados exitosamente**: {sitios_exitosos}
- 🌐 **Fuentes únicas consultadas**: {len(fuentes_unicas)}
- 📄 **Total caracteres recolectados**: {total_caracteres:,}
- 📊 **Promedio por sitio**: {promedio_caracteres:,} caracteres

### Fuentes Consultadas
"""
        
        for fuente in sorted(fuentes_unicas):
            resumen += f"- 🔗 {fuente}\n"
        
        resumen += f"""
### Calidad de la Recolección
- ⭐ **Calidad general**: {'Excelente' if total_caracteres > 15000 else 'Buena' if total_caracteres > 8000 else 'Básica'}
- 🎯 **Diversidad de fuentes**: {'Alta' if len(fuentes_unicas) >= 4 else 'Media' if len(fuentes_unicas) >= 2 else 'Baja'}
- 📈 **Completitud**: {'Completa' if sitios_exitosos >= 4 else 'Parcial'}

### Tiempo de Ejecución
- 🕐 **Inicio**: {resultados.get('timestamp_inicio', 'N/A')}
- 🏁 **Fin**: {resultados.get('timestamp_fin', datetime.now().isoformat())}

**🎯 CONCLUSIÓN**: La recolección de información se completó {'exitosamente' if sitios_exitosos >= 3 else 'parcialmente'} con datos sustanciales de múltiples fuentes web."""
        
        return resumen
    
    def _emit_progress(self, message: str):
        """Emitir mensaje de progreso."""
        logger.info(message)
        if self.websocket_manager and self.task_id:
            try:
                self.websocket_manager.send_log_message(
                    task_id=self.task_id,
                    level="info",
                    message=message
                )
            except Exception as e:
                logger.error(f"❌ Error enviando progreso WebSocket: {e}")

# Función auxiliar para configurar la herramienta
def configurar_herramienta_con_documento(task_id: str, max_sitios: int = 5):
    """Configura la herramienta con parámetros específicos."""
    herramienta = WebSearchConRecoleccionEnVivo()
    herramienta.task_id = task_id
    herramienta.max_sitios_config = max_sitios
    return herramienta