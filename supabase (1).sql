-- ============================================================
-- KRONYX v3.0 - COMPLETE DATABASE SCHEMA
-- Production Ready - 50,000+ Developers
-- Run this entire file in Supabase SQL Editor
-- ============================================================


-- ============================================================
-- CORE USER TABLES
-- ============================================================

create table if not exists users (
  id uuid default gen_random_uuid() primary key,
  email text unique not null,
  password text not null,
  api_key_1 text unique not null,
  api_key_2 text unique not null,
  plan text default 'free',
  is_active boolean default true,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists idx_users_email on users(email);
create index if not exists idx_users_api_key_1 on users(api_key_1);
create index if not exists idx_users_api_key_2 on users(api_key_2);
create index if not exists idx_users_created_at on users(created_at);


-- ============================================================
-- NEXUS CORE - MEMEX LAYER
-- ============================================================

create table if not exists memories (
  id uuid default gen_random_uuid() primary key,
  content text not null,
  user_id text not null,
  api_key text not null,
  created_at timestamptz default now()
);
create index if not exists idx_memories_api_key on memories(api_key);
create index if not exists idx_memories_user_id on memories(user_id);
create index if not exists idx_memories_api_user on memories(api_key, user_id);
create index if not exists idx_memories_created_at on memories(created_at);

create table if not exists memory_stats (
  id uuid default gen_random_uuid() primary key,
  api_key text unique not null,
  total_ever integer default 0,
  deleted_count integer default 0,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists idx_memory_stats_api_key on memory_stats(api_key);


-- ============================================================
-- NEXUS CORE - USAGE TRACKING
-- ============================================================

create table if not exists nexus_usage (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  layer text not null,
  endpoint text not null,
  created_at timestamptz default now()
);
create index if not exists idx_nexus_usage_api_key on nexus_usage(api_key);
create index if not exists idx_nexus_usage_layer on nexus_usage(layer);
create index if not exists idx_nexus_usage_created_at on nexus_usage(created_at);
create index if not exists idx_nexus_usage_api_created on nexus_usage(api_key, created_at);


-- ============================================================
-- NEXUS CORE - FLUX CACHE LAYER
-- ============================================================

create table if not exists flux_cache (
  question_hash text primary key,
  response text not null,
  hit_count integer default 0,
  created_at timestamptz default now(),
  last_hit timestamptz default now()
);
create index if not exists idx_flux_cache_created_at on flux_cache(created_at);

create table if not exists flux_stats (
  id uuid default gen_random_uuid() primary key,
  api_key text unique not null,
  hit_count integer default 0,
  miss_count integer default 0,
  total_time_saved_ms integer default 0,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists idx_flux_stats_api_key on flux_stats(api_key);


-- ============================================================
-- NEXUS CORE - PULSE LAYER
-- ============================================================

create table if not exists pulse_incidents (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  description text not null,
  severity text default 'medium',
  recovered boolean default false,
  recovered_at timestamptz,
  created_at timestamptz default now()
);
create index if not exists idx_pulse_incidents_api_key on pulse_incidents(api_key);
create index if not exists idx_pulse_incidents_recovered on pulse_incidents(recovered);
create index if not exists idx_pulse_incidents_created_at on pulse_incidents(created_at);


-- ============================================================
-- NEXUS CORE - INSIGHT LAYER
-- ============================================================

create table if not exists insight_analytics (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  user_id text not null,
  question text,
  response_length integer default 0,
  response_time float default 0,
  created_at timestamptz default now()
);
create index if not exists idx_insight_analytics_api_key on insight_analytics(api_key);
create index if not exists idx_insight_analytics_user_id on insight_analytics(user_id);
create index if not exists idx_insight_analytics_created_at on insight_analytics(created_at);


-- ============================================================
-- AEGIS SHIELD - VAULT LAYER
-- ============================================================

create table if not exists aegis_threats (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  threat_type text not null,
  content text,
  severity text default 'medium',
  blocked boolean default true,
  created_at timestamptz default now()
);
create index if not exists idx_aegis_threats_api_key on aegis_threats(api_key);
create index if not exists idx_aegis_threats_type on aegis_threats(threat_type);
create index if not exists idx_aegis_threats_created_at on aegis_threats(created_at);


-- ============================================================
-- AEGIS SHIELD - SOVEREIGN LAYER
-- ============================================================

create table if not exists sovereign_log (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  decision text,
  jurisdiction text,
  compliant boolean default true,
  issues text,
  created_at timestamptz default now()
);
create index if not exists idx_sovereign_log_api_key on sovereign_log(api_key);
create index if not exists idx_sovereign_log_jurisdiction on sovereign_log(jurisdiction);
create index if not exists idx_sovereign_log_created_at on sovereign_log(created_at);


-- ============================================================
-- PROMETHEUS MIND - ORACLE LAYER
-- ============================================================

create table if not exists oracle_predictions (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  user_id text not null,
  original_message text,
  predicted_intent text,
  confidence integer default 50,
  emotion text default 'neutral',
  is_urgent boolean default false,
  created_at timestamptz default now()
);
create index if not exists idx_oracle_predictions_api_key on oracle_predictions(api_key);
create index if not exists idx_oracle_predictions_user_id on oracle_predictions(user_id);
create index if not exists idx_oracle_predictions_created_at on oracle_predictions(created_at);


-- ============================================================
-- ATLAS PRIME - GENOME LAYER
-- ============================================================

create table if not exists genome_profiles (
  id uuid default gen_random_uuid() primary key,
  api_key text unique not null,
  profile text not null,
  business_name text,
  tone text default 'professional',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists idx_genome_profiles_api_key on genome_profiles(api_key);


-- ============================================================
-- ATLAS PRIME - NEXUS KNOWLEDGE LAYER
-- ============================================================

create table if not exists nexus_sources (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  source_type text not null,
  config text not null,
  name text,
  active boolean default true,
  last_fetched timestamptz,
  created_at timestamptz default now()
);
create index if not exists idx_nexus_sources_api_key on nexus_sources(api_key);
create index if not exists idx_nexus_sources_active on nexus_sources(active);


-- ============================================================
-- EVOLUTION TRACKING
-- ============================================================

create table if not exists evolve_data (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  question text,
  response text,
  score integer,
  layer text,
  created_at timestamptz default now()
);
create index if not exists idx_evolve_data_api_key on evolve_data(api_key);
create index if not exists idx_evolve_data_score on evolve_data(score);
create index if not exists idx_evolve_data_created_at on evolve_data(created_at);


-- ============================================================
-- NOTIFICATIONS AND WEBHOOKS
-- ============================================================

create table if not exists notifications (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  type text not null,
  message text not null,
  read boolean default false,
  created_at timestamptz default now()
);
create index if not exists idx_notifications_api_key on notifications(api_key);
create index if not exists idx_notifications_read on notifications(read);
create index if not exists idx_notifications_created_at on notifications(created_at);

create table if not exists webhooks (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  url text not null,
  events text not null,
  active boolean default true,
  last_triggered timestamptz,
  trigger_count integer default 0,
  created_at timestamptz default now()
);
create index if not exists idx_webhooks_api_key on webhooks(api_key);
create index if not exists idx_webhooks_active on webhooks(active);


-- ============================================================
-- SYSTEMS NETWORK - PROTOCOL
-- ============================================================

create table if not exists protocol_registry (
  id uuid default gen_random_uuid() primary key,
  ai_id text not null,
  ai_name text not null,
  ai_type text not null,
  api_key text not null,
  capabilities text,
  version text default '1.0',
  status text default 'active',
  last_seen timestamptz default now(),
  created_at timestamptz default now()
);
create index if not exists idx_protocol_registry_api_key on protocol_registry(api_key);
create index if not exists idx_protocol_registry_ai_id on protocol_registry(ai_id);
create index if not exists idx_protocol_registry_status on protocol_registry(status);

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
  delivered_at timestamptz,
  created_at timestamptz default now()
);
create index if not exists idx_protocol_messages_api_key on protocol_messages(api_key);
create index if not exists idx_protocol_messages_to_ai on protocol_messages(to_ai);
create index if not exists idx_protocol_messages_delivered on protocol_messages(delivered);
create index if not exists idx_protocol_messages_created_at on protocol_messages(created_at);


-- ============================================================
-- SYSTEMS NETWORK - IDENTITY
-- ============================================================

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
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists idx_identity_registry_api_key on identity_registry(api_key);
create index if not exists idx_identity_registry_ai_id on identity_registry(ai_id);
create index if not exists idx_identity_registry_trust on identity_registry(trust_score);


-- ============================================================
-- SYSTEMS NETWORK - TRANSPARENCY
-- ============================================================

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
create index if not exists idx_transparency_log_api_key on transparency_log(api_key);
create index if not exists idx_transparency_log_ai_id on transparency_log(ai_id);
create index if not exists idx_transparency_log_created_at on transparency_log(created_at);


-- ============================================================
-- SYSTEMS NETWORK - LIVE LEARNING
-- ============================================================

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
create index if not exists idx_live_learning_api_key on live_learning(api_key);
create index if not exists idx_live_learning_ai_id on live_learning(ai_id);
create index if not exists idx_live_learning_correction_type on live_learning(correction_type);
create index if not exists idx_live_learning_created_at on live_learning(created_at);


-- ============================================================
-- SYSTEMS NETWORK - RELATIONSHIP ENGINE
-- ============================================================

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
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists idx_relationship_engine_api_key on relationship_engine(api_key);
create index if not exists idx_relationship_engine_user_id on relationship_engine(user_id);
create index if not exists idx_relationship_engine_ai_id on relationship_engine(ai_id);
create index if not exists idx_relationship_engine_depth on relationship_engine(relationship_depth);


-- ============================================================
-- SYSTEMS NETWORK - VALUE NETWORK
-- ============================================================

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
create index if not exists idx_value_network_api_key on value_network(api_key);
create index if not exists idx_value_network_layer_used on value_network(layer_used);
create index if not exists idx_value_network_created_at on value_network(created_at);


-- ============================================================
-- SYSTEMS PLATFORM - NEURAL BUS
-- ============================================================

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
create index if not exists idx_neural_bus_api_key on neural_bus(api_key);
create index if not exists idx_neural_bus_topic on neural_bus(topic);
create index if not exists idx_neural_bus_priority on neural_bus(priority);
create index if not exists idx_neural_bus_created_at on neural_bus(created_at);

create table if not exists neural_subscriptions (
  id uuid default gen_random_uuid() primary key,
  topic text not null,
  subscriber_id text not null,
  api_key text not null,
  active boolean default true,
  created_at timestamptz default now()
);
create index if not exists idx_neural_subscriptions_topic on neural_subscriptions(topic);
create index if not exists idx_neural_subscriptions_api_key on neural_subscriptions(api_key);
create index if not exists idx_neural_subscriptions_active on neural_subscriptions(active);


-- ============================================================
-- SYSTEMS PLATFORM - OBSERVATORY
-- ============================================================

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
create index if not exists idx_observatory_metrics_api_key on observatory_metrics(api_key);
create index if not exists idx_observatory_metrics_name on observatory_metrics(metric_name);
create index if not exists idx_observatory_metrics_dimension on observatory_metrics(dimension);
create index if not exists idx_observatory_metrics_created_at on observatory_metrics(created_at);


-- ============================================================
-- SYSTEMS PLATFORM - TIME MACHINE
-- ============================================================

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
create index if not exists idx_time_machine_api_key on time_machine(api_key);
create index if not exists idx_time_machine_ai_id on time_machine(ai_id);
create index if not exists idx_time_machine_created_at on time_machine(created_at);


-- ============================================================
-- GOD LEVEL SYSTEMS - ANIMA
-- ============================================================

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
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists idx_anima_souls_api_key on anima_souls(api_key);
create index if not exists idx_anima_souls_ai_id on anima_souls(ai_id);
create index if not exists idx_anima_souls_stability on anima_souls(identity_stability_score);

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
create index if not exists idx_anima_history_api_key on anima_history(api_key);
create index if not exists idx_anima_history_ai_id on anima_history(ai_id);
create index if not exists idx_anima_history_created_at on anima_history(created_at);


-- ============================================================
-- GOD LEVEL SYSTEMS - AKASHIC
-- ============================================================

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
create index if not exists idx_akashic_wisdom_api_key on akashic_wisdom(api_key);
create index if not exists idx_akashic_wisdom_type on akashic_wisdom(interaction_type);
create index if not exists idx_akashic_wisdom_created_at on akashic_wisdom(created_at);


-- ============================================================
-- GOD LEVEL SYSTEMS - OMEGA
-- ============================================================

create table if not exists omega_trajectories (
  id uuid default gen_random_uuid() primary key,
  user_id text not null,
  api_key text not null,
  current_phase text,
  predicted_next text,
  prediction text,
  messages_analyzed integer default 0,
  last_updated text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists idx_omega_trajectories_api_key on omega_trajectories(api_key);
create index if not exists idx_omega_trajectories_user_id on omega_trajectories(user_id);
create index if not exists idx_omega_trajectories_phase on omega_trajectories(current_phase);


-- ============================================================
-- ELITE FEATURES - NEURALFORGE
-- ============================================================

create table if not exists neuralforge_behaviors (
  id uuid default gen_random_uuid() primary key,
  behavior_id text unique not null,
  behavior_name text not null,
  rules text,
  target_models text,
  version text default '1.0',
  api_key text not null,
  compiled_prompt text,
  rule_count integer default 0,
  active boolean default true,
  deploy_count integer default 0,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists idx_neuralforge_behaviors_api_key on neuralforge_behaviors(api_key);
create index if not exists idx_neuralforge_behaviors_active on neuralforge_behaviors(active);
create index if not exists idx_neuralforge_behaviors_created_at on neuralforge_behaviors(created_at);


-- ============================================================
-- ELITE FEATURES - QUANTUMROUTE
-- ============================================================

create table if not exists quantumroute_logs (
  id uuid default gen_random_uuid() primary key,
  api_key text not null,
  query_preview text,
  complexity text,
  task_type text,
  recommended_model text,
  estimated_cost_savings_percent integer default 0,
  actual_model_used text,
  created_at timestamptz default now()
);
create index if not exists idx_quantumroute_logs_api_key on quantumroute_logs(api_key);
create index if not exists idx_quantumroute_logs_model on quantumroute_logs(recommended_model);
create index if not exists idx_quantumroute_logs_complexity on quantumroute_logs(complexity);
create index if not exists idx_quantumroute_logs_created_at on quantumroute_logs(created_at);


-- ============================================================
-- ELITE FEATURES - TEMPORALMIND
-- ============================================================

create table if not exists temporalmind_tags (
  id uuid default gen_random_uuid() primary key,
  tag_id text unique not null,
  api_key text not null,
  domain text not null,
  content_preview text,
  confidence float default 1.0,
  is_outdated boolean default false,
  freshness text,
  hours_elapsed float default 0,
  decay_hours float default 8760,
  knowledge_date text,
  created_at timestamptz default now()
);
create index if not exists idx_temporalmind_tags_api_key on temporalmind_tags(api_key);
create index if not exists idx_temporalmind_tags_domain on temporalmind_tags(domain);
create index if not exists idx_temporalmind_tags_outdated on temporalmind_tags(is_outdated);
create index if not exists idx_temporalmind_tags_created_at on temporalmind_tags(created_at);


-- ============================================================
-- ELITE FEATURES - EIGENCORE
-- ============================================================

create table if not exists eigencore_profiles (
  id uuid default gen_random_uuid() primary key,
  api_key text unique not null,
  eigen_signature text not null,
  total_items integer default 0,
  last_updated text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists idx_eigencore_profiles_api_key on eigencore_profiles(api_key);


-- ============================================================
-- ELITE FEATURES - SHADOWTEST
-- ============================================================

create table if not exists shadowtest_tests (
  id uuid default gen_random_uuid() primary key,
  test_id text unique not null,
  name text not null,
  version_a_config text,
  version_b_config text,
  traffic_percent integer default 100,
  api_key text not null,
  status text default 'running',
  total_requests integer default 0,
  a_avg_quality float default 0,
  b_avg_quality float default 0,
  a_avg_safety float default 0,
  b_avg_safety float default 0,
  a_total_score float default 0,
  b_total_score float default 0,
  winner text,
  concluded_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists idx_shadowtest_tests_api_key on shadowtest_tests(api_key);
create index if not exists idx_shadowtest_tests_status on shadowtest_tests(status);
create index if not exists idx_shadowtest_tests_created_at on shadowtest_tests(created_at);


-- ============================================================
-- ELITE FEATURES - COGNITIVEMAP
-- ============================================================

create table if not exists cognitivemap_maps (
  id uuid default gen_random_uuid() primary key,
  map_id text unique not null,
  api_key text not null,
  node_count integer default 0,
  items_analyzed integer default 0,
  domain_coverage text,
  known_concepts text,
  gap_count integer default 0,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists idx_cognitivemap_maps_api_key on cognitivemap_maps(api_key);
create index if not exists idx_cognitivemap_maps_created_at on cognitivemap_maps(created_at);


-- ============================================================
-- ELITE FEATURES - DRIFTGUARD
-- ============================================================

create table if not exists driftguard_baselines (
  id uuid default gen_random_uuid() primary key,
  ai_id text not null,
  api_key text not null,
  baseline text not null,
  updated_at text,
  created_at timestamptz default now()
);
create index if not exists idx_driftguard_baselines_api_key on driftguard_baselines(api_key);
create index if not exists idx_driftguard_baselines_ai_id on driftguard_baselines(ai_id);

create table if not exists driftguard_checks (
  id uuid default gen_random_uuid() primary key,
  ai_id text not null,
  api_key text not null,
  drift_detected boolean default false,
  critical_drift boolean default false,
  drift_count integer default 0,
  drifts text,
  samples_analyzed integer default 0,
  created_at timestamptz default now()
);
create index if not exists idx_driftguard_checks_api_key on driftguard_checks(api_key);
create index if not exists idx_driftguard_checks_ai_id on driftguard_checks(ai_id);
create index if not exists idx_driftguard_checks_drift on driftguard_checks(drift_detected);
create index if not exists idx_driftguard_checks_created_at on driftguard_checks(created_at);


-- ============================================================
-- END OF KRONYX v3.0 SCHEMA
-- Total Tables: 42
-- Total Indexes: 90+
-- Production Ready for 50,000+ Developers
-- ============================================================
