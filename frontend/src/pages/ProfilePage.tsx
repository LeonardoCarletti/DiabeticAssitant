import { useState, useEffect } from 'react';
import { User, ArrowLeft, Save } from 'lucide-react';

interface ProfilePageProps {
  userId: string;
  onNavigate: (page: string) => void;
  onLogout: () => void;
}

interface UserProfile {
  name?: string;
  phone?: string;
  diabetes_type?: string;
  birth_year?: number;
  target_glucose_min?: number;
  target_glucose_max?: number;
  insulin_type?: string;
  physician_name?: string;
  notes?: string;
}

const API_BASE = import.meta.env.VITE_API_URL || 'https://diabeticassistant-backend.vercel.app';

async function getProfile(userId: string): Promise<UserProfile> {
  const token = localStorage.getItem('da_token') || '';
  const res = await fetch(`${API_BASE}/api/profile?user_id=${userId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return {};
  return await res.json();
}

async function updateProfile(userId: string, data: UserProfile): Promise<void> {
  const token = localStorage.getItem('da_token') || '';
  await fetch(`${API_BASE}/api/profile`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, ...data }),
  });
}

export default function ProfilePage({ userId, onNavigate, onLogout }: ProfilePageProps) {
  const [profile, setProfile] = useState<UserProfile>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getProfile(userId).then(p => { setProfile(p); setLoading(false); });
  }, [userId]);

  const handleChange = (field: keyof UserProfile, value: string | number) => {
    setProfile(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    await updateProfile(userId, profile);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  if (loading) return (
    <div className="min-h-screen bg-[#050A0F] flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="min-h-screen bg-[#050A0F] text-white">
      <div className="max-w-2xl mx-auto p-4">
        <div className="flex items-center gap-3 mb-6 pt-4">
          <button onClick={() => onNavigate('dashboard')} className="text-gray-400 hover:text-white">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <User className="w-6 h-6 text-cyan-400" />
          <h1 className="text-xl font-bold">Meu Perfil</h1>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4 mb-4 text-center">
          <div className="w-16 h-16 rounded-full bg-cyan-500/20 flex items-center justify-center mx-auto mb-3">
            <User className="w-8 h-8 text-cyan-400" />
          </div>
          <p className="text-sm text-gray-400">ID do usuário</p>
          <p className="text-xs text-gray-500 font-mono">{userId}</p>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-4">
            <h3 className="font-bold text-sm text-gray-300">Informações Pessoais</h3>
            
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Nome</label>
              <input type="text" value={profile.name || ''}
                onChange={e => handleChange('name', e.target.value)}
                placeholder="Seu nome completo"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white" />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Telefone</label>
              <input type="tel" value={profile.phone || ''}
                onChange={e => handleChange('phone', e.target.value)}
                placeholder="11988024265"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white" />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Ano de Nascimento</label>
              <input type="number" value={profile.birth_year || ''}
                onChange={e => handleChange('birth_year', parseInt(e.target.value))}
                placeholder="1990"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white" />
            </div>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-4">
            <h3 className="font-bold text-sm text-gray-300">Saúde & Diabético</h3>
            
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Tipo de Diabetes</label>
              <select value={profile.diabetes_type || ''}
                onChange={e => handleChange('diabetes_type', e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white">
                <option value="">Selecione...</option>
                <option value="type1">Tipo 1</option>
                <option value="type2">Tipo 2</option>
                <option value="gestational">Gestacional</option>
                <option value="lada">LADA</option>
                <option value="mody">MODY</option>
                <option value="prediabetes">Pré-diabético</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Glicemia Alvo Mín</label>
                <input type="number" value={profile.target_glucose_min || ''}
                  onChange={e => handleChange('target_glucose_min', parseInt(e.target.value))}
                  placeholder="70"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white" />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Glicemia Alvo Máx</label>
                <input type="number" value={profile.target_glucose_max || ''}
                  onChange={e => handleChange('target_glucose_max', parseInt(e.target.value))}
                  placeholder="180"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white" />
              </div>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Tipo de Insulina</label>
              <input type="text" value={profile.insulin_type || ''}
                onChange={e => handleChange('insulin_type', e.target.value)}
                placeholder="Ex: Lantus + Novorapid"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white" />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Médico Responsável</label>
              <input type="text" value={profile.physician_name || ''}
                onChange={e => handleChange('physician_name', e.target.value)}
                placeholder="Dr. Nome"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white" />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Observações</label>
              <textarea rows={3} value={profile.notes || ''}
                onChange={e => handleChange('notes', e.target.value)}
                placeholder="Alérgico a..., usa sensor CGM..."
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white resize-none" />
            </div>
          </div>

          <button type="submit" disabled={saving}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-bold bg-cyan-500 hover:bg-cyan-600 text-black disabled:opacity-50 transition-colors">
            <Save className="w-4 h-4" />
            {saving ? 'Salvando...' : saved ? 'Salvo!' : 'Salvar Perfil'}
          </button>
        </form>

        <button onClick={onLogout}
          className="w-full mt-4 py-3 rounded-xl text-sm text-gray-400 bg-white/5 hover:bg-white/10 transition-colors">
          Sair da conta
        </button>
      </div>
    </div>
  );
}
