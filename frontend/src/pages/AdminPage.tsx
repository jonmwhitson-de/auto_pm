import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Settings, Cpu, Plug, Loader2, Eye, EyeOff,
  ChevronDown, ChevronRight, AlertCircle
} from 'lucide-react';
import {
  getLLMConfig, updateLLMConfig,
  getTools, updateTool,
  getIntegrations, updateIntegration, testIntegration,
  type MCPTool, type Integration
} from '../api/client';
import clsx from 'clsx';

type Tab = 'llm' | 'tools' | 'integrations';

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<Tab>('llm');

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Admin Settings</h1>

      <div className="flex gap-2 mb-6 border-b border-gray-200">
        <TabButton
          active={activeTab === 'llm'}
          onClick={() => setActiveTab('llm')}
          icon={<Cpu className="w-4 h-4" />}
          label="LLM Configuration"
        />
        <TabButton
          active={activeTab === 'tools'}
          onClick={() => setActiveTab('tools')}
          icon={<Settings className="w-4 h-4" />}
          label="MCP Tools"
        />
        <TabButton
          active={activeTab === 'integrations'}
          onClick={() => setActiveTab('integrations')}
          icon={<Plug className="w-4 h-4" />}
          label="Integrations"
        />
      </div>

      {activeTab === 'llm' && <LLMConfigSection />}
      {activeTab === 'tools' && <ToolsSection />}
      {activeTab === 'integrations' && <IntegrationsSection />}
    </div>
  );
}

function TabButton({ active, onClick, icon, label }: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        'flex items-center gap-2 px-4 py-2 font-medium border-b-2 -mb-px transition',
        active
          ? 'border-indigo-600 text-indigo-600'
          : 'border-transparent text-gray-600 hover:text-gray-900'
      )}
    >
      {icon}
      {label}
    </button>
  );
}

