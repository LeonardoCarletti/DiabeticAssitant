# Arquitetura de Integração de Dados de Saúde (Health Data Hub)

Esta documentação especifica a arquitetura *production-ready* responsável por ingerir, normalizar, armazenar e disponibilizar dados de saúde a partir de múltiplos dispositivos (wearables) e aplicativos para o ecossistema do **Diabetic Assistant**.

A stack definida utiliza **Python (FastAPI)** no backend e **Supabase (PostgreSQL)** para persistência e Row-Level Security (RLS).

---

## 1. Diagrama Conceitual do Fluxo de Dados

```ascii
[Fontes de Dados]                                      [Health Data Hub - Backend FastAPI]
                                           |
+--------------+   OAuth/Webhook           |   +-----------------------+     +--------------------------+
| Apple Health | ------------------------> |   | 1. API Gateway/Auth   |     | 2. Validador/Normalizador|
+--------------+                           |   | - Valida Token/Assinat| --> | - Unifica Fuso Horário   |
+--------------+   Polling/OAuth           |   | - Rate Limiter        |     | - Converte Unidades      |
| Garmin       | ------------------------> |   +-----------------------+     | - Checa Limites Biológ.  |
+--------------+                           |                                 +--------------------------+
+--------------+   Manual/API Pública      |                                              |
| MySugr/CGM   | ------------------------> |                                              v
+--------------+                           |                                 +--------------------------+
+--------------+   Upload (CSV/PDF)        |                                 | 3. Pipeline de Ingestão  |
| Relatórios   | ------------------------> |                                 | - Detecção Duplicidade   |
+--------------+                           |                                 | - Resolução de Conflitos |
                                           |                                 +--------------------------+
                                                                                          |
                                  [Layer de Persistência]                                 v
                                           |                                 +--------------------------+
+--------------+  <--------------------------------------------------------  | 4. DAO/Supabase Sync     |
|              |     [Consumidores Internos]                                 | - Bulk Inserts           |
|  SUPABASE    |  <---------------------------+                              | - Atualiza Metadados     |
| (PostgreSQL) |                              |                              +--------------------------+
|  + RLS/RBAC  |       +----------------+     |     +----------------+             
+--------------+       |  Modelos IA/ML |     +---  |  Dashboards UI |
                       +----------------+           +----------------+
```

---

## 2. Esquema de Dados Normalizado (Unified Schema)

Todos os dados divergentes (ex: Garmin envia em `ms`, Apple em `s`; Glicose em `mmol/L` ou `mg/dL`) devem convergir para este formato universal.

### Entidade Central: `health_metrics`

| Campo | Tipo | Descrição/Exemplo | Normalização/Limites |
| :--- | :--- | :--- | :--- |
| `id` | UUID | Chave primária | - |
| `user_id` | UUID | FK para a tabela de usuários | Depende do Supabase Auth |
| `metric_type` | String | Extensa: `blood_glucose`, `heart_rate`, `sleep_stage`, `steps` | Enum estrito |
| `value` | Float | O valor medido (Ex: 105.5) | Glicemia: 20-600. FC: 30-220. |
| `unit` | String | Unidade universal padronizada | `mg/dL`, `bpm`, `count`, `minutes` |
| `measured_at` | Timestamptz | Momento exato da medição | Sempre salvo em UTC |
| `source_name` | String | Nome do app/dispositivo (Ex: `apple_health`, `garmin`) | - |
| `source_id` | String | ID único original da fonte (Crucial para deduplicar) | Ex: `hk_uuid_123` |
| `reliability` | Enum | Nível de confiança (`high`, `medium`, `low`, `manual`) | Dinâmico via fonte |
| `metadata` | JSONB | Estrutura p/ extras (Ex: duração de sono profundo, tags) | - |
| `created_at` | Timestamptz | Data de ingestão no nosso sistema | Default: now() |

**Exemplo de Normalização:**
- MySugr: `{"glucose": "5.5", "unit": "mmol/L", "time": "2023-10-25 10:00:00"}`
- *Transformado:* `{"metric_type": "blood_glucose", "value": 99.0, "unit": "mg/dL", "measured_at": "2023-10-25T13:00:00Z" (UTC), "source_name": "mysugr"}`

---

## 3. Especificação das Conexões de Fontes

