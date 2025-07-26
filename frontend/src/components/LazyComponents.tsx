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
  import('./ConfigPanel')
);

export const FilesModal = React.lazy(() => 
  import('./FilesModal')
);

export const ShareModal = React.lazy(() => 
  import('./ShareModal')
);

export const FileUploadModal = React.lazy(() => 
  import('./FileUploadModal')
);

// Solo incluir componentes que existen y funcionan
export const MemoryManager = React.lazy(() => 
  import('./MemoryManager')
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
// LOADING FALLBACKS ESPECÍFICOS
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
  if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
    window.requestIdleCallback(() => {
      importFunction().then(() => {
        preloadedComponents.add(name);
        console.log(`🚀 Preloaded component: ${name}`);
      }).catch((error) => {
        console.warn(`⚠️ Failed to preload component ${name}:`, error);
      });
    });
  } else if (typeof window !== 'undefined') {
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
// PRELOAD CRITICAL COMPONENTS ON APP START
// ========================================================================

export const preloadCriticalComponents = () => {
  // Preload components que es probable que se usen pronto
  preloadComponent('FilesModal', () => import('./FilesModal'));
  preloadComponent('ShareModal', () => import('./ShareModal'));
  preloadComponent('ConfigPanel', () => import('./ConfigPanel'));
};

// Auto-preload on module load (solo en el cliente)
if (typeof window !== 'undefined') {
  // Delay preloading to not interfere with initial render
  setTimeout(preloadCriticalComponents, 2000);
}