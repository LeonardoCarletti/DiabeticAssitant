import { useState } from 'react';
import { requestOtp, verifyOtp, setToken } from '../lib/api';
import { Activity, Shield, Zap, Brain } from 'lucide-react';

interface LoginPageProps {
  onLogin: (token: string, uid: string) => void;
}

export default function LoginPage({ onLogin }: LoginPageProps) {
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [step, setStep] = useState<'phone' | 'otp'>('phone');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRequestOtp = async () => {
    if (!phone) return;
    setLoading(true);
    setError('');
    try {
      await requestOtp(phone);
      setStep('otp');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao enviar OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (!code) return;
    setLoading(true);
    setError('');
    try {
      const res = await verifyOtp(phone, code) as { access_token: string; user_id?: string };
      const token = res.access_token;
      const uid = res.user_id || phone.replace(/\D/g, '');
      onLogin(token, uid);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Codigo invalido');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050A0F] hud-grid flex items-center justify-center overflow-hidden relative">
      {/* Background orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl" />

      {/* Scan line effect */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="h-px w-full bg-gradient-to-r from-transparent via-cyan-400/20 to-transparent animate-pulse" style={{ top: '30%', position: 'absolute' }} />
      </div>

      <div className="w-full max-w-md px-6 relative z-10">
        {/* Logo/Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl glass glow-cyan mb-4 relative">
            <Activity className="w-10 h-10 text-cyan-400" />
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-pulse" />
          </div>
          <h1 className="text-3xl font-bold tracking-wider text-white mb-1">
            DIABETIC
            <span className="text-cyan-400"> ASSIST</span>
          </h1>
          <p className="text-xs text-gray-500 tracking-widest uppercase">Personal Performance HUD</p>
        </div>

        {/* Feature pills */}
        <div className="flex gap-2 justify-center mb-8">
          {[{ icon: Shield, label: 'Secure' }, { icon: Zap, label: 'Real-time' }, { icon: Brain, label: 'AI-Powered' }].map(({ icon: Icon, label }) => (
            <div key={label} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-xs text-gray-400">
              <Icon className="w-3 h-3 text-cyan-400" />
              {label}
            </div>
          ))}
        </div>

        {/* Login card */}
        <div className="glass-strong rounded-2xl p-8 glow-cyan">
          {step === 'phone' ? (
            <>
              <div className="mb-6">
                <label className="block text-xs text-gray-400 uppercase tracking-widest mb-2">Telefone</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={e => setPhone(e.target.value)}
                  placeholder="+55 11 99999-9999"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-cyan-400/50 focus:bg-white/8 transition-all text-sm"
                  onKeyDown={e => e.key === 'Enter' && handleRequestOtp()}
                />
              </div>
              <button
                onClick={handleRequestOtp}
                disabled={loading || !phone}
                className="w-full bg-cyan-400 hover:bg-cyan-300 disabled:opacity-30 disabled:cursor-not-allowed text-black font-bold py-3 rounded-xl transition-all duration-200 text-sm tracking-wider uppercase"
              >
                {loading ? 'Enviando...' : 'Enviar Codigo OTP'}
              </button>
            </>
          ) : (
            <>
              <div className="mb-2">
                <button onClick={() => setStep('phone')} className="text-xs text-gray-500 hover:text-cyan-400 transition-colors mb-4 flex items-center gap-1">
                  ← Voltar
                </button>
                <label className="block text-xs text-gray-400 uppercase tracking-widest mb-2">Codigo OTP</label>
                <input
                  type="text"
                  value={code}
                  onChange={e => setCode(e.target.value)}
                  placeholder="000000"
                  maxLength={6}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-center placeholder-gray-600 focus:outline-none focus:border-cyan-400/50 transition-all text-2xl tracking-widest"
                  onKeyDown={e => e.key === 'Enter' && handleVerifyOtp()}
                />
                <p className="text-xs text-gray-600 mt-2 text-center">Codigo enviado para {phone}</p>
              </div>
              <button
                onClick={handleVerifyOtp}
                disabled={loading || code.length < 4}
                className="w-full mt-4 bg-cyan-400 hover:bg-cyan-300 disabled:opacity-30 disabled:cursor-not-allowed text-black font-bold py-3 rounded-xl transition-all duration-200 text-sm tracking-wider uppercase"
              >
                {loading ? 'Verificando...' : 'Acessar HUD'}
              </button>
            </>
          )}

          {error && (
            <div className="mt-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs text-center">
              {error}
            </div>
          )}
        </div>

        <p className="text-center text-xs text-gray-700 mt-6">
          Diabetic Assistant &copy; 2026 — Performance Intelligence
        </p>
      </div>
    </div>
  );
}
