/**
 * Code Splitting Configuration - VERSION ESTABLE
 * Lazy loading robusto con mejor manejo de errores
 */

import React, { Suspense } from 'react';
import { LoadingPlaceholder } from './LoadingPlaceholder';

// ========================================================================
// LAZY LOADED COMPONENTS CON ERROR HANDLING MEJORADO
// ========================================================================

// Helper para crear lazy components con mejor error handling
const createLazyComponent = (importFn: () => Promise<any>, componentName: string) => {
  return React.lazy(async () => {
    try {
      const module = await importFn();
      console.log(`✅ Lazy component loaded successfully: ${componentName}`);
      return module;
    } catch (error) {
      console.error(`❌ Failed to load lazy component ${componentName}:`, error);
      // Fallback component en caso de error
      return {
        default: () => (
          <div className="p-4 border border-red-500 rounded bg-red-50 text-red-700">
            <h3>Error loading {componentName}</h3>
            <p>Component failed to load. Please refresh the page.</p>
          </div>
        )
      };
    }
  });
};

// Componentes lazy con error handling mejorado
export const ConfigPanel = createLazyComponent(
  () => import('./ConfigPanel'),
  'ConfigPanel'
);

export const FilesModal = createLazyComponent(
  () => import('./FilesModal'),
  'FilesModal'
);

export const ShareModal = createLazyComponent(
  () => import('./ShareModal'),
  'ShareModal'
);

export const FileUploadModal = createLazyComponent(
  () => import('./FileUploadModal'),
  'FileUploadModal'
);

export const MemoryManager = createLazyComponent(
  () => import('./MemoryManager'),
  'MemoryManager'
);

// ========================================================================
// WRAPPER COMPONENTS CON SUSPENSE ROBUSTO
// ========================================================================

interface LazyWrapperProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onError?: (error: Error) => void;
}

const defaultFallback = <LoadingPlaceholder type="card" className="w-full h-64" />;

// Error Boundary específico para lazy components
class LazyErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ReactNode; onError?: (error: Error) => void },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('LazyErrorBoundary caught error:', error, errorInfo);
    this.props.onError?.(error);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-4 border border-yellow-500 rounded bg-yellow-50 text-yellow-700">
          <h3>Component Error</h3>
          <p>A component failed to load. The app continues to work normally.</p>
          <button 
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-2 px-3 py-1 bg-yellow-600 text-white rounded text-sm"
          >
            Retry
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export const LazyWrapper: React.FC<LazyWrapperProps> = ({ 
  children, 
  fallback = defaultFallback,
  onError
}) => (
  <LazyErrorBoundary fallback={fallback} onError={onError}>
    <Suspense fallback={fallback}>
      {children}
    </Suspense>
  </LazyErrorBoundary>
);

// ========================================================================
// LOADING FALLBACKS MEJORADOS
// ========================================================================

export const ModalLoadingFallback: React.FC = () => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-[#212122] rounded-lg border border-[rgba(255,255,255,0.08)] p-8">
      <LoadingPlaceholder type="card" className="w-96 h-64" />
      <p className="text-center text-gray-400 mt-4">Loading component...</p>
    </div>
  </div>
);

export const PanelLoadingFallback: React.FC = () => (
  <div className="h-full w-full p-4">
    <LoadingPlaceholder type="card" className="w-full h-full" />
    <p className="text-center text-gray-400 mt-4">Loading panel...</p>
  </div>
);

// ========================================================================
// PRELOADING UTILITIES MEJORADAS
// ========================================================================

type PreloadableComponent = () => Promise<{ default: React.ComponentType<any> }>;

const preloadedComponents = new Set<string>();

export const preloadComponent = (
  name: string, 
  importFunction: PreloadableComponent
): Promise<void> => {
  if (preloadedComponents.has(name)) {
    return Promise.resolve();
  }
  
  return new Promise((resolve, reject) => {
    const doPreload = () => {
      importFunction()
        .then(() => {
          preloadedComponents.add(name);
          console.log(`🚀 Preloaded component: ${name}`);
          resolve();
        })
        .catch((error) => {
          console.warn(`⚠️ Failed to preload component ${name}:`, error);
          reject(error);
        });
    };

    if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
      window.requestIdleCallback(doPreload);
    } else if (typeof window !== 'undefined') {
      setTimeout(doPreload, 100);
    } else {
      doPreload();
    }
  });
};

// ========================================================================
// PRELOAD CRITICAL COMPONENTS MEJORADO
// ========================================================================

export const preloadCriticalComponents = async (): Promise<void> => {
  const components = [
    { name: 'FilesModal', import: () => import('./FilesModal') },
    { name: 'ShareModal', import: () => import('./ShareModal') },
    { name: 'ConfigPanel', import: () => import('./ConfigPanel') }
  ];

  try {
    await Promise.allSettled(
      components.map(({ name, import: importFn }) => 
        preloadComponent(name, importFn)
      )
    );
    console.log('✅ Critical components preloading completed');
  } catch (error) {
    console.warn('⚠️ Some components failed to preload:', error);
  }
};

// Auto-preload en el cliente con delay mejorado
if (typeof window !== 'undefined') {
  // Delay más largo para asegurar que el app esté estable
  setTimeout(() => {
    preloadCriticalComponents().catch(console.warn);
  }, 5000);
}