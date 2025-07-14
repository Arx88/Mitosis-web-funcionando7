import React, { useState, useEffect, useRef } from 'react';
import { 
  Bell, BellOff, Settings, X, Check, AlertTriangle, 
  AlertCircle, Info, XCircle, Volume2, VolumeX,
  Mail, MessageSquare, Smartphone, Monitor
} from 'lucide-react';

interface AlertRule {
  id: string;
  name: string;
  metric: string;
  condition: 'greater_than' | 'less_than' | 'equals';
  threshold: number;
  level: 'info' | 'warning' | 'error' | 'critical';
  enabled: boolean;
  channels: string[];
  cooldown: number; // minutes
  message_template: string;
}

interface NotificationChannel {
  id: string;
  name: string;
  type: 'email' | 'webhook' | 'browser' | 'sound';
  enabled: boolean;
  config: Record<string, any>;
}

interface Alert {
  id: string;
  title: string;
  message: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  timestamp: number;
  source: string;
  acknowledged: boolean;
  resolved: boolean;
  rule_id?: string;
}

interface AlertsNotificationSystemProps {
  websocket?: WebSocket;
  onAlertUpdate?: (alerts: Alert[]) => void;
}

const ALERT_ICONS = {
  info: Info,
  warning: AlertTriangle,
  error: AlertCircle,
  critical: XCircle
};

const ALERT_COLORS = {
  info: 'bg-blue-100 border-blue-500 text-blue-800',
  warning: 'bg-yellow-100 border-yellow-500 text-yellow-800',
  error: 'bg-red-100 border-red-500 text-red-800',
  critical: 'bg-red-200 border-red-600 text-red-900'
};

const CHANNEL_ICONS = {
  email: Mail,
  webhook: MessageSquare,
  browser: Monitor,
  sound: Volume2
};

