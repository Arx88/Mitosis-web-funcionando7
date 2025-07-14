import { useCallback } from 'react';
import { MarkdownConsoleFormatter } from '../utils/markdownConsoleFormatter';

/**
 * Hook personalizado para formatear y mostrar reportes en consola
 */
export const useConsoleReportFormatter = () => {
  /**
   * Formatea y muestra un reporte de investigación profunda en consola
   */
  const formatDeepResearchReport = useCallback((
    query: string,
    executiveSummary: string,
    keyFindings: string[],
    recommendations: string[],
    sources: any[] = [],
    metadata: any = {}
  ) => {
    const formattedReport = MarkdownConsoleFormatter.formatDeepResearchReport(
      query,
      executiveSummary,
      keyFindings,
      recommendations,
      sources,
      metadata
    );
    
    console.log('📄 INFORME DE INVESTIGACIÓN PROFUNDA');
    console.log('═'.repeat(50));
    console.log(formattedReport);
    console.log('═'.repeat(50));
    
    return formattedReport;
  }, []);

  /**
   * Formatea y muestra un reporte académico en consola
   */
  const formatAcademicReport = useCallback((
    title: string,
    abstract: string,
    introduction: string,
    methodology: string,
    results: string,
    discussion: string,
    conclusions: string,
    references: string[]
  ) => {
    const formattedReport = MarkdownConsoleFormatter.formatAcademicReport(
      title,
      abstract,
      introduction,
      methodology,
      results,
      discussion,
      conclusions,
      references
    );
    
    console.log('📚 INFORME ACADÉMICO');
    console.log('═'.repeat(50));
    console.log(formattedReport);
    console.log('═'.repeat(50));
    
    return formattedReport;
  }, []);

  /**
   * Formatea y muestra texto plano como markdown en consola
   */
  const formatTextToMarkdown = useCallback((text: string, title?: string) => {
    const formattedText = MarkdownConsoleFormatter.textToMarkdown(text);
    
    console.log(title ? `📝 ${title.toUpperCase()}` : '📝 DOCUMENTO MARKDOWN');
    console.log('─'.repeat(50));
    console.log(formattedText);
    console.log('─'.repeat(50));
    
    return formattedText;
  }, []);

  /**
   * Muestra el CSS personalizado en consola
   */
  const showCustomCSS = useCallback(() => {
    const css = MarkdownConsoleFormatter.applyCustomCSS();
    
    console.log('🎨 ESTILOS CSS PERSONALIZADOS');
    console.log('═'.repeat(50));
    console.log(css);
    console.log('═'.repeat(50));
    
    return css;
  }, []);

  /**
   * Formatea datos estructurados para mostrar en consola
   */
  const formatStructuredData = useCallback((data: any, title: string = 'DATOS ESTRUCTURADOS') => {
    console.log(`📊 ${title.toUpperCase()}`);
    console.log('═'.repeat(50));
    
    if (typeof data === 'object') {
      console.log(JSON.stringify(data, null, 2));
    } else {
      console.log(data);
    }
    
    console.log('═'.repeat(50));
    
    return data;
  }, []);

  /**
   * Crea un reporte de progreso para mostrar en consola
   */
  const formatProgressReport = useCallback((
    steps: Array<{
      title: string;
      description: string;
      completed: boolean;
      progress?: number;
    }>,
    overallProgress: number = 0,
    currentStep: string = ''
  ) => {
    console.log('⚡ PROGRESO DE INVESTIGACIÓN');
    console.log('═'.repeat(50));
    console.log(`📈 Progreso general: ${overallProgress}%`);
    console.log(`🎯 Paso actual: ${currentStep}`);
    console.log('');
    console.log('📋 Pasos completados:');
    
    steps.forEach((step, index) => {
      const status = step.completed ? '✅' : '⏳';
      const progress = step.progress ? ` (${step.progress}%)` : '';
      console.log(`${status} ${index + 1}. ${step.title}${progress}`);
      console.log(`   ${step.description}`);
    });
    
    console.log('═'.repeat(50));
    
    return { steps, overallProgress, currentStep };
  }, []);

  /**
   * Formatea métricas de investigación
   */
  const formatResearchMetrics = useCallback((metrics: {
    sourcesAnalyzed: number;
    imagesCollected: number;
    processingTime?: number;
    wordCount?: number;
    [key: string]: any;
  }) => {
    console.log('📊 MÉTRICAS DE INVESTIGACIÓN');
    console.log('═'.repeat(50));
    console.log(`🔍 Fuentes analizadas: ${metrics.sourcesAnalyzed}`);
    console.log(`🖼️ Imágenes recopiladas: ${metrics.imagesCollected}`);
    
    if (metrics.processingTime) {
      const minutes = Math.floor(metrics.processingTime / 60);
      const seconds = metrics.processingTime % 60;
      console.log(`⏱️ Tiempo de procesamiento: ${minutes}m ${seconds}s`);
    }
    
    if (metrics.wordCount) {
      console.log(`📝 Palabras generadas: ${metrics.wordCount.toLocaleString()}`);
    }
    
    // Otras métricas adicionales
    Object.entries(metrics).forEach(([key, value]) => {
      if (!['sourcesAnalyzed', 'imagesCollected', 'processingTime', 'wordCount'].includes(key)) {
        console.log(`📋 ${key}: ${value}`);
      }
    });
    
    console.log('═'.repeat(50));
    
    return metrics;
  }, []);

  return {
    formatDeepResearchReport,
    formatAcademicReport,
    formatTextToMarkdown,
    showCustomCSS,
    formatStructuredData,
    formatProgressReport,
    formatResearchMetrics
  };
};

export default useConsoleReportFormatter;