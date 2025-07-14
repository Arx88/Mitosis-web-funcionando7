import React from 'react';
import { X, AlertTriangle } from 'lucide-react';

interface DeleteConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  taskTitle: string;
}

export const DeleteConfirmationModal: React.FC<DeleteConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  taskTitle
}) => {
  if (!isOpen) return null;

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-[#272728] rounded-xl border border-[rgba(255,255,255,0.08)] w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[rgba(255,255,255,0.08)]">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <h2 className="text-lg font-bold text-[#DADADA]">Confirmar Eliminación</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[#383739] rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-[#DADADA]" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          <div className="mb-4">
            <p className="text-[#DADADA] mb-2">
              ¿Estás seguro de que quieres eliminar esta tarea?
            </p>
            <div className="bg-[#383739] rounded-lg p-3 border border-[rgba(255,255,255,0.08)]">
              <p className="text-sm font-medium text-[#DADADA]">{taskTitle}</p>
            </div>
          </div>
          
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <span className="text-sm text-red-400 font-medium">¡Atención!</span>
            </div>
            <p className="text-sm text-red-400 mt-1">
              Esta acción no se puede deshacer. Se perderán todos los mensajes y archivos asociados a esta tarea.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-[#383739] hover:bg-[#404142] rounded-lg text-sm text-[#DADADA] transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={handleConfirm}
              className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm text-white transition-colors"
            >
              Eliminar Tarea
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};