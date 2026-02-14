import type { ChatResponse, LatestEvalReportResponse } from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function sendChat(prompt: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.2,
      seed: 42
    })
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Backend request failed: ${response.status} ${text}`);
  }

  return (await response.json()) as ChatResponse;
}

export async function fetchLatestEvalReport(): Promise<LatestEvalReportResponse> {
  const response = await fetch(`${API_BASE}/eval/reports/latest`);

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Eval report request failed: ${response.status} ${text}`);
  }

  return (await response.json()) as LatestEvalReportResponse;
}
