/**
 * MEMORY MANAGER AISLADO POR TAREA
 * Cada TaskView tiene su propia memoria completamente independiente
 * SOLUCIÓN AL PROBLEMA DE MEMORIA COMPARTIDA
 */

import { useState, useEffect, useCallback } from 'react';

export interface IsolatedMemoryFile {
  id: string;
  name: string;
  type: 'research_report' | 'uploaded_file' | 'agent_file';
  content: string;
  metadata: {
    size: number;
    createdAt: Date;
    source: string;
    summary?: string;
    wordCount?: number;
    tags?: string[];
  };
  isActive: boolean;
  priority: 'low' | 'medium' | 'high';
}

interface IsolatedMemoryContext {
  activeFiles: IsolatedMemoryFile[];
  totalFiles: number;
  combinedContent: string;
  summary: string;
}

interface UseIsolatedMemoryManagerProps {
  taskId: string;
}

export const useIsolatedMemoryManager = ({ taskId }: UseIsolatedMemoryManagerProps) => {
  const [memoryFiles, setMemoryFiles] = useState<IsolatedMemoryFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Clave única para esta tarea en localStorage
  const storageKey = `mitosis_memory_${taskId}`;

  // ========================================================================
  // CARGAR Y GUARDAR MEMORIA ESPECÍFICA DE LA TAREA
  // ========================================================================

  // Load memory files específicos de esta tarea desde localStorage
  useEffect(() => {
    console.log(`💾 [MEMORY-${taskId}] Loading memory from localStorage`);
    
    const savedMemory = localStorage.getItem(storageKey);
    if (savedMemory) {
      try {
        const parsed = JSON.parse(savedMemory);
        const restoredFiles = parsed.map((file: any) => ({
          ...file,
          metadata: {
            ...file.metadata,
            createdAt: new Date(file.metadata.createdAt)
          }
        }));
        
        setMemoryFiles(restoredFiles);
        console.log(`✅ [MEMORY-${taskId}] Restored ${restoredFiles.length} files from storage`);
      } catch (error) {
        console.error(`❌ [MEMORY-${taskId}] Error loading memory files:`, error);
      }
    } else {
      console.log(`ℹ️ [MEMORY-${taskId}] No existing memory found`);
    }
  }, [taskId, storageKey]);

  // Save memory files específicos de esta tarea a localStorage
  useEffect(() => {
    if (memoryFiles.length > 0) {
      console.log(`💾 [MEMORY-${taskId}] Saving ${memoryFiles.length} files to storage`);
      localStorage.setItem(storageKey, JSON.stringify(memoryFiles));
    }
  }, [memoryFiles, storageKey, taskId]);

  // ========================================================================
  // FUNCIONES DE GESTIÓN DE MEMORIA AISLADA
  // ========================================================================

  // Add a file to memory (con verificación de duplicados específica por tarea)
  const addMemoryFile = useCallback((file: Omit<IsolatedMemoryFile, 'id' | 'isActive' | 'priority'>) => {
    console.log(`📁 [MEMORY-${taskId}] Adding file:`, file.name);
    
    // Check for duplicates based on name and type SOLO en esta tarea
    const isDuplicate = memoryFiles.some(existingFile => 
      existingFile.name === file.name && 
      existingFile.type === file.type &&
      existingFile.metadata.source === file.metadata.source
    );

    if (isDuplicate) {
      console.warn(`⚠️ [MEMORY-${taskId}] File "${file.name}" already exists in task memory`);
      return null; // Return null to indicate duplicate
    }

    const newFile: IsolatedMemoryFile = {
      ...file,
      id: `memory_${taskId}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      isActive: true,
      priority: 'medium'
    };

    setMemoryFiles(prev => {
      const updated = [...prev, newFile];
      console.log(`✅ [MEMORY-${taskId}] File added. Total files: ${updated.length}`);
      return updated;
    });
    
    return newFile.id;
  }, [memoryFiles, taskId]);

  // Add research report to memory específico de la tarea
  const addResearchReportToMemory = useCallback((report: {
    query: string;
    executiveSummary: string;
    keyFindings: string[];
    recommendations: string[];
    sourcesAnalyzed: number;
    wordCount?: number;
  }) => {
    console.log(`📊 [MEMORY-${taskId}] Adding research report:`, report.query);
    
    const reportName = `Investigación: ${report.query}`;
    
    // Check for duplicates SOLO en esta tarea
    const isDuplicate = memoryFiles.some(existingFile => 
      existingFile.name === reportName && 
      existingFile.type === 'research_report'
    );

    if (isDuplicate) {
      console.warn(`⚠️ [MEMORY-${taskId}] Research report "${reportName}" already exists in task memory`);
      return null;
    }

    const content = `
# Informe de Investigación: ${report.query}

## Resumen Ejecutivo
${report.executiveSummary}

## Hallazgos Clave
${report.keyFindings.map((finding, index) => `${index + 1}. ${finding}`).join('\n')}

## Recomendaciones
${report.recommendations.map((rec, index) => `${index + 1}. ${rec}`).join('\n')}

## Metadatos
- Fuentes analizadas: ${report.sourcesAnalyzed}
- Palabras: ${report.wordCount || 'N/A'}
- Fecha: ${new Date().toLocaleString()}
- Tarea: ${taskId}
    `.trim();

    return addMemoryFile({
      name: reportName,
      type: 'research_report',
      content,
      metadata: {
        size: content.length,
        createdAt: new Date(),
        source: 'deep_research',
        summary: report.executiveSummary.substring(0, 200) + '...',
        wordCount: report.wordCount,
        tags: ['investigación', 'informe', 'análisis', `task-${taskId}`]
      }
    });
  }, [addMemoryFile, memoryFiles, taskId]);

  // Remove a file from memory específico de la tarea
  const removeMemoryFile = useCallback((fileId: string) => {
    console.log(`🗑️ [MEMORY-${taskId}] Removing file:`, fileId);
    
    setMemoryFiles(prev => {
      const updated = prev.filter(file => file.id !== fileId);
      console.log(`✅ [MEMORY-${taskId}] File removed. Remaining files: ${updated.length}`);
      return updated;
    });
  }, [taskId]);

  // Toggle file active state específico de la tarea
  const toggleMemoryFile = useCallback((fileId: string) => {
    console.log(`🔄 [MEMORY-${taskId}] Toggling file:`, fileId);
    
    setMemoryFiles(prev => prev.map(file => 
      file.id === fileId 
        ? { ...file, isActive: !file.isActive }
        : file
    ));
  }, [taskId]);

  // Update file priority específico de la tarea
  const updateFilePriority = useCallback((fileId: string, priority: 'low' | 'medium' | 'high') => {
    console.log(`📝 [MEMORY-${taskId}] Updating file priority:`, fileId, priority);
    
    setMemoryFiles(prev => prev.map(file => 
      file.id === fileId 
        ? { ...file, priority }
        : file
    ));
  }, [taskId]);

  // Clear all memory específico de la tarea
  const clearAllMemory = useCallback(() => {
    console.log(`🧹 [MEMORY-${taskId}] Clearing all memory`);
    
    setMemoryFiles([]);
    localStorage.removeItem(storageKey);
  }, [taskId, storageKey]);

  // Get active memory context for API calls específico de la tarea
  const getActiveMemoryContext = useCallback((): IsolatedMemoryContext => {
    const activeFiles = memoryFiles.filter(file => file.isActive);
    
    console.log(`🔍 [MEMORY-${taskId}] Getting active context: ${activeFiles.length} active files`);
    
    // Sort by priority: high > medium > low
    const sortedFiles = activeFiles.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });

    const combinedContent = sortedFiles
      .map(file => `[${file.name}]\n${file.content}\n`)
      .join('\n---\n\n');

    const summary = `Contexto de memoria activo para tarea ${taskId}: ${activeFiles.length} documento(s) - ${activeFiles.map(f => f.name).join(', ')}`;

    return {
      activeFiles: sortedFiles,
      totalFiles: activeFiles.length,
      combinedContent,
      summary
    };
  }, [memoryFiles, taskId]);

  // Check if there's any active memory específico de la tarea
  const hasActiveMemory = memoryFiles.some(file => file.isActive);

  // Get memory statistics específico de la tarea
  const getMemoryStats = useCallback(() => {
    const active = memoryFiles.filter(f => f.isActive).length;
    const total = memoryFiles.length;
    const totalSize = memoryFiles.reduce((sum, file) => sum + file.metadata.size, 0);
    
    const stats = {
      activeFiles: active,
      totalFiles: total,
      totalSize,
      hasActiveMemory,
      taskId
    };
    
    console.log(`📊 [MEMORY-${taskId}] Memory stats:`, stats);
    return stats;
  }, [memoryFiles, hasActiveMemory, taskId]);

  // Check if a file exists in memory específico de la tarea
  const isFileInMemory = useCallback((fileName: string, fileType: 'research_report' | 'uploaded_file' | 'agent_file') => {
    const exists = memoryFiles.some(file => 
      file.name === fileName && 
      file.type === fileType
    );
    
    console.log(`🔍 [MEMORY-${taskId}] File exists check:`, fileName, fileType, exists);
    return exists;
  }, [memoryFiles, taskId]);

  // ========================================================================
  // CLEANUP AL DESMONTAR EL COMPONENTE
  // ========================================================================

  useEffect(() => {
    return () => {
      console.log(`🧹 [MEMORY-${taskId}] Memory manager cleanup`);
    };
  }, [taskId]);

  // ========================================================================
  // API PÚBLICA AISLADA
  // ========================================================================

  return {
    // Estado específico de la tarea
    memoryFiles,
    isLoading,
    taskId,
    
    // Funciones de gestión
    addMemoryFile,
    addResearchReportToMemory,
    removeMemoryFile,
    toggleMemoryFile,
    updateFilePriority,
    clearAllMemory,
    
    // Funciones de consulta
    getActiveMemoryContext,
    hasActiveMemory,
    getMemoryStats,
    isFileInMemory
  };
};