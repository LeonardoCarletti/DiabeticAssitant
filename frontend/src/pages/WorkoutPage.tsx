import { useState } from 'react';
import { ArrowLeft, Dumbbell, Play, CheckCircle, Zap, Droplet, MessageSquare, RefreshCw } from 'lucide-react';
import { generateWorkout } from '../lib/api';

interface Exercise {
  name: string;
  sets: string;
  reps: string;
  rest: string;
  notes?: string;
}

interface WorkoutPlan {
  title: string;
  duration: string;
  level: string;
  glucose_recommendation: string;
  exercises: Exercise[];
  coach_tip: string;
}

interface WorkoutPageProps {
  userId: string;
  onNavigate: (page: 'dashboard' | 'chat' | 'workout') => void;
}

export default function WorkoutPage({ userId, onNavigate }: WorkoutPageProps) {
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState({ level: 'intermediario', goal: 'hipertrofia', glucose: '120' });
  const [completedExs, setCompletedExs] = useState<Set<number>>(new Set());

  async function handleGenerate() {
    setLoading(true);
    setCompletedExs(new Set());
    try {
      const result = await generateWorkout(profile);
      setPlan(result);
    } catch (err) {
      console.error('Erro ao gerar treino:', err);
    } finally {
      setLoading(false);
    }
  }

  function toggleExercise(i: number) {
    setCompletedExs(prev => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  }

  const progress = plan ? Math.round((completedExs.size / plan.exercises.length) * 100) : 0;

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
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-white/5 text-gray-400 hover:text-white transition-colors text-sm">
            <MessageSquare className="w-4 h-4" /> Assistente IA
          </button>
          <button onClick={() => onNavigate('workout')}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl bg-purple-500/10 text-purple-400 text-sm font-medium">
            <Dumbbell className="w-4 h-4" /> Treinos
          </button>
        </nav>
        <div className="mt-auto">
          <p className="text-xs text-gray-600 text-center">USER: {userId.slice(0, 8)}</p>
        </div>
      </div>

      {/* Main */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b border-white/5 px-6 py-4 flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-purple-500/10 flex items-center justify-center">
            <Dumbbell className="w-4 h-4 text-purple-400" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white">Treino Personalizado por IA</h1>
            <p className="text-xs text-gray-500">Gerado de acordo com sua glicemia e objetivos</p>
          </div>
        </div>

        <div className="flex-1 p-6 overflow-y-auto">
          <div className="max-w-3xl mx-auto space-y-5">

            {/* Config Form */}
            {!plan && (
              <div className="bg-white/3 border border-white/5 rounded-2xl p-6 space-y-4">
                <h2 className="text-white font-bold text-sm">Configure seu treino</h2>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs text-gray-500 uppercase tracking-widest block mb-2">Nivel</label>
                    <select
                      value={profile.level}
                      onChange={e => setProfile(p => ({...p, level: e.target.value}))}
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-purple-400/50">
                      <option value="iniciante">Iniciante</option>
                      <option value="intermediario">Intermediario</option>
                      <option value="avancado">Avancado</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 uppercase tracking-widest block mb-2">Objetivo</label>
                    <select
                      value={profile.goal}
                      onChange={e => setProfile(p => ({...p, goal: e.target.value}))}
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-purple-400/50">
                      <option value="hipertrofia">Hipertrofia</option>
                      <option value="emagrecimento">Emagrecimento</option>
                      <option value="resistencia">Resistencia</option>
                      <option value="manutencao">Manutencao</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 uppercase tracking-widest block mb-2">Glicemia atual</label>
                    <input
                      type="number"
                      value={profile.glucose}
                      onChange={e => setProfile(p => ({...p, glucose: e.target.value}))}
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-purple-400/50"
                      placeholder="mg/dL"
                    />
                  </div>
                </div>
                <button
                  onClick={handleGenerate}
                  disabled={loading}
                  className="w-full flex items-center justify-center gap-2 bg-purple-500 hover:bg-purple-400 disabled:opacity-40 text-white font-bold py-3 rounded-xl transition-colors">
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
                  {loading ? 'Gerando treino...' : 'Gerar Treino com IA'}
                </button>
              </div>
            )}

            {/* Workout Plan */}
            {plan && (
              <>
                {/* Plan Header */}
                <div className="bg-purple-500/5 border border-purple-500/20 rounded-2xl p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h2 className="text-white font-bold text-lg">{plan.title}</h2>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-xs text-gray-500">{plan.duration}</span>
                        <span className="text-xs text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded-full">{plan.level}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => { setPlan(null); setCompletedExs(new Set()); }}
                      className="text-xs text-gray-500 hover:text-white bg-white/5 hover:bg-white/10 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1">
                      <RefreshCw className="w-3 h-3" /> Novo
                    </button>
                  </div>

                  {/* Progress bar */}
                  <div className="mb-3">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>Progresso</span>
                      <span>{completedExs.size}/{plan.exercises.length} exercicios</span>
                    </div>
                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-purple-500 rounded-full transition-all duration-500"
                        style={{width: `${progress}%`}}
                      />
                    </div>
                  </div>

                  {/* Glucose tip */}
                  <div className="bg-cyan-500/5 border border-cyan-500/20 rounded-xl p-3">
                    <p className="text-xs text-cyan-400 font-bold mb-1">RECOMENDACAO DE GLICEMIA</p>
                    <p className="text-xs text-gray-300">{plan.glucose_recommendation}</p>
                  </div>
                </div>

                {/* Exercises */}
                <div className="space-y-3">
                  {plan.exercises.map((ex, i) => (
                    <div
                      key={i}
                      onClick={() => toggleExercise(i)}
                      className={`border rounded-xl p-4 cursor-pointer transition-all ${
                        completedExs.has(i)
                          ? 'bg-green-500/5 border-green-500/30'
                          : 'bg-white/3 border-white/5 hover:border-purple-500/30'
                      }`}>
                      <div className="flex items-start gap-3">
                        <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 ${
                          completedExs.has(i) ? 'bg-green-500/20' : 'bg-purple-500/10'
                        }`}>
                          {completedExs.has(i)
                            ? <CheckCircle className="w-4 h-4 text-green-400" />
                            : <Play className="w-4 h-4 text-purple-400" />}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <h3 className={`text-sm font-bold ${
                              completedExs.has(i) ? 'text-green-400 line-through' : 'text-white'
                            }`}>{ex.name}</h3>
                            <span className="text-xs text-gray-600">{i + 1}/{plan.exercises.length}</span>
                          </div>
                          <div className="flex gap-3 mt-1">
                            <span className="text-xs text-purple-400">{ex.sets} series</span>
                            <span className="text-xs text-gray-500">{ex.reps} reps</span>
                            <span className="text-xs text-gray-600">Descanso: {ex.rest}</span>
                          </div>
                          {ex.notes && (
                            <p className="text-xs text-gray-500 mt-1">{ex.notes}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Coach tip */}
                <div className="bg-white/3 border border-white/5 rounded-xl p-4">
                  <p className="text-xs text-gray-500 uppercase tracking-widest mb-2">Dica do Coach</p>
                  <p className="text-sm text-gray-300">{plan.coach_tip}</p>
                </div>

                {progress === 100 && (
                  <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-6 text-center">
                    <CheckCircle className="w-10 h-10 text-green-400 mx-auto mb-3" />
                    <h3 className="text-white font-bold text-lg mb-1">Treino Concluido!</h3>
                    <p className="text-sm text-gray-400">Excelente! Meça sua glicemia apos o treino.</p>
                  </div>
                )}
              </>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}
