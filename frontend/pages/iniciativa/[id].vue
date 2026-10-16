<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue';
import {
  ArrowLeft, CheckCircle, AlertTriangle, Ban, FileText,
  MessageSquare, Sparkles, Building2, Briefcase, MapPin, User, ShieldCheck, UserCheck,
  Calendar, Check, X, FileCheck2, Clock, Send, ArrowRight,
  Shuffle, Pencil, Save, ChevronDown, Copy
} from 'lucide-vue-next';
import type { Initiative, InitiativeStageRecord, StageConsent, WorkflowTransitionResult } from '~/types';
import InstitutionalLoader from '~/components/common/InstitutionalLoader.vue';
import InitiativeInfoTab from '~/components/initiative/InitiativeInfoTab.vue';
import InitiativeTraceabilityTab from '~/components/initiative/InitiativeTraceabilityTab.vue';
import InitiativeObservationsTab from '~/components/initiative/InitiativeObservationsTab.vue';
import InitiativeObserveModal from '~/components/initiative/InitiativeObserveModal.vue';
import InitiativeReubicarModal from '~/components/initiative/InitiativeReubicarModal.vue';
import InitiativeDesestimarModal from '~/components/initiative/InitiativeDesestimarModal.vue';
import { formatDateDDMMYYYY } from '~/utils/initiativeHistory';

const route = useRoute();
const id = route.params.id as string;
const config = useRuntimeConfig();
const apiBase = config.public.apiBase;

// ─── Tabs State (Idéntico al proyecto original) ──────────────────────────────
const activeDetailTab = ref<'info' | 'history' | 'observations'>('info');

// ─── Cargar Iniciativa ───────────────────────────────────────────────────────
const { data: initiative, pending, refresh, error } = await useFetch<Initiative>(`${apiBase}/initiatives/${id}`);

// ─── Cargar Cadena de Custodia ───────────────────────────────────────────────
const { data: stageRecords, refresh: refreshRecords } = await useFetch<InitiativeStageRecord[]>(
  `${apiBase}/initiatives/${id}/stage-records`,
  { default: () => [] }
);

// ─── Cargar Flujo de Trabajo Activo ──────────────────────────────────────────
const { data: activeWorkflowData } = await useFetch<any>(`${apiBase}/workflow/active`);
const activeWorkflow = computed(() => activeWorkflowData.value?.data);

// ─── Usuario y Roles Actuales ────────────────────────────────────────────────
const currentUser = ref({
  id: '',
  name: 'Administrador General',
  email: 'admin@iacs.empresa.com',
  roles: ['admin'] as string[],
});

onMounted(() => {
  if (process.client) {
    const saved = localStorage.getItem('iacs_user');
    if (saved) {
      try {
        const u = JSON.parse(saved);
        currentUser.value = {
          id: u.id || currentUser.value.id,
          name: u.name || currentUser.value.name,
          email: u.email || currentUser.value.email,
          roles: (u.roles && u.roles.length > 0) ? u.roles : (u.role ? [u.role] : ['admin']),
        };
      } catch (e) {}
    }
  }
});

const userRolesList = computed(() => currentUser.value.roles.map((r: string) => r.toLowerCase()));
const isAdmin = computed(() => userRolesList.value.includes('admin') || userRolesList.value.includes('administrador'));

// ─── Mapeo de Estados y Nodos ────────────────────────────────────────────────
const STATUS_TO_NODE: Record<string, string> = {
  'Borrador': 'borrador',
  'Pendiente de aprobación': 'eval_bp',
  'Observada': 'observada',
  'En demanda': 'planificacion',
  'Desestimada': 'desestimada',
};

const ROLE_ALIASES: Record<string, string[]> = {
  'registrador': ['registrador', 'key_user', 'key user'],
  'key_user': ['registrador', 'key_user', 'key user'],
  'bp_ti': ['bp_ti', 'business_partner', 'bp'],
  'business_owner': ['business_owner', 'bo'],
  'vicepresidente_del_negocio': ['vicepresidente', 'vicepresidente_del_negocio', 'vp'],
  'gestor_de_la_demanda': ['gestor_demanda', 'gestor_de_la_demanda'],
  'lider_de_dominio': ['lider_dominio', 'lider_de_dominio'],
  'admin': ['admin', 'administrador', 'administrador general'],
};

const currentNodeId = computed(() => {
  if (!initiative.value) return 'borrador';
  if (initiative.value.current_node_id) return initiative.value.current_node_id;

  const st = (initiative.value.status || '').toLowerCase().trim();
  const nodes = activeWorkflow.value?.graph_json?.nodes || [];

  const byId = nodes.find((n: any) => n.id.toLowerCase() === st);
  if (byId) return byId.id;

  const byLabel = nodes.find((n: any) => (n.data?.label || '').toLowerCase().trim() === st);
  if (byLabel) return byLabel.id;

  if (/borrador/i.test(st)) {
    const n = nodes.find((x: any) => x.id === 'borrador' || /borrador/i.test(x.data?.label || ''));
    if (n) return n.id;
  }
  if (/evalua|bp/i.test(st) || /pendiente/i.test(st)) {
    const n = nodes.find((x: any) => x.id === 'eval_bp' || /evaluación bp/i.test(x.data?.label || ''));
    if (n) return n.id;
  }
  if (/aprob.*bo|patrocinio/i.test(st)) {
    const n = nodes.find((x: any) => x.id === 'aprob_bo' || /aprobación bo/i.test(x.data?.label || ''));
    if (n) return n.id;
  }
  if (/aprob.*vp|vicepresid/i.test(st)) {
    const n = nodes.find((x: any) => x.id === 'aprob_vp' || /aprobación vp/i.test(x.data?.label || ''));
    if (n) return n.id;
  }
  if (/demanda|dominio/i.test(st)) {
    const n = nodes.find((x: any) => x.id === 'asig_demanda' || /demanda/i.test(x.data?.label || ''));
    if (n) return n.id;
  }
  if (/observa/i.test(st)) {
    const n = nodes.find((x: any) => x.id === 'observada' || /observa/i.test(x.data?.label || ''));
    if (n) return n.id;
  }
  if (/desestima/i.test(st)) {
    const n = nodes.find((x: any) => x.id === 'desestimada' || /desestima/i.test(x.data?.label || ''));
    if (n) return n.id;
  }
  if (/planifica/i.test(st)) {
    const n = nodes.find((x: any) => x.id === 'planificacion' || /planifica/i.test(x.data?.label || ''));
    if (n) return n.id;
  }

  return STATUS_TO_NODE[initiative.value.status] || 'borrador';
});

// Aristas salientes
const outgoingEdges = computed(() => {
  if (!activeWorkflow.value?.graph_json?.edges || !initiative.value) return [];
  const currId = currentNodeId.value;
  return activeWorkflow.value.graph_json.edges.filter((e: any) => e.source === currId);
});

const canUserExecuteEdge = (edge: any) => {
  if (isAdmin.value) return true;
  const edgeData = edge.data || {};
  const condCfg = edge.condition_config || {};
  const allowed: string[] = edgeData.allowed_roles || edge.allowed_roles || condCfg.allowed_roles;
  if (!Array.isArray(allowed) || allowed.length === 0) return true;

  const userRolesExpanded = new Set<string>();
  userRolesList.value.forEach((r: string) => {
    userRolesExpanded.add(r);
    (ROLE_ALIASES[r] || []).forEach(alias => userRolesExpanded.add(alias));
  });

  return allowed.some((allowedRole: string) => {
    const normalized = allowedRole.toLowerCase();
    if (userRolesExpanded.has(normalized)) return true;
    const aliases = ROLE_ALIASES[normalized] || [];
    return aliases.some(a => userRolesExpanded.has(a));
  });
};

const userOutgoingEdges = computed(() => {
  return outgoingEdges.value.filter((edge: any) => canUserExecuteEdge(edge));
});

const getEdgeButtonLabel = (edge: any) => {
  if (edge.label && edge.label.trim()) return edge.label.trim();
  const targetNode = activeWorkflow.value?.graph_json?.nodes?.find((n: any) => n.id === edge.target);
  return targetNode?.data?.action_label || targetNode?.data?.label || 'Avanzar';
};

const getEdgeButtonStyle = (edge: any) => {
  const style = edge.data?.style_config || {};
  const bg = style.button_bg || (style.button_color ? 'transparent' : '#EB5F46');
  const border = style.button_color || '#EB5F46';
  const text = style.label_color || (bg === 'transparent' || bg === '#FFFFFF' ? border : '#FFFFFF');
  return {
    backgroundColor: bg,
    borderColor: border,
    color: text,
  };
};

// Estados reactivos de modales
const showConsentModal = ref(false);
const selectedConsent = ref<StageConsent | null>(null);
const consentAccepted = ref(false);
const isSubmitting = ref(false);
const isSavingEdits = ref(false);
const pendingTransition = ref<{ targetId: string; actionLabel: string } | null>(null);

