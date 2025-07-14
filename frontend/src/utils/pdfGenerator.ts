import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

export interface MarkdownToPDFOptions {
  title: string;
  content: string;
  filename?: string;
  customCSS?: string;
}

export const generatePDFWithCustomCSS = async (options: MarkdownToPDFOptions): Promise<void> => {
  const { title, content, filename, customCSS } = options;
  
  // CSS personalizado proporcionado por el usuario
  const defaultCSS = `
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

    ul,
    ol {
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

    th,
    td {
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

  // Función para convertir markdown a HTML
  const convertMarkdownToHTML = (markdown: string): string => {
    return markdown
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
      // Blockquotes
      .replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>')
      // Horizontal rules
      .replace(/^---$/gim, '<hr>')
      // Lists (bullet points)
      .replace(/^\* (.*$)/gim, '<li>$1</li>')
      .replace(/^- (.*$)/gim, '<li>$1</li>')
      // Numbered lists
      .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
      // Links
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
      // Line breaks
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>');
  };

  // Crear HTML completo
  const htmlContent = `
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>${title}</title>
        <style>
            ${customCSS || defaultCSS}
        </style>
    </head>
    <body>
        <div class="header-info">
            <strong>Informe Generado por Manus AI</strong><br>
            ${new Date().toLocaleDateString()} • ${new Date().toLocaleTimeString()}
        </div>
        
        <h1>${title}</h1>
        
        <div class="content">
            ${convertMarkdownToHTML(content)}
        </div>
        
        <div class="footer-info">
            Informe generado automáticamente por Manus AI
        </div>
    </body>
    </html>
  `;

  try {
    // Crear un elemento temporal para renderizar el HTML
    const tempContainer = document.createElement('div');
    tempContainer.innerHTML = htmlContent;
    tempContainer.style.position = 'absolute';
    tempContainer.style.left = '-9999px';
    tempContainer.style.top = '-9999px';
    tempContainer.style.width = '210mm'; // A4 width
    tempContainer.style.backgroundColor = '#f9f9f9';
    tempContainer.style.padding = '20px';
    document.body.appendChild(tempContainer);

    // Crear el PDF usando html2canvas y jsPDF
    const canvas = await html2canvas(tempContainer, {
      scale: 2,
      useCORS: true,
      allowTaint: true,
      backgroundColor: '#f9f9f9',
      width: 794, // A4 width in pixels at 96 DPI
      height: 1123, // A4 height in pixels at 96 DPI
    });

    // Limpiar el elemento temporal
    document.body.removeChild(tempContainer);

    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF('p', 'mm', 'a4');
    
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();
    const imgWidth = canvas.width;
    const imgHeight = canvas.height;
    const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight);
    const imgX = (pdfWidth - imgWidth * ratio) / 2;
    const imgY = 0;

    pdf.addImage(imgData, 'PNG', imgX, imgY, imgWidth * ratio, imgHeight * ratio);

    // Si el contenido es muy largo, agregar páginas adicionales
    if (imgHeight * ratio > pdfHeight) {
      let currentHeight = pdfHeight;
      while (currentHeight < imgHeight * ratio) {
        pdf.addPage();
        pdf.addImage(
          imgData, 
          'PNG', 
          imgX, 
          -currentHeight, 
          imgWidth * ratio, 
          imgHeight * ratio
        );
        currentHeight += pdfHeight;
      }
    }

    // Descargar el PDF
    const finalFilename = filename || `${title.replace(/[^a-zA-Z0-9]/g, '_')}_${new Date().toISOString().slice(0, 10)}.pdf`;
    pdf.save(finalFilename);

  } catch (error) {
    console.error('Error generando PDF:', error);
    
    // Fallback: generar PDF simple con jsPDF
    const pdf = new jsPDF('p', 'mm', 'a4');
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const margin = 20;
    const contentWidth = pageWidth - 2 * margin;
    
    // Header
    pdf.setFontSize(20);
    pdf.setFont('helvetica', 'bold');
    pdf.text(title, margin, margin + 10, { maxWidth: contentWidth });
    
    // Metadata
    pdf.setFontSize(10);
    pdf.setFont('helvetica', 'normal');
    pdf.text(`Generado por Manus AI • ${new Date().toLocaleDateString()}`, margin, margin + 25);
    
    // Content
    const lines = content.split('\n');
    let yPosition = margin + 45;
    
    lines.forEach(line => {
      if (yPosition > pageHeight - margin) {
        pdf.addPage();
        yPosition = margin;
      }
      
      if (line.startsWith('# ')) {
        pdf.setFontSize(16);
        pdf.setFont('helvetica', 'bold');
        pdf.text(line.substring(2), margin, yPosition);
        yPosition += 10;
      } else if (line.startsWith('## ')) {
        pdf.setFontSize(14);
        pdf.setFont('helvetica', 'bold');
        pdf.text(line.substring(3), margin, yPosition);
        yPosition += 8;
      } else if (line.startsWith('### ')) {
        pdf.setFontSize(12);
        pdf.setFont('helvetica', 'bold');
        pdf.text(line.substring(4), margin, yPosition);
        yPosition += 6;
      } else if (line.trim()) {
        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');
        const splitText = pdf.splitTextToSize(line, contentWidth);
        pdf.text(splitText, margin, yPosition);
        yPosition += splitText.length * 4;
      } else {
        yPosition += 4;
      }
    });
    
    const finalFilename = filename || `${title.replace(/[^a-zA-Z0-9]/g, '_')}_${new Date().toISOString().slice(0, 10)}.pdf`;
    pdf.save(finalFilename);
  }
};

export const downloadMarkdownFile = (content: string, title: string): void => {
  const blob = new Blob([content], { type: 'text/markdown' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${title.replace(/[^a-zA-Z0-9]/g, '_')}_${new Date().toISOString().slice(0, 10)}.md`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};