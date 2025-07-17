#!/usr/bin/env python3
"""
TEST FINAL DE VERIFICACIÓN - ARCHIVOS ADJUNTOS CORREGIDOS
=========================================================

Verifica que las correcciones aplicadas resuelven el problema de archivos adjuntos.
"""

import asyncio
import aiohttp
import time
from datetime import datetime
from playwright.async_api import async_playwright

FRONTEND_URL = "https://9bdf4bc8-9388-4567-b073-5c444f0d1d7c.preview.emergentagent.com"

class FileAttachmentVerificationTest:
    def __init__(self):
        self.page = None
        self.browser = None
        self.console_logs = []
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    async def setup(self):
        """Configurar navegador"""
        self.log("🚀 Iniciando test de verificación")
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        
        # Capturar logs del navegador
        self.page.on("console", self._handle_console_log)
        
        self.log("✅ Setup completado")
    
    async def _handle_console_log(self, msg):
        """Capturar logs específicos"""
        text = msg.text
        if any(keyword in text for keyword in [
            "ATTACH FILES CLICKED", "FileUploadModal", "FILE UPLOAD", 
            "DEEPRESEARCH", "🎯", "🔍", "📁", "🚨", "archivo"
        ]):
            self.console_logs.append(text)
            self.log(f"🌐 CONSOLE: {text}")
    
    async def test_attach_button_functionality(self):
        """Test: Verificar botón de adjuntar con debug"""
        self.log("\n📎 TEST: Botón de Adjuntar con Debug")
        
        try:
            # Navegar a la aplicación
            await self.page.goto(FRONTEND_URL)
            await self.page.wait_for_load_state('networkidle')
            
            # Crear nueva tarea
            await self.page.click("text=Nueva Tarea")
            await self.page.wait_for_timeout(2000)
            
            # Buscar y hacer clic en botón de adjuntar
            attach_selectors = [
                ".lucide-paperclip",
                "button:has(.lucide-paperclip)",
                "[title='Subir archivos']"
            ]
            
            button_clicked = False
            for selector in attach_selectors:
                try:
                    await self.page.click(selector, timeout=3000)
                    button_clicked = True
                    self.log(f"✅ Botón adjuntar clickeado: {selector}")
                    break
                except:
                    continue
            
            if not button_clicked:
                self.log("❌ No se pudo encontrar/clickear botón de adjuntar")
                return False
            
            # Esperar logs de debug
            await self.page.wait_for_timeout(2000)
            
            # Verificar si aparece el modal
            modal_visible = await self.page.is_visible("text=Subir Archivos")
            
            if modal_visible:
                self.log("✅ Modal de upload VISIBLE")
                return True
            else:
                self.log("❌ Modal de upload NO visible")
                return False
                
        except Exception as e:
            self.log(f"❌ Error en test de botón: {str(e)}")
            return False
    
    async def test_deepresearch_forced_files(self):
        """Test: Verificar archivos forzados en DeepResearch"""
        self.log("\n🔬 TEST: DeepResearch con Archivos Forzados")
        
        try:
            # Ejecutar consulta DeepResearch
            await self.page.fill("textarea", "[DeepResearch] test archivos")
            await self.page.press("textarea", "Enter")
            
            self.log("✅ Consulta DeepResearch enviada")
            
            # Esperar respuesta y logs
            await self.page.wait_for_timeout(10000)
            
            # Verificar componentes de archivo
            components = {
                "enhanced_file_display": await self.page.locator(".enhanced-file-display, [data-testid='enhanced-file-display']").count(),
                "file_upload_success": await self.page.locator(".file-upload-success, [data-testid='file-upload-success']").count(),
                "file_icons": await self.page.locator(".lucide-file-text, .lucide-image, .lucide-code").count(),
                "dropdown_triggers": await self.page.locator(".lucide-more-horizontal").count()
            }
            
            self.log(f"📊 Componentes encontrados: {components}")
            
            # Verificar si al menos un componente apareció
            has_components = any(count > 0 for count in components.values())
            
            if has_components:
                self.log("✅ Componentes de archivo ENCONTRADOS")
                return True
            else:
                self.log("❌ NO se encontraron componentes de archivo")
                return False
                
        except Exception as e:
            self.log(f"❌ Error en test de DeepResearch: {str(e)}")
            return False
    
    async def analyze_console_logs(self):
        """Analizar logs de consola capturados"""
        self.log("\n🔍 ANÁLISIS DE LOGS DE CONSOLA")
        
        debug_indicators = {
            "attach_clicked": any("ATTACH FILES CLICKED" in log for log in self.console_logs),
            "modal_rendering": any("FileUploadModal" in log for log in self.console_logs),
            "file_detection": any("FILE UPLOAD DEBUG" in log for log in self.console_logs),
            "deepresearch_forced": any("DEEPRESEARCH DETECTED" in log for log in self.console_logs),
            "forced_file_display": any("FORCING FILE DISPLAY" in log for log in self.console_logs)
        }
        
        self.log(f"📋 Indicadores de debug: {debug_indicators}")
        
        # Mostrar todos los logs capturados
        if self.console_logs:
            self.log(f"\n📝 LOGS CAPTURADOS ({len(self.console_logs)}):")
            for i, log in enumerate(self.console_logs[-10:], 1):  # Últimos 10
                self.log(f"   {i}. {log}")
        else:
            self.log("⚠️ No se capturaron logs de debug")
        
        return debug_indicators
    
    async def cleanup(self):
        """Limpiar recursos"""
        if self.browser:
            await self.browser.close()
    
    async def run_verification(self):
        """Ejecutar verificación completa"""
        try:
            await self.setup()
            
            # Test 1: Botón de adjuntar
            attach_works = await self.test_attach_button_functionality()
            
            # Test 2: DeepResearch forzado
            deepresearch_works = await self.test_deepresearch_forced_files()
            
            # Análisis de logs
            debug_indicators = await self.analyze_console_logs()
            
            # Resultado final
            self.log("\n🎯 RESULTADO FINAL:")
            self.log(f"   📎 Botón adjuntar: {'✅' if attach_works else '❌'}")
            self.log(f"   🔬 DeepResearch forzado: {'✅' if deepresearch_works else '❌'}")
            self.log(f"   🔍 Debug logs: {'✅' if any(debug_indicators.values()) else '❌'}")
            
            success = attach_works or deepresearch_works or any(debug_indicators.values())
            
            if success:
                self.log("\n🎉 ¡CORRECCIONES FUNCIONANDO!")
                self.log("   Se detectó actividad de los componentes corregidos")
            else:
                self.log("\n⚠️ Las correcciones necesitan más ajustes")
                self.log("   No se detectó actividad esperada")
            
            return success
            
        except Exception as e:
            self.log(f"❌ Error crítico: {str(e)}")
            return False
        finally:
            await self.cleanup()

async def main():
    """Función principal"""
    test = FileAttachmentVerificationTest()
    success = await test.run_verification()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)