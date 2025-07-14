import { useState, useEffect, useCallback } from 'react';

export interface MemoryFile {
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

interface MemoryContext {
  activeFiles: MemoryFile[];
  totalFiles: number;
  combinedContent: string;
  summary: string;
}

export const useMemoryManager = () => {
  const [memoryFiles, setMemoryFiles] = useState<MemoryFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Load memory files from localStorage on mount
  useEffect(() => {
    const savedMemory = localStorage.getItem('mitosis_memory_files');
    if (savedMemory) {
      try {
        const parsed = JSON.parse(savedMemory);
        setMemoryFiles(parsed.map((file: any) => ({
          ...file,
          metadata: {
            ...file.metadata,
            createdAt: new Date(file.metadata.createdAt)
          }
        })));
      } catch (error) {
        console.error('Error loading memory files:', error);
      }
    }
  }, []);

  // Save memory files to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('mitosis_memory_files', JSON.stringify(memoryFiles));
  }, [memoryFiles]);

  // Add a file to memory (with duplicate check)
  const addMemoryFile = useCallback((file: Omit<MemoryFile, 'id' | 'isActive' | 'priority'>) => {
    // Check for duplicates based on name and type
    const isDuplicate = memoryFiles.some(existingFile => 
      existingFile.name === file.name && 
      existingFile.type === file.type &&
      existingFile.metadata.source === file.metadata.source
    );

    if (isDuplicate) {
      console.warn(`File "${file.name}" already exists in memory`);
      return null; // Return null to indicate duplicate
    }

    const newFile: MemoryFile = {
      ...file,
      id: `memory_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      isActive: true,
      priority: 'medium'
    };

    setMemoryFiles(prev => [...prev, newFile]);
    return newFile.id;
  }, [memoryFiles]);

  // Add research report to memory (with duplicate check)
  const addResearchReportToMemory = useCallback((report: {
    query: string;
    executiveSummary: string;
    keyFindings: string[];
    recommendations: string[];
    sourcesAnalyzed: number;
    wordCount?: number;
  }) => {
    const reportName = `Investigación: ${report.query}`;
    
    // Check for duplicates based on name and type
    const isDuplicate = memoryFiles.some(existingFile => 
      existingFile.name === reportName && 
      existingFile.type === 'research_report'
    );

    if (isDuplicate) {
      console.warn(`Research report "${reportName}" already exists in memory`);
      return null; // Return null to indicate duplicate
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
        tags: ['investigación', 'informe', 'análisis']
      }
    });
  }, [addMemoryFile, memoryFiles]);

  // Remove a file from memory
  const removeMemoryFile = useCallback((fileId: string) => {
    setMemoryFiles(prev => prev.filter(file => file.id !== fileId));
  }, []);

  // Toggle file active state
  const toggleMemoryFile = useCallback((fileId: string) => {
    setMemoryFiles(prev => prev.map(file => 
      file.id === fileId 
        ? { ...file, isActive: !file.isActive }
        : file
    ));
  }, []);

  // Update file priority
  const updateFilePriority = useCallback((fileId: string, priority: 'low' | 'medium' | 'high') => {
    setMemoryFiles(prev => prev.map(file => 
      file.id === fileId 
        ? { ...file, priority }
        : file
    ));
  }, []);

  // Clear all memory
  const clearAllMemory = useCallback(() => {
    setMemoryFiles([]);
  }, []);

  // Get active memory context for API calls
  const getActiveMemoryContext = useCallback((): MemoryContext => {
    const activeFiles = memoryFiles.filter(file => file.isActive);
    
    // Sort by priority: high > medium > low
    const sortedFiles = activeFiles.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });

    const combinedContent = sortedFiles
      .map(file => `[${file.name}]\n${file.content}\n`)
      .join('\n---\n\n');

    const summary = `Contexto de memoria activo: ${activeFiles.length} documento(s) - ${activeFiles.map(f => f.name).join(', ')}`;

    return {
      activeFiles: sortedFiles,
      totalFiles: activeFiles.length,
      combinedContent,
      summary
    };
  }, [memoryFiles]);

  // Check if there's any active memory
  const hasActiveMemory = memoryFiles.some(file => file.isActive);

  // Get memory statistics
  const getMemoryStats = useCallback(() => {
    const active = memoryFiles.filter(f => f.isActive).length;
    const total = memoryFiles.length;
    const totalSize = memoryFiles.reduce((sum, file) => sum + file.metadata.size, 0);
    
    return {
      activeFiles: active,
      totalFiles: total,
      totalSize,
      hasActiveMemory
    };
  }, [memoryFiles, hasActiveMemory]);

  // Check if a file exists in memory
  const isFileInMemory = useCallback((fileName: string, fileType: 'research_report' | 'uploaded_file' | 'agent_file') => {
    return memoryFiles.some(file => 
      file.name === fileName && 
      file.type === fileType
    );
  }, [memoryFiles]);

  return {
    memoryFiles,
    isLoading,
    addMemoryFile,
    addResearchReportToMemory,
    removeMemoryFile,
    toggleMemoryFile,
    updateFilePriority,
    clearAllMemory,
    getActiveMemoryContext,
    hasActiveMemory,
    getMemoryStats,
    isFileInMemory
  };
};

export default useMemoryManager;