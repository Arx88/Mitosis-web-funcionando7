# 🔥 INFORME TÉCNICO DEEPTASK: DIAGNÓSTICO COMPLETO DEL SISTEMA DE GENERACIÓN DE PLANES

**Fecha de Análisis**: 07 Agosto 2025  
**Severidad**: 🔴 **CRÍTICA**  
**Sistema Analizado**: Mitosis - Sistema de Generación de Planes de Tareas  

---

## 📋 RESUMEN EJECUTIVO

**PROBLEMA IDENTIFICADO**: Los planes generados son extremadamente básicos y genéricos debido a múltiples fallas sistémicas en el proceso de generación de tareas. El sistema está configurado para generar planes "fallback" en lugar de usar las capacidades avanzadas de Ollama, resultando en una experiencia de usuario pobre.

**IMPACTO**: 🔴 **CRÍTICO** - Los usuarios reciben planes genéricos de 3-4 pasos básicos en lugar de planes detallados y específicos para sus solicitudes.

---

## 🔍 ANÁLISIS TÉCNICO DETALLADO

### 1. **PROBLEMA PRINCIPAL: GENERACIÓN HARDCODEADA DE PLANES**

**Ubicación**: `/app/backend/src/routes/agent_routes.py` líneas 5330-5387

```python
# LÍNEA 5330-5331: COMENTARIO QUE REVELA EL PROBLEMA
# TEMPORALLY: Use a simpler approach to generate plan
logger.info(f"🔄 Using simplified plan generation for: {message}")
```

**DIAGNÓSTICO**: El código está explícitamente configurado para usar "simplified plan generation" en lugar de llamar a Ollama para generar planes inteligentes. Esto significa que:

- ❌ **NO se llama a Ollama** para generar planes personalizados
- ❌ **Se generan planes hardcodeados** con solo 3 pasos genéricos
- ❌ **Se ignoran las capacidades avanzadas** del LLM

### 2. **LÓGICA DE PLAN FALLBACK SIEMPRE ACTIVA**

**Código Problemático** (líneas 5344-5387):
```python
# Create intelligent steps based on the task
intelligent_steps = [
    {
        "id": "step-1",
        "title": f"Investigar información específica para {message[:50]}",
        "description": f"Buscar datos actualizados y específicos necesarios para: {message}",
        "tool": "web_search",
        # ... pasos genéricos hardcodeados
    }
]
```

**PROBLEMA**: Los planes se generan usando lógica hardcodeada que produce exactamente los mismos 3 pasos para cualquier solicitud del usuario.

### 3. **CÓDIGO OLLAMA DESACTIVADO**

**Ubicación**: líneas 5391-5450 (después del return)

El código que debería usar Ollama para generar planes inteligentes está **después** del return statement, lo que significa que nunca se ejecuta:

```python
# Esta línea 5387 retorna ANTES de que se ejecute la llamada a Ollama
return plan_data

# TODO EL CÓDIGO DE OLLAMA ESTÁ AQUÍ ABAJO Y NUNCA SE EJECUTA
if result.get('error'):
    logger.error(f"❌ Ollama error: {result['error']}")
    # ... resto del código Ollama
```

### 4. **DUPLICACIÓN MASIVA DE CÓDIGO**

Encontré **múltiples sistemas de generación de planes duplicados**:

1. **`generate_unified_ai_plan()`** - Función principal (ROTA)
2. **`generate_task_plan()`** - Wrapper que llama a la función principal
3. **`generate_basic_plan()`** - Plan fallback básico
4. **`generate_intelligent_fallback_plan()`** - Otro sistema fallback
5. **`agent_unified.py`** - Sistema completo duplicado en core
6. **`dynamic_task_planner.py`** - Sistema avanzado no utilizado

### 5. **SISTEMA DE VALIDACIÓN DEFECTUOSO**

**Ubicación**: líneas 189-245 (PLAN_SCHEMA)

El esquema JSON para validación es **demasiado restrictivo**:

```python
PLAN_SCHEMA = {
    "minItems": 3,  # ❌ Fuerza mínimo 3 pasos
    "maxItems": 6,  # ❌ Limita máximo 6 pasos
    "enum": ["web_search", "analysis", "creation"...]  # ❌ Tools limitadas
}
```

**PROBLEMA**: Esta validación fuerza que todos los planes tengan la misma estructura básica, eliminando la flexibilidad.

### 6. **EVALUADOR DE CALIDAD MUY RESTRICTIVO**

**Ubicación**: función `evaluate_result_quality()` líneas 1247-1387

El evaluador de calidad rechaza resultados válidos por criterios demasiado estrictos:

```python
# Criterios problemáticos:
if len(content) < 150:  # ❌ Muy restrictivo
    return False

meta_phrases = [
    'se realizará', 'se analizará'  # ❌ Rechaza contenido válido
]
```

---

## 🛠️ PROBLEMAS ESPECÍFICOS IDENTIFICADOS

### A. **ARQUITECTURA FRAGMENTADA**

```
❌ agent_routes.py (5000+ líneas)
❌ agent_unified.py (sistema duplicado) 
❌ dynamic_task_planner.py (no usado)
❌ Múltiples funciones que hacen lo mismo
```

### B. **FLUJO DE EJECUCIÓN ROTO**

```
1. Usuario solicita tarea
2. ❌ Se llama generate_unified_ai_plan()
3. ❌ Se usa "simplified plan generation"
4. ❌ Se retorna plan hardcodeado
5. ❌ NUNCA se llama a Ollama
6. Usuario recibe plan genérico
```

### C. **CONFIGURACIÓN INCORRECTA**

