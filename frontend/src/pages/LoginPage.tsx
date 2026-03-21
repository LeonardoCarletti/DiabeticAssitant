import { useState } from 'react';
import { requestOtp, setToken } from '../lib/api';
import { Activity, Shield, Zap, Brain } from 'lucide-react';

const DEV_BYPASS_PHONES = ['11988024265', '5511988024265', '+5511988024265'];

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
      const digits = phone.replace(/\D/g, '');
      // Bypass local para numero de desenvolvimento
      if (DEV_BYPASS_PHONES.includes(phone) || DEV_BYPASS_PHONES.includes(digits) || DEV_BYPASS_PHONES.includes('55' + digits)) {
        const uid = '55' + digits;
        const token = `dev-bypass-token-${uid}`;
        setToken(token);
        onLogin(token, uid);
        return;
      }
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
      const API_URL = (import.meta as unknown as { env: { VITE_API_URL?: string } }).env.VITE_API_URL || '';
      const res = await fetch(`${API_URL}/api/auth/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, code }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({})) as { detail?: string };
        throw new Error(err.detail ?? 'Codigo invalido');
      }
      const data = await res.json() as { access_token: string; user_id?: string };
      const token = data.access_token;
      const uid = data.user_id || phone.replace(/\D/g, '');
      setToken(token);
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
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+55 11 90000-0000"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-cyan-500/50 focus:bg-white/8 transition-all"
                  onKeyDown={(e) => e.key === 'Enter' && handleRequestOtp()}
                />
              </div>
              {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
              <button
                onClick={handleRequestOtp}
                disabled={loading || !phone}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-semibold tracking-wider hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {loading ? 'AGUARDE...' : 'CONTINUAR'}
              </button>
            </>
          ) : (
            <>
              <div className="mb-6">
                <label className="block text-xs text-gray-400 uppercase tracking-widest mb-2">Codigo SMS</label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="000000"
                  maxLength={6}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-cyan-500/50 focus:bg-white/8 transition-all text-center text-2xl tracking-widest"
                  onKeyDown={(e) => e.key === 'Enter' && handleVerifyOtp()}
                />
              </div>
              {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
              <button
                onClick={handleVerifyOtp}
                disabled={loading || !code}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-semibold tracking-wider hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {loading ? 'VERIFICANDO...' : 'ENTRAR'}
              </button>
              <button
                onClick={() => { setStep('phone'); setError(''); }}
                className="w-full mt-3 py-2 text-gray-500 text-sm hover:text-gray-300 transition-colors"
              >
                Voltar
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
