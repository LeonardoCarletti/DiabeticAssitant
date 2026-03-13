# Guia: Deploy da Interface Completa no Vercel

Siga estes passos para hospedar seu backend e a nova interface.

## 1. Deploy em Dois Projetos (Recomendado)
- **Backend:** Conecte a pasta `DiabeticAssitant` ao Vercel.
- **Frontend:** Use o prompt abaixo para criar sua interface React e conecte o novo repositório ao Vercel.

## 2. Prompt de Geração (Interface Command Center)
> "Aja como Desenvolvedor Frontend Senior. Crie uma interface **Command Center** em **React (Vite + Tailwind + Shadcn)** para o **'Diabetic Assistant'**. Foco em visibilidade central: HUD central com Glicemia/Predição, Sidebar de Insights à esquerda e Painel Contextual (RAG/Treino/Exames) à direita. Estética Tesla/Dark Mode. Conexão via `VITE_API_URL`."

---

## 3. Configuração de Variáveis (Vercel)
No projeto Frontend do Vercel, adicione:
`VITE_API_URL=https://seu-backend.vercel.app`

## 4. Verificação
- No Backend: `venv\Scripts\pytest backend/tests/test_smoke.py`
