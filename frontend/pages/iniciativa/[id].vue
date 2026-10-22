<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue';
import {
  ArrowLeft, CheckCircle, AlertTriangle, AlertCircle, Ban, FileText,
  MessageSquare, Sparkles, Building2, Briefcase, MapPin, User, ShieldCheck, UserCheck,
  Calendar, Check, X, FileCheck2, Clock, Send, ArrowRight,
  Shuffle, Pencil, Save, ChevronDown, Copy, Layers, Lock, Bot
} from 'lucide-vue-next';
import type { Initiative, InitiativeStageRecord, StageConsent, StageForm, WorkflowTransitionResult } from '~/types';
import InstitutionalLoader from '~/components/common/InstitutionalLoader.vue';
import InitiativeInfoTab from '~/components/initiative/InitiativeInfoTab.vue';
import InitiativeTraceabilityTab from '~/components/initiative/InitiativeTraceabilityTab.vue';
import InitiativeObservationsTab from '~/components/initiative/InitiativeObservationsTab.vue';
import InitiativeObserveModal from '~/components/initiative/InitiativeObserveModal.vue';
import InitiativeReubicarModal from '~/components/initiative/InitiativeReubicarModal.vue';
import InitiativeDesestimarModal from '~/components/initiative/InitiativeDesestimarModal.vue';
import InitiativeStageDecisionPanel from '~/components/initiative/InitiativeStageDecisionPanel.vue';
import InitiativeStageDetailView from '~/components/initiative/InitiativeStageDetailView.vue';
import { formatDateDDMMYYYY } from '~/utils/initiativeHistory';
import { DEFAULT_MACRO_STAGES, type MacroStageDef } from '~/utils/macroStages';
import { formatMarkdownToHtml } from '~/utils/formatHtml';

const route = useRoute();
const id = route.params.id as string;
const config = useRuntimeConfig();
const apiBase = config.public.apiBase;
const { aiName, aiAvatar, loadAiConfig } = useAiAssistant();

onMounted(() => {
  loadAiConfig();
});

// ─── Toast Institucional UX ──────────────────────────────────────────────────
interface ToastNotification {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  title?: string;
  message: string;
  details?: string[];
}

const toast = ref<ToastNotification | null>(null);
let toastTimer: any = null;

const showToast = (
  message: string,
  type: 'success' | 'warning' | 'error' | 'info' = 'info',
  options?: { title?: string; details?: string[]; duration?: number }
) => {
  if (toastTimer) clearTimeout(toastTimer);
  toast.value = {
    id: String(Date.now()),
    type,
    title: options?.title,
    message,
    details: options?.details,
  };
  const duration = options?.duration ?? (type === 'error' || options?.details ? 6000 : 4000);
  toastTimer = setTimeout(() => {
    toast.value = null;
  }, duration);
};

const closeToast = () => {
  if (toastTimer) clearTimeout(toastTimer);
  toast.value = null;
};

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

// ─── Cargar Catálogo de Formularios, Consentimientos y Organización ─────────
const { data: stageFormsData } = await useFetch<any>(`${apiBase}/stage-forms`);
const { data: stageConsentsData } = await useFetch<any>(`${apiBase}/stage-consents`);
const { data: usersData } = await useFetch<any>(`${apiBase}/admin/users`);
const { data: vpsData } = await useFetch<any>(`${apiBase}/admin/vps`);
const { data: direccionesData } = await useFetch<any>(`${apiBase}/admin/direcciones`);

// ─── Usuario y Roles Actuales ────────────────────────────────────────────────
const currentUser = ref({
  id: '',
  name: 'Administrador General',
  email: 'admin@iacs.empresa.com',
  roles: ['admin'] as string[],
  vp_id: null as string | null,
  vp_name: '' as string,
  vpName: '' as string,
  direcciones: [] as string[],
  direcciones_ids: [] as string[],
  profile_roles: [] as any[],
});

const loadCurrentUser = () => {
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
          vp_id: u.vp_id || null,
          vp_name: u.vp_name || u.vpName || '',
          vpName: u.vp_name || u.vpName || '',
          direcciones: Array.isArray(u.direcciones) ? u.direcciones : [],
          direcciones_ids: Array.isArray(u.direcciones_ids) ? u.direcciones_ids : [],
          profile_roles: Array.isArray(u.profile_roles) ? u.profile_roles : [],
        };
      } catch (e) {}
    }
  }
};

onMounted(async () => {
  loadCurrentUser();

  if (process.client) {
    window.addEventListener('iacs_user_updated', () => {
      loadCurrentUser();
    });

    try {
      const emailParam = currentUser.value.email;
      if (emailParam) {
        const token = localStorage.getItem('iacs_token');
        const headers: Record<string, string> = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const fresh: any = await $fetch(`${apiBase}/auth/me?email=${encodeURIComponent(emailParam)}`, { headers });
        if (fresh && fresh.email) {
          currentUser.value = {
            id: fresh.id || currentUser.value.id,
            name: fresh.name || currentUser.value.name,
            email: fresh.email || currentUser.value.email,
            roles: (fresh.roles && fresh.roles.length > 0) ? fresh.roles : currentUser.value.roles,
            vp_id: fresh.vp_id || null,
            vp_name: fresh.vp_name || fresh.vpName || '',
            vpName: fresh.vp_name || fresh.vpName || '',
            direcciones: Array.isArray(fresh.direcciones) ? fresh.direcciones : [],
            direcciones_ids: Array.isArray(fresh.direcciones_ids) ? fresh.direcciones_ids : [],
            profile_roles: Array.isArray(fresh.profile_roles) ? fresh.profile_roles : [],
          };
        }
      }
    } catch (e) {}
  }
});

const userRolesList = computed(() => currentUser.value.roles.map((r: string) => r.toLowerCase()));
const isAdmin = computed(() => userRolesList.value.includes('admin') || userRolesList.value.includes('administrador'));

