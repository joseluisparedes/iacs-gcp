<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { 
  Trash2, 
  Settings2, 
  Layers, 
  GitFork, 
  Check, 
  X, 
  ArrowRight,
  Info,
  Clock,
  Send,
  AlertTriangle,
  AlertCircle,
  GitCommit,
  CheckCircle2,
  Archive,
  Search,
  FileCheck2,
  Paperclip,
  RotateCcw,
  Tag,
  Building2,
  Shuffle,
  Lock,
  Sparkles,
  Pencil,
  ExternalLink,
  Plus
} from 'lucide-vue-next';
import { DEFAULT_MACRO_STAGES, type MacroStageDef } from '~/utils/macroStages';

interface DynamicRole {
  id?: string;
  code: string;
  name: string;
  description?: string;
  color?: string;
  is_system?: boolean;
  is_active?: boolean;
}

interface WorkflowNodeRole {
  role_name: string;
  can_edit: boolean;
  can_approve: boolean;
  can_reject: boolean;
}

interface SystemUser {
  id: string;
  name: string;
  email: string;
  user_roles_whitelist?: Array<{ role: string }>;
  roles?: string[];
}

const props = withDefaults(defineProps<{
  selectedNode: any | null;
  selectedEdge: any | null;
  totalNodes: number;
  totalEdges: number;
  nodes?: any[];
  edges?: any[];
  stageForms?: any[];
  stageConsents?: any[];
  documentTemplates?: any[];
  systemRoles?: DynamicRole[];
  users?: SystemUser[];
  macroStages?: MacroStageDef[];
}>(), {
  nodes: () => [],
  edges: () => [],
  stageForms: () => [],
  stageConsents: () => [],
  documentTemplates: () => [],
  systemRoles: () => [],
  users: () => [],
  macroStages: () => [],
});

const emit = defineEmits<{
  (e: 'update-node', payload: any): void;
  (e: 'update-edge', payload: any): void;
  (e: 'delete-selected'): void;
  (e: 'open-macro-stages-modal'): void;
}>();

const activeTab = ref<'props' | 'roles' | 'custody' | 'ai'>('props');
const roleSearch = ref('');
const roleFilter = ref<'all' | 'assigned'>('all');
const newObservationCategory = ref('');

// Configuración por defecto para estados observados
const DEFAULT_OBSERVATION_CATEGORIES: string[] = [
  'General',
  'Documentación incompleta',
  'Alcance técnico',
  'Presupuesto / Costos',
  'Visto Bueno / VoBo',
];

const DEFAULT_OBSERVATION_FILE_OPTIONS = {
  allowMultiple: true,
  maxFiles: 5,
  fileTypes: {
    pdf: { enabled: true, maxMb: 25 },
    docx: { enabled: true, maxMb: 25 },
    xlsx: { enabled: true, maxMb: 25 },
    image: { enabled: true, maxMb: 25 },
    txt: { enabled: true, maxMb: 10 },
  },
};

const DEFAULT_SYSTEM_ROLES: DynamicRole[] = [
  { code: 'registrador', name: 'Key user', color: 'emerald', is_system: true },
  { code: 'bp_ti', name: 'Business Partner (BP TI)', color: 'indigo', is_system: true },
  { code: 'business_owner', name: 'Business Owner (BO)', color: 'violet', is_system: false },
  { code: 'vicepresidente_del_negocio', name: 'Vicepresidente (VP)', color: 'violet', is_system: false },
  { code: 'gestor_de_la_demanda', name: 'Gestor de la Demanda', color: 'violet', is_system: false },
  { code: 'lider_de_dominio', name: 'Líder de Dominio TI', color: 'violet', is_system: false },
  { code: 'admin', name: 'Administrador General', color: 'rose', is_system: true },
  { code: 'invitado', name: 'Invitado (Solo lectura)', color: 'slate', is_system: true },
];

