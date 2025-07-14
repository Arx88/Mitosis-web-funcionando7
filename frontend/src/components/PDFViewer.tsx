import React, { useState, useEffect } from 'react';
import { X, Download, Maximize2, Minimize2, FileText, Calendar } from 'lucide-react';

interface PDFViewerProps {
  isOpen: boolean;
  onClose: () => void;
  content: string;
  title: string;
  onDownloadPDF?: () => void;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({
  isOpen,
  onClose,
  content,
  title,
  onDownloadPDF
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);

  // CSS personalizado del usuario - optimizado para una sola página
  const customCSS = `
    @page {
      size: A4;
      margin: 2cm;
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
      font-size: 11pt;
      line-height: 1.4;
      color: #333;
      background-color: #f9f9f9;
      margin: 0;
      padding: 0;
      max-width: 100%;
      overflow-x: hidden;
    }

    .page-container {
      max-width: 100%;
      min-height: 100vh;
      padding: 1cm;
      box-sizing: border-box;
    }

    h1 {
      font-family: 'Helvetica Neue', sans-serif;
      font-size: 20pt;
      color: #2c3e50;
      text-align: center;
      margin-top: 0.5cm;
      margin-bottom: 0.8cm;
      padding-bottom: 0.3cm;
      border-bottom: 2px solid #3498db;
      page-break-after: avoid;
    }

    h2 {
      font-family: 'Helvetica Neue', sans-serif;
      font-size: 16pt;
      color: #34495e;
      margin-top: 0.8cm;
      margin-bottom: 0.4cm;
      border-bottom: 1px solid #ccc;
      padding-bottom: 0.2cm;
      page-break-after: avoid;
    }

    h3 {
      font-family: 'Helvetica Neue', sans-serif;
      font-size: 13pt;
      color: #34495e;
      margin-top: 0.6cm;
      margin-bottom: 0.3cm;
      page-break-after: avoid;
    }

    p {
      margin-bottom: 0.8em;
      text-align: justify;
      page-break-inside: avoid;
    }

    ul,
    ol {
      margin-left: 1.5em;
      margin-bottom: 0.8em;
      page-break-inside: avoid;
    }

    li {
      margin-bottom: 0.3em;
      page-break-inside: avoid;
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
      padding: 0.8em;
      border-radius: 5px;
      overflow-x: auto;
      margin-bottom: 0.8em;
      page-break-inside: avoid;
    }

    blockquote {
      border-left: 4px solid #3498db;
      background-color: #ecf0f1;
      margin: 0.8em 0;
      padding: 0.8em 1.2em;
      font-style: italic;
      color: #555;
      page-break-inside: avoid;
    }

    hr {
      border: none;
      border-top: 1px solid #ccc;
      margin: 1.5em 0;
      page-break-after: avoid;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 0.8em;
      page-break-inside: avoid;
    }

    th,
    td {
      border: 1px solid #ddd;
      padding: 6px;
      text-align: left;
      font-size: 10pt;
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

    /* Prevent page breaks */
    .no-break {
      page-break-inside: avoid;
    }

    /* Ensure content fits in one page */
    .single-page {
      max-height: 24cm;
      overflow: hidden;
    }
  `;

  // Función para convertir markdown a HTML con el CSS personalizado
  const convertMarkdownToHTML = (markdown: string) => {
    // Simple markdown parsing (puedes usar una librería como marked.js si necesitas más funcionalidades)
    let html = markdown
      // Headers
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^#### (.*$)/gim, '<h4>$1</h4>')
      // Bold
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Italic
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Code blocks
      .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      // Inline code
      .replace(/`(.*?)`/g, '<code>$1</code>')
      // Lists
      .replace(/^\* (.*$)/gim, '<li>$1</li>')
      .replace(/^- (.*$)/gim, '<li>$1</li>')
      // Links
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
      // Line breaks
      .replace(/\n/g, '<br>');

    // Wrap lists
    html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');

    return html;
  };

  const htmlContent = convertMarkdownToHTML(content);

  const generateStyledHTML = () => {
    return `
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <style>
        ${customCSS}
    </style>
</head>
<body>
    <div class="page-container single-page">
        <h1>${title}</h1>
        <p><strong>Fecha de generación:</strong> ${new Date().toLocaleDateString()}</p>
        <hr>
        <div class="no-break">
            ${htmlContent}
        </div>
        <hr>
        <p><em>Informe generado automáticamente por Manus AI</em></p>
    </div>
</body>
</html>
    `;
  };

  const handlePrint = () => {
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(generateStyledHTML());
      printWindow.document.close();
      printWindow.focus();
      setTimeout(() => {
        printWindow.print();
        printWindow.close();
      }, 250);
    }
  };

  const handleDownloadHTML = () => {
    const htmlContent = generateStyledHTML();
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/[^a-zA-Z0-9]/g, '_')}_styled.html`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  if (!isOpen) return null;

  const containerClasses = isFullscreen 
    ? 'fixed inset-0 z-50 bg-[#1E1E1F] flex flex-col'
    : 'fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center';

  const modalClasses = isFullscreen
    ? 'w-full h-full flex flex-col'
    : 'bg-[#1E1E1F] rounded-xl border border-[rgba(255,255,255,0.08)] w-full max-w-5xl max-h-[90vh] flex flex-col overflow-hidden';

  return (
    <div className={containerClasses}>
      <div className={modalClasses}>
        {/* Header */}
        <div className="bg-gradient-to-r from-[#2a2a2b] to-[#1e1e1f] p-4 border-b border-[rgba(255,255,255,0.08)] flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-lg">
                <FileText className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-[#DADADA] mb-1">📄 VISTA PREVIA DE INFORME</h2>
                <p className="text-sm text-[#ACACAC]">{title}</p>
                <div className="flex items-center gap-2 mt-1">
                  <Calendar className="w-3 h-3 text-[#7f7f7f]" />
                  <span className="text-xs text-[#7f7f7f]">
                    {new Date().toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={handlePrint}
                className="flex items-center gap-2 px-3 py-1.5 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-lg text-sm font-medium transition-colors"
              >
                <Download className="w-4 h-4" />
                Imprimir
              </button>
              <button
                onClick={handleDownloadHTML}
                className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg text-sm font-medium transition-colors"
              >
                <Download className="w-4 h-4" />
                HTML
              </button>
              {onDownloadPDF && (
                <button
                  onClick={onDownloadPDF}
                  className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-lg text-sm font-medium transition-all duration-200"
                >
                  <Download className="w-4 h-4" />
                  PDF
                </button>
              )}
              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="flex items-center gap-2 px-3 py-1.5 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 rounded-lg text-sm font-medium transition-colors"
              >
                {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                {isFullscreen ? 'Ventana' : 'Pantalla completa'}
              </button>
              <button
                onClick={onClose}
                className="flex items-center gap-2 px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg text-sm font-medium transition-colors"
              >
                <X className="w-4 h-4" />
                Cerrar
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          <iframe
            srcDoc={generateStyledHTML()}
            className="w-full h-full border-0"
            title="Vista previa del informe"
          />
        </div>
      </div>
    </div>
  );
};