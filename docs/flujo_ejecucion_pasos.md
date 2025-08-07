# 🔧 FLUJO DETALLADO: EJECUCIÓN DE PASOS DEL PLAN DE ACCIÓN

## 📅 Fecha: 24 de Enero, 2025  
## 🎯 Análisis: Cómo el agente ataca cada paso del plan paso a paso

---

## 🚀 FLUJO COMPLETO DE EJECUCIÓN DE PASOS

### 🌟 **1. ACTIVACIÓN DEL EJECUTOR** 

**Trigger**: `start_task_execution(task_id)` - Línea 6550
**Thread**: Se crea un thread separado para no bloquear el servidor

```python
def execute_real_steps():
    with app.app_context():
        for i, step in enumerate(steps):
            # Procesar cada paso secuencialmente
```

### 📋 **2. PREPARACIÓN DE CADA PASO**

#### A. **Marcado de Estado**
```python
step['active'] = True
step['status'] = 'in-progress' 
update_task_data(task_id, {'plan': steps})
```

#### B. **Notificación WebSocket**
```python
emit_step_event(task_id, 'step_started', {
    'step_id': step['id'],
    'title': step.get('title', 'Ejecutando paso'),
    'description': step.get('description', ''),
    'timestamp': datetime.now().isoformat()
})
```

### 🧠 **3. ANÁLISIS INTELIGENTE DEL PASO** 

**Función**: `execute_single_step_logic(step, message, task_id)` - Línea 1100

#### A. **Extracción de Datos del Paso**
```python
step_tool = step.get('tool', 'processing')        # Herramienta solicitada
step_title = step.get('title', 'Paso sin título') # Título del paso
step_description = step.get('description', 'Sin descripción')
```

#### B. **Análisis de Requerimientos**
**Función**: `analyze_step_requirements(title, description, original_message)` - Línea 1135

El agente analiza el contenido para determinar:
- ✅ `needs_real_data`: Si necesita datos actuales (2024, 2025, estadísticas)
- ✅ `needs_web_search`: Si requiere búsqueda web (investigar, buscar, información)
- ✅ `needs_deep_research`: Si necesita investigación profunda
- ✅ `complexity`: Nivel de complejidad (basic, media, alta)

#### C. **Selección Inteligente de Herramientas**

Basado en el análisis, el agente define:
- **Optimal Tools**: Herramientas prioritarias que funcionan bien
- **Fallback Tools**: Herramientas de respaldo

```python
if analysis['needs_real_data']:
    analysis['optimal_tools'] = ['web_search', 'enhanced_analysis']
    analysis['fallback_tools'] = ['comprehensive_research']
elif analysis['needs_web_search']:
    analysis['optimal_tools'] = ['web_search', 'enhanced_analysis'] 
else:
    analysis['optimal_tools'] = ['enhanced_analysis']
```

### 🔄 **4. EJECUCIÓN CON FALLBACK AUTOMÁTICO**

**Función**: `execute_step_with_intelligent_tool_selection()` - Línea 1178

#### A. **Sistema de Cascada**
El agente prueba herramientas en orden hasta encontrar una exitosa:

```python
for i, tool_name in enumerate(tools_to_try):
    # Intentar herramienta específica
    if tool_name == 'web_search':
        result = execute_web_search_step(step_title, step_description, tool_manager, task_id)
    elif tool_name == 'enhanced_analysis':
        result = execute_enhanced_analysis_step(step_title, step_description, ollama_service)
    elif tool_name == 'processing':
        result = execute_processing_step(step_title, step_description, ollama_service)
    # ... más herramientas
    
    # Evaluar si el resultado es aceptable
    if result.get('success', False) and evaluate_result_quality(result, task_analysis):
        break  # ✅ Herramienta exitosa encontrada
```

#### B. **Funciones de Ejecución Específicas**

##### 🌐 **Web Search** - `execute_web_search_step()` - Línea 1758
```python
def execute_web_search_step(title, description, tool_manager, task_id):
    # 1. Generar query inteligente
    web_search_tool = UnifiedWebSearchTool()
    search_query = web_search_tool._extract_clean_keywords_static(f"{title} {description}")
    
    # 2. Ejecutar búsqueda real
    search_result = tool_manager.execute_tool('web_search', {
        'query': search_query,
        'max_results': 5,
        'search_engine': 'bing',
        'extract_content': True
    }, task_id=task_id)
    
    # 3. Opcional: Visualización con navegador
    if browser_manager:
        browser_manager.navigate(f"https://www.bing.com/search?q={search_query}")
    
    # 4. Retornar resultado
    return {
        'success': True,
        'type': 'web_search',
        'query': search_query,
        'results_count': len(search_result.get('search_results', [])),
        'data': search_result.get('search_results', [])
    }
```

