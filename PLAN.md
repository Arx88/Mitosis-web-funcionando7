# PLAN.md - Visión y Arquitectura del Agente Mitosis V5

## 🎯 Objetivo General

Desarrollar un agente autónomo avanzado que implemente un ciclo OODA completo (Observar, Orientar, Decidir, Actuar) con capacidades de **Metacognición** y **Aprendizaje Continuo**. El agente debe ser capaz de:

- Percibir y procesar inputs multimodales
- Planificar dinámicamente usando LLM
- Ejecutar tareas con replanificación automática ante obstáculos
- Reflexionar sobre sus propias acciones y aprender de ellas
- Mejorar continuamente su rendimiento

## 🧠 Arquitectura de 5 Fases

### **Fase 1: Percepción e Interpretación (El "Input")**

**Responsabilidades:**
- Recepción multimodal (texto, imágenes, audio, archivos)
- Análisis profundo de intención más allá de palabras clave
- Contextualización usando memoria episódica
- Desambiguación inteligente con HumanInTheLoop cuando sea necesario

**Componentes Clave:**
- `MultimodalInputProcessor`: Procesa diferentes tipos de input
- `IntentionAnalyzer`: Usa LLM para análisis semántico profundo
- `ContextRetriever`: Recupera contexto relevante de memoria
- `AmbiguityResolver`: Solicita clarificación cuando es necesario

### **Fase 2: Planificación Estratégica (La "Mente")**

**Responsabilidades:**
- Descomposición dinámica de tareas usando LLM
- Selección inteligente de herramientas basada en razonamiento
- Generación de planes jerárquicos con dependencias (DAG)
- Manejo de contingencias y puntos de control

**Componentes Clave:**
- `DynamicTaskPlanner`: Genera planes usando LLM en tiempo real
- `ToolReasoner`: Razona sobre capacidades de herramientas
- `ContingencyManager`: Maneja escenarios de fallo y alternativas
- `DependencyGraph`: Gestiona dependencias entre sub-tareas

### **Fase 3: Ejecución Supervisada (La "Acción")**

**Responsabilidades:**
- Invocación coordinada de herramientas
- Monitorización en tiempo real del progreso
- **Replanificación dinámica** ante fallos o resultados inesperados
- Manejo sofisticado de errores con análisis de causas

**Componentes Clave:**
- `ExecutionOrchestrator`: Coordina la ejecución del plan
- `ToolInvoker`: Ejecuta herramientas con manejo de errores
- `ReplanningEngine`: **CLAVE** - Replanifica cuando hay obstáculos
- `ErrorAnalyzer`: Analiza tipos de error para informar replanificación

### **Fase 4: Síntesis y Auto-crítica (La "Reflexión")**

**Responsabilidades:**
- Consolidación inteligente de resultados
- **Auto-reflexión** sobre la calidad y eficiencia de acciones
- Análisis de metacognición ("¿Cómo lo hice? ¿Podría hacerlo mejor?")
- Actualización de memoria procedimental con lecciones aprendidas

**Componentes Clave:**
- `ResultSynthesizer`: Consolida resultados de múltiples herramientas
- `SelfReflectionEngine`: **CLAVE** - Evalúa su propio rendimiento
- `MetacognitionAnalyzer`: Analiza patrones de pensamiento y decisión
- `ProceduralMemoryUpdater`: Actualiza estrategias basado en reflexión

### **Fase 5: Generación de Respuesta y Cierre del Bucle**

**Responsabilidades:**
- Composición de respuestas adaptadas al contexto y usuario
- Solicitud proactiva de feedback
- Adaptación de tono y estilo
- Cierre del ciclo con aprendizaje

**Componentes Clave:**
- `ResponseComposer`: Genera respuestas contextualizadas
- `FeedbackSolicitor`: Pide feedback de forma inteligente
- `StyleAdapter`: Adapta tono según contexto
- `LearningLoop`: Cierra el ciclo con aprendizaje activo

