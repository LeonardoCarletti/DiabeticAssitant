import { useState, useEffect } from 'react';
import { Activity, Heart, ArrowLeft, Plus, TrendingUp } from 'lucide-react';

interface VitalsPageProps {
  userId: string;
  onNavigate: (page: string) => void;
}

interface VitalRecord {
  id: string;
  type: string;
  value: number;
  unit: string;
  recorded_at: string;
  notes?: string;
}

const API_BASE = import.meta.env.VITE_API_URL || 'https://diabeticassistant-backend.vercel.app';

async function getVitals(userId: string): Promise<VitalRecord[]> {
  const token = localStorage.getItem('da_token') || '';
  const res = await fetch(`${API_BASE}/api/vitals?user_id=${userId}&limit=20`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.vitals || data || [];
}

async function createVital(payload: Omit<VitalRecord, 'id' | 'recorded_at'>): Promise<void> {
  const token = localStorage.getItem('da_token') || '';
  await fetch(`${API_BASE}/api/vitals`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export default function VitalsPage({ userId, onNavigate }: VitalsPageProps) {
  const [vitals, setVitals] = useState<VitalRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [type, setType] = useState('blood_pressure');
  const [value, setValue] = useState('');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    const data = await getVitals(userId);
    setVitals(data);
    setLoading(false);
  };

  useEffect(() => { load(); }, [userId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    await createVital({ type, value: parseFloat(value), unit: '', notes });
    setValue(''); setNotes(''); setShowForm(false);
    setSaving(false);
    load();
  };

  const vitalTypes = [
    { value: 'blood_pressure', label: 'Pressão Arterial', unit: 'mmHg', icon: Heart },
    { value: 'heart_rate', label: 'Freq. Cardíaca', unit: 'bpm', icon: Activity },
    { value: 'weight', label: 'Peso', unit: 'kg', icon: TrendingUp },
    { value: 'temperature', label: 'Temperatura', unit: '°C', icon: Activity },
    { value: 'oxygen_saturation', label: 'Saturação O2', unit: '%', icon: Heart },
    { value: 'hba1c', label: 'HbA1c', unit: '%', icon: TrendingUp },
  ];

  return (
    <div className="min-h-screen bg-[#050A0F] text-white">
      <div className="max-w-2xl mx-auto p-4">
        <div className="flex items-center gap-3 mb-6 pt-4">
          <button onClick={() => onNavigate('dashboard')} className="text-gray-400 hover:text-white">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <Heart className="w-6 h-6 text-red-400" />
          <h1 className="text-xl font-bold">Sinais Vitais</h1>
          <button onClick={() => setShowForm(!showForm)}
            className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30">
            <Plus className="w-3.5 h-3.5" /> Registrar
          </button>
        </div>

        {showForm && (
          <form onSubmit={handleSubmit} className="bg-gray-900 border border-gray-800 rounded-2xl p-5 mb-6 space-y-3">
            <h3 className="font-bold text-sm">Novo Registro de Sinal Vital</h3>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Tipo</label>
              <select value={type} onChange={e => setType(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white">
                {vitalTypes.map(t => <option key={t.value} value={t.value}>{t.label} ({t.unit})</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Valor</label>
              <input type="number" step="0.1" value={value} onChange={e => setValue(e.target.value)}
                placeholder="Ex: 120" required
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white" />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Observação</label>
              <input type="text" value={notes} onChange={e => setNotes(e.target.value)}
                placeholder="Opcional"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white" />
            </div>
            <div className="flex gap-2">
              <button type="button" onClick={() => setShowForm(false)}
                className="flex-1 py-2 rounded-lg text-sm bg-gray-800 text-gray-400">Cancelar</button>
              <button type="submit" disabled={saving}
                className="flex-1 py-2 rounded-lg text-sm font-bold bg-red-500 hover:bg-red-600 text-white disabled:opacity-50">
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </form>
        )}

        <div className="space-y-3">
          {loading ? (
            <div className="flex justify-center py-10">
              <div className="w-8 h-8 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : vitals.length === 0 ? (
            <div className="text-center py-10 text-gray-500 text-sm">
              Nenhum sinal vital registrado ainda. Registre seu primeiro agora!
            </div>
          ) : (
            vitals.map((v, i) => {
              const vt = vitalTypes.find(t => t.value === v.type);
              return (
                <div key={v.id || i} className="bg-gray-900 border border-gray-800 rounded-2xl p-4 flex items-center justify-between">
                  <div>
                    <p className="font-bold text-sm">{vt?.label || v.type}</p>
                    <p className="text-xs text-gray-500">{new Date(v.recorded_at).toLocaleString('pt-BR')}</p>
                    {v.notes && <p className="text-xs text-gray-400 mt-1">{v.notes}</p>}
                  </div>
                  <div className="text-right">
                    <span className="text-2xl font-black text-red-400">{v.value}</span>
                    <span className="text-xs text-gray-400 ml-1">{vt?.unit || v.unit}</span>
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
