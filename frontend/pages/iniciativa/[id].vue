<script setup lang="ts">
import { ref, computed } from 'vue';
import {
  ArrowLeft, CheckCircle, AlertTriangle, Ban, FileText,
  MessageSquare, Sparkles, Building2, User, ShieldCheck,
  Calendar, Check, X, FileCheck2, Clock, Send, ArrowRight
} from 'lucide-vue-next';
import type { Initiative, InitiativeStageRecord, StageConsent, WorkflowTransitionResult } from '~/types';

const route = useRoute();
const id = route.params.id as string;
const config = useRuntimeConfig();
const apiBase = config.public.apiBase;

import InstitutionalLoader from '~/components/common/InstitutionalLoader.vue';

// ─── Tabs State ──────────────────────────────────────────────────────────────
const activeDetailTab = ref<'info' | 'history' | 'observations'>('info');

// ─── Cargar Iniciativa ───────────────────────────────────────────────────────
const { data: initiative, pending, refresh } = await useFetch<Initiative>(`${apiBase}/initiatives/${id}`);

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

const currentNodeId = computed(() => {
  if (!initiative.value) return 'borrador';
  return initiative.value.current_node_id || STATUS_TO_NODE[initiative.value.status] || 'borrador';
});

// ─── Aristas Salientes del Nodo Actual ───────────────────────────────────────
const outgoingEdges = computed(() => {
  if (!activeWorkflow.value?.graph_json?.edges || !initiative.value) return [];
  const currId = currentNodeId.value;
  return activeWorkflow.value.graph_json.edges.filter((e: any) => e.source === currId);
});

const canUserExecuteEdge = (edge: any) => {
  if (isAdmin.value) return true;
  const edgeData = edge.data || {};
  const condCfg = edge.condition_config || {};
  const allowed = edgeData.allowed_roles || edge.allowed_roles || condCfg.allowed_roles;
  if (Array.isArray(allowed) && allowed.length > 0) {
    return allowed.some((r: string) => userRolesList.value.includes(r.toLowerCase()));
  }
  return true;
};

const userOutgoingEdges = computed(() => {
  return outgoingEdges.value.filter((edge: any) => canUserExecuteEdge(edge));
});

// ─── Helpers Visuales de Botones de Transición ──────────────────────────────
const getEdgeButtonLabel = (edge: any) => {
  if (edge.label && edge.label.trim()) return edge.label.trim();
  const targetNode = activeWorkflow.value?.graph_json?.nodes?.find((n: any) => n.id === edge.target);
  return targetNode?.data?.action_label || targetNode?.data?.label || 'Avanzar';
};

const hasCustomEdgeColor = (edge: any) => {
  const style = edge.data?.style_config || {};
  return Boolean(style.button_bg || style.button_color);
};

const getEdgeButtonStyle = (edge: any) => {
  const style = edge.data?.style_config || {};
  const hasCustom = Boolean(style.button_bg || style.button_color || style.label_color);
  if (!hasCustom) return {};
  return {
    backgroundColor: style.button_bg || style.button_color,
    borderColor: style.button_color || 'transparent',
    color: style.label_color || '#ffffff',
  };
};

const getEdgeButtonDefaultClass = (edge: any) => {
  const targetNode = activeWorkflow.value?.graph_json?.nodes?.find((n: any) => n.id === edge.target);
  const isObs = edge.target === 'observada' || targetNode?.data?.stateSubtype === 'observada' || /observa/i.test(edge.label || '');
  const isDes = edge.target === 'desestimada' || targetNode?.data?.stateSubtype === 'desestimada' || /desestima/i.test(edge.label || '');
  const isAprob = edge.target === 'planificacion' || targetNode?.data?.stateSubtype === 'demanda' || /aproba|vobo/i.test(edge.label || '');

  if (isDes) return 'bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100';
  if (isObs) return 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100';
  if (isAprob) return 'bg-emerald-600 hover:bg-emerald-700 text-white border-emerald-600 shadow-emerald-500/20';
  return 'bg-[#4F5AF5] hover:bg-[#3F49E0] text-white border-transparent shadow-[#4F5AF5]/20';
};

