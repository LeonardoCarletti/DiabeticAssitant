import { useState, useEffect } from 'react';
import { ClipboardList, ArrowLeft, Filter } from 'lucide-react';

interface LogsPageProps {
  userId: string;
  onNavigate: (page: string) => void;
}

interface LogEntry {
  id: string;
  event_type: string;
  description: string;
  created_at: string;
  metadata?: Record<string, unknown>;
}

const API_BASE = import.meta.env.VITE_API_URL || 'https://diabeticassistant-backend.vercel.app';

async function getLogs(userId: string, filter: string): Promise<LogEntry[]> {
  const token = localStorage.getItem('da_token') || '';
  const params = new URLSearchParams({ user_id: userId, limit: '50' });
  if (filter !== 'all') params.append('event_type', filter);
  const res = await fetch(`${API_BASE}/api/logs?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.logs || data || [];
}

const EVENT_TYPES = [
  { value: 'all', label: 'Todos' },
  { value: 'glucose', label: 'Glicemia' },
  { value: 'meal', label: 'Refeições' },
  { value: 'workout', label: 'Treinos' },
  { value: 'medication', label: 'Medicação' },
  { value: 'insulin', label: 'Insulina' },
  { value: 'vital', label: 'Sinais Vitais' },
  { value: 'chat', label: 'Chat IA' },
];

const TYPE_COLORS: Record<string, string> = {
  glucose: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  meal: 'text-orange-400 bg-orange-500/10 border-orange-500/30',
  workout: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
  medication: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
  insulin: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
  vital: 'text-red-400 bg-red-500/10 border-red-500/30',
  chat: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
};

export default function LogsPage({ userId, onNavigate }: LogsPageProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  const load = async () => {
    setLoading(true);
    const data = await getLogs(userId, filter);
    setLogs(data);
    setLoading(false);
  };

  useEffect(() => { load(); }, [userId, filter]);

  return (
    <div className="min-h-screen bg-[#050A0F] text-white">
      <div className="max-w-2xl mx-auto p-4">
        <div className="flex items-center gap-3 mb-6 pt-4">
          <button onClick={() => onNavigate('dashboard')} className="text-gray-400 hover:text-white">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <ClipboardList className="w-6 h-6 text-yellow-400" />
          <h1 className="text-xl font-bold">Histórico & Logs</h1>
        </div>

        <div className="flex items-center gap-2 mb-5 flex-wrap">
          <Filter className="w-4 h-4 text-gray-400" />
          {EVENT_TYPES.map(t => (
            <button key={t.value} onClick={() => setFilter(t.value)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                filter === t.value
                  ? 'bg-yellow-500 text-black'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}>
              {t.label}
            </button>
          ))}
        </div>

        <div className="space-y-2">
          {loading ? (
            <div className="flex justify-center py-10">
              <div className="w-8 h-8 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-10 text-gray-500 text-sm">
              Nenhum registro encontrado{filter !== 'all' ? ' para este filtro' : ''}.
            </div>
          ) : (
            logs.map((log, i) => {
              const color = TYPE_COLORS[log.event_type] || 'text-gray-400 bg-gray-800 border-gray-700';
              return (
                <div key={log.id || i} className="bg-gray-900 border border-gray-800 rounded-xl p-3 flex items-start gap-3">
                  <span className={`text-xs px-2 py-0.5 rounded border ${color} shrink-0 mt-0.5`}>
                    {log.event_type}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white">{log.description}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {new Date(log.created_at).toLocaleString('pt-BR')}
                    </p>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
