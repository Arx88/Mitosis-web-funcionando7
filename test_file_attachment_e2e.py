#!/usr/bin/env python3
"""
TEST INTEGRAL DE EXTREMO A EXTREMO - ARCHIVO ADJUNTO
====================================================

Este test diagnostica por qué los archivos adjuntos no se muestran correctamente
en el chat después de ser subidos. Replica el flujo completo de usuario para 
identificar exactamente dónde falla la lógica.

Problema reportado:
- Los archivos se suben exitosamente al backend
- Pero NO aparecen con iconos coloridos, dropdowns y botones de acción en el chat
- Los componentes EnhancedFileDisplay y FileUploadSuccess no se renderizan

Este test verifica:
1. Backend: APIs de upload y creación de archivos
2. Frontend: Detección de mensajes de éxito y renderizado de componentes
3. Integración: Flujo completo desde upload hasta visualización
"""

import asyncio
import aiohttp
import json
import os
import tempfile
import time
from datetime import datetime
from playwright.async_api import async_playwright
import sys

# Configuración
BACKEND_URL = "http://localhost:8001"
FRONTEND_URL = "https://d26b60d3-abd6-4714-88af-d65f3f002095.preview.emergentagent.com"
TEST_TASK_ID = f"test-task-{int(time.time())}"