const getEdgeButtonIcon = (edge: any) => {
  const targetNode = activeWorkflow.value?.graph_json?.nodes?.find((n: any) => n.id === edge.target);
  const isObs = edge.target === 'observada' || targetNode?.data?.stateSubtype === 'observada' || /observa/i.test(edge.label || '');
  const isDes = edge.target === 'desestimada' || targetNode?.data?.stateSubtype === 'desestimada' || /desestima/i.test(edge.label || '');
  const isAprob = edge.target === 'planificacion' || targetNode?.data?.stateSubtype === 'demanda' || /aproba|vobo/i.test(edge.label || '');

  if (isDes) return Ban;
  if (isObs) return AlertTriangle;
  if (isAprob) return CheckCircle;
  return Send;
};

// ─── Modal de Consentimiento ─────────────────────────────────────────────────
const showConsentModal = ref(false);
const selectedConsent = ref<StageConsent | null>(null);
const consentAccepted = ref(false);
const isSubmitting = ref(false);
const pendingTransition = ref<{ targetId: string; actionLabel: string } | null>(null);

const getStatusBadgeClass = (status: string) => {
  const s = (status || '').toLowerCase();
  if (s.includes('pendiente')) return 'bg-indigo-50 text-[#4F5AF5] border-indigo-200';
  if (s.includes('observad')) return 'bg-amber-50 text-amber-700 border-amber-200';
  if (s.includes('demanda')) return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  if (s.includes('desestimad')) return 'bg-rose-50 text-rose-700 border-rose-200';
  return 'bg-slate-100 text-slate-700 border-slate-200';
};

const handleWorkflowTransition = async (edge: any) => {
  if (!initiative.value) return;

  let targetId = edge.target;
  let targetNodeObj = activeWorkflow.value?.graph_json?.nodes?.find((n: any) => n.id === targetId);
  const buttonLabel = getEdgeButtonLabel(edge);

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

  // Validar requisitos y transición en backend
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

    if (targetNodeObj?.data?.consent_id || buttonLabel.toLowerCase().includes('aprobar') || buttonLabel.toLowerCase().includes('vobo')) {
      selectedConsent.value = {
        id: targetNodeObj?.data?.consent_id || 'DICTAMEN_TECNICO_BP',
        code: 'DICTAMEN_TECNICO_BP',
        title: 'Dictamen Técnico de Factibilidad y Arquitectura',
        statement: 'Declaro que he evaluado los requerimientos técnicos y certifico la viabilidad de la iniciativa.',
        version: 1,
        is_active: true,
      };
      pendingTransition.value = { targetId, actionLabel: buttonLabel };
      showConsentModal.value = true;
      return;
    }

    await applyStateUpdate(targetId, buttonLabel);
  } catch (err: any) {
    alert('Error al validar transición: ' + (err.message || err));
  }
};

const handleTransition = async (actionLabel: string, targetNodeId: string) => {
  if (!initiative.value) return;

  try {
    const res: WorkflowTransitionResult = await $fetch(`${apiBase}/workflow/validate-transition`, {
      params: {
        currentNodeId: currentNodeId.value,
        targetNodeId: targetNodeId,
        userRole: userRolesList.value[0] || 'admin',
        transitionLabel: actionLabel,
      },
    });

    if (!res.allowed) {
      alert(`Acción no permitida: ${res.reason || 'Revisa los requisitos'}`);
      return;
    }

    if (actionLabel.toLowerCase().includes('aprobar')) {
      selectedConsent.value = {
        id: 'DICTAMEN_TECNICO_BP',
        code: 'DICTAMEN_TECNICO_BP',
        title: 'Dictamen Técnico de Factibilidad y Arquitectura',
        statement: 'Declaro que he evaluado los requerimientos técnicos y certifico la viabilidad de la iniciativa.',
        version: 1,
        is_active: true,
      };
      pendingTransition.value = { targetId: targetNodeId, actionLabel };
      showConsentModal.value = true;
      return;
    }

    await applyStateUpdate(targetNodeId, actionLabel);
  } catch (err: any) {
    alert('Error al validar transición: ' + (err.message || err));
  }
};

