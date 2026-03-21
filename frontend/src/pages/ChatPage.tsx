import { useState, useRef, useEffect } from 'react';
import { ArrowLeft, Send, Bot, User, Droplet, Dumbbell, MessageSquare } from 'lucide-react';
import { chatWithResearcher } from '../lib/api';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface ChatPageProps {
  userId: string;
  onNavigate: (page: 'dashboard' | 'chat' | 'workout') => void;
}

export default function ChatPage({ userId, onNavigate }: ChatPageProps) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Ola! Sou seu assistente de saude especializado em diabetes. Posso te ajudar com duvidas sobre glicemia, insulina, nutricao, treinos e bem-estar. Como posso te ajudar hoje?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const suggestions = [
    'Qual glicemia ideal em jejum?',
    'Como o treino afeta a insulina?',
    'O que fazer em hipoglicemia?',
    'Alimentos que aumentam muito a glicemia?',
  ];

  async function handleSend(text?: string) {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;
    setInput('');
    const userMsg: Message = { role: 'user', content: msg };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    try {
      const res = await chatWithResearcher(msg);
      setMessages(prev => [...prev, { role: 'assistant', content: res.response }]);
    } catch {
      setMessages(prev => [...prev, { role: 'system', content: 'Erro ao conectar ao assistente. Tente novamente.' }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#050A0F] flex">
      {/* Sidebar */}
      <div className="w-64 border-r border-white/5 p-5 flex flex-col gap-2">
        <button onClick={() => onNavigate('dashboard')}
          className="flex items-center gap-2 text-gray-400 hover:text-white text-sm mb-4 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Voltar
        </button>
        <nav className="space-y-1">
          <button onClick={() => onNavigate('dashboard')}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-white/5 text-gray-400 hover:text-white transition-colors text-sm">
            <Droplet className="w-4 h-4" /> Dashboard
          </button>
          <button onClick={() => onNavigate('chat')}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl bg-cyan-500/10 text-cyan-400 text-sm font-medium">
            <MessageSquare className="w-4 h-4" /> Assistente IA
          </button>
          <button onClick={() => onNavigate('workout')}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-white/5 text-gray-400 hover:text-white transition-colors text-sm">
            <Dumbbell className="w-4 h-4" /> Treinos
          </button>
        </nav>
        <div className="mt-auto">
          <p className="text-xs text-gray-600 text-center">USER: {userId.slice(0, 8)}</p>
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b border-white/5 px-6 py-4 flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-cyan-500/10 flex items-center justify-center">
            <Bot className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white">Assistente Diabetico IA</h1>
            <p className="text-xs text-gray-500">Especializado em diabetes, nutricao e treinos</p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-xs text-gray-500">Online</span>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${
              msg.role === 'user' ? 'flex-row-reverse' : ''
            }`}>
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
                msg.role === 'user' ? 'bg-purple-500/20' :
                msg.role === 'system' ? 'bg-red-500/20' : 'bg-cyan-500/10'
              }`}>
                {msg.role === 'user' ? <User className="w-4 h-4 text-purple-400" /> : <Bot className="w-4 h-4 text-cyan-400" />}
              </div>
              <div className={`max-w-lg px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'user' ?
                  'bg-purple-500/10 border border-purple-500/20 text-white rounded-tr-sm' :
                msg.role === 'system' ?
                  'bg-red-500/10 border border-red-500/20 text-red-300 rounded-tl-sm' :
                  'bg-cyan-500/5 border border-cyan-500/20 text-gray-200 rounded-tl-sm'
              }`}>
                {msg.content}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-xl bg-cyan-500/10 flex items-center justify-center">
                <Bot className="w-4 h-4 text-cyan-400" />
              </div>
              <div className="bg-cyan-500/5 border border-cyan-500/20 px-4 py-3 rounded-2xl rounded-tl-sm">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{animationDelay:'0ms'}} />
                  <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{animationDelay:'150ms'}} />
                  <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{animationDelay:'300ms'}} />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Suggestions */}
        {messages.length <= 1 && (
          <div className="px-6 pb-3 flex flex-wrap gap-2">
            {suggestions.map(s => (
              <button key={s} onClick={() => handleSend(s)}
                className="text-xs bg-white/5 hover:bg-white/10 border border-white/10 text-gray-400 hover:text-white px-3 py-1.5 rounded-full transition-colors">
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="border-t border-white/5 p-4">
          <div className="flex gap-3">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Pergunte ao assistente de diabetes..."
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-cyan-400/50"
            />
            <button
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              className="px-4 py-3 bg-cyan-500 hover:bg-cyan-400 disabled:opacity-30 disabled:cursor-not-allowed text-black font-bold rounded-xl transition-colors">
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
