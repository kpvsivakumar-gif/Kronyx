create table if not exists users (
  id uuid default gen_random_uuid() primary key,
  email text unique not null,
  password text not null,
  api_key_1 text unique not null,
  api_key_2 text unique not null,
  created_at timestamptz default now()
);

create table if not exists memories (
  id uuid default gen_random_uuid() primary key,
  content text not null,
  user_id text not null,
  api_key text not null,
  created_at timestamptz default now()
);
create index if not exists idx_memories_api_key on memories(api_key);
create index if not exists idx_memories_user_id on memories(user_id);

create table if not exists memory_stats (
  id uuid default gen_random_uuid() primary key,
  api_key text unique not null,
  total_ever integer default 0,
  deleted_count integer default 0,
  created_at timestamptz default now()
);

create table if not exists nexus_usage (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  layer text not null,
  endpoint text not null,
  created_at timestamptz default now()
);
create index if not exists idx_nexus_usage_api_key on nexus_usage(api_key);
create index if not exists idx_nexus_usage_created_at on nexus_usage(created_at);

create table if not exists aegis_threats (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  threat_type text not null,
  content text,
  created_at timestamptz default now()
);
create index if not exists idx_aegis_threats_api_key on aegis_threats(api_key);

create table if not exists flux_cache (
  question_hash text primary key,
  response text not null,
  created_at timestamptz default now()
);

create table if not exists flux_stats (
  id uuid default gen_random_uuid() primary key,
  api_key text unique not null,
  hit_count integer default 0,
  miss_count integer default 0,
  created_at timestamptz default now()
);

create table if not exists pulse_incidents (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  description text not null,
  recovered boolean default false,
  created_at timestamptz default now()
);

create table if not exists insight_analytics (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  user_id text not null,
  question text,
  response_length integer,
  response_time float,
  created_at timestamptz default now()
);
create index if not exists idx_insight_analytics_api_key on insight_analytics(api_key);

create table if not exists oracle_predictions (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  user_id text not null,
  original_message text,
  predicted_intent text,
  created_at timestamptz default now()
);

create table if not exists genome_profiles (
  id uuid default gen_random_uuid() primary key,
  api_key text unique not null,
  profile text not null,
  created_at timestamptz default now()
);

create table if not exists nexus_sources (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  source_type text not null,
  config text not null,
  active boolean default true,
  created_at timestamptz default now()
);

create table if not exists sovereign_log (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  decision text,
  jurisdiction text,
  compliant boolean default true,
  issues text,
  created_at timestamptz default now()
);

create table if not exists evolve_data (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  question text,
  response text,
  score integer,
  created_at timestamptz default now()
);

create table if not exists notifications (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  type text not null,
  message text not null,
  read boolean default false,
  created_at timestamptz default now()
);

create table if not exists webhooks (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  url text not null,
  events text not null,
  active boolean default true,
  created_at timestamptz default now()
);

create table if not exists protocol_registry (
  id uuid default gen_random_uuid() primary key,
  ai_id text not null,
  ai_name text not null,
  ai_type text not null,
  api_key text not null,
  capabilities text,
  version text,
  status text default 'active',
  created_at timestamptz default now()
);

create table if not exists protocol_messages (
  id uuid default gen_random_uuid() primary key,
  message_id text unique not null,
  from_ai text not null,
  to_ai text not null,
  message text not null,
  message_type text not null,
  priority text default 'normal',
  api_key text not null,
  delivered boolean default false,
  created_at timestamptz default now()
);

create table if not exists identity_registry (
  id uuid default gen_random_uuid() primary key,
  ai_id text not null,
  api_key text not null,
  description text,
  intended_use text,
  trust_score integer default 100,
  total_interactions integer default 0,
  verified_accurate integer default 0,
  flagged_inaccurate integer default 0,
  is_verified boolean default false,
  created_at timestamptz default now()
);

create table if not exists transparency_log (
  id uuid default gen_random_uuid() primary key,
  decision_id text unique not null,
  ai_id text not null,
  api_key text not null,
  decision text not null,
  reasoning text,
  outcome text,
  affected_users integer default 0,
  timestamp text,
  created_at timestamptz default now()
);

