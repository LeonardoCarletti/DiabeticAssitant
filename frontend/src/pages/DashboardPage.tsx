// ============================================================
// BLOCO 7 — DashboardPage.tsx com dados reais
// Arquivo: frontend/src/pages/DashboardPage.tsx
// ============================================================

import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ReferenceLine, ResponsiveContainer, CartesianGrid,
} from 'recharts'
import { Activity, Utensils, MessageCircle, Dumbbell, Plus } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import {
  Dialog, DialogContent, DialogHeader,
  DialogTitle, DialogTrigger,
} from '../components/ui/dialog'
import { Input } from '../components/ui/input'
import {
  Select, SelectContent, SelectItem,
  SelectTrigger, SelectValue,
} from '../components/ui/select'
import { getGlucoseLogs, createGlucoseEvent, getMeals } from '../lib/api'
import type {
  GlucoseLogsResponse, GlucoseEventCreate,
  ContextType, MealsListResponse,
} from '../types/clinical'

// ---- helpers ----

function trendArrow(trend: string) {
  if (trend === 'rising')  return '↑'
  if (trend === 'falling') return '↓'
  return '→'
}

function trendColor(trend: string) {
  if (trend === 'rising')  return 'text-red-400'
  if (trend === 'falling') return 'text-blue-400'
  return 'text-emerald-400'
}

function glicemiaColor(val: number) {
  if (val < 70)  return '#ef4444'  // vermelho — hipo
  if (val > 180) return '#f97316'  // laranja — hiper
  return '#00e5b4'                 // verde neon — ok
}

function tirBadgeVariant(pct: number): string {
  if (pct >= 70) return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
  if (pct >= 50) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
  return 'bg-red-500/20 text-red-400 border-red-500/30'
}

// ---- Tooltip customizado para o gráfico ----

function CustomTooltip({ active, payload }: {
  active?: boolean
  payload?: Array<{ payload: { measured_at: string; value_mg_dl: number } }>
}) {
  if (!active || !payload?.length) return null
  const { measured_at, value_mg_dl } = payload[0].payload
  const time = new Date(measured_at).toLocaleTimeString('pt-BR', {
    hour: '2-digit', minute: '2-digit',
  })
  return (
    <div className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm">
      <p className="text-gray-400">{time}</p>
      <p style={{ color: glicemiaColor(value_mg_dl) }} className="font-bold">
        {value_mg_dl} mg/dL
      </p>
    </div>
  )
}

// ---- Formulário de registro manual ----