const ROLE_SWATCHES: Record<string, { swatch: string; bg: string; text: string; border: string }> = {
  indigo: { swatch: '#6366F1', bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200' },
  blue: { swatch: '#3B82F6', bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  emerald: { swatch: '#10B981', bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
  violet: { swatch: '#8B5CF6', bg: 'bg-violet-50', text: 'text-violet-700', border: 'border-violet-200' },
  amber: { swatch: '#F59E0B', bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
  rose: { swatch: '#F43F5E', bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200' },
  red: { swatch: '#EF4444', bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200' },
  cyan: { swatch: '#06B6D4', bg: 'bg-cyan-50', text: 'text-cyan-700', border: 'border-cyan-200' },
  slate: { swatch: '#64748B', bg: 'bg-slate-100', text: 'text-slate-700', border: 'border-slate-200' },
};

const COLOR_PRESETS = [
  { name: 'Por defecto', bg: '#EB5F46', border: '#EB5F46', text: '#FFFFFF', isDefault: true },
  { name: 'Índigo', bg: '#EEF2FF', border: '#4F5AF5', text: '#4F5AF5' },
  { name: 'Esmeralda', bg: '#ECFDF5', border: '#10B981', text: '#047857' },
  { name: 'Ámbar', bg: '#FFFBEB', border: '#F59E0B', text: '#B45309' },
  { name: 'Carmesí', bg: '#FFF1F2', border: '#F43F5E', text: '#BE123C' },
  { name: 'Violeta', bg: '#F5F3FF', border: '#8B5CF6', text: '#6D28D9' },
  { name: 'Cyan', bg: '#ECFEFF', border: '#06B6D4', text: '#0E7490' },
  { name: 'Pizarra', bg: '#F8FAFC', border: '#64748B', text: '#334155' },
  { name: 'Oscuro', bg: '#1E293B', border: '#0F172A', text: '#FFFFFF' },
];

const nodeData = computed(() => props.selectedNode?.data || {});
const edgeData = computed(() => props.selectedEdge?.data || {});

// Available Roles merged
const availableRoles = computed<DynamicRole[]>(() => {
  if (props.systemRoles && props.systemRoles.length > 0) {
    return props.systemRoles;
  }
  return DEFAULT_SYSTEM_ROLES;
});

// Roles asignados normalizados
const assignedRoles = computed<WorkflowNodeRole[]>(() => {
  const raw: WorkflowNodeRole[] = nodeData.value.roles || [];
  return raw;
});

// Usuarios normalizados con sus roles
const normalizedUsers = computed(() => {
  return props.users.map((u) => {
    let userRoles: string[] = [];
    if (Array.isArray(u.roles)) {
      userRoles = u.roles;
    } else if (Array.isArray(u.user_roles_whitelist)) {
      userRoles = u.user_roles_whitelist.map((r) => r.role);
    }
    return {
      id: u.id,
      name: u.name || u.email,
      email: u.email,
      roles: userRoles,
    };
  });
});

// Usuarios filtrados para el rol seleccionado en Salto Manual
const filteredUsersForManualMove = computed(() => {
  if (!nodeData.value.manualStateMoveRole) return [];
  return normalizedUsers.value.filter((u) => u.roles.includes(nodeData.value.manualStateMoveRole));
});

// Is AI Node
const isAINode = computed(() => {
  const type = nodeData.value.nodeType || props.selectedNode?.type;
  return type === 'ai_agent' || type === 'ai_text' || props.selectedNode?.id === 'ai_chat';
});

// Is Gateway Node
const isGatewayNode = computed(() => {
  const type = nodeData.value.nodeType || props.selectedNode?.type;
  return type === 'gateway' || props.selectedNode?.id?.startsWith('gw_');
});

// Outgoing & incoming edges for Gateway
const outgoingEdges = computed(() => {
  if (!props.selectedNode) return [];
  return props.edges.filter((e) => e.source === props.selectedNode.id);
});

const incomingEdges = computed(() => {
  if (!props.selectedNode) return [];
  return props.edges.filter((e) => e.target === props.selectedNode.id);
});

// Macro-Etapas configuradas activas en el flujo (Stepper)
const configuredMacroStages = computed<MacroStageDef[]>(() => {
  if (Array.isArray(props.macroStages) && props.macroStages.length > 0) {
    return props.macroStages;
  }
  return DEFAULT_MACRO_STAGES;
});

// Comprueba si el nodo seleccionado es la cabecera principal de una Macro-Etapa
const isSelfMacroStage = computed(() => {
  if (!props.selectedNode) return null;
  const currentId = props.selectedNode.id;
  const stages = configuredMacroStages.value;
  const idx = stages.findIndex(s => s.id === currentId);
  if (idx !== -1) {
    return {
      index: idx + 1,
      stage: stages[idx]
    };
  }
  return null;
});

// Comprueba si el nodo seleccionado es un sub-estado subordinado a alguna Macro-Etapa
const parentStageInfo = computed(() => {
  if (!props.selectedNode) return null;
  const currentId = props.selectedNode.id;
  const stages = configuredMacroStages.value;

  // Si ya es cabecera principal, no es sub-estado
  if (stages.some(s => s.id === currentId)) return null;

  // 1. Revisar parent_stage_id directo
  const parentId = props.selectedNode.data?.parent_stage_id;
  if (parentId) {
    const idx = stages.findIndex(s => s.id === parentId);
    if (idx !== -1) {
      return { index: idx + 1, id: stages[idx].id, name: stages[idx].name };
    }
  }

  // 2. Revisar si está en los nodeIds de alguna etapa
  const idx = stages.findIndex(s => s.id !== currentId && Array.isArray(s.nodeIds) && s.nodeIds.includes(currentId));
  if (idx !== -1) {
    return { index: idx + 1, id: stages[idx].id, name: stages[idx].name };
  }

  return null;
});

// Nodos candidatos adicionales que no están en la lista de macro-etapas
const availableOtherNodes = computed(() => {
  if (!props.selectedNode) return [];
  const currentId = props.selectedNode.id;
  const macroIds = new Set(configuredMacroStages.value.map(s => s.id));
  return (props.nodes || [])
    .filter((n: any) => n.id !== currentId && n.type !== 'gateway' && !n.id.startsWith('gw_') && !macroIds.has(n.id))
    .map((n: any) => ({
      id: n.id,
      label: n.data?.label || n.id,
      role: n.data?.roles?.[0]?.role_name || '',
    }));
});

// Actualizar un campo del nodo seleccionado
const updateField = (key: string, value: any) => {
  if (!props.selectedNode) return;
  emit('update-node', {
    ...nodeData.value,
    [key]: value
  });
};

// Actualizar un campo de la arista seleccionada
const updateEdgeField = (key: string, value: any) => {
  if (!props.selectedEdge) return;
  if (key === 'label') {
    emit('update-edge', {
      label: value,
      data: { ...edgeData.value }
    });
  } else {
    emit('update-edge', {
      label: props.selectedEdge.label,
      data: {
        ...edgeData.value,
        [key]: value
      }
    });
  }
};

// Toggle Role en el nodo
const handleRoleToggle = (roleCode: string) => {
  const current: WorkflowNodeRole[] = [...assignedRoles.value];
  const idx = current.findIndex((r) => r.role_name === roleCode);
  if (idx >= 0) {
    current.splice(idx, 1);
  } else {
    current.push({
      role_name: roleCode,
      can_edit: roleCode === 'registrador' || roleCode === 'admin',
      can_approve: true,
      can_reject: true,
    });
  }
  updateField('roles', current);
};

// Toggle permiso can_edit de un rol
const handleRolePermissionChange = (roleCode: string, perm: 'can_edit' | 'can_approve' | 'can_reject', value: boolean) => {
  const current: WorkflowNodeRole[] = assignedRoles.value.map((r) => {
    if (r.role_name === roleCode) {
      return { ...r, [perm]: value };
    }
    return r;
  });
  updateField('roles', current);
};

// Agregar nueva categoría de observación
const addObservationCategory = () => {
  const trimmed = newObservationCategory.value.trim();
  if (!trimmed) return;
  const current: string[] = [...(nodeData.value.observationCategories || DEFAULT_OBSERVATION_CATEGORIES)];
  if (!current.some((c) => c.toLowerCase() === trimmed.toLowerCase())) {
    current.push(trimmed);
    updateField('observationCategories', current);
  }
  newObservationCategory.value = '';
};

// Eliminar categoría de observación
const removeObservationCategory = (cat: string) => {
  const current: string[] = (nodeData.value.observationCategories || DEFAULT_OBSERVATION_CATEGORIES).filter((c: string) => c !== cat);
  updateField('observationCategories', current);
};

// Restablecer categorías por defecto
const resetObservationCategories = () => {
  updateField('observationCategories', [...DEFAULT_OBSERVATION_CATEGORIES]);
};

// Toggle Edge Role (Transition RBAC)
const toggleEdgeRole = (roleCode: string) => {
  if (!props.selectedEdge) return;
  const current: string[] = [...(edgeData.value.allowed_roles || [])];
  const idx = current.indexOf(roleCode);
  if (idx >= 0) {
    current.splice(idx, 1);
  } else {
    current.push(roleCode);
  }
  updateEdgeField('allowed_roles', current);
};

// Search, filter and fast-action helpers for Edge RBAC Roles
const edgeRoleSearch = ref('');
const edgeRoleFilterTab = ref<'all' | 'selected'>('all');

const getRoleDisplayName = (code: string) => {
  const found = availableRoles.value.find(r => r.code === code);
  return found?.name || code;
};

const clearAllEdgeRoles = () => {
  if (!props.selectedEdge) return;
  updateEdgeField('allowed_roles', []);
};

const selectAllEdgeRoles = () => {
  if (!props.selectedEdge) return;
  updateEdgeField('allowed_roles', availableRoles.value.map(r => r.code));
};

const removeEdgeRole = (roleCode: string) => {
  if (!props.selectedEdge) return;
  const current = (edgeData.value.allowed_roles || []).filter((c: string) => c !== roleCode);
  updateEdgeField('allowed_roles', current);
};

const filteredAvailableRoles = computed(() => {
  let list = availableRoles.value;
  const q = edgeRoleSearch.value.trim().toLowerCase();
  if (q) {
    list = list.filter(r => r.name.toLowerCase().includes(q) || r.code.toLowerCase().includes(q));
  }
  if (edgeRoleFilterTab.value === 'selected') {
    const selectedCodes = edgeData.value.allowed_roles || [];
    list = list.filter(r => selectedCodes.includes(r.code));
  }
  return list;
});

// Color Presets para Flechas
const applyColorPreset = (preset: any) => {
  if (!props.selectedEdge) return;
  updateEdgeField('style_config', {
    button_bg: preset.bg,
    button_color: preset.border,
    label_color: preset.text,
  });
};

const updateCustomColor = (colorKey: string, hexValue: string) => {
  if (!props.selectedEdge) return;
  updateEdgeField('style_config', {
    ...(edgeData.value.style_config || {}),
    [colorKey]: hexValue,
  });
};

const resetEdgeStyle = () => {
  if (!props.selectedEdge) return;
  const def = COLOR_PRESETS.find(p => p.isDefault) || COLOR_PRESETS[0];
  updateEdgeField('style_config', {
    button_bg: def.bg,
    button_color: def.border,
    label_color: def.text,
  });
};

const isPresetActive = (preset: any) => {
  const cfg = edgeData.value.style_config || {};
  const hasCustom = Boolean(cfg.button_bg || cfg.button_color || cfg.label_color);
  if (!hasCustom && preset.isDefault) return true;
  return cfg.button_color === preset.border && (cfg.button_bg === preset.bg || (!cfg.button_bg && preset.bg === '#EB5F46'));
};

// Gateway Config Helpers
const gatewayConfig = computed(() => {
  return nodeData.value.gatewayConfig || {
    variable: props.selectedNode?.id === 'gw_presupuesto' ? 'requiere_presupuesto' : '',
    rules: [],
  };
});

const getRuleForEdge = (edge: any) => {
  if (!edge) return null;
  const rules: any[] = gatewayConfig.value.rules || [];
  return rules.find((r: any) => r.edgeId === edge.id || (edge.target && r.targetNodeId === edge.target)) || null;
};

const updateGatewayConfig = (updates: any) => {
  updateField('gatewayConfig', {
    ...gatewayConfig.value,
    ...updates,
  });
};

const updateBranchRule = (edgeId: string, targetNodeId: string, updates: any) => {
  const currentRules: any[] = gatewayConfig.value.rules || [];
  const idx = currentRules.findIndex((r: any) => r.edgeId === edgeId || (targetNodeId && r.targetNodeId === targetNodeId));
  let nextRules: any[];
  if (idx >= 0) {
    nextRules = currentRules.map((r, i) => (i === idx ? { ...r, edgeId, targetNodeId, ...updates } : r));
  } else {
    nextRules = [
      ...currentRules,
      { edgeId, targetNodeId, operator: 'equals', value: '', ...updates },
    ];
  }
  updateGatewayConfig({ rules: nextRules });
};

// File Types definition for observation files
const FILE_TYPE_DEFS = [
  { key: 'pdf', label: 'PDF', ext: '.pdf', color: 'text-rose-600' },
  { key: 'docx', label: 'Word', ext: '.docx', color: 'text-blue-600' },
  { key: 'xlsx', label: 'Excel', ext: '.xlsx,.xls', color: 'text-emerald-600' },
  { key: 'image', label: 'Imágenes / Diagramas', ext: '.png,.jpg,.drawio', color: 'text-violet-600' },
  { key: 'txt', label: 'Texto Plano', ext: '.txt', color: 'text-slate-600' },
];

// Catalog of decision variables for Gateways
const SYSTEM_GATEWAY_VARIABLES = [
  { key: 'requiere_presupuesto', label: '¿Requiere Presupuesto? (requiere_presupuesto)' },
  { key: 'tipo_solucion', label: 'Tipo de Solución (tipo_solucion)' },
  { key: 'prioridad_area', label: 'Prioridad del Área (prioridad_area)' },
  { key: 'presupuesto_estimado_usd', label: 'Presupuesto Estimado USD (presupuesto_estimado_usd)' },
  { key: 'es_proyecto_spo', label: '¿Es Proyecto SPO? (es_proyecto_spo)' },
  { key: 'es_un_proceso_nuevo', label: '¿Es Proceso Nuevo? (es_un_proceso_nuevo)' },
  { key: 'institucion', label: 'Institución / Empresa (institucion)' },
  { key: 'vicepresidencia', label: 'Vicepresidencia (vicepresidencia)' },
  { key: 'direccion', label: 'Dirección (direccion)' },
  { key: 'pilar_estrategico', label: 'Pilar Estratégico (pilar_estrategico)' },
];

// Helper to resolve stage form for a given node
const getNodeStageForm = (node: any) => {
  if (!node) return null;
  const formRef = node.data?.form_id;
  if (!formRef) return null;
  return (props.stageForms || []).find((f: any) => f.id === formRef || f.code === formRef) || null;
};

// Direct Incoming Nodes to the Gateway
const directIncomingNodes = computed(() => {
  if (!props.selectedNode) return [];
  const currentId = props.selectedNode.id;
  const inEdges = (props.edges || []).filter((e: any) => e.target === currentId);
  const sourceIds = Array.from(new Set(inEdges.map((e: any) => e.source)));
  return sourceIds
    .map(id => (props.nodes || []).find((n: any) => n.id === id))
    .filter(Boolean);
});

// Direct incoming forms with their nodes
const directIncomingFormItems = computed(() => {
  return directIncomingNodes.value.map((node: any) => {
    const form = getNodeStageForm(node);
    return {
      nodeId: node.id,
      nodeLabel: node.data?.label || node.id,
      form,
    };
  });
});

// Upstream Nodes (BFS backwards traversal through props.edges)
const upstreamNodes = computed(() => {
  if (!props.selectedNode) return [];
  const directIds = new Set(directIncomingNodes.value.map((n: any) => n.id));
  const visited = new Set<string>();
  const queue: string[] = [];

  directIds.forEach(id => {
    visited.add(id);
    queue.push(id);
  });

  const result: any[] = [];

  while (queue.length > 0) {
    const currentId = queue.shift()!;
    const incomingToCurrent = (props.edges || []).filter((e: any) => e.target === currentId);
    for (const edge of incomingToCurrent) {
      if (edge.source && !visited.has(edge.source) && edge.source !== props.selectedNode.id) {
        visited.add(edge.source);
        const sourceNode = (props.nodes || []).find((n: any) => n.id === edge.source);
        if (sourceNode) {
          result.push(sourceNode);
          queue.push(edge.source);
        }
      }
    }
  }

  return result;
});

// Grouped variables for the Gateway decision dropdown
interface GatewayVarOption {
  key: string;
  label: string;
  type?: string;
  sourceLabel?: string;
}

interface GatewayVarGroup {
  id: string;
  label: string;
  options: GatewayVarOption[];
}

const gatewayVariableGroups = computed<GatewayVarGroup[]>(() => {
  const groups: GatewayVarGroup[] = [];
  const addedKeys = new Set<string>();

  // 1. Direct Incoming Node Forms
  directIncomingNodes.value.forEach((node: any) => {
    const form = getNodeStageForm(node);
    const nodeLabel = node.data?.label || node.id;
    if (form && Array.isArray(form.fields) && form.fields.length > 0) {
      const opts: GatewayVarOption[] = [];
      form.fields.forEach((f: any) => {
        const key = f.key || f.id;
        if (key && !addedKeys.has(key)) {
          addedKeys.add(key);
          const typeBadge = f.type ? ` [${f.type}]` : '';
          opts.push({
            key,
            label: `${f.label || f.name || key}${typeBadge} (${key})`,
            type: f.type,
            sourceLabel: `${nodeLabel} - ${form.name}`,
          });
        }
      });
      if (opts.length > 0) {
        groups.push({
          id: `direct-${node.id}`,
          label: `📥 Entrada Directa: ${nodeLabel} (${form.name})`,
          options: opts,
        });
      }
    }
  });

  // 2. Upstream Node Forms
  upstreamNodes.value.forEach((node: any) => {
    const form = getNodeStageForm(node);
    const nodeLabel = node.data?.label || node.id;
    if (form && Array.isArray(form.fields) && form.fields.length > 0) {
      const opts: GatewayVarOption[] = [];
      form.fields.forEach((f: any) => {
        const key = f.key || f.id;
        if (key && !addedKeys.has(key)) {
          addedKeys.add(key);
          const typeBadge = f.type ? ` [${f.type}]` : '';
          opts.push({
            key,
            label: `${f.label || f.name || key}${typeBadge} (${key})`,
            type: f.type,
            sourceLabel: `${nodeLabel} - ${form.name}`,
          });
        }
      });
      if (opts.length > 0) {
        groups.push({
          id: `upstream-${node.id}`,
          label: `🔄 Ruta Previa: ${nodeLabel} (${form.name})`,
          options: opts,
        });
      }
    }
  });

  // 3. Other Stage Forms (Forms not on the direct path but active in the system)
  (props.stageForms || []).forEach((form: any) => {
    if (Array.isArray(form.fields)) {
      const remainingOpts: GatewayVarOption[] = [];
      form.fields.forEach((f: any) => {
        const key = f.key || f.id;
        if (key && !addedKeys.has(key)) {
          addedKeys.add(key);
          const typeBadge = f.type ? ` [${f.type}]` : '';
          remainingOpts.push({
            key,
            label: `${f.label || f.name || key}${typeBadge} (${key})`,
            type: f.type,
            sourceLabel: form.name,
          });
        }
      });
      if (remainingOpts.length > 0) {
        groups.push({
          id: `other-form-${form.id || form.code}`,
          label: `📄 Formulario: ${form.name}`,
          options: remainingOpts,
        });
      }
    }
  });

  // 4. Global Initiative Attributes
  const globalOpts: GatewayVarOption[] = [];
  SYSTEM_GATEWAY_VARIABLES.forEach((v) => {
    if (!addedKeys.has(v.key)) {
      addedKeys.add(v.key);
      globalOpts.push({
        key: v.key,
        label: v.label,
        type: 'global',
        sourceLabel: 'Iniciativa',
      });
    }
  });
  if (globalOpts.length > 0) {
    groups.push({
      id: 'globals',
      label: '📋 Otros Campos de la Iniciativa',
      options: globalOpts,
    });
  }

  return groups;
});

// Check if a variable key is found in any group
const isVariableInGroups = (varKey: string) => {
  if (!varKey) return false;
  return gatewayVariableGroups.value.some(g => g.options.some(o => o.key === varKey));
};

// Selected variable details
const selectedVarInfo = computed(() => {
  const currentKey = gatewayConfig.value.variable;
  if (!currentKey) return null;
  for (const g of gatewayVariableGroups.value) {
    const found = g.options.find(o => o.key === currentKey);
    if (found) return { ...found, groupLabel: g.label };
  }
  return { key: currentKey, label: currentKey, type: 'custom', groupLabel: 'Personalizado' };
});
</script>

<template>
  <aside class="w-[330px] bg-white border-l border-slate-200 flex flex-col h-full overflow-hidden select-none shrink-0 shadow-2xs text-left">
    <!-- ========================================================================= -->
    <!-- CASO 1: NINGÚN ELEMENTO SELECCIONADO (RESUMEN DEL DIAGRAMA)                -->
    <!-- ========================================================================= -->
    <div v-if="!selectedNode && !selectedEdge" class="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar">
      <div>
        <p class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Propiedades</p>
        <p class="text-xs text-slate-500 mt-0.5">Selecciona un elemento para editar</p>
      </div>

      <div class="p-4 bg-slate-50/80 rounded-2xl border border-slate-200/90 space-y-4 shadow-2xs">
        <div class="flex items-center gap-2">
          <Info class="w-4 h-4 text-[#EB5F46]" />
          <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider">Resumen del Diagrama</h3>
        </div>

        <div class="grid grid-cols-2 gap-3 pt-1">
          <div class="bg-white p-3 rounded-xl border border-slate-200/90 shadow-2xs">
            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Nodos</p>
            <p class="text-2xl font-black text-slate-800 mt-0.5">{{ totalNodes }}</p>
          </div>
          <div class="bg-white p-3 rounded-xl border border-slate-200/90 shadow-2xs">
            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Transiciones</p>
            <p class="text-2xl font-black text-slate-800 mt-0.5">{{ totalEdges }}</p>
          </div>
        </div>

        <div class="pt-2 border-t border-slate-200/60 text-xs text-slate-500 space-y-1.5 leading-relaxed">
          <p class="font-semibold text-slate-700">Consejos rápidos:</p>
          <ul class="list-disc pl-4 space-y-1 text-[11px]">
            <li>Haz clic en cualquier caja para configurar roles, formularios y SLA.</li>
            <li>Haz clic en una flecha para editar su etiqueta y reglas condicionales.</li>
            <li>Presiona <kbd class="px-1 py-0.5 bg-slate-200 text-slate-700 rounded text-[10px]">Supr</kbd> para eliminar el elemento seleccionado.</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- ========================================================================= -->
    <!-- CASO 2: NODO GATEWAY (COMPUERTA DE DECISIÓN)                              -->
    <!-- ========================================================================= -->
    <div v-else-if="selectedNode && isGatewayNode" class="flex-1 flex flex-col h-full overflow-hidden select-none bg-white">
      <!-- Header Gateway -->
      <div class="p-3 border-b border-amber-200/80 bg-gradient-to-r from-amber-50 to-orange-50/50 flex items-center justify-between shrink-0">
        <div class="flex items-center gap-2 truncate">
          <div class="w-7 h-7 rounded-lg bg-amber-100 border border-amber-300 flex items-center justify-center text-amber-700 shrink-0 shadow-xs">
            <GitFork class="w-4 h-4" />
          </div>
          <div class="truncate">
            <h3 class="text-xs font-bold text-slate-900 truncate">
              {{ nodeData.label || 'Compuerta de Decisión' }}
            </h3>
            <div class="flex items-center gap-1.5 mt-0.5">
              <span class="text-[9px] bg-amber-200/80 text-amber-900 font-bold px-1.5 py-0.2 rounded border border-amber-300">
                Compuerta Lógica
              </span>
              <span class="text-[10px] text-slate-500 font-mono">{{ selectedNode.id }}</span>
            </div>
          </div>
        </div>
        <button
          type="button"
          @click="emit('delete-selected')"
          class="p-1 text-red-500 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
          title="Eliminar compuerta"
        >
          <Trash2 class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- Contenido Gateway -->
      <div class="p-3.5 space-y-4 text-xs overflow-y-auto flex-1 custom-scrollbar">
        <!-- Nombre de la Decisión -->
        <div>
          <label class="block text-[11px] font-semibold text-slate-700 mb-1">
            Nombre de la Decisión
          </label>
          <input
            type="text"
            :value="nodeData.label || ''"
            @input="updateField('label', ($event.target as HTMLInputElement).value)"
            class="w-full px-2.5 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 text-xs font-medium bg-white"
            placeholder="Ej: ¿Requiere Presupuesto? o ¿Tipo de Solución?"
          />
        </div>

        <!-- Selector Dinámico de Variable Basado en Formularios Entrantes -->
        <div class="p-3 bg-amber-50/80 border border-amber-200/90 rounded-xl space-y-2.5 shadow-xs">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-1.5 text-amber-950 font-bold text-xs">
              <GitFork class="w-3.5 h-3.5 text-amber-600" />
              <span>Variable de Evaluación</span>
            </div>
            <span v-if="directIncomingNodes.length > 0" class="text-[9px] font-bold text-amber-800 bg-amber-200/80 px-1.5 py-0.5 rounded border border-amber-300">
              {{ directIncomingNodes.length }} nodo{{ directIncomingNodes.length > 1 ? 's' : '' }} input
            </span>
          </div>

          <p class="text-[10px] text-amber-900/80 leading-tight">
            Selecciona el campo de los formularios que entran como input a esta caja para bifurcar el flujo:
          </p>

          <!-- Badges de Nodos y Formularios de Entrada Directa -->
          <div v-if="directIncomingFormItems.length > 0" class="space-y-1">
            <div
              v-for="item in directIncomingFormItems"
              :key="item.nodeId"
              class="px-2 py-1 bg-white border border-amber-200/90 rounded-lg text-[10px] text-slate-700 shadow-2xs"
            >
              <div class="flex items-center gap-1.5">
                <ArrowRight class="w-3 h-3 text-amber-600 shrink-0" />
                <span class="font-bold text-slate-800 truncate">{{ item.nodeLabel }}</span>
              </div>
              <div v-if="item.form" class="mt-0.5 pl-4 text-[9px] text-amber-700 flex items-center justify-between">
                <span class="truncate">📄 {{ item.form.name }}</span>
                <span class="font-medium bg-amber-100 text-amber-800 px-1 rounded shrink-0">
                  {{ item.form.fields?.length || 0 }} campos
                </span>
              </div>
              <div v-else class="mt-0.5 pl-4 text-[9px] text-slate-400 italic">
                (Sin formulario asignado en este nodo)
              </div>
            </div>
          </div>
          <div v-else class="px-2 py-1.5 bg-amber-100/60 border border-amber-300 rounded-lg text-[10px] text-amber-900 flex items-center gap-1.5">
            <AlertCircle class="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span>Sin flechas entrantes a esta compuerta. Conecta un nodo previo para captar sus campos.</span>
          </div>

          <!-- Select con grupos dinámicos (Entrada Directa, Ruta Previa, etc.) -->
          <div>
            <label class="block text-[10px] font-semibold text-amber-950 mb-1">
              Campo del formulario a evaluar:
            </label>
            <select
              :value="gatewayConfig.variable || ''"
              @change="updateGatewayConfig({ variable: ($event.target as HTMLSelectElement).value })"
              class="w-full px-2.5 py-1.5 bg-white border border-amber-300 rounded-lg text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-500 shadow-2xs"
            >
              <option value="">-- Seleccionar Variable de Decisión --</option>
              
              <!-- Variable actual preservada si no está en ningún grupo -->
              <option
                v-if="gatewayConfig.variable && !isVariableInGroups(gatewayConfig.variable)"
                :value="gatewayConfig.variable"
              >
                ⭐ {{ gatewayConfig.variable }} (Selección actual)
              </option>

              <!-- Optgroups dinámicos -->
              <optgroup
                v-for="grp in gatewayVariableGroups"
                :key="grp.id"
                :label="grp.label"
              >
                <option
                  v-for="opt in grp.options"
                  :key="opt.key"
                  :value="opt.key"
                >
                  {{ opt.label }}
                </option>
              </optgroup>
            </select>
          </div>

          <!-- Variable Activa Feedback -->
          <div v-if="gatewayConfig.variable" class="flex items-center justify-between pt-1 border-t border-amber-200/70 text-[10px]">
            <span class="text-slate-500">Variable activa:</span>
            <div class="flex items-center gap-1 font-mono font-bold text-amber-900 bg-amber-100/80 border border-amber-200 px-1.5 py-0.5 rounded">
              <span>{{ gatewayConfig.variable }}</span>
              <span v-if="selectedVarInfo?.type" class="text-[8px] uppercase px-1 py-0.2 rounded bg-amber-200 text-amber-800">
                {{ selectedVarInfo.type }}
              </span>
            </div>
          </div>
        </div>

        <!-- Ramas de Salida y Reglas -->
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <h4 class="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
              Ramas y Condiciones ({{ outgoingEdges.length }})
            </h4>
          </div>

          <div v-if="outgoingEdges.length === 0" class="p-3 text-center bg-slate-50 border border-dashed border-slate-200 rounded-xl text-slate-400 text-xs">
            Conecta flechas que salgan de esta compuerta hacia los siguientes estados.
          </div>

          <div v-else class="space-y-2.5">
            <div
              v-for="edge in outgoingEdges"
              :key="edge.id"
              class="p-2.5 bg-slate-50 border border-slate-200/90 rounded-xl space-y-2 text-xs"
            >
              <div class="flex items-center justify-between font-bold text-slate-800">
                <div class="flex items-center gap-1.5 truncate">
                  <ArrowRight class="w-3.5 h-3.5 text-[#4F5AF5] shrink-0" />
                  <span class="truncate">{{ (nodes.find((n: any) => n.id === edge.target)?.data?.label) || edge.target }}</span>
                </div>
              </div>

              <!-- Etiqueta de la flecha -->
              <div>
                <span class="text-[10px] text-slate-500 font-semibold block mb-0.5">Etiqueta de la flecha:</span>
                <input
                  type="text"
                  :value="edge.label || ''"
                  @input="emit('update-edge', { label: ($event.target as HTMLInputElement).value, data: { ...edge.data } })"
                  placeholder="Ej: Sí, No, Avanzar..."
                  class="w-full px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-xs font-medium focus:ring-1 focus:ring-indigo-400"
                />
              </div>

              <!-- Regla Condicional -->
              <div class="grid grid-cols-2 gap-2 pt-0.5">
                <div>
                  <span class="text-[10px] text-slate-500 font-semibold block mb-0.5">Operador:</span>
                  <select
                    :value="getRuleForEdge(edge)?.operator || 'equals'"
                    @change="updateBranchRule(edge.id, edge.target, { operator: ($event.target as HTMLSelectElement).value })"
                    class="w-full px-2 py-1 bg-white border border-slate-200 rounded-lg text-[11px] font-medium"
                  >
                    <option value="equals">Es igual a (=)</option>
                    <option value="not_equals">Diferente de (≠)</option>
                    <option value="contains">Contiene texto</option>
                    <option value="greater_than">Mayor que (&gt;)</option>
                    <option value="less_than">Menor que (&lt;)</option>
                  </select>
                </div>
                <div>
                  <span class="text-[10px] text-slate-500 font-semibold block mb-0.5">Valor esperado:</span>
                  <input
                    type="text"
                    :value="getRuleForEdge(edge)?.value ?? ''"
                    @input="updateBranchRule(edge.id, edge.target, { value: ($event.target as HTMLInputElement).value })"
                    placeholder="Ej: Sí, No, 50000"
                    class="w-full px-2 py-1 bg-white border border-slate-200 rounded-lg text-[11px] font-bold text-slate-800 focus:ring-1 focus:ring-amber-400"
                  />
                </div>
              </div>

              <!-- Sugerencias Rápidas y Toggle Default -->
              <div class="flex items-center justify-between pt-1 border-t border-slate-200/60 gap-2">
                <div class="flex items-center gap-1">
                  <span class="text-[9px] text-slate-400 font-semibold">Rápido:</span>
                  <button
                    type="button"
                    @click="updateBranchRule(edge.id, edge.target, { value: 'Sí' })"
                    class="px-1.5 py-0.2 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 rounded text-[9px] font-bold cursor-pointer"
                  >
                    Sí
                  </button>
                  <button
                    type="button"
                    @click="updateBranchRule(edge.id, edge.target, { value: 'No' })"
                    class="px-1.5 py-0.2 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded text-[9px] font-bold cursor-pointer"
                  >
                    No
                  </button>
                </div>

                <label class="flex items-center gap-1 text-[10px] text-slate-600 font-semibold cursor-pointer">
                  <input
                    type="checkbox"
                    :checked="Boolean(getRuleForEdge(edge)?.isDefault)"
                    @change="updateBranchRule(edge.id, edge.target, { isDefault: ($event.target as HTMLInputElement).checked })"
                    class="w-3 h-3 text-amber-600 rounded cursor-pointer"
                  />
                  <span>Rama por defecto</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- Flujo de Entrada -->
        <div v-if="incomingEdges.length > 0" class="p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-[11px] space-y-1">
          <span class="font-semibold text-slate-600 block">Flujo de Entrada:</span>
          <div class="space-y-1">
            <div
              v-for="e in incomingEdges"
              :key="e.id"
              class="flex items-center gap-1.5 text-slate-700 bg-white px-2 py-1 rounded border border-slate-200"
            >
              <ArrowRight class="w-3 h-3 text-[#4F5AF5] shrink-0" />
              <span class="truncate font-medium">
                {{ (nodes.find((n: any) => n.id === e.source)?.data?.label) || e.source }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ========================================================================= -->
    <!-- CASO 3: NODO ESTADO REGULAR (STATE / START / END / AI)                    -->
    <!-- ========================================================================= -->
    <div v-else-if="selectedNode" class="flex-1 flex flex-col h-full overflow-hidden select-none bg-white">
      <!-- Header de Selección de Nodo -->
      <div class="p-3 border-b border-slate-100 flex items-center justify-between shrink-0">
        <div class="flex items-center gap-1.5 truncate">
          <Settings2 class="w-4 h-4 text-[#4F5AF5]" />
          <h3 class="text-xs font-bold text-slate-800 truncate" :title="nodeData.label">
            {{ nodeData.label || 'Configurar Nodo' }}
          </h3>
        </div>
        <button
          type="button"
          @click="emit('delete-selected')"
          class="p-1 text-red-500 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
          title="Eliminar nodo"
        >
          <Trash2 class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- Tabs (Idénticos al Original) -->
      <div class="flex border-b border-slate-100 bg-slate-50/70 p-1 gap-1 text-[11px] shrink-0">
        <button
          type="button"
          @click="activeTab = 'props'"
          :class="[
            'flex-1 py-1 px-1.5 rounded-md font-medium transition-colors cursor-pointer',
            activeTab === 'props' ? 'bg-white text-[#4F5AF5] shadow-xs font-bold' : 'text-slate-500 hover:text-slate-800'
          ]"
        >
          General
        </button>

        <button
          type="button"
          @click="activeTab = 'roles'"
          :class="[
            'flex-1 py-1 px-1.5 rounded-md font-medium transition-colors flex items-center justify-center gap-1 cursor-pointer',
            activeTab === 'roles' ? 'bg-white text-[#4F5AF5] shadow-xs font-bold' : 'text-slate-500 hover:text-slate-800'
          ]"
        >
          <span>Roles</span>
          <span
            v-if="assignedRoles.length > 0"
            :class="[
              'px-1.5 py-0.2 rounded-full text-[9px] font-bold',
              activeTab === 'roles' ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-200 text-slate-600'
            ]"
          >
            {{ assignedRoles.length }}
          </span>
        </button>

        <button
          type="button"
          @click="activeTab = 'custody'"
          :class="[
            'flex-1 py-1 px-1.5 rounded-md font-medium transition-colors flex items-center justify-center gap-1 cursor-pointer',
            activeTab === 'custody' ? 'bg-white text-[#4F5AF5] shadow-xs font-bold' : 'text-slate-500 hover:text-slate-800'
          ]"
        >
          <span>Dictamen</span>
          <span
            v-if="nodeData.form_id || nodeData.consent_id || nodeData.document_template_id"
            class="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0"
          />
        </button>

        <button
          v-if="isAINode"
          type="button"
          @click="activeTab = 'ai'"
          :class="[
            'flex-1 py-1 px-1.5 rounded-md font-medium transition-colors cursor-pointer',
            activeTab === 'ai' ? 'bg-white text-violet-600 shadow-xs font-bold' : 'text-slate-500 hover:text-slate-800'
          ]"
        >
          IA
        </button>
      </div>

      <!-- Tab Contents -->
      <div class="p-3 space-y-4 overflow-y-auto flex-1 text-xs custom-scrollbar">
        <!-- ── TAB 1: GENERAL (PROPIEDADES) ── -->
        <div v-if="activeTab === 'props'" class="space-y-3">
          <!-- 1. Nombre del Nodo / Estado -->
          <div>
            <label class="block text-[11px] font-semibold text-slate-600 mb-1">
              Nombre del Nodo / Estado
            </label>
            <input
              type="text"
              :value="nodeData.label || ''"
              @input="updateField('label', ($event.target as HTMLInputElement).value)"
              class="w-full px-2.5 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4F5AF5] text-xs font-medium"
            />
          </div>

          <!-- 2. Perfil y Semántica del Estado (4 Cards Exactas) -->
          <div>
            <label class="block text-[11px] font-semibold text-slate-600 mb-1.5">
              Perfil y Semántica del Estado
            </label>
            <div class="grid grid-cols-2 gap-1.5">
              <!-- Estándar -->
              <button
                type="button"
                @click="updateField('stateSubtype', 'standard')"
                :class="[
                  'p-2 rounded-lg border text-left flex items-center gap-2 transition-all cursor-pointer',
                  (!nodeData.stateSubtype || nodeData.stateSubtype === 'standard')
                    ? 'bg-indigo-50 border-[#4F5AF5] text-[#4F5AF5] font-semibold shadow-xs'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                ]"
              >
                <Layers class="w-3.5 h-3.5 shrink-0" />
                <span class="text-[11px] truncate">Estándar</span>
              </button>

              <!-- Observada -->
              <button
                type="button"
                @click="updateField('stateSubtype', 'observada')"
                :class="[
                  'p-2 rounded-lg border text-left flex items-center gap-2 transition-all cursor-pointer',
                  nodeData.stateSubtype === 'observada'
                    ? 'bg-amber-50 border-amber-400 text-amber-800 font-semibold shadow-xs'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                ]"
              >
                <AlertTriangle class="w-3.5 h-3.5 shrink-0 text-amber-600" />
                <span class="text-[11px] truncate">Observada</span>
              </button>

              <!-- En demanda -->
              <button
                type="button"
                @click="updateField('stateSubtype', 'demanda')"
                :class="[
                  'p-2 rounded-lg border text-left flex items-center gap-2 transition-all cursor-pointer',
                  nodeData.stateSubtype === 'demanda'
                    ? 'bg-emerald-50 border-emerald-400 text-emerald-800 font-semibold shadow-xs'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                ]"
              >
                <CheckCircle2 class="w-3.5 h-3.5 shrink-0 text-emerald-600" />
                <span class="text-[11px] truncate">En demanda</span>
              </button>

              <!-- Desestimada -->
              <button
                type="button"
                @click="updateField('stateSubtype', 'desestimada')"
                :class="[
                  'p-2 rounded-lg border text-left flex items-center gap-2 transition-all cursor-pointer',
                  nodeData.stateSubtype === 'desestimada'
                    ? 'bg-red-50 border-red-400 text-red-800 font-semibold shadow-xs'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                ]"
              >
                <Archive class="w-3.5 h-3.5 shrink-0 text-red-600" />
                <span class="text-[11px] truncate">Desestimada</span>
              </button>
            </div>
            <p class="text-[10px] text-slate-400 mt-1">
              Define el ícono, coloración y reglas de transición de este estado.
            </p>

            <!-- Opciones específicas de estados observados o desestimados -->
            <div
              v-if="nodeData.stateSubtype === 'observada' || nodeData.stateSubtype === 'desestimada'"
              class="mt-2.5 p-3 bg-slate-50 border border-slate-200/80 rounded-xl space-y-3"
            >
              <label class="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="nodeData.requireObservationComment !== false"
                  @change="updateField('requireObservationComment', ($event.target as HTMLInputElement).checked)"
                  class="w-3.5 h-3.5 rounded text-[#4F5AF5] mt-0.5 cursor-pointer"
                />
                <div class="text-[10px]">
                  <span class="font-bold text-slate-700 block">
                    Requerir justificación / detalle obligatorio
                  </span>
                  <span class="text-slate-400">
                    Abre un modal para ingresar los motivos antes de transicionar a este estado.
                  </span>
                </div>
              </label>

              <!-- EXCLUSIVO PARA OBSERVADA: CATEGORÍAS Y ADJUNTOS -->
              <div v-if="nodeData.stateSubtype === 'observada'" class="space-y-3">
                <!-- 1. GESTIÓN DE CATEGORÍAS DE OBSERVACIÓN -->
                <div class="pt-2 border-t border-slate-200/60 space-y-2">
                  <div class="flex items-center justify-between">
                    <span class="text-[10px] font-bold text-slate-700 flex items-center gap-1.5">
                      <Tag class="w-3 h-3 text-amber-600" />
                      Categorías de Observación
                    </span>
                    <button
                      type="button"
                      @click="resetObservationCategories"
                      class="text-[9px] font-semibold text-slate-400 hover:text-amber-700 flex items-center gap-1 transition-colors cursor-pointer"
                      title="Restablecer categorías sugeridas"
                    >
                      <RotateCcw class="w-2.5 h-2.5" />
                      Restablecer
                    </button>
                  </div>

                  <!-- Badges de categorías -->
                  <div class="flex flex-wrap gap-1.5">
                    <span
                      v-for="(cat, catIdx) in (nodeData.observationCategories || DEFAULT_OBSERVATION_CATEGORIES)"
                      :key="catIdx"
                      class="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-[10px] font-medium shadow-2xs"
                    >
                      <span>{{ cat }}</span>
                      <button
                        v-if="(nodeData.observationCategories || DEFAULT_OBSERVATION_CATEGORIES).length > 1"
                        type="button"
                        @click="removeObservationCategory(cat)"
                        class="text-amber-500 hover:text-rose-600 transition-colors p-0.5 cursor-pointer"
                        :title="`Eliminar categoría ${cat}`"
                      >
                        <X class="w-2.5 h-2.5" />
                      </button>
                    </span>
                  </div>

                  <!-- Input para añadir nueva categoría -->
                  <div class="flex items-center gap-1.5 pt-1">
                    <input
                      type="text"
                      v-model="newObservationCategory"
                      @keydown.enter.prevent="addObservationCategory"
                      placeholder="Nueva categoría..."
                      class="flex-1 px-2 py-1 text-[11px] bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                    />
                    <button
                      type="button"
                      @click="addObservationCategory"
                      class="px-2.5 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-[10px] font-bold transition-all shrink-0 cursor-pointer"
                    >
                      Añadir
                    </button>
                  </div>
                </div>

                <!-- 2. ARCHIVOS ADJUNTOS EN SUBSANACIÓN -->
                <div class="pt-2 border-t border-slate-200/60 space-y-2.5">
                  <label class="flex items-start gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      :checked="nodeData.allowObservationFiles !== false"
                      @change="updateField('allowObservationFiles', ($event.target as HTMLInputElement).checked)"
                      class="w-3.5 h-3.5 rounded text-[#4F5AF5] mt-0.5 cursor-pointer"
                    />
                    <div class="text-[10px]">
                      <span class="font-bold text-slate-700 block">
                        Permitir adjuntar archivos de soporte en la subsanación
                      </span>
                      <span class="text-slate-400">
                        Habilita la subida de documentos probatorios de subsanación.
                      </span>
                    </div>
                  </label>

                  <!-- Detalle de tipos de archivo -->
                  <div
                    v-if="nodeData.allowObservationFiles !== false"
                    class="p-2.5 bg-white border border-slate-200 rounded-xl space-y-2.5"
                  >
                    <div class="flex items-center justify-between pb-1.5 border-b border-slate-100">
                      <span class="text-[10px] font-bold text-slate-700 flex items-center gap-1">
                        <Paperclip class="w-3 h-3 text-indigo-500" />
                        Formatos y Límites en MB
                      </span>
                      <div class="flex items-center gap-1.5">
                        <label class="text-[9px] font-medium text-slate-500 flex items-center gap-1 cursor-pointer">
                          <input
                            type="checkbox"
                            :checked="(nodeData.observationFileOptions?.allowMultiple !== false)"
                            @change="updateField('observationFileOptions', {
                              ...(nodeData.observationFileOptions || DEFAULT_OBSERVATION_FILE_OPTIONS),
                              allowMultiple: ($event.target as HTMLInputElement).checked
                            })"
                            class="w-3 h-3 rounded text-[#4F5AF5] cursor-pointer"
                          />
                          <span>Múltiples</span>
                        </label>
                        <div
                          v-if="nodeData.observationFileOptions?.allowMultiple !== false"
                          class="flex items-center gap-1 text-[9px] text-slate-400"
                        >
                          <span>(máx</span>
                          <input
                            type="number"
                            min="1"
                            max="10"
                            :value="nodeData.observationFileOptions?.maxFiles || 5"
                            @input="updateField('observationFileOptions', {
                              ...(nodeData.observationFileOptions || DEFAULT_OBSERVATION_FILE_OPTIONS),
                              maxFiles: Math.min(10, Math.max(1, parseInt(($event.target as HTMLInputElement).value) || 1))
                            })"
                            class="w-7 px-0.5 py-0.5 text-center text-[10px] bg-slate-50 border border-slate-200 rounded font-bold"
                          />
                          <span>)</span>
                        </div>
                      </div>
                    </div>

                    <div class="space-y-1.5">
                      <div
                        v-for="def in FILE_TYPE_DEFS"
                        :key="def.key"
                        :class="[
                          'flex items-center justify-between p-1.5 rounded-lg border text-[10px] transition-all',
                          (nodeData.observationFileOptions?.fileTypes?.[def.key]?.enabled !== false)
                            ? 'bg-slate-50/70 border-slate-200'
                            : 'bg-slate-100/50 border-slate-200/40 opacity-50'
                        ]"
                      >
                        <label class="flex items-center gap-1.5 cursor-pointer min-w-0">
                          <input
                            type="checkbox"
                            :checked="(nodeData.observationFileOptions?.fileTypes?.[def.key]?.enabled !== false)"
                            @change="updateField('observationFileOptions', {
                              ...(nodeData.observationFileOptions || DEFAULT_OBSERVATION_FILE_OPTIONS),
                              fileTypes: {
                                ...((nodeData.observationFileOptions || DEFAULT_OBSERVATION_FILE_OPTIONS).fileTypes || DEFAULT_OBSERVATION_FILE_OPTIONS.fileTypes),
                                [def.key]: {
                                  ...((nodeData.observationFileOptions?.fileTypes?.[def.key]) || { enabled: true, maxMb: 25 }),
                                  enabled: ($event.target as HTMLInputElement).checked
                                }
                              }
                            })"
                            class="w-3 h-3 rounded text-[#4F5AF5] cursor-pointer"
                          />
                          <span class="font-bold text-slate-700">{{ def.label }}</span>
                          <span class="text-[9px] text-slate-400 font-mono">({{ def.ext }})</span>
                        </label>

                        <div class="flex items-center gap-1 shrink-0">
                          <span class="text-[9px] text-slate-400">Máx:</span>
                          <input
                            type="number"
                            min="1"
                            max="25"
                            :value="nodeData.observationFileOptions?.fileTypes?.[def.key]?.maxMb || 25"
                            :disabled="nodeData.observationFileOptions?.fileTypes?.[def.key]?.enabled === false"
                            @input="updateField('observationFileOptions', {
                              ...(nodeData.observationFileOptions || DEFAULT_OBSERVATION_FILE_OPTIONS),
                              fileTypes: {
                                ...((nodeData.observationFileOptions || DEFAULT_OBSERVATION_FILE_OPTIONS).fileTypes || DEFAULT_OBSERVATION_FILE_OPTIONS.fileTypes),
                                [def.key]: {
                                  ...((nodeData.observationFileOptions?.fileTypes?.[def.key]) || { enabled: true, maxMb: 25 }),
                                  maxMb: Math.min(25, Math.max(1, parseInt(($event.target as HTMLInputElement).value) || 1))
                                }
                              }
                            })"
                            class="w-9 px-1 py-0.5 text-center text-[10px] bg-white border border-slate-200 rounded font-bold disabled:opacity-50"
                          />
                          <span class="text-[9px] text-slate-500 font-semibold">MB</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 2.B UBICACIÓN EN STEPPER (INFORMATIVO DE SOLO LECTURA) -->
          <div class="p-3 bg-slate-50 border border-slate-200/90 rounded-xl space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                <Layers class="w-3.5 h-3.5 text-[#4F5AF5]" />
                Ubicación en Stepper (Riel de Avance)
              </span>
              <button
                type="button"
                @click="emit('open-macro-stages-modal')"
                class="text-[10px] text-indigo-600 hover:text-indigo-800 font-bold inline-flex items-center gap-1 cursor-pointer transition-colors"
                title="Configurar etapas y sub-estados en el gestor central"
              >
                <Settings2 class="w-3 h-3 text-indigo-600" />
                <span>Gestionar</span>
              </button>
            </div>

            <!-- Caso 1: Es Cabecera Principal de una Macro-Etapa -->
            <div
              v-if="isSelfMacroStage"
              class="flex items-center justify-between p-2.5 rounded-lg bg-indigo-50/90 border border-indigo-200/90 text-indigo-950 text-xs shadow-2xs gap-2"
            >
              <div class="flex items-center gap-2.5 min-w-0 flex-1">
                <span class="w-5 h-5 rounded-md bg-[#0D253F] text-white font-extrabold text-[10px] flex items-center justify-center shrink-0">
                  {{ isSelfMacroStage.index }}
                </span>
                <div class="min-w-0 flex-1">
                  <span class="font-bold block text-xs text-indigo-950 break-words leading-snug">
                    Etapa {{ isSelfMacroStage.index }}: {{ isSelfMacroStage.stage.name }}
                  </span>
                  <span class="text-[10px] text-indigo-700 font-medium">Cabecera Principal del Stepper</span>
                </div>
              </div>
              <span class="text-[9px] px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800 font-bold border border-indigo-200 shrink-0">
                Principal
              </span>
            </div>

            <!-- Caso 2: Es Sub-estado subordinado a una Macro-Etapa -->
            <div
              v-else-if="parentStageInfo"
              class="flex items-center justify-between p-2.5 rounded-lg bg-emerald-50/80 border border-emerald-200/80 text-emerald-950 text-xs shadow-2xs gap-2"
            >
              <div class="flex items-center gap-2.5 min-w-0 flex-1">
                <GitCommit class="w-4 h-4 text-emerald-600 shrink-0" />
                <div class="min-w-0 flex-1">
                  <span class="font-bold block text-xs text-emerald-950 break-words leading-snug">
                    Sub-estado de: {{ parentStageInfo.name }}
                  </span>
                  <span class="text-[10px] text-emerald-700 font-medium">Etapa #{{ parentStageInfo.index }} en el Stepper</span>
                </div>
              </div>
              <span class="text-[9px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold border border-emerald-200 shrink-0">
                Sub-estado
              </span>
            </div>

            <!-- Caso 3: Es Estado Independiente / No Agrupado -->
            <div
              v-else
              class="flex items-center justify-between p-2.5 rounded-lg bg-amber-50/70 border border-amber-200/80 text-amber-950 text-xs shadow-2xs gap-2"
            >
              <div class="flex items-center gap-2.5 min-w-0 flex-1">
                <AlertCircle class="w-4 h-4 text-amber-600 shrink-0" />
                <div class="min-w-0 flex-1">
                  <span class="font-bold block text-xs text-amber-950 break-words leading-snug">
                    Estado Independiente
                  </span>
                  <span class="text-[10px] text-amber-700 font-medium">Transversal (no secuencial)</span>
                </div>
              </div>
              <button
                type="button"
                @click="emit('open-macro-stages-modal')"
                class="text-[9px] px-2 py-0.5 rounded-full bg-amber-200/80 hover:bg-amber-300 text-amber-900 font-bold border border-amber-300 shrink-0 cursor-pointer transition-colors"
              >
                + Asignar
              </button>
            </div>
          </div>

          <!-- 3. CONFIGURACIÓN DE APROBADORES SIGUIENTES (ESTADO DEL REQUERIMIENTO) -->
          <div class="p-3 bg-slate-50 border border-slate-200/90 rounded-xl space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                <Building2 class="w-3.5 h-3.5 text-[#4F5AF5]" />
                Aprobadores Siguientes (En Estado del Requerimiento)
              </span>
              <label class="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  :checked="Boolean(nodeData.showNextApprovers)"
                  @change="updateField('showNextApprovers', ($event.target as HTMLInputElement).checked)"
                  class="sr-only peer"
                />
                <div class="w-8 h-4 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-[#4F5AF5]" />
              </label>
            </div>
            <p class="text-[10px] text-slate-400 leading-tight">
              Muestra en la tarjeta "Estado del Requerimiento" de la iniciativa la relación de aprobadores pendientes (ej: lista de Vicepresidencias o roles) para avanzar.
            </p>

            <div v-if="nodeData.showNextApprovers" class="space-y-2.5 pt-2 border-t border-slate-200/70">
              <div>
                <label class="block text-[10px] font-semibold text-slate-600 mb-1">
                  Título en la Tarjeta
                </label>
                <input
                  type="text"
                  :value="nodeData.nextApproversTitle || ''"
                  placeholder="Aprobadores siguientes (VPs)"
                  @input="updateField('nextApproversTitle', ($event.target as HTMLInputElement).value)"
                  class="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium focus:ring-1 focus:ring-[#4F5AF5]"
                />
              </div>

              <div>
                <label class="block text-[10px] font-semibold text-slate-600 mb-1">
                  Relación / Origen de Aprobadores
                </label>
                <div class="flex items-center gap-2 px-2.5 py-1.5 bg-slate-100/90 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700">
                  <span class="w-2 h-2 rounded-full bg-[#4F5AF5]" />
                  <span>Roles / Evaluadores del estado</span>
                </div>
              </div>

              <div class="pt-1 border-t border-slate-200/60">
                <label class="flex items-center gap-2 text-[11px] font-medium text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    :checked="Boolean(nodeData.includeAdminInApprovers)"
                    @change="updateField('includeAdminInApprovers', ($event.target as HTMLInputElement).checked)"
                    class="w-3.5 h-3.5 text-[#4F5AF5] rounded cursor-pointer"
                  />
                  <span>Incluir Administrador en la lista de aprobadores</span>
                </label>
                <p class="text-[10px] text-slate-400 pl-5.5 leading-tight">
                  Si está desactivado, el rol Administrador no se listará como aprobador requerido.
                </p>
              </div>
            </div>
          </div>

          <!-- 4. CONFIGURACIÓN DEL BOTÓN 'MOVER ESTADO' (SALTO MANUAL) -->
          <div
            :class="[
              'p-3 border rounded-xl space-y-2.5 transition-colors',
              nodeData.allowManualStateMove ? 'bg-purple-50/50 border-purple-200 shadow-2xs' : 'bg-slate-50 border-slate-200/90'
            ]"
          >
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                <Shuffle :class="['w-3.5 h-3.5', nodeData.allowManualStateMove ? 'text-purple-600' : 'text-slate-400']" />
                Botón "Mover estado"
              </span>
              <label class="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  :checked="Boolean(nodeData.allowManualStateMove)"
                  @change="updateField('allowManualStateMove', ($event.target as HTMLInputElement).checked)"
                  class="sr-only peer"
                />
                <div class="w-8 h-4 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-purple-600" />
              </label>
            </div>
            <p class="text-[10px] text-slate-400 leading-tight">
              Permite habilitar el botón "Mover estado" en la iniciativa desde esta etapa. Por defecto viene apagado en todos los estados.
            </p>

            <div v-if="nodeData.allowManualStateMove" class="space-y-2.5 pt-2 border-t border-purple-200/70">
              <div>
                <label class="block text-[10px] font-semibold text-slate-700 mb-1">
                  Rol autorizado <span class="text-red-500">*</span>
                </label>
                <select
                  :value="nodeData.manualStateMoveRole || ''"
                  @change="updateField('manualStateMoveRole', ($event.target as HTMLSelectElement).value); updateField('manualStateMoveUserId', '')"
                  class="w-full px-2.5 py-1.5 bg-white border border-purple-200 rounded-lg text-xs font-medium focus:ring-1 focus:ring-purple-500 focus:outline-none"
                >
                  <option value="">-- Seleccionar Rol --</option>
                  <option v-for="r in availableRoles" :key="r.code" :value="r.code">
                    {{ r.name }} ({{ r.code }})
                  </option>
                </select>
              </div>

              <div>
                <label class="block text-[10px] font-semibold text-slate-700 mb-1">
                  Usuario de ese rol autorizado <span class="text-red-500">*</span>
                </label>
                <select
                  :value="nodeData.manualStateMoveUserId || ''"
                  :disabled="!nodeData.manualStateMoveRole"
                  @change="updateField('manualStateMoveUserId', ($event.target as HTMLSelectElement).value)"
                  class="w-full px-2.5 py-1.5 bg-white border border-purple-200 rounded-lg text-xs font-medium focus:ring-1 focus:ring-purple-500 focus:outline-none disabled:bg-slate-100 disabled:text-slate-400"
                >
                  <option value="">
                    {{ !nodeData.manualStateMoveRole
                      ? 'Primero seleccione un rol'
                      : filteredUsersForManualMove.length === 0
                      ? 'No hay usuarios registrados con este rol'
                      : '-- Seleccionar Usuario Autorizado --'
                    }}
                  </option>
                  <option v-for="u in filteredUsersForManualMove" :key="u.id" :value="u.id">
                    {{ u.name }} — {{ u.email }}
                  </option>
                </select>
                <p v-if="nodeData.manualStateMoveRole && filteredUsersForManualMove.length === 0" class="text-[10px] text-amber-600 mt-1">
                  No se encontraron usuarios registrados con el rol "{{ nodeData.manualStateMoveRole }}".
                </p>
              </div>
            </div>
          </div>

          <!-- 5. DESCRIPCIÓN / INSTRUCCIONES -->
          <div>
            <label class="block text-[11px] font-semibold text-slate-600 mb-1">
              Descripción / Instrucciones
            </label>
            <textarea
              rows="3"
              :value="nodeData.description || ''"
              @input="updateField('description', ($event.target as HTMLTextAreaElement).value)"
              placeholder="Instrucciones para el usuario en esta etapa..."
              class="w-full px-2.5 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4F5AF5] text-xs resize-none"
            />
          </div>

          <!-- 7. FOOTER INFO BOX -->
          <div class="p-2.5 bg-slate-50 rounded-xl border border-slate-200 space-y-1 text-[11px]">
            <div class="flex justify-between text-slate-500">
              <span>Tipo:</span>
              <span class="font-semibold text-slate-700">{{ nodeData.nodeType || selectedNode.type || 'state' }}</span>
            </div>
            <div class="flex justify-between text-slate-500">
              <span>ID interno:</span>
              <span class="font-mono text-[10px] text-slate-600">{{ selectedNode.id }}</span>
            </div>
          </div>
        </div>

        <!-- ── TAB 2: ROLES PERMITIDOS (EXACTAMENTE COMO EL ORIGINAL) ── -->
        <div v-else-if="activeTab === 'roles'" class="space-y-2.5">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                Permisos por Rol
              </span>
              <span class="text-[10px] font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-200">
                {{ assignedRoles.length }} {{ assignedRoles.length === 1 ? 'asignado' : 'asignados' }}
              </span>
            </div>

            <!-- Buscador Rápido -->
            <div class="relative">
              <Search class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                v-model="roleSearch"
                placeholder="Buscar rol por nombre o slug..."
                class="w-full pl-8 pr-7 py-1.5 bg-slate-50 hover:bg-slate-100/70 border border-slate-200 rounded-lg text-xs outline-none focus:border-[#4F5AF5] focus:bg-white text-slate-800 placeholder:text-slate-400 transition-colors"
              />
              <button
                v-if="roleSearch"
                type="button"
                @click="roleSearch = ''"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5 cursor-pointer"
              >
                <X class="w-3 h-3" />
              </button>
            </div>

            <!-- Filtros Segmentados: Todos vs Asignados -->
            <div class="flex bg-slate-100 p-0.5 rounded-lg gap-0.5 text-[10px] font-bold">
              <button
                type="button"
                @click="roleFilter = 'all'"
                :class="[
                  'flex-1 py-1 rounded-md transition-all cursor-pointer flex items-center justify-center gap-1',
                  roleFilter === 'all' ? 'bg-white text-slate-800 shadow-2xs' : 'text-slate-500 hover:text-slate-700'
                ]"
              >
                <span>Todos</span>
                <span class="text-[9px] px-1 py-0.1 rounded-full bg-slate-200 text-slate-600">
                  {{ availableRoles.length }}
                </span>
              </button>
              <button
                type="button"
                @click="roleFilter = 'assigned'"
                :class="[
                  'flex-1 py-1 rounded-md transition-all cursor-pointer flex items-center justify-center gap-1',
                  roleFilter === 'assigned' ? 'bg-white text-[#4F5AF5] shadow-2xs' : 'text-slate-500 hover:text-slate-700'
                ]"
              >
                <span>Asignados</span>
                <span class="text-[9px] px-1 py-0.1 rounded-full bg-indigo-50 text-indigo-700">
                  {{ assignedRoles.length }}
                </span>
              </button>
            </div>
          </div>

          <!-- Lista de Roles -->
          <div class="space-y-2 pt-1">
            <template
              v-for="roleItem in availableRoles
                .filter((r) => {
                  const matchesSearch = !roleSearch || r.name.toLowerCase().includes(roleSearch.toLowerCase()) || r.code.toLowerCase().includes(roleSearch.toLowerCase());
                  const isAssigned = assignedRoles.some((assigned) => assigned.role_name === r.code);
                  if (roleFilter === 'assigned') return matchesSearch && isAssigned;
                  return matchesSearch;
                })
                .sort((a, b) => {
                  const aAssigned = assignedRoles.some((assigned) => assigned.role_name === a.code);
                  const bAssigned = assignedRoles.some((assigned) => assigned.role_name === b.code);
                  if (aAssigned && !bAssigned) return -1;
                  if (!aAssigned && bAssigned) return 1;
                  return 0;
                })"
              :key="roleItem.code"
            >
              <!-- 1. ROL ASIGNADO (TARJETA COMPLETA CON PILLS DE ACCIÓN) -->
              <div
                v-if="assignedRoles.some((r) => r.role_name === roleItem.code)"
                class="relative bg-white rounded-xl border border-indigo-200/90 shadow-2xs hover:shadow-xs transition-all overflow-hidden"
              >
                <!-- Borde temático izquierdo -->
                <div
                  class="absolute left-0 top-0 bottom-0 w-1"
                  :style="{ backgroundColor: ROLE_SWATCHES[roleItem.color || '']?.swatch || '#6366F1' }"
                />

                <div class="pl-3 pr-2.5 py-2.5">
                  <div class="flex items-center justify-between gap-2">
                    <div class="min-w-0 flex-1">
                      <div class="flex items-center gap-1.5 flex-wrap">
                        <span class="font-bold text-xs text-slate-900 leading-tight truncate max-w-[170px]" :title="roleItem.name">
                          {{ roleItem.name }}
                        </span>
                        <span
                          v-if="roleItem.is_system"
                          class="inline-flex items-center gap-0.5 text-[9px] font-bold text-slate-500 bg-slate-100 px-1 py-0.2 rounded shrink-0"
                        >
                          <Lock class="w-2.5 h-2.5 text-slate-400" />
                          Base
                        </span>
                        <span
                          v-else
                          class="inline-flex items-center gap-0.5 text-[9px] font-bold text-violet-700 bg-violet-50 px-1 py-0.2 rounded shrink-0"
                        >
                          <Sparkles class="w-2.5 h-2.5 text-violet-500" />
                          Custom
                        </span>
                      </div>
                      <span class="font-mono text-[10px] text-slate-400 block truncate">
                        {{ roleItem.code }}
                      </span>
                    </div>

                    <!-- Switch interactivo ON -->
                    <button
                      type="button"
                      @click="handleRoleToggle(roleItem.code)"
                      class="relative inline-flex h-4 w-7 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none bg-[#4F5AF5]"
                      title="Clic para desasignar rol de este nodo"
                    >
                      <span class="translate-x-3 pointer-events-none inline-block h-3 w-3 transform rounded-full bg-white shadow-xs transition duration-200 ease-in-out" />
                    </button>
                  </div>

                  <!-- Permiso de Modificación de Datos (Solo Editar) -->
                  <div class="pt-2 mt-2 border-t border-slate-100 flex items-center justify-between">
                    <div class="flex items-center gap-1.5 text-[11px] text-slate-600 font-medium">
                      <Pencil class="w-3 h-3 text-slate-400" />
                      <span>Modificar datos previos</span>
                    </div>
                    <button
                      type="button"
                      @click="handleRolePermissionChange(roleItem.code, 'can_edit', !assignedRoles.find((r) => r.role_name === roleItem.code)?.can_edit)"
                      :class="[
                        'px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all flex items-center gap-1.5 border cursor-pointer',
                        assignedRoles.find((r) => r.role_name === roleItem.code)?.can_edit
                          ? 'bg-indigo-50 border-indigo-200 text-indigo-700 shadow-2xs'
                          : 'bg-slate-50 border-slate-200 text-slate-400 hover:text-slate-600 hover:bg-slate-100'
                      ]"
                      title="Habilitar para permitir que este rol modifique información registrada previamente en la iniciativa"
                    >
                      <Pencil :class="['w-2.5 h-2.5', assignedRoles.find((r) => r.role_name === roleItem.code)?.can_edit ? 'text-indigo-600' : 'text-slate-400']" />
                      <span>{{ assignedRoles.find((r) => r.role_name === roleItem.code)?.can_edit ? 'Editar: Activado' : 'Solo Lectura' }}</span>
                    </button>
                  </div>
                </div>
              </div>

              <!-- 2. ROL DISPONIBLE NO ASIGNADO (FILA COMPACTA CON BOTÓN RÁPIDO) -->
              <div
                v-else
                class="p-2 rounded-xl border border-slate-200/80 bg-slate-50/60 hover:bg-white hover:border-slate-300 transition-all flex items-center justify-between gap-2 group shadow-2xs"
              >
                <div class="min-w-0 flex-1 flex items-center gap-2">
                  <span
                    class="w-2 h-2 rounded-full shrink-0"
                    :style="{ backgroundColor: ROLE_SWATCHES[roleItem.color || '']?.swatch || '#94A3B8' }"
                  />
                  <div class="min-w-0 flex-1">
                    <div class="flex items-center gap-1.5">
                      <span class="font-semibold text-xs text-slate-700 truncate block">
                        {{ roleItem.name }}
                      </span>
                      <span v-if="roleItem.is_system" class="text-[9px] text-slate-400 font-bold shrink-0">· Base</span>
                      <span v-else class="text-[9px] text-violet-600 font-bold shrink-0">· Custom</span>
                    </div>
                    <span class="font-mono text-[9px] text-slate-400 block truncate">
                      {{ roleItem.code }}
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  @click="handleRoleToggle(roleItem.code)"
                  class="px-2 py-0.5 rounded-lg text-[10px] font-bold text-slate-600 hover:text-[#4F5AF5] bg-white hover:bg-indigo-50 border border-slate-200 hover:border-indigo-200 transition-all shrink-0 cursor-pointer shadow-2xs"
                >
                  + Habilitar
                </button>
              </div>
            </template>
          </div>
        </div>

        <!-- ── TAB 3: DICTAMEN (FORMULARIOS, CONSENTIMIENTOS, DOCUMENTOS) ── -->
        <div v-else-if="activeTab === 'custody'" class="space-y-4">
          <div class="p-2.5 bg-indigo-50/70 border border-indigo-100 rounded-xl text-[11px] text-indigo-900 flex items-start gap-2">
            <FileCheck2 class="w-4 h-4 text-[#4F5AF5] shrink-0 mt-0.5" />
            <p>
              Asocia un <strong>Formulario</strong> y una <strong>Declaración de Consentimiento</strong> obligatorios para este estado. El evaluador deberá completarlos antes de aprobar.
            </p>
          </div>

          <!-- Selector de Formulario de Etapa -->
          <div class="space-y-1.5">
            <label class="block text-[11px] font-bold text-slate-700 uppercase tracking-wider">
              Formulario de Etapa
            </label>
            <select
              :value="nodeData.form_id || ''"
              @change="updateField('form_id', ($event.target as HTMLSelectElement).value || undefined)"
              class="w-full px-2.5 py-1.5 border border-slate-300 rounded-xl text-xs bg-white focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]"
            >
              <option value="">Ninguno (Sin formulario adicional)</option>
              <option v-for="sf in stageForms" :key="sf.id || sf.code" :value="sf.id || sf.code">
                {{ sf.name }} ({{ (sf.fields || []).length }} campos)
              </option>
            </select>

            <!-- Preview Formulario -->
            <div
              v-if="nodeData.form_id && stageForms.find((f: any) => f.id === nodeData.form_id || f.code === nodeData.form_id)"
              class="p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-[11px] space-y-1"
            >
              <div class="flex justify-between font-semibold text-slate-800">
                <span>{{ stageForms.find((f: any) => f.id === nodeData.form_id || f.code === nodeData.form_id)?.name }}</span>
                <span class="font-mono text-[10px] text-slate-500">{{ stageForms.find((f: any) => f.id === nodeData.form_id || f.code === nodeData.form_id)?.code }}</span>
              </div>
              <p
                v-if="stageForms.find((f: any) => f.id === nodeData.form_id || f.code === nodeData.form_id)?.description"
                class="text-[10px] text-slate-500"
              >
                {{ stageForms.find((f: any) => f.id === nodeData.form_id || f.code === nodeData.form_id)?.description }}
              </p>
              <div class="pt-1 flex flex-wrap gap-1">
                <span
                  v-for="f in (stageForms.find((item: any) => item.id === nodeData.form_id || item.code === nodeData.form_id)?.fields || [])"
                  :key="f.id || f.key"
                  class="px-1.5 py-0.5 bg-white border border-slate-200 rounded text-[9px] text-slate-600"
                >
                  {{ f.label || f.key }} {{ f.required ? '*' : '' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Selector de Consentimiento -->
          <div class="space-y-1.5">
            <label class="block text-[11px] font-bold text-slate-700 uppercase tracking-wider">
              Consentimiento / Declaración
            </label>
            <select
              :value="nodeData.consent_id || ''"
              @change="updateField('consent_id', ($event.target as HTMLSelectElement).value || undefined)"
              class="w-full px-2.5 py-1.5 border border-slate-300 rounded-xl text-xs bg-white focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]"
            >
              <option value="">Ninguno (Sin consentimiento requerido)</option>
              <option v-for="sc in stageConsents" :key="sc.id || sc.code" :value="sc.id || sc.code">
                {{ sc.title }} (v{{ sc.version || '1.0' }})
              </option>
            </select>

            <!-- Preview Consentimiento -->
            <div
              v-if="nodeData.consent_id && stageConsents.find((c: any) => c.id === nodeData.consent_id || c.code === nodeData.consent_id)"
              class="p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-[11px] space-y-1"
            >
              <div class="flex justify-between font-semibold text-slate-800">
                <span>{{ stageConsents.find((c: any) => c.id === nodeData.consent_id || c.code === nodeData.consent_id)?.title }}</span>
                <span class="font-mono text-[10px] text-indigo-600 font-bold">v{{ stageConsents.find((c: any) => c.id === nodeData.consent_id || c.code === nodeData.consent_id)?.version || '1.0' }}</span>
              </div>
              <p class="text-[10px] text-slate-600 italic line-clamp-3">
                "{{ stageConsents.find((c: any) => c.id === nodeData.consent_id || c.code === nodeData.consent_id)?.statement }}"
              </p>
            </div>
          </div>

          <!-- Selector de Documento / Plantilla PDF -->
          <div class="space-y-1.5">
            <label class="block text-[11px] font-bold text-slate-700 uppercase tracking-wider">
              Documento / Plantilla PDF de Etapa
            </label>
            <select
              :value="nodeData.document_template_id || ''"
              @change="updateField('document_template_id', ($event.target as HTMLSelectElement).value || undefined)"
              class="w-full px-2.5 py-1.5 border border-slate-300 rounded-xl text-xs bg-white focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]"
            >
              <option value="">Ninguno (Sin documento asociado)</option>
              <option v-for="dt in documentTemplates" :key="dt.id || dt.code" :value="dt.id || dt.code">
                {{ dt.name }} ({{ dt.code }})
              </option>
            </select>

            <!-- Preview Document Template -->
            <div
              v-if="nodeData.document_template_id && documentTemplates.find((d: any) => d.id === nodeData.document_template_id || d.code === nodeData.document_template_id)"
              class="p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-[11px] space-y-1"
            >
              <div class="flex justify-between font-semibold text-slate-800">
                <span>{{ documentTemplates.find((d: any) => d.id === nodeData.document_template_id || d.code === nodeData.document_template_id)?.name }}</span>
                <span class="font-mono text-[10px] text-rose-600 font-bold">{{ documentTemplates.find((d: any) => d.id === nodeData.document_template_id || d.code === nodeData.document_template_id)?.code }}</span>
              </div>
              <p
                v-if="documentTemplates.find((d: any) => d.id === nodeData.document_template_id || d.code === nodeData.document_template_id)?.description"
                class="text-[10px] text-slate-600 line-clamp-2"
              >
                {{ documentTemplates.find((d: any) => d.id === nodeData.document_template_id || d.code === nodeData.document_template_id)?.description }}
              </p>
            </div>
          </div>

          <div class="pt-2 border-t border-slate-100">
            <a
              href="/admin/formularios-consentimientos"
              target="_blank"
              class="inline-flex items-center gap-1 text-[11px] font-semibold text-[#4F5AF5] hover:text-indigo-700 hover:underline cursor-pointer"
            >
              <span>Administrar catálogo de formularios, consentimientos & documentos</span>
              <ExternalLink class="w-3 h-3" />
            </a>
          </div>
        </div>

        <!-- ── TAB 4: IA ── -->
        <div v-else-if="activeTab === 'ai' && isAINode" class="space-y-3">
          <div class="p-2.5 bg-violet-50 border border-violet-200 rounded-xl text-[11px] text-violet-900 flex items-center gap-2">
            <Sparkles class="w-4 h-4 text-violet-600 shrink-0" />
            <span>Conectado al motor cognitivo de Vertex AI / Gemini de IACS</span>
          </div>

          <div>
            <label class="block text-[11px] font-semibold text-slate-600 mb-1">
              Prompt / Instrucción Base
            </label>
            <textarea
              rows="4"
              :value="nodeData.aiConfig?.promptTemplate || ''"
              @input="updateField('aiConfig', { ...(nodeData.aiConfig || {}), promptTemplate: ($event.target as HTMLTextAreaElement).value })"
              placeholder="Instrucciones específicas para el modelo de lenguaje en este paso..."
              class="w-full px-2.5 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-violet-500 text-xs resize-none font-mono text-[11px]"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- ========================================================================= -->
    <!-- CASO 4: TRANSICIÓN / ARISTA SELECCIONADA (EDGE)                           -->
    <!-- ========================================================================= -->
    <div v-else-if="selectedEdge" class="flex-1 flex flex-col h-full overflow-hidden select-none bg-white">
      <!-- Header de Transición -->
      <div class="p-3 border-b border-slate-100 flex items-center justify-between shrink-0 bg-white">
        <div class="flex items-center gap-1.5 min-w-0">
          <ArrowRight class="w-4 h-4 text-[#EB5F46] shrink-0" />
          <h3 class="text-xs font-bold text-slate-800 truncate">Configurar Transición</h3>
        </div>
        <button
          type="button"
          @click="emit('delete-selected')"
          class="p-1 text-red-500 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
          title="Eliminar transición"
        >
          <Trash2 class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- Cuerpo de Configuración de la Transición -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar text-xs">
        <!-- 1. Etiqueta de la Flecha (Nombre del Botón) -->
        <div>
          <label class="block text-[11px] font-bold text-slate-700 mb-1">
            Etiqueta de la Flecha (Nombre del Botón)
          </label>
          <input
            type="text"
            :value="selectedEdge.label"
            @input="updateEdgeField('label', ($event.target as HTMLInputElement).value)"
            placeholder="Ej: Re estimar iniciativa, Enviar a Aprobación..."
            class="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5] text-xs font-medium text-slate-800 bg-white shadow-2xs"
          />
          <p class="text-[10px] text-slate-400 mt-1 leading-tight">
            Este texto será exactamente el nombre del botón que verá el usuario en la iniciativa.
          </p>
        </div>

        <!-- 2. Roles Autorizados (Transition RBAC) -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <label class="block text-[11px] font-bold text-slate-700">
              Roles Autorizados (Transition RBAC)
            </label>
            <div class="flex items-center gap-1.5">
              <span
                :class="[
                  'text-[10px] font-bold px-2 py-0.5 rounded-full border transition-all',
                  (edgeData.allowed_roles || []).length > 0
                    ? 'text-indigo-700 bg-indigo-50 border-indigo-200 shadow-2xs'
                    : 'text-amber-700 bg-amber-50 border-amber-200'
                ]"
              >
                {{ (edgeData.allowed_roles || []).length }} seleccionados
              </span>
            </div>
          </div>

          <p class="text-[10px] text-slate-500 leading-tight">
            Solo los usuarios con al menos uno de los roles seleccionados verán el botón de acción para esta transición.
          </p>

          <!-- BANDEJA DE ROLES ACTIVOS (VISTA INMEDIATA SIN SCROLL NI ADIVINANZAS) -->
          <div
            v-if="(edgeData.allowed_roles || []).length > 0"
            class="p-2.5 bg-gradient-to-br from-indigo-50/90 to-slate-50 border border-indigo-100 rounded-xl space-y-1.5 shadow-2xs"
          >
            <div class="flex items-center justify-between text-[10px]">
              <span class="font-extrabold text-indigo-900 uppercase tracking-wider flex items-center gap-1">
                <CheckCircle2 class="w-3.5 h-3.5 text-indigo-600" />
                Roles activos ({{ (edgeData.allowed_roles || []).length }}):
              </span>
              <button
                type="button"
                @click="clearAllEdgeRoles"
                class="text-[10px] font-semibold text-rose-600 hover:text-rose-700 hover:underline cursor-pointer"
                title="Deseleccionar todos los roles"
              >
                Limpiar todos
              </button>
            </div>

            <!-- Chips de roles seleccionados con botón de quitar directo -->
            <div class="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto custom-scrollbar p-0.5">
              <span
                v-for="code in (edgeData.allowed_roles || [])"
                :key="code"
                class="inline-flex items-center gap-1.5 pl-2 pr-1 py-0.5 rounded-lg text-[11px] font-semibold bg-white border border-indigo-200 text-indigo-900 shadow-2xs group hover:border-rose-300 transition-colors"
              >
                <span>{{ getRoleDisplayName(code) }}</span>
                <button
                  type="button"
                  @click.stop="removeEdgeRole(code)"
                  class="w-3.5 h-3.5 rounded-full hover:bg-rose-100 hover:text-rose-600 text-slate-400 flex items-center justify-center transition-colors cursor-pointer"
                  :title="`Quitar rol ${getRoleDisplayName(code)}`"
                >
                  <X class="w-2.5 h-2.5 stroke-[2.5]" />
                </button>
              </span>
            </div>
          </div>

          <!-- AVISO CUANDO NO HAY ROLES SELECCIONADOS (0 ROLES) -->
          <div
            v-else
            class="flex items-center gap-2 p-2.5 bg-amber-50/80 border border-amber-200/80 rounded-xl text-[10px] text-amber-800"
          >
            <AlertCircle class="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span class="leading-tight font-medium">
              Ningún rol seleccionado. Este botón estará <strong>oculto para todos</strong> (solo visible para Administradores).
            </span>
          </div>

          <!-- BARRA DE HERRAMIENTAS: Búsqueda y Filtro Rápido (Todos vs Solo Activos) -->
          <div class="space-y-1.5 pt-0.5">
            <div class="flex items-center gap-1.5">
              <!-- Buscador -->
              <div class="relative flex-1">
                <Search class="w-3 h-3 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  v-model="edgeRoleSearch"
                  type="text"
                  placeholder="Buscar rol por nombre o código..."
                  class="w-full pl-7 pr-6 py-1 bg-white border border-slate-200 rounded-lg text-[11px] text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-400 focus:border-indigo-400 transition-all"
                />
                <button
                  v-if="edgeRoleSearch"
                  @click="edgeRoleSearch = ''"
                  type="button"
                  class="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  <X class="w-2.5 h-2.5" />
                </button>
              </div>

              <!-- Pestañas Filtro: Todos vs Solo Seleccionados -->
              <div class="flex items-center bg-slate-100 rounded-lg p-0.5 border border-slate-200 shrink-0">
                <button
                  type="button"
                  @click="edgeRoleFilterTab = 'all'"
                  :class="[
                    'px-2 py-0.5 text-[10px] font-bold rounded-md transition-all cursor-pointer',
                    edgeRoleFilterTab === 'all'
                      ? 'bg-white text-indigo-700 shadow-2xs font-extrabold'
                      : 'text-slate-600 hover:text-slate-900'
                  ]"
                >
                  Todos ({{ availableRoles.length }})
                </button>
                <button
                  type="button"
                  @click="edgeRoleFilterTab = 'selected'"
                  :class="[
                    'px-2 py-0.5 text-[10px] font-bold rounded-md transition-all cursor-pointer flex items-center gap-1',
                    edgeRoleFilterTab === 'selected'
                      ? 'bg-white text-indigo-700 shadow-2xs font-extrabold'
                      : 'text-slate-600 hover:text-slate-900'
                  ]"
                >
                  <span>Activos</span>
                  <span
                    v-if="(edgeData.allowed_roles || []).length > 0"
                    class="w-4 h-4 rounded-full bg-indigo-600 text-white text-[9px] flex items-center justify-center font-bold"
                  >
                    {{ (edgeData.allowed_roles || []).length }}
                  </span>
                </button>
              </div>
            </div>

            <!-- LISTA DE CHECKBOXES CON SCROLL Y RESALTADO -->
            <div class="space-y-1 max-h-40 overflow-y-auto border border-slate-200 rounded-xl p-1.5 bg-slate-50/60 custom-scrollbar">
              <label
                v-for="r in filteredAvailableRoles"
                :key="r.code"
                :class="[
                  'flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs cursor-pointer transition-all select-none',
                  (edgeData.allowed_roles || []).includes(r.code)
                    ? 'bg-indigo-50/90 text-indigo-950 font-semibold border border-indigo-200 shadow-2xs'
                    : 'hover:bg-slate-100 text-slate-700 border border-transparent'
                ]"
              >
                <input
                  type="checkbox"
                  :checked="(edgeData.allowed_roles || []).includes(r.code)"
                  @change="toggleEdgeRole(r.code)"
                  class="rounded border-slate-300 text-[#4F5AF5] focus:ring-[#4F5AF5] shrink-0"
                />
                <span class="truncate flex-1 font-medium">{{ r.name }}</span>
                <span
                  v-if="(edgeData.allowed_roles || []).includes(r.code)"
                  class="text-[9px] font-bold text-indigo-700 bg-indigo-100 px-1.5 py-0.5 rounded uppercase tracking-wider shrink-0"
                >
                  Activo
                </span>
                <span v-else class="text-[9px] text-slate-400 font-mono shrink-0">{{ r.code }}</span>
              </label>

              <!-- Mensaje vacío si la búsqueda o filtro no da resultados -->
              <div
                v-if="filteredAvailableRoles.length === 0"
                class="py-4 text-center text-slate-400 text-xs italic"
              >
                <span v-if="edgeRoleFilterTab === 'selected'">No hay roles activos seleccionados.</span>
                <span v-else>No se encontraron roles coincidentes con "{{ edgeRoleSearch }}".</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. Vista Previa en Requerimiento -->
        <div class="p-3 bg-gradient-to-r from-indigo-50/90 via-white to-slate-50 rounded-xl border border-indigo-100 shadow-2xs space-y-2">
          <span class="text-[10px] font-extrabold text-[#EB5F46] uppercase tracking-wider block">
            VISTA PREVIA EN REQUERIMIENTO
          </span>
          <div class="flex items-center gap-2">
            <div
              :style="{
                backgroundColor: edgeData.style_config?.button_bg || (edgeData.style_config?.button_color ? 'transparent' : '#EB5F46'),
                borderColor: edgeData.style_config?.button_color || '#EB5F46',
                color: edgeData.style_config?.label_color || '#FFFFFF',
              }"
              class="px-3.5 py-1.5 rounded-xl font-bold text-xs shadow-xs flex items-center gap-1.5 transition-all border"
            >
              <Send class="w-3.5 h-3.5 shrink-0" />
              <span>{{ selectedEdge.label || 'Avanzar' }}</span>
            </div>
            <span class="text-[10px] text-slate-400 italic">
              {{ (edgeData.allowed_roles || []).length > 0 ? `Visible para ${(edgeData.allowed_roles || []).length} roles` : 'Visible para todos' }}
            </span>
          </div>
        </div>

        <!-- 4. Paleta y Estilos del Botón -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <label class="block text-[11px] font-bold text-slate-700">
              Paleta y Estilos del Botón
            </label>
            <button
              type="button"
              @click="resetEdgeStyle"
              class="text-[10px] font-semibold text-slate-400 hover:text-slate-700 transition-colors cursor-pointer"
            >
              Restablecer
            </button>
          </div>

          <div class="grid grid-cols-3 gap-1.5">
            <button
              v-for="preset in COLOR_PRESETS"
              :key="preset.name"
              type="button"
              @click="applyColorPreset(preset)"
              :class="[
                'px-2 py-1.5 rounded-lg border text-[11px] font-semibold flex items-center gap-1.5 transition-all cursor-pointer truncate',
                isPresetActive(preset)
                  ? 'border-indigo-500 bg-indigo-50/60 shadow-xs'
                  : 'border-slate-200 bg-white hover:bg-slate-50'
              ]"
            >
              <span
                class="w-2.5 h-2.5 rounded-full shrink-0 border border-black/10"
                :style="{ backgroundColor: preset.border }"
              />
              <span class="truncate">{{ preset.name }}</span>
            </button>
          </div>

          <!-- Color Pickers Personalizados -->
          <div class="grid grid-cols-3 gap-2 pt-1 border-t border-slate-100">
            <div>
              <label class="block text-[10px] text-slate-500 font-semibold mb-1">Fondo</label>
              <div class="flex items-center gap-1.5">
                <input
                  type="color"
                  :value="edgeData.style_config?.button_bg || '#EB5F46'"
                  @input="updateCustomColor('button_bg', ($event.target as HTMLInputElement).value)"
                  class="w-6 h-6 rounded cursor-pointer border border-slate-200"
                />
                <span class="text-[9px] font-mono text-slate-400 truncate">{{ edgeData.style_config?.button_bg || 'auto' }}</span>
              </div>
            </div>

            <div>
              <label class="block text-[10px] text-slate-500 font-semibold mb-1">Borde</label>
              <div class="flex items-center gap-1.5">
                <input
                  type="color"
                  :value="edgeData.style_config?.button_color || '#EB5F46'"
                  @input="updateCustomColor('button_color', ($event.target as HTMLInputElement).value)"
                  class="w-6 h-6 rounded cursor-pointer border border-slate-200"
                />
                <span class="text-[9px] font-mono text-slate-400 truncate">{{ edgeData.style_config?.button_color || 'auto' }}</span>
              </div>
            </div>

            <div>
              <label class="block text-[10px] text-slate-500 font-semibold mb-1">Texto</label>
              <div class="flex items-center gap-1.5">
                <input
                  type="color"
                  :value="edgeData.style_config?.label_color || '#FFFFFF'"
                  @input="updateCustomColor('label_color', ($event.target as HTMLInputElement).value)"
                  class="w-6 h-6 rounded cursor-pointer border border-slate-200"
                />
                <span class="text-[9px] font-mono text-slate-400 truncate">{{ edgeData.style_config?.label_color || '#fff' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 5. Detalles de Origen y Destino -->
        <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1.5 text-[11px]">
          <div class="flex justify-between text-slate-500">
            <span>Origen:</span>
            <span class="font-semibold text-slate-700 truncate max-w-[150px]">
              {{ (nodes.find((n: any) => n.id === selectedEdge.source)?.data?.label) || selectedEdge.source }}
            </span>
          </div>
          <div class="flex justify-between text-slate-500">
            <span>Destino:</span>
            <span class="font-semibold text-slate-700 truncate max-w-[150px]">
              {{ (nodes.find((n: any) => n.id === selectedEdge.target)?.data?.label) || selectedEdge.target }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