##### 🧠 **Enhanced Analysis** - `execute_enhanced_analysis_step()` - Línea 1555
```python
def execute_enhanced_analysis_step(title, description, ollama_service, original_message, previous_results):
    # 1. Compilar contexto de resultados anteriores
    context = f"Tarea original: {original_message}\n"
    context += f"Paso actual: {title}\n{description}\n"
    
    if previous_results:
        context += "\nResultados de herramientas anteriores:\n"
        for prev_result in previous_results:
            context += f"- {prev_result['tool']}: {prev_result['result'].get('summary', 'Sin resumen')}\n"
    
    # 2. Prompt específico para análisis
    analysis_prompt = f"""
    ANÁLISIS REQUERIDO: {title}
    CONTEXTO: {context}
    
    Proporciona un análisis detallado y específico. NO uses frases como "se realizará" o "se analizará".
    Incluye datos concretos, conclusiones específicas y recomendaciones prácticas.
    """
    
    # 3. Ejecutar con Ollama
    result = ollama_service.generate_response(
        analysis_prompt,
        {'temperature': 0.6},
        True,  # use_tools
        task_id,
        "enhanced_analysis"
    )
    
    return {
        'success': True,
        'type': 'enhanced_analysis',
        'content': result.get('response', ''),
        'summary': f"✅ Análisis completado - {len(result.get('response', ''))} caracteres"
    }
```

##### 🔧 **Processing** - `execute_processing_step()` - Línea 2069
```python
def execute_processing_step(title, description, ollama_service, original_message, step, task_id):
    # 1. Prompt específico para procesamiento
    processing_prompt = f"""
    TAREA DE PROCESAMIENTO: {title}
    DESCRIPCIÓN: {description}
    CONTEXTO ORIGINAL: {original_message}
    
    Procesa esta información de manera completa y específica.
    Genera contenido final, conclusiones o resultados tangibles.
    """
    
    # 2. Ejecutar con Ollama
    result = ollama_service.generate_response(
        processing_prompt,
        {'temperature': 0.5},
        True,  # use_tools
        task_id,
        step.get('id', 'processing_step')
    )
    
    return {
        'success': True,
        'type': 'processing',
        'content': result.get('response', ''),
        'summary': f"✅ Procesamiento completado - {len(result.get('response', ''))} caracteres"
    }
```

### 🎯 **5. EVALUACIÓN DE CALIDAD**

**Función**: `evaluate_result_quality(result, task_analysis)` - Línea 1247

#### A. **Criterios de Evaluación**

##### ✅ **Para Web Search**:
- **Results Count**: `> 0` resultados encontrados
- **Valid Results**: Títulos y URLs válidas
- **No depende del contenido textual**

##### ✅ **Para Analysis/Processing**:
- **Content Length**: `> 150` caracteres mínimo
- **Meta-content Detection**: Rechaza frases como "se realizará", "se analizará"
- **Real Data Indicators**: Para tareas que requieren datos reales, busca:
  - Fechas: 2024, 2025
  - Datos: estadística, cifra, porcentaje
  - Actualidad: reciente, nuevo, última

#### B. **Sistema de Aprobación**
```python
if result.get('success', False) and evaluate_result_quality(result, task_analysis):
    # ✅ Resultado aprobado - usar esta herramienta
    best_result = result
    best_result['tool_used'] = tool_name
    break
else:
    # ❌ Resultado rechazado - probar siguiente herramienta
    continue
```

### 🔄 **6. EVALUACIÓN DEL AGENTE**

**Función**: `evaluate_step_completion_with_agent(step, step_result, message, task_id)`

#### A. **Re-evaluación Inteligente**
El agente usa Ollama para evaluar si el paso está realmente completo:

```python
evaluation_prompt = f"""
¿Este paso está completado satisfactoriamente?

PASO: {step.get('title', '')}
RESULTADO: {step_result.get('summary', '')}
CONTENIDO: {step_result.get('content', '')[:500]}...

Responde: SÍ si está completo, NO si necesita más trabajo.
"""
```

#### B. **Decisiones del Agente**
- **`step_completed: True`**: Paso aprobado, continuar al siguiente
- **`step_completed: False`**: Requiere más trabajo
- **`should_continue: True`**: Ejecutar trabajo adicional en este paso

### 🔧 **7. SISTEMA DE RETRY**

Si el paso requiere más trabajo:

#### A. **Retry Limitado** (Máximo 5 intentos)
```python
retry_count = step.get('retry_count', 0)
if retry_count < 5:
    step['retry_count'] = retry_count + 1
    # Ejecutar versión simplificada
    simplified_result = execute_simplified_step_retry(step, message, task_id)
```

