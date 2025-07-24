#!/usr/bin/env python3
"""
Create a new improved generate_plan function as a separate module
"""

import json
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def generate_intelligent_plan(message: str, task_id: str, ollama_service) -> dict:
    """
    Generate intelligent and specific plans using simplified but effective prompts
    """
    if not ollama_service or not ollama_service.is_healthy():
        logger.error("❌ Ollama service not available")
        return generate_fallback_plan(message, task_id)
    
    # Simplified but intelligent prompt that works
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

CREA UN PLAN QUE SUPERE LAS EXPECTATIVAS - RESPONDE SOLO JSON:"""

    try:
        # Generate plan with Ollama
        result = ollama_service.generate_response(plan_prompt, {'temperature': 0.3})
        
        if result.get('error'):
            logger.error(f"❌ Ollama error: {result['error']}")
            return generate_fallback_plan(message, task_id)
        
        # Parse JSON response
        response_text = result.get('response', '').strip()
        
        try:
            # Clean response
            cleaned_response = response_text.replace('```json', '').replace('```', '').strip()
            plan_data = json.loads(cleaned_response)
            
            # Validate basic structure
            if not plan_data.get('steps') or not isinstance(plan_data['steps'], list):
                raise ValueError("Invalid plan structure")
            
            # Add missing fields to steps
            for step in plan_data['steps']:
                step['completed'] = False
                step['active'] = False
                step['status'] = 'pending'
            
            logger.info(f"✅ Intelligent plan generated with {len(plan_data['steps'])} specific steps")
            
            return {
                'plan': plan_data['steps'],
                'enhanced_title': f"Plan inteligente: {message[:50]}...",
                'task_id': task_id,
                'total_steps': len(plan_data['steps']),
                'estimated_total_time': plan_data.get('estimated_total_time', '45-60 minutos'),
                'task_type': plan_data.get('task_type', 'tarea especializada'),
                'complexity': plan_data.get('complexity', 'media')
            }
            
        except (json.JSONDecodeError, ValueError) as parse_error:
            logger.error(f"❌ JSON parse error: {parse_error}")
            logger.error(f"❌ Response was: {response_text[:200]}...")
            return generate_fallback_plan(message, task_id)
            
    except Exception as e:
        logger.error(f"❌ Error generating intelligent plan: {e}")
        return generate_fallback_plan(message, task_id)

def generate_fallback_plan(message: str, task_id: str) -> dict:
    """
    Generate a basic fallback plan when intelligent generation fails
    """
    fallback_steps = [
        {
            "id": "step-1",
            "title": f"Investigación específica: {message[:30]}...",
            "description": "Realizar búsqueda detallada y recopilación de información relevante",
            "tool": "web_search",
            "completed": False,
            "active": False,
            "status": "pending"
        },
        {
            "id": "step-2", 
            "title": "Análisis profesional de la información",
            "description": "Procesar y analizar los datos para generar insights valiosos",
            "tool": "analysis",
            "completed": False,
            "active": False,
            "status": "pending" 
        },
        {
            "id": "step-3",
            "title": "Creación del entregable final",
            "description": "Desarrollar el producto final con calidad profesional", 
            "tool": "creation",
            "completed": False,
            "active": False,
            "status": "pending"
        }
    ]
    
    logger.warning(f"⚠️ Using fallback plan for task: {message[:30]}...")
    
    return {
        'plan': fallback_steps,
        'enhanced_title': f"Plan básico: {message[:50]}...",
        'task_id': task_id,
        'total_steps': len(fallback_steps),
        'estimated_total_time': '30-45 minutos',
        'task_type': 'general',
        'complexity': 'media'
    }