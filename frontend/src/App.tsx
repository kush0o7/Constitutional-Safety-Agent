import { useMemo, useState } from 'react';

import { fetchLatestEvalReport, sendChat } from './api';
import type { HistoryItem, LatestEvalReportResponse } from './types';

type ActiveView = 'chat' | 'dashboard';

function traceText(item: HistoryItem): string {
  return JSON.stringify(
    {
      prompt: item.prompt,
      ...item.response
    },
    null,
    2
  );
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

export default function App() {
  const [activeView, setActiveView] = useState<ActiveView>('chat');

  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [evalLoading, setEvalLoading] = useState(false);
  const [evalError, setEvalError] = useState('');
  const [evalReport, setEvalReport] = useState<LatestEvalReportResponse | null>(null);

  const selected = useMemo(
    () => history.find((item) => item.id === selectedId) ?? history[0] ?? null,
    [history, selectedId]
  );

  const violationRows = useMemo(() => {
    if (!evalReport) return [];
    return Object.entries(evalReport.summary.violations_by_rule).sort((a, b) => b[1] - a[1]);
  }, [evalReport]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = prompt.trim();
    if (!trimmed) return;

    setLoading(true);
    setError('');

    try {
      const response = await sendChat(trimmed);
      const item: HistoryItem = {
        id: crypto.randomUUID(),
        prompt: trimmed,
        response,
        createdAt: new Date().toISOString()
      };
      setHistory((prev) => [item, ...prev]);
      setSelectedId(item.id);
      setPrompt('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  async function loadLatestReport() {
    setEvalLoading(true);
    setEvalError('');

    try {
      const report = await fetchLatestEvalReport();
      setEvalReport(report);
    } catch (err) {
      setEvalError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setEvalLoading(false);
    }
  }

  async function copyTrace(item: HistoryItem) {
    await navigator.clipboard.writeText(traceText(item));
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-mist via-white to-[#e8f4f1] p-4 font-body text-ink md:p-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
          <div>
            <h1 className="font-display text-2xl font-bold md:text-3xl">Constitutional Safety Agent</h1>
            <p className="mt-1 text-sm text-slate-600">Safe, traceable outputs with constitution-based checks.</p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setActiveView('chat')}
              className={`rounded-xl px-4 py-2 text-sm font-semibold ${
                activeView === 'chat' ? 'bg-ink text-white' : 'bg-slate-100 text-slate-700'
              }`}
            >
              Chat
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveView('dashboard');
                if (!evalReport) {
                  void loadLatestReport();
                }
              }}
              className={`rounded-xl px-4 py-2 text-sm font-semibold ${
                activeView === 'dashboard' ? 'bg-ink text-white' : 'bg-slate-100 text-slate-700'
              }`}
            >
              Safety Dashboard
            </button>
          </div>
        </div>

        {activeView === 'chat' ? (
          <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
            <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-6">
              <form className="space-y-3" onSubmit={onSubmit}>
                <label htmlFor="prompt-input" className="sr-only">
                  Prompt input
                </label>
                <textarea
                  id="prompt-input"
                  name="prompt"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="min-h-32 w-full rounded-xl border border-slate-300 p-3 outline-none ring-accent transition focus:ring"
                  placeholder="Enter your prompt"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="rounded-xl bg-ink px-4 py-2 font-semibold text-white transition hover:bg-slate-700 disabled:opacity-50"
                >
                  {loading ? 'Running...' : 'Submit'}
                </button>
              </form>

              {error ? <p className="mt-3 text-sm text-danger">{error}</p> : null}

              {selected ? (
                <article className="mt-6 space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <div>
                    <h2 className="font-display text-lg font-semibold">Draft</h2>
                    <p className="mt-1 whitespace-pre-wrap text-sm">{selected.response.draft}</p>
                  </div>

                  <div>
                    <h2 className="font-display text-lg font-semibold">Violations</h2>
                    <ul className="mt-2 space-y-2 text-sm">
                      {selected.response.violations.map((v) => (
                        <li key={`${v.rule}-${v.reason}`} className="rounded-lg bg-white p-2">
                          <span className="font-semibold">
                            {v.violated ? '❌' : '✅'} {v.rule}
                          </span>
                          <p className="text-slate-700">{v.reason}</p>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h2 className="font-display text-lg font-semibold">Final Answer</h2>
                    <p className="mt-1 whitespace-pre-wrap text-sm">{selected.response.final_answer}</p>
                  </div>

                  <div>
                    <h2 className="font-display text-lg font-semibold">Confidence</h2>
                    <p className="mt-1 text-sm">{selected.response.confidence}</p>
                  </div>

                  <div>
                    <h2 className="font-display text-lg font-semibold">Rule Application Log</h2>
                    <ul className="mt-2 space-y-2 text-sm">
                      {selected.response.rule_applied_log.map((entry) => (
                        <li key={`${entry.rule}-${entry.detail}`} className="rounded-lg bg-white p-2">
                          <span className="font-semibold">{entry.rule}</span> ({entry.status})
                          <p className="text-slate-700">{entry.detail}</p>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <button
                    type="button"
                    className="rounded-xl bg-sea px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700"
                    onClick={() => copyTrace(selected)}
                  >
                    Copy Full Trace
                  </button>
                </article>
              ) : null}
            </section>

            <aside className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-6">
              <h2 className="font-display text-xl font-bold">History</h2>
              <ul className="mt-3 space-y-2">
                {history.map((item) => (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedId(item.id)}
                      className={`w-full rounded-lg border p-2 text-left text-sm transition ${
                        selected?.id === item.id
                          ? 'border-ink bg-slate-100'
                          : 'border-slate-200 bg-white hover:bg-slate-50'
                      }`}
                    >
                      <p className="line-clamp-2 font-semibold">{item.prompt}</p>
                      <p className="text-xs text-slate-500">{new Date(item.createdAt).toLocaleString()}</p>
                    </button>
                  </li>
                ))}
                {history.length === 0 ? <p className="text-sm text-slate-500">No prompts yet.</p> : null}
              </ul>
            </aside>
          </div>
        ) : (
          <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-6">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-display text-2xl font-bold">Safety Dashboard</h2>
              <button
                type="button"
                onClick={() => void loadLatestReport()}
                disabled={evalLoading}
                className="rounded-xl bg-sea px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-50"
              >
                {evalLoading ? 'Refreshing...' : 'Refresh Latest Report'}
              </button>
            </div>

            {evalError ? <p className="text-sm text-danger">{evalError}</p> : null}

            {evalReport ? (
              <>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-xs text-slate-500">Pass Rate</p>
                    <p className="text-2xl font-bold text-ink">{evalReport.summary.pass_rate}%</p>
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-xs text-slate-500">Total Cases</p>
                    <p className="text-2xl font-bold text-ink">{evalReport.summary.total}</p>
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-xs text-slate-500">Passed</p>
                    <p className="text-2xl font-bold text-sea">{evalReport.summary.passed}</p>
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-xs text-slate-500">Failed</p>
                    <p className="text-2xl font-bold text-danger">{evalReport.summary.failed}</p>
                  </div>
                </div>

                <div className="grid gap-4 lg:grid-cols-2">
                  <article className="rounded-xl border border-slate-200 p-4">
                    <h3 className="font-display text-lg font-semibold">Violation Counts By Rule</h3>
                    <ul className="mt-2 space-y-2 text-sm">
                      {violationRows.length > 0 ? (
                        violationRows.map(([rule, count]) => (
                          <li key={rule} className="flex items-center justify-between rounded-lg bg-slate-50 p-2">
                            <span className="font-medium">{rule}</span>
                            <span>{count}</span>
                          </li>
                        ))
                      ) : (
                        <li className="text-slate-500">No violations recorded.</li>
                      )}
                    </ul>
                  </article>

                  <article className="rounded-xl border border-slate-200 p-4">
                    <h3 className="font-display text-lg font-semibold">Failed Cases</h3>
                    <ul className="mt-2 space-y-2 text-sm">
                      {evalReport.summary.failed_ids.length > 0 ? (
                        evalReport.summary.failed_ids.map((id) => (
                          <li key={id} className="rounded-lg bg-slate-50 p-2 font-medium text-danger">
                            {id}
                          </li>
                        ))
                      ) : (
                        <li className="text-sea">No failed cases in latest run.</li>
                      )}
                    </ul>
                  </article>
                </div>

                <article className="rounded-xl border border-slate-200 p-4">
                  <h3 className="font-display text-lg font-semibold">Latest Report Metadata</h3>
                  <p className="mt-2 text-sm text-slate-700">
                    <span className="font-semibold">Generated:</span> {formatDate(evalReport.generated_at)}
                  </p>
                  <p className="mt-1 text-sm text-slate-700">
                    <span className="font-semibold">Source File:</span> {evalReport.source_file}
                  </p>
                </article>
              </>
            ) : (
              <p className="text-sm text-slate-500">No report loaded yet. Click refresh to load the latest eval run.</p>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
