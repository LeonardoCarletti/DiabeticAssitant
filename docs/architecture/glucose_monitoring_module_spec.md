# Documentação Técnica e Funcional: Módulo de Monitoramento de Glicemia (Glucose Hub)

Este documento especifica a arquitetura e as funcionalidades do **Módulo de Monitoramento de Glicemia** para o Diabetic Assistant. O módulo é projetado como uma "verdade única" (Source of Truth) para pacientes, coachs e profissionais de saúde, inspirado na robustez de sistemas como Dexcom, Libre e MySugr.

---

## A. Arquitetura de Dados

O banco de dados (Supabase/PostgreSQL) garante que nenhuma leitura seja perdida e que o contexto seja imutável.

### Entidades Principais
1. **GlucoseReading (Leitura):** 
   - `id`, `user_id`, `value` (Float), `unit` (mg/dL ou mmol/L), `measured_at` (Timestamp Exato).
   - `context`: Enum (fasting, pre_meal, post_meal, sleep, exercise, stress, random).
   - `source`: Enum (cgm_libre, cgm_dexcom, ble_meter, manual, voice_ai, imported).
   - `user_notes` (Texto livre) e `is_anomaly` (Booleano gerado pelo sistema).

2. **GlucoseTarget (Meta):**
   - `id`, `user_id`, `created_by` (paciente ou id_medico).
   - `period_of_day` (geral, fasting, post_meal).
   - `min_value`, `max_value`.

3. **ClinicalEvent (Evento/Marcador):**
   - Registro de correlações atípicas: Hipoglicemia severa, Ajuste de Insulina Basal, Dia de Doença. Vincula-se ao período temporal do paciente.

4. **ClinicalFeedback:**
   - `id`, `professional_id`, `patient_id`, `target_period` (Range de datas analisado), `clinical_notes`, `suggested_actions`.

---

## B. Fluxos de Usuário

### 1. Entrada de Dados Dinâmica (Logging)
- **Dispositivos CGM/BLE:** Sincronização passiva em background via HealthKit/Integrações de API. Leituras a cada 5-15 min são salvas automaticamente.
- **Voz/IA:** O usuário abre o App e diz: *"Minha glicemia está 145 agora, acabei de comer"*. A IA entende, extrai `value: 145`, `context: post_meal`, e pede confirmação visual antes de salvar.
- **Manual UI:** Slider grande ou Keypad simplificado (inspirado no MySugr) com botões de tag rápida para contexto.

### 2. Painel de Análise e Benchmarks
- **Visualização Primária:** Gráfico de linha suavizada (trend interpolation) mostrando a curva glicêmica do dia.
- O usuário escolhe no topo: **"Comparar contra: [x] Minhas Metas Livres ou [  ] Protocolo do Médico"**. As cores do gráfico adaptam-se imediatamente (verde no alvo, vermelho fora).

### 3. Profissionais & Coachs
- O profissional acessa um **Dashboard de Pacientes** ordenado por "Sinal de Risco" (menor TIR no topo). Seleciona o paciente e deixa notas clínicas na linha do tempo que o paciente verá em destaque.

---

## C. Funcionalidades de IA (Agente Especialista)

A IA Conversacional atua como um navegador de dados e não como substituto médico. O comportamento do prompt é ajustado pela _Role_ solicitada:

1. **Modo Clínico (Para Profissionais/Discussão Técnica):**
   - Foca em estatísticas duras. *"O paciente apresentou TIR de 65%. Houve 4 padrões anômalos de hiperglicemia noturna (02:00-04:00) correlacionados a jantares high-carb."*
2. **Modo Empático (Coach/Suporte):**
   - *"Notei que ontem foi um dia difícil com as oscilações. Você mandou muito bem registrando tudo! Que tal tentarmos ajustar nossa hidratação hoje?"*
3. **Modo Acessível (Assistente Rápido):**
   - *"Glicemia de 110 salva com sucesso. Boa marca antes do treino!"*

**Limites Arquitetados (Safety Layer):**
Se a IA detecta pedidos de alteração de dosagem de insulina, o `SafetyRouter` neural bloqueia o prompt e injeta a resposta: ⚠️ *"Não posso prescrever alterações de dosagem. Baseado nos seus logs, sua glicemia noturna está caindo. Valide uma redução de basal com seu médico. Posso gerar um PDF destes dias para você enviar a ele?"*

---

## D. Cálculos e Índices Clínicos Automáticos

O backend (FastAPI/Pandas) processa e entrega para o frontend os seguintes cálculos em tempo real:

- **TIR (Time In Range):** `%` de leituras (via interpolação) dentro do Target configurado (Ex: 70-180 mg/dL). Calculado também para TBR (Time Below Range) e TAR (Time Above Range).
- **GMI (Glucose Management Indicator):** Fórmula de aproximação científica de A1C baseada na glicemia média dos últimos 14+ dias: `3.31 + (0.02392 * Glicemia_Media_mg_dL)`.
- **CV (Coeficiente de Variação):** `%` da variabilidade. `(Desvio Padrão / Glicemia Média) * 100`. Meta clínica: < 36%.
- **Padrões de Recorrência:** Cron jobs diários buscam clusters. Ex: Se `TBR > 5%` entre 00h-06h por 3 dias seguidos, o sistema levanta a flag `nocturnal_hypo_trend`.

---

## E. Segurança e Conformidade (Compliance)

- Todas as leituras portam RLS (Row-Level Security) no Supabase. Paciente lê `auth.uid() == user_id`. Profissionais só leem se `care_relations.status == "active"`.
- As mensagens trocadas com a IA e os históricos de log nunca assumem diagnóstico.
- Exportações PDF/CSV exigem re-autenticação JWT para emissão.
- Conformidade HIPAA: Todos os Patient Health Information (PHI) crus são mascarados nos logs de erro de servidores.

---

## F. Interface e Experiência (HUD & UI)

**Visão do Paciente (Estilo Dexcom + Sibionics):**
- **Semaforização:** Tela preta/escura (Dark Mode OLED) onde o número gigantesco da glicemia atual é a estrela. Seta de tendência inclinada ao lado do número.
- **Heatpad de Aderência:** Calendário estilo GitHub *commits* abaixo do gráfico, onde dias verdes representam TIR > 80%, vermelho TIR < 50%.
- Botão flutuante fixo centralizado `[ + Log ]`, que aciona microfone por default.

**Visão do Profissional (Estilo LibreView):**
- Layout "Command Center" extenso. Coluna esquerda com a lista de pacientes e alertas piscando `! Variabilidade Alta`.
- Centro com gráfico empilhável (Ambulatory Glucose Profile - AGP), sobrepondo 14 dias em um único bloco de 24h para escancarar tendências medianas.
- Lateral direita dedicada para "Intervenções", onde o médico digita os feedbacks que disparam Push Notifications no app do paciente.
