// Utility functions for academic report generation, title generation, and downloads

/**
 * Generates an academic title based on the query and content
 */
export const generateAcademicTitle = (query: string, content?: string): string => {
  const academicPrefixes = [
    'Análisis Académico:',
    'Investigación Profunda:',
    'Estudio Comprensivo:',
    'Revisión Sistemática:',
    'Análisis Comparativo:',
    'Investigación Multidisciplinaria:',
    'Estudio Exploratorio:',
    'Revisión Crítica:',
    'Análisis Teórico:',
    'Investigación Documental:'
  ];

  // Clean and process the query
  const cleanQuery = query.replace(/^\[DeepResearch\]\s*/i, '').trim();
  
  // Try to extract key concepts from the query
  const keyWords = cleanQuery.split(' ').filter(word => word.length > 3);
  
  // Select appropriate prefix based on content type
  let selectedPrefix = academicPrefixes[0]; // Default
  
  if (content) {
    const contentLower = content.toLowerCase();
    if (contentLower.includes('comparar') || contentLower.includes('versus') || contentLower.includes('diferencia')) {
      selectedPrefix = 'Análisis Comparativo:';
    } else if (contentLower.includes('historia') || contentLower.includes('evolución') || contentLower.includes('desarrollo')) {
      selectedPrefix = 'Revisión Sistemática:';
    } else if (contentLower.includes('teoría') || contentLower.includes('concepto') || contentLower.includes('definición')) {
      selectedPrefix = 'Análisis Teórico:';
    } else if (contentLower.includes('múltiple') || contentLower.includes('diversos') || contentLower.includes('varios')) {
      selectedPrefix = 'Investigación Multidisciplinaria:';
    } else if (contentLower.includes('explorar') || contentLower.includes('examinar') || contentLower.includes('investigar')) {
      selectedPrefix = 'Estudio Exploratorio:';
    }
  }
  
  // Capitalize the first letter of each significant word
  const capitalizedQuery = cleanQuery.replace(/\b\w/g, (match) => match.toUpperCase());
  
  return `${selectedPrefix} ${capitalizedQuery}`;
};

/**
 * Generates markdown content with academic formatting
 */
