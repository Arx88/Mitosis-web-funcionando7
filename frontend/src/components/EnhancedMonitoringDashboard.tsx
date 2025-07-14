import React, { useState, useEffect, useRef } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import { 
  AlertTriangle, Activity, Cpu, HardDrive, Wifi, Clock, 
  TrendingUp, TrendingDown, AlertCircle, CheckCircle, XCircle,
  Settings, Filter, Download, RefreshCw, Maximize2
} from 'lucide-react';

interface Alert {
  id: string;
  title: string;
  message: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  timestamp: number;
  source: string;
  acknowledged: boolean;
  resolved: boolean;
}

interface Metric {
  name: string;
  current: number;
  average: number;
  min: number;
  max: number;
  unit: string;
}

interface DashboardData {
  timestamp: number;
  alerts: {
    active_count: number;
    by_level: Record<string, number>;
    recent: Alert[];
  };
  metrics: Record<string, Metric>;
  errors: {
    recent_count: number;
    by_type: Record<string, number>;
  };
  performance: {
    average_by_component: Record<string, number>;
    total_profiles: number;
  };
  system_health: {
    monitoring_active: boolean;
    queue_size: number;
    total_metrics: number;
  };
}

interface EnhancedMonitoringDashboardProps {
  websocket?: WebSocket;
  refreshInterval?: number;
}

const ALERT_COLORS = {
  info: '#3b82f6',
  warning: '#f59e0b',
  error: '#ef4444',
  critical: '#dc2626'
};