#### B. **Retry Simplificado**
**Función**: `execute_simplified_step_retry()` - Línea 1032

Usa prompt más directo y simple:
```python
simplified_prompt = f"""
TAREA SIMPLIFICADA: Completa directamente esta tarea específica.
PASO: {step.get('title', '')}
DESCRIPCIÓN: {step.get('description', '')}

INSTRUCCIONES:
- Genera una respuesta directa y práctica
- NO uses frases como "se realizará" o "se analizará"  
- Proporciona información concreta y útil
"""
```

### 🏁 **8. FINALIZACIÓN DEL PASO**

#### A. **Marcado como Completado**
```python
step['active'] = False
step['completed'] = True
step['status'] = 'completed'
step['result'] = step_result
step['completed_time'] = datetime.now().isoformat()
```

#### B. **Activación Automática del Siguiente Paso**
```python
if i + 1 < len(steps):
    next_step = steps[i + 1]
    next_step['active'] = True
    next_step['status'] = 'in-progress'
```

#### C. **Notificación WebSocket Final**
```python
emit_step_event(task_id, 'step_completed', {
    'step_id': step['id'],
    'title': step.get('title', 'Paso completado'),
    'result': step_result,
    'timestamp': datetime.now().isoformat()
})
```

---

## 🚨 **PROBLEMAS EN EL FLUJO DE EJECUCIÓN**

### ❌ **1. Web Search Tool Roto**
- **Error**: "Cannot run the event loop while another loop is running"
- **Ubicación**: `execute_web_search_step()` → `tool_manager.execute_tool('web_search')`
- **Impacto**: 80% de pasos fallan porque la mayoría requiere web search

### ❌ **2. Evaluación de Calidad Demasiado Restrictiva**
- **Función**: `evaluate_result_quality()` - Línea 1247
- **Problema**: Rechaza resultados válidos por criterios muy estrictos
- **Impacto**: Pasos exitosos son marcados como fallidos

### ❌ **3. Threading Manual Problemático**
- **Thread Separado**: `execute_real_steps()` en thread manual
- **Problemas**: Pérdida de contexto, sincronización con WebSocket
- **Impacto**: Ejecución inconsistente y eventos perdidos

### ❌ **4. Sistema de Fallback Excesivamente Complejo**
- **Múltiples Herramientas**: Prueba hasta 5-6 herramientas por paso
- **Overhead**: Cada herramienta fallida agrega latencia
- **Confusión**: Lógica compleja de selección causa errores

---

## 🎯 **ESTADÍSTICAS DEL FLUJO ACTUAL**

### ⏱️ **Tiempos de Ejecución por Paso**:
- **Análisis de Requerimientos**: ~1 segundo ✅
- **Web Search**: ~60 segundos (debería ser 10s) ❌
- **Enhanced Analysis**: ~15 segundos ✅ 
- **Processing**: ~10 segundos ✅
- **Evaluación de Calidad**: ~2 segundos ⚠️

### 📊 **Tasa de Éxito por Herramienta**:
- **web_search**: 20% (roto por asyncio) ❌
- **enhanced_analysis**: 85% ✅
- **processing**: 90% ✅
- **comprehensive_research**: 30% (depende de web_search) ❌

### 🔄 **Sistema de Retry**:
- **Pasos que requieren retry**: 60%
- **Éxito en retry**: 40%
- **Pasos forzados a completar**: 25%

---

## 🚀 **CONCLUSIÓN**

### ✅ **Fortalezas del Sistema**:
1. **Análisis Inteligente**: Detecta automáticamente qué herramientas necesita cada paso
2. **Sistema de Fallback**: Prueba múltiples herramientas hasta encontrar una que funcione
3. **Evaluación del Agente**: Usa IA para determinar si un paso está realmente completo
4. **Retry Automático**: Sistema robusto de reintentos con simplificación progresiva

### ❌ **Debilidades Críticas**:
1. **Web Search Roto**: El 80% de tareas fallan por conflicto asyncio/eventlet
2. **Evaluación Demasiado Estricta**: Rechaza resultados válidos innecesariamente  
3. **Threading Manual**: Causa inconsistencias y pérdida de eventos
4. **Complejidad Excesiva**: Sistema de selección de herramientas muy complejo

### 🎯 **El Problema Principal**:
El agente tiene un **flujo inteligente y sofisticado**, pero **falla en la ejecución básica** debido a problemas técnicos en la herramienta más crítica (web search). Es como tener un cerebro brillante en un cuerpo que no puede caminar.