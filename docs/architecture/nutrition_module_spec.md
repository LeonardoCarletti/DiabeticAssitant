# Documentação Técnica e Funcional: Módulo de Nutrição (Elite Nutrition)

Este documento detalha a arquitetura e as funcionalidades do Módulo de Nutrição do **Diabetic Assistant**, projetado para ser o complemento metabólico definitivo ao módulo de treinamento.

---

## 1. Estrutura de Dados e Entidades

Para suportar a flexibilidade exigida, o banco de dados deve seguir o modelo de relacionamentos abaixo:

### 1.1. Plano Nutricional (NutritionalPlan)
- **Atributos:** ID, Nome, Objetivo (Cutting/Bulking/Saúde), Duração, Frequência (Refeições/Dia), Dias de Vigência, Notas Gerais.
- **Relacionamentos:** Um plano possui várias `Refeições`.

### 1.2. Refeição (Meal)
- **Atributos:** ID, Nome (Café, Almoço, etc.), Horário Previsto, Foto Referência (URL), Notas/Restrições.
- **Estrutura Interna:** Itens de Alimentos (Alimento + Quantidade + Macros Calculados).
- **Componentes Adicionais:** Checkbox para 'Cardio Pré/Pós', 'Aquecimento Metabólico'.

### 1.3. Banco de Alimentos (FoodDatabase)
- **Atributos:** ID, Nome, Marca (Opcional), Porção Base (g/ml), Proteína, Carbo, Gordura, Caloria, Micronutrientes (Fibras, Sódio, etc.).
- **Diferencial:** Flag `is_custom` para distinguir alimentos globais de cadastros do usuário.

### 1.4. Log de Consumo (NutritionLog)
- **Atributos:** ID, Data/Hora Efetiva, Quantidade Real, Foto da Refeição (para análise de IA), Feedback do Usuário, IDs dos Alimentos consumidos.

---

## 2. Fluxos de Interação (UX)

### 2.1. Criação e Customização (Acesso Profissional/IA)
- **Manual:** Layout de grade onde cada refeição é um bloco arrastável. Inserção de alimentos via busca no banco com cálculo de macros em tempo real na barra lateral.
- **Via IA:** O usuário digita "Crie uma dieta de 2500kcal para hipertrofia com foco em baixo índice glicêmico". A IA gera a estrutura e preenche automaticamente os blocos de refeição.

### 2.2. Command Center (Logging Diário)
- Interface de Timeline vertical mostrando as refeições do dia.
- **Botão Inteligente:** Aciona a câmera para "Análise Visual". A IA reconhece o prato, estima porções e sugere os macros para o log.

---

## 3. Funcionalidades de Inteligência Artificial

### 3.1. IA Conversacional (Elite Coach GPT)
- **Capacidade:** Montar planos complexos, sugerir substituições (ex: "Troque o frango por uma fonte vegetal equivalente") e ajustar o plano com base no feedback de performance.
- **Saída:** Gera um JSON estruturado que alimenta diretamente os componentes da interface, garantindo que o plano aceito seja persistido no formato padrão.

### 3.2. IA Visual (Vision Analysis)
- **Reconhecimento de Imagem:** Identifica tipos de alimentos e volume aproximado.
- **Cálculo Automático:** Converte a imagem em uma estimativa de calorias e macros, que o usuário apenas confirma antes de salvar no log.

---

## 4. Análises, Benchmarks e Relatórios

### 4.1. Análise de Aderência (Precision Analysis)
- **Benchmark Fixo:** Comparação contra o Plano Prescrito (Previsto vs. Realizado).
- **Benchmark Flexível:** Comparação contra metas de macros (IIFYM - If It Fits Your Macros).

### 4.2. Relatório Expert (PDF)
- **Capa:** Resumo de performance metabólica do período.
- **Gráficos:** Progressão de peso vs. Consumo calórico média, dispersão de macros por refeição.
- **Insights Narrativos:** "Você manteve 90% de aderência no café da manhã, mas os lanches da tarde estão 20% acima do carbo planejado."

---

## 5. Gestão de Histórico e Protocolos

- **Imutabilidade:** Planos antigos são arquivados com o status `archived`. Nunca são removidos, permitindo que a IA analise a evolução das estratégias nutricionais do usuário ao longo de meses/anos.
- **Protocolos Temporais:** Agrupamento de planos por fases (ex: "Protocolo Arnold Classic - 12 semanas").

---

## 6. Sistema de Feedback Profissional

- **Timeline de Orientação:** Espaço para o coach deixar áudios ou notas curtas em cada refeição ou no resumo do dia.
- **Alerta de Desvio:** Notificação automática para o profissional quando o aluno reporta 3 dias seguidos com desvio de >15% nas calorias meta.
