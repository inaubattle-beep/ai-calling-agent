export interface Call {
  id: string;
  phone_number: string;
  direction: 'INBOUND' | 'OUTBOUND';
  language: string;
  status: string;
  agent_id?: string;
  started_at: string;
  answered_at?: string;
  ended_at?: string;
  duration: number;
}

export interface TranscriptMessage {
  id: string;
  call_id: string;
  speaker: 'customer' | 'ai' | 'system';
  text: string;
  language: string;
  latency_ms?: number;
  timestamp: string;
}

export interface CallDetail extends Call {
  transcripts: TranscriptMessage[];
}

export interface Agent {
  id: string;
  name: string;
  status: string;
  current_call_id?: string;
  model: string;
  primary_language: string;
  stt_latency_ms: number;
  llm_latency_ms: number;
  tts_latency_ms: number;
}

export interface SystemEvent {
  id: string;
  event: string;
  call_id?: string;
  agent_id?: string;
  data: Record<string, any>;
  timestamp: string;
}

const API_BASE = typeof window !== 'undefined' ? '' : (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000');

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}

export async function fetchCalls(status?: string): Promise<Call[]> {
  const url = status ? `${API_BASE}/api/calls?status=${status}` : `${API_BASE}/api/calls`;
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) return [];
  return res.json();
}

export async function fetchCallDetail(id: string): Promise<CallDetail | null> {
  const res = await fetch(`${API_BASE}/api/calls/${id}`, { cache: 'no-store' });
  if (!res.ok) return null;
  return res.json();
}

export async function createCall(data: {
  phone_number: string;
  direction?: string;
  language?: string;
  agent_id?: string;
}): Promise<Call> {
  const res = await fetch(`${API_BASE}/api/calls`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function hangupCall(id: string): Promise<void> {
  await fetch(`${API_BASE}/api/calls/${id}/hangup`, { method: 'POST' });
}

export async function interruptCall(id: string): Promise<void> {
  await fetch(`${API_BASE}/api/calls/${id}/interrupt`, { method: 'POST' });
}

export async function simulateCall(data: {
  phone_number?: string;
  language?: string;
  barge_in?: boolean;
}): Promise<{ status: string; call_id: string }> {
  const res = await fetch(`${API_BASE}/api/calls/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function fetchAgents(): Promise<Agent[]> {
  const res = await fetch(`${API_BASE}/api/agents`, { cache: 'no-store' });
  if (!res.ok) return [];
  return res.json();
}

export async function fetchEvents(): Promise<SystemEvent[]> {
  const res = await fetch(`${API_BASE}/api/events`, { cache: 'no-store' });
  if (!res.ok) return [];
  return res.json();
}
