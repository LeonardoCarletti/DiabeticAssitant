import { useState, useEffect } from 'react';
import { Activity, LogOut, MessageSquare, TrendingUp, Zap, Droplet } from 'lucide-react';
import { chatWithResearcher, getLogs, getPredictiveAnalysis } from '../lib/api';

interface DashboardProps {
  userId: string;
  onLogout: () => void;
}

export default function DashboardPage({ userId, onLogout }: DashboardProps) {
  const [glucose, setGlucose] = useState(120);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<{role: string; content: string}[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return;
    const userMsg = { role: 'user', content: chatInput };
    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setLoading(true);
    try {
      const res = await chatWithResearcher(chatInput);
      setChatMessages(prev => [...prev, { role: 'assistant', content: res.response }]);
    } catch (e) {
      setChatMessages(prev => [...prev, { role: 'system', content: 'Erro ao enviar mensagem' }]);
    }
    setLoading(false);
  };

  const glucoseStatus = glucose < 70 ? 'LOW' : glucose > 180 ? 'HIGH' : 'NORMAL';
  const glucoseColor = glucoseStatus === 'LOW' ? 'text-red-400' : glucoseStatus === 'HIGH' ? 'text-orange-400' : 'text-green-400';

  return (
    <div className="min-h-screen bg-[#050A0F] hud-grid flex overflow-hidden">
      {/* Left Sidebar - Coach Brain */}
      <div className="w-80 border-r border-white/5 p-6 overflow-y-auto flex flex-col">
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-xl glass flex items-center justify-center">
              <Activity className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-white font-bold text-sm">DIABETIC ASSIST</h2>
              <p className="text-xs text-gray-600">USER: {userId.slice(0,8)}</p>
            </div>
          </div>
        </div>

        <div className="glass rounded-xl p-4 mb-4">
          <h3 className="text-xs text-gray-500 uppercase tracking-widest mb-3">Insights do Coach</h3>
          <div className="space-y-2">
            <div className="p-3 glass rounded-lg">
              <p className="text-xs text-cyan-300 mb-1 font-bold">RECOMENDACAO</p>
              <p className="text-xs text-gray-400">Glicemia estavel. Mantenha a rotina atual.</p>
            </div>
          </div>
        </div>

        <div className="mt-auto">
          <button onClick={onLogout} className="w-full flex items-center justify-center gap-2 glass hover:bg-white/10 transition-colors py-3 rounded-xl text-sm text-gray-400">
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </div>

      {/* Central HUD */}
      <div className="flex-1 flex flex-col">
        <div className="border-b border-white/5 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <span className="text-xs text-gray-500 uppercase tracking-widest">System Online</span>
            </div>
            <div className="text-xs text-gray-600">{new Date().toLocaleTimeString('pt-BR')}</div>
          </div>
        </div>

        <div className="flex-1 p-6 overflow-y-auto">
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Glucose HUD */}
            <div className="glass-strong rounded-2xl p-8 glow-cyan">
              <div className="text-center">
                <div className="inline-flex items-center gap-2 mb-2">
                  <Droplet className="w-5 h-5 text-cyan-400" />
                  <span className="text-xs text-gray-500 uppercase tracking-widest">Glicemia Atual</span>
                </div>
                <div className={`text-6xl font-bold ${glucoseColor} mb-2`}>{glucose}</div>
                <div className="text-sm text-gray-600">mg/dL</div>
                <div className="mt-4 flex justify-center gap-2">
                  <div className="px-3 py-1 rounded-full glass text-xs">
                    <span className="text-gray-600">Min: </span>
                    <span className="text-white">80</span>
                  </div>
                  <div className="px-3 py-1 rounded-full glass text-xs">
                    <span className="text-gray-600">Max: </span>
                    <span className="text-white">150</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Metrics Row */}
            <div className="grid grid-cols-3 gap-4">
              {[{ label: 'Insulina', value: '24u', icon: Zap, color: 'cyan' },
                { label: 'Carbos', value: '180g', icon: TrendingUp, color: 'green' },
                { label: 'Readiness', value: '92%', icon: Activity, color: 'blue' }].map(m => (
                <div key={m.label} className="glass rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <m.icon className={`w-4 h-4 text-${m.color}-400`} />
                    <span className="text-xs text-gray-500 uppercase">{m.label}</span>
                  </div>
                  <div className="text-2xl font-bold text-white">{m.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Chat */}
      <div className="w-96 border-l border-white/5 flex flex-col">
        <div className="border-b border-white/5 p-4 flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-bold text-white">LabMode Chat</h3>
        </div>

        <div className="flex-1 p-4 overflow-y-auto space-y-3">
          {chatMessages.map((msg, i) => (
            <div key={i} className={`p-3 rounded-xl ${msg.role === 'user' ? 'glass ml-auto max-w-[80%]' : 'bg-cyan-500/10 mr-auto max-w-[90%]'}`}>
              <div className="text-xs text-gray-500 mb-1">{msg.role === 'user' ? 'VOCÊ' : 'ASSIST'}</div>
              <div className="text-sm text-white">{msg.content}</div>
            </div>
          ))}
          {loading && <div className="text-center text-cyan-400 text-sm">Processando...</div>}
        </div>

        <div className="border-t border-white/5 p-4">
          <div className="flex gap-2">
            <input
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
              placeholder="Pergunte ao assistente..."
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-cyan-400/50"
            />
            <button
              onClick={handleSendMessage}
              disabled={loading || !chatInput.trim()}
              className="px-4 py-2 bg-cyan-400 hover:bg-cyan-300 disabled:opacity-30 disabled:cursor-not-allowed text-black font-bold rounded-xl transition-colors text-sm"
            >
              Enviar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
