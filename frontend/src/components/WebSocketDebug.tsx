import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

export const WebSocketDebug: React.FC = () => {
  const { socket, isConnected, connectionType } = useWebSocket();
  const [testMessage, setTestMessage] = useState<string>('');

  const testConnection = () => {
    if (socket && isConnected) {
      socket.emit('test_connection', { message: 'Hello from frontend!' });
      setTestMessage('Test message sent');
    } else {
      setTestMessage('Socket not connected');
    }
  };

  useEffect(() => {
    console.log('🔌 WebSocket Debug - Connection Status:', {
      socket: !!socket,
      isConnected,
      connectionType
    });
  }, [socket, isConnected, connectionType]);

  return (
    <div className="p-4 border rounded bg-gray-100 text-black">
      <h3 className="font-bold mb-2">WebSocket Debug</h3>
      <div className="space-y-2 text-sm">
        <div>Socket: {socket ? '✅ Loaded' : '❌ Not loaded'}</div>
        <div>Connected: {isConnected ? '✅ Yes' : '❌ No'}</div>
        <div>Type: {connectionType}</div>
        <button 
          onClick={testConnection}
          className="bg-blue-500 text-white px-2 py-1 rounded text-xs"
        >
          Test Connection
        </button>
        {testMessage && <div className="text-xs">{testMessage}</div>}
      </div>
    </div>
  );
};