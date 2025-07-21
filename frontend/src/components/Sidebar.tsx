import React, { useState } from 'react';
import { Task } from '../types';
import { PlusIcon, ClipboardListIcon, Settings, X, ChevronLeft, ChevronRight, Search, Edit3, Check, Star } from 'lucide-react';
import { DeleteConfirmationModal } from './DeleteConfirmationModal';
import { TaskIcon } from './TaskIcon';
import { TaskButtonStyles } from './TaskButtonStyles';

interface SidebarProps {
  tasks: Task[];
  activeTaskId: string | null;
  onTaskSelect: (taskId: string) => void;
  onCreateTask: (title: string, iconType?: string) => Task;
  onDeleteTask: (taskId: string) => void;
  onUpdateTask?: (task: Task) => void;
  onConfigOpen: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  tasks,
  activeTaskId,
  onTaskSelect,
  onCreateTask,
  onDeleteTask,
  onUpdateTask,
  onConfigOpen,
  isCollapsed,
  onToggleCollapse
}) => {
  const [hoveredTaskId, setHoveredTaskId] = useState<string | null>(null);
  const [deleteConfirmation, setDeleteConfirmation] = useState<{isOpen: boolean, taskId: string, taskTitle: string}>({
    isOpen: false,
    taskId: '',
    taskTitle: ''
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | 'favorites'>('all');

  // Función para crear tarea automáticamente
  const handleCreateTask = () => {
    const taskNumber = tasks.length + 1;
    const defaultTitle = `Tarea ${taskNumber}`;
    
    // Crear la nueva tarea - ya setea activeTaskId internamente
    onCreateTask(defaultTitle);
    
    // No necesitamos setTimeout ni setActiveTaskId adicional porque createTask ya lo hace
  };

  const handleDeleteTask = (taskId: string, taskTitle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleteConfirmation({
      isOpen: true,
      taskId,
      taskTitle
    });
  };

  const confirmDeleteTask = () => {
    onDeleteTask(deleteConfirmation.taskId);
    setDeleteConfirmation({ isOpen: false, taskId: '', taskTitle: '' });
  };

  const handleEditTask = (taskId: string, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingTaskId(taskId);
    setEditingTitle(currentTitle);
  };

  const saveTaskTitle = () => {
    if (editingTaskId && editingTitle.trim() && onUpdateTask) {
      const task = tasks.find(t => t.id === editingTaskId);
      if (task) {
        onUpdateTask({
          ...task,
          title: editingTitle.trim()
        });
      }
    }
    setEditingTaskId(null);
    setEditingTitle('');
  };

  const cancelEdit = () => {
    setEditingTaskId(null);
    setEditingTitle('');
  };

  // Función para toggle favorito
  const toggleFavorite = (taskId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (onUpdateTask) {
      const task = tasks.find(t => t.id === taskId);
      if (task) {
        onUpdateTask({
          ...task,
          isFavorite: !task.isFavorite
        });
      }
    }
  };

  // Filtrar tareas por búsqueda y tab activo
  const filteredTasks = tasks.filter(task => {
    // Filtro por búsqueda
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      const matchesSearch = task.title.toLowerCase().includes(query) ||
        task.messages.some(message => message.content.toLowerCase().includes(query));
      if (!matchesSearch) return false;
    }
    
    // Filtro por tab
    if (activeTab === 'favorites') {
      return task.isFavorite === true;
    }
    
    return true;
  });

  const favoritesCount = tasks.filter(task => task.isFavorite === true).length;

  return (
    <div className={`${isCollapsed ? 'w-16' : 'w-80'} bg-[#212122] border-r border-[rgba(255,255,255,0.08)] flex flex-col font-sans transition-all duration-300 flex-shrink-0`}>
      {/* Header */}
      <div className={`${isCollapsed ? 'p-2' : 'p-4'} border-b border-[rgba(255,255,255,0.08)] flex items-center justify-between min-h-[64px]`}>
        {!isCollapsed && (
          <div className="flex items-center gap-2">
            <img 
              src="/images/logo.png" 
              alt="Mitosis Logo" 
              className="h-10 w-auto opacity-90 ml-1 my-2"
            />
          </div>
        )}
        <button
          onClick={onToggleCollapse}
          className="p-2 rounded-lg hover:bg-[rgba(255,255,255,0.08)] transition-colors z-10"
          title={isCollapsed ? 'Expandir sidebar' : 'Contraer sidebar'}
        >
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4 text-[#ACACAC]" />
          ) : (
            <ChevronLeft className="w-4 h-4 text-[#ACACAC]" />
          )}
        </button>
      </div>
      
      {/* Nueva tarea - MEJORADO PARA PARECER MÁS BOTÓN */}
      <div className={`${isCollapsed ? 'p-2' : 'p-4'} border-b border-[rgba(255,255,255,0.08)]`}>
        <button 
          onClick={handleCreateTask} 
          className={`flex items-center w-full text-[#DADADA] rounded-xl hover:bg-[rgba(255,255,255,0.12)] transition-colors ${
            isCollapsed ? 'justify-center p-2 bg-[rgba(255,255,255,0.08)]' : 'px-4 py-3 bg-[rgba(255,255,255,0.08)]'
          }`}
          title={isCollapsed ? 'Nueva tarea' : ''}
        >
          <PlusIcon className={`w-4 h-4 ${!isCollapsed ? 'mr-2' : ''}`} />
          {!isCollapsed && <span className="font-medium">Nueva tarea</span>}
        </button>
      </div>
      
      {/* Barra de búsqueda - SIN BORDES */}
      {!isCollapsed && (
        <div className="p-4 border-b border-[rgba(255,255,255,0.08)]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#7f7f7f]" />
            <input
              type="text"
              placeholder="Buscar tareas..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#272728] rounded-lg pl-10 pr-4 py-2 text-sm text-[#DADADA] placeholder-[#7f7f7f] focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 hover:bg-[rgba(255,255,255,0.08)] rounded transition-colors"
              >
                <X className="w-3 h-3 text-[#7f7f7f]" />
              </button>
            )}
          </div>
          {searchQuery && (
            <div className="mt-2 text-xs text-[#7f7f7f]">
              {filteredTasks.length} de {tasks.length} tareas encontradas
            </div>
          )}
        </div>
      )}

      {/* Tabs de filtrado - SIEMPRE VISIBLE, adaptado para collapsed */}
      <div className={`${isCollapsed ? 'px-1 py-2' : 'px-4 py-2'} border-b border-[rgba(255,255,255,0.08)]`}>
        {isCollapsed ? (
          // Versión colapsada: iconos verticales centrados
          <div className="flex flex-col items-center space-y-1">
            <button
              onClick={() => setActiveTab('all')}
              className={`w-10 h-10 flex items-center justify-center rounded-lg transition-all duration-200 ${
                activeTab === 'all'
                  ? 'bg-[rgba(255,255,255,0.12)] text-[#DADADA] shadow-sm'
                  : 'text-[#ACACAC] hover:text-[#DADADA] hover:bg-[rgba(255,255,255,0.06)]'
              }`}
              title={`Todo (${tasks.length})`}
            >
              <ClipboardListIcon className="w-4 h-4" />
            </button>
            <button
              onClick={() => setActiveTab('favorites')}
              className={`w-10 h-10 flex items-center justify-center rounded-lg transition-all duration-200 ${
                activeTab === 'favorites'
                  ? 'bg-[rgba(255,255,255,0.12)] text-[#DADADA] shadow-sm'
                  : 'text-[#ACACAC] hover:text-[#DADADA] hover:bg-[rgba(255,255,255,0.06)]'
              }`}
              title={`Favoritos (${favoritesCount})`}
            >
              <Star className="w-4 h-4" />
            </button>
          </div>
        ) : (
          // Versión expandida: layout original
          <div className="flex items-center space-x-0.5 bg-[rgba(255,255,255,0.04)] p-1 rounded-lg">
            <button
              onClick={() => setActiveTab('all')}
              className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs font-medium rounded-md transition-all duration-200 ${
                activeTab === 'all'
                  ? 'bg-[rgba(255,255,255,0.12)] text-[#DADADA] shadow-sm'
                  : 'text-[#ACACAC] hover:text-[#DADADA] hover:bg-[rgba(255,255,255,0.06)]'
              }`}
            >
              <ClipboardListIcon className="w-3 h-3" />
              <span>Todo</span>
              <span className="bg-[rgba(255,255,255,0.15)] text-xs px-1 py-0.5 rounded text-[10px] leading-none min-w-[16px] text-center">
                {tasks.length}
              </span>
            </button>
            <button
              onClick={() => setActiveTab('favorites')}
              className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs font-medium rounded-md transition-all duration-200 ${
                activeTab === 'favorites'
                  ? 'bg-[rgba(255,255,255,0.12)] text-[#DADADA] shadow-sm'
                  : 'text-[#ACACAC] hover:text-[#DADADA] hover:bg-[rgba(255,255,255,0.06)]'
              }`}
            >
              <Star className="w-3 h-3" />
              <span>Favoritos</span>
              <span className="bg-[rgba(255,255,255,0.15)] text-xs px-1 py-0.5 rounded text-[10px] leading-none min-w-[16px] text-center">
                {favoritesCount}
              </span>
            </button>
          </div>
        )}
      </div>
      
      {/* Tareas - LAYOUT PROFESIONAL con scroll mejorado */}
      <div className="flex-1 overflow-hidden">
        <div className={`${isCollapsed ? 'p-1' : 'p-4'} h-full overflow-y-auto overflow-x-hidden custom-scrollbar`} style={{
          scrollbarWidth: 'thin',
          scrollbarColor: '#7f7f7f #383739'
        }}>
          <div className="space-y-2">
            {filteredTasks.map(task => (
              <div
                key={task.id}
                onMouseEnter={() => setHoveredTaskId(task.id)}
                onMouseLeave={() => setHoveredTaskId(null)}
                className={isCollapsed ? 'px-1' : ''}
              >
                <TaskButtonStyles
                  task={task}
                  isActive={task.id === activeTaskId}
                  isCollapsed={isCollapsed}
                  isHovered={hoveredTaskId === task.id}
                  isEditing={editingTaskId === task.id}
                  editingTitle={editingTitle}
                  onTaskSelect={onTaskSelect}
                  onEditTask={handleEditTask}
                  onDeleteTask={handleDeleteTask}
                  onSaveEdit={saveTaskTitle}
                  onEditTitleChange={setEditingTitle}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') saveTaskTitle();
                    if (e.key === 'Escape') cancelEdit();
                  }}
                />
              </div>
            ))}
            
            {/* Mensaje cuando no hay resultados de búsqueda */}
            {!isCollapsed && searchQuery && filteredTasks.length === 0 && (
              <div className="text-center py-6 text-[#7f7f7f] text-sm">
                No se encontraron tareas que coincidan con "{searchQuery}"
              </div>
            )}

            {/* Mensaje cuando no hay favoritos */}
            {!isCollapsed && activeTab === 'favorites' && !searchQuery && favoritesCount === 0 && (
              <div className="text-center py-8 text-[#7f7f7f] text-sm">
                <Star className="w-6 h-6 mx-auto mb-3 opacity-50" />
                <p className="font-medium">No tienes tareas favoritas</p>
                <p className="text-xs mt-1 opacity-75">Marca una tarea con ⭐ para agregarla aquí</p>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Configuración - MEJORADO PARA PARECER MÁS BOTÓN */}
      <div className={`${isCollapsed ? 'p-2' : 'p-4'} border-t border-[rgba(255,255,255,0.08)]`}>
        <button
          onClick={onConfigOpen}
          className={`flex items-center w-full text-[#DADADA] rounded-xl hover:bg-[rgba(255,255,255,0.12)] transition-colors ${
            isCollapsed ? 'justify-center p-2 bg-[rgba(255,255,255,0.08)]' : 'px-4 py-3 bg-[rgba(255,255,255,0.08)]'
          }`}
          title={isCollapsed ? 'Configuración' : ''}
        >
          <Settings className={`w-4 h-4 ${!isCollapsed ? 'mr-2' : ''}`} />
          {!isCollapsed && <span className="font-medium">Configuración</span>}
        </button>
      </div>
      
      {/* Modal de confirmación de eliminación */}
      <DeleteConfirmationModal
        isOpen={deleteConfirmation.isOpen}
        onClose={() => setDeleteConfirmation({ isOpen: false, taskId: '', taskTitle: '' })}
        onConfirm={confirmDeleteTask}
        taskTitle={deleteConfirmation.taskTitle}
      />
    </div>
  );
};