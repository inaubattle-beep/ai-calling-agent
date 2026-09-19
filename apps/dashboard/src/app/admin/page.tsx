'use client';

import { FormEvent, useEffect, useState } from 'react';
import { Save, Settings as SettingsIcon, Bot } from 'lucide-react';
import { Header } from '@/components/header';
import { Agent, AppSettings, fetchAgents, fetchSettings, updateAgent, updateSettings } from '@/lib/api';
import { useWebSocket } from '@/lib/websocket';

const emptySettings: AppSettings = {
  id: 1,
  business_name: '',
  dashboard_title: '',
  sip_extension: '',
  default_language: 'bn-BD',
  supported_languages: [],
  default_phone_number: '',
  default_agent_id: '',
};

export default function AdminPage() {
  const [settings, setSettings] = useState<AppSettings>(emptySettings);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [message, setMessage] = useState('');
  const { isConnected } = useWebSocket({ url: '/ws/dashboard' });

  useEffect(() => {
    Promise.all([fetchSettings(), fetchAgents()]).then(([savedSettings, agents]) => {
      if (savedSettings) setSettings(savedSettings);
      setAgent(agents[0] || null);
    });
  }, []);

  const saveSettings = async (event: FormEvent) => {
    event.preventDefault();
    await updateSettings(settings);
    setMessage('Platform settings saved');
  };

  const saveAgent = async (event: FormEvent) => {
    event.preventDefault();
    if (!agent) return;
    const { id, status, current_call_id, stt_latency_ms, llm_latency_ms, tts_latency_ms, ...editable } = agent;
    const saved = await updateAgent(id, editable);
    setAgent(saved);
    setMessage('Agent configuration saved');
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#090d16]">
      <Header wsConnected={isConnected} />
      <main className="p-6 space-y-6 max-w-5xl w-full mx-auto">
        <div>
          <h1 className="text-xl font-bold text-white">Admin Settings</h1>
          <p className="text-xs text-slate-400 mt-1">Every editable value below is stored in SQLite.</p>
        </div>
        {message && <div className="text-xs text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-4 py-3">{message}</div>}

        <form onSubmit={saveSettings} className="glass-panel rounded-2xl border border-border/80 p-6 space-y-5">
          <div className="flex items-center gap-2 text-white font-semibold"><SettingsIcon className="w-4 h-4 text-cyan-400" /> Platform configuration</div>
          <div className="grid md:grid-cols-2 gap-4">
            {([
              ['business_name', 'Business name'], ['dashboard_title', 'Dashboard title'],
              ['sip_extension', 'SIP extension'], ['default_phone_number', 'Default phone number'],
              ['default_language', 'Default language'], ['default_agent_id', 'Default agent ID'],
            ] as const).map(([key, label]) => (
              <label key={key} className="text-xs text-slate-300 space-y-1.5">
                {label}
                <input value={settings[key]} onChange={(e) => setSettings({ ...settings, [key]: e.target.value })} className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-white" required />
              </label>
            ))}
          </div>
          <label className="text-xs text-slate-300 space-y-1.5 block">Supported languages (comma separated)
            <input value={settings.supported_languages.join(', ')} onChange={(e) => setSettings({ ...settings, supported_languages: e.target.value.split(',').map((value) => value.trim()).filter(Boolean) })} className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-white" required />
          </label>
          <button className="inline-flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-xs font-semibold text-white"><Save className="w-4 h-4" /> Save platform settings</button>
        </form>

        {agent && <form onSubmit={saveAgent} className="glass-panel rounded-2xl border border-border/80 p-6 space-y-5">
          <div className="flex items-center gap-2 text-white font-semibold"><Bot className="w-4 h-4 text-emerald-400" /> Agent configuration</div>
          <div className="grid md:grid-cols-2 gap-4">
            {(['name', 'model', 'primary_language'] as const).map((key) => (
              <label key={key} className="text-xs text-slate-300 space-y-1.5">{key.replace('_', ' ')}
                <input value={agent[key]} onChange={(e) => setAgent({ ...agent, [key]: e.target.value })} className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-white" required />
              </label>
            ))}
          </div>
          <label className="text-xs text-slate-300 space-y-1.5 block">Description
            <input value={agent.description} onChange={(e) => setAgent({ ...agent, description: e.target.value })} className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-white" required />
          </label>
          <label className="text-xs text-slate-300 space-y-1.5 block">Greeting
            <textarea value={agent.greeting} onChange={(e) => setAgent({ ...agent, greeting: e.target.value })} className="w-full min-h-20 rounded-lg bg-background border border-border px-3 py-2 text-sm text-white" required />
          </label>
          <label className="text-xs text-slate-300 space-y-1.5 block">System prompt
            <textarea value={agent.system_prompt} onChange={(e) => setAgent({ ...agent, system_prompt: e.target.value })} className="w-full min-h-32 rounded-lg bg-background border border-border px-3 py-2 text-sm text-white" required />
          </label>
          <label className="text-xs text-slate-300 space-y-1.5 block">Supported languages (comma separated)
            <input value={agent.supported_languages.join(', ')} onChange={(e) => setAgent({ ...agent, supported_languages: e.target.value.split(',').map((value) => value.trim()).filter(Boolean) })} className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-white" required />
          </label>
          <label className="flex items-center gap-2 text-xs text-slate-300"><input type="checkbox" checked={agent.enabled} onChange={(e) => setAgent({ ...agent, enabled: e.target.checked })} /> Agent enabled</label>
          <button className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white"><Save className="w-4 h-4" /> Save agent configuration</button>
        </form>}
      </main>
    </div>
  );
}