const showConfirmModal = ref(false);
const pendingEdgeTransition = ref<{ targetId: string; actionLabel: string; targetLabel: string } | null>(null);

const showSuccessModal = ref(false);
const successModalData = ref({
  title: '¡Iniciativa Actualizada con Éxito!',
  actionLabel: '',
  nextStatus: '',
  message: 'El cambio de estado ha sido procesado formalmente y sellado en la cadena de custodia institucional.',
});

// Modales de Observar, Reubicar y Desestimar
const showObserveModal = ref(false);
const showReubicarModal = ref(false);
const showDesestimarModal = ref(false);

// Lista de nodos para el modal de reubicación
const availableNodes = computed(() => {
  const nodes = activeWorkflow.value?.graph_json?.nodes || [];
  return nodes
    .filter((n: any) => n.type !== 'gateway' && !n.id.startsWith('gw_'))
    .map((n: any) => ({
      id: n.id,
      label: n.data?.label || n.id,
    }));
});

// Cálculo del contador de observaciones y movimientos (Idéntico al proyecto original)
const observationCount = computed(() => {
  const history: any[] = initiative.value?.form_data?._observation_history || [];
  let count = 0;
  history.forEach((h: any) => {
    const act = (h.action || '').toLowerCase();
    if (act.includes('observad') || act.includes('salto') || act.includes('mov') || act.includes('reubic') || act.includes('desestimad')) {
      count++;
    }
  });
  if (count === 0 && initiative.value?.form_data?._current_observation) {
    count = 1;
  }
  return count;
});

const isObservedState = computed(() => {
  const st = (initiative.value?.status || '').toLowerCase();
  return st.includes('observad');
});

const getStatusBadgeClass = (status: string) => {
  const s = (status || '').toLowerCase();
  if (s.includes('pendiente')) return 'bg-[#FFF0ED] text-[#EB5F46] border-[#FCD9D2]';
  if (s.includes('observad')) return 'bg-amber-50 text-amber-700 border-amber-200';
  if (s.includes('demanda') || s.includes('planificad')) return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  if (s.includes('desestimad')) return 'bg-rose-50 text-rose-700 border-rose-200';
  return 'bg-slate-100 text-slate-700 border-slate-200';
};

// ─── 7 Macro-Etapas Corporativas (Referencia Imagen 2) ─────────────────────
interface MacroStage {
  id: string;
  name: string;
  role: string;
  substepsCount?: number;
  substeps?: string[];
  nodeIds: string[];
  statusKeywords: string[];
}

const MACRO_STAGES: MacroStage[] = [
  {
    id: 'registro',
    name: 'Registro',
    role: 'Key User',
    nodeIds: ['borrador', 'start', 'ai_chat', 'node_borrador'],
    statusKeywords: ['borrador', 'draft', 'chat', '1. borrador'],
  },
  {
    id: 'viabilidad_bp',
    name: 'Viabilidad BP TI',
    role: 'Business Partner',
    nodeIds: ['eval_bp', 'node_eval_bp'],
    statusKeywords: ['pendiente', 'evalua', 'viabilidad', 'eval_bp', '2. evaluaci'],
  },
  {
    id: 'patrocinio_bo',
    name: 'Patrocinio BO',
    role: 'Business Owner',
    nodeIds: ['aprob_bo', 'node_aprob_bo'],
    statusKeywords: ['patrocinio', 'aprob.*bo', '3. aprobaci'],
  },
  {
    id: 'aprobacion_vp',
    name: 'Aprobación VP',
    role: 'Vicepresidencia',
    nodeIds: ['aprob_vp', 'node_aprob_vp'],
    statusKeywords: ['aprob.*vp', 'vicepresid', '4. aprobaci'],
  },
  {
    id: 'demanda_ti',
    name: 'Demanda TI',
    role: 'Gestor Demanda',
    nodeIds: ['asig_demanda', 'node_demanda', 'demanda'],
    statusKeywords: ['demanda', 'asignación de dominio', '5. asignaci'],
  },
  {
    id: 'estimacion',
    name: 'Estimación',
    role: 'Líder Dominio',
    substepsCount: 5,
    substeps: [
      'Compromiso de Ventana de Estimación',
      'Análisis técnico y dimensionamiento de esfuerzo',
      'Elaboración de estimación económica / presupuesto',
      'Validación técnica por Business Partner TI',
      'VoBo formal de estimación por Business Owner',
    ],
    nodeIds: ['ventana_est', 'gw_presupuesto', 'est_con_presupuesto', 'est_sin_presupuesto', 'val_est_bp', 'vobo_est_bo'],
    statusKeywords: ['estimaci', 'ventana', 'presupuesto', 'vobo_est'],
  },
  {
    id: 'planificacion',
    name: 'Planificación',
    role: 'Producción',
    substepsCount: 3,
    substeps: [
      'Planificación formal de fechas de inicio y fin',
      'Validación de calendario por BP TI y BO',
      'Pase oficial a Cartera TI institucional',
    ],
    nodeIds: ['plan_fechas', 'val_plan_bp', 'aprob_plan_bo', 'planificacion', 'end'],
    statusKeywords: ['planifica', 'cartera', 'finalizada', 'aprobada'],
  },
];

const isObserved = computed(() => {
  const st = (initiative.value?.status || '').toLowerCase();
  const nd = (currentNodeId.value || '').toLowerCase();
  return st.includes('observad') || nd.includes('observad');
});

const isDismissed = computed(() => {
  const st = (initiative.value?.status || '').toLowerCase();
  const nd = (currentNodeId.value || '').toLowerCase();
  return st.includes('desestimad') || nd.includes('desestimad');
});

const currentStageIndex = computed(() => {
  if (!initiative.value) return 0;
  const currNode = (currentNodeId.value || '').toLowerCase();
  const st = (initiative.value.status || '').toLowerCase();

  for (let i = 0; i < MACRO_STAGES.length; i++) {
    const s = MACRO_STAGES[i];
    if (s.nodeIds.some(nid => currNode === nid || currNode.includes(nid))) {
      return i;
    }
  }

  for (let i = 0; i < MACRO_STAGES.length; i++) {
    const s = MACRO_STAGES[i];
    if (s.statusKeywords.some(kw => new RegExp(kw, 'i').test(st))) {
      return i;
    }
  }

  if (isObserved.value) return 1;
  return 0;
});

const getStageState = (idx: number) => {
  if (isDismissed.value) {
    if (idx === currentStageIndex.value) return 'dismissed';
    if (idx < currentStageIndex.value) return 'completed';
    return 'pending';
  }
  if (isObserved.value && idx === currentStageIndex.value) {
    return 'observed';
  }
  if (idx < currentStageIndex.value) {
    return 'completed';
  }
  if (idx === currentStageIndex.value) {
    return 'active';
  }
  return 'pending';
};

const isConnectorCompleted = (idx: number) => {
  return idx < currentStageIndex.value;
};

// ─── Progreso continuo de la barra del stepper ─────────────────────────────
const stepperProgressPercent = computed(() => {
  if (MACRO_STAGES.length <= 1) return 0;
  const idx = Math.min(Math.max(currentStageIndex.value, 0), MACRO_STAGES.length - 1);
  return (idx / (MACRO_STAGES.length - 1)) * 100;
});

// ─── Copiar código de la iniciativa ─────────────────────────────────────────
const copiedId = ref(false);
const copyId = async () => {
  const codeToCopy = initiative.value?.summary?.id_corta || initiative.value?.id || '';
  if (!codeToCopy) return;
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(codeToCopy);
      copiedId.value = true;
      setTimeout(() => {
        copiedId.value = false;
      }, 2000);
    }
  } catch (e) {
    console.error('Error al copiar ID:', e);
  }
};

// ─── Etiqueta contextual de observación (según estado de la iniciativa) ─────
const observationButtonLabel = computed(() => {
  const st = (initiative.value?.status || '').toLowerCase();
  if (st.includes('planific')) return 'Observa iniciativa planificada';
  if (st.includes('estimac')) return 'Observar estimación';
  if (st.includes('demanda')) return 'Observar demanda';
  return 'Observar / Solicitar Ajustes';
});

const activePopoverStage = ref<string | null>(null);
const toggleSubsteps = (stageId: string) => {
  activePopoverStage.value = activePopoverStage.value === stageId ? null : stageId;
};

const institucionDisplay = computed(() => {
  if (!initiative.value?.form_data?.institucion) return 'UPN';
  const inst = initiative.value.form_data.institucion;
  return Array.isArray(inst) ? inst.join(', ') : String(inst);
});

// Botones de acción hacia adelante (excluyendo observaciones y desestimaciones que tienen modal propio)
const forwardEdges = computed(() => {
  return userOutgoingEdges.value.filter((edge: any) => {
    const targetId = (edge.target || '').toLowerCase();
    const label = (edge.label || '').toLowerCase();
    if (!isObservedState.value) {
      return !targetId.includes('observad') && !label.includes('observa') &&
             !targetId.includes('desestimad') && !label.includes('desestima');
    }
    return !targetId.includes('observad') && !targetId.includes('desestimad') && !label.includes('desestima');
  });
});