// ─── Validación de Alcance Organizacional (Vicepresidencia y Direcciones) ───
const hasOrganizationalScope = (targetRole?: string): boolean => {
  if (isAdmin.value) return true;
  if (!initiative.value) return false;

  const initFd = initiative.value.form_data || {};
  const initVpRaw = (initFd.vicepresidencia || '').toString().trim();
  const initDirRaw = (initFd.direccion || '').toString().trim();

  // Si la iniciativa no especifica VP en su ficha, no se restringe por VP
  if (!initVpRaw) return true;

  const allVps: any[] = Array.isArray(vpsData.value) ? vpsData.value : (vpsData.value?.data || []);
  const allDirs: any[] = Array.isArray(direccionesData.value) ? direccionesData.value : (direccionesData.value?.data || []);

  // Encontrar el objeto VP de la iniciativa
  const initiativeVpObj = allVps.find((v: any) =>
    v.id === initVpRaw ||
    v.name?.toLowerCase().trim() === initVpRaw.toLowerCase().trim()
  );
  const initiativeVpId = initiativeVpObj?.id || initVpRaw;
  const initiativeVpName = initiativeVpObj?.name || initVpRaw;

  // Encontrar el objeto Dirección de la iniciativa
  const initiativeDirObj = allDirs.find((d: any) =>
    d.id === initDirRaw ||
    d.name?.toLowerCase().trim() === initDirRaw.toLowerCase().trim()
  );
  const initiativeDirId = initiativeDirObj?.id || initDirRaw;
  const initiativeDirName = initiativeDirObj?.name || initDirRaw;

  // Evaluar asignaciones de rol del usuario
  const userAssignments = currentUser.value.profile_roles || [];

  if (userAssignments.length === 0) {
    if (userRolesList.value.some(r => r === 'admin' || r === 'entrenador_ia')) {
      return true;
    }
    const userVpName = (currentUser.value.vp_name || currentUser.value.vpName || '').toLowerCase().trim();
    const userVpId = currentUser.value.vp_id;
    if (userVpName || userVpId) {
      const vpMatches = (userVpId && userVpId === initiativeVpId) || (userVpName && userVpName === initiativeVpName.toLowerCase().trim());
      if (!vpMatches) return false;

      if (currentUser.value.direcciones?.length > 0 && initiativeDirName) {
        const dirMatches = currentUser.value.direcciones.some((dName: string) =>
          dName.toLowerCase().trim() === initiativeDirName.toLowerCase().trim()
        );
        if (!dirMatches && currentUser.value.direcciones_ids?.length > 0) {
          return currentUser.value.direcciones_ids.includes(initiativeDirId);
        }
        return dirMatches;
      }
      return true;
    }
    return false;
  }

  // Filtrar asignaciones si se especificó forRole
  let relevantAssignments = userAssignments;
  if (targetRole) {
    const tLower = targetRole.toLowerCase().trim();
    const aliases = new Set([tLower, ...(ROLE_ALIASES[tLower] || []).map(a => a.toLowerCase().trim())]);
    relevantAssignments = userAssignments.filter((a: any) => {
      const aRole = (a.role || '').toLowerCase().trim();
      return aliases.has(aRole) || (ROLE_ALIASES[aRole] || []).some(al => aliases.has(al.toLowerCase().trim()));
    });
  }

  if (relevantAssignments.length === 0) {
    return false;
  }

  return relevantAssignments.some((a: any) => {
    // 1. Asignación con alcance transversal global
    if (a.is_transversal || a.role === 'admin' || a.role === 'entrenador_ia') {
      return true;
    }

    // 2. Verificar correspondencia de Vicepresidencia
    const assignmentVpObj = allVps.find((v: any) => v.id === a.vp_id);
    const assignmentVpName = assignmentVpObj?.name || '';
    const vpMatches = (a.vp_id && a.vp_id === initiativeVpId) ||
                      (assignmentVpName && assignmentVpName.toLowerCase().trim() === initiativeVpName.toLowerCase().trim());

    if (!vpMatches) {
      return false;
    }

    // 3. Si la asignación tiene Direcciones específicas acotadas:
    const assignedDirIds: string[] = a.direcciones_ids || [];
    if (assignedDirIds.length > 0 && initDirRaw) {
      const dirIdMatches = assignedDirIds.includes(initiativeDirId);
      if (dirIdMatches) return true;

      const assignedDirNames = allDirs
        .filter((d: any) => assignedDirIds.includes(d.id))
        .map((d: any) => d.name?.toLowerCase().trim());

      return assignedDirNames.includes(initiativeDirName.toLowerCase().trim());
    }

    return true;
  });
};

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
  if (!hasOrganizationalScope()) return false;

  const edgeData = edge.data || {};
  const condCfg = edge.condition_config || {};
  const allowed: string[] = edgeData.allowed_roles || edge.allowed_roles || condCfg.allowed_roles;

  const userRolesExpanded = new Set<string>();
  userRolesList.value.forEach((r: string) => {
    const rClean = r.toLowerCase().trim();
    userRolesExpanded.add(rClean);
    (ROLE_ALIASES[rClean] || []).forEach(alias => userRolesExpanded.add(alias.toLowerCase().trim()));
  });

  // 1. Si la flecha tiene explícitamente configurada la lista de roles autorizados (Transition RBAC):
  if (Array.isArray(allowed)) {
    // Si tiene 0 roles seleccionados, ningún usuario estándar puede verla ni ejecutarla
    if (allowed.length === 0) {
      return false;
    }

    const matchingAllowedRole = allowed.find((allowedRole: string) => {
      const normalized = allowedRole.toLowerCase().trim();
      if (userRolesExpanded.has(normalized)) return true;
      const aliases = ROLE_ALIASES[normalized] || [];
      return aliases.some(a => userRolesExpanded.has(a.toLowerCase().trim()));
    });

    if (!matchingAllowedRole) return false;
    return hasOrganizationalScope(matchingAllowedRole);
  }

  // 2. Si la flecha no tiene 'allowed_roles' explícito, hereda los roles asignados al nodo origen:
  const sourceNode = activeWorkflow.value?.graph_json?.nodes?.find((n: any) => n.id === edge.source);
  const sourceRoles: Array<{ role_name: string; can_approve?: boolean }> = sourceNode?.data?.roles || [];

  if (sourceRoles.length > 0) {
    const matching = sourceRoles.filter((sr: any) => {
      const srRole = (sr.role_name || '').toLowerCase().trim();
      return userRolesExpanded.has(srRole) || (ROLE_ALIASES[srRole] || []).some(a => userRolesExpanded.has(a.toLowerCase().trim()));
    });

    if (matching.length === 0) return false;
    return matching.some((sr: any) => sr.can_approve !== false) && hasOrganizationalScope(matching[0].role_name);
  }

  // 3. Casos por defecto si no hay roles en la flecha ni en el nodo:
  const st = (initiative.value?.status || '').toLowerCase();
  if (st.includes('borrador') || st.includes('draft') || edge.source === 'borrador' || edge.source === 'start') {
    return userRolesExpanded.has('registrador') || userRolesExpanded.has('key_user');
  }

  return false;
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
  subRoles?: Record<string, string>;
  statusKeywords: string[];
}

const MACRO_STAGES = computed<MacroStage[]>(() => {
  const custom = activeWorkflow.value?.graph_json?.macro_stages;
  if (Array.isArray(custom) && custom.length > 0) {
    return custom.map((s: any, idx: number) => {
      const id = s.id || `stage_${idx + 1}`;
      const defaultMatch = DEFAULT_MACRO_STAGES.find(d => d.id === id || d.name.toLowerCase() === (s.name || '').toLowerCase());
      return {
        id: id,
        name: s.name || `Etapa ${idx + 1}`,
        role: s.role || 'Responsable',
        subRoles: s.subRoles || defaultMatch?.subRoles || {},
        nodeIds: Array.isArray(s.nodeIds) && s.nodeIds.length > 0 ? s.nodeIds : (defaultMatch?.nodeIds || [id]),
        statusKeywords: Array.isArray(s.statusKeywords) && s.statusKeywords.length > 0 ? s.statusKeywords : (defaultMatch?.statusKeywords || [s.name.toLowerCase(), id.toLowerCase()]),
      };
    });
  }
  return DEFAULT_MACRO_STAGES.map((s: any) => ({
    id: s.id,
    name: s.name,
    role: s.role,
    subRoles: s.subRoles || {},
    nodeIds: s.nodeIds || [s.id],
    statusKeywords: s.statusKeywords || [s.name.toLowerCase(), s.id.toLowerCase()],
  }));
});

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
  const stages = MACRO_STAGES.value;

  for (let i = 0; i < stages.length; i++) {
    const s = stages[i];
    if (s.nodeIds.some(nid => currNode === nid || currNode.includes(nid))) {
      return i;
    }
  }

  for (let i = 0; i < stages.length; i++) {
    const s = stages[i];
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
  const stages = MACRO_STAGES.value;
  if (stages.length <= 1) return 0;
  const idx = Math.min(Math.max(currentStageIndex.value, 0), stages.length - 1);
  return (idx / (stages.length - 1)) * 100;
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
  if (st.includes('iniciativa planificada')) return 'Observar iniciativa planificada';
  if (st.includes('planific')) return 'Observar planificación';
  if (st.includes('estimac')) return 'Observar estimación';
  if (st.includes('demanda')) return 'Observar demanda';
  return 'Observar / Solicitar Ajustes';
});

const activePopoverStage = ref<string | null>(null);
const toggleSubsteps = (stageId: string) => {
  activePopoverStage.value = activePopoverStage.value === stageId ? null : stageId;
};

// ─── Sub-estados configurables y visibles en Stepper ──────────────────────────
export interface SubNodeDef {
  id: string;
  label: string;
  role: string;
  order?: number;
}

const DEFAULT_MACRO_SUB_NODES: Record<string, SubNodeDef[]> = {
  registro: [
    { id: 'borrador', label: 'Ficha de Registro', role: 'Key User', order: 1 },
  ],
  viabilidad_bp: [
    { id: 'eval_bp', label: 'Viabilidad BP TI', role: 'BP TI', order: 1 },
    { id: 'observada', label: 'Observación BP TI', role: 'BP TI', order: 2 },
  ],
  patrocinio_bo: [
    { id: 'aprob_bo', label: 'Patrocinio BO', role: 'Business Owner', order: 1 },
  ],
  aprobacion_vp: [
    { id: 'aprob_vp', label: 'Aprobación VP', role: 'VP Negocio', order: 1 },
  ],
  demanda_ti: [
    { id: 'asig_demanda', label: 'Asignación Gestor Demanda', role: 'Gestor Demanda', order: 1 },
    { id: 'asig_dominio', label: 'Asignación Líder Dominio', role: 'Gestor Demanda', order: 2 },
  ],
  estimacion: [
    { id: 'ventana_est', label: 'Compromiso Estimación', role: 'Líder Dominio', order: 1 },
    { id: 'est_con_presupuesto', label: 'Estimación con Presupuesto', role: 'Líder Dominio', order: 2 },
    { id: 'est_sin_presupuesto', label: 'Estimación sin Presupuesto', role: 'Líder Dominio', order: 2 },
    { id: 'val_est_bp', label: 'Validación Estimación BP', role: 'BP TI', order: 3 },
    { id: 'vobo_est_bo', label: 'VoBo Estimación BO', role: 'Business Owner', order: 4 },
  ],
  planificacion: [
    { id: 'plan_fechas', label: 'Planificación de Fechas', role: 'Líder Dominio', order: 1 },
    { id: 'val_plan_bp', label: 'Validación Planificación BP', role: 'BP TI', order: 2 },
    { id: 'aprob_plan_bo', label: 'Aprobación Final Fechas', role: 'Business Owner', order: 3 },
    { id: 'planificacion', label: 'Pase a Producción / Cartera', role: 'Gestor Demanda', order: 4 },
  ],
};

