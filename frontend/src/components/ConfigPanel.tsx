import React, { useState } from 'react';
import { AgentConfig } from '../types';
import { X, Settings, Brain, Database, Cpu, Wrench, Save, RefreshCw } from 'lucide-react';
import { NumberInput } from './ui/NumberInput';
import { CustomSelect } from './ui/CustomSelect';
import { ConnectionStatus } from './ui/ConnectionStatus';
import { useOllamaConnection } from '../hooks/useOllamaConnection';

interface ConfigPanelProps {
  config: AgentConfig;
  onConfigChange: (config: AgentConfig) => void;
  onClose: () => void;
  isOpen: boolean;
}

export const ConfigPanel: React.FC<ConfigPanelProps> = ({
  config,
  onConfigChange,
  onClose,
  isOpen
}) => {
  const [activeTab, setActiveTab] = useState<'prompt' | 'memory' | 'ollama' | 'openrouter' | 'tools'>('prompt');
  const [tempConfig, setTempConfig] = useState<AgentConfig>(config);
  
  // Ollama connection hook
  const ollamaConnection = useOllamaConnection({
    endpoint: tempConfig.ollama.endpoint,
    enabled: tempConfig.ollama.enabled
  });

  const handleSave = () => {
    onConfigChange(tempConfig);
    onClose();
  };

  const handleReset = () => {
    setTempConfig(config);
  };

  const updateConfig = (path: string, value: any) => {
    const keys = path.split('.');
    const newConfig = { ...tempConfig };
    let current = newConfig as any;
    
    for (let i = 0; i < keys.length - 1; i++) {
      current = current[keys[i]];
    }
    current[keys[keys.length - 1]] = value;
    
    setTempConfig(newConfig);
  };

  const tabs = [
    { id: 'prompt', label: 'Prompt', icon: Brain },
    { id: 'memory', label: 'Memoria', icon: Database },
    { id: 'ollama', label: 'Ollama', icon: Cpu },
    { id: 'openrouter', label: 'OpenRouter', icon: Cpu },
    { id: 'tools', label: 'Herramientas', icon: Wrench }
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-[#383739] rounded-xl w-full max-w-4xl max-h-[90vh] overflow-hidden border border-[rgba(255,255,255,0.08)]">
        {/* Header */}
        <div className="p-6 border-b border-[rgba(255,255,255,0.08)] flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Settings className="w-6 h-6 text-[#DADADA]" />
            <h2 className="text-2xl font-bold text-[#DADADA]">Configuración del Agente</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-[rgba(255,255,255,0.08)] transition-colors"
          >
            <X className="w-5 h-5 text-[#ACACAC]" />
          </button>
        </div>

        <div className="flex h-[70vh]">
          {/* Sidebar */}
          <div className="w-64 bg-[#272728] border-r border-[rgba(255,255,255,0.08)] p-4">
            <div className="space-y-2">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-[rgba(255,255,255,0.08)] text-[#DADADA]'
                      : 'hover:bg-[rgba(255,255,255,0.06)] text-[#ACACAC]'
                  }`}
                >
                  <tab.icon className="w-5 h-5" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {activeTab === 'prompt' && (
              <div className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-[#DADADA] mb-3">Prompt del Sistema</h3>
                  <textarea
                    value={tempConfig.systemPrompt}
                    onChange={(e) => updateConfig('systemPrompt', e.target.value)}
                    className="w-full h-64 bg-[#2A2A2B] rounded-lg p-4 text-[#DADADA] border border-[rgba(255,255,255,0.08)] focus:outline-none focus:ring-2 focus:ring-[rgba(255,255,255,0.16)] resize-none"
                    placeholder="Ingresa el prompt del sistema para el agente..."
                  />
                  <p className="text-sm text-[#ACACAC] mt-2">
                    Define cómo se debe comportar el agente y qué personalidad debe tener.
                  </p>
                </div>
              </div>
            )}

            {activeTab === 'memory' && (
              <div className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-[#DADADA] mb-3">Configuración de Memoria</h3>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-[#DADADA]">Memoria habilitada</span>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={tempConfig.memory.enabled}
                          onChange={(e) => updateConfig('memory.enabled', e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-[#2A2A2B] peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[rgba(255,255,255,0.16)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>

                    <div>
                      <label className="block text-[#DADADA] mb-2">Máximo de mensajes</label>
                      <NumberInput
                        value={tempConfig.memory.maxMessages}
                        onChange={(value) => updateConfig('memory.maxMessages', value)}
                        min={1}
                        max={100}
                        step={1}
                        placeholder="Número de mensajes"
                      />
                    </div>

                    <div>
                      <label className="block text-[#DADADA] mb-2">Ventana de contexto</label>
                      <NumberInput
                        value={tempConfig.memory.contextWindow}
                        onChange={(value) => updateConfig('memory.contextWindow', value)}
                        min={1024}
                        max={32768}
                        step={1024}
                        placeholder="Tamaño de contexto"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'ollama' && (
              <div className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-[#DADADA] mb-3">Configuración de Ollama</h3>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-[#DADADA]">Ollama habilitado</span>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={tempConfig.ollama.enabled}
                          onChange={(e) => updateConfig('ollama.enabled', e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-[#2A2A2B] peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[rgba(255,255,255,0.16)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>

                    <div>
                      <label className="block text-[#DADADA] mb-2">Modelo</label>
                      <select
                        value={tempConfig.ollama.model}
                        onChange={(e) => updateConfig('ollama.model', e.target.value)}
                        className="w-full bg-[#2A2A2B] rounded-lg p-3 text-[#DADADA] border border-[rgba(255,255,255,0.08)] focus:outline-none focus:ring-2 focus:ring-[rgba(255,255,255,0.16)]"
                      >
                        <option value="llama3.2">Llama 3.2</option>
                        <option value="mistral">Mistral</option>
                        <option value="codellama">CodeLlama</option>
                        <option value="phi">Phi</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[#DADADA] mb-2">Temperatura: {tempConfig.ollama.temperature}</label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={tempConfig.ollama.temperature}
                        onChange={(e) => updateConfig('ollama.temperature', parseFloat(e.target.value))}
                        className="w-full h-2 bg-[#2A2A2B] rounded-lg appearance-none cursor-pointer"
                      />
                    </div>

                    <div>
                      <label className="block text-[#DADADA] mb-2">Máximo de tokens</label>
                      <input
                        type="number"
                        value={tempConfig.ollama.maxTokens}
                        onChange={(e) => updateConfig('ollama.maxTokens', parseInt(e.target.value))}
                        className="w-full bg-[#2A2A2B] rounded-lg p-3 text-[#DADADA] border border-[rgba(255,255,255,0.08)] focus:outline-none focus:ring-2 focus:ring-[rgba(255,255,255,0.16)]"
                        min="100"
                        max="4096"
                      />
                    </div>

                    <div>
                      <label className="block text-[#DADADA] mb-2">Endpoint</label>
                      <input
                        type="text"
                        value={tempConfig.ollama.endpoint}
                        onChange={(e) => updateConfig('ollama.endpoint', e.target.value)}
                        className="w-full bg-[#2A2A2B] rounded-lg p-3 text-[#DADADA] border border-[rgba(255,255,255,0.08)] focus:outline-none focus:ring-2 focus:ring-[rgba(255,255,255,0.16)]"
                        placeholder="http://localhost:11434"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'openrouter' && (
              <div className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-[#DADADA] mb-3">Configuración de OpenRouter</h3>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-[#DADADA]">OpenRouter habilitado</span>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={tempConfig.openrouter.enabled}
                          onChange={(e) => updateConfig('openrouter.enabled', e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-[#2A2A2B] peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[rgba(255,255,255,0.16)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>

                    <div>
                      <label className="block text-[#DADADA] mb-2">Modelo</label>
                      <select
                        value={tempConfig.openrouter.model}
                        onChange={(e) => updateConfig('openrouter.model', e.target.value)}
                        className="w-full bg-[#2A2A2B] rounded-lg p-3 text-[#DADADA] border border-[rgba(255,255,255,0.08)] focus:outline-none focus:ring-2 focus:ring-[rgba(255,255,255,0.16)]"
                      >
                        <option value="mistral-7b-instruct">Mistral 7B Instruct</option>
                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                        <option value="gpt-4">GPT-4</option>
                        <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                        <option value="llama-2-70b-chat">Llama 2 70B Chat</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[#DADADA] mb-2">API Key</label>
                      <input
                        type="password"
                        value={tempConfig.openrouter.apiKey}
                        onChange={(e) => updateConfig('openrouter.apiKey', e.target.value)}
                        className="w-full bg-[#2A2A2B] rounded-lg p-3 text-[#DADADA] border border-[rgba(255,255,255,0.08)] focus:outline-none focus:ring-2 focus:ring-[rgba(255,255,255,0.16)]"
                        placeholder="Ingresa tu API Key de OpenRouter"
                      />
                    </div>

                    <div>
                      <label className="block text-[#DADADA] mb-2">Temperatura: {tempConfig.openrouter.temperature}</label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={tempConfig.openrouter.temperature}
                        onChange={(e) => updateConfig('openrouter.temperature', parseFloat(e.target.value))}
                        className="w-full h-2 bg-[#2A2A2B] rounded-lg appearance-none cursor-pointer"
                      />
                    </div>

                    <div>
                      <label className="block text-[#DADADA] mb-2">Máximo de tokens</label>
                      <input
                        type="number"
                        value={tempConfig.openrouter.maxTokens}
                        onChange={(e) => updateConfig('openrouter.maxTokens', parseInt(e.target.value))}
                        className="w-full bg-[#2A2A2B] rounded-lg p-3 text-[#DADADA] border border-[rgba(255,255,255,0.08)] focus:outline-none focus:ring-2 focus:ring-[rgba(255,255,255,0.16)]"
                        min="100"
                        max="4096"
                      />
                    </div>

                    <div>
                      <label className="block text-[#DADADA] mb-2">Endpoint</label>
                      <input
                        type="text"
                        value={tempConfig.openrouter.endpoint}
                        onChange={(e) => updateConfig('openrouter.endpoint', e.target.value)}
                        className="w-full bg-[#2A2A2B] rounded-lg p-3 text-[#DADADA] border border-[rgba(255,255,255,0.08)] focus:outline-none focus:ring-2 focus:ring-[rgba(255,255,255,0.16)]"
                        placeholder="https://openrouter.ai/api/v1"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'tools' && (
              <div className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-[#DADADA] mb-3">Configuración de Herramientas</h3>
                  
                  <div className="space-y-6">
                    {/* Shell Tool */}
                    <div className="border border-[rgba(255,255,255,0.08)] rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-[#DADADA] font-medium">Shell</h4>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={tempConfig.tools.shell.enabled}
                            onChange={(e) => updateConfig('tools.shell.enabled', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-[#2A2A2B] peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[rgba(255,255,255,0.16)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                      <div className="space-y-3">
                        <div>
                          <label className="block text-[#ACACAC] mb-2">Timeout (segundos)</label>
                          <input
                            type="number"
                            value={tempConfig.tools.shell.timeout}
                            onChange={(e) => updateConfig('tools.shell.timeout', parseInt(e.target.value))}
                            className="w-full bg-[#2A2A2B] rounded-lg p-3 text-[#DADADA] border border-[rgba(255,255,255,0.08)] focus:outline-none focus:ring-2 focus:ring-[rgba(255,255,255,0.16)]"
                            min="5"
                            max="300"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Web Search Tool */}
                    <div className="border border-[rgba(255,255,255,0.08)] rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-[#DADADA] font-medium">Búsqueda Web</h4>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={tempConfig.tools.webSearch.enabled}
                            onChange={(e) => updateConfig('tools.webSearch.enabled', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-[#2A2A2B] peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[rgba(255,255,255,0.16)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                      <div className="space-y-3">
                        <div>
                          <label className="block text-[#ACACAC] mb-2">Máximo de resultados</label>
                          <input
                            type="number"
                            value={tempConfig.tools.webSearch.maxResults}
                            onChange={(e) => updateConfig('tools.webSearch.maxResults', parseInt(e.target.value))}
                            className="w-full bg-[#2A2A2B] rounded-lg p-3 text-[#DADADA] border border-[rgba(255,255,255,0.08)] focus:outline-none focus:ring-2 focus:ring-[rgba(255,255,255,0.16)]"
                            min="1"
                            max="20"
                          />
                        </div>
                        <div>
                          <label className="block text-[#ACACAC] mb-2">Timeout (segundos)</label>
                          <input
                            type="number"
                            value={tempConfig.tools.webSearch.timeout}
                            onChange={(e) => updateConfig('tools.webSearch.timeout', parseInt(e.target.value))}
                            className="w-full bg-[#2A2A2B] rounded-lg p-3 text-[#DADADA] border border-[rgba(255,255,255,0.08)] focus:outline-none focus:ring-2 focus:ring-[rgba(255,255,255,0.16)]"
                            min="5"
                            max="60"
                          />
                        </div>
                      </div>
                    </div>

                    {/* File Manager Tool */}
                    <div className="border border-[rgba(255,255,255,0.08)] rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-[#DADADA] font-medium">Gestor de Archivos</h4>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={tempConfig.tools.fileManager.enabled}
                            onChange={(e) => updateConfig('tools.fileManager.enabled', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-[#2A2A2B] peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[rgba(255,255,255,0.16)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                      <div className="space-y-3">
                        <div>
                          <label className="block text-[#ACACAC] mb-2">Tamaño máximo de archivo (MB)</label>
                          <input
                            type="number"
                            value={tempConfig.tools.fileManager.maxFileSize}
                            onChange={(e) => updateConfig('tools.fileManager.maxFileSize', parseInt(e.target.value))}
                            className="w-full bg-[#2A2A2B] rounded-lg p-3 text-[#DADADA] border border-[rgba(255,255,255,0.08)] focus:outline-none focus:ring-2 focus:ring-[rgba(255,255,255,0.16)]"
                            min="1"
                            max="100"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-[rgba(255,255,255,0.08)] flex justify-between">
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-[rgba(255,255,255,0.08)] hover:bg-[rgba(255,255,255,0.06)] transition-colors text-[#ACACAC]"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Reiniciar</span>
          </button>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg border border-[rgba(255,255,255,0.08)] hover:bg-[rgba(255,255,255,0.06)] transition-colors text-[#ACACAC]"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 transition-colors text-white"
            >
              <Save className="w-4 h-4" />
              <span>Guardar</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};