- **Ollama Service**: ✅ Funcionando
- **Ollama Health**: ✅ Saludable  
- **Llamadas a Ollama**: ❌ **NO SE REALIZAN** por el bug del return

### D. **HERRAMIENTAS AVANZADAS NO UTILIZADAS**

El sistema tiene capacidades avanzadas que no se usan:
- ❌ `WebBrowserManager` - Navegación en tiempo real
- ❌ `DynamicTaskPlanner` - Planificación con LLM
- ❌ `ReplanningEngine` - Replanificación inteligente
- ❌ Análisis de dependencias de tareas
- ❌ Estimación de complejidad inteligente

---

## 🎯 PLAN DE SOLUCIÓN PRIORITARIO

### **FASE 1: REPARACIÓN CRÍTICA** ⚡ (1-2 horas)

1. **FIX INMEDIATO**: Remover el return prematuro en línea 5387
2. **ACTIVAR OLLAMA**: Mover la lógica hardcodeada después de la llamada a Ollama
3. **SIMPLIFICAR PROMPTS**: Usar prompts más directos y menos restrictivos

### **FASE 2: OPTIMIZACIÓN** 🔧 (2-4 horas) 

1. **CONSOLIDAR CÓDIGO**: Eliminar duplicaciones
2. **RELAJAR VALIDACIÓN**: Hacer el schema más flexible
3. **MEJORAR EVALUADOR**: Criterios de calidad menos restrictivos

### **FASE 3: MEJORAS AVANZADAS** 🚀 (4-8 horas)

1. **INTEGRAR HERRAMIENTAS**: Usar WebBrowserManager y DynamicTaskPlanner
2. **SISTEMA HÍBRIDO**: Combinar Ollama con lógica heurística  
3. **ANÁLISIS INTELIGENTE**: Detección de complejidad real

---

## 💡 RECOMENDACIONES ESPECÍFICAS

### **1. PROMPT ENGINEERING**

Cambiar de prompts complejos y restrictivos a prompts más directos:

```python
# ❌ ACTUAL (muy complejo)
plan_prompt = f"""INSTRUCCIÓN: Responde ÚNICAMENTE con JSON válido...
CORRECCIÓN CRÍTICA: Los pasos deben ejecutar EXACTAMENTE...
EJEMPLO CORRECTO: Si el usuario pide...
JSON de respuesta (SOLO JSON, sin explicaciones):"""

# ✅ RECOMENDADO (simple y directo)  
plan_prompt = f"""Crea un plan detallado para: {message}
Responde solo con JSON:
{{"steps": [...], "complexity": "alta", "estimated_total_time": "..."}}"""
```

### **2. ARQUITECTURA SIMPLIFICADA**

```python
# ✅ FLUJO RECOMENDADO
def generate_plan(message, task_id):
    if ollama_available():
        return generate_with_ollama(message, task_id)
    else:
        return generate_intelligent_fallback(message, task_id)
```

### **3. VALIDACIÓN FLEXIBLE**

```python
# ✅ Schema más permisivo
PLAN_SCHEMA = {
    "minItems": 2,  # Mínimo más bajo
    "maxItems": 10, # Máximo más alto
    "additionalProperties": True  # Permitir campos extras
}
```

---

## 📊 MÉTRICAS DE IMPACTO

| Métrica | Estado Actual | Objetivo Post-Fix |
|---------|---------------|-------------------|
| Uso de Ollama | 0% (siempre fallback) | 95% |
| Diversidad de planes | 3 pasos genéricos | 4-8 pasos específicos |
| Tiempo de generación | 2-3 seg (hardcoded) | 5-15 seg (AI-powered) |
| Satisfacción usuario | ❌ Baja | ✅ Alta |

---

## ⚠️ RIESGOS IDENTIFICADOS

1. **TÉCNICO**: El fix puede exponer otros bugs ocultos por el fallback
2. **RENDIMIENTO**: Ollama puede ser más lento que lógica hardcodeada
3. **DEPENDENCIA**: Si Ollama falla, todo el sistema fallará sin el fallback

---

## 🔧 CÓDIGO DE EJEMPLO PARA FIX INMEDIATO

```python
def generate_unified_ai_plan(message: str, task_id: str) -> dict:
    """FIX: Generar plan usando Ollama primero, fallback después"""
    
    # 1. Intentar con Ollama PRIMERO
    ollama_service = get_ollama_service()
    if ollama_service and ollama_service.is_healthy():
        try:
            # Prompt simplificado
            prompt = f"Crea un plan detallado para: {message}\nResponde solo JSON válido:"
            result = ollama_service.generate_response(prompt)
            
            if result and not result.get('error'):
                plan_data = parse_and_validate_plan(result['response'])
                if plan_data:
                    logger.info("✅ Plan generado con Ollama")
                    return plan_data
        except Exception as e:
            logger.warning(f"❌ Ollama falló: {e}")
    
    # 2. Fallback inteligente solo si Ollama falla
    logger.info("🔄 Usando fallback inteligente")
    return generate_intelligent_fallback_plan(message, task_id)
```

---

## 📝 CONCLUSIONES

1. **CAUSA RAÍZ**: Un simple bug de `return` prematuro está causando que todo el sistema use planes hardcodeados
2. **SEVERIDAD**: Crítica - afecta 100% de las generaciones de planes  
3. **SOLUCIÓN**: Rápida - se puede solucionar en < 2 horas
4. **IMPACTO**: Alto - mejorará dramáticamente la experiencia del usuario

**RECOMENDACIÓN**: Proceder inmediatamente con la **FASE 1** del plan de solución para restaurar la funcionalidad básica de generación inteligente de planes.

---

*Informe generado por: Agente de Diagnóstico Técnico*  
*Próxima revisión recomendada: Post-implementación del fix*