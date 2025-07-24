#!/usr/bin/env python3
"""
Test script for improved planning prompts
"""
import requests
import json

def test_ollama_direct():
    """Test Ollama directly with simplified intelligent prompt"""
    
    message = "Crear un análisis completo del mercado inmobiliario en Valencia 2025"
    
    # Simplified but still intelligent prompt
    prompt = f"""Crea un plan excepcional de 3-4 pasos para: {message}

Como agente experto, diseña pasos ESPECÍFICOS y DETALLADOS que superen expectativas:

RESPONDE SOLO con JSON válido:
{{
  "steps": [
    {{
      "id": "step-1",
      "title": "Título específico orientado al valor máximo",
      "description": "Metodología detallada con entregables específicos", 
      "tool": "web_search"
    }},
    {{
      "id": "step-2",
      "title": "Segundo paso que construya sobre el anterior",
      "description": "Proceso de análisis avanzado con insights únicos",
      "tool": "analysis"
    }},
    {{
      "id": "step-3", 
      "title": "Paso final con resultados profesionales",
      "description": "Síntesis y entrega con formato accionable",
      "tool": "creation"
    }}
  ],
  "task_type": "análisis inmobiliario especializado",
  "complexity": "alta",
  "estimated_total_time": "45-60 minutos"
}}

IMPORTANTE: Los pasos deben ser específicos para mercado inmobiliario Valencia, no genéricos.
HERRAMIENTAS: web_search, analysis, creation, planning, delivery

RESPONDE SOLO JSON:"""

    try:
        response = requests.post(
            'https://bef4a4bb93d1.ngrok-free.app/api/generate',
            json={
                'model': 'llama3.1:8b', 
                'prompt': prompt,
                'stream': False,
                'options': {'temperature': 0.3}
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '').strip()
            print("=== OLLAMA RESPONSE ===")
            print(response_text)
            print("\n=== ATTEMPTING JSON PARSE ===")
            
            # Try to parse JSON
            try:
                # Clean response
                cleaned = response_text.replace('```json', '').replace('```', '').strip()
                plan_data = json.loads(cleaned)
                print("✅ JSON PARSED SUCCESSFULLY!")
                print(json.dumps(plan_data, indent=2))
                return plan_data
            except json.JSONDecodeError as e:
                print(f"❌ JSON PARSE ERROR: {e}")
                print(f"Raw response: {response_text[:200]}...")
                return None
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Request Error: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Testing improved Ollama prompt...")
    result = test_ollama_direct()
    
    if result:
        print("\n🎉 SUCCESS: Intelligent planning working!")
    else:
        print("\n❌ FAILED: Need to adjust prompt strategy")