const getStageAllSubNodes = (stageId: string): SubNodeDef[] => {
  const stage = MACRO_STAGES.value.find(s => s.id === stageId);
  const nodes = activeWorkflow.value?.graph_json?.nodes || [];

  // 1. Si la macro-etapa tiene nodeIds configurados explícitamente en el workflow activo
  if (stage && Array.isArray(stage.nodeIds) && stage.nodeIds.length > 0) {
    const subIds = stage.nodeIds.filter(nid => nid !== stage.id);
    if (subIds.length > 0) {
      return subIds.map((nid, idx) => {
        const nodeObj = nodes.find((n: any) => n.id === nid);
        const subRole = stage.subRoles?.[nid] || nodeObj?.data?.sub_stage_role || nodeObj?.data?.roles?.[0]?.role_name || nodeObj?.data?.role || 'Responsable';
        return {
          id: nid,
          label: nodeObj?.data?.label || nodeObj?.data?.name || nid,
          role: subRole,
          order: idx + 1,
        };
      });
    }
  }

  // 2. Buscar en el grafo del workflow activo si hay nodos configurados con parent_stage_id
  const stageNodeIds = (stage?.nodeIds || []).map(nid => nid.toLowerCase());
  const stageName = (stage?.name || '').toLowerCase();
  const configuredNodes = nodes.filter((n: any) => {
    const parent = (n.data?.parent_stage_id || '').toLowerCase().trim();
    if (!parent) return false;
    return (
      parent === stageId.toLowerCase() ||
      stageNodeIds.includes(parent) ||
      (stageName && (parent === stageName || stageName.includes(parent)))
    );
  });

  if (configuredNodes.length > 0) {
    return configuredNodes
      .map((n: any) => ({
        id: n.id,
        label: n.data?.label || n.data?.name || n.id,
        role: n.data?.sub_stage_role || n.data?.role || 'Responsable',
        order: Number(n.data?.sub_stage_order) || 99,
      }))
      .sort((a: SubNodeDef, b: SubNodeDef) => (a.order || 99) - (b.order || 99));
  }

  // 3. Fallback a sub-nodos predeterminados
  return DEFAULT_MACRO_SUB_NODES[stageId] || [];
};

const getStageVisibleSubNodes = (stageId: string): SubNodeDef[] => {
  const allSubs = getStageAllSubNodes(stageId);
  return allSubs;
};

const openSubstepperStageId = ref<string | null>(null);
const selectedSubNodeId = ref<string | null>(null);

const toggleSubstepper = (stageId: string) => {
  if (openSubstepperStageId.value === stageId) {
    openSubstepperStageId.value = null;
  } else {
    openSubstepperStageId.value = stageId;
  }
};

const openSubstepperStage = computed(() => {
  if (!openSubstepperStageId.value) return null;
  return MACRO_STAGES.value.find(s => s.id === openSubstepperStageId.value) || null;
});

const openSubstepperVisibleSubNodes = computed(() => {
  if (!openSubstepperStageId.value) return [];
  return getStageVisibleSubNodes(openSubstepperStageId.value);
});

const handleSelectSubNode = (stageId: string, subId: string) => {
  selectedTimelineStageKey.value = stageId;
  selectedSubNodeId.value = subId;
  activeDetailTab.value = 'info';
};

const isSubNodeCompleted = (subId: string, subLabel?: string) => {
  if (isSubNodeActive(subId)) return false;

  const sIdLower = (subId || '').toLowerCase();
  const sLabelLower = (subLabel || '').toLowerCase();

  // 1. Si la etapa macro que contiene este sub-nodo ya fue superada completamente
  if (openSubstepperStageId.value) {
    const stageIdx = MACRO_STAGES.value.findIndex(s => s.id === openSubstepperStageId.value);
    if (stageIdx !== -1 && stageIdx < currentStageIndex.value) {
      return true;
    }
    // Si estamos en la etapa macro actual, pero este sub-nodo está posicionado antes del sub-nodo activo
    if (stageIdx === currentStageIndex.value) {
      const subs = openSubstepperVisibleSubNodes.value;
      const thisIdx = subs.findIndex(s => (s.id || '').toLowerCase() === sIdLower);
      const activeIdx = subs.findIndex(s => isSubNodeActive(s.id));
      if (thisIdx !== -1 && activeIdx !== -1 && thisIdx < activeIdx) {
        return true;
      }
    }
  }

  // 2. Verificar en el historial de observaciones/transiciones
  const history = initiative.value?.form_data?._observation_history || [];
  const inHistory = history.some((h: any) => {
    const fromN = (h.from_node_id || '').toLowerCase();
    const fromS = (h.from_stage || '').toLowerCase();
    return fromN === sIdLower || (sLabelLower && (fromS === sLabelLower || fromS.includes(sLabelLower)));
  });
  if (inHistory) return true;

  // 3. Verificar en los registros de custodia (stageRecords)
  const records = stageRecords.value || [];
  return records.some((r: any) => {
    const rNode = (r.node_id || '').toLowerCase();
    const rStage = (r.stage_name || '').toLowerCase();
    return rNode === sIdLower || rNode.includes(sIdLower) ||
           (sLabelLower && (rStage === sLabelLower || rStage.includes(sLabelLower)));
  });
};

const isSubNodeActive = (subId: string) => {
  if (isDismissed.value) return false;
  return (currentNodeId.value || '').toLowerCase() === (subId || '').toLowerCase();
};

// ─── Selección Interactiva de Etapa en el Stepper Horizontal ─────────────────
const selectedTimelineStageKey = ref<string | null>(null);

const handleSelectTimelineStage = (stageId: string) => {
  if (selectedTimelineStageKey.value === stageId) {
    selectedTimelineStageKey.value = null; // Toggle off al hacer clic en la misma etapa
    selectedSubNodeId.value = null;
  } else {
    selectedTimelineStageKey.value = stageId;
    selectedSubNodeId.value = null; // Reiniciar filtro específico de sub-nodo al cambiar de etapa macro
    activeDetailTab.value = 'info';
  }
};

const selectedTimelineStage = computed(() => {
  if (!selectedTimelineStageKey.value) return null;
  return MACRO_STAGES.value.find(s => s.id === selectedTimelineStageKey.value) || null;
});

const selectedTimelineStageIndex = computed(() => {
  if (!selectedTimelineStageKey.value) return -1;
  return MACRO_STAGES.value.findIndex(s => s.id === selectedTimelineStageKey.value);
});

const selectedTimelineStageRecords = computed(() => {
  if (!selectedTimelineStage.value || !stageRecords.value) return [];
  const stg = selectedTimelineStage.value;
  const stgId = stg.id;

  const allSubNodes = getStageAllSubNodes(stgId);
  const subNodeIds = allSubNodes.map(s => s.id.toLowerCase());

  return (stageRecords.value || []).filter((r: any) => {
    const rNode = (r.node_id || '').toLowerCase().trim();
    const rStage = (r.stage_name || '').toLowerCase().trim();

    // 0. Match con sub-nodos asignados (configurados dinámicamente o por defecto)
    if (subNodeIds.some(sid => rNode === sid || rNode.includes(sid) || rStage.includes(sid))) {
      return true;
    }

    // 1. Match directo por IDs de nodo
    if (stg.nodeIds && stg.nodeIds.some((nid: string) => rNode === nid.toLowerCase() || rNode.includes(nid.toLowerCase()))) {
      return true;
    }

    // 2. Match por palabras clave de estado
    if (stg.statusKeywords && stg.statusKeywords.some((kw: string) => new RegExp(kw, 'i').test(rStage) || new RegExp(kw, 'i').test(rNode))) {
      return true;
    }

    // 3. Reglas semánticas por etapa
    if ((stgId === 'viabilidad_bp' || stgId === 'eval_bp') && (/bp/i.test(rStage) || /viabilidad/i.test(rStage))) return true;
    if ((stgId === 'patrocinio_bo' || stgId === 'aprob_bo') && (/bo/i.test(rStage) || /patrocinio/i.test(rStage) || /owner/i.test(rStage))) return true;
    if ((stgId === 'aprobacion_vp' || stgId === 'aprob_vp') && (/vp/i.test(rStage) || /vicepresid/i.test(rStage))) return true;
    if ((stgId === 'demanda_ti' || stgId === 'demanda') && (/demanda/i.test(rStage) || /dominio/i.test(rStage))) return true;
    if (stgId === 'estimacion' && (/estimaci/i.test(rStage) || /presupuesto/i.test(rStage) || /ventana/i.test(rStage))) return true;
    if (stgId === 'planificacion' && (/planifica/i.test(rStage) || /producci/i.test(rStage) || /cartera/i.test(rStage))) return true;

    return false;
  });
});

const institucionDisplay = computed(() => {
  if (!initiative.value?.form_data?.institucion) return 'UPN';
  const inst = initiative.value.form_data.institucion;
  return Array.isArray(inst) ? inst.join(', ') : String(inst);
});