class FileAttachmentE2ETest:
    def __init__(self):
        self.session = None
        self.page = None
        self.browser = None
        self.test_results = {
            "backend_apis": {},
            "frontend_components": {},
            "integration_flow": {},
            "logs": [],
            "errors": []
        }
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.test_results["logs"].append(log_entry)
    
    def error(self, message):
        self.log(message, "ERROR")
        self.test_results["errors"].append(message)
    
    async def setup(self):
        """Configurar sesión HTTP y navegador"""
        self.log("🚀 Iniciando test integral de archivos adjuntos")
        
        # Configurar sesión HTTP para APIs
        self.session = aiohttp.ClientSession()
        
        # Configurar navegador para frontend
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        
        # Configurar captura de logs del navegador
        self.page.on("console", self._handle_console_log)
        self.page.on("pageerror", self._handle_page_error)
        
        self.log("✅ Setup completado")
    
    async def _handle_console_log(self, msg):
        """Capturar logs del navegador"""
        if any(keyword in msg.text for keyword in [
            "FILE UPLOAD", "FileUploadSuccess", "EnhancedFileDisplay", 
            "🎯", "🔍", "📁", "archivo", "cargado"
        ]):
            self.log(f"🌐 CONSOLE: {msg.text}")
    
    async def _handle_page_error(self, error):
        """Capturar errores del navegador"""
        self.error(f"🌐 PAGE ERROR: {error}")
    
    async def test_backend_file_upload_api(self):
        """Test 1: Verificar que la API de upload del backend funciona"""
        self.log("\n📤 TEST 1: Backend File Upload API")
        
        try:
            # Crear archivo de prueba
            test_content = f"""Archivo de prueba E2E
Timestamp: {datetime.now().isoformat()}
Task ID: {TEST_TASK_ID}
Propósito: Test integral de archivos adjuntos

Este archivo debe aparecer en el chat con:
- Icono colorido según tipo de archivo
- Menú dropdown con 3 puntos
- Botones: Ver archivo, Descargar, Eliminar, Memoria
"""
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_content)
                test_file_path = f.name
            
            # Preparar datos para upload
            with open(test_file_path, 'rb') as f:
                form_data = aiohttp.FormData()
                form_data.add_field('task_id', TEST_TASK_ID)
                form_data.add_field('files', f, filename='test_archivo_adjunto.txt', 
                                  content_type='text/plain')
                
                # Ejecutar upload
                async with self.session.post(
                    f"{BACKEND_URL}/api/agent/upload-files",
                    data=form_data
                ) as response:
                    response_data = await response.json()
                    
                    # Verificar respuesta
                    success = response.status == 200 and response_data.get('success', False)
                    files_count = len(response_data.get('files', []))
                    
                    self.test_results["backend_apis"]["upload"] = {
                        "success": success,
                        "status_code": response.status,
                        "files_uploaded": files_count,
                        "response_structure": {
                            "has_success": 'success' in response_data,
                            "has_files": 'files' in response_data,
                            "has_message": 'message' in response_data,
                            "has_upload_data": 'upload_data' in response_data
                        },
                        "first_file_metadata": response_data.get('files', [{}])[0] if files_count > 0 else {}
                    }
                    
                    if success:
                        self.log(f"✅ Upload exitoso: {files_count} archivo(s)")
                        self.log(f"   📄 Estructura: {response_data.get('files', [{}])[0].get('name', 'N/A')}")
                        self.log(f"   📊 Tamaño: {response_data.get('files', [{}])[0].get('size', 'N/A')} bytes")
                    else:
                        self.error(f"❌ Upload falló: {response.status} - {response_data}")
            
            # Limpiar archivo temporal
            os.unlink(test_file_path)
            
        except Exception as e:
            self.error(f"❌ Error en test de upload: {str(e)}")
            self.test_results["backend_apis"]["upload"] = {"error": str(e)}
    
    async def test_backend_deepresearch_files(self):
        """Test 2: Verificar que DeepResearch crea archivos correctamente"""
        self.log("\n🔬 TEST 2: Backend DeepResearch File Creation")
        
        try:
            # Ejecutar consulta DeepResearch
            query_data = {
                "message": "[DeepResearch] test de archivos adjuntos",
                "context": {"task_id": TEST_TASK_ID},
                "search_mode": "deepsearch"
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/api/agent/chat",
                json=query_data
            ) as response:
                response_data = await response.json()
                
                # Verificar respuesta
                success = response.status == 200
                created_files = response_data.get('created_files', [])
                search_mode = response_data.get('search_mode')
                
                self.test_results["backend_apis"]["deepresearch"] = {
                    "success": success,
                    "status_code": response.status,
                    "search_mode": search_mode,
                    "files_created": len(created_files),
                    "created_files_structure": created_files,
                    "has_search_data": 'search_data' in response_data,
                    "response_keys": list(response_data.keys())
                }
                
                if success and created_files:
                    self.log(f"✅ DeepResearch exitoso: {len(created_files)} archivo(s) creado(s)")
                    for i, file_info in enumerate(created_files):
                        self.log(f"   📄 Archivo {i+1}: {file_info.get('name', 'N/A')}")
                        self.log(f"      💾 Tamaño: {file_info.get('size', 'N/A')} bytes")
                        self.log(f"      🏷️  Tipo: {file_info.get('mime_type', 'N/A')}")
                        self.log(f"      🎯 Source: {file_info.get('source', 'N/A')}")
                else:
                    self.error(f"❌ DeepResearch no creó archivos: {response_data}")
                    
        except Exception as e:
            self.error(f"❌ Error en test de DeepResearch: {str(e)}")
            self.test_results["backend_apis"]["deepresearch"] = {"error": str(e)}
    
    async def test_frontend_navigation(self):
        """Test 3: Navegar al frontend y crear tarea"""
        self.log("\n🌐 TEST 3: Frontend Navigation and Task Creation")
        
        try:
            # Navegar a la aplicación
            await self.page.goto(FRONTEND_URL)
            await self.page.wait_for_load_state('networkidle')
            
            # Esperar a que la interfaz esté lista
            await self.page.wait_for_selector('[data-testid="main-app"], .flex', timeout=10000)
            
            # Buscar y hacer clic en "Nueva tarea"
            new_task_selectors = [
                "text=Nueva tarea",
                "text=Nueva Tarea", 
                "button:has-text('Nueva')",
                "[data-testid='new-task']",
                ".lucide-plus"
            ]
            
            task_created = False
            for selector in new_task_selectors:
                try:
                    await self.page.click(selector, timeout=2000)
                    task_created = True
                    self.log(f"✅ Tarea creada con selector: {selector}")
                    break
                except:
                    continue
            
            if not task_created:
                # Intentar crear tarea manualmente en input
                input_selectors = ["input", "textarea", "[contenteditable]"]
                for selector in input_selectors:
                    try:
                        await self.page.fill(selector, "Test archivo adjunto E2E")
                        await self.page.press(selector, "Enter")
                        task_created = True
                        self.log(f"✅ Tarea creada vía input: {selector}")
                        break
                    except:
                        continue
            
            # Esperar a que aparezca la interfaz de chat
            await self.page.wait_for_timeout(2000)
            
            self.test_results["frontend_components"]["navigation"] = {
                "page_loaded": True,
                "task_created": task_created,
                "url": self.page.url
            }
            
            if task_created:
                self.log("✅ Navegación exitosa y tarea creada")
            else:
                self.error("❌ No se pudo crear tarea")
                
        except Exception as e:
            self.error(f"❌ Error en navegación frontend: {str(e)}")
            self.test_results["frontend_components"]["navigation"] = {"error": str(e)}
    
    async def test_frontend_file_upload_modal(self):
        """Test 4: Probar el modal de upload de archivos"""
        self.log("\n📎 TEST 4: Frontend File Upload Modal")
        
        try:
            # Buscar botón de adjuntar (paperclip)
            attach_selectors = [
                ".lucide-paperclip",
                "[data-testid='attach-button']",
                "button:has(.lucide-paperclip)",
                "svg[data-lucide='paperclip']"
            ]
            
            modal_opened = False
            for selector in attach_selectors:
                try:
                    await self.page.click(selector, timeout=2000)
                    # Verificar si se abre el modal
                    await self.page.wait_for_selector("text=Subir Archivos", timeout=3000)
                    modal_opened = True
                    self.log(f"✅ Modal abierto con selector: {selector}")
                    break
                except:
                    continue
            
            if modal_opened:
                # Verificar elementos del modal
                modal_elements = {
                    "title": await self.page.is_visible("text=Subir Archivos"),
                    "drag_drop_zone": await self.page.is_visible("text=Arrastra archivos"),
                    "file_input": await self.page.locator("input[type='file']").count() > 0,
                    "close_button": await self.page.is_visible(".lucide-x")
                }
                
                self.test_results["frontend_components"]["upload_modal"] = {
                    "opened": True,
                    "elements": modal_elements
                }
                
                self.log("✅ Modal de upload funcional")
                
                # Cerrar modal
                await self.page.click(".lucide-x")
                
            else:
                self.error("❌ No se pudo abrir modal de upload")
                self.test_results["frontend_components"]["upload_modal"] = {
                    "opened": False,
                    "attach_button_found": await self.page.locator(".lucide-paperclip").count() > 0
                }
                
        except Exception as e:
            self.error(f"❌ Error en test de modal: {str(e)}")
            self.test_results["frontend_components"]["upload_modal"] = {"error": str(e)}
    
    async def test_frontend_deepresearch_execution(self):
        """Test 5: Ejecutar DeepResearch y monitorear componentes"""
        self.log("\n🔬 TEST 5: Frontend DeepResearch Execution")
        
        try:
            # Encontrar input de chat
            input_selectors = [
                "textarea",
                "input[placeholder*='Describe']",
                "[contenteditable='true']",
                ".vanish-input textarea"
            ]
            
            input_found = False
            for selector in input_selectors:
                try:
                    await self.page.fill(selector, "[DeepResearch] archivos adjuntos test")
                    await self.page.press(selector, "Enter")
                    input_found = True
                    self.log(f"✅ Consulta enviada con selector: {selector}")
                    break
                except:
                    continue
            
            if not input_found:
                self.error("❌ No se encontró input de chat")
                return
            
            # Monitorear componentes que deberían aparecer
            self.log("🔍 Monitoreando aparición de componentes...")
            
            components_to_monitor = {
                "success_message": "text=/.*archivo.*cargado.*exitosamente.*/i",
                "enhanced_file_display": "[data-testid='enhanced-file-display'], .enhanced-file-display",
                "file_upload_success": "[data-testid='file-upload-success'], .file-upload-success",
                "file_upload_parser": "[data-testid='file-upload-parser'], .file-upload-parser",
                "dropdown_triggers": ".lucide-more-horizontal, [data-testid='file-actions-dropdown']",
                "colored_file_icons": ".lucide-file-text, .lucide-image, .lucide-code",
                "action_buttons": "text=Ver archivo, text=Descargar, text=Eliminar, text=Memoria"
            }
            
            # Esperar hasta 30 segundos por la respuesta
            await self.page.wait_for_timeout(30000)
            
            # Verificar componentes
            component_results = {}
            for component_name, selector in components_to_monitor.items():
                try:
                    count = await self.page.locator(selector).count()
                    is_visible = count > 0
                    component_results[component_name] = {
                        "found": is_visible,
                        "count": count
                    }
                    
                    if is_visible:
                        self.log(f"✅ {component_name}: {count} encontrado(s)")
                    else:
                        self.log(f"❌ {component_name}: NO encontrado")
                        
                except Exception as e:
                    component_results[component_name] = {"error": str(e)}
                    self.error(f"❌ Error verificando {component_name}: {str(e)}")
            
            # Verificar mensajes en el chat
            chat_content = await self.page.text_content("body")
            has_success_indicators = any(keyword in chat_content.lower() for keyword in [
                "archivo", "cargado", "exitosamente", "✅", "disponible"
            ])
            
            self.test_results["frontend_components"]["deepresearch_execution"] = {
                "input_found": input_found,
                "query_sent": input_found,
                "components": component_results,
                "has_success_indicators": has_success_indicators,
                "chat_content_sample": chat_content[:500] if chat_content else None
            }
            
            if has_success_indicators:
                self.log("✅ Se detectaron indicadores de éxito en el chat")
            else:
                self.error("❌ NO se detectaron indicadores de éxito")
                
        except Exception as e:
            self.error(f"❌ Error en test de DeepResearch frontend: {str(e)}")
            self.test_results["frontend_components"]["deepresearch_execution"] = {"error": str(e)}
    
    async def test_debug_javascript_state(self):
        """Test 6: Inspeccionar estado JavaScript del frontend"""
        self.log("\n🔍 TEST 6: JavaScript State Debug")
        
        try:
            # Ejecutar JavaScript para inspeccionar estado
            debug_result = await self.page.evaluate("""
                () => {
                    const debug = {
                        components: {},
                        dom_elements: {},
                        react_components: {},
                        console_logs: []
                    };
                    
                    // Buscar componentes específicos en el DOM
                    debug.dom_elements.enhanced_file_display = document.querySelectorAll('.enhanced-file-display, [data-testid="enhanced-file-display"]').length;
                    debug.dom_elements.file_upload_success = document.querySelectorAll('.file-upload-success, [data-testid="file-upload-success"]').length;
                    debug.dom_elements.file_upload_parser = document.querySelectorAll('.file-upload-parser, [data-testid="file-upload-parser"]').length;
                    debug.dom_elements.dropdown_triggers = document.querySelectorAll('.lucide-more-horizontal').length;
                    debug.dom_elements.file_icons = document.querySelectorAll('.lucide-file-text, .lucide-image, .lucide-code').length;
                    debug.dom_elements.success_messages = document.querySelectorAll('*').length > 0 ? 
                        Array.from(document.querySelectorAll('*')).filter(el => 
                            el.textContent && el.textContent.includes('archivo') && 
                            (el.textContent.includes('cargado') || el.textContent.includes('exitosamente'))
                        ).length : 0;
                    
                    // Buscar elementos de React
                    debug.react_components = {
                        react_root: !!document.getElementById('root'),
                        has_react_fiber: !!document.querySelector('[data-reactroot]') || 
                                       !!document.querySelector('#root')?.hasAttribute('data-reactroot'),
                        chat_interface: document.querySelectorAll('.chat-interface, [data-id]').length
                    };
                    
                    // Capturar logs recientes del console
                    if (window.console && window.console.logs) {
                        debug.console_logs = window.console.logs.slice(-10);
                    }
                    
                    return debug;
                }
            """)
            
            self.test_results["frontend_components"]["javascript_debug"] = debug_result
            
            self.log("🔍 Estado JavaScript capturado:")
            self.log(f"   📊 DOM Elements: {debug_result['dom_elements']}")
            self.log(f"   ⚛️  React Components: {debug_result['react_components']}")
            
            # Verificar si los componentes críticos están presentes
            critical_components = debug_result['dom_elements']
            if critical_components['enhanced_file_display'] == 0:
                self.error("❌ CRÍTICO: EnhancedFileDisplay NO encontrado en DOM")
            if critical_components['file_upload_success'] == 0:
                self.error("❌ CRÍTICO: FileUploadSuccess NO encontrado en DOM")
            if critical_components['dropdown_triggers'] == 0:
                self.error("❌ CRÍTICO: Dropdown triggers NO encontrados en DOM")
                
        except Exception as e:
            self.error(f"❌ Error en debug JavaScript: {str(e)}")
            self.test_results["frontend_components"]["javascript_debug"] = {"error": str(e)}
    
    async def test_integration_flow_analysis(self):
        """Test 7: Análisis del flujo de integración completo"""
        self.log("\n🔄 TEST 7: Integration Flow Analysis")
        
        # Analizar resultados de tests anteriores
        backend_upload_success = self.test_results.get("backend_apis", {}).get("upload", {}).get("success", False)
        backend_deepresearch_success = self.test_results.get("backend_apis", {}).get("deepresearch", {}).get("success", False)
        frontend_modal_works = self.test_results.get("frontend_components", {}).get("upload_modal", {}).get("opened", False)
        frontend_components_render = any(
            comp.get("found", False) for comp in 
            self.test_results.get("frontend_components", {}).get("deepresearch_execution", {}).get("components", {}).values()
            if isinstance(comp, dict)
        )
        
        # Identificar punto de falla
        failure_point = "unknown"
        if not backend_upload_success and not backend_deepresearch_success:
            failure_point = "backend_apis"
        elif not frontend_modal_works:
            failure_point = "frontend_upload_modal"
        elif not frontend_components_render:
            failure_point = "frontend_component_rendering"
        else:
            failure_point = "integration_logic"
        
        # Generar diagnóstico
        diagnosis = {
            "backend_upload_working": backend_upload_success,
            "backend_deepresearch_working": backend_deepresearch_success,
            "frontend_modal_working": frontend_modal_works,
            "frontend_components_rendering": frontend_components_render,
            "failure_point": failure_point,
            "recommended_fixes": []
        }
        
        # Generar recomendaciones
        if failure_point == "backend_apis":
            diagnosis["recommended_fixes"].extend([
                "Verificar que el backend esté ejecutándose en puerto 8001",
                "Revisar logs del backend para errores en APIs",
                "Verificar conexión con MongoDB y sistema de archivos"
            ])
        elif failure_point == "frontend_upload_modal":
            diagnosis["recommended_fixes"].extend([
                "Verificar que el botón de adjuntar esté correctamente wired",
                "Revisar estado showFileUpload en ChatInterface",
                "Verificar que FileUploadModal se renderice cuando showFileUpload=true"
            ])
        elif failure_point == "frontend_component_rendering":
            diagnosis["recommended_fixes"].extend([
                "Revisar lógica de FileUploadParser en ChatInterface.tsx líneas 592-629",
                "Verificar condiciones para renderizar FileUploadSuccess y EnhancedFileDisplay",
                "Verificar que los mensajes de éxito tengan la estructura correcta",
                "Revisar que los archivos en attachments/created_files tengan metadatos completos"
            ])
        elif failure_point == "integration_logic":
            diagnosis["recommended_fixes"].extend([
                "Revisar comunicación entre backend y frontend",
                "Verificar que las variables de entorno REACT_APP_BACKEND_URL estén correctas",
                "Revisar que los IDs de tarea se mantengan consistentes",
                "Verificar logs del navegador para errores JavaScript"
            ])
        
        self.test_results["integration_flow"]["diagnosis"] = diagnosis
        
        self.log("🔄 DIAGNÓSTICO INTEGRAL:")
        self.log(f"   🔧 Backend Upload: {'✅' if backend_upload_success else '❌'}")
        self.log(f"   🔬 Backend DeepResearch: {'✅' if backend_deepresearch_success else '❌'}")
        self.log(f"   📎 Frontend Modal: {'✅' if frontend_modal_works else '❌'}")
        self.log(f"   🎨 Frontend Components: {'✅' if frontend_components_render else '❌'}")
        self.log(f"   🎯 Punto de falla: {failure_point}")
        
        for fix in diagnosis["recommended_fixes"]:
            self.log(f"   💡 {fix}")
    
    async def generate_final_report(self):
        """Generar reporte final del test"""
        self.log("\n📋 GENERANDO REPORTE FINAL...")
        
        # Calcular estadísticas
        total_tests = 7
        backend_tests_passed = sum(1 for result in self.test_results["backend_apis"].values() 
                                 if isinstance(result, dict) and result.get("success", False))
        frontend_tests_passed = sum(1 for result in self.test_results["frontend_components"].values() 
                                  if isinstance(result, dict) and not result.get("error"))
        
        # Generar reporte
        report = f"""
{'='*80}
REPORTE FINAL - TEST INTEGRAL DE ARCHIVOS ADJUNTOS
{'='*80}

🕒 Timestamp: {datetime.now().isoformat()}
🎯 Task ID de prueba: {TEST_TASK_ID}
📊 Total de tests: {total_tests}

RESUMEN DE RESULTADOS:
{'-'*40}
🔧 Backend APIs: {backend_tests_passed}/2 exitosos
🌐 Frontend Tests: {frontend_tests_passed}/{len(self.test_results["frontend_components"])} exitosos
❌ Errores encontrados: {len(self.test_results["errors"])}

DIAGNÓSTICO:
{'-'*40}
{json.dumps(self.test_results["integration_flow"].get("diagnosis", {}), indent=2, ensure_ascii=False)}

DETALLES TÉCNICOS:
{'-'*40}
Backend APIs:
{json.dumps(self.test_results["backend_apis"], indent=2, ensure_ascii=False)}

Frontend Components:
{json.dumps(self.test_results["frontend_components"], indent=2, ensure_ascii=False)}

LOGS COMPLETOS:
{'-'*40}
"""
        
        for log_entry in self.test_results["logs"]:
            report += f"{log_entry}\n"
        
        if self.test_results["errors"]:
            report += f"\nERRORES ENCONTRADOS:\n{'-'*20}\n"
            for error in self.test_results["errors"]:
                report += f"{error}\n"
        
        report += f"\n{'='*80}\n"
        
        # Guardar reporte
        report_path = f"/app/test_file_attachment_report_{int(time.time())}.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.log(f"📄 Reporte guardado en: {report_path}")
        print(report)
        
        return report_path
    
    async def cleanup(self):
        """Limpiar recursos"""
        self.log("🧹 Limpiando recursos...")
        
        if self.session:
            await self.session.close()
        
        if self.browser:
            await self.browser.close()
        
        self.log("✅ Cleanup completado")
    
    async def run_complete_test(self):
        """Ejecutar test completo"""
        try:
            await self.setup()
            
            # Ejecutar tests secuencialmente
            await self.test_backend_file_upload_api()
            await self.test_backend_deepresearch_files()
            await self.test_frontend_navigation()
            await self.test_frontend_file_upload_modal()
            await self.test_frontend_deepresearch_execution()
            await self.test_debug_javascript_state()
            await self.test_integration_flow_analysis()
            
            # Generar reporte final
            report_path = await self.generate_final_report()
            
            return report_path
            
        except Exception as e:
            self.error(f"❌ Error crítico en test: {str(e)}")
            raise
        finally:
            await self.cleanup()


async def main():
    """Función principal"""
    test = FileAttachmentE2ETest()
    
    try:
        report_path = await test.run_complete_test()
        print(f"\n🎉 Test completado. Reporte disponible en: {report_path}")
        return 0
    except Exception as e:
        print(f"\n💥 Test falló con error crítico: {str(e)}")
        return 1


if __name__ == "__main__":
    # Instalar dependencias si es necesario
    try:
        import aiohttp
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Dependencias faltantes. Instalando...")
        os.system("pip install aiohttp playwright")
        os.system("playwright install chromium")
        print("✅ Dependencias instaladas")
    
    # Ejecutar test
    exit_code = asyncio.run(main())
    sys.exit(exit_code)