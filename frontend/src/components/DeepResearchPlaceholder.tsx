import React, { useState, useEffect } from 'react';
import { DeepResearchReport } from './DeepResearchReport';
import { useConsoleReportFormatter } from '../hooks/useConsoleReportFormatter';

// Datos de ejemplo para demostrar el formato académico
const PLACEHOLDER_REPORT = {
  query: "Inteligencia Artificial en el Sector Educativo: Impacto y Transformación Digital",
  sourcesAnalyzed: 25,
  imagesCollected: 12,
  timestamp: new Date().toISOString(),
  processingTime: 180,
  wordCount: 2847,
  
  executiveSummary: `La integración de la Inteligencia Artificial (IA) en el sector educativo representa una transformación paradigmática que está redefiniendo los métodos de enseñanza, aprendizaje y evaluación. 

Esta investigación comprehensiva analiza el impacto multifacético de la IA en la educación, identificando tendencias emergentes, desafíos operativos y oportunidades de innovación. Los hallazgos revelan que la IA está democratizando el acceso a la educación personalizada, optimizando procesos administrativos y creando experiencias de aprendizaje más inmersivas y adaptativas.

El análisis de 25 fuentes especializadas y 12 estudios de caso visuales demuestra que las instituciones educativas que adoptan tecnologías de IA experimentan mejoras significativas en la retención estudiantil (32% promedio), personalización del aprendizaje (78% de efectividad) y eficiencia operativa (45% reducción en tareas administrativas).

Sin embargo, la implementación exitosa requiere abordar desafíos críticos relacionados con la privacidad de datos, la equidad en el acceso tecnológico y la formación docente en competencias digitales avanzadas.`,

  keyFindings: [
    "La IA personalizada mejora los resultados de aprendizaje en un 67% promedio, adaptándose al ritmo y estilo de cada estudiante mediante algoritmos de machine learning que analizan patrones de comportamiento y rendimiento académico.",
    
    "Los sistemas de tutorización inteligente reducen en un 45% el tiempo necesario para completar cursos, proporcionando retroalimentación inmediata y rutas de aprendizaje optimizadas basadas en las fortalezas y debilidades individuales.",
    
    "La automatización de procesos administrativos mediante IA libera hasta 30 horas semanales del personal docente, permitiendo mayor enfoque en la interacción directa con estudiantes y el desarrollo de contenido pedagógico innovador.",
    
    "Las herramientas de análisis predictivo identifican estudiantes en riesgo de abandono con una precisión del 85%, permitiendo intervenciones tempranas que incrementan la tasa de retención en un 28%.",
    
    "La implementación de chatbots educativos inteligentes proporciona soporte 24/7 a estudiantes, resolviendo el 73% de consultas académicas y administrativas sin intervención humana.",
    
    "Los sistemas de evaluación automatizada utilizando procesamiento de lenguaje natural mejoran la consistencia en la calificación y reducen el sesgo evaluativo en un 52%.",
    
    "La realidad virtual y aumentada potenciada por IA crea experiencias de aprendizaje inmersivas que incrementan la retención de conocimientos en un 89% comparado con métodos tradicionales."
  ],

  recommendations: [
    "**Desarrollo de Marco Estratégico Integral:** Implementar un plan maestro de transformación digital que incluya evaluación de necesidades institucionales, selección de tecnologías apropiadas, cronograma de implementación y métricas de éxito específicas para cada fase del proceso.",
    
    "**Inversión en Capacitación Docente Especializada:** Establecer programas de formación continua en competencias digitales avanzadas, incluyendo certificaciones en herramientas de IA educativa, metodologías de aprendizaje híbrido y análisis de datos académicos.",
    
    "**Implementación de Sistemas de Privacidad y Seguridad Robustos:** Desarrollar protocolos de protección de datos estudiantiles que cumplan con regulaciones internacionales (GDPR, FERPA), incluyendo encriptación avanzada, auditorías de seguridad regulares y políticas de consentimiento informado.",
    
    "**Creación de Alianzas Estratégicas Público-Privadas:** Establecer colaboraciones entre instituciones educativas, empresas tecnológicas y organismos gubernamentales para desarrollar soluciones de IA contextualizada y culturalmente relevante.",
    
    "**Desarrollo de Métricas de Impacto Comprehensivas:** Implementar sistemas de monitoreo que evalúen tanto el rendimiento académico como el bienestar estudiantil, la satisfacción docente y la eficiencia operativa institucional.",
    
    "**Fomento de la Equidad Digital:** Establecer programas de acceso inclusivo que garanticen que todos los estudiantes, independientemente de su situación socioeconómica, tengan acceso a tecnologías de IA educativa y conectividad adecuada.",
    
    "**Investigación y Desarrollo Continuo:** Crear centros de innovación educativa dedicados a la investigación en IA, fomentando la colaboración entre académicos, desarrolladores y pedagogos para el desarrollo de soluciones emergentes."
  ],

  console_report: "" // Se llenará con el formato académico
};

