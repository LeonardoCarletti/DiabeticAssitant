-- ============================================================
-- BLOCO 1: Schema completo de dados clínicos
-- Rodar no Supabase SQL Editor na ordem abaixo
-- ============================================================

-- 1.1 Perfis de usuários
create table if not exists public.user_profiles (
  id                       uuid primary key references auth.users(id) on delete cascade,
  full_name                text,
  date_of_birth            date,
  diabetes_type            text check (diabetes_type in ('type1','type2','gestational','other')),
  weight_kg                numeric(5,2),
  height_cm                numeric(5,2),
  insulin_user             boolean default false,
  data_processing_consent  boolean default false,
  analytics_consent        boolean default false,
  data_retention_years     int default 5,
  created_at               timestamptz default now(),
  updated_at               timestamptz default now()
);

-- 1.2 Eventos de glicemia
create table if not exists public.glucose_events (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid references auth.users(id) on delete cascade not null,
  source         text check (source in ('manual','cgm','lab','other')) default 'manual',
  device_id      text,
  value_mg_dl    numeric(5,1) not null,
  trend          text check (trend in ('falling','rising','stable','unknown')) default 'unknown',
  context        text check (context in (
                   'fasting','pre_meal','post_meal','pre_workout',
                   'post_workout','bedtime','random','other'
                 )) default 'random',
  hypo_flag      boolean generated always as (value_mg_dl < 70) stored,
  hyper_flag     boolean generated always as (value_mg_dl > 180) stored,
  notes          text,
  measured_at    timestamptz not null,
  recorded_at    timestamptz default now(),
  created_by     text check (created_by in ('user','system','import')) default 'user',
  correlation_id uuid,
  constraint glucose_events_user_time_unique unique (user_id, measured_at)
);

-- 1.3 Refeições
create table if not exists public.meals (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid references auth.users(id) on delete cascade not null,
  name            text,
  meal_type       text check (meal_type in ('breakfast','lunch','dinner','snack','other')) default 'other',
  total_carbs_g   numeric(6,1),
  total_protein_g numeric(6,1),
  total_fat_g     numeric(6,1),
  estimated       boolean default true,
  notes           text,
  eaten_at        timestamptz not null,
  recorded_at     timestamptz default now()
);

-- 1.4 Itens de refeição
create table if not exists public.meal_items (
  id         uuid primary key default gen_random_uuid(),
  meal_id    uuid references public.meals(id) on delete cascade not null,
  name       text not null,
  carbs_g    numeric(6,1),
  protein_g  numeric(6,1),
  fat_g      numeric(6,1),
  portion    text
);

-- 1.5 Links refeição <-> glicemia
create table if not exists public.meal_glucose_links (
  id               uuid primary key default gen_random_uuid(),
  meal_id          uuid references public.meals(id) on delete cascade not null,
  glucose_event_id uuid references public.glucose_events(id) on delete cascade not null,
  relation         text check (relation in (
                     'pre_meal','post_meal_1h','post_meal_2h','post_meal_other'
                   )) not null
);

-- 1.6 Índices para queries de Dashboard
create index if not exists idx_glucose_events_user_time
  on public.glucose_events (user_id, measured_at desc);

create index if not exists idx_meals_user_time
  on public.meals (user_id, eaten_at desc);

-- 1.7 Row Level Security (RLS) — cada usuário só vê seus dados
alter table public.user_profiles    enable row level security;
alter table public.glucose_events   enable row level security;
alter table public.meals            enable row level security;
alter table public.meal_items       enable row level security;
alter table public.meal_glucose_links enable row level security;

-- Policies glucose_events
create policy "user vê seus glucose_events"
  on public.glucose_events for all
  using (auth.uid() = user_id);

-- Policies meals
create policy "user vê suas meals"
  on public.meals for all
  using (auth.uid() = user_id);

-- Policies meal_items (via meal_id)
create policy "user vê seus meal_items"
  on public.meal_items for all
  using (
    exists (
      select 1 from public.meals m
      where m.id = meal_id and m.user_id = auth.uid()
    )
  );

-- Policies meal_glucose_links
create policy "user vê seus meal_glucose_links"
  on public.meal_glucose_links for all
  using (
    exists (
      select 1 from public.meals m
      where m.id = meal_id and m.user_id = auth.uid()
    )
  );

-- Policies user_profiles
create policy "user vê seu profile"
  on public.user_profiles for all
  using (auth.uid() = id);
