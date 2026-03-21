// ============================================================
// BLOCO 6D — NutritionPage.tsx
// Arquivo: frontend/src/pages/NutritionPage.tsx
// ============================================================

import React, { useEffect, useState } from 'react'
import { getMeals, createMeal } from '../lib/api'
import type { MealOut, MealCreateRequest, MealType } from '../types/clinical'
import { LogOut, Apple, Plus, ArrowLeft } from 'lucide-react'

const MEAL_LABELS: Record<MealType, string> = {
  breakfast: 'Café da manhã',
  lunch:     'Almoço',
  dinner:    'Jantar',
  snack:     'Lanche',
  other:     'Outro',
}

const MEAL_COLORS: Record<MealType, string> = {
  breakfast: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  lunch:     'bg-green-500/20 text-green-400 border-green-500/30',
  dinner:    'bg-blue-500/20 text-blue-400 border-blue-500/30',
  snack:     'bg-purple-500/20 text-purple-400 border-purple-500/30',
  other:     'bg-gray-500/20 text-gray-400 border-gray-500/30',
}

function formatDatetimeLocal(iso: string) {
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

// ---- Formulário de nova refeição ----
function NewMealForm({ onCreated, onCancel }: { onCreated: () => void, onCancel: () => void }) {
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState<string | null>(null)

  const [name, setName]               = useState('')
  const [mealType, setMealType]       = useState<MealType>('snack')
  const [carbs, setCarbs]             = useState('')
  const [protein, setProtein]         = useState('')
  const [fat, setFat]                 = useState('')
  const [notes, setNotes]             = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const payload: MealCreateRequest = {
      name:            name || undefined,
      meal_type:       mealType,
      eaten_at:        new Date().toISOString(),
      total_carbs_g:   carbs   ? parseFloat(carbs)   : undefined,
      total_protein_g: protein ? parseFloat(protein) : undefined,
      total_fat_g:     fat     ? parseFloat(fat)     : undefined,
      estimated:       true,
      notes:           notes || undefined,
    }

    try {
      await createMeal(payload)
      setName(''); setCarbs(''); setProtein(''); setFat(''); setNotes('')
      onCreated()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar refeição')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white/5 border border-white/10 p-5 rounded-2xl flex flex-col gap-4">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-white font-medium">Registrar Nova Refeição</h3>
        <button type="button" onClick={onCancel} className="text-gray-400 hover:text-white text-sm">Cancelar</button>
      </div>

      {error && <div className="text-sm text-red-400 bg-red-500/10 p-3 rounded-lg border border-red-500/20">{error}</div>}
      
      <div className="flex flex-col gap-3">
        <input 
          type="text" 
          placeholder="Nome (Ex: Pão com ovo)" 
          className="bg-black/20 border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-cyan-500 text-sm"
          value={name} 
          onChange={e => setName(e.target.value)} 
        />
        
        <select 
          className="bg-[#0f172a] border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-cyan-500 text-sm"
          value={mealType} 
          onChange={e => setMealType(e.target.value as MealType)}
        >
          {Object.entries(MEAL_LABELS).map(([val, label]) => (
            <option key={val} value={val}>{label}</option>
          ))}
        </select>
        
        <div className="grid grid-cols-3 gap-3">
          <input 
            type="number" step="0.1" placeholder="Carbos (g)" 
            className="bg-black/20 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500 text-sm"
            value={carbs} onChange={e => setCarbs(e.target.value)} 
          />
          <input 
            type="number" step="0.1" placeholder="Prot. (g)" 
            className="bg-black/20 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500 text-sm"
            value={protein} onChange={e => setProtein(e.target.value)} 
          />
          <input 
            type="number" step="0.1" placeholder="Gord. (g)" 
            className="bg-black/20 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500 text-sm"
            value={fat} onChange={e => setFat(e.target.value)} 
          />
        </div>
        
        <textarea 
          placeholder="Notas adicionais..." 
          className="bg-black/20 border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-cyan-500 text-sm h-20 resize-none"
          value={notes} 
          onChange={e => setNotes(e.target.value)} 
        />
      </div>

      <button disabled={loading} type="submit" className="w-full bg-cyan-500 hover:bg-cyan-600 text-black font-bold py-3 rounded-xl transition-colors mt-2 text-sm disabled:opacity-50">
        {loading ? 'Salvando...' : 'Salvar Refeição'}
      </button>
    </form>
  )
}

interface NutritionProps {
  userId: string;
  onNavigate: (page: 'dashboard' | 'chat' | 'workout' | 'nutrition') => void;
}

export default function NutritionPage({ onNavigate }: NutritionProps) {
  const [meals, setMeals] = useState<MealOut[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  async function loadMeals() {
    setLoading(true)
    try {
      const res = await getMeals({ range: '30d' })
      setMeals(res.meals || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadMeals()
  }, [])

  return (
    <div className="min-h-screen bg-[#050A0F] flex flex-col pt-4">
      <div className="px-6 py-4 flex items-center justify-between border-b border-white/5 max-w-3xl mx-auto w-full">
        <div className="flex items-center gap-3">
          <button onClick={() => onNavigate('dashboard')} className="p-2 border border-white/10 rounded-xl hover:bg-white/5 transition-colors">
            <ArrowLeft className="w-4 h-4 text-gray-400" />
          </button>
          <div className="w-10 h-10 bg-green-500/10 rounded-xl flex items-center justify-center">
            <Apple className="w-5 h-5 text-green-400" />
          </div>
          <div>
            <h1 className="text-white font-bold text-lg leading-tight">Nutrição</h1>
            <p className="text-xs text-gray-500">Acompanhamento e diário de refeições</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6 pb-24">
        <div className="max-w-3xl mx-auto space-y-6">
          
          <div className="flex justify-between items-center">
            <h2 className="text-sm text-gray-500 uppercase tracking-widest">Suas Refeições</h2>
            {!showForm && (
              <button onClick={() => setShowForm(true)} className="flex items-center gap-2 bg-green-500/10 text-green-400 border border-green-500/20 px-3 py-1.5 rounded-lg text-sm hover:bg-green-500/20 transition-colors">
                <Plus className="w-4 h-4" /> Nova
              </button>
            )}
          </div>

          {showForm && (
            <NewMealForm 
              onCreated={() => { setShowForm(false); loadMeals(); }} 
              onCancel={() => setShowForm(false)} 
            />
          )}

          {loading ? (
            <div className="text-center py-10 text-gray-500 text-sm animate-pulse">Carregando diário...</div>
          ) : meals.length === 0 ? (
            <div className="bg-white/3 border border-white/5 rounded-2xl p-8 text-center">
              <Apple className="w-8 h-8 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400 text-sm mb-4">Nenhuma refeição registrada ultimamente.</p>
              {!showForm && (
                <button onClick={() => setShowForm(true)} className="text-green-400 underline text-sm">Registre a primeira do dia</button>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {meals.map(meal => (
                <div key={meal.id} className="bg-white/5 border border-white/10 p-4 rounded-xl flex flex-col gap-3">
                  <div className="flex justify-between items-start">
                    <div className="flex flex-col">
                      <span className="text-white font-medium">{meal.name || 'Refeição Sem Nome'}</span>
                      <span className="text-xs text-gray-500">{formatDatetimeLocal(meal.eaten_at)}</span>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${MEAL_COLORS[meal.meal_type]}`}>
                      {MEAL_LABELS[meal.meal_type]}
                    </span>
                  </div>
                  {(meal.total_carbs_g || meal.total_protein_g || meal.total_fat_g) && (
                    <div className="flex gap-4 border-t border-white/5 pt-3 mt-1">
                      <div className="flex flex-col">
                        <span className="text-[10px] text-gray-500 uppercase">Carbos</span>
                        <span className="text-sm font-bold text-white">{meal.total_carbs_g ?? '--'}g</span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-[10px] text-gray-500 uppercase">Proteínas</span>
                        <span className="text-sm font-bold text-white">{meal.total_protein_g ?? '--'}g</span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-[10px] text-gray-500 uppercase">Gorduras</span>
                        <span className="text-sm font-bold text-white">{meal.total_fat_g ?? '--'}g</span>
                      </div>
                    </div>
                  )}
                  {meal.notes && (
                    <p className="text-xs text-gray-400 italic">"{meal.notes}"</p>
                  )}
                </div>
              ))}
            </div>
          )}

        </div>
      </div>
    </div>
  )
}