interface DeepResearchPlaceholderProps {
  onGenerateReport?: () => void;
  className?: string;
}

export const DeepResearchPlaceholder: React.FC<DeepResearchPlaceholderProps> = ({
  onGenerateReport,
  className = ""
}) => {
  const [showPlaceholder, setShowPlaceholder] = useState(true);
  const [generatingReport, setGeneratingReport] = useState(false);
  const { formatDeepResearchReport, formatAcademicReport } = useConsoleReportFormatter();

  // Generar el reporte formatado al cargar el componente
  useEffect(() => {
    const generateFormattedReport = () => {
      // Usar el formateador de reportes académicos
      const academicReport = formatAcademicReport(
        PLACEHOLDER_REPORT.query,
        PLACEHOLDER_REPORT.executiveSummary,
        "La presente investigación adopta un enfoque metodológico mixto que combina análisis cuantitativo de datos académicos con evaluación cualitativa de casos de estudio. Se realizó una revisión sistemática de literatura científica, análisis de métricas de rendimiento educativo y entrevistas con expertos en tecnología educativa de 15 países.",
        "El análisis de 25 fuentes especializadas y 12 estudios de caso reveló patrones consistentes en la adopción de IA educativa. Los datos cuantitativos muestran mejoras significativas en personalización del aprendizaje (78% efectividad), retención estudiantil (32% incremento) y eficiencia operativa (45% reducción en tareas administrativas).",
        "Los resultados indican que la integración exitosa de IA en educación requiere un enfoque holístico que considere aspectos tecnológicos, pedagógicos y organizacionales. Las instituciones que implementan estrategias integrales experimentan resultados superiores en términos de adopción tecnológica y satisfacción estudiantil.",
        "La investigación concluye que la IA representa una oportunidad transformadora para la educación, pero su implementación exitosa requiere planificación estratégica, inversión en capacitación docente y marcos regulatorios apropiados. Las instituciones que abordan estos desafíos proactivamente están mejor posicionadas para aprovechar el potencial completo de estas tecnologías emergentes.",
        [
          "Johnson, M. et al. (2024). 'Artificial Intelligence in Educational Settings: A Comprehensive Analysis'. Journal of Educational Technology, 45(3), 234-267.",
          "UNESCO (2024). 'AI and Education: Guidance for Policy-makers'. UNESCO Publishing.",
          "García, L. & Smith, R. (2024). 'Machine Learning Applications in Student Assessment'. Educational Data Mining Review, 12(2), 45-78.",
          "European Commission (2024). 'Digital Education Action Plan 2024-2027'. EC Publications Office.",
          "Thompson, K. (2024). 'Privacy and Ethics in AI-Driven Educational Systems'. Technology and Society, 31(4), 123-145."
        ]
      );

      // También generar el reporte de investigación profunda
      const deepResearchReport = formatDeepResearchReport(
        PLACEHOLDER_REPORT.query,
        PLACEHOLDER_REPORT.executiveSummary,
        PLACEHOLDER_REPORT.keyFindings,
        PLACEHOLDER_REPORT.recommendations,
        [
          { title: "UNESCO AI Education Guidelines", url: "https://unesco.org/ai-education" },
          { title: "MIT Technology Review - AI in Education", url: "https://technologyreview.com/ai-education" },
          { title: "Stanford HAI Education Report", url: "https://hai.stanford.edu/education" }
        ],
        {
          sourcesAnalyzed: PLACEHOLDER_REPORT.sourcesAnalyzed,
          imagesCollected: PLACEHOLDER_REPORT.imagesCollected,
          processingTime: PLACEHOLDER_REPORT.processingTime,
          wordCount: PLACEHOLDER_REPORT.wordCount
        }
      );

      // Actualizar el reporte con el contenido formateado
      PLACEHOLDER_REPORT.console_report = deepResearchReport;
      
      return academicReport;
    };

    generateFormattedReport();
  }, [formatDeepResearchReport, formatAcademicReport]);

  const handleGenerateReport = async () => {
    setGeneratingReport(true);
    
    // Simular generación del reporte
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setGeneratingReport(false);
    setShowPlaceholder(false);
    
    if (onGenerateReport) {
      onGenerateReport();
    }
  };

  const handleDownload = () => {
    console.log('💾 Descargando reporte académico...');
    // La funcionalidad de descarga está en DeepResearchReport
  };

  const handleViewInConsole = () => {
    console.log('👁️ Mostrando reporte en consola...');
    
    // Mostrar el reporte completo en consola con formato académico
    formatDeepResearchReport(
      PLACEHOLDER_REPORT.query,
      PLACEHOLDER_REPORT.executiveSummary,
      PLACEHOLDER_REPORT.keyFindings,
      PLACEHOLDER_REPORT.recommendations,
      [
        { title: "UNESCO AI Education Guidelines", url: "https://unesco.org/ai-education" },
        { title: "MIT Technology Review - AI in Education", url: "https://technologyreview.com/ai-education" },
        { title: "Stanford HAI Education Report", url: "https://hai.stanford.edu/education" }
      ],
      {
        sourcesAnalyzed: PLACEHOLDER_REPORT.sourcesAnalyzed,
        imagesCollected: PLACEHOLDER_REPORT.imagesCollected,
        processingTime: PLACEHOLDER_REPORT.processingTime,
        wordCount: PLACEHOLDER_REPORT.wordCount
      }
    );
  };

  if (showPlaceholder) {
    return (
      <div className={`space-y-6 ${className}`}>
        {/* Placeholder para generar el reporte */}
        <div className="bg-gradient-to-r from-[#2a2a2b] to-[#323233] rounded-xl border border-[rgba(255,255,255,0.08)] p-8 text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          
          <h3 className="text-2xl font-bold text-[#DADADA] mb-2">
            Demostración de Formato Académico
          </h3>
          <p className="text-[#ACACAC] mb-6 max-w-2xl mx-auto">
            Haz clic en el botón para generar un reporte de investigación profunda de ejemplo que muestra el formato académico y profesional implementado.
          </p>
          
          <button
            onClick={handleGenerateReport}
            disabled={generatingReport}
            className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-medium transition-all disabled:opacity-50 shadow-lg hover:shadow-xl"
          >
            {generatingReport ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generando Reporte...
              </span>
            ) : (
              'Generar Reporte de Demostración'
            )}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Indicador de que es un placeholder */}
      <div className="bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/20 rounded-lg p-4 mb-6">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 bg-amber-500 rounded-full flex items-center justify-center">
            <span className="text-white text-xs font-bold">!</span>
          </div>
          <span className="text-amber-400 font-medium">Reporte de Demostración</span>
        </div>
        <p className="text-amber-300/80 text-sm mt-2">
          Este es un reporte placeholder que demuestra el formato académico y profesional implementado. 
          El contenido y métricas son ejemplos para mostrar las capacidades del sistema.
        </p>
      </div>

      {/* Componente principal del reporte */}
      <DeepResearchReport
        report={PLACEHOLDER_REPORT}
        onDownload={handleDownload}
        onViewInConsole={handleViewInConsole}
        className=""
        taskId="placeholder-demo"
      />

      {/* Botón para generar otro reporte */}
      <div className="text-center">
        <button
          onClick={() => setShowPlaceholder(true)}
          className="px-6 py-2 bg-[rgba(255,255,255,0.08)] hover:bg-[rgba(255,255,255,0.12)] text-[#DADADA] rounded-lg font-medium transition-all border border-[rgba(255,255,255,0.12)] hover:border-[rgba(255,255,255,0.20)]"
        >
          Generar Otro Reporte de Demostración
        </button>
      </div>
    </div>
  );
};

export default DeepResearchPlaceholder;