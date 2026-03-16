import { useState, useEffect } from 'react';
import { Activity, LogOut, TrendingUp, Zap, Droplet, MessageSquare, Dumbbell } from 'lucide-react';
import { getLogs, getPredictiveAnalysis } from '../lib/api';

interface LogEntry {
  id: number;
  timestamp: string;
  value: number;
  type: string;
}

interface PredictData {
  prediction: string;
  confidence: number;
  next_glucose: number;
  trend: string;
}

interface DashboardProps {
  userId: string;
  onLogout: () => void;
  onNavigate: (page: 'dashboard' | 'chat' | 'workout') => void;
}

export default function DashboardPage({ userId, onLogout, onNavigate }: DashboardProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [predict, setPredict] = useState<PredictData | null>(null);
  const [loadingData, setLoadingData] = useState(true);
  const [time, setTime] = useState(new Date());

  // Atualiza relogio a cada segundo
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // Carrega logs e predicao ao montar
  useEffect(() => {
    async function fetchData() {
      setLoadingData(true);
      try {
        const [logsData, predictData] = await Promise.all([
          getLogs(),
          getPredictiveAnalysis(),
        ]);
        setLogs(logsData);
        setPredict(predictData);
      } catch (err) {
        console.error('Erro ao carregar dados:', err);
      } finally {
        setLoadingData(false);
      }
    }
    fetchData();
    // Atualiza a cada 5 minutos
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const currentGlucose = logs.length > 0 ? logs[0].value : (predict?.next_glucose ?? 120);
  const glucoseStatus = currentGlucose < 70 ? 'LOW' : currentGlucose > 180 ? 'HIGH' : 'NORMAL';
  const glucoseColor = glucoseStatus === 'LOW' ? 'text-red-400' : glucoseStatus === 'HIGH' ? 'text-orange-400' : 'text-green-400';

  const trendIcon = predict?.trend === 'subindo' ? '↗️' : predict?.trend === 'descendo' ? '↘️' : '→';
  const trendColor = predict?.trend === 'subindo' ? 'text-orange-400' : predict?.trend === 'descendo' ? 'text-blue-400' : 'text-green-400';

  // Ultimas 6 medicoes para o mini grafico
  const recentLogs = logs.slice(0, 6).reverse();
  const maxVal = Math.max(...recentLogs.map(l => l.value), 1);

  return (
    <div className="min-h-screen bg-[#050A0F] flex overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 border-r border-white/5 p-5 flex flex-col gap-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 flex items-center justify-center">
            <Activity className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h2 className="text-white font-bold text-sm">DIABETIC ASSIST</h2>
            <p className="text-xs text-gray-600">USER: {userId.slice(0, 8)}</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="space-y-1 flex-1">
          <button onClick={() => onNavigate('dashboard')}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl bg-cyan-500/10 text-cyan-400 text-sm font-medium">
            <Droplet className="w-4 h-4" /> Dashboard
          </button>
          <button onClick={() => onNavigate('chat')}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-white/5 text-gray-400 hover:text-white transition-colors text-sm">
            <MessageSquare className="w-4 h-4" /> Assistente IA
          </button>
          <button onClick={() => onNavigate('workout')}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-white/5 text-gray-400 hover:text-white transition-colors text-sm">
            <Dumbbell className="w-4 h-4" /> Treinos
          </button>
        </nav>

        {/* Coach Insight */}
        {predict && (
          <div className="bg-white/5 rounded-xl p-3">
            <h3 className="text-xs text-gray-500 uppercase tracking-widest mb-2">Coach</h3>
            <p className="text-xs text-cyan-300 font-bold mb-1">PREVISAO</p>
            <p className="text-xs text-gray-400">{predict.prediction}</p>
            <p className={`text-xs mt-1 font-medium ${trendColor}`}>Tendencia: {predict.trend} {trendIcon}</p>
            <p className="text-xs text-gray-600 mt-1">Confianca: {Math.round(predict.confidence * 100)}%</p>
          </div>
        )}

        <button onClick={onLogout}
          className="w-full flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 transition-colors py-2 rounded-xl text-sm text-gray-400">
          <LogOut className="w-4 h-4" /> Logout
        </button>
      </div>

      {/* Main */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b border-white/5 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-xs text-gray-500 uppercase tracking-widest">System Online</span>
          </div>
          <span className="text-xs text-gray-600">{time.toLocaleTimeString('pt-BR')}</span>
        </div>

        <div className="flex-1 p-6 overflow-y-auto">
          <div className="max-w-3xl mx-auto space-y-5">

            {/* Glucose Card */}
            <div className="bg-cyan-500/5 border border-cyan-500/20 rounded-2xl p-8">
              <div className="text-center">
                <div className="inline-flex items-center gap-2 mb-2">
                  <Droplet className="w-5 h-5 text-cyan-400" />
                  <span className="text-xs text-gray-500 uppercase tracking-widest">Glicemia Atual</span>
                </div>
                {loadingData ? (
                  <div className="text-4xl font-bold text-gray-600 mb-2 animate-pulse">---</div>
                ) : (
                  <div className={`text-6xl font-bold ${glucoseColor} mb-2`}>{Math.round(currentGlucose)}</div>
                )}
                <div className="text-sm text-gray-600">mg/dL</div>
                <div className="mt-2">
                  <span className={`text-sm font-medium ${trendColor}`}>{trendIcon} {predict?.trend ?? 'carregando...'}</span>
                </div>
              </div>
            </div>

            {/* Mini grafico de historico */}
            {recentLogs.length > 0 && (
              <div className="bg-white/3 border border-white/5 rounded-xl p-5">
                <h3 className="text-xs text-gray-500 uppercase tracking-widest mb-4">Historico (ultimas 6h)</h3>
                <div className="flex items-end gap-2 h-20">
                  {recentLogs.map((log, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1">
                      <div
                        className={`w-full rounded-t ${
                          log.value < 70 ? 'bg-red-500' :
                          log.value > 180 ? 'bg-orange-500' : 'bg-cyan-500'
                        }`}
                        style={{ height: `${(log.value / maxVal) * 100}%`, minHeight: '4px' }}
                      />
                      <span className="text-xs text-gray-600">{Math.round(log.value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Metric Cards */}
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: 'Ultima Medicao', value: logs.length > 0 ? `${Math.round(logs[0].value)} mg/dL` : '---', icon: Droplet, color: 'cyan' },
                { label: 'Tendencia', value: predict?.trend ?? '---', icon: TrendingUp, color: 'green' },
                { label: 'Confianca IA', value: predict ? `${Math.round(predict.confidence * 100)}%` : '---', icon: Activity, color: 'blue' },
              ].map(m => (
                <div key={m.label} className="bg-white/5 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <m.icon className={`w-4 h-4 text-${m.color}-400`} />
                    <span className="text-xs text-gray-500 uppercase">{m.label}</span>
                  </div>
                  <div className="text-xl font-bold text-white">{loadingData ? '...' : m.value}</div>
                </div>
              ))}
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-2 gap-4">
              <button onClick={() => onNavigate('chat')}
                className="bg-cyan-500/10 border border-cyan-500/20 rounded-xl p-4 flex items-center gap-3 hover:bg-cyan-500/20 transition-colors">
                <MessageSquare className="w-5 h-5 text-cyan-400" />
                <div className="text-left">
                  <div className="text-sm text-white font-medium">Assistente IA</div>
                  <div className="text-xs text-gray-500">Tire suas duvidas</div>
                </div>
              </button>
              <button onClick={() => onNavigate('workout')}
                className="bg-purple-500/10 border border-purple-500/20 rounded-xl p-4 flex items-center gap-3 hover:bg-purple-500/20 transition-colors">
                <Dumbbell className="w-5 h-5 text-purple-400" />
                <div className="text-left">
                  <div className="text-sm text-white font-medium">Treino de Hoje</div>
                  <div className="text-xs text-gray-500">Ver plano personalizado</div>
                </div>
              </button>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}
