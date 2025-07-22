#!/usr/bin/env python3
"""
Test del Sistema de Navegación Web REAL del Agente Mitosis
Evaluación de la Fase 2 del NEWUPGRADE.md

Este test evalúa las capacidades REALES de navegación web del sistema:
1. WebSearchTool con DuckDuckGo real
2. TavilySearchTool con API de Tavily real
3. Funcionalidad a través del endpoint /api/agent/chat
4. Evaluación de limitaciones y necesidades de WebBrowserManager Playwright
"""

import requests
import json
import time
import os
import sys
from typing import Dict, Any, List
from datetime import datetime

# Configuración
BACKEND_URL = "https://0eea585b-9491-4595-8054-818b778be2a7.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class WebBrowsingTester:
    def __init__(self):
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "backend_url": BACKEND_URL,
            "tests_performed": [],
            "web_search_tool": {"status": "unknown", "results": []},
            "tavily_search_tool": {"status": "unknown", "results": []},
            "chat_endpoint_web": {"status": "unknown", "results": []},
            "limitations_found": [],
            "recommendations": [],
            "phase_2_status": "unknown"
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_backend_health(self) -> bool:
        """Test básico de conectividad del backend"""
        self.log("🔍 Verificando conectividad del backend...")
        
        try:
            response = requests.get(f"{API_BASE}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Backend conectado: {data.get('status', 'unknown')}")
                return True
            else:
                self.log(f"❌ Backend no responde correctamente: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error conectando al backend: {e}")
            return False
    
    def test_websearch_tool_direct(self) -> Dict[str, Any]:
        """Test directo de WebSearchTool con DuckDuckGo"""
        self.log("🔍 Testeando WebSearchTool con DuckDuckGo REAL...")
        
        test_result = {
            "tool_name": "WebSearchTool",
            "test_queries": [],
            "success_rate": 0,
            "avg_response_time": 0,
            "real_results_found": False,
            "errors": []
        }
        
        # Queries de test para evaluar capacidades reales
        test_queries = [
            "últimas noticias inteligencia artificial 2024",
            "tendencias tecnología 2025",
            "Python programming best practices"
        ]
        
        successful_tests = 0
        total_time = 0
        
        for query in test_queries:
            self.log(f"  🔎 Probando query: '{query}'")
            start_time = time.time()
            
            try:
                # Importar y usar directamente la herramienta
                sys.path.append('/app/backend/src/tools')
                from web_search_tool import WebSearchTool
                
                tool = WebSearchTool()
                result = tool.execute({
                    "query": query,
                    "action": "search",
                    "max_results": 5
                })
                
                response_time = time.time() - start_time
                total_time += response_time
                
                query_result = {
                    "query": query,
                    "response_time": response_time,
                    "success": result.get("success", False),
                    "results_count": len(result.get("results", [])),
                    "has_real_urls": False,
                    "sample_results": []
                }
                
                if result.get("success") and result.get("results"):
                    successful_tests += 1
                    
                    # Verificar que son resultados REALES
                    for res in result["results"][:2]:  # Tomar 2 ejemplos
                        url = res.get("url", "")
                        if url.startswith("http"):
                            query_result["has_real_urls"] = True
                            test_result["real_results_found"] = True
                        
                        query_result["sample_results"].append({
                            "title": res.get("title", "")[:100],
                            "url": url,
                            "snippet": res.get("snippet", "")[:150]
                        })
                    
                    self.log(f"    ✅ Query exitosa: {len(result['results'])} resultados reales")
                else:
                    error_msg = result.get("error", "Unknown error")
                    query_result["error"] = error_msg
                    test_result["errors"].append(f"Query '{query}': {error_msg}")
                    self.log(f"    ❌ Query falló: {error_msg}")
                
                test_result["test_queries"].append(query_result)
                
            except Exception as e:
                error_msg = str(e)
                test_result["errors"].append(f"Query '{query}': {error_msg}")
                self.log(f"    ❌ Error ejecutando query: {error_msg}")
                
                test_result["test_queries"].append({
                    "query": query,
                    "response_time": time.time() - start_time,
                    "success": False,
                    "error": error_msg
                })
        
        # Calcular métricas
        test_result["success_rate"] = successful_tests / len(test_queries) if test_queries else 0
        test_result["avg_response_time"] = total_time / len(test_queries) if test_queries else 0
        
        self.log(f"📊 WebSearchTool - Tasa de éxito: {test_result['success_rate']:.1%}, Tiempo promedio: {test_result['avg_response_time']:.2f}s")
        
        return test_result
    
    def test_tavily_search_tool_direct(self) -> Dict[str, Any]:
        """Test directo de TavilySearchTool con API real"""
        self.log("🔍 Testeando TavilySearchTool con API de Tavily REAL...")
        
        test_result = {
            "tool_name": "TavilySearchTool",
            "test_queries": [],
            "success_rate": 0,
            "avg_response_time": 0,
            "real_results_found": False,
            "api_key_configured": False,
            "errors": []
        }
        
        try:
            # Verificar si la API key está configurada
            sys.path.append('/app/backend/src/tools')
            from tavily_search_tool import TavilySearchTool
            
            tool = TavilySearchTool()
            test_result["api_key_configured"] = tool.api_key is not None
            
            if not test_result["api_key_configured"]:
                self.log("⚠️  API key de Tavily no configurada")
                test_result["errors"].append("Tavily API key not configured")
                return test_result
            
            # Queries de test
            test_queries = [
                "artificial intelligence trends 2024",
                "latest technology news",
                "Python programming tutorials"
            ]
            
            successful_tests = 0
            total_time = 0
            
            for query in test_queries:
                self.log(f"  🔎 Probando query Tavily: '{query}'")
                start_time = time.time()
                
                try:
                    result = tool.execute({
                        "query": query,
                        "max_results": 5,
                        "include_answer": True
                    })
                    
                    response_time = time.time() - start_time
                    total_time += response_time
                    
                    query_result = {
                        "query": query,
                        "response_time": response_time,
                        "success": result.get("success", False),
                        "results_count": len(result.get("results", [])),
                        "has_answer": bool(result.get("answer", "")),
                        "has_real_urls": False,
                        "sample_results": []
                    }
                    
                    if result.get("success") and result.get("results"):
                        successful_tests += 1
                        
                        # Verificar que son resultados REALES
                        for res in result["results"][:2]:
                            url = res.get("url", "")
                            if url.startswith("http"):
                                query_result["has_real_urls"] = True
                                test_result["real_results_found"] = True
                            
                            query_result["sample_results"].append({
                                "title": res.get("title", "")[:100],
                                "url": url,
                                "snippet": res.get("snippet", "")[:150],
                                "score": res.get("score", 0)
                            })
                        
                        self.log(f"    ✅ Query Tavily exitosa: {len(result['results'])} resultados, answer: {bool(result.get('answer'))}")
                    else:
                        error_msg = result.get("error", "Unknown error")
                        query_result["error"] = error_msg
                        test_result["errors"].append(f"Query '{query}': {error_msg}")
                        self.log(f"    ❌ Query Tavily falló: {error_msg}")
                    
                    test_result["test_queries"].append(query_result)
                    
                except Exception as e:
                    error_msg = str(e)
                    test_result["errors"].append(f"Query '{query}': {error_msg}")
                    self.log(f"    ❌ Error ejecutando query Tavily: {error_msg}")
                    
                    test_result["test_queries"].append({
                        "query": query,
                        "response_time": time.time() - start_time,
                        "success": False,
                        "error": error_msg
                    })
            
            # Calcular métricas
            test_result["success_rate"] = successful_tests / len(test_queries) if test_queries else 0
            test_result["avg_response_time"] = total_time / len(test_queries) if test_queries else 0
            
            self.log(f"📊 TavilySearchTool - Tasa de éxito: {test_result['success_rate']:.1%}, Tiempo promedio: {test_result['avg_response_time']:.2f}s")
            
        except Exception as e:
            error_msg = str(e)
            test_result["errors"].append(f"Tool initialization error: {error_msg}")
            self.log(f"❌ Error inicializando TavilySearchTool: {error_msg}")
        
        return test_result
    
    def test_chat_endpoint_web_queries(self) -> Dict[str, Any]:
        """Test del endpoint /api/agent/chat con queries que requieren búsqueda web"""
        self.log("🔍 Testeando endpoint /api/agent/chat con queries de búsqueda web...")
        
        test_result = {
            "endpoint": "/api/agent/chat",
            "test_messages": [],
            "success_rate": 0,
            "avg_response_time": 0,
            "web_tools_triggered": False,
            "autonomous_execution": False,
            "errors": []
        }
        
        # Mensajes que deberían activar búsqueda web
        test_messages = [
            "¿Cuáles son las últimas noticias sobre inteligencia artificial en 2024?",
            "Busca información sobre las tendencias tecnológicas más importantes de 2025",
            "Investiga qué empresas están liderando el desarrollo de IA generativa"
        ]
        
        successful_tests = 0
        total_time = 0
        
        for message in test_messages:
            self.log(f"  💬 Probando mensaje: '{message[:50]}...'")
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{API_BASE}/agent/chat",
                    json={"message": message},
                    timeout=30
                )
                
                response_time = time.time() - start_time
                total_time += response_time
                
                message_result = {
                    "message": message,
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "autonomous_execution": False,
                    "web_search_mentioned": False,
                    "response_length": 0
                }
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get("response", "")
                    message_result["response_length"] = len(response_text)
                    message_result["autonomous_execution"] = data.get("autonomous_execution", False)
                    
                    # Verificar si menciona búsqueda web o herramientas
                    web_keywords = ["búsqueda", "search", "web", "internet", "información", "investigar"]
                    if any(keyword in response_text.lower() for keyword in web_keywords):
                        message_result["web_search_mentioned"] = True
                        test_result["web_tools_triggered"] = True
                    
                    if message_result["autonomous_execution"]:
                        test_result["autonomous_execution"] = True
                    
                    successful_tests += 1
                    self.log(f"    ✅ Mensaje procesado: {len(response_text)} chars, autónomo: {message_result['autonomous_execution']}")
                else:
                    error_msg = f"HTTP {response.status_code}"
                    message_result["error"] = error_msg
                    test_result["errors"].append(f"Message '{message[:30]}...': {error_msg}")
                    self.log(f"    ❌ Error HTTP: {response.status_code}")
                
                test_result["test_messages"].append(message_result)
                
            except Exception as e:
                error_msg = str(e)
                test_result["errors"].append(f"Message '{message[:30]}...': {error_msg}")
                self.log(f"    ❌ Error procesando mensaje: {error_msg}")
                
                test_result["test_messages"].append({
                    "message": message,
                    "response_time": time.time() - start_time,
                    "success": False,
                    "error": error_msg
                })
        
        # Calcular métricas
        test_result["success_rate"] = successful_tests / len(test_messages) if test_messages else 0
        test_result["avg_response_time"] = total_time / len(test_messages) if test_messages else 0
        
        self.log(f"📊 Chat Endpoint - Tasa de éxito: {test_result['success_rate']:.1%}, Tiempo promedio: {test_result['avg_response_time']:.2f}s")
        
        return test_result
    
    def evaluate_limitations(self, websearch_result: Dict, tavily_result: Dict, chat_result: Dict):
        """Evaluar limitaciones del sistema actual"""
        self.log("🔍 Evaluando limitaciones del sistema de navegación web...")
        
        limitations = []
        
        # Evaluar WebSearchTool
        if websearch_result["success_rate"] < 0.8:
            limitations.append({
                "component": "WebSearchTool",
                "issue": "Baja tasa de éxito en búsquedas",
                "impact": "Búsquedas web poco confiables",
                "severity": "high"
            })
        
        if not websearch_result["real_results_found"]:
            limitations.append({
                "component": "WebSearchTool", 
                "issue": "No se encontraron resultados reales con URLs válidas",
                "impact": "Posibles resultados simulados o errores de parsing",
                "severity": "critical"
            })
        
        if websearch_result["avg_response_time"] > 10:
            limitations.append({
                "component": "WebSearchTool",
                "issue": "Tiempo de respuesta lento",
                "impact": "Experiencia de usuario degradada",
                "severity": "medium"
            })
        
        # Evaluar TavilySearchTool
        if not tavily_result["api_key_configured"]:
            limitations.append({
                "component": "TavilySearchTool",
                "issue": "API key no configurada",
                "impact": "Herramienta de búsqueda avanzada no disponible",
                "severity": "high"
            })
        
        if tavily_result["success_rate"] < 0.8:
            limitations.append({
                "component": "TavilySearchTool",
                "issue": "Baja tasa de éxito",
                "impact": "Búsquedas avanzadas poco confiables",
                "severity": "high"
            })
        
        # Evaluar integración con Chat
        if not chat_result["web_tools_triggered"]:
            limitations.append({
                "component": "Chat Integration",
                "issue": "Herramientas web no se activan automáticamente",
                "impact": "Búsquedas web no se ejecutan cuando se necesitan",
                "severity": "critical"
            })
        
        if not chat_result["autonomous_execution"]:
            limitations.append({
                "component": "Autonomous Execution",
                "issue": "Ejecución autónoma no se activa para búsquedas web",
                "impact": "Usuario debe activar manualmente las búsquedas",
                "severity": "medium"
            })
        
        # Limitaciones generales identificadas
        general_limitations = [
            {
                "component": "JavaScript Rendering",
                "issue": "Sin capacidad de ejecutar JavaScript",
                "impact": "Sitios web dinámicos no accesibles",
                "severity": "high"
            },
            {
                "component": "Interactive Navigation",
                "issue": "Sin navegación interactiva (clicks, forms)",
                "impact": "Limitado a contenido estático",
                "severity": "medium"
            },
            {
                "component": "Session Management",
                "issue": "Sin manejo de sesiones/cookies",
                "impact": "No puede acceder a contenido que requiere login",
                "severity": "medium"
            }
        ]
        
        limitations.extend(general_limitations)
        
        self.results["limitations_found"] = limitations
        
        # Log limitaciones encontradas
        critical_count = len([l for l in limitations if l["severity"] == "critical"])
        high_count = len([l for l in limitations if l["severity"] == "high"])
        
        self.log(f"⚠️  Limitaciones encontradas: {len(limitations)} total ({critical_count} críticas, {high_count} altas)")
        
        for limitation in limitations:
            severity_emoji = "🔴" if limitation["severity"] == "critical" else "🟠" if limitation["severity"] == "high" else "🟡"
            self.log(f"  {severity_emoji} {limitation['component']}: {limitation['issue']}")
    
    def generate_recommendations(self):
        """Generar recomendaciones basadas en los resultados"""
        self.log("💡 Generando recomendaciones...")
        
        recommendations = []
        
        # Analizar limitaciones críticas
        critical_limitations = [l for l in self.results["limitations_found"] if l["severity"] == "critical"]
        
        if critical_limitations:
            recommendations.append({
                "priority": "high",
                "action": "Implementar WebBrowserManager con Playwright",
                "reason": "Limitaciones críticas en navegación web actual",
                "benefits": [
                    "Renderizado de JavaScript",
                    "Navegación interactiva",
                    "Manejo de sesiones",
                    "Capturas de pantalla",
                    "Automatización completa"
                ]
            })
        
        # Recomendaciones específicas por herramienta
        if not self.results["tavily_search_tool"]["api_key_configured"]:
            recommendations.append({
                "priority": "medium",
                "action": "Configurar API key de Tavily",
                "reason": "Herramienta de búsqueda avanzada no disponible",
                "benefits": ["Búsquedas más precisas", "Respuestas resumidas", "Mayor confiabilidad"]
            })
        
        if self.results["web_search_tool"]["success_rate"] < 0.8:
            recommendations.append({
                "priority": "medium", 
                "action": "Mejorar robustez de WebSearchTool",
                "reason": "Baja tasa de éxito en búsquedas básicas",
                "benefits": ["Mayor confiabilidad", "Mejor experiencia de usuario"]
            })
        
        if not self.results["chat_endpoint_web"]["web_tools_triggered"]:
            recommendations.append({
                "priority": "high",
                "action": "Mejorar integración de herramientas web en chat",
                "reason": "Herramientas web no se activan automáticamente",
                "benefits": ["Experiencia más fluida", "Automatización real"]
            })
        
        # Recomendaciones de mejora general
        recommendations.append({
            "priority": "low",
            "action": "Implementar cache de resultados web",
            "reason": "Optimizar rendimiento y reducir llamadas API",
            "benefits": ["Mejor rendimiento", "Reducción de costos", "Experiencia más rápida"]
        })
        
        recommendations.append({
            "priority": "medium",
            "action": "Añadir métricas de calidad de resultados",
            "reason": "Evaluar automáticamente la relevancia de resultados",
            "benefits": ["Mejor calidad", "Detección automática de problemas"]
        })
        
        self.results["recommendations"] = recommendations
        
        # Log recomendaciones
        high_priority = len([r for r in recommendations if r["priority"] == "high"])
        self.log(f"💡 Recomendaciones generadas: {len(recommendations)} total ({high_priority} alta prioridad)")
    
    def determine_phase_2_status(self):
        """Determinar el estado de la Fase 2 del NEWUPGRADE.md"""
        self.log("📊 Determinando estado de la Fase 2 del NEWUPGRADE.md...")
        
        # Criterios para evaluar la Fase 2
        websearch_working = self.results["web_search_tool"]["success_rate"] >= 0.7
        tavily_available = self.results["tavily_search_tool"]["api_key_configured"]
        tavily_working = self.results["tavily_search_tool"]["success_rate"] >= 0.7 if tavily_available else False
        chat_integration = self.results["chat_endpoint_web"]["success_rate"] >= 0.7
        real_results = (self.results["web_search_tool"]["real_results_found"] or 
                       self.results["tavily_search_tool"]["real_results_found"])
        
        critical_limitations = len([l for l in self.results["limitations_found"] if l["severity"] == "critical"])
        
        # Determinar estado
        if websearch_working and real_results and chat_integration and critical_limitations == 0:
            status = "COMPLETAMENTE_EXITOSA"
            description = "Sistema de navegación web completamente funcional con herramientas reales"
        elif websearch_working and real_results and critical_limitations <= 1:
            status = "PARCIALMENTE_EXITOSA"
            description = "Sistema funcional con limitaciones menores"
        elif websearch_working or tavily_working:
            status = "FUNCIONAL_CON_LIMITACIONES"
            description = "Algunas herramientas funcionan pero hay limitaciones significativas"
        else:
            status = "NECESITA_MEJORAS"
            description = "Sistema requiere mejoras significativas para ser funcional"
        
        self.results["phase_2_status"] = status
        self.results["phase_2_description"] = description
        
        # Determinar si WebBrowserManager Playwright es necesario
        playwright_needed = critical_limitations > 0 or not chat_integration
        self.results["playwright_needed"] = playwright_needed
        
        status_emoji = "✅" if status == "COMPLETAMENTE_EXITOSA" else "🟡" if "PARCIAL" in status else "⚠️" if "FUNCIONAL" in status else "❌"
        self.log(f"{status_emoji} Estado Fase 2: {status}")
        self.log(f"📝 Descripción: {description}")
        self.log(f"🎭 WebBrowserManager Playwright necesario: {'Sí' if playwright_needed else 'No'}")
    
    def run_comprehensive_test(self):
        """Ejecutar test comprensivo del sistema de navegación web"""
        self.log("🚀 Iniciando test comprensivo del sistema de navegación web REAL...")
        self.log(f"🎯 Objetivo: Evaluar estado de Fase 2 del NEWUPGRADE.md")
        self.log(f"🌐 Backend URL: {BACKEND_URL}")
        
        # 1. Verificar conectividad
        if not self.test_backend_health():
            self.log("❌ No se puede continuar sin conectividad al backend")
            return self.results
        
        # 2. Test WebSearchTool directo
        self.results["web_search_tool"] = self.test_websearch_tool_direct()
        self.results["tests_performed"].append("WebSearchTool Direct Test")
        
        # 3. Test TavilySearchTool directo
        self.results["tavily_search_tool"] = self.test_tavily_search_tool_direct()
        self.results["tests_performed"].append("TavilySearchTool Direct Test")
        
        # 4. Test endpoint chat con queries web
        self.results["chat_endpoint_web"] = self.test_chat_endpoint_web_queries()
        self.results["tests_performed"].append("Chat Endpoint Web Queries Test")
        
        # 5. Evaluar limitaciones
        self.evaluate_limitations(
            self.results["web_search_tool"],
            self.results["tavily_search_tool"], 
            self.results["chat_endpoint_web"]
        )
        
        # 6. Generar recomendaciones
        self.generate_recommendations()
        
        # 7. Determinar estado de Fase 2
        self.determine_phase_2_status()
        
        self.log("✅ Test comprensivo completado")
        return self.results
    
    def save_results(self, filename: str = "web_browsing_test_results.json"):
        """Guardar resultados en archivo JSON"""
        try:
            with open(f"/app/{filename}", 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
            self.log(f"💾 Resultados guardados en: /app/{filename}")
        except Exception as e:
            self.log(f"❌ Error guardando resultados: {e}")
    
    def print_summary(self):
        """Imprimir resumen de resultados"""
        self.log("\n" + "="*80)
        self.log("📊 RESUMEN DE RESULTADOS - SISTEMA DE NAVEGACIÓN WEB REAL")
        self.log("="*80)
        
        # Estado general
        status = self.results["phase_2_status"]
        status_emoji = "✅" if status == "COMPLETAMENTE_EXITOSA" else "🟡" if "PARCIAL" in status else "⚠️" if "FUNCIONAL" in status else "❌"
        self.log(f"\n{status_emoji} ESTADO FASE 2 NEWUPGRADE.MD: {status}")
        self.log(f"📝 {self.results['phase_2_description']}")
        
        # Resultados por herramienta
        self.log(f"\n🔍 WEBSEARCHTOOL (DuckDuckGo):")
        ws = self.results["web_search_tool"]
        self.log(f"   Tasa de éxito: {ws['success_rate']:.1%}")
        self.log(f"   Resultados reales: {'✅' if ws['real_results_found'] else '❌'}")
        self.log(f"   Tiempo promedio: {ws['avg_response_time']:.2f}s")
        
        self.log(f"\n🎯 TAVILYSEARCHTOOL (API Tavily):")
        ts = self.results["tavily_search_tool"]
        self.log(f"   API configurada: {'✅' if ts['api_key_configured'] else '❌'}")
        self.log(f"   Tasa de éxito: {ts['success_rate']:.1%}")
        self.log(f"   Resultados reales: {'✅' if ts['real_results_found'] else '❌'}")
        
        self.log(f"\n💬 INTEGRACIÓN CHAT:")
        cs = self.results["chat_endpoint_web"]
        self.log(f"   Tasa de éxito: {cs['success_rate']:.1%}")
        self.log(f"   Herramientas web activadas: {'✅' if cs['web_tools_triggered'] else '❌'}")
        self.log(f"   Ejecución autónoma: {'✅' if cs['autonomous_execution'] else '❌'}")
        
        # Limitaciones críticas
        critical = [l for l in self.results["limitations_found"] if l["severity"] == "critical"]
        self.log(f"\n🔴 LIMITACIONES CRÍTICAS: {len(critical)}")
        for limitation in critical:
            self.log(f"   • {limitation['component']}: {limitation['issue']}")
        
        # Recomendación principal
        self.log(f"\n💡 RECOMENDACIÓN PRINCIPAL:")
        if self.results["playwright_needed"]:
            self.log("   🎭 IMPLEMENTAR WebBrowserManager con Playwright")
            self.log("   📋 Razón: Limitaciones críticas en navegación web actual")
        else:
            self.log("   ✅ Sistema actual es suficiente para objetivos básicos")
            self.log("   📋 Considerar mejoras menores para optimización")
        
        self.log("\n" + "="*80)

def main():
    """Función principal"""
    print("🧪 SISTEMA DE TESTING DE NAVEGACIÓN WEB REAL - MITOSIS AGENT")
    print("📋 Evaluación de Fase 2 del NEWUPGRADE.md")
    print("="*80)
    
    # Crear tester y ejecutar
    tester = WebBrowsingTester()
    results = tester.run_comprehensive_test()
    
    # Guardar y mostrar resultados
    tester.save_results()
    tester.print_summary()
    
    return results

if __name__ == "__main__":
    main()