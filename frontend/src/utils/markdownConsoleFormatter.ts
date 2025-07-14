/**
 * Utilidades para formatear reportes en markdown para mostrar en consola
 * Basado en las especificaciones del usuario para informes profesionales
 */

export interface MarkdownReportData {
  title: string;
  subtitle?: string;
  sections: MarkdownSection[];
  metadata?: {
    author?: string;
    date?: string;
    version?: string;
    [key: string]: any;
  };
}

export interface MarkdownSection {
  title: string;
  content: string;
  subsections?: MarkdownSubsection[];
  list?: string[];
  codeBlocks?: CodeBlock[];
  tables?: TableData[];
  quotes?: string[];
}

export interface MarkdownSubsection {
  title: string;
  content: string;
  list?: string[];
}

export interface CodeBlock {
  language: string;
  code: string;
  title?: string;
}

export interface TableData {
  headers: string[];
  rows: string[][];
}

export class MarkdownConsoleFormatter {
  /**
   * Genera un reporte completo en markdown formateado para consola
   */
  static generateReport(data: MarkdownReportData): string {
    const sections: string[] = [];
    
    // Header principal
    sections.push(this.formatTitle(data.title));
    
    if (data.subtitle) {
      sections.push(this.formatSubtitle(data.subtitle));
    }
    
    // Metadata si está disponible
    if (data.metadata) {
      sections.push(this.formatMetadata(data.metadata));
    }
    
    // Secciones principales
    data.sections.forEach(section => {
      sections.push(this.formatSection(section));
    });
    
    return sections.join('\n\n');
  }

  /**
   * Formatea el título principal
   */
  private static formatTitle(title: string): string {
    return `# ${title}`;
  }

  /**
   * Formatea el subtítulo
   */
  private static formatSubtitle(subtitle: string): string {
    return `## ${subtitle}`;
  }

  /**
   * Formatea metadata del documento
   */
  private static formatMetadata(metadata: any): string {
    const lines: string[] = [];
    lines.push('---');
    
    if (metadata.author) lines.push(`**Autor:** ${metadata.author}`);
    if (metadata.date) lines.push(`**Fecha:** ${metadata.date}`);
    if (metadata.version) lines.push(`**Versión:** ${metadata.version}`);
    
    // Otros metadatos
    Object.entries(metadata).forEach(([key, value]) => {
      if (!['author', 'date', 'version'].includes(key)) {
        lines.push(`**${this.capitalizeFirst(key)}:** ${value}`);
      }
    });
    
    lines.push('---');
    return lines.join('\n');
  }

  /**
   * Formatea una sección completa
   */
  private static formatSection(section: MarkdownSection): string {
    const parts: string[] = [];
    
    // Título de la sección
    parts.push(`## ${section.title}`);
    
    // Contenido principal
    if (section.content) {
      parts.push(section.content);
    }
    
    // Subsecciones
    if (section.subsections && section.subsections.length > 0) {
      section.subsections.forEach(subsection => {
        parts.push(this.formatSubsection(subsection));
      });
    }
    
    // Listas
    if (section.list && section.list.length > 0) {
      parts.push(this.formatList(section.list));
    }
    
    // Bloques de código
    if (section.codeBlocks && section.codeBlocks.length > 0) {
      section.codeBlocks.forEach(codeBlock => {
        parts.push(this.formatCodeBlock(codeBlock));
      });
    }
    
    // Tablas
    if (section.tables && section.tables.length > 0) {
      section.tables.forEach(table => {
        parts.push(this.formatTable(table));
      });
    }
    
    // Citas
    if (section.quotes && section.quotes.length > 0) {
      section.quotes.forEach(quote => {
        parts.push(this.formatQuote(quote));
      });
    }
    
    return parts.join('\n\n');
  }

  /**
   * Formatea una subsección
   */
  private static formatSubsection(subsection: MarkdownSubsection): string {
    const parts: string[] = [];
    
    parts.push(`### ${subsection.title}`);
    
    if (subsection.content) {
      parts.push(subsection.content);
    }
    
    if (subsection.list && subsection.list.length > 0) {
      parts.push(this.formatList(subsection.list));
    }
    
    return parts.join('\n\n');
  }

  /**
   * Formatea una lista
   */
  private static formatList(items: string[]): string {
    return items.map(item => `• ${item}`).join('\n');
  }

  /**
   * Formatea un bloque de código
   */
  private static formatCodeBlock(codeBlock: CodeBlock): string {
    const parts: string[] = [];
    
    if (codeBlock.title) {
      parts.push(`**${codeBlock.title}**`);
    }
    
    parts.push(`\`\`\`${codeBlock.language}`);
    parts.push(codeBlock.code);
    parts.push('```');
    
    return parts.join('\n');
  }

  /**
   * Formatea una tabla
   */
  private static formatTable(table: TableData): string {
    const lines: string[] = [];
    
    // Headers
    lines.push('| ' + table.headers.join(' | ') + ' |');
    lines.push('|' + table.headers.map(() => '---').join('|') + '|');
    
    // Rows
    table.rows.forEach(row => {
      lines.push('| ' + row.join(' | ') + ' |');
    });
    
    return lines.join('\n');
  }

