/**
 * Code Splitting Configuration - Fase 5: Optimización de Performance
 * Lazy loading de componentes para reducir bundle size inicial
 */

import React, { Suspense } from 'react';
import { LoadingPlaceholder } from './LoadingPlaceholder';

// ========================================================================
// LAZY LOADED COMPONENTS - REDUCIR BUNDLE INICIAL
// ========================================================================

// Componentes pesados que no se necesitan inmediatamente
export const ConfigPanel = React.lazy(() => 
  import('./ConfigPanel').then(module => ({ default: module.ConfigPanel }))
);

export const FilesModal = React.lazy(() => 
  import('./FilesModal').then(module => ({ default: module.FilesModal }))
);

export const ShareModal = React.lazy(() => 
  import('./ShareModal').then(module => ({ default: module.ShareModal }))
);

export const FileUploadModal = React.lazy(() => 
  import('./FileUploadModal').then(module => ({ default: module.FileUploadModal }))
);

export const PDFViewer = React.lazy(() => 
  import('./PDFViewer').then(module => ({ default: module.PDFViewer }))
);

export const DeepResearchProgress = React.lazy(() => 
  import('./DeepResearchProgress').then(module => ({ default: module.DeepResearchProgress }))
);

export const DeepResearchReport = React.lazy(() => 
  import('./DeepResearchReport').then(module => ({ default: module.DeepResearchReport }))
);

export const EnhancedMonitoringDashboard = React.lazy(() => 
  import('./EnhancedMonitoringDashboard').then(module => ({ default: module.EnhancedMonitoringDashboard }))
);

export const MemoryManager = React.lazy(() => 
  import('./MemoryManager').then(module => ({ default: module.MemoryManager }))
);

// Componentes de contexto pesados
export const ContextVariablesPanel = React.lazy(() => 
  import('./ContextManager/ContextVariablesPanel').then(module => ({ default: module.ContextVariablesPanel }))
);

export const ContextCheckpointsPanel = React.lazy(() => 
  import('./ContextManager/ContextCheckpointsPanel').then(module => ({ default: module.ContextCheckpointsPanel }))
);

// Componentes de ejecución pesados
export const ExecutionControlPanel = React.lazy(() => 
  import('./ExecutionEngine/ExecutionControlPanel').then(module => ({ default: module.ExecutionControlPanel }))
);

export const TaskAnalysisPanel = React.lazy(() => 
  import('./ExecutionEngine/TaskAnalysisPanel').then(module => ({ default: module.TaskAnalysisPanel }))
);

// ========================================================================
// WRAPPER COMPONENTS CON SUSPENSE OPTIMIZADO
// ========================================================================

interface LazyWrapperProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  error?: React.ComponentType<any>;
}

const defaultFallback = <LoadingPlaceholder type="card" className="w-full h-64" />;

export const LazyWrapper: React.FC<LazyWrapperProps> = ({ 
  children, 
  fallback = defaultFallback 
}) => (
  <Suspense fallback={fallback}>
    {children}
  </Suspense>
);

// ========================================================================
// HIGH-ORDER COMPONENTS PARA LAZY LOADING FÁCIL
// ========================================================================

export const withLazyLoading = <P extends object>(
  importFunction: () => Promise<{ default: React.ComponentType<P> }>,
  fallback?: React.ReactNode
) => {
  const LazyComponent = React.lazy(importFunction);
  
  return React.forwardRef<any, P>((props, ref) => (
    <Suspense fallback={fallback || defaultFallback}>
      <LazyComponent {...props} ref={ref} />
    </Suspense>
  ));
};

// ========================================================================
// PRELOADING UTILITIES
// ========================================================================

type PreloadableComponent = () => Promise<{ default: React.ComponentType<any> }>;

const preloadedComponents = new Set<string>();

export const preloadComponent = (
  name: string, 
  importFunction: PreloadableComponent
): void => {
  if (preloadedComponents.has(name)) return;
  
  // Preload during idle time
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(() => {
      importFunction().then(() => {
        preloadedComponents.add(name);
        console.log(`🚀 Preloaded component: ${name}`);
      }).catch((error) => {
        console.warn(`⚠️ Failed to preload component ${name}:`, error);
      });
    });
  } else {
    // Fallback for browsers without requestIdleCallback
    setTimeout(() => {
      importFunction().then(() => {
        preloadedComponents.add(name);
        console.log(`🚀 Preloaded component: ${name}`);
      }).catch((error) => {
        console.warn(`⚠️ Failed to preload component ${name}:`, error);
      });
    }, 100);
  }
};

// ========================================================================
// SPECIFIC LOADING FALLBACKS
// ========================================================================

export const ModalLoadingFallback: React.FC = () => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-[#212122] rounded-lg border border-[rgba(255,255,255,0.08)] p-8">
      <LoadingPlaceholder type="card" className="w-96 h-64" />
    </div>
  </div>
);

export const PanelLoadingFallback: React.FC = () => (
  <div className="h-full w-full p-4">
    <LoadingPlaceholder type="card" className="w-full h-full" />
  </div>
);

export const DashboardLoadingFallback: React.FC = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
    {[...Array(6)].map((_, i) => (
      <LoadingPlaceholder key={i} type="card" className="h-48" />
    ))}
  </div>
);

// ========================================================================
// ROUTE-BASED CODE SPLITTING
// ========================================================================

// Para futuro uso si implementamos routing
export const RouteComponents = {
  Dashboard: React.lazy(() => import('./EnhancedMonitoringDashboard')),
  Memory: React.lazy(() => import('./MemoryManager')), 
  Settings: React.lazy(() => import('./ConfigPanel')),
  Files: React.lazy(() => import('./FilesModal'))
};

// ========================================================================
// BUNDLE ANALYSIS HELPERS
// ========================================================================

export const logBundleInfo = () => {
  if (process.env.NODE_ENV === 'development') {
    console.log('📦 Bundle Analysis:', {
      lazyComponents: [
        'ConfigPanel',
        'FilesModal', 
        'ShareModal',
        'FileUploadModal',
        'PDFViewer',
        'DeepResearchProgress',
        'DeepResearchReport',
        'EnhancedMonitoringDashboard',
        'MemoryManager',
        'ContextVariablesPanel',
        'ContextCheckpointsPanel',
        'ExecutionControlPanel',
        'TaskAnalysisPanel'
      ].length,
      preloadedComponents: preloadedComponents.size,
      suspenseEnabled: true
    });
  }
};

// ========================================================================
// PRELOAD CRITICAL COMPONENTS ON APP START
// ========================================================================

export const preloadCriticalComponents = () => {
  // Preload components que es probable que se usen pronto
  preloadComponent('FilesModal', () => import('./FilesModal'));
  preloadComponent('ShareModal', () => import('./ShareModal'));
  preloadComponent('ConfigPanel', () => import('./ConfigPanel'));
};

// Auto-preload on module load
if (typeof window !== 'undefined') {
  // Delay preloading to not interfere with initial render
  setTimeout(preloadCriticalComponents, 2000);
}