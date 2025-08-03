/**
 * TASK UTILITIES - ANTI-DUPLICACIÓN Y GESTIÓN DE IDs ÚNICOS
 * Utilidades centralizadas para prevenir la duplicación de tareas
 */

// Generador de IDs únicos más robusto
let taskIdCounter = 0;

/**
 * Genera un ID único para tareas usando una combinación de timestamp, 
 * contador incremental y número aleatorio para máxima unicidad
 */
export const generateUniqueTaskId = (): string => {
  const timestamp = Date.now();
  const counter = ++taskIdCounter;
  const random = Math.floor(Math.random() * 10000);
  
  return `task-${timestamp}-${counter}-${random}`;
};

/**
 * Genera un ID temporal único para tareas antes del backend
 */
export const generateTempTaskId = (): string => {
  const timestamp = Date.now();
  const counter = ++taskIdCounter;
  const random = Math.floor(Math.random() * 10000);
  
  return `temp-task-${timestamp}-${counter}-${random}`;
};

/**
 * Validación para evitar IDs duplicados
 */
export const isValidTaskId = (taskId: string): boolean => {
  return taskId && taskId.length > 0 && !taskId.includes('undefined') && !taskId.includes('null');
};

/**
 * Cache para prevenir creaciones duplicadas rápidas
 */
const creationCache = new Set<string>();

/**
 * Previene la creación de tareas duplicadas mediante cache temporal
 */
export const preventDuplicateCreation = (messageContent: string): boolean => {
  const cacheKey = messageContent.trim().toLowerCase();
  
  if (creationCache.has(cacheKey)) {
    console.warn('🚫 Preventing duplicate task creation for:', cacheKey);
    return false; // Prevenir duplicado
  }
  
  // Agregar al cache por 2 segundos
  creationCache.add(cacheKey);
  setTimeout(() => {
    creationCache.delete(cacheKey);
  }, 2000);
  
  return true; // Permitir creación
};

/**
 * Debounce map para prevenir múltiples llamadas rápidas
 */
const debounceMap = new Map<string, NodeJS.Timeout>();

/**
 * Debounce para funciones de creación de tareas
 */
export const debounceTaskCreation = (key: string, callback: () => void, delay: number = 500): void => {
  // Limpiar timeout anterior si existe
  if (debounceMap.has(key)) {
    clearTimeout(debounceMap.get(key)!);
  }
  
  // Crear nuevo timeout
  const timeoutId = setTimeout(() => {
    callback();
    debounceMap.delete(key);
  }, delay);
  
  debounceMap.set(key, timeoutId);
};

/**
 * Validación de integridad de tarea
 */
export const validateTask = (task: any): boolean => {
  if (!task || typeof task !== 'object') {
    console.error('❌ Task is not a valid object:', task);
    return false;
  }
  
  if (!isValidTaskId(task.id)) {
    console.error('❌ Task has invalid ID:', task.id);
    return false;
  }
  
  if (!task.title || task.title.trim().length === 0) {
    console.error('❌ Task has invalid title:', task.title);
    return false;
  }
  
  // ✅ CRITICAL FIX: Log and preserve plan data
  if (task.plan && Array.isArray(task.plan) && task.plan.length > 0) {
    console.log(`📋 [VALIDATE-TASK] Task ${task.id} has valid plan with ${task.plan.length} steps`);
    task.plan.forEach((step, index) => {
      if (step.completed) {
        console.log(`  ✅ Step ${index + 1}: ${step.title} (COMPLETED)`);
      } else if (step.active) {
        console.log(`  🟡 Step ${index + 1}: ${step.title} (ACTIVE)`);
      } else {
        console.log(`  ⏸️  Step ${index + 1}: ${step.title} (PENDING)`);
      }
    });
  } else {
    console.log(`📋 [VALIDATE-TASK] Task ${task.id} has no plan or empty plan`);
  }
  
  return true;
};

/**
 * Utilidad para limpiar tareas duplicadas en un array
 */
export const removeDuplicateTasks = (tasks: any[]): any[] => {
  const seen = new Set<string>();
  const uniqueTasks = [];
  
  for (const task of tasks) {
    if (task && task.id && !seen.has(task.id)) {
      seen.add(task.id);
      uniqueTasks.push(task);
    } else {
      console.warn('🔄 Removing duplicate task:', task?.id);
    }
  }
  
  return uniqueTasks;
};

/**
 * Debug utilities para identificar problemas de duplicación
 */
export const debugTaskDuplication = (tasks: any[], context: string): void => {
  const idCount = new Map<string, number>();
  
  tasks.forEach(task => {
    if (task && task.id) {
      const count = idCount.get(task.id) || 0;
      idCount.set(task.id, count + 1);
    }
  });
  
  const duplicates = Array.from(idCount.entries()).filter(([_, count]) => count > 1);
  
  if (duplicates.length > 0) {
    console.error(`🚨 DUPLICATE TASKS DETECTED in ${context}:`, duplicates);
    duplicates.forEach(([taskId, count]) => {
      console.error(`  - Task ID "${taskId}" appears ${count} times`);
    });
  } else {
    console.log(`✅ No duplicates detected in ${context}`);
  }
};