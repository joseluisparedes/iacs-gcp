export type Role = 'Solicitante' | 'Aprobador' | 'Administrador' | 'Entrenador IA';

export type Status = 
  | 'Borrador' 
  | 'Chat pendiente'
  | 'Pendiente de aprobación' 
  | 'Observada' 
  | 'Desestimada' 
  | 'En demanda';

export type FieldType = 'text' | 'date' | 'select' | 'file';

export interface FieldDefinition {
  id: string;
  label: string;
  key: string;
  field_type: FieldType;
  options: any;
  is_visible: boolean;
  is_required: boolean;
  sort_order: number;
  section?: 'form' | 'ai';
  depends_on?: string;
  options_map?: Record<string, string[]>;
  ai_instructions?: string;
  allow_multiple?: boolean;
  help_text?: string;
  requires_confirmation?: boolean;
  ask_in_initial_form?: boolean;
}

export interface Initiative {
  id: string;
  created_at: string;
  updated_at: string;
  status: Status;
  form_data: Record<string, any>;
  chat_history: Array<{ role: string; text: string }>;
  summary?: Record<string, any>;
  rejection_reason?: string;
  user_id?: string;
  confirmed_fields?: Record<string, boolean>;
  unstructured_text?: string;
  workflow_version?: string;
  current_node_id?: string;
}

export interface WorkflowTransitionResult {
  allowed: boolean;
  reason?: string;
  missing_fields?: string[];
  next_node_id?: string;
  next_node_label?: string;
}

export interface StageForm {
  id: string;
  code: string;
  name: string;
  description?: string;
  fields: Array<Record<string, any>>;
  is_active: boolean;
}

export interface StageConsent {
  id: string;
  code: string;
  title: string;
  statement: string;
  version: number;
  is_active: boolean;
}

export interface InitiativeStageRecord {
  id: string;
  initiative_id: string;
  node_id: string;
  stage_name?: string;
  form_id?: string;
  consent_id?: string;
  user_name?: string;
  user_role?: string;
  form_data: Record<string, any>;
  consent_accepted: boolean;
  consent_text_snapshot?: string;
  action_taken: string;
  submitted_at: string;
}