export const AlertsNotificationSystem: React.FC<AlertsNotificationSystemProps> = ({
  websocket,
  onAlertUpdate
}) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [alertRules, setAlertRules] = useState<AlertRule[]>([]);
  const [notificationChannels, setNotificationChannels] = useState<NotificationChannel[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [browserNotificationsEnabled, setBrowserNotificationsEnabled] = useState(false);
  const [selectedTab, setSelectedTab] = useState<'alerts' | 'rules' | 'channels'>('alerts');
  const [newRule, setNewRule] = useState<Partial<AlertRule>>({});
  const [newChannel, setNewChannel] = useState<Partial<NotificationChannel>>({});
  
  const audioRef = useRef<HTMLAudioElement>();

  useEffect(() => {
    // Solicitar permisos para notificaciones del navegador
    if ('Notification' in window) {
      Notification.requestPermission().then(permission => {
        setBrowserNotificationsEnabled(permission === 'granted');
      });
    }

    // Cargar configuración inicial
    loadAlertRules();
    loadNotificationChannels();
    loadAlerts();

    // Configurar WebSocket
    if (websocket) {
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'new_alert') {
          handleNewAlert(data.payload);
        } else if (data.type === 'alert_update') {
          updateAlert(data.payload);
        }
      };
    }
  }, [websocket]);

  useEffect(() => {
    if (onAlertUpdate) {
      onAlertUpdate(alerts);
    }
  }, [alerts, onAlertUpdate]);

  const loadAlerts = async () => {
    try {
      const response = await fetch('/api/alerts');
      const data = await response.json();
      setAlerts(data);
    } catch (error) {
      console.error('Error loading alerts:', error);
    }
  };

  const loadAlertRules = async () => {
    try {
      const response = await fetch('/api/alert-rules');
      const data = await response.json();
      setAlertRules(data);
    } catch (error) {
      console.error('Error loading alert rules:', error);
    }
  };

  const loadNotificationChannels = async () => {
    try {
      const response = await fetch('/api/notification-channels');
      const data = await response.json();
      setNotificationChannels(data);
    } catch (error) {
      console.error('Error loading notification channels:', error);
    }
  };

  const handleNewAlert = (alert: Alert) => {
    setAlerts(prev => [alert, ...prev]);
    
    // Reproducir sonido si está habilitado
    if (soundEnabled && alert.level !== 'info') {
      playAlertSound(alert.level);
    }
    
    // Mostrar notificación del navegador
    if (browserNotificationsEnabled) {
      showBrowserNotification(alert);
    }
  };

  const updateAlert = (updatedAlert: Alert) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === updatedAlert.id ? updatedAlert : alert
    ));
  };

  const playAlertSound = (level: string) => {
    if (audioRef.current) {
      // Diferentes tonos para diferentes niveles
      const frequencies = {
        warning: 800,
        error: 600,
        critical: 400
      };
      
      // Crear tono usando Web Audio API (simplificado)
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.value = frequencies[level as keyof typeof frequencies] || 700;
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    }
  };

  const showBrowserNotification = (alert: Alert) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(alert.title, {
        body: alert.message,
        icon: '/favicon.ico',
        tag: alert.id
      });
    }
  };

  const acknowledgeAlert = async (alertId: string) => {
    try {
      await fetch(`/api/alerts/${alertId}/acknowledge`, { method: 'POST' });
      setAlerts(prev => prev.map(alert => 
        alert.id === alertId ? { ...alert, acknowledged: true } : alert
      ));
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  const resolveAlert = async (alertId: string) => {
    try {
      await fetch(`/api/alerts/${alertId}/resolve`, { method: 'POST' });
      setAlerts(prev => prev.map(alert => 
        alert.id === alertId ? { ...alert, resolved: true } : alert
      ));
    } catch (error) {
      console.error('Error resolving alert:', error);
    }
  };

  const createAlertRule = async () => {
    try {
      const response = await fetch('/api/alert-rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newRule)
      });
      
      if (response.ok) {
        const rule = await response.json();
        setAlertRules(prev => [...prev, rule]);
        setNewRule({});
      }
    } catch (error) {
      console.error('Error creating alert rule:', error);
    }
  };

  const updateAlertRule = async (ruleId: string, updates: Partial<AlertRule>) => {
    try {
      const response = await fetch(`/api/alert-rules/${ruleId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      
      if (response.ok) {
        const updatedRule = await response.json();
        setAlertRules(prev => prev.map(rule => 
          rule.id === ruleId ? updatedRule : rule
        ));
      }
    } catch (error) {
      console.error('Error updating alert rule:', error);
    }
  };

  const createNotificationChannel = async () => {
    try {
      const response = await fetch('/api/notification-channels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newChannel)
      });
      
      if (response.ok) {
        const channel = await response.json();
        setNotificationChannels(prev => [...prev, channel]);
        setNewChannel({});
      }
    } catch (error) {
      console.error('Error creating notification channel:', error);
    }
  };

  const activeAlerts = alerts.filter(alert => !alert.resolved);
  const criticalAlerts = activeAlerts.filter(alert => alert.level === 'critical');

  return (
    <div className="relative">
      {/* Alert Bell Icon */}
      <div className="relative">
        <button
          onClick={() => setShowSettings(!showSettings)}
          className={`p-2 rounded-full ${
            criticalAlerts.length > 0 
              ? 'bg-red-100 text-red-600 animate-pulse' 
              : activeAlerts.length > 0 
                ? 'bg-yellow-100 text-yellow-600' 
                : 'bg-gray-100 text-gray-600'
          }`}
        >
          {soundEnabled ? <Bell className="w-6 h-6" /> : <BellOff className="w-6 h-6" />}
        </button>
        
        {activeAlerts.length > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {activeAlerts.length > 99 ? '99+' : activeAlerts.length}
          </span>
        )}
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="absolute right-0 top-12 w-96 bg-white rounded-lg shadow-lg border z-50">
          <div className="p-4 border-b">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">Alertas y Notificaciones</h3>
              <button
                onClick={() => setShowSettings(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            {/* Quick Settings */}
            <div className="flex space-x-4 mt-3">
              <button
                onClick={() => setSoundEnabled(!soundEnabled)}
                className={`flex items-center space-x-2 px-3 py-1 rounded ${
                  soundEnabled ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
                }`}
              >
                {soundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
                <span className="text-sm">Sonido</span>
              </button>
              
              <button
                onClick={() => setBrowserNotificationsEnabled(!browserNotificationsEnabled)}
                className={`flex items-center space-x-2 px-3 py-1 rounded ${
                  browserNotificationsEnabled ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
                }`}
              >
                <Monitor className="w-4 h-4" />
                <span className="text-sm">Navegador</span>
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b">
            {(['alerts', 'rules', 'channels'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setSelectedTab(tab)}
                className={`flex-1 px-4 py-2 text-sm font-medium ${
                  selectedTab === tab
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab === 'alerts' && 'Alertas'}
                {tab === 'rules' && 'Reglas'}
                {tab === 'channels' && 'Canales'}
              </button>
            ))}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {/* Alerts Tab */}
            {selectedTab === 'alerts' && (
              <div className="p-4">
                {activeAlerts.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Check className="w-8 h-8 mx-auto mb-2" />
                    <p>No hay alertas activas</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {activeAlerts.slice(0, 10).map(alert => {
                      const IconComponent = ALERT_ICONS[alert.level];
                      return (
                        <div
                          key={alert.id}
                          className={`p-3 rounded-lg border-l-4 ${ALERT_COLORS[alert.level]}`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex items-start space-x-2">
                              <IconComponent className="w-4 h-4 mt-0.5" />
                              <div>
                                <p className="font-medium text-sm">{alert.title}</p>
                                <p className="text-xs opacity-75">{alert.message}</p>
                                <p className="text-xs opacity-60 mt-1">
                                  {new Date(alert.timestamp * 1000).toLocaleString()}
                                </p>
                              </div>
                            </div>
                            
                            <div className="flex space-x-1">
                              {!alert.acknowledged && (
                                <button
                                  onClick={() => acknowledgeAlert(alert.id)}
                                  className="p-1 hover:bg-white hover:bg-opacity-50 rounded"
                                  title="Reconocer"
                                >
                                  <Check className="w-3 h-3" />
                                </button>
                              )}
                              
                              <button
                                onClick={() => resolveAlert(alert.id)}
                                className="p-1 hover:bg-white hover:bg-opacity-50 rounded"
                                title="Resolver"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* Rules Tab */}
            {selectedTab === 'rules' && (
              <div className="p-4">
                <div className="space-y-3 mb-4">
                  {alertRules.map(rule => (
                    <div key={rule.id} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-sm">{rule.name}</p>
                          <p className="text-xs text-gray-600">
                            {rule.metric} {rule.condition.replace('_', ' ')} {rule.threshold}
                          </p>
                        </div>
                        
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={rule.enabled}
                            onChange={(e) => updateAlertRule(rule.id, { enabled: e.target.checked })}
                            className="mr-2"
                          />
                          <span className="text-sm">Activa</span>
                        </label>
                      </div>
                    </div>
                  ))}
                </div>

                {/* New Rule Form */}
                <div className="border-t pt-4">
                  <h4 className="font-medium text-sm mb-3">Nueva Regla</h4>
                  <div className="space-y-2">
                    <input
                      type="text"
                      placeholder="Nombre de la regla"
                      value={newRule.name || ''}
                      onChange={(e) => setNewRule(prev => ({ ...prev, name: e.target.value }))}
                      className="w-full px-3 py-2 border rounded text-sm"
                    />
                    
                    <div className="grid grid-cols-2 gap-2">
                      <select
                        value={newRule.metric || ''}
                        onChange={(e) => setNewRule(prev => ({ ...prev, metric: e.target.value }))}
                        className="px-3 py-2 border rounded text-sm"
                      >
                        <option value="">Métrica</option>
                        <option value="cpu_usage">CPU</option>
                        <option value="memory_usage">Memoria</option>
                        <option value="disk_usage">Disco</option>
                        <option value="error_count">Errores</option>
                      </select>
                      
                      <select
                        value={newRule.condition || ''}
                        onChange={(e) => setNewRule(prev => ({ ...prev, condition: e.target.value as any }))}
                        className="px-3 py-2 border rounded text-sm"
                      >
                        <option value="">Condición</option>
                        <option value="greater_than">Mayor que</option>
                        <option value="less_than">Menor que</option>
                        <option value="equals">Igual a</option>
                      </select>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="number"
                        placeholder="Umbral"
                        value={newRule.threshold || ''}
                        onChange={(e) => setNewRule(prev => ({ ...prev, threshold: Number(e.target.value) }))}
                        className="px-3 py-2 border rounded text-sm"
                      />
                      
                      <select
                        value={newRule.level || ''}
                        onChange={(e) => setNewRule(prev => ({ ...prev, level: e.target.value as any }))}
                        className="px-3 py-2 border rounded text-sm"
                      >
                        <option value="">Nivel</option>
                        <option value="info">Info</option>
                        <option value="warning">Advertencia</option>
                        <option value="error">Error</option>
                        <option value="critical">Crítico</option>
                      </select>
                    </div>
                    
                    <button
                      onClick={createAlertRule}
                      disabled={!newRule.name || !newRule.metric || !newRule.condition}
                      className="w-full px-3 py-2 bg-blue-600 text-white rounded text-sm disabled:bg-gray-300"
                    >
                      Crear Regla
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Channels Tab */}
            {selectedTab === 'channels' && (
              <div className="p-4">
                <div className="space-y-3 mb-4">
                  {notificationChannels.map(channel => {
                    const IconComponent = CHANNEL_ICONS[channel.type];
                    return (
                      <div key={channel.id} className="p-3 border rounded-lg">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <IconComponent className="w-4 h-4" />
                            <div>
                              <p className="font-medium text-sm">{channel.name}</p>
                              <p className="text-xs text-gray-600">{channel.type}</p>
                            </div>
                          </div>
                          
                          <label className="flex items-center">
                            <input
                              type="checkbox"
                              checked={channel.enabled}
                              onChange={(e) => {
                                // Update channel enabled status
                              }}
                              className="mr-2"
                            />
                            <span className="text-sm">Activo</span>
                          </label>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* New Channel Form */}
                <div className="border-t pt-4">
                  <h4 className="font-medium text-sm mb-3">Nuevo Canal</h4>
                  <div className="space-y-2">
                    <input
                      type="text"
                      placeholder="Nombre del canal"
                      value={newChannel.name || ''}
                      onChange={(e) => setNewChannel(prev => ({ ...prev, name: e.target.value }))}
                      className="w-full px-3 py-2 border rounded text-sm"
                    />
                    
                    <select
                      value={newChannel.type || ''}
                      onChange={(e) => setNewChannel(prev => ({ ...prev, type: e.target.value as any }))}
                      className="w-full px-3 py-2 border rounded text-sm"
                    >
                      <option value="">Tipo de canal</option>
                      <option value="email">Email</option>
                      <option value="webhook">Webhook</option>
                      <option value="browser">Navegador</option>
                      <option value="sound">Sonido</option>
                    </select>
                    
                    <button
                      onClick={createNotificationChannel}
                      disabled={!newChannel.name || !newChannel.type}
                      className="w-full px-3 py-2 bg-blue-600 text-white rounded text-sm disabled:bg-gray-300"
                    >
                      Crear Canal
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Hidden audio element for sound notifications */}
      <audio ref={audioRef} preload="auto" />
    </div>
  );
};

export default AlertsNotificationSystem;