create table if not exists live_learning (
  id uuid default gen_random_uuid() primary key,
  correction_id text unique not null,
  ai_id text not null,
  api_key text not null,
  original_response text,
  corrected_response text,
  correction_type text not null,
  context text,
  applied boolean default false,
  impact_count integer default 0,
  created_at timestamptz default now()
);

create table if not exists relationship_engine (
  id uuid default gen_random_uuid() primary key,
  user_id text not null,
  ai_id text not null,
  api_key text not null,
  total_interactions integer default 0,
  total_quality_score integer default 0,
  avg_quality float default 0,
  relationship_depth text default 'new',
  last_interaction text,
  created_at timestamptz default now()
);

create table if not exists value_network (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  user_id text,
  interaction_type text,
  goal_achieved boolean default false,
  time_saved_minutes integer default 0,
  estimated_value_usd float default 0,
  value_score integer default 0,
  layer_used text,
  created_at timestamptz default now()
);

create table if not exists studio_workflows (
  id uuid default gen_random_uuid() primary key,
  workflow_id text unique not null,
  name text not null,
  description text,
  steps text not null,
  trigger text default 'manual',
  api_key text not null,
  active boolean default true,
  run_count integer default 0,
  created_at timestamptz default now()
);

create table if not exists neural_bus (
  id uuid default gen_random_uuid() primary key,
  message_id text unique not null,
  topic text not null,
  payload text not null,
  publisher_id text,
  priority text default 'normal',
  api_key text not null,
  consumed_count integer default 0,
  created_at timestamptz default now()
);

create table if not exists neural_subscriptions (
  id uuid default gen_random_uuid() primary key,
  topic text not null,
  subscriber_id text not null,
  api_key text not null,
  active boolean default true,
  created_at timestamptz default now()
);

create table if not exists observatory_metrics (
  id uuid default gen_random_uuid() primary key,
  metric_name text not null,
  value float not null,
  ai_id text,
  dimension text default 'performance',
  unit text,
  api_key text not null,
  created_at timestamptz default now()
);

create table if not exists forge_experiments (
  id uuid default gen_random_uuid() primary key,
  experiment_id text unique not null,
  name text not null,
  hypothesis text,
  variant_a text,
  variant_b text,
  metric_to_track text,
  api_key text not null,
  status text default 'running',
  a_count integer default 0,
  b_count integer default 0,
  a_total_score float default 0,
  b_total_score float default 0,
  created_at timestamptz default now()
);

create table if not exists time_machine (
  id uuid default gen_random_uuid() primary key,
  snapshot_id text unique not null,
  ai_id text not null,
  api_key text not null,
  state_data text not null,
  label text,
  snapshot_time text,
  created_at timestamptz default now()
);

create table if not exists marketplace (
  id uuid default gen_random_uuid() primary key,
  item_id text unique not null,
  item_name text not null,
  item_type text not null,
  description text,
  config_data text,
  price_usd float default 0,
  tags text,
  publisher_api_key text not null,
  downloads integer default 0,
  rating float default 0,
  rating_count integer default 0,
  active boolean default true,
  created_at timestamptz default now()
);

create table if not exists anima_souls (
  id uuid default gen_random_uuid() primary key,
  ai_id text not null,
  api_key text not null,
  core_values text,
  identity_description text,
  total_interactions integer default 0,
  total_corrections_received integer default 0,
  identity_stability_score integer default 100,
  dominant_state text default 'present',
  creation_timestamp text,
  last_interaction text,
  created_at timestamptz default now()
);

create table if not exists anima_history (
  id uuid default gen_random_uuid() primary key,
  ai_id text not null,
  api_key text not null,
  interaction_content text,
  interaction_quality integer,
  state_at_time text,
  user_id text,
  created_at timestamptz default now()
);

create table if not exists akashic_wisdom (
  id uuid default gen_random_uuid() primary key,
  wisdom_id text unique not null,
  api_key text not null,
  interaction_type text not null,
  original_content text,
  corrected_content text,
  wisdom_principle text,
  new_concepts text,
  removed_concepts text,
  created_at timestamptz default now()
);

create table if not exists omega_trajectories (
  id uuid default gen_random_uuid() primary key,
  user_id text not null,
  api_key text not null,
  current_phase text,
  predicted_next text,
  prediction text,
  messages_analyzed integer default 0,
  last_updated text,
  created_at timestamptz default now()
);
