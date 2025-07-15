# INSTRUCCIONES CRÍTICAS DE DESARROLLO

## 🚨 **REGLA FUNDAMENTAL: NO DUPLICAR FUNCIONALIDADES**

### **ANTES DE AGREGAR CUALQUIER FUNCIONALIDAD:**
1. **CONSULTAR AL USUARIO** - Cualquier nueva UI/UX debe ser aprobada explícitamente
2. **VERIFICAR DUPLICACIÓN** - Revisar si ya existe funcionalidad similar
3. **DOCUMENTAR EN PLAN.md** - Todo cambio debe estar detallado en el plan de trabajo

---

## 📋 **FUNCIONALIDADES EXISTENTES - NO DUPLICAR**

### **Sistema de Estado del Agente:**
- ✅ **Plan de Acción** - Muestra pasos y progreso de la tarea
- ✅ **Barra de Estado sobre Chatbox** - Estado granular del agente en tiempo real
- ❌ **NO AGREGAR** - Componentes adicionales de estado/progreso

### **Sistema de Gestión de Tareas:**
- ✅ **Sidebar con Tareas** - Lista y gestión de tareas
- ✅ **TaskView** - Vista detallada de cada tarea
- ❌ **NO AGREGAR** - Gestores adicionales de tareas

### **Sistema de Configuración:**
- ✅ **ConfigPanel** - Panel de configuración del agente
- ❌ **NO AGREGAR** - Paneles adicionales de configuración

---

## 🎯 **PRINCIPIOS DEL SISTEMA AUTÓNOMO**

### **PARA EL USUARIO:**
- **Simplicidad** - Interfaz clara y sin elementos innecesarios
- **Autonomía** - El sistema debe funcionar sin intervención manual
- **Información Relevante** - Solo mostrar lo que el usuario necesita saber

### **PARA EL DESARROLLADOR:**
- **Funcionalidad Backend** - Puede existir para operaciones internas
- **Sin Exposición UI** - No crear interfaces para funcionalidades internas
- **Documentación** - Todo debe estar documentado en PLAN.md

---

## 📝 **PROCESO DE DESARROLLO**

### **ANTES DE CUALQUIER CAMBIO:**
1. **Revisar PLAN.md** - Verificar si está contemplado en el plan
2. **Consultar al Usuario** - Obtener aprobación explícita para nuevas UI/UX
3. **Verificar Duplicación** - Asegurar que no existe funcionalidad similar

### **DURANTE EL DESARROLLO:**
1. **Actualizar PLAN.md** - Documentar prolijamente cada cambio
2. **Mantener Simplicidad** - Evitar complejidad innecesaria
3. **Testing Completo** - Verificar que no se rompa funcionalidad existente

### **DESPUÉS DEL DESARROLLO:**
1. **Documentar en PLAN.md** - Marcar como completado
2. **Cleanup** - Eliminar código innecesario
3. **Validation** - Confirmar que funciona como esperado

---

## ⚠️ **ELEMENTOS A ELIMINAR/EVITAR**

### **COMPONENTES DUPLICADOS:**
- ❌ **Advanced Task Manager** - Funcionalidad interna, no UI
- ❌ **AgentStatus** - Duplica Plan de Acción y barra de estado
- ❌ **Múltiples indicadores de progreso** - Solo uno por funcionalidad

### **FUNCIONALIDADES PROHIBIDAS:**
- ❌ **Botones "Advanced"** - Sistema debe ser autónomo
- ❌ **Controles manuales** - Solo los absolutamente necesarios
- ❌ **Información técnica** - Solo para debug interno

---

## 🔧 **MANTENIMIENTO DEL CÓDIGO**

### **LIMPIEZA REGULAR:**
- Eliminar componentes no utilizados
- Consolidar funcionalidades similares
- Simplificar interfaces complejas

### **DOCUMENTACIÓN:**
- Mantener PLAN.md actualizado
- Documentar razones de cada decisión
- Explicar arquitectura claramente

---

## 📊 **PLAN DE TRABAJO**

**UBICACIÓN:** `/app/PLAN.md`

### **CONTENIDO REQUERIDO:**
- ✅ **Tareas Completadas** - Detalle prolijo de lo realizado
- 📋 **Tareas Pendientes** - Lista clara de lo que falta
- 🔄 **Tareas en Progreso** - Estado actual del desarrollo
- 📝 **Decisiones Tomadas** - Justificación de cambios importantes

---

## 🎯 **OBJETIVO FINAL**

**SISTEMA AUTÓNOMO LIMPIO:**
- Interfaz simple y eficiente
- Funcionalidad robusta sin duplicaciones
- Experiencia de usuario fluida
- Código mantenible y documentado

---

**RECORDATORIO:** Este es un sistema AUTÓNOMO. El usuario no debe gestionar manualmente los procesos internos. La interfaz debe ser simple, clara y sin elementos innecesarios.