// Nodo actual en el workflow y configuraciones dinámicas de la caja (estado)
const currentNodeObj = computed(() => {
  return activeWorkflow.value?.graph_json?.nodes?.find((n: any) => n.id === currentNodeId.value) || null;
});

// Switch 1: Botón 'Mover estado' (Configurable en el diseñador de workflow por estado)
const canShowManualMove = computed(() => {
  if (!currentNodeObj.value) return false;
  const nodeData = currentNodeObj.value.data || {};
  if (!nodeData.allowManualStateMove) {
    return false;
  }
  if (isAdmin.value) return true;

  const allowedRole = nodeData.manualStateMoveRole;
  if (!allowedRole) return true;

  const userRolesExpanded = new Set<string>();
  userRolesList.value.forEach((r: string) => {
    userRolesExpanded.add(r);
    (ROLE_ALIASES[r] || []).forEach(alias => userRolesExpanded.add(alias));
  });

  const normalized = allowedRole.toLowerCase();
  if (userRolesExpanded.has(normalized)) return true;
  const aliases = ROLE_ALIASES[normalized] || [];
  return aliases.some(a => userRolesExpanded.has(a));
});

// Switch 2: Aprobadores Siguientes (En Estado del Requerimiento)
const showNextApproversCard = computed(() => {
  return Boolean(currentNodeObj.value?.data?.showNextApprovers);
});

const nextApproversData = computed(() => {
  if (!currentNodeObj.value?.data) return null;
  const d = currentNodeObj.value.data;
  return {
    title: d.nextApproversTitle || 'Aprobadores siguientes (VPs)',
    roles: Array.isArray(d.nextApproversRoles) ? d.nextApproversRoles : (Array.isArray(d.nextApproversList) ? d.nextApproversList : []),
    description: d.nextApproversDescription || 'Relación de roles pendientes para avanzar la iniciativa.',
  };
});

const canObserveCurrentState = computed(() => {
  if (!initiative.value) return false;
  const st = (initiative.value.status || '').toLowerCase();
  if (st.includes('borrador') || st.includes('draft') || st.includes('desestimad') || st.includes('observad')) {
    return false;
  }
  return true;
});

// Modal de Conversación con Teo
const showTeoChatModal = ref(false);
const openTeoChat = () => {
  showTeoChatModal.value = true;
};

// Permiso dinámico de Edición (RBAC gobernado por el nodo del Workflow)
const canEditCurrentState = computed(() => {
  if (!initiative.value) return false;

  const st = (initiative.value.status || '').toLowerCase();
  if (st.includes('desestimad') || st.includes('cancelad') || st.includes('finaliz')) {
    return false;
  }

  // 1. Obtener el nodo actual del workflow activo
  const currNode = activeWorkflow.value?.graph_json?.nodes?.find((n: any) => n.id === currentNodeId.value);
  const nodeRoles: Array<{ role_name: string; can_edit?: boolean }> = currNode?.data?.roles || [];

  // 2. Roles del usuario actual normalizados con alias
  const userRolesExpanded = new Set<string>();
  userRolesList.value.forEach((r: string) => {
    const rLower = r.toLowerCase().trim();
    userRolesExpanded.add(rLower);
    (ROLE_ALIASES[rLower] || []).forEach(alias => userRolesExpanded.add(alias.toLowerCase().trim()));
  });

  // 3. Si el nodo actual tiene roles configurados en el workflow:
  if (nodeRoles.length > 0) {
    // Buscar los roles asignados a este nodo que coincidan con los roles del usuario
    const matchingRoles = nodeRoles.filter((nr: any) => {
      const nrRole = (nr.role_name || '').toLowerCase().trim();
      return userRolesExpanded.has(nrRole) || (ROLE_ALIASES[nrRole] || []).some(a => userRolesExpanded.has(a.toLowerCase().trim()));
    });

    if (matchingRoles.length > 0) {
      // El rol del usuario está asignado al nodo: el switch 'can_edit' configurado gobierna estrictamente el permiso
      return matchingRoles.some((nr: any) => Boolean(nr.can_edit));
    }

    // Si el usuario es administrador general puro (no personificando otro rol como bp_ti)
    if (isAdmin.value && !userRolesList.value.some(r => r === 'bp_ti' || r === 'business_partner')) {
      return true;
    }

    // Ningún rol del usuario coincide con los roles asignados en este nodo
    return false;
  }

  // 4. Si el nodo no tiene roles definidos:
  if (st.includes('borrador')) {
    return userRolesExpanded.has('registrador') || userRolesExpanded.has('key_user') || isAdmin.value;
  }

  return false;
});

// Referencia a pestaña de información para activar modo edición
const infoTabRef = ref<any>(null);
const isEditingFicha = ref(false);

const triggerEdit = () => {
  if (!canEditCurrentState.value) return;
  activeDetailTab.value = 'info';
  isEditingFicha.value = true;
  nextTick(() => {
    if (infoTabRef.value?.startEditMode) {
      infoTabRef.value.startEditMode();
    }
  });
};

const cancelFichaEdit = () => {
  isEditingFicha.value = false;
  infoTabRef.value?.cancelEditMode();
};

const saveFichaEdit = () => {
  infoTabRef.value?.saveEdits();
  isEditingFicha.value = false;
};

// ─── Transición de Workflow Regular ──────────────────────────────────────────
const handleWorkflowTransition = async (edge: any) => {
  if (!initiative.value) return;

  let targetId = edge.target;
  let targetNodeObj = activeWorkflow.value?.graph_json?.nodes?.find((n: any) => n.id === targetId);
  const buttonLabel = getEdgeButtonLabel(edge);

  // Si la acción es Observar, abrir modal específico de observación
  if (targetId === 'observada' || buttonLabel.toLowerCase().includes('observar')) {
    showObserveModal.value = true;
    return;
  }

  // Si la acción es Desestimar, abrir modal específico de desestimación
  if (targetId === 'desestimada' || buttonLabel.toLowerCase().includes('desestimar')) {
    showDesestimarModal.value = true;
    return;
  }

  // Si la iniciativa está en estado Observada: ejecutar subsanación formal con datos de la ficha
  if (isObservedState.value) {
    const subsanacionData = infoTabRef.value?.getSubsanacionData?.() || { comment: '', files: [] };
    const hasComment = Boolean(subsanacionData.comment && subsanacionData.comment.trim());
    const hasFiles = Boolean(subsanacionData.files && subsanacionData.files.length > 0);

    if (!hasComment && !hasFiles) {
      alert('Por favor describe las correcciones realizadas o adjunta archivos de soporte en el panel de observación antes de avanzar.');
      activeDetailTab.value = 'info';
      return;
    }

    await handleSubsanacion(
      {
        comment: subsanacionData.comment,
        files: subsanacionData.files,
      },
      {
        nextStatus: targetNodeObj?.data?.label || targetId,
        nextNodeId: targetId,
        actionLabel: buttonLabel,
      }
    );
    return;
  }

  // Si el destino es una compuerta lógica (Gateway), bifurcar dinámicamente
  if (targetNodeObj?.type === 'gateway' || targetNodeObj?.data?.nodeType === 'gateway' || targetId.startsWith('gw_')) {
    const currentFd = { ...(initiative.value.form_data || {}) };
    const gwConfig = targetNodeObj?.data?.gatewayConfig || {};
    const variable = gwConfig?.variable || (targetId === 'gw_presupuesto' ? 'requiere_presupuesto' : '');
    const rawVal = String(currentFd[variable] ?? '').trim().toLowerCase();

    const gwEdges = activeWorkflow.value?.graph_json?.edges?.filter((e: any) => e.source === targetId) || [];
    const rules = gwConfig?.rules || [];

    let chosenEdge: any = null;
    for (const rule of rules) {
      if (rule.isDefault) continue;
      const ruleVal = String(rule.value || '').trim().toLowerCase();
      if (rawVal === ruleVal || ((rawVal === 'sí' || rawVal === 'si' || rawVal === 'true') && (ruleVal === 'sí' || ruleVal === 'si' || ruleVal === 'true'))) {
        chosenEdge = gwEdges.find((e: any) => e.id === rule.edgeId || e.target === rule.targetNodeId);
        if (chosenEdge) break;
      }
    }
    if (!chosenEdge && gwEdges.length > 0) {
      chosenEdge = gwEdges[0];
    }
    if (chosenEdge) {
      targetId = chosenEdge.target;
      targetNodeObj = activeWorkflow.value?.graph_json?.nodes?.find((n: any) => n.id === targetId) || targetNodeObj;
    }
  }

  // Validar transición en backend
  try {
    const res: WorkflowTransitionResult = await $fetch(`${apiBase}/workflow/validate-transition`, {
      params: {
        currentNodeId: currentNodeId.value,
        targetNodeId: targetId,
        userRole: userRolesList.value[0] || 'admin',
        transitionLabel: buttonLabel,
      },
    });

    if (!res.allowed) {
      alert(`Acción no permitida: ${res.reason || 'Revisa los requisitos'}`);
      return;
    }

    pendingEdgeTransition.value = {
      targetId,
      actionLabel: buttonLabel,
      targetLabel: targetNodeObj?.data?.label || targetId,
    };
    showConfirmModal.value = true;
  } catch (err: any) {
    alert('Error al validar transición: ' + (err.message || err));
  }
};