function RegisterGlucoseDialog({ onRegistered }: { onRegistered: () => void }) {
  const [open, setOpen]       = useState(false)
  const [value, setValue]     = useState('')
  const [context, setContext] = useState<ContextType>('random')
  const [notes, setNotes]     = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const num = parseFloat(value)
    if (isNaN(num) || num < 20 || num > 600) {
      setError('Valor inválido. Use entre 20 e 600 mg/dL.')
      return
    }
    setLoading(true)
    setError(null)
    const payload: GlucoseEventCreate = {
      value_mg_dl: num,
      measured_at: new Date().toISOString(),
      source:      'manual',
      context,
      notes:       notes || undefined,
    }
    try {
      await createGlucoseEvent(payload)
      setValue(''); setNotes(''); setContext('random')
      setOpen(false)
      onRegistered()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Erro ao registrar')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          size="sm"
          className="bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30"
        >
          <Plus className="w-4 h-4 mr-1" /> Registrar Glicemia
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-gray-900 border-gray-700 text-white max-w-sm">
        <DialogHeader>
          <DialogTitle className="text-emerald-400">Registrar Glicemia Manual</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Valor (mg/dL)</label>
            <Input
              type="number"
              min={20} max={600}
              placeholder="Ex: 118"
              value={value}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setValue(e.target.value)}
              className="bg-gray-800 border-gray-700 text-white"
              required
            />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Contexto</label>
            <Select value={context} onValueChange={(v: string) => setContext(v as ContextType)}>
              <SelectTrigger className="bg-gray-800 border-gray-700 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-900 border-gray-700">
                <SelectItem value="fasting">Jejum</SelectItem>
                <SelectItem value="pre_meal">Pré-refeição</SelectItem>
                <SelectItem value="post_meal">Pós-refeição</SelectItem>
                <SelectItem value="pre_workout">Pré-treino</SelectItem>
                <SelectItem value="post_workout">Pós-treino</SelectItem>
                <SelectItem value="bedtime">Antes de dormir</SelectItem>
                <SelectItem value="random">Aleatório</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Observação (opcional)</label>
            <Input
              placeholder="Ex: após exercício leve"
              value={notes}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNotes(e.target.value)}
              className="bg-gray-800 border-gray-700 text-white"
            />
          </div>
          {error && <p className="text-red-400 text-xs">{error}</p>}
          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-emerald-500 hover:bg-emerald-600 text-black font-bold"
          >
            {loading ? 'Salvando...' : 'Salvar'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ---- Componente principal ----

interface DashboardProps {
    userId: string;
    onLogout: () => void;
    onNavigate: (page: 'dashboard' | 'chat' | 'workout' | 'nutrition') => void;
}

export default function DashboardPage({ userId, onLogout, onNavigate }: DashboardProps) {

  const [logs, setLogs]       = useState<GlucoseLogsResponse | null>(null)
  const [meals, setMeals]     = useState<MealsListResponse | null>(null)
  const [range, setRange]     = useState<'6h' | '24h' | '7d' | '30d'>('6h')
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [logsData, mealsData] = await Promise.all([
        getGlucoseLogs({ range, granularity: 'point' }),
        getMeals({ range: '24h' }),
      ])
      setLogs(logsData)
      setMeals(mealsData)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar dados')
    } finally {
      setLoading(false)
    }
  }, [range])

  useEffect(() => { loadData() }, [loadData])

  // --- valores derivados ---
  const events       = logs?.glucose_events ?? []
  const metrics      = logs?.metrics
  const lastEvent    = events[events.length - 1]
  const lastValue    = lastEvent?.value_mg_dl ?? null
  const lastTrend    = lastEvent?.trend ?? 'unknown'
  const tir          = metrics?.time_in_range
  const totalCarbsDay = meals?.meals.reduce((acc, m) => acc + (m.total_carbs_g ?? 0), 0) ?? 0
  const mealsCount   = meals?.meals.length ?? 0

  // dados para o gráfico
  const chartData = events.map(e => ({
    measured_at: e.measured_at,
    value_mg_dl: e.value_mg_dl,
    label: new Date(e.measured_at).toLocaleTimeString('pt-BR', {
      hour: '2-digit', minute: '2-digit',
    }),
  }))

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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white">Dashboard</h1>
          <p className="text-xs text-gray-400">
            {new Date().toLocaleDateString('pt-BR', {
              weekday: 'long', day: '2-digit', month: 'long',
            })}
          </p>
        </div>
        <div className="flex gap-4 items-center flex-wrap">
          {/* seletor de range */}
          <div className="flex bg-white/5 rounded p-1">
            {(['6h','24h','7d','30d'] as const).map(r => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={`px-3 py-1 rounded text-xs transition-colors ${
                  range === r
                    ? 'bg-cyan-500/20 text-cyan-400 font-medium border border-cyan-500/30'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {r}
              </button>
            ))}
          </div>
          <RegisterGlucoseDialog onRegistered={loadData} />
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Metric Cards Top */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Card 1 — Atual */}
        <Card className="bg-white/5 border-white/5">
          <CardContent className="p-5 flex flex-col justify-between h-full">
            <p className="text-xs text-gray-400 uppercase tracking-widest flex items-center gap-1">
              <Activity className="w-3 h-3 text-cyan-400" /> Atual
            </p>
            {loading ? (
               <div className="h-16 flex items-center animate-pulse text-gray-500 tracking-widest text-2xl">...</div>
            ) : (
              <div className="mt-2 text-left">
                <span className="text-5xl font-bold" style={{ color: lastValue ? glicemiaColor(lastValue) : '#00e5b4' }}>
                  {lastValue ?? '--'}
                </span>
                <span className="text-gray-400 text-sm ml-1">mg/dL</span>
                <div className={`mt-1 text-xs font-medium ${trendColor(lastTrend)}`}>
                  {trendArrow(lastTrend)} {lastTrend === 'stable' ? 'estável' : lastTrend === 'rising' ? 'subindo' : lastTrend === 'falling' ? 'caindo' : 'desconhecida'}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Card 2 — TIR (Time in Range) */}
        <Card className="bg-white/5 border-white/5">
          <CardContent className="p-5 flex gap-4 h-full">
            <div className="flex-1 flex flex-col justify-between">
               <p className="text-xs text-gray-400 uppercase tracking-widest mb-1">Na Meta (70–180)</p>
               {loading ? (
                 <div className="h-16 flex items-center animate-pulse text-gray-500 text-2xl">...</div>
               ) : (
                 <>
                   <div className="flex items-end gap-1">
                     <span className="text-4xl font-bold text-white">
                       {tir?.percent_in_range !== undefined ? Math.round(tir.percent_in_range) : '--'}
                     </span>
                     <span className="text-gray-400 mb-1">%</span>
                   </div>
                   {tir && (
                     <Badge className={`mt-1 w-fit text-[10px] uppercase ${tirBadgeVariant(tir.percent_in_range)}`}>
                       {tir.percent_in_range >= 70 ? 'Excelente' : tir.percent_in_range >= 50 ? 'Atenção' : 'Abaixo do esperado'}
                     </Badge>
                   )}
                 </>
               )}
            </div>
            {/* Split Barras Hipos/Hipers */}
            {tir && !loading && (
               <div className="w-16 flex flex-col gap-1 justify-center text-[10px] text-right">
                 <div className="flex items-center justify-end gap-1 text-red-400">
                    <span>{Math.round(tir.percent_below_range)}%</span>
                    <div className="w-1.5 h-1.5 rounded-full bg-red-400" />
                 </div>
                 <div className="flex items-center justify-end gap-1 text-emerald-400">
                    <span>{Math.round(tir.percent_in_range)}%</span>
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                 </div>
                 <div className="flex items-center justify-end gap-1 text-orange-400">
                    <span>{Math.round(tir.percent_above_range)}%</span>
                    <div className="w-1.5 h-1.5 rounded-full bg-orange-400" />
                 </div>
               </div>
            )}
          </CardContent>
        </Card>

        {/* Card 3 — Resumo Nutrição Hoje */}
        <Card className="bg-white/5 border-white/5">
          <CardContent className="p-5 flex flex-col justify-between h-full">
            <p className="text-xs text-gray-400 uppercase tracking-widest flex items-center gap-1">
              <Utensils className="w-3 h-3 text-emerald-400" /> Hoje
            </p>
            {loading ? (
                <div className="h-16 flex items-center animate-pulse text-gray-500 text-2xl">...</div>
            ) : (
                <div className="mt-2 flex items-end justify-between">
                    <div>
                        <p className="text-3xl font-bold text-white">{mealsCount}</p>
                        <p className="text-xs text-gray-400">Refeições</p>
                    </div>
                    <div className="text-right">
                        <p className="text-2xl font-bold text-emerald-400">{Math.round(totalCarbsDay)} <span className="text-xs text-gray-500 font-normal">g</span></p>
                        <p className="text-xs text-gray-400 border-t border-white/10 pt-1 mt-1">Carboidratos</p>
                    </div>
                </div>
            )}
          </CardContent>
        </Card>

        {/* Card 4 — Leituras */}
        <Card className="bg-white/5 border-white/5">
          <CardContent className="p-5 flex flex-col justify-between h-full">
             <p className="text-xs text-gray-400 uppercase tracking-widest">Leituras</p>
             {loading ? (
                 <div className="h-16 flex items-center animate-pulse text-gray-500 text-2xl">...</div>
             ) : (
                 <div className="mt-2">
                     <div className="flex justify-between items-end border-b border-white/5 pb-2 mb-2">
                         <span className="text-sm text-gray-400">Sensores (CGM)</span>
                         <span className="text-lg font-bold text-white">{metrics?.distribution?.cgm_count ?? 0}</span>
                     </div>
                     <div className="flex justify-between items-end">
                         <span className="text-sm text-gray-400">Pontas de Dedo</span>
                         <span className="text-lg font-bold text-emerald-400">{metrics?.distribution?.manual_count ?? 0}</span>
                     </div>
                 </div>
             )}
          </CardContent>
        </Card>

      </div>

      {/* Gráfico histórico Recharts */}
      <Card className="bg-white/5 border-white/5 mt-6">
        <CardHeader className="pb-2 border-b border-white/5 mb-4 px-6 flex flex-row items-center justify-between">
          <CardTitle className="text-sm text-gray-400 uppercase tracking-widest">
            Curva de Glicose ({range})
          </CardTitle>
          {loading && <div className="text-[10px] text-gray-500 animate-pulse uppercase">Sincronizando...</div>}
        </CardHeader>
        <CardContent className="px-6 pb-6">
          {chartData.length === 0 && !loading ? (
            <div className="h-56 flex flex-col items-center justify-center text-gray-500 space-y-2 border border-dashed border-white/10 rounded-xl">
               <Activity className="w-8 h-8 text-gray-600 mb-1" />
               <p className="text-sm">Nenhuma leitura encontrada neste período.</p>
               <RegisterGlucoseDialog onRegistered={loadData} />
            </div>
          ) : (
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer>
                <LineChart data={chartData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                  <XAxis
                    dataKey="label"
                    stroke="#ffffff40"
                    fontSize={10}
                    tickMargin={10}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="#ffffff40"
                    fontSize={10}
                    tickLine={false}
                    axisLine={false}
                    width={40}
                    domain={['dataMin - 20', 'dataMax + 20']}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <ReferenceLine y={180} stroke="#f97316" strokeDasharray="3 3" strokeOpacity={0.4} />
                  <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.4} />
                  <Line
                    type="monotone"
                    dataKey="value_mg_dl"
                    stroke="#00e5b4"
                    strokeWidth={3}
                    dot={{ fill: '#00e5b4', r: 3, strokeWidth: 0 }}
                    activeDot={{ r: 5, fill: '#fff' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
      </div>
    </div>
  )
}
