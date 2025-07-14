import React, { useState, useEffect } from 'react';
import { Download, FileText, ExternalLink, Maximize2, Minimize2, Share2, Copy, Check } from 'lucide-react';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

interface AcademicMarkdownRendererProps {
  content: string;
  title: string;
  onDownloadPDF: () => void;
  onDownloadMarkdown: () => void;
  className?: string;
  statistics?: {
    totalWords: number;
    readingTime: number;
    sections: number;
    references: number;
  };
  qualityScore?: number;
}

export const AcademicMarkdownRenderer: React.FC<AcademicMarkdownRendererProps> = ({
  content,
  title,
  onDownloadPDF,
  onDownloadMarkdown,
  className = '',
  statistics,
  qualityScore
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);

  // Enhanced PDF generation with jsPDF
  const generateProfessionalPDF = async () => {
    setIsGeneratingPDF(true);
    
    try {
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const margin = 20;
      const contentWidth = pageWidth - 2 * margin;
      
      // Add header
      pdf.setFontSize(20);
      pdf.setFont('helvetica', 'bold');
      pdf.text(title, margin, margin + 10, { maxWidth: contentWidth });
      
      // Add metadata
      pdf.setFontSize(10);
      pdf.setFont('helvetica', 'normal');
      pdf.text(`Generado por AURA • ${new Date().toLocaleDateString()}`, margin, margin + 25);
      
      if (statistics) {
        pdf.text(`${statistics.totalWords} palabras • ${statistics.readingTime} min lectura • ${statistics.sections} secciones`, margin, margin + 30);
      }
      
      // Add content
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
      
      const filename = `${title.replace(/[^a-zA-Z0-9]/g, '_')}_${new Date().toISOString().slice(0, 10)}.pdf`;
      pdf.save(filename);
      
    } catch (error) {
      console.error('Error generating PDF:', error);
      // Fallback to original method
      onDownloadPDF();
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Error copying to clipboard:', error);
    }
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };
  // Enhanced markdown processing with better styling
  const processMarkdownContent = (content: string) => {
    if (!content) return [];

    const lines = content.split('\n');
    const processedLines = [];
    let codeBlockContent = '';
    let inCodeBlock = false;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Code blocks
      if (line.startsWith('```')) {
        if (inCodeBlock) {
          // End of code block
          processedLines.push(
            <div key={i} className="bg-[#1a1a1a] border border-[rgba(255,255,255,0.15)] rounded-lg p-4 mb-4 overflow-x-auto">
              <pre className="text-[#DADADA] text-sm font-mono leading-relaxed whitespace-pre-wrap">
                {codeBlockContent}
              </pre>
            </div>
          );
          codeBlockContent = '';
          inCodeBlock = false;
        } else {
          // Start of code block
          inCodeBlock = true;
          const language = line.substring(3).trim();
          if (language) {
            processedLines.push(
              <div key={`lang-${i}`} className="text-xs text-[#ACACAC] mb-1 font-mono">
                {language}
              </div>
            );
          }
        }
        continue;
      }
      
      if (inCodeBlock) {
        codeBlockContent += line + '\n';
        continue;
      }
      
      // Headers with enhanced styling
      if (line.startsWith('# ')) {
        processedLines.push(
          <h1 key={i} className="text-3xl font-bold text-[#DADADA] mb-8 pb-3 border-b-2 border-gradient-to-r from-blue-500 to-purple-600">
            {line.substring(2)}
          </h1>
        );
      } else if (line.startsWith('## ')) {
        processedLines.push(
          <h2 key={i} className="text-2xl font-semibold text-[#DADADA] mb-6 mt-10 pb-2 border-b border-[rgba(255,255,255,0.2)]">
            {line.substring(3)}
          </h2>
        );
      } else if (line.startsWith('### ')) {
        processedLines.push(
          <h3 key={i} className="text-xl font-medium text-[#DADADA] mb-4 mt-8">
            {line.substring(4)}
          </h3>
        );
      } else if (line.startsWith('#### ')) {
        processedLines.push(
          <h4 key={i} className="text-lg font-medium text-[#DADADA] mb-3 mt-6">
            {line.substring(5)}
          </h4>
        );
      }
      // Enhanced bullet points
      else if (line.startsWith('- ') || line.startsWith('* ')) {
        processedLines.push(
          <div key={i} className="flex items-start gap-3 mb-3 text-[#DADADA] text-sm leading-relaxed">
            <div className="w-2 h-2 bg-gradient-to-r from-blue-400 to-purple-500 rounded-full mt-2 flex-shrink-0"></div>
            <span>{line.substring(2)}</span>
          </div>
        );
      }
      // Enhanced numbered lists
      else if (/^\d+\.\s/.test(line)) {
        const match = line.match(/^(\d+)\.\s(.*)$/);
        if (match) {
          processedLines.push(
            <div key={i} className="flex items-start gap-3 mb-3 text-[#DADADA] text-sm leading-relaxed">
              <span className="text-blue-400 font-bold min-w-[24px] bg-blue-500/20 rounded-full w-6 h-6 flex items-center justify-center text-xs">
                {match[1]}
              </span>
              <span>{match[2]}</span>
            </div>
          );
        }
      }
      // Enhanced bold text
      else if (line.includes('**')) {
        const processedLine = line.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-[#DADADA] bg-gradient-to-r from-blue-500/20 to-purple-500/20 px-1 rounded">$1</strong>');
        processedLines.push(
          <p key={i} className="text-[#DADADA] text-sm leading-relaxed mb-4" dangerouslySetInnerHTML={{ __html: processedLine }} />
        );
      }
      // Enhanced blockquotes
      else if (line.startsWith('> ')) {
        processedLines.push(
          <div key={i} className="border-l-4 border-gradient-to-b from-blue-500 to-purple-600 pl-6 py-3 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-r-lg mb-4">
            <p className="text-[#DADADA] text-sm italic leading-relaxed font-medium">
              {line.substring(2)}
            </p>
          </div>
        );
      }
      // Enhanced links
      else if (line.includes('http')) {
        const processedLine = line.replace(
          /(https?:\/\/[^\s]+)/g, 
          '<a href="$1" target="_blank" class="text-blue-400 hover:text-blue-300 underline decoration-blue-400/50 hover:decoration-blue-300 transition-colors font-medium">$1</a>'
        );
        processedLines.push(
          <p key={i} className="text-[#DADADA] text-sm leading-relaxed mb-4" dangerouslySetInnerHTML={{ __html: processedLine }} />
        );
      }
      // Table detection
      else if (line.includes('|') && line.trim().length > 0) {
        const cells = line.split('|').filter(cell => cell.trim() !== '').map(cell => cell.trim());
        if (cells.length > 1) {
          processedLines.push(
            <div key={i} className="overflow-x-auto mb-4">
              <table className="w-full border-collapse border border-[rgba(255,255,255,0.2)]">
                <tr>
                  {cells.map((cell, idx) => (
                    <td key={idx} className="border border-[rgba(255,255,255,0.1)] px-3 py-2 text-[#DADADA] text-sm">
                      {cell}
                    </td>
                  ))}
                </tr>
              </table>
            </div>
          );
        }
      }
      // Empty lines
      else if (line.trim() === '') {
        processedLines.push(<div key={i} className="mb-3"></div>);
      }
      // Regular paragraphs
      else if (line.trim() !== '') {
        processedLines.push(
          <p key={i} className="text-[#DADADA] text-sm leading-relaxed mb-4 text-justify">
            {line}
          </p>
        );
      }
    }
    
    return processedLines;
  };

  const processedContent = processMarkdownContent(content);

  const containerClasses = isFullscreen 
    ? 'fixed inset-0 z-50 bg-[#1E1E1F] flex flex-col'
    : `bg-[#1E1E1F] border border-[rgba(255,255,255,0.08)] rounded-lg overflow-hidden ${className}`;

  return (
    <div className={containerClasses}>
      {/* Enhanced Header */}
      <div className="bg-gradient-to-r from-[#2a2a2b] to-[#1e1e1f] p-4 border-b border-[rgba(255,255,255,0.08)] flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-lg">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-[#DADADA] mb-1">📋 INFORME ACADÉMICO</h2>
              <p className="text-sm text-[#ACACAC]">{title}</p>
              {statistics && (
                <div className="flex items-center gap-4 mt-1">
                  <span className="text-xs text-[#7f7f7f]">
                    {statistics.totalWords.toLocaleString()} palabras
                  </span>
                  <span className="text-xs text-[#7f7f7f]">
                    {statistics.readingTime} min lectura
                  </span>
                  <span className="text-xs text-[#7f7f7f]">
                    {statistics.sections} secciones
                  </span>
                  {qualityScore && (
                    <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">
                      {qualityScore}% calidad
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={copyToClipboard}
              className="flex items-center gap-2 px-3 py-1.5 bg-gray-500/20 hover:bg-gray-500/30 text-gray-400 rounded-lg text-sm font-medium transition-colors"
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copiado' : 'Copiar'}
            </button>
            <button
              onClick={toggleFullscreen}
              className="flex items-center gap-2 px-3 py-1.5 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 rounded-lg text-sm font-medium transition-colors"
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              {isFullscreen ? 'Minimizar' : 'Pantalla completa'}
            </button>
            <button
              onClick={onDownloadMarkdown}
              className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg text-sm font-medium transition-colors"
            >
              <Download className="w-4 h-4" />
              Markdown
            </button>
            <button
              onClick={generateProfessionalPDF}
              disabled={isGeneratingPDF}
              className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-lg text-sm font-medium transition-all duration-200 disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              {isGeneratingPDF ? 'Generando...' : 'PDF'}
            </button>
          </div>
        </div>
      </div>

      {/* Enhanced Content */}
      <div className={`bg-[#1a1a1b] overflow-y-auto custom-scrollbar flex-1 ${isFullscreen ? 'p-8' : 'p-6'}`}>
        <div className="max-w-none">
          {processedContent.length > 0 ? (
            <div className="space-y-1">
              {processedContent}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-[#7f7f7f] text-sm">
                No hay contenido disponible para mostrar
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Enhanced Footer */}
      <div className="bg-[#252526] p-4 border-t border-[rgba(255,255,255,0.08)] flex-shrink-0">
        <div className="flex items-center justify-between text-xs text-[#ACACAC]">
          <div className="flex items-center gap-4">
            <span>Generado por AURA • Informe académico profesional</span>
            {statistics && (
              <span>
                {statistics.totalWords.toLocaleString()} palabras • {statistics.sections} secciones • {statistics.references} referencias
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span>{new Date().toLocaleDateString()} • {new Date().toLocaleTimeString()}</span>
            {qualityScore && (
              <span className="bg-green-500/20 text-green-400 px-2 py-0.5 rounded">
                Calidad: {qualityScore}%
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AcademicMarkdownRenderer;