| Fonte | Modo Oficial | Sincronia / Coleta | Fallback |
| :--- | :--- | :--- | :--- |
| **Apple Health** (HealthKit) | Push (App Nativo via API/Webhook) | Background Sync a cada 1 hora. iOS envia para API. | Sincronia na abertura do App mobile. |
| **Garmin** (Health API) | Push (Webhook Ping) | Garmin manda payload para nosso endpoint quando há novo dado. | Pull (Polling noturno das últimas 24h via ping OAuth API). |
| **MySugr / Libre** (CGM) | API Externa (se disp.) / Manual | Polling horário em APIs não-oficiais (ex: LibreView API) ou CSV Upload. | Upload explícito manual pelo painel web Web. |
| **Arquivos (PDFs/Labs)** | Upload Manual | O usuário sobe via Frontend, API manda p/ worker OCR (LlamaParse). | Erro de IA solicita correção humana na UI. |

*Nota OAuth:* O Supabase lidará com os tokens OAuth armazenados criptograficamente na master table `integrations`, permitindo "Re-Syncs".

---

## 4. Pipeline de Ingestão (Lógica em FastAPI)

```python
# Pseudocódigo Simplificado do Pipeline (Python / FastAPI)
async def ingest_health_data(raw_payload: list, source: str, user_id: str):
    # 1. Validação de Contrato Basal
    validated_raw = validate_schema(raw_payload, source)
    
    normalized_data = []
    for item in validated_raw:
        # 2. Transformação e Unificação
        norm_item = normalizer.standardize_metric(item, source)
        
        # 3. Validação Limites Fisiológicos Subliminares
        if not passes_biological_threshold(norm_item):
            log_warning(f"Implausible data discarded for user {user_id}: {norm_item}")
            continue
            
        normalized_data.append(norm_item)
        
    # 4. Resolução de Conflitos e Deduplicação (Usando source_id e range de tempo)
    unique_data = deduplicator.resolve_conflicts(normalized_data, user_id)
    
    # 5. Bulk Insert Supabase (Upsert em caso de conflito de constraints)
    try:
        supa_client.table('health_metrics').upsert(
            unique_data, on_conflict="source_id, user_id"
        ).execute()
    except Exception as e:
        log_error(f"Failed to persist metrics: {e}")
        send_to_dead_letter_queue(unique_data) # Quarantine
```

### Regras de Conflito:
- Se houver medição simultânea de **Passos** (Apple Watch = `source_id_A`, iPhone = `source_id_B`), priorizar o device catalogado com maior `reliability` (ex: Apple Watch).

---

## 5. Modelo de Banco de Dados (Supabase/SQL)

A estrutura suporta RBAC e Row-Level Security dinâmico: Médico só vê paciente que o autorizou.

```sql
-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Perfis (Engloba roles: 'patient', 'doctor', 'admin')
CREATE TABLE profiles (
  id UUID REFERENCES auth.users PRIMARY KEY,
  role TEXT NOT NULL DEFAULT 'patient',
  full_name TEXT
);

-- Relações de Cuidado (Quem cuida de quem)
CREATE TABLE care_relations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  doctor_id UUID REFERENCES profiles(id),
  patient_id UUID REFERENCES profiles(id),
  status TEXT DEFAULT 'active' -- 'active', 'revoked'
);

-- Tabela Central (Otimizada para Time-Series)
CREATE TABLE health_metrics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  metric_type TEXT NOT NULL,
  value NUMERIC NOT NULL,
  unit TEXT NOT NULL,
  measured_at TIMESTAMPTZ NOT NULL,
  source_name TEXT NOT NULL,
  source_id TEXT UNIQUE, -- Chave de Deduplicação
  reliability TEXT DEFAULT 'medium',
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Índices (Cruciais para Time-Series Queries)
CREATE INDEX idx_health_user_metric_time ON health_metrics (user_id, metric_type, measured_at DESC);

-- === POLÍTICAS RLS (Row-Level Security) ===

ALTER TABLE health_metrics ENABLE ROW LEVEL SECURITY;

-- 1. Paciente vê e insere apenas seus próprios dados
CREATE POLICY "Users can access their own data"
ON health_metrics FOR ALL USING (auth.uid() = user_id);

-- 2. Médicos veem dados de pacientes onde a relação na `care_relations` é ativa
CREATE POLICY "Doctors can view linked patient data"
ON health_metrics FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM care_relations cr 
    WHERE cr.doctor_id = auth.uid() 
    AND cr.patient_id = health_metrics.user_id 
    AND cr.status = 'active'
  )
);
```

