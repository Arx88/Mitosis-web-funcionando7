import React from 'react';
import { Terminal, Globe, FileText, Command, CheckCircle, Clock, AlertCircle, Loader, Activity } from 'lucide-react';

interface ToolExecutionDetailsProps {
  tool: string;
  command?: string;
  parameters?: Record<string, any>;
  status?: 'executing' | 'completed' | 'error' | 'pending';
  className?: string;
  showDetailedView?: boolean;
}

export const ToolExecutionDetails: React.FC<ToolExecutionDetailsProps> = ({
  tool,
  command,
  parameters = {},
  status = 'pending',
  className = '',
  showDetailedView = false
}) => {
  
  const getToolIcon = (toolName: string) => {
    const iconClass = showDetailedView ? "w-5 h-5" : "w-4 h-4";
    
    switch (toolName.toLowerCase()) {
      case 'shell':
        return <Terminal className={`${iconClass} text-green-400`} />;
      case 'web_search':
        return <Globe className={`${iconClass} text-blue-400`} />;
      case 'file_manager':
        return <FileText className={`${iconClass} text-yellow-400`} />;
      default:
        return <Command className={`${iconClass} text-gray-400`} />;
    }
  };

  const getStatusIcon = (currentStatus: string) => {
    const iconClass = showDetailedView ? "w-5 h-5" : "w-4 h-4";
    
    switch (currentStatus) {
      case 'executing':
        return <Loader className={`${iconClass} text-blue-400 animate-spin`} />;
      case 'completed':
        return <CheckCircle className={`${iconClass} text-green-400`} />;
      case 'error':
        return <AlertCircle className={`${iconClass} text-red-400`} />;
      case 'pending':
      default:
        return <Clock className={`${iconClass} text-gray-400`} />;
    }
  };

  const getStatusColor = (currentStatus: string) => {
    switch (currentStatus) {
      case 'executing':
        return 'border-blue-500/30 bg-blue-500/10';
      case 'completed':
        return 'border-green-500/30 bg-green-500/10';
      case 'error':
        return 'border-red-500/30 bg-red-500/10';
      case 'pending':
      default:
        return 'border-gray-500/30 bg-gray-500/10';
    }
  };

  const formatParameters = (params: Record<string, any>) => {
    return Object.entries(params)
      .map(([key, value]) => `${key}: ${String(value)}`)
      .join(', ');
  };

  const getToolDisplayName = (toolName: string) => {
    const names = {
      'shell': 'Terminal',
      'web_search': 'Búsqueda Web',
      'file_manager': 'Gestor de Archivos'
    };
    return names[toolName as keyof typeof names] || toolName;
  };

  const getCommandDescription = (tool: string, params: Record<string, any>) => {
    switch (tool.toLowerCase()) {
      case 'shell':
        return params.command ? `Ejecutando: ${params.command}` : 'Ejecutando comando de terminal';
      case 'web_search':
        return params.query ? `Buscando: "${params.query}"` : 'Realizando búsqueda web';
      case 'file_manager':
        const action = params.action;
        const path = params.path;
        if (action && path) {
          const actionText = {
            'read': 'Leyendo',
            'write': 'Escribiendo',
            'create': 'Creando',
            'delete': 'Eliminando',
            'list': 'Listando',
            'copy': 'Copiando',
            'move': 'Moviendo',
            'mkdir': 'Creando directorio'
          }[action] || action;
          return `${actionText}: ${path}`;
        }
        return 'Gestionando archivos';
      default:
        return 'Ejecutando herramienta';
    }
  };

  const getStatusText = (currentStatus: string) => {
    switch (currentStatus) {
      case 'executing':
        return 'Ejecutando...';
      case 'completed':
        return 'Completado';
      case 'error':
        return 'Error';
      case 'pending':
      default:
        return 'Pendiente';
    }
  };

  if (showDetailedView) {
    return (
      <div className={`
        flex flex-col gap-3 p-4 rounded-lg border transition-all duration-200
        ${getStatusColor(status)} ${className}
      `}>
        {/* Header with tool and status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getToolIcon(tool)}
            <div className="flex flex-col">
              <span className="text-sm font-semibold text-[#DADADA]">
                {getToolDisplayName(tool)}
              </span>
              <span className="text-xs text-[#ACACAC]">
                Herramienta de automatización
              </span>
            </div>
          </div>
          
          {/* Status indicator with animation */}
          <div className="flex items-center gap-2">
            {status === 'executing' && (
              <Activity className="w-4 h-4 text-blue-400 animate-pulse" />
            )}
            {getStatusIcon(status)}
            <span className={`text-xs font-medium ${
              status === 'executing' ? 'text-blue-400' :
              status === 'completed' ? 'text-green-400' :
              status === 'error' ? 'text-red-400' :
              'text-gray-400'
            }`}>
              {getStatusText(status)}
            </span>
          </div>
        </div>

        {/* Command/Action Description */}
        <div className="bg-[#1E1E1F] rounded-md p-3 border border-[rgba(255,255,255,0.08)]">
          <div className="text-sm text-[#DADADA] font-medium mb-1">
            Acción actual:
          </div>
          <div className="text-sm text-[#ACACAC] font-mono">
            {getCommandDescription(tool, parameters)}
          </div>
        </div>

        {/* Parameters detail if available */}
        {Object.keys(parameters).length > 0 && (
          <div className="bg-[#1E1E1F] rounded-md p-3 border border-[rgba(255,255,255,0.08)]">
            <div className="text-xs text-[#7f7f7f] mb-2">Parámetros:</div>
            <div className="space-y-1">
              {Object.entries(parameters).map(([key, value]) => (
                <div key={key} className="flex items-start gap-2 text-xs">
                  <span className="text-[#ACACAC] font-medium min-w-0 flex-shrink-0">
                    {key}:
                  </span>
                  <span className="text-[#7f7f7f] font-mono break-all">
                    {String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Original compact view
  return (
    <div className={`
      flex items-center gap-3 px-3 py-2 rounded-lg border transition-all duration-200
      ${getStatusColor(status)} ${className}
    `}>
      {/* Tool Icon */}
      <div className="flex-shrink-0 flex items-center gap-2">
        {getToolIcon(tool)}
        <span className="text-sm font-medium text-[#DADADA]">
          {getToolDisplayName(tool)}
        </span>
      </div>

      {/* Command/Parameters */}
      <div className="flex-1 min-w-0">
        {command && (
          <div className="text-xs text-[#ACACAC] font-mono truncate">
            {command}
          </div>
        )}
        {Object.keys(parameters).length > 0 && (
          <div className="text-xs text-[#7f7f7f] truncate">
            {formatParameters(parameters)}
          </div>
        )}
      </div>

      {/* Status Icon */}
      <div className="flex-shrink-0 flex items-center gap-2">
        {getStatusIcon(status)}
        <span className="text-xs text-[#7f7f7f] capitalize">
          {getStatusText(status)}
        </span>
      </div>
    </div>
  );
};