import React, { useState } from 'react';
import { X, Copy, Check, Share2, Link, ExternalLink, AlertCircle } from 'lucide-react';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  taskTitle: string;
  taskId: string;
  onGenerateLink: (taskId: string) => Promise<string>;
}

export const ShareModal: React.FC<ShareModalProps> = ({
  isOpen,
  onClose,
  taskTitle,
  taskId,
  onGenerateLink
}) => {
  const [shareLink, setShareLink] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [error, setError] = useState<string>('');

  if (!isOpen) return null;

  const generateShareLink = async () => {
    setIsGenerating(true);
    setError('');
    
    try {
      const link = await onGenerateLink(taskId);
      setShareLink(link);
    } catch (error) {
      console.error('Error generating share link:', error);
      setError('Error al generar el enlace. Verifica que el servidor esté funcionando.');
    } finally {
      setIsGenerating(false);
    }
  };

  const copyToClipboard = async () => {
    if (!shareLink) return;
    
    try {
      await navigator.clipboard.writeText(shareLink);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (error) {
      console.error('Error copying to clipboard:', error);
      // Fallback para navegadores que no soportan clipboard API
      const textArea = document.createElement('textarea');
      textArea.value = shareLink;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    }
  };

  const openInNewTab = () => {
    if (shareLink) {
      window.open(shareLink, '_blank');
    }
  };

  const handleClose = () => {
    // Limpiar estado al cerrar
    setShareLink('');
    setError('');
    setIsCopied(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-[#272728] rounded-xl border border-[rgba(255,255,255,0.08)] w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[rgba(255,255,255,0.08)]">
          <div className="flex items-center gap-2">
            <Share2 className="w-5 h-5 text-[#DADADA]" />
            <h2 className="text-lg font-bold text-[#DADADA]">Compartir Conversación</h2>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-[#383739] rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-[#DADADA]" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          <div className="mb-4">
            <h3 className="text-sm font-medium text-[#DADADA] mb-1">{taskTitle}</h3>
            <p className="text-xs text-[#7f7f7f]">
              Genera un enlace público para compartir esta conversación
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400" />
              <span className="text-sm text-red-400">{error}</span>
            </div>
          )}

          {!shareLink ? (
            <div className="text-center py-6">
              <Link className="w-12 h-12 text-[#7f7f7f] mx-auto mb-4" />
              <p className="text-[#ACACAC] mb-4">
                Haz clic para generar un enlace compartible
              </p>
              <button
                onClick={generateShareLink}
                disabled={isGenerating}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 
                  disabled:bg-[#7f7f7f] disabled:cursor-not-allowed rounded-lg text-white 
                  transition-colors mx-auto font-medium"
              >
                {isGenerating ? (
                  <>
                    <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                    Generando...
                  </>
                ) : (
                  <>
                    <Share2 className="w-4 h-4" />
                    Crear Enlace
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[#DADADA] mb-2">
                  Enlace público
                </label>
                <div className="flex items-center gap-2 p-3 bg-[#383739] rounded-lg">
                  <input
                    type="text"
                    value={shareLink}
                    readOnly
                    className="flex-1 bg-transparent text-sm text-[#DADADA] outline-none"
                  />
                  <button
                    onClick={copyToClipboard}
                    className="flex items-center gap-1 px-3 py-1.5 bg-[#4A4A4C] hover:bg-[#5A5A5C] 
                      rounded text-xs text-[#DADADA] transition-colors"
                  >
                    {isCopied ? (
                      <>
                        <Check className="w-3 h-3" />
                        Copiado
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        Copiar
                      </>
                    )}
                  </button>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={openInNewTab}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 
                    bg-[#383739] hover:bg-[#404142] rounded-lg text-sm text-[#DADADA] transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                  Abrir Enlace
                </button>
                <button
                  onClick={copyToClipboard}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 
                    bg-blue-600 hover:bg-blue-700 rounded-lg text-sm text-white transition-colors"
                >
                  <Copy className="w-4 h-4" />
                  Copiar Enlace
                </button>
              </div>

              <div className="text-xs text-[#7f7f7f] text-center">
                Este enlace es público y cualquier persona puede acceder a él
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};