const cancelConfirmTransition = () => {
  showConfirmModal.value = false;
  pendingEdgeTransition.value = null;
};

const confirmStateTransition = async () => {
  showConfirmModal.value = false;
  if (!pendingEdgeTransition.value) return;

  const { targetId, actionLabel } = pendingEdgeTransition.value;
  pendingEdgeTransition.value = null;

  const targetNodeObj = activeWorkflow.value?.graph_json?.nodes?.find((n: any) => n.id === targetId);

  // Si requiere consentimiento / VoBo de firma, abrir modal de consentimiento
  if (targetNodeObj?.data?.consent_id || actionLabel.toLowerCase().includes('aprobar') || actionLabel.toLowerCase().includes('vobo')) {
    selectedConsent.value = {
      id: targetNodeObj?.data?.consent_id || 'DICTAMEN_TECNICO_BP',
      code: 'DICTAMEN_TECNICO_BP',
      title: 'Dictamen Técnico de Factibilidad y Arquitectura',
      statement: 'Declaro que he evaluado los requerimientos técnicos y certifico la viabilidad de la iniciativa.',
      version: 1,
      is_active: true,
    };
    pendingTransition.value = { targetId, actionLabel };
    showConsentModal.value = true;
    return;
  }

  await applyStateUpdate(targetId, actionLabel);
};

// Actualizar estado general persistiendo en backend y agregando a _observation_history
const applyStateUpdate = async (targetNodeId: string, actionLabel: string, extraUpdates: Record<string, any> = {}) => {
  if (!initiative.value) return;
  isSubmitting.value = true;
  try {
    const targetNodeObj = activeWorkflow.value?.graph_json?.nodes?.find((n: any) => n.id === targetNodeId);
    let nextStatus = 'Pendiente de aprobación';

    if (targetNodeId === 'planificacion' || targetNodeId === 'node_demanda' || targetNodeObj?.data?.stateSubtype === 'demanda') {
      nextStatus = 'En demanda';
    } else if (targetNodeId === 'observada' || targetNodeId === 'node_observada' || targetNodeObj?.data?.stateSubtype === 'observada') {
      nextStatus = 'Observada';
    } else if (targetNodeId === 'desestimada' || targetNodeId === 'node_desestimada' || targetNodeObj?.data?.stateSubtype === 'desestimada') {
      nextStatus = 'Desestimada';
    } else if (targetNodeId === 'borrador' || targetNodeId === 'node_borrador' || targetNodeObj?.data?.stateSubtype === 'borrador') {
      nextStatus = 'Borrador';
    } else if (targetNodeObj?.data?.label) {
      nextStatus = targetNodeObj.data.label;
    }

    const currentFd = { ...(initiative.value.form_data || {}) };
    const prevStatus = initiative.value.status || 'Borrador';

    // Generar entrada de historial
    const historyEntry = {
      date: new Date().toISOString(),
      user_name: currentUser.value.name,
      user_role: currentUser.value.roles[0] || 'admin',
      action: actionLabel,
      details: `Se cambió el estado de '${prevStatus}' a '${nextStatus}'`,
      from_stage: prevStatus,
      target_stage: nextStatus,
    };

    const newHistory = [...(currentFd._observation_history || []), historyEntry];
    const updatedFormData = {
      ...currentFd,
      ...extraUpdates,
      _observation_history: newHistory,
    };

    await $fetch(`${apiBase}/initiatives/${id}`, {
      method: 'PATCH',
      body: {
        status: nextStatus,
        current_node_id: targetNodeId,
        form_data: updatedFormData,
      },
    });

    await $fetch(`${apiBase}/initiatives/${id}/stage-record`, {
      method: 'POST',
      body: {
        node_id: targetNodeId,
        stage_name: nextStatus,
        consent_accepted: consentAccepted.value,
        consent_text_snapshot: selectedConsent.value?.statement || null,
        action_taken: actionLabel,
      },
    });

    showConsentModal.value = false;
    consentAccepted.value = false;
    pendingTransition.value = null;
    await refresh();
    await refreshRecords();

    successModalData.value = {
      title: '¡Iniciativa Actualizada con Éxito!',
      actionLabel: actionLabel,
      nextStatus: nextStatus,
      message: `El estado del requerimiento se ha actualizado formalmente a "${nextStatus}" mediante la acción "${actionLabel}".`,
    };
    showSuccessModal.value = true;
  } catch (err: any) {
    alert('Error al actualizar iniciativa: ' + (err.message || err));
  } finally {
    isSubmitting.value = false;
  }
};

// ─── Guardar Edición de Ficha Técnica ─────────────────────────────────────────
const handleSaveEdits = async (updatedFormData: Record<string, any>) => {
  if (!initiative.value) return;
  isSavingEdits.value = true;
  try {
    await $fetch(`${apiBase}/initiatives/${id}`, {
      method: 'PATCH',
      body: {
        form_data: updatedFormData,
      },
    });
    await refresh();
    alert('¡Ficha técnica guardada exitosamente!');
  } catch (err: any) {
    alert('Error al guardar la ficha: ' + (err.message || err));
  } finally {
    isSavingEdits.value = false;
  }
};

// ─── Formular Observación ─────────────────────────────────────────────────────
const handleObserveConfirm = async ({ category, details }: { category: string; details: string }) => {
  if (!initiative.value) return;
  isSubmitting.value = true;
  try {
    const currentFd = { ...(initiative.value.form_data || {}) };
    const prevStatus = initiative.value.status || 'Borrador';

    const obsId = `obs_${Date.now()}`;
    const newObs = {
      id: obsId,
      date: new Date().toISOString(),
      observed_by: currentUser.value.name,
      user_role: currentUser.value.roles[0] || 'BP TI',
      action: 'Observada',
      category: category,
      details: details,
      from_stage: prevStatus,
      from_node_id: currentNodeId.value,
      resolved: false,
    };

    const historyEntry = {
      date: new Date().toISOString(),
      user_name: currentUser.value.name,
      user_role: currentUser.value.roles[0] || 'BP TI',
      action: 'Observada',
      category: category,
      details: `[${category}] ${details}`,
      from_stage: prevStatus,
      from_node_id: currentNodeId.value,
    };

    const updatedFormData = {
      ...currentFd,
      _current_observation: newObs,
      _observation_history: [...(currentFd._observation_history || []), historyEntry],
    };

    await $fetch(`${apiBase}/initiatives/${id}`, {
      method: 'PATCH',
      body: {
        status: 'Observada',
        current_node_id: 'observada',
        form_data: updatedFormData,
      },
    });

    await $fetch(`${apiBase}/initiatives/${id}/stage-record`, {
      method: 'POST',
      body: {
        node_id: 'observada',
        stage_name: 'Observada',
        action_taken: 'Observar Iniciativa',
        user_role: currentUser.value.roles[0] || 'BP TI',
      },
    });

    showObserveModal.value = false;
    await refresh();
    await refreshRecords();

    successModalData.value = {
      title: '¡Observación Formulada con Éxito!',
      actionLabel: 'Observar Iniciativa',
      nextStatus: 'Observada',
      message: `Se ha registrado formalmente la observación en la categoría "${category}" y la iniciativa pasó a estado Observada.`,
    };
    showSuccessModal.value = true;
  } catch (err: any) {
    alert('Error al registrar observación: ' + (err.message || err));
  } finally {
    isSubmitting.value = false;
  }
};

