import React, { useEffect, useState } from 'react';

// Función para verificar WebSocket sin usar el hook (evitar circularidad)
const checkWebSocketStatus = () => {
  try {
    // Importar socket.io-client directamente
    // @ts-ignore
    import('socket.io-client').then((io) => {
      console.log('✅ Socket.IO imported successfully:', !!io.io);
      return !!io.io;
    }).catch((e) => {
      console.error('❌ Failed to import socket.io-client:', e);
      return false;
    });
  } catch (e) {
    console.error('❌ Error checking socket.io:', e);
    return false;
  }
};

export const WebSocketDebug: React.FC = () => {
  const [socketIOLoaded, setSocketIOLoaded] = useState<boolean>(false);
  const [socketIOError, setSocketIOError] = useState<string>('');
  const [testMessage, setTestMessage] = useState<string>('');

  useEffect(() => {
    console.log('🔌 WebSocketDebug mounted, checking Socket.IO...');
    
    // Verificar si socket.io está disponible
    const checkSocket = async () => {
      try {
        const ioModule = await import('socket.io-client');
        console.log('✅ Socket.IO module imported:', !!ioModule.io);
        setSocketIOLoaded(true);
        setSocketIOError('');
      } catch (e) {
        console.error('❌ Failed to import Socket.IO:', e);
        setSocketIOLoaded(false);
        setSocketIOError(e.message || 'Import failed');
      }
    };
    
    checkSocket();
  }, []);

  const testConnection = () => {
    setTestMessage('Testing Socket.IO import...');
    checkWebSocketStatus();
  };

  return (
    <div className="p-4 border rounded bg-gray-100 text-black text-xs">
      <h3 className="font-bold mb-2">WebSocket Debug</h3>
      <div className="space-y-2">
        <div>Socket.IO: {socketIOLoaded ? '✅ Loaded' : '❌ Failed'}</div>
        {socketIOError && <div className="text-red-600">Error: {socketIOError}</div>}
        <button 
          onClick={testConnection}
          className="bg-blue-500 text-white px-2 py-1 rounded text-xs"
        >
          Test Import
        </button>
        {testMessage && <div className="text-xs mt-2">{testMessage}</div>}
      </div>
    </div>
  );
};