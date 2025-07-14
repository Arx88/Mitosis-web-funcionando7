import React from 'react';
import { Edit3, X, Check, Star, Clock, Zap, Diamond, Shield, Target, Flame, Sparkles, Crown, Hexagon } from 'lucide-react';
import { TaskIcon } from './TaskIcon';

interface TaskButtonStylesProps {
  task: any;
  isActive: boolean;
  isCollapsed: boolean;
  isHovered: boolean;
  isEditing: boolean;
  editingTitle: string;
  onTaskSelect: (taskId: string) => void;
  onEditTask: (taskId: string, title: string, e: React.MouseEvent) => void;
  onDeleteTask: (taskId: string, title: string, e: React.MouseEvent) => void;
  onSaveEdit: () => void;
  onEditTitleChange: (title: string) => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
}

export const TaskButtonStyles: React.FC<TaskButtonStylesProps> = ({
  task,
  isActive,
  isCollapsed,
  isHovered,
  isEditing,
  editingTitle,
  onTaskSelect,
  onEditTask,
  onDeleteTask,
  onSaveEdit,
  onEditTitleChange,
  onKeyDown
}) => {
  
  const getStyleByTaskTitle = (title: string) => {
    // All tasks will use the classic style
    return 'classic';
  };

  const style = getStyleByTaskTitle(task.title);

  const buttonStyles = {
    // Estilo 1: Clásico - Con bordes redondeados y colores suaves
    classic: {
      container: isActive 
        ? 'bg-gradient-to-r from-[#1d3470]/20 to-[#1d3470]/30 border-2 border-[#1d3470]/50' 
        : 'bg-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.08)] border-2 border-transparent hover:border-[#1d3470]/20',
      text: isActive ? 'text-blue-100' : 'text-[#DADADA]',
      icon: isActive ? 'text-[#1d3470] opacity-100' : 'text-[#ACACAC] opacity-80',
      editBtn: 'bg-[#3b82f6]/30 hover:bg-[#3b82f6]/40 text-[#93c5fd]',
      deleteBtn: 'bg-red-500/20 hover:bg-red-500/30 text-red-400'
    },
    
    // Estilo 2: Moderno - Con esquinas más afiladas y efectos de sombra
    modern: {
      container: isActive 
        ? 'bg-gradient-to-r from-emerald-500/20 to-teal-500/20 border-l-4 border-emerald-400 shadow-lg' 
        : 'bg-[rgba(255,255,255,0.05)] hover:bg-[rgba(255,255,255,0.1)] border-l-4 border-transparent hover:border-emerald-400/50',
      text: isActive ? 'text-emerald-100' : 'text-[#DADADA]',
      icon: isActive ? 'text-emerald-400' : 'text-[#ACACAC]',
      editBtn: 'bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400',
      deleteBtn: 'bg-red-500/20 hover:bg-red-500/30 text-red-400'
    },
    
    // Estilo 3: Neon - Con efectos brillantes y colores vibrantes
    neon: {
      container: isActive 
        ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-2 border-purple-400 shadow-[0_0_20px_rgba(168,85,247,0.3)]' 
        : 'bg-[rgba(255,255,255,0.03)] hover:bg-[rgba(255,255,255,0.07)] border-2 border-transparent hover:border-purple-400/50 hover:shadow-[0_0_15px_rgba(168,85,247,0.2)]',
      text: isActive ? 'text-purple-100' : 'text-[#DADADA]',
      icon: isActive ? 'text-purple-400' : 'text-[#ACACAC]',
      editBtn: 'bg-purple-500/25 hover:bg-purple-500/40 text-purple-300 shadow-[0_0_10px_rgba(168,85,247,0.3)]',
      deleteBtn: 'bg-pink-500/25 hover:bg-pink-500/40 text-pink-300 shadow-[0_0_10px_rgba(236,72,153,0.3)]'
    },
    
    // Estilo 4: Minimal - Limpio y minimalista
    minimal: {
      container: isActive 
        ? 'bg-white/10 border-b-2 border-white/30' 
        : 'bg-transparent hover:bg-white/05 border-b-2 border-transparent hover:border-white/20',
      text: isActive ? 'text-white' : 'text-[#DADADA]',
      icon: isActive ? 'text-white' : 'text-[#ACACAC]',
      editBtn: 'bg-white/10 hover:bg-white/20 text-white',
      deleteBtn: 'bg-white/10 hover:bg-white/20 text-white'
    },
    
    // Estilo 5: Elegante - Con gradientes suaves y tipografía refinada
    elegant: {
      container: isActive 
        ? 'bg-gradient-to-br from-amber-500/15 to-orange-500/15 border border-amber-400/50 shadow-md' 
        : 'bg-gradient-to-br from-[rgba(255,255,255,0.03)] to-[rgba(255,255,255,0.06)] hover:from-[rgba(255,255,255,0.06)] hover:to-[rgba(255,255,255,0.09)] border border-[rgba(255,255,255,0.08)] hover:border-amber-400/30',
      text: isActive ? 'text-amber-100 font-medium' : 'text-[#DADADA] font-medium',
      icon: isActive ? 'text-amber-400' : 'text-[#ACACAC]',
      editBtn: 'bg-amber-500/20 hover:bg-amber-500/30 text-amber-400',
      deleteBtn: 'bg-red-500/20 hover:bg-red-500/30 text-red-400'
    },
    
    // Estilo 6: Colorido - Con múltiples colores y efectos alegres
    colorful: {
      container: isActive 
        ? 'bg-gradient-to-r from-red-500/15 via-yellow-500/15 to-green-500/15 border-2 border-transparent bg-clip-padding' 
        : 'bg-gradient-to-r from-[rgba(255,255,255,0.04)] via-[rgba(255,255,255,0.06)] to-[rgba(255,255,255,0.04)] hover:from-red-500/10 hover:via-yellow-500/10 hover:to-green-500/10 border-2 border-transparent',
      text: isActive ? 'text-yellow-100' : 'text-[#DADADA]',
      icon: isActive ? 'text-yellow-400' : 'text-[#ACACAC]',
      editBtn: 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 hover:from-blue-500/30 hover:to-purple-500/30 text-blue-300',
      deleteBtn: 'bg-gradient-to-r from-red-500/20 to-pink-500/20 hover:from-red-500/30 hover:to-pink-500/30 text-red-300'
    },
    
    // Estilo 7: Profesional - Sobrio y empresarial
    professional: {
      container: isActive 
        ? 'bg-slate-600/20 border-2 border-slate-400/50' 
        : 'bg-slate-800/20 hover:bg-slate-700/30 border-2 border-slate-700/30 hover:border-slate-600/50',
      text: isActive ? 'text-slate-100' : 'text-[#DADADA]',
      icon: isActive ? 'text-slate-300' : 'text-[#ACACAC]',
      editBtn: 'bg-slate-500/20 hover:bg-slate-500/30 text-slate-300',
      deleteBtn: 'bg-red-600/20 hover:bg-red-600/30 text-red-300'
    },
    
    // Estilo 8: Futurista - Con formas geométricas y efectos tech
    futuristic: {
      container: isActive 
        ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/50 transform skew-x-[-2deg] shadow-[0_0_20px_rgba(6,182,212,0.2)]' 
        : 'bg-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.08)] border border-[rgba(255,255,255,0.08)] hover:border-cyan-400/30 transform skew-x-[-2deg] hover:shadow-[0_0_15px_rgba(6,182,212,0.1)]',
      text: isActive ? 'text-cyan-100 transform skew-x-[2deg]' : 'text-[#DADADA] transform skew-x-[2deg]',
      icon: isActive ? 'text-cyan-400' : 'text-[#ACACAC]',
      editBtn: 'bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 transform skew-x-[2deg]',
      deleteBtn: 'bg-red-500/20 hover:bg-red-500/30 text-red-400 transform skew-x-[2deg]'
    },
    
    // Estilo 9: Vintage - Con colores cálidos y efectos retro
    vintage: {
      container: isActive 
        ? 'bg-gradient-to-r from-yellow-600/20 to-orange-600/20 border-2 border-yellow-600/50 shadow-inner' 
        : 'bg-amber-900/10 hover:bg-amber-800/20 border-2 border-amber-800/20 hover:border-yellow-600/40',
      text: isActive ? 'text-yellow-100' : 'text-[#DADADA]',
      icon: isActive ? 'text-yellow-400' : 'text-[#ACACAC]',
      editBtn: 'bg-yellow-600/20 hover:bg-yellow-600/30 text-yellow-400',
      deleteBtn: 'bg-orange-600/20 hover:bg-orange-600/30 text-orange-400'
    },
    
    // Estilo 10: Gaming - Con efectos dinámicos y colores vibrantes
    gaming: {
      container: isActive 
        ? 'bg-gradient-to-r from-green-500/20 via-lime-500/20 to-green-500/20 border-2 border-green-400/50 shadow-[0_0_25px_rgba(34,197,94,0.3)] animate-pulse' 
        : 'bg-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.08)] border-2 border-[rgba(255,255,255,0.08)] hover:border-green-400/50 hover:shadow-[0_0_20px_rgba(34,197,94,0.2)]',
      text: isActive ? 'text-green-100 font-bold' : 'text-[#DADADA] font-bold',
      icon: isActive ? 'text-green-400' : 'text-[#ACACAC]',
      editBtn: 'bg-green-500/25 hover:bg-green-500/40 text-green-300 shadow-[0_0_10px_rgba(34,197,94,0.3)]',
      deleteBtn: 'bg-red-500/25 hover:bg-red-500/40 text-red-300 shadow-[0_0_10px_rgba(239,68,68,0.3)]'
    },
    
    // Estilo por defecto
    default: {
      container: isActive 
        ? 'bg-[rgba(255,255,255,0.08)] text-[#DADADA]' 
        : 'hover:bg-[rgba(255,255,255,0.06)] text-[#ACACAC]',
      text: isActive ? 'text-[#DADADA]' : 'text-[#ACACAC]',
      icon: isActive ? 'text-blue-400' : 'text-[#ACACAC]',
      editBtn: 'bg-[rgba(255,255,255,0.08)] hover:bg-blue-500/20 text-blue-400',
      deleteBtn: 'bg-[rgba(255,255,255,0.08)] hover:bg-red-500/20 text-red-400'
    }
  };

  const currentStyle = buttonStyles[style] || buttonStyles.default;

  return (
    <div className="relative group">
      <button 
        onClick={() => onTaskSelect(task.id)} 
        className={`w-full relative ${currentStyle.container} ${isCollapsed ? 'flex items-center justify-center p-2 rounded-lg' : 'text-left px-4 py-3 rounded-xl'} ${isActive ? 'task-button-active border-none' : ''}`}
        title={isCollapsed ? task.title : ''}
      >
        {isCollapsed ? (
          <div className="flex items-center justify-center w-8 h-8">
            <TaskIcon 
              type={task.iconType || task.title} 
              size="small" 
              showProgress={true}
              progressValue={task.progress || 0}
              isActive={isActive}
              isCompleted={task.status === 'completed'}
            />
          </div>
        ) : (
          <>
            {isEditing ? (
              <div className="pr-16" onClick={(e) => e.stopPropagation()}>
                <input
                  type="text"
                  value={editingTitle}
                  onChange={(e) => onEditTitleChange(e.target.value)}
                  onKeyDown={onKeyDown}
                  onBlur={onSaveEdit}
                  autoFocus
                  className="w-full bg-[#272728] rounded px-2 py-1 text-sm text-[#DADADA] focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                />
              </div>
            ) : (
              <div className="flex items-start gap-3">
                <div className="flex items-center justify-center">
                  <TaskIcon 
                    type={task.iconType || task.title} 
                    size="small" 
                    showProgress={true}
                    progressValue={task.progress || 0}
                    isActive={isActive}
                    isCompleted={task.status === 'completed'}
                  />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className={`truncate text-sm ${isActive ? 'font-medium' : 'font-light'} ${currentStyle.text} ${isHovered ? 'pr-20' : ''}`}>
                      {task.title}
                    </span>
                  </div>
                  <div className="flex items-center justify-between mt-0.5">
                    <div className="text-xs text-[#7f7f7f]">
                      {new Date(task.createdAt).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </button>
      
      {/* Botones de acción mejorados */}
      {isHovered && !isCollapsed && !isEditing && (
        <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex gap-1 z-10">
          <button
            onClick={(e) => onEditTask(task.id, task.title, e)}
            className={`p-1.5 rounded-lg transition-all duration-200 ${currentStyle.editBtn}`}
            title="Editar nombre"
          >
            <Edit3 className="w-3 h-3" />
          </button>
          <button
            onClick={(e) => onDeleteTask(task.id, task.title, e)}
            className={`p-1.5 rounded-lg transition-all duration-200 ${currentStyle.deleteBtn}`}
            title="Eliminar tarea"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      )}
      
      {/* Botón de confirmar edición */}
      {isEditing && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onSaveEdit();
          }}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg hover:bg-green-500/20 transition-colors"
          title="Guardar cambios"
        >
          <Check className="w-3 h-3 text-green-400" />
        </button>
      )}
    </div>
  );
};