## 🔄 Ciclo OODA + Metacognición

### **Observar (Percepción)**
- `classify_message_mode`: Clasificación inicial
- `retrieve_relevant_context`: Recuperación de contexto
- **NUEVO**: `MultimodalInputProcessor` para inputs no-textuales
- **NUEVO**: `IntentionAnalyzer` para análisis semántico profundo

### **Orientar (Planificación)**
- `generate-plan`: Generación de planes (actual)
- `TaskOrchestrator`: Orquestación de tareas
- **NUEVO**: `DynamicTaskPlanner` con LLM
- **NUEVO**: `ToolReasoner` para selección inteligente

### **Decidir (Selección de Herramientas)**
- `ToolManager`: Gestión de herramientas actual
- `execute_agent_task`: Lógica de ejecución
- **NUEVO**: Razonamiento sobre capacidades de herramientas
- **NUEVO**: Manejo de contingencias en decisiones

### **Actuar (Ejecución)**
- `ExecutionEngine`: Motor de ejecución actual
- `ToolManager.execute_tool`: Ejecución de herramientas
- **NUEVO**: `ReplanningEngine` - **CRÍTICO**
- **NUEVO**: `ErrorAnalyzer` para análisis de errores

### **Metacognición (Reflexión y Aprendizaje)**
- **NUEVO**: `SelfReflectionEngine` - **CRÍTICO**
- **NUEVO**: `MetacognitionAnalyzer`
- **NUEVO**: `ProceduralMemoryUpdater`
- **NUEVO**: `LearningLoop` para aprendizaje continuo

## 📊 Componentes de Memoria Avanzados

### **Memoria Episódica Enriquecida**
- Almacena no solo conversaciones, sino planes, ejecuciones y resultados
- Incluye metadata sobre éxito/fallo, tiempo de ejecución, herramientas usadas
- Permite análisis de patrones históricos

### **Memoria Procedimental Inteligente**
- Almacena estrategias exitosas y fallidas
- Se actualiza automáticamente basado en reflexión
- Influye en planificación futura

### **Memoria Semántica Contextual**
- Conocimiento sobre dominios específicos
- Relaciones entre conceptos y herramientas
- Actualización dinámica basada en experiencias

## 🎯 Características Diferenciadoras Clave

### **1. Replanificación Dinámica (CRÍTICO)**
- Cuando una herramienta falla, el agente no se detiene
- Analiza el error y genera un plan alternativo
- Vuelve a la fase de planificación con nueva información
- Ejemplo: Si web_search falla → intenta deep_research → pregunta al usuario

### **2. Auto-Reflexión y Metacognición (CRÍTICO)**
- Evalúa la calidad de sus propias respuestas
- Analiza la eficiencia de sus planes
- Aprende de errores y éxitos
- Mejora estrategias futuras automáticamente

### **3. Aprendizaje Continuo**
- Actualiza memoria procedimental basado en reflexión
- Mejora selección de herramientas con el tiempo
- Adapta estrategias según patrones históricos
- Personaliza respuestas según preferencias del usuario

### **4. Multimodalidad Real**
- Procesa imágenes, audio, archivos de datos
- Entiende contexto visual y auditivo
- Integra información multimodal en decisiones
- Responde de forma multimodal cuando es apropiado

### **5. Interacción Humana Inteligente**
- Detecta ambigüedad y pide clarificación
- Solicita feedback proactivamente
- Adapta comunicación al contexto
- Aprende de interacciones pasadas

## 🚀 Prioridades de Implementación

### **Prioridad Alta (Implementar Primero)**
1. **ReplanningEngine** - Replanificación dinámica
2. **SelfReflectionEngine** - Auto-reflexión y metacognición
3. **DynamicTaskPlanner** - Planificación con LLM
4. **ErrorAnalyzer** - Análisis sofisticado de errores

