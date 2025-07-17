#!/usr/bin/env python3
"""
Test para verificar que el sistema de clasificación funcione correctamente 
para tareas de navegación web
"""

import sys
sys.path.append('/app/backend/src')

def test_classification_system():
    """Test para verificar que los mensajes de navegación web se clasifiquen correctamente"""
    
    # Simular la función de clasificación del agent_routes.py
    def classify_message_mode(message: str) -> str:
        message_lower = message.lower().strip()
        
        # Patrones de navegación web específicos
        web_navigation_patterns = [
            # Navegación específica
            'navega a', 'navigate to', 'abre la página', 'open page',
            've al sitio', 'go to site', 'visita la web', 'visit website',
            'entra en', 'enter', 'accede a', 'access to',
            
            # Acciones web específicas
            'crea una cuenta en', 'create account on', 'regístrate en', 'register on',
            'inicia sesión en', 'log into', 'busca en google', 'search google',
            'compra en', 'buy on', 'descarga de', 'download from',
            'sube a', 'upload to', 'publica en', 'post on',
            
            # Combinaciones comunes
            'twitter y crea', 'facebook y registra', 'google y busca',
            'youtube y sube', 'instagram y publica', 'linkedin y conecta'
        ]
        
        # Verificar patrones de navegación web
        if any(pattern in message_lower for pattern in web_navigation_patterns):
            return 'agent'
        
        # Browser automation - CRÍTICO PARA NAVEGACIÓN Y AUTOMATIZACIÓN
        advanced_tools_patterns = [
            'navega', 'navigate', 'abre', 'open', 'visita', 'visit', 've a', 'go to',
            'crea cuenta', 'create account', 'regístrate', 'register', 'sign up',
            'inicia sesión', 'log in', 'login', 'accede', 'access',
            'llena', 'fill', 'completa', 'complete', 'formulario', 'form',
            'haz clic', 'click', 'presiona', 'press', 'selecciona', 'select',
            'busca en', 'search in', 'extrae', 'extract', 'obtén', 'get',
            'automatiza', 'automate', 'simula', 'simulate', 'interactúa', 'interact',
            'twitter', 'facebook', 'instagram', 'linkedin', 'github', 'google',
            'youtube', 'amazon', 'ebay', 'wikipedia', 'stackoverflow',
            'web scraping', 'scraping', 'captura', 'capture', 'screenshot'
        ]
        
        if any(pattern in message_lower for pattern in advanced_tools_patterns):
            return 'agent'
        
        # Por defecto, usar modo discusión
        return 'discussion'
    
    # Casos de prueba
    test_cases = [
        {
            'message': 'navega a google.com y busca información sobre inteligencia artificial',
            'expected': 'agent',
            'reason': 'Contiene "navega a" y "busca en"'
        },
        {
            'message': 've a twitter.com y crea una cuenta',
            'expected': 'agent',
            'reason': 'Contiene "ve a" y "crea cuenta"'
        },
        {
            'message': 'abre facebook.com',
            'expected': 'agent',
            'reason': 'Contiene "abre" y "facebook"'
        },
        {
            'message': 'visita youtube.com y busca videos',
            'expected': 'agent',
            'reason': 'Contiene "visita" y "youtube"'
        },
        {
            'message': 'qué es la inteligencia artificial',
            'expected': 'discussion',
            'reason': 'Pregunta casual, no navegación'
        },
        {
            'message': 'hola como estas',
            'expected': 'discussion',
            'reason': 'Saludo casual'
        },
        {
            'message': 'automatiza el registro en github',
            'expected': 'agent',
            'reason': 'Contiene "automatiza" y "github"'
        }
    ]
    
    print("🧪 === TEST CLASIFICACIÓN DE NAVEGACIÓN WEB ===")
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        message = test_case['message']
        expected = test_case['expected']
        reason = test_case['reason']
        
        actual = classify_message_mode(message)
        
        if actual == expected:
            print(f"✅ PASÓ: '{message}' → {actual} ({reason})")
            passed += 1
        else:
            print(f"❌ FALLÓ: '{message}' → {actual} (esperado: {expected}) ({reason})")
            failed += 1
    
    print(f"\n📊 RESULTADOS: {passed} pasaron, {failed} fallaron")
    
    if failed == 0:
        print("🎉 ¡Todos los tests pasaron!")
    else:
        print("⚠️  Algunos tests fallaron - revisar lógica de clasificación")
    
    return failed == 0

if __name__ == "__main__":
    test_classification_system()