const applyStateUpdate = async (targetNodeId: string, actionLabel: string) => {
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

    await $fetch(`${apiBase}/initiatives/${id}`, {
      method: 'PATCH',
      body: {
        status: nextStatus,
        current_node_id: targetNodeId,
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
    alert(`Iniciativa actualizada a estado: ${nextStatus}`);
  } catch (err: any) {
    alert('Error al actualizar iniciativa: ' + (err.message || err));
  } finally {
    isSubmitting.value = false;
  }
};

function formatDate(iso: string) {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
  } catch {
    return iso;
  }
}
</script>

<template>
  <div class="max-w-6xl mx-auto space-y-6 pb-16">
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
      <!-- ── Encabezado Principal del Expediente ── -->
      <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="space-y-1.5 min-w-0 flex-1">
          <div class="flex items-center gap-2.5 flex-wrap">
            <NuxtLink
              to="/dashboard"
              class="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-slate-900 border border-slate-200 px-2.5 py-1 rounded-lg"
            >
              <ArrowLeft class="w-3.5 h-3.5" /> Volver
            </NuxtLink>
            <span class="text-xs font-mono font-semibold text-[#4F5AF5] bg-[#EEF2FF] px-2.5 py-0.5 rounded-md">
              #{{ initiative.summary?.id_corta || initiative.id.slice(0, 8) }}
            </span>
            <span :class="['px-3 py-0.5 rounded-full text-xs font-bold border', getStatusBadgeClass(initiative.status)]">
              {{ initiative.status }}
            </span>
          </div>

          <h1 class="text-2xl font-bold text-slate-900 tracking-tight leading-snug">
            {{ initiative.summary?.titulo || initiative.form_data?.titulo || initiative.id }}
          </h1>

          <p class="text-xs text-slate-500">
            {{ initiative.form_data?.institucion || 'UPC' }} · {{ initiative.form_data?.vicepresidencia || 'Sin VP' }} · {{ initiative.form_data?.direccion || 'Sin Dirección' }}
          </p>
        </div>

        <!-- Acciones del Flujo de Trabajo (Transiciones Dinámicas y Personalizadas) -->
        <div class="flex flex-wrap items-center gap-2 shrink-0">
          <template v-if="userOutgoingEdges.length > 0">
            <button
              v-for="edge in userOutgoingEdges"
              :key="edge.id"
              @click="handleWorkflowTransition(edge)"
              :style="getEdgeButtonStyle(edge)"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all shadow-sm cursor-pointer border',
                !hasCustomEdgeColor(edge) ? getEdgeButtonDefaultClass(edge) : 'hover:opacity-90 shadow-md'
              ]"
              :title="`Transición a ${edge.target}`"
            >
              <component :is="getEdgeButtonIcon(edge)" class="w-3.5 h-3.5 shrink-0" />
              <span>{{ getEdgeButtonLabel(edge) }}</span>
            </button>
          </template>

          <!-- Fallback si el workflow activo aún no tiene aristas desde este estado -->
          <template v-else>
            <button
              v-if="initiative.status === 'Borrador'"
              @click="handleTransition('Enviar a Revisión', 'eval_bp')"
              class="px-4 py-2 text-xs font-semibold text-white bg-[#4F5AF5] hover:bg-[#3F49E0] rounded-xl transition-colors shadow-sm"
            >
              Enviar a Revisión
            </button>

            <template v-if="initiative.status === 'Pendiente de aprobación'">
              <button
                @click="handleTransition('Aprobar (VoBo)', 'planificacion')"
                class="px-4 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl transition-colors shadow-sm flex items-center gap-1.5"
              >
                <CheckCircle class="w-4 h-4" />
                <span>Aprobar (VoBo Demanda)</span>
              </button>
              <button
                @click="handleTransition('Observar', 'observada')"
                class="px-4 py-2 text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-200 rounded-xl hover:bg-amber-100 transition-colors"
              >
                Observar
              </button>
              <button
                @click="handleTransition('Desestimar', 'desestimada')"
                class="px-4 py-2 text-xs font-semibold text-rose-700 bg-rose-50 border border-rose-200 rounded-xl hover:bg-rose-100 transition-colors"
              >
                Desestimar
              </button>
            </template>

            <button
              v-if="initiative.status === 'Observada'"
              @click="handleTransition('Subsanar Observación', 'eval_bp')"
              class="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-colors"
            >
              Subsanar Observación
            </button>
          </template>
        </div>
      </div>

      <!-- ── 3 Pestañas Corporativas (Ficha Técnica | Historial con Teo | Observaciones) ── -->
      <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-1.5 flex items-center gap-2">
        <button
          type="button"
          @click="activeDetailTab = 'info'"
          :class="[
            'flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer',
            activeDetailTab === 'info'
              ? 'bg-[#4F5AF5] text-white shadow-sm'
              : 'text-slate-600 hover:text-[#4F5AF5] hover:bg-slate-50'
          ]"
        >
          <FileText class="w-4 h-4" />
          Ficha Técnica
        </button>

        <button
          type="button"
          @click="activeDetailTab = 'history'"
          :class="[
            'flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer',
            activeDetailTab === 'history'
              ? 'bg-[#4F5AF5] text-white shadow-sm'
              : 'text-slate-600 hover:text-[#4F5AF5] hover:bg-slate-50'
          ]"
        >
          <MessageSquare class="w-4 h-4" />
          Historial de Levantamiento con Teo
          <span v-if="initiative.chat_history?.length" class="text-[10px] px-1.5 py-0.2 rounded-full font-bold bg-white/20">
            {{ initiative.chat_history.length }}
          </span>
        </button>

        <button
          type="button"
          @click="activeDetailTab = 'observations'"
          :class="[
            'flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer',
            activeDetailTab === 'observations'
              ? 'bg-[#4F5AF5] text-white shadow-sm'
              : 'text-slate-600 hover:text-[#4F5AF5] hover:bg-slate-50'
          ]"
        >
          <Clock class="w-4 h-4" />
          Cadena de Custodia & Dictámenes
          <span v-if="stageRecords?.length" class="text-[10px] px-1.5 py-0.2 rounded-full font-bold bg-white/20">
            {{ stageRecords.length }}
          </span>
        </button>
      </div>

      <!-- ── Tab 1: Ficha Técnica ── -->
      <div v-if="activeDetailTab === 'info'" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Columna Izquierda: Datos y Resumen Ejecutivo -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Resumen Ejecutivo IA -->
          <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 class="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-2.5">
              <Sparkles class="w-4 h-4 text-[#4F5AF5]" />
              Resumen Ejecutivo IA (Teo)
            </h3>

            <div class="space-y-3.5">
              <div class="bg-[#F8FAFF] border border-[#EEF2FF] p-4 rounded-xl space-y-1">
                <span class="text-[10px] font-bold text-[#4F5AF5] uppercase tracking-wider">Objetivo</span>
                <p class="text-sm text-slate-800 leading-relaxed font-medium">
                  {{ initiative.summary?.objetivo || initiative.form_data?.objetivo || 'Sin objetivo especificado' }}
                </p>
              </div>

              <div class="bg-[#FFFBF5] border border-amber-100 p-4 rounded-xl space-y-1">
                <span class="text-[10px] font-bold text-amber-700 uppercase tracking-wider">Problema que Resuelve</span>
                <p class="text-sm text-slate-800 leading-relaxed">
                  {{ initiative.summary?.descripcionProblema || initiative.form_data?.descripcion_de_la_necesidad || 'Sin descripción' }}
                </p>
              </div>

              <div class="grid grid-cols-2 gap-3 pt-2">
                <div class="bg-slate-50 p-3 rounded-xl border border-slate-200 text-center">
                  <span class="text-[10px] font-semibold text-slate-400 uppercase">Complejidad Estimada</span>
                  <p class="text-sm font-bold text-slate-800 mt-0.5">{{ initiative.summary?.complejidad || 'Media' }}</p>
                </div>
                <div class="bg-slate-50 p-3 rounded-xl border border-slate-200 text-center">
                  <span class="text-[10px] font-semibold text-slate-400 uppercase">Riesgo Operativo</span>
                  <p class="text-sm font-bold text-slate-800 mt-0.5">{{ initiative.summary?.riesgo || 'Bajo' }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Estructura Organizacional -->
          <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 class="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-2.5">
              <Building2 class="w-4 h-4 text-slate-500" />
              Estructura Organizacional & Solicitante
            </h3>

            <div class="grid grid-cols-2 gap-4 text-xs">
              <div class="p-3 bg-slate-50 rounded-xl">
                <span class="text-slate-400 block text-[10px] uppercase font-bold">Institución</span>
                <p class="text-slate-800 font-semibold text-sm mt-0.5">{{ initiative.form_data?.institucion || 'UPC' }}</p>
              </div>
              <div class="p-3 bg-slate-50 rounded-xl">
                <span class="text-slate-400 block text-[10px] uppercase font-bold">Key User / Solicitante</span>
                <p class="text-slate-800 font-semibold text-sm mt-0.5">{{ initiative.form_data?.registrador || 'Administrador' }}</p>
              </div>
              <div class="p-3 bg-slate-50 rounded-xl">
                <span class="text-slate-400 block text-[10px] uppercase font-bold">Vicepresidencia</span>
                <p class="text-slate-800 font-semibold text-sm mt-0.5">{{ initiative.form_data?.vicepresidencia || '—' }}</p>
              </div>
              <div class="p-3 bg-slate-50 rounded-xl">
                <span class="text-slate-400 block text-[10px] uppercase font-bold">Dirección</span>
                <p class="text-slate-800 font-semibold text-sm mt-0.5">{{ initiative.form_data?.direccion || '—' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Columna Derecha: Gobernanza y Asignaciones TI -->
        <div class="space-y-6">
          <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 class="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-2.5">
              <ShieldCheck class="w-4 h-4 text-[#4F5AF5]" />
              Gobernanza TI Laureate
            </h3>

            <div class="space-y-3">
              <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Business Partner TI (BP TI)</span>
                <p :class="['text-sm font-bold mt-1', initiative.form_data?.bp_ti_asignado ? 'text-slate-800' : 'text-amber-600']">
                  {{ initiative.form_data?.bp_ti_asignado || 'Pendiente de Asignación' }}
                </p>
              </div>

              <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Líder de Dominio (LD)</span>
                <p :class="['text-sm font-bold mt-1', initiative.form_data?.lider_de_dominio_responsable ? 'text-indigo-700' : 'text-slate-400 italic']">
                  {{ initiative.form_data?.lider_de_dominio_responsable || 'Sin Asignar (Etapa de Demanda)' }}
                </p>
              </div>

              <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Fecha de Registro</span>
                <p class="text-sm font-semibold text-slate-800 mt-1">{{ formatDate(initiative.created_at) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Tab 2: Historial de Levantamiento con Teo ── -->
      <div v-else-if="activeDetailTab === 'history'" class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <h3 class="text-sm font-bold text-slate-800 uppercase tracking-wider border-b border-slate-100 pb-2.5 flex items-center gap-2">
          <MessageSquare class="w-4 h-4 text-[#4F5AF5]" />
          Conversación Cronológica con Teo (Asistente Cognitivo)
        </h3>

        <div v-if="!initiative.chat_history || initiative.chat_history.length === 0" class="py-12 text-center text-slate-400 text-sm">
          No hay transcripción de chat registrada para esta iniciativa.
        </div>

        <div v-else class="space-y-4 max-h-[600px] overflow-y-auto pr-2">
          <div
            v-for="(msg, idx) in initiative.chat_history"
            :key="idx"
            :class="['flex items-start gap-3 max-w-[85%]', msg.role === 'user' ? 'ml-auto flex-row-reverse' : '']"
          >
            <div
              :class="[
                'w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0',
                msg.role === 'user' ? 'bg-slate-900 text-white' : 'bg-[#FFF0ED] text-[#EB5F46] border border-[#FCD9D2]'
              ]"
            >
              {{ msg.role === 'user' ? 'YO' : 'TEO' }}
            </div>
            <div
              :class="[
                'p-4 rounded-2xl text-xs sm:text-sm leading-relaxed',
                msg.role === 'user'
                  ? 'bg-slate-900 text-white rounded-tr-none'
                  : 'bg-slate-50 border border-slate-200 text-slate-800 rounded-tl-none'
              ]"
            >
              <div class="text-[10px] uppercase font-bold tracking-wider mb-1 opacity-70">
                {{ msg.role === 'user' ? 'Solicitante' : 'Teo (Vertex AI)' }}
              </div>
              <p class="whitespace-pre-line">{{ msg.text }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Tab 3: Cadena de Custodia & Dictámenes ── -->
      <div v-else-if="activeDetailTab === 'observations'" class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <h3 class="text-sm font-bold text-slate-800 uppercase tracking-wider border-b border-slate-100 pb-2.5 flex items-center gap-2">
          <FileCheck2 class="w-4 h-4 text-[#4F5AF5]" />
          Cadena de Custodia y Dictámenes Formales
        </h3>

        <div v-if="!stageRecords || stageRecords.length === 0" class="py-12 text-center text-slate-400 text-sm">
          Aún no se registran firmas, dictámenes o consentimientos formalizados en el flujo.
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="rec in stageRecords"
            :key="rec.id"
            class="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2"
          >
            <div class="flex items-center justify-between">
              <span class="text-sm font-bold text-slate-900 flex items-center gap-2">
                <CheckCircle class="w-4 h-4 text-emerald-600" />
                {{ rec.stage_name }}
              </span>
              <span class="text-xs font-mono text-slate-400">{{ formatDate(rec.submitted_at) }}</span>
            </div>
            <p class="text-xs text-slate-600">
              Acción: <strong>{{ rec.action_taken || 'Aprobado' }}</strong> por <strong>{{ rec.user_name || 'Usuario' }}</strong> ({{ rec.user_role }})
            </p>
            <div v-if="rec.consent_text_snapshot" class="p-3 bg-white border border-slate-200 rounded-xl text-xs text-slate-700 italic">
              "{{ rec.consent_text_snapshot }}"
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal de Consentimiento y Firma Electrónica -->
    <div
      v-if="showConsentModal && selectedConsent"
      class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4"
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
            class="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
          >
            Cancelar
          </button>
          <button
            @click="applyStateUpdate(pendingTransition?.targetId || 'planificacion', pendingTransition?.actionLabel || 'Aprobar (VoBo)')"
            :disabled="!consentAccepted || isSubmitting"
            class="px-5 py-2 text-xs font-semibold text-white bg-[#4F5AF5] hover:bg-[#3F49E0] rounded-xl disabled:opacity-50 transition-colors shadow-sm"
          >
            {{ pendingTransition?.actionLabel ? `Firmar: ${pendingTransition.actionLabel}` : 'Firmar y Pasar a Demanda' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