  /**
   * Formatea una cita
   */
  private static formatQuote(quote: string): string {
    return `> ${quote}`;
  }

  /**
   * Formatea un reporte de investigación profunda
   */
  static formatDeepResearchReport(
    query: string,
    executiveSummary: string,
    keyFindings: string[],
    recommendations: string[],
    sources: any[],
    metadata: any
  ): string {
    const reportData: MarkdownReportData = {
      title: 'Informe de Investigación Profunda',
      subtitle: 'Análisis Comprehensivo',
      metadata: {
        autor: 'Manus AI',
        fecha: new Date().toLocaleDateString('es-ES'),
        tema: query,
        fuentes: metadata.sourcesAnalyzed || 0,
        imágenes: metadata.imagesCollected || 0,
        ...metadata
      },
      sections: [
        {
          title: 'Introducción',
          content: `Este informe presenta un análisis profundo sobre: **${query}**\n\nLa investigación se realizó utilizando múltiples fuentes de información para proporcionar una perspectiva comprehensiva y actualizada del tema.`
        },
        {
          title: 'Resumen Ejecutivo',
          content: executiveSummary
        },
        {
          title: 'Hallazgos Clave',
          content: 'Los siguientes hallazgos representan los puntos más importantes identificados durante la investigación:',
          list: keyFindings
        },
        {
          title: 'Recomendaciones',
          content: 'Basándose en los hallazgos obtenidos, se presentan las siguientes recomendaciones:',
          list: recommendations
        },
        {
          title: 'Fuentes Consultadas',
          content: sources.length > 0 
            ? 'Las siguientes fuentes fueron consultadas durante la investigación:'
            : 'No se especificaron fuentes detalladas en este reporte.',
          list: sources.map((source, index) => 
            `**${source.title || `Fuente ${index + 1}`}** - ${source.url || 'URL no disponible'}`
          )
        }
      ]
    };
    
    return this.generateReport(reportData);
  }

  /**
   * Formatea un reporte personalizado con estilo académico
   */
  static formatAcademicReport(
    title: string,
    abstract: string,
    introduction: string,
    methodology: string,
    results: string,
    discussion: string,
    conclusions: string,
    references: string[]
  ): string {
    const reportData: MarkdownReportData = {
      title,
      metadata: {
        autor: 'Manus AI',
        fecha: new Date().toLocaleDateString('es-ES'),
        tipo: 'Informe Académico'
      },
      sections: [
        {
          title: 'Resumen',
          content: abstract
        },
        {
          title: 'Introducción',
          content: introduction
        },
        {
          title: 'Metodología',
          content: methodology
        },
        {
          title: 'Resultados',
          content: results
        },
        {
          title: 'Discusión',
          content: discussion
        },
        {
          title: 'Conclusiones',
          content: conclusions
        },
        {
          title: 'Referencias',
          content: 'Fuentes consultadas durante la investigación:',
          list: references
        }
      ]
    };
    
    return this.generateReport(reportData);
  }

  /**
   * Convierte texto plano en markdown con formato básico
   */
  static textToMarkdown(text: string): string {
    return text
      .replace(/\*\*(.*?)\*\*/g, '**$1**') // Bold
      .replace(/\*(.*?)\*/g, '*$1*') // Italic
      .replace(/`(.*?)`/g, '`$1`') // Code
      .replace(/^# (.*)/gm, '# $1') // H1
      .replace(/^## (.*)/gm, '## $1') // H2
      .replace(/^### (.*)/gm, '### $1') // H3
      .replace(/^- (.*)/gm, '• $1') // Lists
      .replace(/^> (.*)/gm, '> $1'); // Quotes
  }

  /**
   * Aplica el CSS personalizado al HTML generado
   */
  static applyCustomCSS(): string {
    return `
/* Estilos personalizados para informes Manus AI */
@page {
  size: A4;
  margin: 2.5cm;
  @top-center {
    content: "Informe Generado por Manus AI";
    font-family: 'Arial', sans-serif;
    font-size: 10pt;
    color: #555;
  }
  @bottom-center {
    content: counter(page);
    font-family: 'Arial', sans-serif;
    font-size: 9pt;
    color: #777;
  }
}

body {
  font-family: 'Georgia', serif;
  font-size: 12pt;
  line-height: 1.6;
  color: #333;
  background-color: #f9f9f9;
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

code {
  font-family: 'Courier New', monospace;
  background-color: #ecf0f1;
  padding: 2px 4px;
  border-radius: 3px;
}

pre {
  background-color: #2d2d2d;
  color: #f8f8f2;
  padding: 1em;
  border-radius: 5px;
  overflow-x: auto;
  margin-bottom: 1em;
}

blockquote {
  border-left: 4px solid #3498db;
  background-color: #ecf0f1;
  margin: 1em 0;
  padding: 1em 1.5em;
  font-style: italic;
  color: #555;
}

hr {
  border: none;
  border-top: 1px solid #ccc;
  margin: 2em 0;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1em;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

th {
  background-color: #f2f2f2;
  font-weight: bold;
}

a {
  color: #3498db;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
    `;
  }

  /**
   * Utilitarios privados
   */
  private static capitalizeFirst(str: string): string {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }
}

export default MarkdownConsoleFormatter;