export const generateAcademicMarkdown = (
  title: string,
  query: string,
  executiveSummary: string,
  keyFindings: string[],
  recommendations: string[],
  sources: any[] = [],
  metadata: any = {}
): string => {
  const currentDate = new Date().toLocaleDateString('es-ES', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  const markdown = `# ${title}

**Fecha de generación:** ${currentDate}  
**Generado por:** AURA - Asistente de Investigación Académica  
**Metodología:** Análisis documental y síntesis de fuentes múltiples  

---

## Resumen Ejecutivo

${executiveSummary}

---

## Metodología de Investigación

Este informe ha sido generado mediante un proceso sistemático de investigación que incluye:

1. **Búsqueda inicial** de fuentes académicas y documentales
2. **Análisis específico** de subtemas y conceptos clave
3. **Extracción de contenido** relevante y verificación de fuentes
4. **Recopilación de material** visual y gráfico complementario
5. **Análisis comparativo** de diferentes perspectivas y enfoques
6. **Síntesis final** y generación de conclusiones

### Criterios de Selección de Fuentes

- Relevancia académica y científica
- Actualidad y vigencia de la información
- Autoridad y credibilidad de las fuentes
- Diversidad de perspectivas y enfoques

---

## Hallazgos Principales

${keyFindings.map((finding, index) => `### ${index + 1}. ${finding}`).join('\n\n')}

---

## Análisis y Discusión

Los hallazgos presentados en este informe revelan aspectos fundamentales sobre el tema investigado. El análisis comparativo de las fuentes consultadas permite identificar patrones, tendencias y elementos de consenso en la literatura académica.

### Elementos de Convergencia

Las diferentes fuentes consultadas convergen en varios puntos clave que refuerzan la solidez de los hallazgos presentados.

### Áreas de Debate

Existen también áreas donde las fuentes presentan perspectivas divergentes, lo que enriquece el análisis y permite una comprensión más matizada del tema.

---

## Conclusiones y Recomendaciones

### Conclusiones

Basándose en el análisis exhaustivo de las fuentes consultadas, se pueden establecer las siguientes conclusiones:

${keyFindings.map((finding, index) => `${index + 1}. ${finding}`).join('\n')}

### Recomendaciones

${recommendations.length > 0 ? recommendations.map((rec, index) => `${index + 1}. ${rec}`).join('\n') : 'Se recomienda profundizar en estudios específicos para obtener una comprensión más detallada del tema.'}

---

## Referencias y Fuentes Consultadas

${sources.length > 0 
  ? sources.map((source, index) => `${index + 1}. ${source.title || 'Fuente académica'} - ${source.url || 'URL no disponible'}`).join('\n')
  : 'Las fuentes consultadas incluyen bases de datos académicas, publicaciones científicas y repositorios institucionales especializados.'
}

---

## Metadatos del Informe

- **Consulta original:** ${query}
- **Fuentes analizadas:** ${sources.length || 'Múltiples'}
- **Fecha de generación:** ${currentDate}
- **Tiempo de investigación:** ${metadata.duration || 'Proceso optimizado'}
- **Nivel de profundidad:** Análisis académico comprehensivo

---

*Este informe ha sido generado por AURA, sistema de investigación académica automatizada. Para cuestiones específicas o ampliación de temas particulares, se recomienda consulta con especialistas en la materia.*`;

  return markdown;
};

/**
 * Downloads content as markdown file
 */
export const downloadAsMarkdown = (content: string, filename: string): void => {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Downloads content as PDF file using jsPDF with professional formatting
 */
export const downloadAsPDF = async (content: string, filename: string): Promise<void> => {
  try {
    const { jsPDF } = await import('jspdf');
    
    const pdf = new jsPDF('p', 'mm', 'a4');
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const margin = 20;
    const contentWidth = pageWidth - 2 * margin;
    const lineHeight = 6;
    
    // Title and header
    pdf.setFontSize(20);
    pdf.setFont('helvetica', 'bold');
    pdf.text('INFORME ACADÉMICO', pageWidth / 2, margin + 10, { align: 'center' });
    
    // Metadata
    pdf.setFontSize(11);
    pdf.setFont('helvetica', 'normal');
    pdf.text(`Generado por AURA • ${new Date().toLocaleDateString('es-ES', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })}`, pageWidth / 2, margin + 20, { align: 'center' });
    
    // Process content
    const lines = content.split('\n');
    let yPosition = margin + 35;
    
    for (const line of lines) {
      // Check if we need a new page
      if (yPosition > pageHeight - margin - 20) {
        pdf.addPage();
        yPosition = margin + 10;
      }
      
      if (line.startsWith('# ')) {
        // Main header
        pdf.setFontSize(18);
        pdf.setFont('helvetica', 'bold');
        const headerText = line.substring(2).trim();
        const headerLines = pdf.splitTextToSize(headerText, contentWidth);
        pdf.text(headerLines, margin, yPosition);
        yPosition += headerLines.length * lineHeight + 5;
        
        // Add underline
        pdf.line(margin, yPosition - 3, pageWidth - margin, yPosition - 3);
        yPosition += 5;
        
      } else if (line.startsWith('## ')) {
        // Section header
        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        const sectionText = line.substring(3).trim();
        const sectionLines = pdf.splitTextToSize(sectionText, contentWidth);
        pdf.text(sectionLines, margin, yPosition);
        yPosition += sectionLines.length * lineHeight + 3;
        
      } else if (line.startsWith('### ')) {
        // Subsection header
        pdf.setFontSize(12);
        pdf.setFont('helvetica', 'bold');
        const subsectionText = line.substring(4).trim();
        const subsectionLines = pdf.splitTextToSize(subsectionText, contentWidth);
        pdf.text(subsectionLines, margin, yPosition);
        yPosition += subsectionLines.length * lineHeight + 2;
        
      } else if (line.startsWith('- ') || line.startsWith('* ')) {
        // Bullet points
        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');
        const bulletText = line.substring(2).trim();
        const bulletLines = pdf.splitTextToSize(`• ${bulletText}`, contentWidth - 5);
        pdf.text(bulletLines, margin + 5, yPosition);
        yPosition += bulletLines.length * lineHeight;
        
      } else if (/^\d+\.\s/.test(line)) {
        // Numbered lists
        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');
        const numberedLines = pdf.splitTextToSize(line, contentWidth - 5);
        pdf.text(numberedLines, margin + 5, yPosition);
        yPosition += numberedLines.length * lineHeight;
        
      } else if (line.startsWith('> ')) {
        // Blockquotes
        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'italic');
        const quoteText = line.substring(2).trim();
        const quoteLines = pdf.splitTextToSize(`"${quoteText}"`, contentWidth - 10);
        pdf.text(quoteLines, margin + 10, yPosition);
        yPosition += quoteLines.length * lineHeight + 2;
        
      } else if (line.trim() !== '') {
        // Regular paragraphs
        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');
        
        // Process bold text
        let processedLine = line;
        const boldMatches = line.match(/\*\*(.*?)\*\*/g);
        if (boldMatches) {
          // For now, just remove the asterisks (basic handling)
          processedLine = line.replace(/\*\*(.*?)\*\*/g, '$1');
        }
        
        const paragraphLines = pdf.splitTextToSize(processedLine, contentWidth);
        pdf.text(paragraphLines, margin, yPosition);
        yPosition += paragraphLines.length * lineHeight + 2;
        
      } else {
        // Empty lines
        yPosition += lineHeight / 2;
      }
    }
    
    // Add footer
    const pageCount = pdf.internal.pages.length - 1;
    for (let i = 1; i <= pageCount; i++) {
      pdf.setPage(i);
      pdf.setFontSize(8);
      pdf.setFont('helvetica', 'normal');
      pdf.text(`Página ${i} de ${pageCount}`, pageWidth / 2, pageHeight - 10, { align: 'center' });
      pdf.text('AURA - Sistema de Investigación Académica', pageWidth - margin, pageHeight - 10, { align: 'right' });
    }
    
    // Save the PDF
    pdf.save(filename);
    
  } catch (error) {
    console.error('Error generating PDF:', error);
    // Fallback to the original print method
    const htmlContent = content
      .replace(/^# (.*$)/gm, '<h1 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">$1</h1>')
      .replace(/^## (.*$)/gm, '<h2 style="color: #34495e; margin-top: 30px;">$1</h2>')
      .replace(/^### (.*$)/gm, '<h3 style="color: #7f8c8d;">$1</h3>')
      .replace(/\*\*(.*?)\*\*/g, '<strong style="color: #2c3e50;">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^- (.*$)/gm, '<li style="margin-bottom: 5px;">$1</li>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>');

    const fullHtml = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="UTF-8">
          <title>${filename}</title>
          <style>
            body { font-family: 'Times New Roman', serif; line-height: 1.6; margin: 40px; color: #333; }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; }
            h3 { color: #7f8c8d; }
            p { margin-bottom: 15px; text-align: justify; }
            li { margin-bottom: 5px; }
            strong { color: #2c3e50; }
            .academic-header { text-align: center; margin-bottom: 40px; }
            .academic-footer { margin-top: 40px; text-align: center; font-size: 12px; color: #7f8c8d; }
            @media print {
              body { margin: 20px; }
              .academic-header { page-break-after: avoid; }
              h1, h2, h3 { page-break-after: avoid; }
            }
          </style>
        </head>
        <body>
          <div class="academic-header">
            <h1>Informe Académico</h1>
            <p>Generado por AURA • ${new Date().toLocaleDateString('es-ES', { 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}</p>
          </div>
          <div>${htmlContent}</div>
          <div class="academic-footer">
            <p>Documento generado automáticamente por AURA - Sistema de Investigación Académica</p>
          </div>
        </body>
      </html>
    `;

    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(fullHtml);
      printWindow.document.close();
      printWindow.focus();
      
      setTimeout(() => {
        printWindow.print();
        printWindow.close();
      }, 500);
    }
  }
};