function LLMConfigSection() {
  const queryClient = useQueryClient();
  const [showApiKey, setShowApiKey] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [endpoint, setEndpoint] = useState('');
  const [deployment, setDeployment] = useState('');

  const { data: config, isLoading } = useQuery({
    queryKey: ['llm-config'],
    queryFn: getLLMConfig,
  });

  // Update local state when config loads
  if (config && !endpoint && config.azure_endpoint) {
    setEndpoint(config.azure_endpoint);
  }
  if (config && !deployment && config.azure_deployment) {
    setDeployment(config.azure_deployment);
  }

  const updateMutation = useMutation({
    mutationFn: updateLLMConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-config'] });
      setApiKey('');
    },
  });

  if (isLoading) {
    return <LoadingSpinner />;
  }

  const handleProviderChange = (provider: string) => {
    updateMutation.mutate({ provider });
  };

  const handleSaveAzureConfig = () => {
    const data: Parameters<typeof updateLLMConfig>[0] = {};
    if (endpoint) data.azure_endpoint = endpoint;
    if (deployment) data.azure_deployment = deployment;
    if (apiKey) data.azure_api_key = apiKey;
    updateMutation.mutate(data);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">LLM Provider</h3>

        <div className="space-y-3">
          <label className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
            <input
              type="radio"
              name="provider"
              checked={config?.provider === 'stub'}
              onChange={() => handleProviderChange('stub')}
              className="text-indigo-600"
            />
            <div>
              <p className="font-medium">Stub (Development)</p>
              <p className="text-sm text-gray-500">Returns sample data for testing</p>
            </div>
          </label>

          <label className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
            <input
              type="radio"
              name="provider"
              checked={config?.provider === 'azure_openai'}
              onChange={() => handleProviderChange('azure_openai')}
              className="text-indigo-600"
            />
            <div>
              <p className="font-medium">Azure OpenAI</p>
              <p className="text-sm text-gray-500">Production-ready AI responses</p>
            </div>
          </label>
        </div>
      </div>

      {config?.provider === 'azure_openai' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Azure OpenAI Configuration</h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Endpoint URL
              </label>
              <input
                type="url"
                value={endpoint}
                onChange={(e) => setEndpoint(e.target.value)}
                placeholder="https://your-resource.openai.azure.com/"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Deployment Name
              </label>
              <input
                type="text"
                value={deployment}
                onChange={(e) => setDeployment(e.target.value)}
                placeholder="gpt-4"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API Key {config.has_api_key && <span className="text-green-600">(configured)</span>}
              </label>
              <div className="relative">
                <input
                  type={showApiKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={config.has_api_key ? '••••••••••••••••' : 'Enter API key'}
                  className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showApiKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div className="text-sm text-gray-500">
              API Version: {config.azure_api_version}
            </div>

            <button
              onClick={handleSaveAzureConfig}
              disabled={updateMutation.isPending}
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
            >
              {updateMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Save Configuration
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ToolsSection() {
  const queryClient = useQueryClient();

  const { data: tools, isLoading } = useQuery({
    queryKey: ['tools'],
    queryFn: getTools,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { enabled?: boolean } }) =>
      updateTool(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tools'] });
    },
  });

  if (isLoading) {
    return <LoadingSpinner />;
  }

  const handleToggle = (tool: MCPTool) => {
    updateMutation.mutate({ id: tool.id, data: { enabled: !tool.enabled } });
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">MCP Tools</h3>
        <p className="text-sm text-gray-500">Enable or disable AI tools used for project management</p>
      </div>

      <div className="divide-y divide-gray-200">
        {tools?.map((tool) => (
          <div key={tool.id} className="flex items-center justify-between p-4">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h4 className="font-medium text-gray-900">{formatToolName(tool.name)}</h4>
                {tool.enabled ? (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">Active</span>
                ) : (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">Disabled</span>
                )}
              </div>
              <p className="text-sm text-gray-500 mt-1">{tool.description}</p>
            </div>
            <button
              onClick={() => handleToggle(tool)}
              disabled={updateMutation.isPending}
              className={clsx(
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                tool.enabled ? 'bg-indigo-600' : 'bg-gray-200'
              )}
            >
              <span
                className={clsx(
                  'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                  tool.enabled ? 'translate-x-6' : 'translate-x-1'
                )}
              />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

function IntegrationsSection() {
  const queryClient = useQueryClient();
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [configInputs, setConfigInputs] = useState<Record<string, string>>({});

  const { data: integrations, isLoading } = useQuery({
    queryKey: ['integrations'],
    queryFn: getIntegrations,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { enabled?: boolean; config?: Record<string, string> } }) =>
      updateIntegration(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
    },
  });

  const testMutation = useMutation({
    mutationFn: testIntegration,
  });

  if (isLoading) {
    return <LoadingSpinner />;
  }

  const handleToggle = (integration: Integration) => {
    updateMutation.mutate({ id: integration.id, data: { enabled: !integration.enabled } });
  };

  const handleSaveConfig = (integration: Integration) => {
    const config: Record<string, string> = {};
    getConfigFields(integration.name).forEach(field => {
      const value = configInputs[`${integration.id}-${field.key}`];
      if (value) config[field.key] = value;
    });
    updateMutation.mutate({ id: integration.id, data: { config } });
  };

  const handleTest = (integration: Integration) => {
    testMutation.mutate(integration.id);
  };

  return (
    <div className="space-y-4">
      {integrations?.map((integration) => (
        <div key={integration.id} className="bg-white rounded-lg border border-gray-200">
          <div
            className="flex items-center justify-between p-4 cursor-pointer"
            onClick={() => setExpandedId(expandedId === integration.id ? null : integration.id)}
          >
            <div className="flex items-center gap-3">
              {expandedId === integration.id ? (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronRight className="w-5 h-5 text-gray-400" />
              )}
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="font-medium text-gray-900">{integration.display_name}</h4>
                  <StatusBadge status={integration.status} />
                </div>
                {integration.config_keys.length > 0 && (
                  <p className="text-xs text-gray-500 mt-1">
                    Configured: {integration.config_keys.join(', ')}
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); handleToggle(integration); }}
              disabled={updateMutation.isPending}
              className={clsx(
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                integration.enabled ? 'bg-indigo-600' : 'bg-gray-200'
              )}
            >
              <span
                className={clsx(
                  'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                  integration.enabled ? 'translate-x-6' : 'translate-x-1'
                )}
              />
            </button>
          </div>

          {expandedId === integration.id && (
            <div className="border-t border-gray-200 p-4 bg-gray-50">
              <div className="space-y-4">
                {getConfigFields(integration.name).map((field) => (
                  <div key={field.key}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {field.label}
                    </label>
                    <input
                      type={field.type}
                      value={configInputs[`${integration.id}-${field.key}`] || ''}
                      onChange={(e) => setConfigInputs({
                        ...configInputs,
                        [`${integration.id}-${field.key}`]: e.target.value,
                      })}
                      placeholder={field.placeholder}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>
                ))}

                <div className="flex gap-2">
                  <button
                    onClick={() => handleSaveConfig(integration)}
                    disabled={updateMutation.isPending}
                    className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
                  >
                    Save
                  </button>
                  <button
                    onClick={() => handleTest(integration)}
                    disabled={testMutation.isPending}
                    className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50 flex items-center gap-2"
                  >
                    {testMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                    Test Connection
                  </button>
                </div>

                {testMutation.data && (
                  <div className={clsx(
                    'p-3 rounded-lg text-sm flex items-center gap-2',
                    testMutation.data.success ? 'bg-green-50 text-green-700' : 'bg-yellow-50 text-yellow-700'
                  )}>
                    <AlertCircle className="w-4 h-4" />
                    {testMutation.data.message}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-48">
      <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors = {
    connected: 'bg-green-100 text-green-700',
    disconnected: 'bg-gray-100 text-gray-600',
    error: 'bg-red-100 text-red-700',
  };
  return (
    <span className={clsx('text-xs px-2 py-0.5 rounded-full', colors[status as keyof typeof colors] || colors.disconnected)}>
      {status}
    </span>
  );
}

function formatToolName(name: string): string {
  return name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function getConfigFields(integrationName: string): { key: string; label: string; type: string; placeholder: string }[] {
  const fields: Record<string, { key: string; label: string; type: string; placeholder: string }[]> = {
    outlook: [
      { key: 'client_id', label: 'Client ID', type: 'text', placeholder: 'Azure AD Application Client ID' },
      { key: 'client_secret', label: 'Client Secret', type: 'password', placeholder: 'Application Secret' },
      { key: 'tenant_id', label: 'Tenant ID', type: 'text', placeholder: 'Azure AD Tenant ID' },
    ],
    google_calendar: [
      { key: 'client_id', label: 'Client ID', type: 'text', placeholder: 'Google OAuth Client ID' },
      { key: 'client_secret', label: 'Client Secret', type: 'password', placeholder: 'Client Secret' },
    ],
    teams: [
      { key: 'webhook_url', label: 'Webhook URL', type: 'url', placeholder: 'Teams Incoming Webhook URL' },
    ],
    slack: [
      { key: 'bot_token', label: 'Bot Token', type: 'password', placeholder: 'xoxb-...' },
      { key: 'channel_id', label: 'Default Channel ID', type: 'text', placeholder: 'C0123456789' },
    ],
  };
  return fields[integrationName] || [];
}
