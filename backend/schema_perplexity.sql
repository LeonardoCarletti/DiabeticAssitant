-- Usuário já existe em auth.users (Supabase)
-- Tabela de perfis complementares
create table if not exists public.user_profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  date_of_birth date,
  diabetes_type text check (diabetes_type in ('type1','type2','gestational','other')),
  weight_kg numeric(5,2),
  height_cm numeric(5,2),
  insulin_user boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Logs de glicose (manual + CGM)
create table if not exists public.glucose_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  source text check (source in ('manual','cgm','lab','other')) default 'manual',
  device_id text,
  value_mg_dl numeric(5,1) not null,
  trend text check (trend in ('falling','rising','stable','unknown')) default 'unknown',
  context text check (context in ('fasting','pre_meal','post_meal','pre_workout','post_workout','bedtime','random','other')) default 'random',
  hypo_flag boolean generated always as (value_mg_dl < 70) stored,
  hyper_flag boolean generated always as (value_mg_dl > 180) stored,
  notes text,
  measured_at timestamptz not null,
  recorded_at timestamptz default now(),
  created_by text check (created_by in ('user','system','import')) default 'user',
  correlation_id uuid, -- p/ ligar com refeição/treino
  constraint glucose_events_user_time_unique unique (user_id, measured_at)
);

-- Refeições / ingestão de carboidratos
create table if not exists public.meals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  name text, -- "Almoço", "Lanche pré-treino"
  meal_type text check (meal_type in ('breakfast','lunch','dinner','snack','other')) default 'other',
  total_carbs_g numeric(6,1), -- total estimado
  total_protein_g numeric(6,1),
  total_fat_g numeric(6,1),
  estimated boolean default true, -- true = estimado pelo usuário/IA
  notes text,
  eaten_at timestamptz not null,
  recorded_at timestamptz default now()
);

-- Itens da refeição (opcional, para granularidade)
create table if not exists public.meal_items (
  id uuid primary key default gen_random_uuid(),
  meal_id uuid references public.meals(id) on delete cascade,
  name text not null,
  carbs_g numeric(6,1),
  protein_g numeric(6,1),
  fat_g numeric(6,1),
  portion text -- "1 fatia", "200 ml", etc.
);

-- Associação refeição <-> glicemia (pré/pós)
create table if not exists public.meal_glucose_links (
  id uuid primary key default gen_random_uuid(),
  meal_id uuid references public.meals(id) on delete cascade,
  glucose_event_id uuid references public.glucose_events(id) on delete cascade,
  relation text check (relation in ('pre_meal','post_meal_1h','post_meal_2h','post_meal_other')) not null
);

-- Índice para queries de dashboard
create index if not exists idx_glucose_events_user_time on public.glucose_events (user_id, measured_at desc);
create index if not exists idx_meals_user_time on public.meals (user_id, eaten_at desc);
