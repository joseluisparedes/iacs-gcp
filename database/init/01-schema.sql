-- ==============================================================================
-- IACS GCP — ESQUEMA COMPLETO DE BASE DE DATOS (PostgreSQL 17)
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 1. ESTRUCTURA ORGANIZACIONAL (VPs y Direcciones)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vps (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  bp_name TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS direcciones (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  vp_id UUID REFERENCES vps(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(name, vp_id)
);

-- ------------------------------------------------------------------------------
-- 2. GOBERNANZA, USUARIOS Y RBAC MULTINIVEL
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app_roles (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  color TEXT DEFAULT 'indigo',
  is_system BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS allowed_users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  vp_id UUID REFERENCES vps(id) ON DELETE SET NULL,
  direccion_id UUID REFERENCES direcciones(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_roles_whitelist (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  allowed_user_id UUID REFERENCES allowed_users(id) ON DELETE CASCADE,
  role TEXT NOT NULL,
  vp_id UUID REFERENCES vps(id) ON DELETE CASCADE,
  direcciones_ids UUID[] DEFAULT '{}',
  is_transversal BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS profiles (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  vp_id UUID REFERENCES vps(id) ON DELETE SET NULL,
  direccion_id UUID REFERENCES direcciones(id) ON DELETE SET NULL,
  avatar_url TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS profile_roles (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  role TEXT NOT NULL,
  vp_id UUID REFERENCES vps(id) ON DELETE CASCADE,
  direcciones_ids UUID[] DEFAULT '{}',
  is_transversal BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 3. CONFIGURACIÓN DEL SITIO Y CAMPOS DINÁMICOS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS site_settings (
  id INT PRIMARY KEY DEFAULT 1,
  maintenance_mode BOOLEAN DEFAULT false,
  system_notice TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS initiative_fields (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  label TEXT NOT NULL,
  key TEXT UNIQUE NOT NULL,
  field_type TEXT NOT NULL,
  options JSONB DEFAULT '[]'::jsonb,
  is_visible BOOLEAN DEFAULT true,
  is_required BOOLEAN DEFAULT false,
  sort_order INT DEFAULT 0,
  section TEXT DEFAULT 'form',
  depends_on TEXT,
  options_map JSONB DEFAULT '{}'::jsonb,
  ai_instructions TEXT,
  allow_multiple BOOLEAN DEFAULT false,
  help_text TEXT,
  requires_confirmation BOOLEAN DEFAULT false,
  ask_in_initial_form BOOLEAN DEFAULT false,
  file_options JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_table_preferences (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  table_id TEXT NOT NULL,
  preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, table_id)
);

-- ------------------------------------------------------------------------------
-- 4. MOTOR DE FLUJOS DE TRABAJO (WORKFLOW ENGINE)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS workflow_definitions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  version INT NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
  graph_json JSONB NOT NULL DEFAULT '{"nodes":[],"edges":[]}'::jsonb,
  description TEXT,
  created_by UUID REFERENCES profiles(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  published_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS workflow_definitions_one_published
  ON workflow_definitions(status) WHERE status = 'published';

CREATE TABLE IF NOT EXISTS workflow_node_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id UUID NOT NULL REFERENCES workflow_definitions(id) ON DELETE CASCADE,
  node_id TEXT NOT NULL,
  role_name TEXT NOT NULL,
  can_edit BOOLEAN NOT NULL DEFAULT false,
  can_approve BOOLEAN NOT NULL DEFAULT false,
  can_reject BOOLEAN NOT NULL DEFAULT false,
  required_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_workflow_node_roles_lookup ON workflow_node_roles(workflow_id, node_id);

CREATE TABLE IF NOT EXISTS workflow_transitions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id UUID NOT NULL REFERENCES workflow_definitions(id) ON DELETE CASCADE,
  edge_id TEXT NOT NULL,
  label TEXT NOT NULL,
  source_node_id TEXT NOT NULL,
  target_node_id TEXT NOT NULL,
  condition_type TEXT NOT NULL CHECK (condition_type IN ('always', 'field_required', 'vobo_check', 'role_only')),
  condition_config JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_workflow_transitions_lookup ON workflow_transitions(workflow_id, source_node_id);

CREATE TABLE IF NOT EXISTS workflow_role_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id UUID NOT NULL REFERENCES workflow_definitions(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  role_name TEXT NOT NULL,
  assigned_by UUID REFERENCES profiles(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(workflow_id, user_id, role_name)
);
CREATE INDEX IF NOT EXISTS idx_workflow_role_assignments_lookup ON workflow_role_assignments(workflow_id, user_id);

CREATE TABLE IF NOT EXISTS workflow_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id UUID REFERENCES workflow_definitions(id),
  actor_id UUID REFERENCES profiles(id),
  action TEXT NOT NULL,
  details JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 5. FORMULARIOS DE ETAPA, CONSENTIMIENTOS Y PLANTILLAS DE DICTAMEN
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stage_forms (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  fields JSONB NOT NULL DEFAULT '[]'::jsonb,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS stage_consents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  statement TEXT NOT NULL,
  version INT DEFAULT 1,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  template_html TEXT NOT NULL,
  margins JSONB DEFAULT '{"top": 20, "right": 20, "bottom": 20, "left": 20}'::jsonb,
  is_active BOOLEAN DEFAULT true,
  is_default BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 6. GESTIÓN DE INICIATIVAS Y EXPEDIENTE DE ETAPAS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS initiatives (
  id TEXT PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  status TEXT NOT NULL DEFAULT 'Borrador',
  form_data JSONB NOT NULL DEFAULT '{}'::jsonb,
  chat_history JSONB NOT NULL DEFAULT '[]'::jsonb,
  summary JSONB DEFAULT '{}'::jsonb,
  rejection_reason TEXT,
  user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
  confirmed_fields JSONB DEFAULT '{}'::jsonb,
  unstructured_text TEXT,
  workflow_version TEXT,
  current_node_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_initiatives_status ON initiatives(status);
CREATE INDEX IF NOT EXISTS idx_initiatives_user ON initiatives(user_id);
CREATE INDEX IF NOT EXISTS idx_initiatives_workflow ON initiatives(workflow_version, current_node_id);

CREATE TABLE IF NOT EXISTS initiative_stage_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  initiative_id TEXT NOT NULL REFERENCES initiatives(id) ON DELETE CASCADE,
  node_id TEXT NOT NULL,
  stage_name TEXT,
  form_id UUID REFERENCES stage_forms(id) ON DELETE SET NULL,
  consent_id UUID REFERENCES stage_consents(id) ON DELETE SET NULL,
  user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
  user_name TEXT,
  user_role TEXT,
  form_data JSONB DEFAULT '{}'::jsonb,
  consent_accepted BOOLEAN DEFAULT true,
  consent_text_snapshot TEXT,
  action_taken TEXT DEFAULT 'approved',
  submitted_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_stage_records_init ON initiative_stage_records(initiative_id);
CREATE INDEX IF NOT EXISTS idx_stage_records_node ON initiative_stage_records(node_id);

-- ------------------------------------------------------------------------------
-- 7. BASE DE CONOCIMIENTO Y ENTRENAMIENTO DE IA (TEO)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_knowledge_folders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  parent_id UUID REFERENCES ai_knowledge_folders(id) ON DELETE CASCADE,
  level INT NOT NULL DEFAULT 1 CHECK (level >= 1 AND level <= 3),
  sort_order INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_training_config (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  layer TEXT NOT NULL CHECK (layer IN ('identity', 'context', 'examples', 'guardrails', 'settings')),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  is_active BOOLEAN DEFAULT true,
  sort_order INT DEFAULT 0,
  source TEXT DEFAULT 'manual',
  folder_id UUID REFERENCES ai_knowledge_folders(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ai_training_folder ON ai_training_config(folder_id);

CREATE TABLE IF NOT EXISTS ai_feedback (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  initiative_id TEXT,
  message_index INT DEFAULT 0,
  user_message TEXT NOT NULL,
  agent_response TEXT NOT NULL,
  rating TEXT NOT NULL CHECK (rating IN ('positive', 'negative')),
  admin_approved BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  task_id TEXT,
  agent_name TEXT NOT NULL,
  action TEXT NOT NULL,
  status TEXT DEFAULT 'in_progress',
  progress INT DEFAULT 0,
  details JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 8. COMUNICACIONES Y AUDITORÍA
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS email_logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  initiative_id TEXT,
  recipient TEXT NOT NULL,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS notifications (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  link TEXT,
  is_read BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);
