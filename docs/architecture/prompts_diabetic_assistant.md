# Prompts para Evolução do Diabetic Assistant

Aqui estão os comandos (prompts) que você pode usar para que a IA crie uma interface integrada e de alta performance.

---

## 1. Prompt de Identificação (Para Perplexity/Research)
Use este prompt para que a IA mapeie a inteligência do projeto e o diferencie de outros:

> "Analise a arquitetura de uma aplicação avançada chamada **'Diabetic Assistant'** (focada em performance de elite para diabéticos). O backend em **FastAPI** gerencia:
> 1. **RAG Científico:** Consulta em artigos médicos e PDFs.
> 2. **Profile & Logs:** Glicemia, Insulina e Carboidratos.
> 3. **Análise Preditiva:** Padrões metabólicos via IA.
> 4. **Exames Lab:** OCR de laudos para extração de indicadores.
> 5. **Elite Trainer & Nutrition:** Treinos de musculação (RPE/Carga) e gestão de macros.
> 6. **Recovery Hub:** Readiness via HRV e Sono, integração com Apple/Garmin.
> Explique como integrar esses fluxos em uma 'Single Source of Truth' para o usuário."

---

## 2. Prompt de Geração de Frontend (Interface Command Center)
Use este comando para gerar uma aplicação estilo **"HUD/Command Center"**, integrada e sem abas excessivas:

> "Aja como Desenvolvedor Frontend Senior e UX Designer. Crie uma interface **Premium, Fluida e Integrada** em **React (Vite + Tailwind + Shadcn)** para o **'Diabetic Assistant'**.
>
> **Layout Integrado:**
> - **Dashboard Central:** HUD com gráfico de Glicemia + Predição centralizado e widgets de status (Macros, Readiness, Next Workout).
> - **Cérebro (Left Sidebar):** Feed de Insights do Coach e Barra de 'Quick Action' universal (Voz/Texto).
> - **Action Panel (Right Sidebar):** Painel contextual expansível que alterna entre 'LabMode' (Chat RAG), 'ExamView' e 'GymMode' conforme a necessidade.
>
> **Estética:** Estilo Tesla/SpaceX/Whoop. Dark mode, glassmorphism, visual 'Heads-Up Display', transições fluidas e visual de alta performance. Conexão via `VITE_API_URL`."