// ─── Subsanar Observación ─────────────────────────────────────────────────────
const handleSubsanacion = async (
  { comment, files }: { comment: string; files: any[] },
  overrideTarget?: { nextStatus?: string; nextNodeId?: string; actionLabel?: string }
) => {
  if (!initiative.value) return;
  isSubmitting.value = true;
  try {
    const currentFd = { ...(initiative.value.form_data || {}) };
    const currentObs = currentFd._current_observation || {};

    const nextStatus = overrideTarget?.nextStatus || currentObs.from_stage || 'En evaluación del BP TI';
    const nextNodeId = overrideTarget?.nextNodeId || currentObs.from_node_id || 'eval_bp';
    const actionLabel = overrideTarget?.actionLabel || 'Subsanar Observación';

    const historyEntry = {
      date: new Date().toISOString(),
      user_name: currentUser.value.name,
      user_role: currentUser.value.roles[0] || 'Key user',
      action: 'Subsanada',
      details: comment ? `Subsanación: ${comment}` : 'Subsanación técnica con archivos de soporte adjuntos.',
      files: files || [],
      from_stage: 'Observada',
      target_stage: nextStatus,
    };

    const resolvedObs = {
      ...currentObs,
      resolved: true,
      resolved_at: new Date().toISOString(),
      resolved_by: currentUser.value.name,
      resolution_comment: comment,
      resolution_files: files || [],
    };

    const updatedFormData = {
      ...currentFd,
      _current_observation: resolvedObs,
      _observation_history: [...(currentFd._observation_history || []), historyEntry],
    };

    await $fetch(`${apiBase}/initiatives/${id}`, {
      method: 'PATCH',
      body: {
        status: nextStatus,
        current_node_id: nextNodeId,
        form_data: updatedFormData,
      },
    });

    await $fetch(`${apiBase}/initiatives/${id}/stage-record`, {
      method: 'POST',
      body: {
        node_id: nextNodeId,
        stage_name: nextStatus,
        action_taken: actionLabel,
        user_role: currentUser.value.roles[0] || 'Key user',
      },
    });

    if (infoTabRef.value?.clearSubsanacion) {
      infoTabRef.value.clearSubsanacion();
    }

    await refresh();
    await refreshRecords();

    successModalData.value = {
      title: '¡Subsanación Registrada con Éxito!',
      actionLabel: actionLabel,
      nextStatus: nextStatus,
      message: `La justificación y evidencias fueron selladas en la cadena de custodia y el requerimiento avanza formalmente a "${nextStatus}".`,
    };
    showSuccessModal.value = true;
  } catch (err: any) {
    alert('Error al subsanar observación: ' + (err.message || err));
  } finally {
    isSubmitting.value = false;
  }
};

// Disparador de subsanación desde la barra superior de acciones
const triggerHeaderSubsanacion = async () => {
  const subsanacionData = infoTabRef.value?.getSubsanacionData?.() || { comment: '', files: [] };
  const hasComment = Boolean(subsanacionData.comment && subsanacionData.comment.trim());
  const hasFiles = Boolean(subsanacionData.files && subsanacionData.files.length > 0);

  if (!hasComment && !hasFiles) {
    alert('Por favor describe las correcciones realizadas o adjunta archivos de soporte en el panel de observación antes de reenviar la iniciativa.');
    activeDetailTab.value = 'info';
    return;
  }

  await handleSubsanacion({
    comment: subsanacionData.comment,
    files: subsanacionData.files,
  });
};

// ─── Reubicación Manual / Salto Libre ─────────────────────────────────────────
const handleReubicarConfirm = async ({ targetNodeId, targetStatus, reason }: { targetNodeId: string; targetStatus: string; reason: string }) => {
  if (!initiative.value) return;
  isSubmitting.value = true;
  try {
    const currentFd = { ...(initiative.value.form_data || {}) };
    const prevStatus = initiative.value.status || 'Borrador';

    const historyEntry = {
      date: new Date().toISOString(),
      user_name: currentUser.value.name,
      user_role: currentUser.value.roles[0] || 'Administrador',
      action: 'Salto Libre',
      details: `[SALTO LIBRE] Se reubicó manualmente el requerimiento de '${prevStatus}' hacia '${targetStatus}'. Motivo: ${reason}`,
      from_stage: prevStatus,
      target_stage: targetStatus,
      reason: reason,
    };

    const updatedFormData = {
      ...currentFd,
      _observation_history: [...(currentFd._observation_history || []), historyEntry],
    };

    await $fetch(`${apiBase}/initiatives/${id}`, {
      method: 'PATCH',
      body: {
        status: targetStatus,
        current_node_id: targetNodeId,
        form_data: updatedFormData,
      },
    });

    await $fetch(`${apiBase}/initiatives/${id}/stage-record`, {
      method: 'POST',
      body: {
        node_id: targetNodeId,
        stage_name: targetStatus,
        action_taken: 'Reubicación Manual',
        user_role: currentUser.value.roles[0] || 'Administrador',
      },
    });

    showReubicarModal.value = false;
    await refresh();
    await refreshRecords();

    successModalData.value = {
      title: '¡Iniciativa Reubicada con Éxito!',
      actionLabel: 'Reubicación Manual',
      nextStatus: targetStatus,
      message: `El requerimiento ha sido reubicado en el estado "${targetStatus}" con auditoría completa de trazabilidad.`,
    };
    showSuccessModal.value = true;
  } catch (err: any) {
    alert('Error al reubicar iniciativa: ' + (err.message || err));
  } finally {
    isSubmitting.value = false;
  }
};