const bpTiDisplay = computed(() => {
  const fd = initiative.value?.form_data || {};
  return (
    fd.bp_ti_asignado ||
    fd.bp_ti_responsable ||
    fd.business_partner ||
    fd.bp_ti ||
    'Sin asignar'
  );
});

const keyUserDisplay = computed(() => {
  const fd = initiative.value?.form_data || {};
  if (fd.registrador) return fd.registrador;
  if (fd.solicitante) return fd.solicitante;
  if (fd.lider_solicitante) return fd.lider_solicitante;
  if (fd.key_user) return fd.key_user;
  if (fd.nombre_solicitante) return fd.nombre_solicitante;
  if (fd.registrador_nombre) return fd.registrador_nombre;
  if (fd.registrador_email) return fd.registrador_email;

  if (Array.isArray(fd._observation_history) && fd._observation_history.length > 0) {
    const firstAction = fd._observation_history[0];
    if (firstAction?.user_name && firstAction.user_name !== 'Sistema') {
      return firstAction.user_name;
    }
  }

  return 'Sin especificar';
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
  if (!hasOrganizationalScope()) return false;

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
const SYSTEM_ROLES_MAP: Record<string, string> = {
  registrador: 'Key User (Solicitante)',
  key_user: 'Key User (Solicitante)',
  bp_ti: 'Business Partner TI',
  business_partner: 'Business Partner TI',
  business_owner: 'Business Owner',
  bo: 'Business Owner',
  vicepresidente_del_negocio: 'Vicepresidente del Negocio',
  vp: 'Vicepresidente',
  gestor_de_la_demanda: 'Gestor de la Demanda',
  lider_de_dominio: 'Líder de Dominio',
  admin: 'Administrador',
  administrador: 'Administrador',
};

const formatRoleName = (role?: string | null): string => {
  if (!role) return 'Responsable';
  const clean = String(role).trim().toLowerCase();
  return (
    SYSTEM_ROLES_MAP[clean] ||
    SYSTEM_ROLES_MAP[clean.replace(/[\s-]+/g, '_')] ||
    role.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  );
};

const isNonApproverState = computed(() => {
  const currId = (currentNodeId.value || '').toLowerCase();
  return ['borrador', 'observada', 'desestimada', 'end', 'iniciativa_planificada'].includes(currId);
});

const showNextApproversCard = computed(() => {
  if (isNonApproverState.value) return false;
  return Boolean(currentNodeObj.value?.data?.showNextApprovers);
});

const isVPApprovalState = computed(() => {
  return currentNodeId.value === 'aprob_vp' || /aprobaci[oó]n\s+vp/i.test(initiative.value?.status || '');
});

const nextApproversList = computed(() => {
  if (!showNextApproversCard.value || !currentNodeObj.value?.data) return [];
  const d = currentNodeObj.value.data;
  const source = (d.nextApproversSource as string) || (isVPApprovalState.value ? 'initiative_vp' : 'target_stage_roles');
  const includeAdmin = Boolean(d.includeAdminInApprovers);

  const initVpName = initiative.value?.form_data?.vicepresidencia;
  const allVps: any[] = Array.isArray(vpsData.value) ? vpsData.value : (vpsData.value?.data || []);
  const allUsers: any[] = Array.isArray(usersData.value) ? usersData.value : (usersData.value?.data || []);

  const matchedVp = allVps.find(
    (v: any) =>
      v.name?.toLowerCase().trim() === String(initVpName || '').toLowerCase().trim() ||
      v.id === initVpName
  );

  // Caso A: Etapa de Aprobación VP -> Mostrar el Vicepresidente asignado a la iniciativa
  if (source === 'initiative_vp' || (isVPApprovalState.value && source !== 'target_stage_roles')) {
    const vpUsers = allUsers.filter((u: any) => {
      const whitelist = Array.isArray(u.user_roles_whitelist) ? u.user_roles_whitelist : [];
      if (
        whitelist.some((w: any) =>
          ['vicepresidente_del_negocio', 'vp'].includes((w.role || '').toLowerCase().trim())
        )
      ) return true;
      if (Array.isArray(u.roles) && u.roles.some((ro: string) => ['vicepresidente_del_negocio', 'vp'].includes(ro.toLowerCase().trim()))) return true;
      return false;
    });

    const vpPersonName = matchedVp?.bp_name || (vpUsers.length > 0 ? vpUsers[0].name : null);
    const vpEmail = matchedVp?.email || (vpUsers.length > 0 ? vpUsers[0].email : null);

    const list: Array<{ id: string; name: string; person: string | null; email: string | null; role: string }> = [{
      id: matchedVp?.id || 'vp_assigned',
      name: vpPersonName || (initVpName ? `Vicepresidente de ${initVpName}` : 'Vicepresidente del Negocio'),
      person: initVpName ? `Vicepresidencia ${initVpName}` : 'Vicepresidencia',
      email: vpEmail,
      role: 'Vicepresidente del Negocio',
    }];

    if (includeAdmin) {
      list.push({
        id: 'admin_role',
        name: 'Administrador del Sistema',
        person: null,
        email: null,
        role: 'Administrador',
      });
    }
    return list;
  }

  // Caso B: Roles y Evaluadores del Estado (target_stage_roles)
  const stageRoles = (d.roles || []) as any[];
  const filteredRoles = includeAdmin
    ? stageRoles
    : stageRoles.filter((r: any) => {
        const roleStr = (r.role_name || r.name || '').toLowerCase();
        return roleStr !== 'admin' && roleStr !== 'administrador';
      });

  const result: Array<{ id: string; name: string; person: string | null; email: string | null; role: string }> = [];

  for (const r of filteredRoles) {
    const roleName = r.role_name || r.name || '';
    const roleLower = roleName.toLowerCase().trim();

    // 1. Si la iniciativa ya tiene una persona específica asignada en su expediente para este rol:
    let assignedPersonName: string | null = null;
    if (roleLower === 'bp_ti') assignedPersonName = (initiative.value?.form_data?.bp_ti_asignado as string) || (initiative.value?.form_data?.bp_ti_responsable as string) || null;
    if (roleLower === 'lider_de_dominio') assignedPersonName = (initiative.value?.form_data?.lider_tecnico_asignado as string) || null;
    if (roleLower === 'business_owner') assignedPersonName = (initiative.value?.form_data?.business_owner as string) || (initiative.value?.form_data?.bo_asignado as string) || null;

    // 2. Buscar personas registradas en el sistema con este rol
    const matchingUsers = allUsers.filter((u: any) => {
      const whitelist = Array.isArray(u.user_roles_whitelist) ? u.user_roles_whitelist : [];
      const hasRoleInWhitelist = whitelist.some((w: any) => {
        const rClean = (w.role || '').toLowerCase().trim();
        const matchesRole =
          rClean === roleLower ||
          (ROLE_ALIASES[rClean] || []).includes(roleLower) ||
          (ROLE_ALIASES[roleLower] || []).includes(rClean);

        if (!matchesRole) return false;

        // Si tiene alcance restringido a VP y no es transversal, verificar pertenencia a la VP de la iniciativa
        if (!w.is_transversal && (w.vp_id || w.vps?.name)) {
          const vpMatches =
            (w.vps?.name && initVpName && w.vps.name.toLowerCase().trim() === String(initVpName).toLowerCase().trim()) ||
            (w.vp_id && initVpName && (w.vp_id === initVpName || (matchedVp && w.vp_id === matchedVp.id)));
          if (!vpMatches) return false;
        }
        return true;
      });

      if (hasRoleInWhitelist) return true;

      if (Array.isArray(u.roles) && u.roles.some((ro: string) => {
        const roClean = ro.toLowerCase().trim();
        return roClean === roleLower || (ROLE_ALIASES[roClean] || []).includes(roleLower);
      })) return true;

      return false;
    });

    if (assignedPersonName) {
      const existingInDb = matchingUsers.find((u: any) =>
        (u.name || '').toLowerCase().trim() === assignedPersonName!.toLowerCase().trim() ||
        (u.email || '').toLowerCase().trim() === assignedPersonName!.toLowerCase().trim()
      );
      result.push({
        id: existingInDb?.id || assignedPersonName,
        name: existingInDb?.name || assignedPersonName,
        person: `${formatRoleName(roleName)} Asignado`,
        email: existingInDb?.email || null,
        role: formatRoleName(roleName),
      });
      continue;
    }

    if (matchingUsers.length > 0) {
      matchingUsers.forEach((u: any) => {
        const normName = (u.name || '').toLowerCase().trim();
        const normEmail = (u.email || '').toLowerCase().trim();
        const isAlreadyAdded = result.some(existing => {
          const exName = (existing.name || '').toLowerCase().trim();
          const exEmail = (existing.email || '').toLowerCase().trim();
          return (normEmail && exEmail && normEmail === exEmail) || (normName && exName && normName === exName);
        });

        if (!isAlreadyAdded) {
          result.push({
            id: u.id || u.email || u.name,
            name: u.name,
            person: null,
            email: u.email || null,
            role: formatRoleName(roleName),
          });
        }
      });
    } else {
      result.push({
        id: r.id || roleName,
        name: formatRoleName(roleName),
        person: null,
        email: null,
        role: 'Rol Requerido',
      });
    }
  }

  return result;
});

const nextApproversData = computed(() => {
  if (!currentNodeObj.value?.data) return null;
  const d = currentNodeObj.value.data;
  return {
    title: d.nextApproversTitle || 'Aprobadores siguientes (VPs)',
    roles: nextApproversList.value,
    description: d.nextApproversDescription || 'Relación de roles pendientes para avanzar la iniciativa.',
  };
});

const canObserveCurrentState = computed(() => {
  if (!initiative.value) return false;
  if (!hasOrganizationalScope()) return false;

  const st = (initiative.value.status || '').toLowerCase();
  if (
    st.includes('borrador') ||
    st.includes('draft') ||
    st.includes('desestimad') ||
    st.includes('observad') ||
    st.includes('cerrad') ||
    st.includes('finaliz')
  ) {
    return false;
  }

  // Administrador del sistema siempre tiene facultades de control y observación
  if (isAdmin.value) return true;

  // 1. Obtener el nodo actual del workflow activo
  const currNode = currentNodeObj.value || activeWorkflow.value?.graph_json?.nodes?.find((n: any) => n.id === currentNodeId.value);
  const nodeRoles: Array<{ role_name: string; can_reject?: boolean; can_approve?: boolean }> = currNode?.data?.roles || [];

  // 2. Roles del usuario actual normalizados y expandidos con alias
  const userRolesExpanded = new Set<string>();
  userRolesList.value.forEach((r: string) => {
    const rLower = r.toLowerCase().trim();
    userRolesExpanded.add(rLower);
    (ROLE_ALIASES[rLower] || []).forEach(alias => userRolesExpanded.add(alias.toLowerCase().trim()));
  });

  // 3. Si el nodo actual tiene roles asignados en el workflow:
  if (nodeRoles.length > 0) {
    const matching = nodeRoles.filter((nr: any) => {
      const nrRole = (nr.role_name || '').toLowerCase().trim();
      return userRolesExpanded.has(nrRole) || (ROLE_ALIASES[nrRole] || []).some(a => userRolesExpanded.has(a.toLowerCase().trim()));
    });
    if (matching.length === 0) {
      // El rol del usuario NO es el responsable de evaluar/aprobar esta etapa
      return false;
    }
    // Debe tener permiso de rechazar/observar en este nodo (can_reject !== false)
    return matching.some((nr: any) => nr.can_reject !== false) && hasOrganizationalScope(matching[0].role_name);
  }

  // 4. Si el nodo no define roles explícitos, verificar si el usuario tiene transiciones activas de observación
  const observeEdges = userOutgoingEdges.value.filter((edge: any) => {
    const targetId = (edge.target || '').toLowerCase();
    const label = (edge.label || '').toLowerCase();
    return targetId.includes('observad') || label.includes('observa');
  });
  if (observeEdges.length > 0) return true;

  // 5. Fallback a permisos de acción generales sobre la etapa
  return canActOnCurrentStage.value;
});

// Modal de Conversación con Teo
const showTeoChatModal = ref(false);
const openTeoChat = () => {
  loadAiConfig();
  showTeoChatModal.value = true;
};

// Permiso dinámico de Edición (RBAC gobernado por el nodo del Workflow)
const canEditCurrentState = computed(() => {
  if (!initiative.value) return false;
  if (!hasOrganizationalScope()) return false;

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
    // Si la configuración del nodo no permite editar (ningún rol tiene can_edit === true), esta etapa no es editable
    const stageAllowsEditing = nodeRoles.some((nr: any) => Boolean(nr.can_edit));
    if (!stageAllowsEditing) {
      return false;
    }

    // Si es administrador y la etapa permite edición según el workflow:
    if (isAdmin.value) {
      return true;
    }

    // Buscar los roles asignados a este nodo que coincidan con los roles del usuario
    const matchingRoles = nodeRoles.filter((nr: any) => {
      const nrRole = (nr.role_name || '').toLowerCase().trim();
      return userRolesExpanded.has(nrRole) || (ROLE_ALIASES[nrRole] || []).some(a => userRolesExpanded.has(a.toLowerCase().trim()));
    });

    if (matchingRoles.length > 0) {
      // El rol del usuario está asignado al nodo: el switch 'can_edit' configurado gobierna estrictamente el permiso
      return matchingRoles.some((nr: any) => Boolean(nr.can_edit));
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

// ─── Ficha de Dictamen y Consentimiento Dinámico de Etapa ───────────────────
const activeNodeForm = computed<StageForm | null>(() => {
  if (!currentNodeObj.value?.data?.form_id) return null;
  const targetId = currentNodeObj.value.data.form_id;
  const forms = stageFormsData.value?.data || stageFormsData.value?.forms || [];
  return forms.find((f: any) => f.id === targetId || f.code === targetId) || null;
});

const activeNodeConsent = computed<StageConsent | null>(() => {
  if (!currentNodeObj.value?.data?.consent_id) return null;
  const targetId = currentNodeObj.value.data.consent_id;
  const consents = stageConsentsData.value?.data || stageConsentsData.value?.consents || [];
  return consents.find((c: any) => c.id === targetId || c.code === targetId) || null;
});

const canActOnCurrentStage = computed(() => {
  if (isAdmin.value) return true;
  if (!initiative.value) return false;
  if (!hasOrganizationalScope()) return false;

  const currNode = currentNodeObj.value;
  const nodeRoles: Array<{ role_name: string; can_approve?: boolean; can_reject?: boolean; can_edit?: boolean }> = currNode?.data?.roles || [];

  const userRolesExpanded = new Set<string>();
  userRolesList.value.forEach((r: string) => {
    const rLower = r.toLowerCase().trim();
    userRolesExpanded.add(rLower);
    (ROLE_ALIASES[rLower] || []).forEach(alias => userRolesExpanded.add(alias.toLowerCase().trim()));
  });

  if (nodeRoles.length > 0) {
    const matching = nodeRoles.filter((nr: any) => {
      const nrRole = (nr.role_name || '').toLowerCase().trim();
      return userRolesExpanded.has(nrRole) || (ROLE_ALIASES[nrRole] || []).some(a => userRolesExpanded.has(a.toLowerCase().trim()));
    });
    if (matching.length > 0) {
      return matching.some((nr: any) => Boolean(nr.can_approve || nr.can_reject || nr.can_edit)) && hasOrganizationalScope(matching[0].role_name);
    }
  }

  if (userOutgoingEdges.value.length > 0) {
    return true;
  }

  return false;
});

const getEligibleRoleUsers = (field: any) => {
  const usersList = usersData.value || [];
  if (!field || !usersList.length) return [];
  const targetRoleRaw = (field.target_role || 'bp_ti').trim().toLowerCase();
  const filterByScope = field.filter_by_scope !== false;

  const formValues = initiative.value?.form_data || {};
  const vpName = formValues.vicepresidencia;
  const dirName = formValues.direccion;

  const allVps = vpsData.value || [];
  const allDirs = direccionesData.value || [];

  const vpObj = allVps.find((v: any) =>
    v.name?.toLowerCase().trim() === String(vpName || '').toLowerCase().trim() ||
    v.id === vpName
  );
  const vpId = vpObj?.id;

  const dirObj = allDirs.find((d: any) =>
    (d.name?.toLowerCase().trim() === String(dirName || '').toLowerCase().trim() || d.id === dirName) &&
    (!vpId || d.vp_id === vpId)
  );
  const dirId = dirObj?.id;

  return usersList.filter((u: any) => {
    const whitelist = u.user_roles_whitelist || [];
    if (!Array.isArray(whitelist)) return false;
    return whitelist.some((r: any) => {
      const userRole = (r.role || '').toLowerCase().trim();
      const roleMatches =
        userRole === targetRoleRaw ||
        (ROLE_ALIASES[userRole] || []).some(a => a.toLowerCase().trim() === targetRoleRaw);

      if (!roleMatches) return false;
      if (!filterByScope) return true;

      // Alcance transversal
      if (r.is_transversal === true) return true;
      if (!r.vp_id || r.vp_id === '') return true;

      // Alcance por VP / Dirección
      if (vpId && (r.vp_id === vpId || (vpName && r.vp_id === vpName))) {
        if (!r.direcciones_ids || !Array.isArray(r.direcciones_ids) || r.direcciones_ids.length === 0) return true;
        if (dirId && r.direcciones_ids.includes(dirId)) return true;
        if (dirName && r.direcciones_ids.includes(dirName)) return true;
        if (!dirId) return true;
      }
      return false;
    });
  });
};

const eligibleRoleUsersMap = computed(() => {
  const map: Record<string, any[]> = {};
  if (!activeNodeForm.value?.fields) return map;
  activeNodeForm.value.fields.forEach((f: any) => {
    if (f.type === 'role_user') {
      map[f.key] = getEligibleRoleUsers(f);
    }
  });
  return map;
});

const stageFormData = ref<Record<string, any>>({});
const stageConsentAccepted = ref(false);

// Inicializar stageFormData con valores ya guardados en initiative.form_data
watch(
  () => [activeNodeForm.value, initiative.value?.form_data],
  () => {
    if (!activeNodeForm.value) return;
    const fd = initiative.value?.form_data || {};
    const updated = { ...stageFormData.value };
    let changed = false;

    (activeNodeForm.value.fields || []).forEach((field: any) => {
      if (updated[field.key] === undefined && fd[field.key] !== undefined) {
        updated[field.key] = fd[field.key];
        changed = true;
      }
    });

    if (changed) {
      stageFormData.value = updated;
    }
  },
  { immediate: true }
);

// Asignación automática y bloqueo si hay un único candidato elegible
watch(
  () => [activeNodeForm.value, eligibleRoleUsersMap.value],
  () => {
    if (!activeNodeForm.value) return;
    const updated = { ...stageFormData.value };
    let changed = false;

    (activeNodeForm.value.fields || []).forEach((field: any) => {
      if (field.type === 'role_user') {
        const candidates = eligibleRoleUsersMap.value[field.key] || [];
        if (candidates.length === 1) {
          const onlyUser = candidates[0].name;
          if (updated[field.key] !== onlyUser) {
            updated[field.key] = onlyUser;
            changed = true;
          }
        }
      }
    });

    if (changed) {
      stageFormData.value = updated;
    }
  },
  { immediate: true }
);

let stageAutoSaveTimer: any = null;
const handleStageFieldChange = (key: string, value: any) => {
  stageFormData.value = {
    ...stageFormData.value,
    [key]: value,
  };

  if (initiative.value) {
    initiative.value.form_data = {
      ...(initiative.value.form_data || {}),
      [key]: value,
    };
  }

  if (stageAutoSaveTimer) clearTimeout(stageAutoSaveTimer);
  stageAutoSaveTimer = setTimeout(async () => {
    try {
      await $fetch(`${apiBase}/initiatives/${id}`, {
        method: 'PATCH',
        body: {
          form_data: {
            ...(initiative.value?.form_data || {}),
            ...stageFormData.value,
          },
        },
      });
    } catch (e) {
      console.warn('Auto-save error on stage field:', e);
    }
  }, 700);
};

const missingStageFields = computed(() => {
  if (!activeNodeForm.value) return [];
  const currFd = { ...(initiative.value?.form_data || {}), ...stageFormData.value };
  return (activeNodeForm.value.fields || [])
    .filter((f: any) => {
      if (!f.required) return false;
      const val = currFd[f.key];
      if (val !== undefined && val !== null && String(val).trim() !== '') return false;
      if (f.type === 'role_user') {
        const eligible = eligibleRoleUsersMap.value[f.key] || [];
        if (eligible.length === 1) return false;
      }
      return true;
    })
    .map((f: any) => f.label || f.key);
});

const dateRangeErrors = computed(() => {
  if (!activeNodeForm.value?.fields) return [];
  const errors: string[] = [];
  const currFd = { ...(initiative.value?.form_data || {}), ...stageFormData.value };

  for (const field of activeNodeForm.value.fields) {
    if (field.type !== 'date') continue;
    const key = (field.key || '').toLowerCase();
    const label = (field.label || '').toLowerCase();

    if (key.includes('fin') || key.includes('limite') || key.includes('hasta') || key.includes('end') || label.includes('fin') || label.includes('límite') || label.includes('limite')) {
      const endVal = currFd[field.key];
      // Buscar campo de inicio relacionado
      const startField = activeNodeForm.value.fields.find((f: any) => {
        if (f.key === field.key || f.type !== 'date') return false;
        const fk = (f.key || '').toLowerCase();
        const fl = (f.label || '').toLowerCase();
        return fk.includes('ini') || fk.includes('desde') || fk.includes('start') || fl.includes('inicio') || fl.includes('desde');
      });
      if (startField) {
        const startVal = currFd[startField.key];
        if (startVal && endVal && endVal < startVal) {
          errors.push(`"${field.label}" no puede ser anterior a "${startField.label}"`);
        }
      }
    }
  }
  return errors;
});

const isStageReadyToApprove = computed(() => {
  if (activeNodeForm.value && missingStageFields.value.length > 0) return false;
  if (dateRangeErrors.value.length > 0) return false;
  if (activeNodeConsent.value && !stageConsentAccepted.value) return false;
  return true;
});

// ─── Transición de Workflow Regular ──────────────────────────────────────────
const handleWorkflowTransition = async (edge: any) => {
  if (!initiative.value) return;

  // Validación de requisitos de etapa pendientes antes de avanzar
  const isBorradorStage = (initiative.value.status || '').toLowerCase().includes('borrador') || currentNodeId.value === 'borrador';
  if (!isBorradorStage && canActOnCurrentStage.value) {
    const details: string[] = [];
    if (missingStageFields.value.length > 0) {
      details.push(`Campos obligatorios sin completar: ${missingStageFields.value.join(', ')}`);
    }
    if (dateRangeErrors.value.length > 0) {
      details.push(...dateRangeErrors.value);
    }
    if (details.length > 0) {
      showToast(
        'Para avanzar debes completar todos los requisitos de esta etapa.',
        'warning',
        {
          title: 'Requisitos de Etapa Pendientes',
          details,
          duration: 6000,
        }
      );
      return;
    }
  }

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
      showToast(
        'Por favor describe las correcciones realizadas o adjunta archivos de soporte en el panel de observación antes de avanzar.',
        'warning',
        { title: 'Subsanación Requerida' }
      );
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
      showToast(
        res.reason || 'Revisa los requisitos necesarios para avanzar a este estado.',
        'warning',
        { title: 'Acción No Permitida' }
      );
      return;
    }

    pendingEdgeTransition.value = {
      targetId,
      actionLabel: buttonLabel,
      targetLabel: targetNodeObj?.data?.label || targetId,
    };
    showConfirmModal.value = true;
  } catch (err: any) {
    showToast(err.message || 'Error al validar la transición.', 'error', { title: 'Error de Validación' });
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

    const currentFd = { ...(initiative.value.form_data || {}), ...stageFormData.value };
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

    if (activeNodeForm.value || activeNodeConsent.value) {
      try {
        await $fetch(`${apiBase}/initiatives/${id}/stage-record`, {
          method: 'POST',
          body: {
            node_id: currentNodeId.value,
            stage_name: currentNodeObj.value?.data?.label || initiative.value.status,
            form_id: activeNodeForm.value?.id || null,
            consent_id: activeNodeConsent.value?.id || null,
            form_data: stageFormData.value,
            consent_accepted: activeNodeConsent.value ? stageConsentAccepted.value : true,
            consent_text_snapshot: activeNodeConsent.value?.statement || null,
            action_taken: actionLabel,
            user_role: currentUser.value.roles[0] || (isAdmin.value ? 'Administrador' : 'BP TI'),
          },
        });
      } catch (recErr) {
        console.warn('Error recording stage custody:', recErr);
      }
    } else {
      await $fetch(`${apiBase}/initiatives/${id}/stage-record`, {
        method: 'POST',
        body: {
          node_id: currentNodeId.value || targetNodeId,
          stage_name: currentNodeObj.value?.data?.label || initiative.value.status,
          consent_accepted: consentAccepted.value,
          consent_text_snapshot: selectedConsent.value?.statement || null,
          action_taken: actionLabel,
          user_role: currentUser.value.roles[0] || (isAdmin.value ? 'Administrador' : 'BP TI'),
        },
      });
    }

    stageConsentAccepted.value = false;

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
    showToast(err.message || 'Error al actualizar la iniciativa.', 'error', { title: 'Error de Actualización' });
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
    showToast('¡Ficha técnica guardada exitosamente!', 'success', { title: 'Ficha Guardada' });
  } catch (err: any) {
    showToast(err.message || 'Error al guardar la ficha técnica.', 'error', { title: 'Error al Guardar' });
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
    showToast(err.message || 'Error al registrar observación.', 'error', { title: 'Error al Observar' });
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
    showToast(err.message || 'Error al subsanar observación.', 'error', { title: 'Error de Subsanación' });
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
    showToast(
      'Por favor describe las correcciones realizadas o adjunta archivos de soporte en el panel de observación antes de reenviar la iniciativa.',
      'warning',
      { title: 'Subsanación Requerida' }
    );
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
    showToast(err.message || 'Error al reubicar iniciativa.', 'error', { title: 'Error de Reubicación' });
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
    showToast(err.message || 'Error al desestimar iniciativa.', 'error', { title: 'Error al Desestimar' });
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
                {{ initiative.form_data?.vicepresidencia || 'Sin especificar' }}
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
                {{ initiative.form_data?.direccion || 'Sin especificar' }}
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
                {{ keyUserDisplay }}
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
              <p
                :class="[
                  'text-xs sm:text-[13px] font-bold leading-snug mt-0.5 break-words',
                  bpTiDisplay === 'Sin asignar' ? 'text-amber-600 font-medium' : 'text-[#EB5F46]'
                ]"
              >
                {{ bpTiDisplay }}
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
      </div>

      <!-- ── STEPPER HORIZONTAL CORPORATIVO (DINÁMICO SEGÚN MACRO-ETAPAS DEL FLUJO) ── -->
      <div class="bg-white p-5 sm:p-6 rounded-2xl border border-slate-100 shadow-[0_1px_3px_rgba(0,0,0,0.04)] overflow-x-auto">
        <div class="min-w-[760px] w-full">
          <div
            class="w-full relative"
            :style="{ display: 'grid', gridTemplateColumns: `repeat(${MACRO_STAGES.length}, minmax(0, 1fr))` }"
          >
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

              <!-- Botón Interactivo de la Etapa (Círculo + Textos) -->
              <button
                type="button"
                @click="handleSelectTimelineStage(stage.id)"
                class="relative z-10 flex flex-col items-center text-center cursor-pointer group focus:outline-none w-full"
                :title="`Ver información de la etapa: ${stage.name}`"
              >
                <!-- Círculo del Estado -->
                <div
                  :class="[
                    'w-8 h-8 sm:w-9 sm:h-9 rounded-full flex items-center justify-center transition-all duration-200 select-none group-hover:scale-105',
                    (getStageState(idx) === 'completed' || getStageState(idx) === 'active')
                      ? '!bg-[#059669] text-white shadow-xs'
                      : getStageState(idx) === 'observed'
                      ? '!bg-amber-500 text-white shadow-xs'
                      : getStageState(idx) === 'dismissed'
                      ? '!bg-rose-500 text-white shadow-xs'
                      : '!bg-white border-[1.5px] border-slate-300 text-slate-300 group-hover:border-indigo-400 group-hover:text-indigo-600',
                    selectedTimelineStageKey === stage.id
                      ? 'ring-4 ring-[#4F5AF5] ring-offset-2 ring-offset-white shadow-md scale-110 !border-[#4F5AF5]'
                      : getStageState(idx) === 'active'
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
                      'text-[11px] sm:text-xs block leading-tight transition-colors',
                      selectedTimelineStageKey === stage.id
                        ? 'text-[#4F5AF5] font-black underline'
                        : getStageState(idx) === 'active'
                        ? 'text-[#EB5F46] font-bold group-hover:text-[#EB5F46]/80'
                        : getStageState(idx) === 'completed'
                        ? 'text-slate-800 font-bold group-hover:text-[#4F5AF5]'
                        : getStageState(idx) === 'observed'
                        ? 'text-amber-700 font-bold'
                        : 'text-slate-400 font-medium group-hover:text-slate-600'
                    ]"
                  >
                    {{ stage.name }}
                  </span>
                  <span class="text-[10px] text-slate-400 block font-normal leading-tight">
                    {{ stage.role }}
                  </span>
                  <span
                    v-if="selectedTimelineStageKey === stage.id"
                    class="inline-block mt-0.5 px-1.5 py-0.5 rounded-full text-[9px] font-extrabold bg-indigo-50 text-[#4F5AF5] border border-indigo-200"
                  >
                    Viendo etapa
                  </span>
                </div>
              </button>

              <!-- Sub-pasos interactivos (para etapas con sub-estados) -->
              <div v-if="getStageVisibleSubNodes(stage.id).length > 0" class="relative inline-block pt-1 z-20">
                <button
                  type="button"
                  @click.stop="toggleSubstepper(stage.id)"
                  :class="[
                    'text-[10px] font-bold px-2 py-0.5 rounded-md inline-flex items-center gap-1 transition-all cursor-pointer',
                    openSubstepperStageId === stage.id
                      ? 'bg-[#FFF5F2] text-[#EB5F46] border border-[#FDBA74] shadow-xs'
                      : 'text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200'
                  ]"
                  :title="openSubstepperStageId === stage.id ? 'Plegar sub-estados' : 'Desplegar sub-estados'"
                >
                  <span>{{ getStageVisibleSubNodes(stage.id).length }} {{ getStageVisibleSubNodes(stage.id).length === 1 ? 'paso' : 'pasos' }}</span>
                  <ChevronDown class="w-3 h-3 transition-transform duration-200" :class="openSubstepperStageId === stage.id ? 'rotate-180 text-[#EB5F46]' : ''" />
                </button>
              </div>
            </div>
          </div>

          <!-- ── BANDEJA EXPANDIBLE DE SUB-ESTADOS (IDÉNTICA A IMAGEN 2) ── -->
          <div 
            :class="[
              'grid transition-[grid-template-rows,opacity,margin,padding] duration-500 ease-[cubic-bezier(0.16,1,0.3,1)]',
              openSubstepperStageId && openSubstepperVisibleSubNodes.length > 0
                ? 'grid-rows-[1fr] opacity-100 mt-4 pt-3.5 border-t border-slate-100' 
                : 'grid-rows-[0fr] opacity-0 mt-0 pt-0 border-t-0 pointer-events-none'
            ]"
          >
            <div class="overflow-hidden">
              <div :class="[
                'transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)]',
                openSubstepperStageId ? 'translate-y-0 opacity-100' : '-translate-y-2 opacity-0'
              ]">
                <!-- Barra de cabecera ligera y minimalista -->
                <div class="flex items-center justify-between gap-3 mb-3 px-1">
                  <div class="flex items-center gap-2">
                    <div class="w-5 h-5 rounded-md bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shrink-0">
                      <Layers class="w-3 h-3" />
                    </div>
                    <span class="text-xs font-black text-slate-800 tracking-tight">
                      Sub-estados de {{ openSubstepperStage?.name }}
                    </span>
                    <span class="text-[10px] text-slate-400 font-medium hidden sm:inline">
                      ({{ openSubstepperVisibleSubNodes.length }} pasos)
                    </span>
                  </div>

                  <span class="text-[10px] text-slate-400 font-medium italic">
                    Clic en la tarea padre para plegar
                  </span>
                </div>

                <!-- Riel horizontal con circulitos idénticos -->
                <div class="overflow-x-auto pb-1 pt-1">
                  <div class="flex items-start w-full min-w-[560px] relative px-2">
                    <div
                      v-for="(sub, sIdx) in openSubstepperVisibleSubNodes"
                      :key="sub.id"
                      class="flex-1 relative flex flex-col items-center"
                    >
                      <!-- Conector acotado entre circulitos — ¡NO sobresale del último circulito! -->
                      <div
                        v-if="sIdx < openSubstepperVisibleSubNodes.length - 1"
                        :class="[
                          'absolute top-[16px] left-1/2 w-full h-[2.5px] -translate-y-1/2 z-0 transition-all duration-500 ease-out',
                          isSubNodeCompleted(sub.id, sub.label) ? 'bg-emerald-500' : 'bg-slate-200'
                        ]"
                      ></div>

                      <button
                        type="button"
                        @click="handleSelectSubNode(openSubstepperStageId!, sub.id)"
                        class="flex flex-col items-center relative z-10 w-full px-1 group cursor-pointer focus:outline-none transition-all"
                        :title="`Inspeccionar dictamen de ${sub.label} (${sub.role})`"
                      >
                        <!-- Circulito idéntico al macro stepper -->
                        <div
                          :class="[
                            'w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ease-out group-hover:scale-105',
                            selectedSubNodeId === sub.id && selectedTimelineStageKey === openSubstepperStageId
                              ? 'ring-4 ring-indigo-200 shadow-md bg-indigo-600 text-white'
                              : isSubNodeCompleted(sub.id, sub.label)
                              ? 'bg-emerald-600 text-white shadow-xs ring-2 ring-emerald-50'
                              : isSubNodeActive(sub.id)
                              ? 'bg-indigo-600 text-white ring-4 ring-indigo-100 shadow-sm animate-pulse'
                              : 'bg-white text-slate-400 border-2 border-slate-300 group-hover:border-indigo-400 group-hover:text-indigo-600'
                          ]"
                        >
                          <Check v-if="isSubNodeCompleted(sub.id, sub.label)" class="w-4 h-4 stroke-[3]" />
                          <Clock v-else-if="isSubNodeActive(sub.id)" class="w-4 h-4" />
                          <span v-else>{{ sIdx + 1 }}</span>
                        </div>

                        <!-- Nombre del sub-estado -->
                        <span
                          :class="[
                            'text-[11px] font-bold mt-1.5 text-center leading-tight transition-colors px-1',
                            selectedSubNodeId === sub.id && selectedTimelineStageKey === openSubstepperStageId
                              ? 'text-indigo-600 font-black'
                              : isSubNodeCompleted(sub.id, sub.label)
                              ? 'text-slate-800 group-hover:text-indigo-600'
                              : isSubNodeActive(sub.id)
                              ? 'text-indigo-900 font-black'
                              : 'text-slate-400 group-hover:text-slate-600'
                          ]"
                        >
                          {{ sub.label }}
                        </span>

                        <!-- Rol responsable -->
                        <span class="text-[10px] text-slate-400 font-medium text-center mt-0.5 leading-tight">
                          {{ sub.role }}
                        </span>

                        <!-- Indicador de seleccionado -->
                        <span
                          :class="[
                            'mt-1.5 w-4 h-1 rounded-full transition-all duration-300',
                            selectedSubNodeId === sub.id && selectedTimelineStageKey === openSubstepperStageId
                              ? 'bg-indigo-600'
                              : 'bg-transparent'
                          ]"
                        ></span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── GRID PRINCIPAL: 2 COLUMNAS (CONTENIDO + FICHA LATERAL STICKY) ── -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <!-- Columna Izquierda: Pestañas y Contenido (7 cols en lg, 8 en xl) -->
        <div class="lg:col-span-7 xl:col-span-8 space-y-6">
          <!-- ── BARRA DE PESTAÑAS (IDÉNTICA A IMÁGENES 2, 3 Y 4) ── -->
          <div class="flex items-center gap-1.5 p-1.5 bg-slate-100/90 rounded-2xl border border-slate-200/90 w-full sm:w-fit overflow-x-auto shadow-2xs">
            <!-- Pestaña 1: Información de la Necesidad -->
            <button
              type="button"
              @click="activeDetailTab = 'info'; selectedTimelineStageKey = null"
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
          <!-- Si se hizo clic en un círculo del stepper y estamos en Tab Info: mostrar Detalle de Etapa -->
          <InitiativeStageDetailView
            v-if="selectedTimelineStage && activeDetailTab === 'info'"
            :stage="selectedTimelineStage"
            :stage-index="selectedTimelineStageIndex"
            :stage-records="selectedTimelineStageRecords"
            :current-stage-index="currentStageIndex"
            :is-end-workflow="isDismissed"
            :initiative="initiative"
            :selected-sub-node-id="selectedSubNodeId"
            @close="selectedTimelineStageKey = null; selectedSubNodeId = null"
            @clear-subnode="selectedSubNodeId = null"
          />

          <!-- TAB 1: Información de la Necesidad (Imagen 2) -->
          <InitiativeInfoTab
            v-else-if="activeDetailTab === 'info'"
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

        <!-- Columna Derecha: Ficha de Dictamen & Consentimiento de Etapa (Sticky en Desktop) -->
        <div class="lg:col-span-5 xl:col-span-4 lg:sticky lg:top-6 space-y-5">
          <InitiativeStageDecisionPanel
            :initiative="initiative"
            :current-node="currentNodeObj"
            :active-node-form="activeNodeForm"
            :active-node-consent="activeNodeConsent"
            :can-act-on-current-stage="canActOnCurrentStage"
            :stage-form-data="stageFormData"
            :stage-consent-accepted="stageConsentAccepted"
            :is-stage-ready-to-approve="isStageReadyToApprove"
            :missing-stage-fields="missingStageFields"
            :eligible-role-users-map="eligibleRoleUsersMap"
            :stage-records="stageRecords || []"
            :next-approvers-list="nextApproversList"
            :should-show-next-approvers="showNextApproversCard"
            :next-approvers-title="nextApproversData?.title"
            :is-submitting="isSubmitting"
            :forward-edges="forwardEdges"
            @update:field="handleStageFieldChange"
            @update:consent="stageConsentAccepted = $event"
            @execute-transition="handleWorkflowTransition"
            @notify="showToast($event.message, $event.type || 'info', { title: $event.title })"
          />
        </div>
      </div>
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

    <!-- ── Toast Notificación Flotante Institucional (UX Premium) ── -->
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="transform translate-y-4 opacity-0 scale-95"
      enter-to-class="transform translate-y-0 opacity-100 scale-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="transform translate-y-0 opacity-100 scale-100"
      leave-to-class="transform translate-y-4 opacity-0 scale-95"
    >
      <div
        v-if="toast"
        class="fixed bottom-6 right-6 z-[9999] max-w-md w-full shadow-2xl rounded-2xl border p-4 pointer-events-auto backdrop-blur-md"
        :class="[
          toast.type === 'success' ? 'bg-[#064E3B]/95 text-emerald-50 border-emerald-500/40 shadow-emerald-500/20' :
          toast.type === 'warning' ? 'bg-[#78350F]/95 text-amber-50 border-amber-500/40 shadow-amber-500/20' :
          toast.type === 'error' ? 'bg-[#881337]/95 text-rose-50 border-rose-500/40 shadow-rose-500/20' :
          'bg-slate-900/95 text-white border-slate-700 shadow-slate-900/30'
        ]"
      >
        <div class="flex items-start gap-3">
          <div class="shrink-0 mt-0.5">
            <CheckCircle v-if="toast.type === 'success'" class="w-5 h-5 text-emerald-400" />
            <AlertTriangle v-else-if="toast.type === 'warning'" class="w-5 h-5 text-amber-400" />
            <AlertCircle v-else class="w-5 h-5 text-rose-400" />
          </div>
          <div class="flex-1 min-w-0 space-y-1">
            <h4 v-if="toast.title" class="text-xs font-bold uppercase tracking-wider">
              {{ toast.title }}
            </h4>
            <p class="text-xs leading-relaxed font-medium">
              {{ toast.message }}
            </p>
            <ul v-if="toast.details && toast.details.length > 0" class="mt-1 space-y-0.5 text-[11px] opacity-90 list-disc list-inside">
              <li v-for="(item, idx) in toast.details" :key="idx">
                {{ item }}
              </li>
            </ul>
          </div>
          <button
            type="button"
            @click="closeToast"
            class="shrink-0 text-white/60 hover:text-white p-1 rounded-lg transition-colors cursor-pointer"
          >
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>
    </Transition>

    <!-- Modal de Confirmación de Transición de Estado -->
    <CommonTransitionConfirmationModal
      :is-open="showConfirmModal"
      title="¿Estás seguro de la acción que estás realizando?"
      :action-label="pendingEdgeTransition?.actionLabel || 'Avanzar'"
      :current-state="initiative?.status || 'Estado actual'"
      :target-state="pendingEdgeTransition?.targetLabel || 'Siguiente estado'"
      :initiative-title="initiative?.summary?.titulo || initiative?.form_data?.titulo || initiative?.id || ''"
      :consent-title="activeNodeConsent?.title"
      :consent-statement="activeNodeConsent?.statement"
      :consent-accepted="stageConsentAccepted"
      :is-submitting="isSubmitting"
      confirm-text="Aceptar"
      cancel-text="Regresar"
      @update:consent="stageConsentAccepted = $event"
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
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-full bg-white border border-slate-200 overflow-hidden flex items-center justify-center text-[#EB5F46] shrink-0 shadow-xs">
              <img v-if="aiAvatar" :src="aiAvatar" :alt="aiName || 'Teo'" class="w-full h-full object-cover" />
              <Bot v-else class="w-4 h-4 text-[#EB5F46]" />
            </div>
            <div>
              <h3 class="font-bold text-slate-900 text-sm">Conversación Cronológica con {{ aiName || 'Teo' }}</h3>
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
                v-if="msg.role === 'user'"
                class="w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 bg-slate-900 text-white shadow-2xs"
              >
                YO
              </div>
              <div
                v-else
                class="w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 bg-white border border-slate-200 overflow-hidden shadow-2xs"
              >
                <img v-if="aiAvatar" :src="aiAvatar" :alt="aiName || 'Teo'" class="w-full h-full object-cover" />
                <Bot v-else class="w-4 h-4 text-[#EB5F46]" />
              </div>
              <div
                :class="[
                  'p-3.5 rounded-2xl text-xs leading-relaxed max-w-[85%]',
                  msg.role === 'user'
                    ? 'bg-slate-900 text-white rounded-tr-none'
                    : 'bg-slate-50 border border-slate-200 text-slate-800 rounded-tl-none shadow-2xs'
                ]"
              >
                <div
                  :class="[
                    'text-[9px] uppercase font-bold tracking-wider mb-1',
                    msg.role === 'user' ? 'text-slate-300' : 'text-slate-400'
                  ]"
                >
                  {{ msg.role === 'user' ? 'Solicitante' : (aiName || 'Teo') + ' (Asesor IA)' }}
                </div>
                <div
                  v-if="msg.role === 'user'"
                  class="leading-relaxed text-white break-words [&_p]:text-white [&_strong]:text-white [&_strong]:font-bold [&_li]:text-white"
                  v-html="formatMarkdownToHtml(msg.text, { isDark: true })"
                />
                <div
                  v-else
                  class="leading-relaxed text-slate-800 break-words"
                  v-html="formatMarkdownToHtml(msg.text)"
                />
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
