import { useEffect, useState, useCallback } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ReferenceLine, ResponsiveContainer, CartesianGrid
} from 'recharts'
import { Activity, Utensils, MessageCircle, Dumbbell, Plus } from 'lucide-react'
import { getGlucoseLogs, createGlucoseEvent, getMeals } from '../lib/api'
import type {
  GlucoseLogsResponse, GlucoseEventCreate,
  ContextType, MealsListResponse,
} from '../types/clinical'

interface DashboardProps {
    userId: string;
    onLogout: () => void;
    onNavigate: (page: 'dashboard' | 'chat' | 'workout' | 'nutrition') => void;
}

// ─── helpers ────────────────────────────────────────────────

function trendLabel(t: string | undefined) {
  if (t === 'rising') return '↑ Subindo'
  if (t === 'falling') return '↓ Caindo'
  return '→ Estável'
}

function trendColor(t: string | undefined) {
  if (t === 'rising') return '#ef4444'
  if (t === 'falling') return '#60a5fa'
  return '#00e5b4'
}

function glucoseColor(v: number) {
  if (v < 70)  return '#ef4444'
  if (v > 180) return '#f97316'
  return '#00e5b4'
}

// ─── Tooltip do gráfico ─────────────────────────────────────

function ChartTooltip({ active, payload }: {
  active?: boolean
  payload?: Array<{ payload: { label: string; value_mg_dl: number } }>
}) {
  if (!active || !payload?.length) return null
  const { label, value_mg_dl } = payload[0].payload
  return (
    <div className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm z-50">
      <p className="text-gray-400 text-xs">{label}</p>
      <p style={{ color: glucoseColor(value_mg_dl) }} className="font-bold">
        {value_mg_dl} mg/dL
      </p>
    </div>
  )
}

// ─── Dialog de registro manual ───────────────────────────────