---

## 6. Endpoints FastAPI e Queries Práticas

Exemplo de estruturação de rotas robustas para dashboards. As chamadas devem ser enxutas para a UI carregar rápido na Vercel.

**Endpoint:** `GET /api/v1/metrics/glucose/summary`
**Propósito:** Gerar a métrica de "7 dias" e TIR (Time In Range).
```python
@router.get("/metrics/{metric_type}/summary")
async def get_metric_summary(
    metric_type: str, 
    days: int = 7, 
    patient_id: Optional[UUID] = None, # Para uso de médicos
    current_user: User = Depends(get_current_active_user)
):
    target_uid = patient_id if patient_id else current_user.id
    # Verificação granular de permissão se target_uid != current_user.id
    verify_care_access(current_user.id, target_uid)
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Exemplo Query Supabase
    response = supabase.table('health_metrics')\
        .select('*')\
        .eq('user_id', target_uid)\
        .eq('metric_type', metric_type)\
        .gte('measured_at', cutoff_date)\
        .execute()
        
    df = pd.DataFrame(response.data)
    # Aggregation via Pandas p/ CPU rápido (ou via SQL Edge Functions na Supabase)
    agg = calculate_time_in_range(df, lower=70, upper=180)
    
    return {"status": "success", "period": f"{days} days", "data": agg}
```

---

## 7. Setup e Deployment (Backend FastAPI)

### Estrutura Sugerida:
```
backend/
├── main.py                # Gateway inicial / Middleware CORS e Error Handling globally
├── core/                  
│   ├── config.py          # Leitura de ENV (Supabase keys, JWT Secrets)
│   └── security.py        # RBAC, validação JWT do Supabase via FastAPI Depends
├── api/                   
│   ├── v1/ingest.py       # Webhooks nativos (Garmin, Apps p/ POST)
│   └── v1/metrics.py      # Endpoints para os Dashboards Web/Mobile
├── ingestion/             
│   ├── normalizers.py     # Adapters (Ex: garmin_adapter.py, apple_adapter.py)
│   └── deduplicator.py
└── requirements.txt
```

### Inicialização (Vercel ou Render/Railway):
A API deve ser inicializada sem estado na memória para escalonamento horizontal. Processamento pesado de relatórios (ex: PDF parsing) deve ser jogado via Celery/Workers, ou endpoints Serverless assíncronos que avisem a UI via WebSockets/SSE.

---

## 8. Segurança e Compliance (LGPD / HIPAA)

Dado que os dados são PhI (Personal Health Information):
1. **Criptografia em Repouso:** Garantida nativamente pelo Supabase AWS.
2. **Criptografia em Trânsito:** Forçar TLS 1.2+ em todos os endpoints FastAPI. Redirecionamento 301.
3. **Auditoria Lógica:** Implementar *Triggers* PostgreSQL no Supabase (tabela `audit_logs`) que grave cada UPDATE/DELETE na tabela `health_metrics`, registrando ID do usuário efetuante (Garante trilha de segurança).
4. **Isolamento de Credenciais de OAuth:** Chaves de Wearables (Strava, Garmin tokens) devem ficar encriptadas na tabela (`pgsodium` extension on Supabase) via cofres virtuais, limitando até admins de lendas ver os tokens puristas.
5. **Retenção e Exclusão:** Rota `/api/v1/compliance/forget-me` que expurga dados PII e pseudonimiza os registros de métricas caso o usuário exerça o direito de deleção (LGPD).

---

## 9. Considerações Finais

### Escalabilidade e IA:
- Como esta stack usa PostgreSQL/Supabase, a agregação brutal pode ficar lenta no longo prazo (+100M rows). Em 2 anos, os relatórios para *insights* de IA Conversacional deverão usar uma visão materializada (*Materialized View*) agregando os dados em blocos de horas.
- Todo pipeline validado nesta arquitetura não fornece os dados crus ao RAG; ele fornece agregações diárias sumarizadas ao RAG prompt preventivamente, reduzindo alucinação e custos de Token da OpenAI.