// ─── Desestimar Iniciativa ────────────────────────────────────────────────────
const handleDesestimarConfirm = async (reason: string) => {
  if (!initiative.value) return;
  isSubmitting.value = true;
  try {
    const currentFd = { ...(initiative.value.form_data || {}) };
    const prevStatus = initiative.value.status || 'Borrador';

    const historyEntry = {
      date: new Date().toISOString(),
      user_name: currentUser.value.name,
      user_role: currentUser.value.roles[0] || 'Administrador',
      action: 'Desestimada',
      details: reason,
      from_stage: prevStatus,
    };

    const updatedFormData = {
      ...currentFd,
      _current_observation: {
        id: `des_${Date.now()}`,
        date: new Date().toISOString(),
        observed_by: currentUser.value.name,
        user_role: currentUser.value.roles[0] || 'Administrador',
        action: 'Desestimada',
        details: reason,
        from_stage: prevStatus,
      },
      _observation_history: [...(currentFd._observation_history || []), historyEntry],
    };

    await $fetch(`${apiBase}/initiatives/${id}`, {
      method: 'PATCH',
      body: {
        status: 'Desestimada',
        current_node_id: 'desestimada',
        form_data: updatedFormData,
      },
    });

    await $fetch(`${apiBase}/initiatives/${id}/stage-record`, {
      method: 'POST',
      body: {
        node_id: 'desestimada',
        stage_name: 'Desestimada',
        action_taken: 'Desestimar',
        user_role: currentUser.value.roles[0] || 'Administrador',
      },
    });

    showDesestimarModal.value = false;
    await refresh();
    await refreshRecords();

    successModalData.value = {
      title: 'Iniciativa Desestimada',
      actionLabel: 'Desestimar',
      nextStatus: 'Desestimada',
      message: 'Se ha registrado formalmente el dictamen de no viabilidad en el expediente institucional.',
    };
    showSuccessModal.value = true;
  } catch (err: any) {
    alert('Error al desestimar iniciativa: ' + (err.message || err));
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6 pb-16">
    <div v-if="pending" class="py-20 bg-white rounded-2xl border border-slate-200 flex items-center justify-center">
      <InstitutionalLoader 
        title="Cargando Expediente de la Iniciativa" 
        subtitle="Recuperando cadena de custodia y dictámenes técnicos..."
        :phrases="[
          'Sincronizando estado con la cadena de custodia...',
          'Cargando trazabilidad y dictámenes técnicos...',
          'Validando directrices y políticas de TI...',
          'Verificando acuerdos y consentimientos digitales...'
        ]"
      />
    </div>

    <div v-else-if="!initiative" class="p-12 text-center text-rose-500">
      Iniciativa no encontrada.
    </div>

    <div v-else class="space-y-6">
      <!-- ── ENCABEZADO SUPERIOR DIRECTO EN CANVAS (RÉPLICA EXACTA DE IMAGEN 2) ── -->
      <div class="space-y-3.5 pt-2">
        <!-- Fila 1: Link Volver a la Bandeja -->
        <div>
          <NuxtLink
            to="/dashboard"
            class="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-slate-500 hover:text-slate-900 transition-colors cursor-pointer group"
          >
            <ArrowLeft class="w-4 h-4 text-slate-400 group-hover:text-slate-800 transition-colors" />
            <span>Volver a la Bandeja</span>
          </NuxtLink>
        </div>

        <!-- Fila 2: Código de la Iniciativa con Botón Copiar -->
        <div class="flex items-center gap-2">
          <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white border border-slate-200/90 shadow-2xs text-xs font-mono font-medium text-slate-700 select-all">
            <span>#{{ initiative.summary?.id_corta || initiative.id }}</span>
            <button
              type="button"
              @click="copyId"
              class="text-slate-400 hover:text-slate-700 p-0.5 rounded transition-colors cursor-pointer"
              :title="copiedId ? '¡Copiado!' : 'Copiar código'"
            >
              <Check v-if="copiedId" class="w-3.5 h-3.5 text-emerald-600" />
              <Copy v-else class="w-3.5 h-3.5" />
            </button>
          </div>
          <span v-if="copiedId" class="text-[11px] font-semibold text-emerald-600 animate-in fade-in duration-200">
            ¡Copiado!
          </span>
        </div>

        <!-- Fila 3: Título de Ancho Completo (Full Width) con Tipografía Ejecutiva -->
        <h1 class="text-xl sm:text-2xl lg:text-[26px] font-bold text-[#0D253F] tracking-tight leading-snug break-words">
          {{ initiative.summary?.titulo || initiative.form_data?.titulo || initiative.id }}
        </h1>

        <!-- Fila 4: Botones de Acción (Lógica y Orden Exacto de Imagen 2) -->
        <div class="flex flex-wrap items-center gap-2.5 sm:gap-3 pt-1">
          <!-- 1. Ver conversación con Teo -->
          <button
            type="button"
            @click="openTeoChat"
            class="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-[13px] font-semibold border border-[#FFD5CC] bg-[#FFF7F5] text-[#E75D43] hover:bg-[#FFEAE3] hover:border-[#FBBFAD] transition-all cursor-pointer shadow-2xs"
          >
            <MessageSquare class="w-4 h-4 text-[#E75D43]" />
            <span>Ver conversación con Teo</span>
          </button>

          <!-- 2. Observa iniciativa (Texto Dinámico: 'Observa iniciativa planificada' / 'Observar / Solicitar Ajustes') -->
          <button
            v-if="canObserveCurrentState"
            type="button"
            @click="showObserveModal = true"
            class="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-[13px] font-semibold border border-[#FDE68A] bg-[#FFFDF2] text-[#92400E] hover:bg-[#FEF9C3] hover:border-[#FCD34D] transition-all cursor-pointer shadow-2xs"
          >
            <AlertTriangle class="w-4 h-4 text-[#B45309]" />
            <span>{{ observationButtonLabel }}</span>
          </button>

          <!-- 3. Editar Ficha / Guardar Cambios (Sincronizado sin duplicidad y con RBAC) -->
          <template v-if="canEditCurrentState">
            <template v-if="isEditingFicha">
              <button
                type="button"
                @click="cancelFichaEdit"
                class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs sm:text-[13px] font-semibold border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-all cursor-pointer shadow-2xs"
              >
                <X class="w-4 h-4 text-slate-500" />
                <span>Cancelar</span>
              </button>
              <button
                type="button"
                @click="saveFichaEdit"
                :disabled="isSavingEdits"
                class="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs sm:text-[13px] font-bold text-white bg-[#4F5AF5] hover:bg-[#3F49E0] transition-all cursor-pointer shadow-2xs disabled:opacity-50"
              >
                <Save class="w-4 h-4" />
                <span>{{ isSavingEdits ? 'Guardando...' : 'Guardar Cambios' }}</span>
              </button>
            </template>
            <template v-else>
              <button
                type="button"
                @click="triggerEdit"
                class="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-[13px] font-semibold border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-all cursor-pointer shadow-2xs"
              >
                <Pencil class="w-4 h-4 text-[#EB5F46]" />
                <span>Editar</span>
              </button>
            </template>
          </template>

          <!-- 4. Botón 'Mover estado' (Gobernado por la configuración del estado actual en el Workflow) -->
          <button
            v-if="canShowManualMove"
            type="button"
            @click="showReubicarModal = true"
            class="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-[13px] font-semibold text-purple-700 bg-purple-50 hover:bg-purple-100 border border-purple-200 transition-colors cursor-pointer shadow-2xs"
            title="Mover estado manualmente según regla del flujo"
          >
            <Shuffle class="w-4 h-4 text-purple-600" />
            <span>Mover estado</span>
          </button>

          <!-- 5. Transición(es) de Avance en la Cabecera (Respeta las reglas y colores del Workflow) -->
          <template v-if="forwardEdges.length > 0">
            <button
              v-for="edge in forwardEdges"
              :key="edge.id"
              @click="handleWorkflowTransition(edge)"
              :style="getEdgeButtonStyle(edge)"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-[13px] font-bold shadow-xs transition-all cursor-pointer border hover:shadow-md hover:scale-[1.01]"
              :title="`Transición a ${edge.target}`"
            >
              <Send class="w-3.5 h-3.5 shrink-0" :style="{ color: getEdgeButtonStyle(edge).color }" />
              <span>{{ getEdgeButtonLabel(edge) }}</span>
            </button>
          </template>

          <!-- Fallback exclusivo si está en Observada y no hay aristas cargadas -->
          <template v-else-if="isObservedState">
            <button
              type="button"
              @click="triggerHeaderSubsanacion"
              style="background-color: #EEF2FF; border-color: #4F5AF5; color: #4F5AF5;"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-[13px] font-bold shadow-xs transition-all cursor-pointer border hover:shadow-md"
              title="Subsanar observación y reenviar la iniciativa"
            >
              <Send class="w-3.5 h-3.5 shrink-0 text-[#4F5AF5]" />
              <span>Subsanar y Reenviar</span>
            </button>
          </template>

          <!-- Fallbacks si no hay aristas cargadas del workflow (y no está observada) -->
          <template v-else-if="outgoingEdges.length === 0">
            <button
              v-if="initiative.status === 'Borrador'"
              @click="handleTransition('Enviar a Revisión', 'eval_bp')"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-[13px] font-semibold text-white bg-[#EB5F46] hover:bg-[#D94F38] shadow-sm cursor-pointer"
            >
              <Send class="w-3.5 h-3.5" />
              <span>Enviar a Revisión</span>
            </button>

            <button
              v-else-if="initiative.status === 'Pendiente de aprobación'"
              @click="handleTransition('Solicitar aprobación de BO', 'aprob_bo')"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-[13px] font-semibold text-white bg-[#EB5F46] hover:bg-[#D94F38] shadow-sm cursor-pointer"
            >
              <Send class="w-3.5 h-3.5" />
              <span>Solicitar aprobación de BO</span>
            </button>
          </template>
        </div>
      </div>

      <!-- ── BARRA DE METADATOS INSTITUCIONALES (6 CARDS DE IMAGEN 2) ── -->
      <div class="bg-white p-4 sm:p-5 rounded-2xl border border-slate-100 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
          <!-- 1. INSTITUCIÓN -->
          <div class="rounded-xl border border-slate-100 bg-white p-3 sm:p-3.5 flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-[#FFF7ED] text-[#EA580C] flex items-center justify-center shrink-0">
              <Building2 class="w-5 h-5 stroke-[2]" />
            </div>
            <div class="min-w-0 flex-1">
              <span class="text-[10px] font-extrabold text-[#94A3B8] uppercase tracking-wider block leading-tight">INSTITUCIÓN</span>
              <p class="text-xs sm:text-[13px] font-bold text-[#0D253F] leading-snug mt-0.5 break-words">
                {{ institucionDisplay }}
              </p>
            </div>
          </div>

          <!-- 2. VICEPRESIDENCIA -->
          <div class="rounded-xl border border-slate-100 bg-white p-3 sm:p-3.5 flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-[#FEF2F2] text-[#EF4444] flex items-center justify-center shrink-0">
              <Briefcase class="w-5 h-5 stroke-[2]" />
            </div>
            <div class="min-w-0 flex-1">
              <span class="text-[10px] font-extrabold text-[#94A3B8] uppercase tracking-wider block leading-tight">VICEPRESIDENCIA</span>
              <p class="text-xs sm:text-[13px] font-bold text-[#0D253F] leading-snug mt-0.5 break-words">
                {{ initiative.form_data?.vicepresidencia || 'Comercial' }}
              </p>
            </div>
          </div>

          <!-- 3. DIRECCIÓN SOLICITANTE -->
          <div class="rounded-xl border border-slate-100 bg-white p-3 sm:p-3.5 flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-[#FAF5FF] text-[#A855F7] flex items-center justify-center shrink-0">
              <MapPin class="w-5 h-5 stroke-[2]" />
            </div>
            <div class="min-w-0 flex-1">
              <span class="text-[10px] font-extrabold text-[#94A3B8] uppercase tracking-wider block leading-tight">DIRECCIÓN SOLICITANTE</span>
              <p class="text-xs sm:text-[13px] font-bold text-[#0D253F] leading-snug mt-0.5 break-words">
                {{ initiative.form_data?.direccion || 'Central de Admisión' }}
              </p>
            </div>
          </div>

          <!-- 4. LÍDER SOLICITANTE -->
          <div class="rounded-xl border border-slate-100 bg-white p-3 sm:p-3.5 flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-[#F0FDF4] text-[#16A34A] flex items-center justify-center shrink-0">
              <User class="w-5 h-5 stroke-[2]" />
            </div>
            <div class="min-w-0 flex-1">
              <span class="text-[10px] font-extrabold text-[#94A3B8] uppercase tracking-wider block leading-tight">LÍDER SOLICITANTE</span>
              <p class="text-xs sm:text-[13px] font-bold text-[#0D253F] leading-snug mt-0.5 break-words">
                {{ initiative.form_data?.registrador || initiative.form_data?.solicitante || 'Key User (Solicitante)' }}
              </p>
            </div>
          </div>

          <!-- 5. BUSINESS PARTNER TI (Highlighted in bold coral-red) -->
          <div class="rounded-xl border border-slate-100 bg-white p-3 sm:p-3.5 flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-[#F0FDFA] text-[#0D9488] flex items-center justify-center shrink-0">
              <UserCheck class="w-5 h-5 stroke-[2]" />
            </div>
            <div class="min-w-0 flex-1">
              <span class="text-[10px] font-extrabold text-[#94A3B8] uppercase tracking-wider block leading-tight">BUSINESS PARTNER TI</span>
              <p class="text-xs sm:text-[13px] font-bold text-[#EB5F46] leading-snug mt-0.5 break-words">
                {{ initiative.form_data?.bp_ti_asignado || initiative.form_data?.business_partner || 'José Pérez del Solar' }}
              </p>
            </div>
          </div>

          <!-- 6. FECHA DE REGISTRO -->
          <div class="rounded-xl border border-slate-100 bg-white p-3 sm:p-3.5 flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center shrink-0">
              <Calendar class="w-5 h-5 stroke-[2]" />
            </div>
            <div class="min-w-0 flex-1">
              <span class="text-[10px] font-extrabold text-[#94A3B8] uppercase tracking-wider block leading-tight">FECHA DE REGISTRO</span>
              <p class="text-xs sm:text-[13px] font-bold text-[#0D253F] leading-snug mt-0.5 break-words">
                {{ formatDateDDMMYYYY(initiative.created_at) }}
              </p>
            </div>
          </div>
        </div>

        <!-- ── APROBADORES SIGUIENTES (Configurable por estado desde el Diseñador de Workflow) ── -->
        <div
          v-if="showNextApproversCard && nextApproversData"
          class="mt-4 pt-3.5 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-gradient-to-r from-indigo-50/60 via-white to-indigo-50/20 p-3.5 sm:p-4 rounded-xl border border-indigo-100 shadow-2xs"
        >
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-indigo-100 text-[#4F5AF5] flex items-center justify-center shrink-0">
              <Building2 class="w-4 h-4 stroke-[2]" />
            </div>
            <div>
              <span class="text-[10px] font-extrabold text-[#4F5AF5] uppercase tracking-wider block leading-tight">
                {{ nextApproversData.title }}
              </span>
              <p class="text-xs font-semibold text-slate-700 mt-0.5">
                {{ nextApproversData.description }}
              </p>
            </div>
          </div>
          <div v-if="nextApproversData.roles.length > 0" class="flex flex-wrap items-center gap-1.5">
            <span
              v-for="(r, rIdx) in nextApproversData.roles"
              :key="rIdx"
              class="px-2.5 py-1 rounded-lg text-xs font-bold bg-white text-indigo-900 border border-indigo-200 shadow-2xs"
            >
              {{ r }}
            </span>
          </div>
        </div>
      </div>

      <!-- ── STEPPER HORIZONTAL CORPORATIVO (7 ETAPAS EXACTAS DE IMAGEN 2) ── -->
      <div class="bg-white p-5 sm:p-6 rounded-2xl border border-slate-100 shadow-[0_1px_3px_rgba(0,0,0,0.04)] overflow-x-auto">
        <div class="min-w-[760px] w-full">
          <div class="grid grid-cols-7 w-full relative">
            <div
              v-for="(stage, idx) in MACRO_STAGES"
              :key="stage.id"
              class="relative flex flex-col items-center text-center px-1"
            >
              <!-- Segmento conector izquierdo (del centro del paso anterior a este círculo) -->
              <div
                v-if="idx > 0"
                :class="[
                  'absolute top-4 sm:top-[18px] left-0 right-1/2 h-[2.5px] -translate-y-1/2 z-0 transition-colors duration-300',
                  idx <= currentStageIndex ? 'bg-[#059669]' : 'bg-slate-200'
                ]"
              ></div>

              <!-- Segmento conector derecho (de este círculo al siguiente paso) -->
              <div
                v-if="idx < MACRO_STAGES.length - 1"
                :class="[
                  'absolute top-4 sm:top-[18px] left-1/2 right-0 h-[2.5px] -translate-y-1/2 z-0 transition-colors duration-300',
                  idx < currentStageIndex ? 'bg-[#059669]' : 'bg-slate-200'
                ]"
              ></div>

              <!-- Círculo del Estado -->
              <div
                :class="[
                  'relative z-10 w-8 h-8 sm:w-9 sm:h-9 rounded-full flex items-center justify-center transition-all duration-200 select-none',
                  (getStageState(idx) === 'completed' || getStageState(idx) === 'active')
                    ? '!bg-[#059669] text-white shadow-xs'
                    : getStageState(idx) === 'observed'
                    ? '!bg-amber-500 text-white shadow-xs'
                    : getStageState(idx) === 'dismissed'
                    ? '!bg-rose-500 text-white shadow-xs'
                    : '!bg-white border-[1.5px] border-slate-300 text-slate-300',
                  getStageState(idx) === 'active'
                    ? 'ring-4 ring-[#818CF8]/40 ring-offset-2 ring-offset-white'
                    : ''
                ]"
              >
                <!-- Checkmark para completadas y activas (idéntico a Imagen 2) -->
                <Check v-if="getStageState(idx) === 'completed' || getStageState(idx) === 'active'" class="w-4 h-4 text-white stroke-[2.5]" />
                <AlertTriangle v-else-if="getStageState(idx) === 'observed'" class="w-3.5 h-3.5 text-white" />
                <X v-else-if="getStageState(idx) === 'dismissed'" class="w-3.5 h-3.5 text-white" />
                <div v-else class="w-2 h-2 rounded-full bg-slate-300"></div>
              </div>

              <!-- Textos del paso -->
              <div class="mt-2 space-y-0.5">
                <span
                  :class="[
                    'text-[11px] sm:text-xs block leading-tight',
                    getStageState(idx) === 'active'
                      ? 'text-[#EB5F46] font-bold'
                      : getStageState(idx) === 'completed'
                      ? 'text-slate-800 font-bold'
                      : getStageState(idx) === 'observed'
                      ? 'text-amber-700 font-bold'
                      : 'text-slate-400 font-medium'
                  ]"
                >
                  {{ stage.name }}
                </span>
                <span class="text-[10px] text-slate-400 block font-normal leading-tight">
                  {{ stage.role }}
                </span>

                <!-- Sub-pasos interactivos (para Estimación y Planificación) -->
                <div v-if="stage.substepsCount" class="relative inline-block pt-0.5">
                  <button
                    type="button"
                    @click="toggleSubsteps(stage.id)"
                    class="text-[10px] font-semibold text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 px-2 py-0.5 rounded-md inline-flex items-center gap-1 transition-colors cursor-pointer"
                  >
                    <span>{{ stage.substepsCount }} pasos</span>
                    <ChevronDown class="w-3 h-3 transition-transform" :class="activePopoverStage === stage.id ? 'rotate-180' : ''" />
                  </button>

                  <!-- Popover flotante con detalle de sub-pasos -->
                  <div
                    v-if="activePopoverStage === stage.id"
                    class="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-64 bg-white rounded-xl shadow-xl border border-slate-200 p-3 z-30 text-left space-y-2 animate-in fade-in zoom-in-95 duration-150"
                  >
                    <div class="flex items-center justify-between border-b border-slate-100 pb-1.5">
                      <span class="text-[11px] font-bold text-slate-800">Sub-etapas de {{ stage.name }}</span>
                      <button @click.stop="activePopoverStage = null" class="text-slate-400 hover:text-slate-600">✕</button>
                    </div>
                    <ul class="space-y-1.5 text-[11px] text-slate-600">
                      <li v-for="(substep, sIdx) in stage.substeps" :key="sIdx" class="flex items-start gap-1.5">
                        <span class="w-4 h-4 rounded-full bg-slate-100 text-slate-600 font-bold text-[9px] flex items-center justify-center shrink-0 mt-0.5">
                          {{ sIdx + 1 }}
                        </span>
                        <span>{{ substep }}</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── BARRA DE PESTAÑAS (IDÉNTICA A IMÁGENES 2, 3 Y 4) ── -->
      <div class="flex items-center gap-1.5 p-1.5 bg-slate-100/90 rounded-2xl border border-slate-200/90 w-full sm:w-fit overflow-x-auto shadow-2xs">
        <!-- Pestaña 1: Información de la Necesidad -->
        <button
          type="button"
          @click="activeDetailTab = 'info'"
          :class="[
            'flex items-center gap-2 px-3.5 sm:px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer',
            activeDetailTab === 'info'
              ? 'bg-white text-[#EB5F46] shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
          ]"
        >
          <FileText :class="['w-4 h-4 shrink-0 transition-colors', activeDetailTab === 'info' ? 'text-[#EB5F46]' : 'text-slate-500']" />
          <span>Información</span>
          <span class="hidden sm:inline"> de la Necesidad</span>
        </button>

        <!-- Pestaña 2: Trazabilidad & Cambios -->
        <button
          type="button"
          @click="activeDetailTab = 'history'"
          :class="[
            'flex items-center gap-2 px-3.5 sm:px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer',
            activeDetailTab === 'history'
              ? 'bg-white text-[#EB5F46] shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
          ]"
        >
          <Clock :class="['w-4 h-4 shrink-0 transition-colors', activeDetailTab === 'history' ? 'text-[#EB5F46]' : 'text-slate-500']" />
          <span>Trazabilidad</span>
          <span class="hidden sm:inline"> & Cambios</span>
        </button>

        <!-- Pestaña 3: Observaciones & Movimientos (con badge interactivo) -->
        <button
          type="button"
          @click="activeDetailTab = 'observations'"
          :class="[
            'flex items-center gap-2 px-3.5 sm:px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer',
            activeDetailTab === 'observations'
              ? 'bg-white text-[#EB5F46] shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
          ]"
        >
          <MessageSquare :class="['w-4 h-4 shrink-0 transition-colors', activeDetailTab === 'observations' ? 'text-[#EB5F46]' : 'text-slate-500']" />
          <span>Observaciones</span>
          <span class="hidden sm:inline"> & Movimientos</span>
          <span
            v-if="observationCount > 0"
            :class="[
              'inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full text-[10px] font-black leading-none transition-all',
              isObservedState ? 'bg-amber-500 text-white animate-pulse' : 'bg-slate-200 text-slate-700'
            ]"
          >
            {{ observationCount }}
          </span>
        </button>
      </div>

      <!-- ── CONTENIDO ACTIVO SEGÚN PESTAÑA ── -->
      <!-- TAB 1: Información de la Necesidad (Imagen 2) -->
      <InitiativeInfoTab
        v-if="activeDetailTab === 'info'"
        ref="infoTabRef"
        :initiative="initiative"
        :is-admin="isAdmin"
        :can-edit="canEditCurrentState"
        :is-saving="isSavingEdits"
        @save-edits="handleSaveEdits"
        @submit-subsanacion="handleSubsanacion"
      />

      <!-- TAB 2: Trazabilidad & Cambios (Imagen 3) -->
      <InitiativeTraceabilityTab
        v-else-if="activeDetailTab === 'history'"
        :initiative="initiative"
        :stage-records="stageRecords"
      />

      <!-- TAB 3: Observaciones & Movimientos (Imagen 4) -->
      <InitiativeObservationsTab
        v-else-if="activeDetailTab === 'observations'"
        :initiative="initiative"
      />
    </div>

    <!-- ── MODALES INSTITUCIONALES ── -->
    <!-- Modal de Observar -->
    <InitiativeObserveModal
      :is-open="showObserveModal"
      :is-submitting="isSubmitting"
      @close="showObserveModal = false"
      @confirm="handleObserveConfirm"
    />

    <!-- Modal de Reubicación Manual (Salto Libre) -->
    <InitiativeReubicarModal
      :is-open="showReubicarModal"
      :current-status="initiative?.status || 'Estado actual'"
      :available-nodes="availableNodes"
      :is-submitting="isSubmitting"
      @close="showReubicarModal = false"
      @confirm="handleReubicarConfirm"
    />

    <!-- Modal de Desestimar -->
    <InitiativeDesestimarModal
      :is-open="showDesestimarModal"
      :is-submitting="isSubmitting"
      @close="showDesestimarModal = false"
      @confirm="handleDesestimarConfirm"
    />

    <!-- Modal de Consentimiento y Firma Electrónica -->
    <div
      v-if="showConsentModal && selectedConsent"
      class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 class="font-bold text-slate-900 text-base">{{ selectedConsent.title }}</h3>
          <button @click="showConsentModal = false" class="text-slate-400 hover:text-slate-600">✕</button>
        </div>

        <div class="bg-indigo-50/60 border border-indigo-100 rounded-xl p-4 text-xs text-indigo-900 leading-relaxed">
          {{ selectedConsent.statement }}
        </div>

        <label class="flex items-start gap-3 cursor-pointer pt-2">
          <input
            v-model="consentAccepted"
            type="checkbox"
            class="mt-1 rounded text-[#4F5AF5] focus:ring-[#4F5AF5]"
          />
          <span class="text-xs text-slate-700 leading-tight">
            Acepto formalmente el dictamen técnico y certifico la viabilidad de la iniciativa.
          </span>
        </label>

        <div class="flex justify-end gap-3 pt-4 border-t border-slate-100">
          <button
            @click="showConsentModal = false"
            class="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer"
          >
            Cancelar
          </button>
          <button
            @click="applyStateUpdate(pendingTransition?.targetId || 'planificacion', pendingTransition?.actionLabel || 'Aprobar (VoBo)')"
            :disabled="!consentAccepted || isSubmitting"
            class="px-5 py-2 text-xs font-semibold text-white bg-[#4F5AF5] hover:bg-[#3F49E0] rounded-xl disabled:opacity-50 transition-colors shadow-sm cursor-pointer"
          >
            {{ pendingTransition?.actionLabel ? `Firmar: ${pendingTransition.actionLabel}` : 'Firmar y Pasar a Demanda' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal de Confirmación de Transición de Estado -->
    <CommonTransitionConfirmationModal
      :is-open="showConfirmModal"
      title="¿Estás seguro de la acción que estás realizando?"
      :action-label="pendingEdgeTransition?.actionLabel || 'Avanzar'"
      :current-state="initiative?.status || 'Estado actual'"
      :target-state="pendingEdgeTransition?.targetLabel || 'Siguiente estado'"
      :initiative-title="initiative?.summary?.titulo || initiative?.form_data?.titulo || initiative?.id || ''"
      :is-submitting="isSubmitting"
      confirm-text="Aceptar"
      cancel-text="Regresar"
      @confirm="confirmStateTransition"
      @cancel="cancelConfirmTransition"
    />

    <!-- Modal de Éxito tras completar Transición -->
    <CommonTransitionSuccessModal
      :is-open="showSuccessModal"
      :title="successModalData.title"
      :action-label="successModalData.actionLabel"
      :next-status="successModalData.nextStatus"
      :message="successModalData.message"
      primary-button-text="Continuar"
      @primary="showSuccessModal = false"
      @close="showSuccessModal = false"
    />

    <!-- ── MODAL: CONVERSACIÓN CON TEO (ASISTENTE COGNITIVO) ── -->
    <div
      v-if="showTeoChatModal"
      class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150"
    >
      <div class="bg-white rounded-3xl max-w-2xl w-full p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[85vh] flex flex-col">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3 shrink-0">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-full bg-[#FFF0ED] text-[#EB5F46] border border-[#FCD9D2] flex items-center justify-center font-bold text-xs">
              TEO
            </div>
            <div>
              <h3 class="font-bold text-slate-900 text-sm">Conversación Cronológica con Teo</h3>
              <p class="text-[11px] text-slate-400">Levantamiento interactivo con Inteligencia Artificial (Vertex AI)</p>
            </div>
          </div>
          <button @click="showTeoChatModal = false" class="text-slate-400 hover:text-slate-600 cursor-pointer p-1 rounded-lg">✕</button>
        </div>

        <!-- Mensajes del chat -->
        <div class="flex-1 overflow-y-auto space-y-3.5 pr-2 min-h-[250px] max-h-[550px]">
          <div v-if="!initiative?.chat_history || initiative.chat_history.length === 0" class="py-16 text-center text-slate-400 text-xs">
            No hay transcripción de chat registrada para esta iniciativa.
          </div>
          <template v-else>
            <div
              v-for="(msg, idx) in initiative.chat_history"
              :key="idx"
              :class="['flex items-start gap-2.5 max-w-[88%]', msg.role === 'user' ? 'ml-auto flex-row-reverse' : '']"
            >
              <div
                :class="[
                  'w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0',
                  msg.role === 'user' ? 'bg-slate-900 text-white' : 'bg-[#FFF0ED] text-[#EB5F46] border border-[#FCD9D2]'
                ]"
              >
                {{ msg.role === 'user' ? 'YO' : 'TEO' }}
              </div>
              <div
                :class="[
                  'p-3.5 rounded-2xl text-xs leading-relaxed',
                  msg.role === 'user'
                    ? 'bg-slate-900 text-white rounded-tr-none'
                    : 'bg-slate-50 border border-slate-200 text-slate-800 rounded-tl-none'
                ]"
              >
                <div class="text-[9px] uppercase font-bold tracking-wider mb-1 opacity-60">
                  {{ msg.role === 'user' ? 'Solicitante' : 'Teo' }}
                </div>
                <p class="whitespace-pre-line">{{ msg.text }}</p>
              </div>
            </div>
          </template>
        </div>

        <div class="flex justify-end pt-3 border-t border-slate-100 shrink-0">
          <button
            type="button"
            @click="showTeoChatModal = false"
            class="px-5 py-2 text-xs font-bold text-white bg-[#EB5F46] hover:bg-[#D94F38] rounded-xl transition-colors shadow-sm cursor-pointer"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