function RegisterDialog({ onDone }: { onDone: () => void }) {
  const [open, setOpen]       = useState(false)
  const [value, setValue]     = useState('')
  const [context, setContext] = useState<ContextType>('random')
  const [notes, setNotes]     = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    const num = parseFloat(value)
    if (isNaN(num) || num < 20 || num > 600) {
      setError('Valor inválido (20–600 mg/dL)')
      return
    }
    setLoading(true)
    setError('')
    try {
      const payload: GlucoseEventCreate = {
        value_mg_dl: num,
        measured_at: new Date().toISOString(),
        source: 'manual',
        context,
        notes: notes || undefined,
      }
      await createGlucoseEvent(payload)
      setValue(''); setNotes(''); setContext('random')
      setOpen(false)
      onDone()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Erro ao registrar')
    } finally {
      setLoading(false)
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
          bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400
          border border-emerald-500/30 transition-colors"
      >
        <Plus className="w-3.5 h-3.5" /> Registrar Glicemia
      </button>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-sm space-y-4">
        <h3 className="text-white font-bold text-lg">Registrar Glicemia</h3>
        <form onSubmit={submit} className="space-y-3 flex flex-col items-start w-full">

          <div className="w-full">
            <label className="text-xs text-gray-400 mb-1 block">Valor (mg/dL)</label>
            <input
              type="number" min={20} max={600}
              placeholder="Ex: 118"
              value={value}
              onChange={e => setValue(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg
                px-3 py-2 text-white text-sm placeholder-gray-600
                focus:outline-none focus:border-emerald-500"
              required
            />
          </div>

          <div className="w-full">
            <label className="text-xs text-gray-400 mb-1 block">Contexto</label>
            <select
              value={context}
              onChange={e => setContext(e.target.value as ContextType)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg
                px-3 py-2 text-white text-sm
                focus:outline-none focus:border-emerald-500"
            >
              <option value="fasting">Jejum</option>
              <option value="pre_meal">Pré-refeição</option>
              <option value="post_meal">Pós-refeição</option>
              <option value="pre_workout">Pré-treino</option>
              <option value="post_workout">Pós-treino</option>
              <option value="bedtime">Antes de dormir</option>
              <option value="random">Aleatório</option>
            </select>
          </div>

          <div className="w-full">
            <label className="text-xs text-gray-400 mb-1 block">Observação (opcional)</label>
            <input
              type="text"
              placeholder="Ex: após exercício leve"
              value={notes}
              onChange={e => setNotes(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg
                px-3 py-2 text-white text-sm placeholder-gray-600
                focus:outline-none focus:border-emerald-500"
            />
          </div>

          {error && <p className="text-red-400 text-xs w-full">{error}</p>}

          <div className="flex gap-2 pt-1 w-full">
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="flex-1 px-4 py-2 rounded-lg text-sm
                bg-gray-800 text-gray-400 hover:bg-gray-700 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 rounded-lg text-sm font-bold
                bg-emerald-500 hover:bg-emerald-600 text-black
                disabled:opacity-50 transition-colors"
            >
              {loading ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Componente principal ────────────────────────────────────

const RANGES = ['6h', '24h', '7d', '30d'] as const
type Range = typeof RANGES[number]

export default function DashboardPage({ userId, onLogout, onNavigate }: DashboardProps) {

  const [range, setRange]     = useState<Range>('6h')
  const [logs, setLogs]       = useState<GlucoseLogsResponse | null>(null)
  const [meals, setMeals]     = useState<MealsListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [apiError, setApiError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    setApiError(null)
    try {
      const [logsData, mealsData] = await Promise.all([
        getGlucoseLogs({ range, granularity: 'point' }),
        getMeals({ range: '24h' }),
      ])
      setLogs(logsData)
      setMeals(mealsData)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Erro desconhecido'
      setApiError(`Erro ao carregar dados: ${msg}`)
      console.error('[Dashboard] loadData error:', err)
    } finally {
      setLoading(false)
    }
  }, [range])

  useEffect(() => { loadData() }, [loadData])

  // ── valores derivados ──
  const events    = logs?.glucose_events ?? []
  const metrics   = logs?.metrics ?? null
  const tir       = metrics?.time_in_range ?? null
  const lastEvent = events.length > 0 ? events[events.length - 1] : null
  const lastValue = lastEvent?.value_mg_dl ?? null
  const lastTrend = lastEvent?.trend ?? 'unknown'

  const totalCarbsDay = meals?.meals?.reduce(
    (acc, m) => acc + (m.total_carbs_g ?? 0), 0
  ) ?? 0

  const chartData = events.map(e => ({
    label: new Date(e.measured_at).toLocaleTimeString('pt-BR', {
      hour: '2-digit', minute: '2-digit',
    }),
    value_mg_dl: e.value_mg_dl,
    measured_at: e.measured_at,
  }))

  // ── render ──
  return (
    <div className="min-h-screen bg-[#050A0F] flex overflow-hidden">
        
      {/* Sidebar - Preserved layout */}
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
            <Activity className="w-4 h-4" /> Dashboard
          </button>
          <button onClick={() => onNavigate('chat')}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-white/5 text-gray-400 hover:text-white transition-colors text-sm">
            <MessageCircle className="w-4 h-4" /> Assistente IA
          </button>
          <button onClick={() => onNavigate('workout')}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-white/5 text-gray-400 hover:text-white transition-colors text-sm">
            <Dumbbell className="w-4 h-4" /> Treinos
          </button>
          <button onClick={() => onNavigate('nutrition')}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-white/5 text-gray-400 hover:text-white transition-colors text-sm">
            <Utensils className="w-4 h-4 text-emerald-400" /> Nutrição
          </button>
        </nav>

        <button onClick={onLogout}
          className="w-full flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 transition-colors py-2 rounded-xl text-sm text-gray-400">
          Sair
        </button>
      </div>

      <div className="flex-1 overflow-y-auto text-white p-4 md:p-6 space-y-6">

          {/* Header */}
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <h1 className="text-lg font-bold text-white">Dashboard</h1>
              <p className="text-xs text-gray-500">
                {new Date().toLocaleDateString('pt-BR', {
                  weekday: 'long', day: '2-digit', month: 'long', year: 'numeric',
                })}
              </p>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <div className="flex gap-1">
                {RANGES.map(r => (
                  <button
                    key={r}
                    onClick={() => setRange(r)}
                    className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                      range === r
                        ? 'bg-emerald-500 text-black'
                        : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>
              <RegisterDialog onDone={loadData} />
            </div>
          </div>

          {/* Erro de API */}
          {apiError && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm">
              <strong>Erro de conexão:</strong> {apiError}
              <button
                onClick={loadData}
                className="ml-3 underline text-red-300 hover:text-white text-xs"
              >
                Tentar novamente
              </button>
            </div>
          )}

          {/* Card glicemia atual */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 text-center">
            <p className="text-xs text-gray-500 uppercase tracking-widest mb-3">
              Glicemia Atual
            </p>
            {loading ? (
              <div className="flex items-center justify-center h-20">
                <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <div>
                <div className="flex items-end justify-center gap-1">
                  <span className="text-6xl font-black" style={{ color: lastValue ? glucoseColor(lastValue) : '#00e5b4' }}>
                    {lastValue ?? '--'}
                  </span>
                  <span className="text-gray-400 text-sm mb-1 uppercase tracking-widest font-bold">mg/dL</span>
                </div>
                <p className="mt-2 text-sm font-medium" style={{ color: trendColor(lastTrend) }}>
                  {trendLabel(lastTrend)}
                </p>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Card TIR */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
              <p className="text-xs text-gray-500 uppercase tracking-widest mb-3">Na Meta (70–180)</p>
              {loading ? (
                 <div className="h-10 border border-gray-800 animate-pulse rounded"></div>
              ) : (
                 <div className="flex justify-between items-end">
                    <div className="flex items-end gap-1">
                      <span className="text-4xl font-bold">{tir?.percent_in_range !== undefined ? Math.round(tir.percent_in_range) : '--'}</span>
                      <span className="text-gray-400 mb-1 font-bold">%</span>
                    </div>
                    <span className="text-xs text-emerald-400 font-bold uppercase tracking-wider bg-emerald-500/10 px-2 py-1 rounded">meta: {'>'}70%</span>
                 </div>
              )}
            </div>
            
            {/* Card Refeições */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 flex flex-col justify-between">
               <p className="text-xs text-gray-500 uppercase tracking-widest mb-3">Refeições Hoje</p>
               {loading ? (
                 <div className="h-10 border border-gray-800 animate-pulse rounded"></div>
               ) : (
                 <div className="flex justify-between items-end">
                    <span className="text-4xl font-bold">{meals?.meals?.length ?? 0}</span>
                    <span className="text-xs text-emerald-400 tracking-wider uppercase font-bold bg-emerald-500/10 px-2 py-1 rounded">{Math.round(totalCarbsDay)}g carbs</span>
                 </div>
               )}
            </div>

            {/* Card Leituras */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 flex flex-col justify-between">
               <p className="text-xs text-gray-500 uppercase tracking-widest mb-3">Leituras {range}</p>
               {loading ? (
                 <div className="h-10 border border-gray-800 animate-pulse rounded"></div>
               ) : (
                 <div className="flex justify-between items-end">
                    <span className="text-4xl font-bold">{events.length}</span>
                    <div className="text-right text-xs text-gray-400 flex flex-col uppercase tracking-wider">
                        <span>CGM: {metrics?.distribution?.cgm_count ?? 0}</span>
                        <span>Manual: {metrics?.distribution?.manual_count ?? 0}</span>
                    </div>
                 </div>
               )}
            </div>
          </div>

          {/* Gráfico */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 mt-4">
              <p className="text-xs text-gray-500 uppercase tracking-widest mb-4">Curva Glicêmica</p>
              {loading ? (
                  <div className="h-[250px] flex items-center justify-center">
                      <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                  </div>
              ) : chartData.length === 0 ? (
                  <div className="h-[250px] flex items-center justify-center border border-dashed border-gray-800 rounded-xl text-gray-500 uppercase tracking-widest text-xs">
                      Nenhuma leitura encontrada.
                  </div>
              ) : (
                  <div className="h-[250px] w-full">
                      <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={chartData} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                              <XAxis 
                                  dataKey="label" 
                                  stroke="#4b5563" 
                                  fontSize={10} 
                                  tickMargin={10} 
                                  axisLine={false} 
                                  tickLine={false} 
                              />
                              <YAxis 
                                  stroke="#4b5563" 
                                  fontSize={10} 
                                  axisLine={false} 
                                  tickLine={false} 
                                  width={40} 
                                  domain={['dataMin - 10', 'dataMax + 10']} 
                              />
                              <Tooltip content={<ChartTooltip />} cursor={{ stroke: '#374151', strokeDasharray: '3 3' }} />
                              <ReferenceLine y={180} stroke="#f97316" strokeDasharray="3 3" strokeOpacity={0.4} />
                              <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.4} />
                              <Line 
                                  type="monotone" 
                                  dataKey="value_mg_dl" 
                                  stroke="#00e5b4" 
                                  strokeWidth={2} 
                                  dot={{ fill: '#00e5b4', r: 3, strokeWidth: 0 }} 
                                  activeDot={{ r: 5, fill: '#fff' }} 
                              />
                          </LineChart>
                      </ResponsiveContainer>
                  </div>
              )}
          </div>
      </div>
    </div>
  )
}