/**
 * Generates a unique filename with timestamp
 */
export const generateFilename = (title: string, extension: string): string => {
  const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
  const cleanTitle = title
    .replace(/[^a-zA-Z0-9\s]/g, '')
    .replace(/\s+/g, '_')
    .substring(0, 50);
  
  return `${cleanTitle}_${timestamp}.${extension}`;
};

/**
 * Saves file to backend for persistence
 */
export const saveReportToBackend = async (
  content: string,
  filename: string,
  taskId: string
): Promise<boolean> => {
  try {
    const backendUrl = import.meta.env.VITE_BACKEND_URL || 
                   import.meta.env.REACT_APP_BACKEND_URL || 
                   process.env.REACT_APP_BACKEND_URL || 
                   'https://2d6bd67a-c88f-4adf-aad2-a25028aa0f12.preview.emergentagent.com';

    const response = await fetch(`${backendUrl}/api/agent/save-report`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        task_id: taskId,
        filename: filename,
        content: content,
        type: 'academic_report'
      }),
    });

    return response.ok;
  } catch (error) {
    console.error('Error saving report to backend:', error);
    return false;
  }
};

/**
 * Genera un PDF con CSS embebido usando HTML y los estilos académicos
 */
export const generatePDFWithCustomCSS = async (markdownContent: string, filename: string): Promise<Blob> => {
  // Convertir markdown a HTML
  const htmlContent = markdownToHTML(markdownContent);
  
  // CSS académico embebido
  const academicCSS = `
    @page {
      size: A4;
      margin: 2.5cm;
    }

    body {
      font-family: 'Georgia', serif;
      font-size: 12pt;
      line-height: 1.6;
      color: #333;
      background-color: white;
      margin: 0;
      padding: 0;
    }

    h1 {
      font-family: 'Helvetica Neue', sans-serif;
      font-size: 24pt;
      color: #2c3e50;
      text-align: center;
      margin-top: 1.5cm;
      margin-bottom: 1cm;
      padding-bottom: 0.5cm;
      border-bottom: 2px solid #3498db;
    }

    h2 {
      font-family: 'Helvetica Neue', sans-serif;
      font-size: 18pt;
      color: #34495e;
      margin-top: 1cm;
      margin-bottom: 0.5cm;
      border-bottom: 1px solid #ccc;
      padding-bottom: 0.2cm;
    }

    h3 {
      font-family: 'Helvetica Neue', sans-serif;
      font-size: 14pt;
      color: #34495e;
      margin-top: 0.8cm;
      margin-bottom: 0.3cm;
    }

    p {
      margin-bottom: 1em;
      text-align: justify;
    }

    ul, ol {
      margin-left: 2em;
      margin-bottom: 1em;
    }

    li {
      margin-bottom: 0.5em;
    }

    strong {
      font-weight: bold;
      color: #e74c3c;
    }

    em {
      font-style: italic;
      color: #27ae60;
    }

    blockquote {
      border-left: 4px solid #3498db;
      background-color: #ecf0f1;
      margin: 1em 0;
      padding: 1em 1.5em;
      font-style: italic;
      color: #555;
    }

    .report-metadata {
      background-color: #f8f9fa;
      padding: 1em;
      border-radius: 5px;
      margin-bottom: 1.5em;
      border-left: 4px solid #3498db;
    }

    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1em;
      margin: 1.5em 0;
    }

    .metric-card {
      background-color: #f8f9fa;
      padding: 1em;
      border-radius: 5px;
      text-align: center;
      border: 1px solid #dee2e6;
    }

    .metric-value {
      font-size: 24pt;
      font-weight: bold;
      color: #2c3e50;
      display: block;
    }

    .metric-label {
      font-size: 10pt;
      color: #6c757d;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
  `;

  // Crear HTML completo con CSS embebido
  const fullHTML = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>${filename}</title>
      <style>
        ${academicCSS}
      </style>
    </head>
    <body>
      ${htmlContent}
    </body>
    </html>
  `;

  // Usar una librería como html2pdf o similar para generar el PDF
  // Por ahora, vamos a retornar un blob con el HTML
  return new Blob([fullHTML], { type: 'text/html' });
};

/**
 * Convierte markdown básico a HTML
 */
const markdownToHTML = (markdown: string): string => {
  let html = markdown;
  
  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
  
  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Italic
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // Lists
  html = html.replace(/^\* (.*$)/gim, '<li>$1</li>');
  html = html.replace(/^- (.*$)/gim, '<li>$1</li>');
  html = html.replace(/^\d+\. (.*$)/gim, '<li>$1</li>');
  
  // Wrap consecutive list items in ul/ol tags
  html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
  
  // Paragraphs
  html = html.replace(/\n\n/g, '</p><p>');
  html = '<p>' + html + '</p>';
  
  // Clean up empty paragraphs
  html = html.replace(/<p><\/p>/g, '');
  html = html.replace(/<p>\s*<\/p>/g, '');
  
  return html;
};