### **Prioridad Media**
1. **ToolReasoner** - Selección inteligente de herramientas
2. **ProceduralMemoryUpdater** - Aprendizaje de estrategias
3. **MultimodalInputProcessor** - Soporte multimodal
4. **FeedbackSolicitor** - Interacción proactiva

### **Prioridad Baja**
1. **MetacognitionAnalyzer** - Análisis avanzado de patrones
2. **StyleAdapter** - Adaptación de estilo
3. **ContingencyManager** - Manejo avanzado de contingencias
4. **LearningLoop** - Optimizaciones de aprendizaje

## 📈 Métricas de Éxito

### **Rendimiento Operacional**
- Tasa de éxito en replanificación tras fallos
- Tiempo de respuesta con replanificación
- Número de herramientas utilizadas eficientemente
- Calidad de consolidación de resultados

### **Aprendizaje y Mejora**
- Mejora en selección de herramientas con el tiempo
- Reducción de errores repetitivos
- Incremento en satisfacción del usuario
- Precisión en auto-evaluación de respuestas

### **Interacción Usuario**
- Reducción en necesidad de clarificación
- Aumento en relevancia de respuestas
- Mejora en adaptación de estilo
- Incremento en solicitud proactiva de feedback

## 🔧 Integración con Arquitectura Actual

### **Componentes Existentes a Extender**
- `TaskOrchestrator` → `ExecutionOrchestrator`
- `ToolManager` → `ToolInvoker` + `ToolReasoner`
- `memory_manager` → Sistema de memoria enriquecido
- `ExecutionEngine` → `ReplanningEngine`

### **Nuevos Módulos a Desarrollar**
- `src/agents/` - Agentes especializados
- `src/reflection/` - Módulos de reflexión
- `src/planning/` - Planificación avanzada
- `src/multimodal/` - Procesamiento multimodal
- `src/learning/` - Aprendizaje continuo

## 🎬 Ejemplo de Flujo Completo

```
1. Usuario: "Analiza las ventas de Q4 y sugiere mejoras"

2. PERCEPCIÓN:
   - Detecta: tarea de análisis de datos + recomendaciones
   - Recupera: contexto de análisis anteriores
   - Identifica: necesidad de datos estructurados

3. PLANIFICACIÓN:
   - LLM genera plan: [Buscar datos Q4 → Análizar tendencias → Identificar problemas → Sugerir mejoras]
   - Selecciona herramientas: [file_manager, data_analyzer, web_search]
   - Define contingencias: Si no hay datos → pedir al usuario

4. EJECUCIÓN:
   - Ejecuta file_manager → FALLA (no encuentra archivos)
   - REPLANIFICACIÓN: Analiza error → Decide pedir datos al usuario
   - Ejecuta web_search → ÉXITO (encuentra datos públicos)
   - Ejecuta data_analyzer → ÉXITO

5. REFLEXIÓN:
   - Evalúa: "Plan inicial falló, pero replanificación funcionó"
   - Aprende: "Para análisis de ventas, verificar disponibilidad de datos primero"
   - Actualiza memoria procedimental

6. RESPUESTA:
   - Consolida resultados de análisis
   - Pide feedback: "¿Te gustaría que profundice en algún aspecto?"
   - Adapta estilo: formal para análisis de negocios
```

## 🔮 Visión a Largo Plazo

**Mitosis V5** debe convertirse en un agente que:
- Aprende y mejora continuamente de cada interacción
- Se adapta dinámicamente a obstáculos y cambios
- Desarrolla estrategias personalizadas para cada usuario
- Maneja tareas completamente nuevas sin programación adicional
- Reflexiona sobre su propio rendimiento y lo optimiza
- Colabora inteligentemente con humanos cuando es necesario

Este agente no solo ejecuta tareas, sino que **piensa sobre cómo las ejecuta** y **aprende cómo hacerlo mejor**.