const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export const EnhancedMonitoringDashboard: React.FC<EnhancedMonitoringDashboardProps> = ({
  websocket,
  refreshInterval = 5000
}) => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [historicalData, setHistoricalData] = useState<any[]>([]);
  const [selectedTimeRange, setSelectedTimeRange] = useState('1h');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['cpu_usage', 'memory_usage']);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [alertFilter, setAlertFilter] = useState<string>('all');
  const intervalRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (autoRefresh) {
      fetchDashboardData();
      intervalRef.current = setInterval(fetchDashboardData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh, refreshInterval]);

  useEffect(() => {
    if (websocket) {
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'monitoring_update') {
          setDashboardData(data.payload);
          updateHistoricalData(data.payload);
        }
      };
    }
  }, [websocket]);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/monitoring/dashboard');
      const data = await response.json();
      setDashboardData(data);
      updateHistoricalData(data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const updateHistoricalData = (data: DashboardData) => {
    setHistoricalData(prev => {
      const newEntry = {
        timestamp: data.timestamp,
        cpu_usage: data.metrics.cpu_usage?.current || 0,
        memory_usage: data.metrics.memory_usage?.current || 0,
        disk_usage: data.metrics.disk_usage?.current || 0,
        active_alerts: data.alerts.active_count,
        error_count: data.errors.recent_count
      };

      const updated = [...prev, newEntry];
      // Mantener solo los últimos 100 puntos
      return updated.slice(-100);
    });
  };

  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'critical':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      default:
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  const getMetricTrend = (metric: Metric) => {
    const trend = metric.current - metric.average;
    if (Math.abs(trend) < 0.1) return null;
    return trend > 0 ? 
      <TrendingUp className="w-4 h-4 text-red-500" /> : 
      <TrendingDown className="w-4 h-4 text-green-500" />;
  };

  const filteredAlerts = dashboardData?.alerts.recent.filter(alert => {
    if (alertFilter === 'all') return true;
    return alert.level === alertFilter;
  }) || [];

  if (!dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Cargando dashboard...</span>
      </div>
    );
  }

  return (
    <div className={`p-6 bg-gray-50 min-h-screen ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard de Monitoreo</h1>
          <p className="text-gray-600">
            Última actualización: {formatTimestamp(dashboardData.timestamp)}
          </p>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded-lg flex items-center space-x-2 ${
              autoRefresh ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            <span>Auto-refresh</span>
          </button>
          
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg flex items-center space-x-2"
          >
            <Maximize2 className="w-4 h-4" />
            <span>Pantalla completa</span>
          </button>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Alertas Activas</p>
              <p className="text-2xl font-bold text-gray-900">{dashboardData.alerts.active_count}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-yellow-500" />
          </div>
          <div className="mt-2 flex space-x-2">
            {Object.entries(dashboardData.alerts.by_level).map(([level, count]) => (
              <span
                key={level}
                className="px-2 py-1 text-xs rounded-full"
                style={{ 
                  backgroundColor: ALERT_COLORS[level as keyof typeof ALERT_COLORS] + '20',
                  color: ALERT_COLORS[level as keyof typeof ALERT_COLORS]
                }}
              >
                {level}: {count}
              </span>
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">CPU</p>
              <p className="text-2xl font-bold text-gray-900">
                {dashboardData.metrics.cpu_usage?.current.toFixed(1) || 0}%
              </p>
            </div>
            <Cpu className="w-8 h-8 text-blue-500" />
          </div>
          <div className="mt-2 flex items-center space-x-2">
            {getMetricTrend(dashboardData.metrics.cpu_usage)}
            <span className="text-sm text-gray-500">
              Promedio: {dashboardData.metrics.cpu_usage?.average.toFixed(1) || 0}%
            </span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Memoria</p>
              <p className="text-2xl font-bold text-gray-900">
                {dashboardData.metrics.memory_usage?.current.toFixed(1) || 0}%
              </p>
            </div>
            <Activity className="w-8 h-8 text-green-500" />
          </div>
          <div className="mt-2 flex items-center space-x-2">
            {getMetricTrend(dashboardData.metrics.memory_usage)}
            <span className="text-sm text-gray-500">
              Promedio: {dashboardData.metrics.memory_usage?.average.toFixed(1) || 0}%
            </span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Errores Recientes</p>
              <p className="text-2xl font-bold text-gray-900">{dashboardData.errors.recent_count}</p>
            </div>
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
          <div className="mt-2">
            <span className="text-sm text-gray-500">
              Última hora
            </span>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* System Metrics Chart */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Métricas del Sistema</h3>
            <select
              value={selectedTimeRange}
              onChange={(e) => setSelectedTimeRange(e.target.value)}
              className="px-3 py-1 border rounded-md text-sm"
            >
              <option value="1h">Última hora</option>
              <option value="6h">Últimas 6 horas</option>
              <option value="24h">Últimas 24 horas</option>
            </select>
          </div>
          
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={(value) => new Date(value * 1000).toLocaleTimeString()}
              />
              <YAxis />
              <Tooltip 
                labelFormatter={(value) => new Date(value * 1000).toLocaleString()}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="cpu_usage" 
                stroke="#3b82f6" 
                name="CPU %" 
                strokeWidth={2}
              />
              <Line 
                type="monotone" 
                dataKey="memory_usage" 
                stroke="#10b981" 
                name="Memoria %" 
                strokeWidth={2}
              />
              <Line 
                type="monotone" 
                dataKey="disk_usage" 
                stroke="#f59e0b" 
                name="Disco %" 
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Performance by Component */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Rendimiento por Componente</h3>
          
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={Object.entries(dashboardData.performance.average_by_component).map(([component, duration]) => ({
              component,
              duration: Number(duration.toFixed(3))
            }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="component" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value}s`, 'Duración promedio']} />
              <Bar dataKey="duration" fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Alerts and Errors Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Alerts */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Alertas Recientes</h3>
            <select
              value={alertFilter}
              onChange={(e) => setAlertFilter(e.target.value)}
              className="px-3 py-1 border rounded-md text-sm"
            >
              <option value="all">Todas</option>
              <option value="critical">Críticas</option>
              <option value="error">Errores</option>
              <option value="warning">Advertencias</option>
              <option value="info">Información</option>
            </select>
          </div>
          
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {filteredAlerts.map((alert) => (
              <div
                key={alert.id}
                className="flex items-start space-x-3 p-3 rounded-lg border-l-4"
                style={{ borderLeftColor: ALERT_COLORS[alert.level] }}
              >
                {getAlertIcon(alert.level)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">{alert.title}</p>
                  <p className="text-sm text-gray-600">{alert.message}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatTimestamp(alert.timestamp)} - {alert.source}
                  </p>
                </div>
              </div>
            ))}
            
            {filteredAlerts.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                No hay alertas que mostrar
              </div>
            )}
          </div>
        </div>

        {/* Error Distribution */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Distribución de Errores</h3>
          
          {Object.keys(dashboardData.errors.by_type).length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={Object.entries(dashboardData.errors.by_type).map(([type, count], index) => ({
                    name: type,
                    value: count,
                    fill: CHART_COLORS[index % CHART_COLORS.length]
                  }))}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-500">
              <CheckCircle className="w-8 h-8 mr-2" />
              <span>No hay errores recientes</span>
            </div>
          )}
        </div>
      </div>

      {/* System Health Footer */}
      <div className="mt-6 bg-white p-4 rounded-lg shadow-sm border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                dashboardData.system_health.monitoring_active ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <span className="text-sm text-gray-600">
                Monitoreo {dashboardData.system_health.monitoring_active ? 'Activo' : 'Inactivo'}
              </span>
            </div>
            
            <span className="text-sm text-gray-600">
              Cola de eventos: {dashboardData.system_health.queue_size}
            </span>
            
            <span className="text-sm text-gray-600">
              Total métricas: {dashboardData.system_health.total_metrics}
            </span>
          </div>
          
          <div className="text-sm text-gray-500">
            Perfiles de rendimiento: {dashboardData.performance.total_profiles}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedMonitoringDashboard;

