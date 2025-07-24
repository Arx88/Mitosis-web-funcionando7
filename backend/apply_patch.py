#!/usr/bin/env python3
"""
Patch script to replace the complex prompt with simplified intelligent version
"""
import re

def apply_intelligent_prompt_patch():
    """Apply the simplified intelligent prompt patch"""
    
    agent_routes_path = '/app/backend/src/routes/agent_routes.py'
    
    # Read the current file
    with open(agent_routes_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define the new simplified intelligent prompt
    new_prompt = '''        # 🧠 PROMPT INTELIGENTE SIMPLIFICADO - AGENTE EXCEPCIONAL
        plan_prompt = f"""Crea un plan excepcional de 3-4 pasos para: {message}

Como agente experto, diseña pasos ESPECÍFICOS y DETALLADOS que superen expectativas del usuario.

METODOLOGÍA INTELIGENTE:
- Si es investigación: Incluye fuentes múltiples, análisis comparativo, tendencias actuales
- Si es creación: Estructura profesional, contenido original, ejemplos prácticos  
- Si es análisis: Datos cuantitativos, insights profundos, recomendaciones accionables
- Si es técnico: Mejores prácticas, código optimizado, documentación clara

RESPONDE SOLO con JSON válido en este formato:
{{
  "steps": [
    {{
      "id": "step-1",
      "title": "Título específico orientado al valor máximo para esta tarea",
      "description": "Metodología detallada con entregables específicos y fuentes concretas", 
      "tool": "web_search"
    }},
    {{
      "id": "step-2",
      "title": "Segundo paso que construya sobre el anterior y amplifique el valor",
      "description": "Proceso de análisis avanzado que genere insights únicos y útiles",
      "tool": "analysis"
    }},
    {{
      "id": "step-3", 
      "title": "Paso final que consolide y entregue resultados profesionales",
      "description": "Síntesis y entrega con formato accionable y recomendaciones específicas",
      "tool": "creation"
    }}
  ],
  "task_type": "clasificación profesional específica para esta tarea",
  "complexity": "evaluación realista: baja|media|alta",
  "estimated_total_time": "tiempo realista considerando calidad profesional"
}}

IMPORTANTE: Los pasos deben ser específicos para "{message}", no genéricos.
HERRAMIENTAS: web_search, analysis, creation, planning, delivery, processing, synthesis, data_analysis, research

CREA UN PLAN QUE SUPERE LAS EXPECTATIVAS - RESPONDE SOLO JSON:"""'''
    
    # Find and replace the complex prompt section
    # Looking for the pattern that starts with the prompt definition
    pattern = r'(        # 🧠 PROMPT INTELIGENTE.*?plan_prompt = f""".*?CREA UN PLAN EXCEPCIONAL QUE SUPERE EXPECTATIVAS 🚀""")'
    
    # Replace with new simplified version
    new_content = re.sub(pattern, new_prompt, content, flags=re.DOTALL)
    
    if new_content != content:
        # Write back the modified content
        with open(agent_routes_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Successfully applied intelligent prompt patch!")
        return True
    else:
        print("❌ Pattern not found - no changes made")
        return False

if __name__ == "__main__":
    print("🔧 Applying intelligent prompt patch...")
    success = apply_intelligent_prompt_patch()
    
    if success:
        print("🎉 Patch applied! Now testing with curl...")
        
        # Test the patch
        import subprocess
        try:
            result = subprocess.run([
                'curl', '-X', 'POST', 'http://localhost:8001/api/agent/generate-plan',
                '-H', 'Content-Type: application/json',
                '-d', '{"task_title": "Crear estrategia de marketing digital para startup tech", "task_id": "test-patch-001"}'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("📡 API Response:")
                print(result.stdout)
            else:
                print(f"❌ API Error: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Test Error: {e}")
    else:
        print("❌ Patch failed!")