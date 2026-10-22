<template>
  <div class="h-[calc(100vh-4rem)] flex flex-col overflow-hidden bg-slate-100">
    <!-- Top Bar: Status, Auto-save indicator, Undo/Redo, Macro-Etapas, Favoritas & Guardar/Publicar -->
    <WorkflowVersionBar
      :workflow-name="workflow?.name || 'Flujo Oficial de Gestión de la Demanda'"
      :version="workflow?.version || 2"
      :status="workflow?.status || 'published'"
      :is-dirty="isDirty"
      :is-saving="isSaving"
      :can-undo="historyIndex > 0"
      :can-redo="historyIndex < history.length - 1"
      @save-and-publish="saveAndPublishWorkflow"
      @open-macro-stages-modal="showMacroStagesModal = true"
      @save-favorite-coordinates="saveFavoriteCoordinates"
      @apply-favorite-coordinates="applyFavoriteCoordinates"
      @undo="undo"
      @redo="redo"
    />

    <!-- Main Workspace Area -->
    <div class="flex-1 flex overflow-hidden relative">
      <!-- Left Sidebar: Draggable Nodes Toolbar -->
      <WorkflowToolbar
        @add-node="handleAddNode"
        @auto-layout="autoLayout"
      />

      <!-- Center: Interactive Vue Flow Canvas -->
      <main
        class="flex-1 h-full relative bg-slate-50"
        @dragover="handleDragOver"
        @drop="handleDrop"
      >
        <VueFlow
          v-model:nodes="nodes"
          v-model:edges="edges"
          :connection-mode="ConnectionMode.Loose"
          :default-viewport="{ zoom: 0.75, x: 50, y: 150 }"
          :min-zoom="0.15"
          :max-zoom="2.5"
          :fit-view-on-init="false"
          :elevate-edges-on-select="true"
          :connect-on-click="false"
          :edges-updatable="true"
          :edge-updater-radius="18"
          :auto-pan-on-connect="false"
          :auto-pan-on-node-drag="false"
          :is-valid-connection="isValidConnection"
          :delete-key-code="['Delete', 'Backspace']"
          class="w-full h-full"
          @node-click="handleNodeClick"
          @edge-click="handleEdgeClick"
          @edge-update-start="handleEdgeUpdateStart"
          @edge-update="handleEdgeUpdate"
          @edge-update-end="handleEdgeUpdateEnd"
          @pane-click="handlePaneClick"
          @nodes-change="handleNodesChange"
          @edges-change="handleEdgesChange"
          @node-drag-stop="handleNodeDragStop"
          @viewport-change-end="handleViewportChangeEnd"
          @connect-start="handleConnectStart"
          @connect-end="handleConnectEnd"
          @connect="handleConnect"
        >
          <!-- Background Grid Pattern -->
          <Background
            pattern-color="#cbd5e1"
            :gap="20"
            :size="1.5"
          />

          <!-- Canvas Controls (Zoom, Fit View, Lock) -->
          <Controls position="bottom-left" class="bg-white/90 backdrop-blur-sm border border-slate-200 rounded-xl shadow-md p-1" />

          <!-- MiniMap for easy navigation of the 18+ nodes -->
          <MiniMap
            position="bottom-right"
            :node-color="getNodeColor"
            :mask-color="'rgba(241, 245, 249, 0.7)'"
            class="!w-44 !h-28 bg-white/95 backdrop-blur-sm border border-slate-200 rounded-xl shadow-lg !m-4"
          />

          <!-- Custom Node Templates -->
          <template #node-state="props">
            <StateNode v-bind="props" />
          </template>
          <template #node-start="props">
            <StateNode v-bind="props" />
          </template>
          <template #node-end="props">
            <StateNode v-bind="props" />
          </template>
          <template #node-gateway="props">
            <GatewayNode v-bind="props" />
          </template>
          <template #node-ai_agent="props">
            <AIAgentNode v-bind="props" />
          </template>

          <!-- Custom Edge Template -->
          <template #edge-workflow="props">
            <WorkflowEdge v-bind="props" @select-edge="handleSelectEdgeById" @delete-edge="handleDeleteEdgeById" />
          </template>
          <template #edge-default="props">
            <WorkflowEdge v-bind="props" @select-edge="handleSelectEdgeById" @delete-edge="handleDeleteEdgeById" />
          </template>
        </VueFlow>

        <!-- Status Toast Banner -->
        <div
          v-if="toastMessage"
          class="absolute top-4 right-4 z-50 flex items-center gap-2 px-4 py-2.5 rounded-xl shadow-xl border text-xs font-semibold transition-all transform animate-fade-in"
          :class="toastType === 'success' ? 'bg-emerald-900 text-white border-emerald-700' : 'bg-red-900 text-white border-red-700'"
        >
          <CheckCircle2 v-if="toastType === 'success'" class="w-4 h-4 text-emerald-300" />
          <AlertCircle v-else class="w-4 h-4 text-rose-300" />
          <span>{{ toastMessage }}</span>
        </div>
      </main>

      <!-- Right Sidebar: Properties & Node/Edge Inspector -->
      <NodeConfigPanel
        :selected-node="selectedNode"
        :selected-edge="selectedEdge"
        :total-nodes="nodes.length"
        :total-edges="edges.length"
        :nodes="nodes"
        :edges="edges"
        :macro-stages="workflowMacroStages"
        :stage-forms="stageForms"
        :stage-consents="stageConsents"
        :document-templates="documentTemplates"
        :system-roles="allRoles"
        :users="allUsers"
        @update-node="handleUpdateNode"
        @update-edge="handleUpdateEdge"
        @delete-selected="handleDeleteSelected"
        @open-macro-stages-modal="showMacroStagesModal = true"
      />
    </div>

    <!-- Macro Stages Configuration Modal -->
    <MacroStagesModal
      :is-open="showMacroStagesModal"
      :macro-stages="workflowMacroStages"
      :nodes="nodes"
      @close="showMacroStagesModal = false"
      @save="handleSaveMacroStages"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { VueFlow, useVueFlow, MarkerType, applyNodeChanges, applyEdgeChanges, ConnectionMode } from '@vue-flow/core';
import { Background } from '@vue-flow/background';
import { Controls } from '@vue-flow/controls';
import { MiniMap } from '@vue-flow/minimap';
import { Sparkles, Bookmark, Copy, CheckCircle2, AlertCircle } from 'lucide-vue-next';

import StateNode from '~/components/workflow/nodes/StateNode.vue';
import GatewayNode from '~/components/workflow/nodes/GatewayNode.vue';
import AIAgentNode from '~/components/workflow/nodes/AIAgentNode.vue';
import WorkflowEdge from '~/components/workflow/WorkflowEdge.vue';
import WorkflowVersionBar from '~/components/workflow/WorkflowVersionBar.vue';
import WorkflowToolbar from '~/components/workflow/WorkflowToolbar.vue';
import NodeConfigPanel from '~/components/workflow/NodeConfigPanel.vue';
import MacroStagesModal from '~/components/workflow/MacroStagesModal.vue';
import { DEFAULT_MACRO_STAGES, type MacroStageDef } from '~/utils/macroStages';

// Coordenadas Maestras Oficiales de IACS para 18 nodos con espaciado amplio y nombres completos
const DEFAULT_MASTER_COORDINATES: Record<string, { x: number; y: number }> = {
  start: { x: 60, y: 180 },
  borrador: { x: 280, y: 140 },
  ai_chat: { x: 280, y: 380 },
  eval_bp: { x: 660, y: 140 },
  aprob_bo: { x: 1040, y: 140 },
  aprob_vp: { x: 1420, y: 140 },
  asig_demanda: { x: 1800, y: 140 },
  ventana_est: { x: 2180, y: 140 },
  gw_presupuesto: { x: 2560, y: 140 },
  est_con_presupuesto: { x: 2940, y: 30 },
  est_sin_presupuesto: { x: 2940, y: 260 },
  val_est_bp: { x: 3320, y: 140 },
  vobo_est_bo: { x: 3700, y: 140 },
  plan_fechas: { x: 4080, y: 140 },
  val_plan_bp: { x: 4460, y: 140 },
  aprob_plan_bo: { x: 4840, y: 140 },
  planificacion: { x: 5220, y: 140 },
  end: { x: 5580, y: 180 },
  observada: { x: 2180, y: 480 },
  desestimada: { x: 2560, y: 480 },
};

const config = useRuntimeConfig();
const apiBase = config.public.apiBase || '/api/v1';

const { project, fitView, setViewport, removeSelectedEdges, addSelectedEdges, findEdge } = useVueFlow();

// State
const workflow = ref<any>(null);
const nodes = ref<any[]>([]);
const edges = ref<any[]>([]);
const isDirty = ref(false);
const isSaving = ref(false);
const showMacroStagesModal = ref(false);

const VIEWPORT_STORAGE_KEY = 'iacs_workflow_viewport_v2';
const FAVORITES_STORAGE_KEY = 'iacs_workflow_favorite_coordinates_v2';

let isLoadingWorkflow = false;

const handleNodeDragStop = () => {
  if (isLoadingWorkflow || isApplyingHistory) return;
  isDirty.value = true;
};

const handleViewportChangeEnd = (viewport: any) => {
  if (typeof window !== 'undefined' && viewport) {
    try {
      localStorage.setItem(VIEWPORT_STORAGE_KEY, JSON.stringify(viewport));
    } catch (e) {}
  }
};

const handleBeforeUnload = (e: BeforeUnloadEvent) => {
  if (isDirty.value) {
    e.preventDefault();
    e.returnValue = 'Tienes cambios no guardados en el diagrama. ¿Seguro que deseas salir?';
    return e.returnValue;
  }
};

const workflowMacroStages = computed<MacroStageDef[]>(() => {
  const ms = workflow.value?.graph_json?.macro_stages;
  if (Array.isArray(ms) && ms.length > 0) return ms;
  return DEFAULT_MACRO_STAGES;
});

const handleSaveMacroStages = (updatedStages: MacroStageDef[]) => {
  if (!workflow.value) return;
  if (!workflow.value.graph_json) {
    workflow.value.graph_json = { nodes: nodes.value, edges: edges.value };
  }
  workflow.value.graph_json.macro_stages = updatedStages;

  // Sincronizar parent_stage_id, sub_stage_order y sub_stage_role en los nodos del diagrama
  const nodeToInfoMap = new Map<string, { parentId: string; order: number; role?: string }>();
  for (const stg of updatedStages) {
    const subIds = (stg.nodeIds || []).filter(nid => nid !== stg.id);
    subIds.forEach((subId, sIdx) => {
      nodeToInfoMap.set(subId, {
        parentId: stg.id,
        order: sIdx + 1,
        role: stg.subRoles?.[subId] || '',
      });
    });
  }

  nodes.value.forEach(n => {
    if (!n.data) n.data = {};
    if (nodeToInfoMap.has(n.id)) {
      const info = nodeToInfoMap.get(n.id)!;
      n.data.parent_stage_id = info.parentId;
      n.data.sub_stage_order = info.order;
      if (info.role) {
        n.data.sub_stage_role = info.role;
      }
    } else {
      n.data.parent_stage_id = null;
      delete n.data.sub_stage_order;
    }
  });

  if (selectedNode.value) {
    const updated = nodes.value.find(n => n.id === selectedNode.value.id);
    if (updated) {
      selectedNode.value = { ...updated };
    }
  }

  isDirty.value = true;
  pushHistory();
  showToast('Macro-etapas y sub-estados actualizados exitosamente', 'success');
};

const selectedNode = ref<any | null>(null);
const selectedEdge = ref<any | null>(null);

const stageForms = ref<any[]>([]);
const stageConsents = ref<any[]>([]);
const documentTemplates = ref<any[]>([]);
const allRoles = ref<any[]>([]);
const allUsers = ref<any[]>([]);

// Toast Notification
const toastMessage = ref('');
const toastType = ref<'success' | 'error'>('success');
let toastTimer: any = null;

const showToast = (message: string, type: 'success' | 'error' = 'success') => {
  toastMessage.value = message;
  toastType.value = type;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastMessage.value = '';
  }, 3500);
};

// Undo / Redo History Stack
interface HistorySnapshot {
  nodes: any[];
  edges: any[];
}
const history = ref<HistorySnapshot[]>([]);
const historyIndex = ref(-1);
let isApplyingHistory = false;

const pushHistory = () => {
  if (isApplyingHistory) return;
  const snapshot: HistorySnapshot = {
    nodes: JSON.parse(JSON.stringify(nodes.value)),
    edges: JSON.parse(JSON.stringify(edges.value)),
  };
  // Trim redo future
  if (historyIndex.value < history.value.length - 1) {
    history.value = history.value.slice(0, historyIndex.value + 1);
  }
  history.value.push(snapshot);
  if (history.value.length > 30) history.value.shift();
  historyIndex.value = history.value.length - 1;
  isDirty.value = true;
};

const undo = () => {
  if (historyIndex.value > 0) {
    isApplyingHistory = true;
    historyIndex.value--;
    const snapshot = history.value[historyIndex.value];
    nodes.value = JSON.parse(JSON.stringify(snapshot.nodes));
    edges.value = JSON.parse(JSON.stringify(snapshot.edges));
    selectedNode.value = null;
    selectedEdge.value = null;
    setTimeout(() => { isApplyingHistory = false; }, 50);
  }
};

const redo = () => {
  if (historyIndex.value < history.value.length - 1) {
    isApplyingHistory = true;
    historyIndex.value++;
    const snapshot = history.value[historyIndex.value];
    nodes.value = JSON.parse(JSON.stringify(snapshot.nodes));
    edges.value = JSON.parse(JSON.stringify(snapshot.edges));
    selectedNode.value = null;
    selectedEdge.value = null;
    setTimeout(() => { isApplyingHistory = false; }, 50);
  }
};

const ALL_VALID_HANDLES = new Set([
  'top', 'top-left', 'top-right',
  'bottom', 'bottom-left', 'bottom-right',
  'left', 'left-top', 'left-bottom',
  'right', 'right-top', 'right-bottom'
]);

// Normalizador seguro de manijas/conectores: respeta al 100% la selección del usuario
const normalizeEdgeHandle = (handleId: string | undefined | null, isSource: boolean): string => {
  if (!handleId) return isSource ? 'right' : 'left';
  if (ALL_VALID_HANDLES.has(handleId)) return handleId;
  for (const pos of ['top-left', 'top-right', 'bottom-left', 'bottom-right', 'left-top', 'left-bottom', 'right-top', 'right-bottom', 'top', 'bottom', 'left', 'right']) {
    if (handleId.includes(pos)) return pos;
  }
  return handleId;
};

// Serializador limpio para evitar volcar el DOM / handleBounds internos de Vue Flow a la base de datos
const serializeGraph = () => ({
  nodes: nodes.value.map(n => ({
    id: n.id,
    type: n.type || 'state',
    position: { x: Math.round(n.position?.x ?? 0), y: Math.round(n.position?.y ?? 0) },
    data: n.data || {},
  })),
  edges: edges.value.map(e => ({
    id: e.id,
    source: e.source,
    target: e.target,
    sourceHandle: normalizeEdgeHandle(e.sourceHandle, true),
    targetHandle: normalizeEdgeHandle(e.targetHandle, false),
    type: e.type || 'workflow',
    label: e.label || '',
    markerEnd: e.markerEnd,
    data: e.data || {},
  })),
  macro_stages: workflowMacroStages.value,
  favorite_coordinates: workflow.value?.graph_json?.favorite_coordinates || {},
});

// Load Initial Data
const loadActiveWorkflow = async () => {
  isLoadingWorkflow = true;
  try {
    const res = await $fetch<any>(`${apiBase}/workflow/active`);
    const data = res?.data || res;
    if (data) {
      workflow.value = data;
      const graph = data.graph_json || { nodes: [], edges: [] };
      nodes.value = (graph.nodes || []).map((n: any) => ({
        ...n,
        // Map canonical node type
        type: n.type || (n.id.startsWith('gw_') ? 'gateway' : n.id === 'ai_chat' ? 'ai_agent' : 'state'),
      }));
      edges.value = (graph.edges || []).map((e: any) => {
        const isObs = (e.target === 'observada' || (e.target || '').includes('obs') || (e.label || '').toLowerCase().includes('observa'));
        const isDesest = (e.target === 'desestimada' || (e.target || '').includes('desest') || (e.label || '').toLowerCase().includes('desestima'));
        const defaultColor = isObs ? '#F59E0B' : isDesest ? '#EF4444' : '#4F5AF5';
        const edgeColor = e.data?.style_config?.button_color || defaultColor;
        const srcHandle = normalizeEdgeHandle(e.sourceHandle, true);
        const tgtHandle = normalizeEdgeHandle(e.targetHandle, false);
        return {
          ...e,
          sourceHandle: srcHandle,
          targetHandle: tgtHandle,
          type: 'workflow',
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: edgeColor,
            width: 18,
            height: 18,
          },
        };
      });

      // Initialize history
      history.value = [{
        nodes: JSON.parse(JSON.stringify(nodes.value)),
        edges: JSON.parse(JSON.stringify(edges.value)),
      }];
      historyIndex.value = 0;
      isDirty.value = false;

      // Restaurar viewport exacto para que F5 NUNCA salte ni mueva las cajas de lugar
      let restoredViewport = false;
      if (typeof window !== 'undefined') {
        try {
          const rawVp = localStorage.getItem(VIEWPORT_STORAGE_KEY);
          if (rawVp) {
            const vp = JSON.parse(rawVp);
            if (vp && typeof vp.zoom === 'number' && typeof vp.x === 'number') {
              setTimeout(() => {
                setViewport(vp);
              }, 100);
              restoredViewport = true;
            }
          }
        } catch (e) {}
      }

      // Solo si el usuario nunca ha movido el viewport, hacer fitView inicial
      if (!restoredViewport) {
        setTimeout(() => {
          fitView({ padding: 0.15 });
        }, 300);
      }
    }
  } catch (err: any) {
    console.error('Error loading active workflow:', err);
    showToast('Error al cargar flujo activo', 'error');
  } finally {
    setTimeout(() => {
      isLoadingWorkflow = false;
      isDirty.value = false;
    }, 350);
  }
};

const loadMetadata = async () => {
  try {
    const [formsRes, consentsRes, docsRes, rolesRes, usersRes] = await Promise.all([
      $fetch<any>(`${apiBase}/stage-forms`).catch(() => ({ data: [] })),
      $fetch<any>(`${apiBase}/stage-consents`).catch(() => ({ data: [] })),
      $fetch<any>(`${apiBase}/document-templates`).catch(() => ({ data: [] })),
      $fetch<any>(`${apiBase}/roles`).catch(() => []),
      $fetch<any>(`${apiBase}/users`).catch(() => []),
    ]);
    stageForms.value = formsRes?.data || formsRes || [];
    stageConsents.value = consentsRes?.data || consentsRes || [];
    documentTemplates.value = docsRes?.data || docsRes || [];
    allRoles.value = Array.isArray(rolesRes) ? rolesRes : (rolesRes?.data || []);
    allUsers.value = Array.isArray(usersRes) ? usersRes : (usersRes?.data || []);
  } catch (err) {
    console.warn('Error loading workflow catalog metadata:', err);
  }
};

// Detección de si el usuario está escribiendo en campos de formulario
const isTypingInField = (target: EventTarget | null): boolean => {
  if (!target || !(target instanceof HTMLElement)) return false;
  const tag = target.tagName?.toUpperCase();
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true;
  if (target.isContentEditable) return true;
  if (target.closest('input, textarea, select, [contenteditable="true"]')) return true;
  return false;
};

// Tecla Suprimir (Delete), Retroceso (Backspace) para borrar o Escape para cancelar flechas
const handleKeyDown = (e: KeyboardEvent) => {
  if (isTypingInField(e.target)) return;

  if (e.key === 'Escape') {
    if (showMacroStagesModal.value) {
      showMacroStagesModal.value = false;
      return;
    }
    selectedNode.value = null;
    selectedEdge.value = null;
    return;
  }

  if (e.key === 'Delete' || e.key === 'Del' || e.key === 'Backspace' || e.keyCode === 46 || e.keyCode === 8) {
    // 1. Si hay un nodo seleccionado en el inspector
    if (selectedNode.value) {
      e.preventDefault();
      e.stopPropagation();
      const nodeLabel = selectedNode.value.data?.label || selectedNode.value.id;
      handleDeleteSelected();
      showToast(`Estado "${nodeLabel}" eliminado`, 'success');
      return;
    }

    // 2. Si hay una arista seleccionada en el inspector
    if (selectedEdge.value) {
      e.preventDefault();
      e.stopPropagation();
      const edgeLabel = selectedEdge.value.label || selectedEdge.value.id;
      handleDeleteSelected();
      showToast(`Flecha "${edgeLabel}" eliminada`, 'success');
      return;
    }

    // 3. Si hay nodos o aristas marcados como seleccionados en el canvas de VueFlow
    const selNodes = nodes.value.filter(n => n.selected);
    const selEdges = edges.value.filter(e => e.selected);
    if (selNodes.length > 0 || selEdges.length > 0) {
      e.preventDefault();
      e.stopPropagation();
      const nIds = new Set(selNodes.map(n => n.id));
      const eIds = new Set(selEdges.map(e => e.id));

      if (nIds.size > 0) {
        nodes.value = nodes.value.filter(n => !nIds.has(n.id));
        edges.value = edges.value.filter(edge => !nIds.has(edge.source) && !nIds.has(edge.target));
      }
      if (eIds.size > 0) {
        edges.value = edges.value.filter(edge => !eIds.has(edge.id));
      }

      selectedNode.value = null;
      selectedEdge.value = null;
      pushHistory();
      showToast('Elementos seleccionados eliminados del diagrama', 'success');
    }
  }
};

onMounted(() => {
  loadActiveWorkflow();
  loadMetadata();
  window.addEventListener('keydown', handleKeyDown);
  window.addEventListener('beforeunload', handleBeforeUnload);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
  window.removeEventListener('beforeunload', handleBeforeUnload);
});

// Selection Handlers
const handleNodeClick = ({ node }: { node: any }) => {
  selectedNode.value = node;
  selectedEdge.value = null;
  removeSelectedEdges();
  edges.value.forEach(e => { e.selected = false; });
};

const handleEdgeClick = ({ edge }: { edge: any }) => {
  selectedEdge.value = edge;
  selectedNode.value = null;
  removeSelectedEdges();
  addSelectedEdges([edge]);
  edges.value.forEach(e => {
    e.selected = (e.id === edge.id);
  });
};

const handleSelectEdgeById = (edgeId: string) => {
  const edge = edges.value.find(e => e.id === edgeId);
  const flowEdge = findEdge(edgeId);
  if (edge) {
    selectedEdge.value = { ...edge };
    selectedNode.value = null;
    removeSelectedEdges();
    if (flowEdge) addSelectedEdges([flowEdge]);
    edges.value.forEach(e => {
      e.selected = (e.id === edgeId);
    });
  }
};

// Validación de conexiones
const isValidConnection = (connection: any) => {
  if (connection.source === connection.target) return false;
  return true;
};

// Reconexión y movimiento seguro de flechas (Edge Updater)
const edgeUpdateSuccessful = ref(false);
const edgeUpdateSnapshot = ref<any | null>(null);

const handleEdgeUpdateStart = ({ edge }: any) => {
  edgeUpdateSuccessful.value = false;
  edgeUpdateSnapshot.value = JSON.parse(JSON.stringify(edge));
};

const handleEdgeUpdate = ({ edge, connection }: { edge: any; connection: any }) => {
  edgeUpdateSuccessful.value = true;
  if (!connection || !connection.source || !connection.target) return;

  if (connection.source === connection.target) {
    showToast('No se puede conectar un nodo consigo mismo', 'error');
    return;
  }

  const idx = edges.value.findIndex(e => e.id === edge.id);
  if (idx !== -1) {
    edges.value[idx].source = connection.source;
    edges.value[idx].target = connection.target;
    const newSourceHandle = connection.sourceHandle || edge.sourceHandle || 'right';
    const newTargetHandle = connection.targetHandle || edge.targetHandle || 'left';
    edges.value[idx].sourceHandle = normalizeEdgeHandle(newSourceHandle, true);
    edges.value[idx].targetHandle = normalizeEdgeHandle(newTargetHandle, false);

    const isObs = (connection.target === 'observada' || (connection.target || '').includes('obs'));
    const isDesest = (connection.target === 'desestimada' || (connection.target || '').includes('desest'));
    const defaultColor = isObs ? '#F59E0B' : isDesest ? '#EF4444' : '#4F5AF5';
    edges.value[idx].markerEnd = {
      type: MarkerType.ArrowClosed,
      color: edges.value[idx].data?.style_config?.button_color || defaultColor,
      width: 18,
      height: 18,
    };

    if (selectedEdge.value?.id === edge.id) {
      selectedEdge.value = { ...edges.value[idx] };
    }
    pushHistory();
    showToast(`Transición reconectada hacia ${connection.target}`, 'success');
  }
};

const handleEdgeUpdateEnd = ({ edge }: any) => {
  // Si soltó en el vacío o canceló, restaurar la arista original para que NUNCA se borre
  setTimeout(() => {
    if (!edgeUpdateSuccessful.value && edgeUpdateSnapshot.value) {
      const snap = edgeUpdateSnapshot.value;
      const idx = edges.value.findIndex(e => e.id === snap.id);
      if (idx === -1) {
        edges.value.push({ ...snap });
      } else {
        edges.value[idx] = { ...snap };
      }
      if (selectedEdge.value?.id === snap.id) {
        selectedEdge.value = { ...snap };
      }
      showToast('Reconexión cancelada: la flecha se mantiene en su estado original', 'info');
    }
    edgeUpdateSnapshot.value = null;
    edgeUpdateSuccessful.value = false;
  }, 40);
};

const handlePaneClick = () => {
  selectedNode.value = null;
  selectedEdge.value = null;
  removeSelectedEdges();
  edges.value.forEach(e => { e.selected = false; });
};

const handleNodesChange = (changes: any) => {
  if (isLoadingWorkflow || isApplyingHistory) return;
  if (!Array.isArray(changes)) return;
  const isActualChange = changes.some(c => (c.type === 'position' && c.dragging === false) || c.type === 'remove' || c.type === 'add');
  if (isActualChange) {
    isDirty.value = true;
  }
  const removeChanges = changes.filter(c => c.type === 'remove');
  if (removeChanges.length > 0) {
    nodes.value = applyNodeChanges(removeChanges, nodes.value);
  }
};

const handleEdgesChange = (changes: any) => {
  if (isLoadingWorkflow || isApplyingHistory) return;
  if (!Array.isArray(changes)) return;
  const isActualChange = changes.some(c => c.type === 'remove' || c.type === 'add');
  if (isActualChange) {
    isDirty.value = true;
  }
  const removeChanges = changes.filter(c => c.type === 'remove');
  if (removeChanges.length > 0) {
    edges.value = applyEdgeChanges(removeChanges, edges.value);
  }
};

// Connection tracking para asegurar que la caja donde se hace clic es SIEMPRE el origen
const connectStartNodeId = ref<string | null>(null);
const connectStartHandleId = ref<string | null>(null);

const handleConnectStart = (params: any) => {
  if (params && params.nodeId) {
    connectStartNodeId.value = params.nodeId;
    connectStartHandleId.value = params.handleId || null;
  }
};

const handleConnectEnd = () => {
  connectStartNodeId.value = null;
  connectStartHandleId.value = null;
};

// Connections
const handleConnect = (params: any) => {
  let source = params.source;
  let target = params.target;
  let sourceHandle = normalizeEdgeHandle(params.sourceHandle || 'right', true);
  let targetHandle = normalizeEdgeHandle(params.targetHandle || 'left', false);

  // Regla de Oro: La caja donde el usuario hace el clic inicial es SIEMPRE el origen.
  // La caja donde suelta el ratón es SIEMPRE el destino (hacia donde apunta la flecha).
  if (connectStartNodeId.value) {
    if (connectStartNodeId.value === target) {
      source = params.target;
      target = params.source;
      sourceHandle = normalizeEdgeHandle(params.targetHandle || connectStartHandleId.value || 'right', true);
      targetHandle = normalizeEdgeHandle(params.sourceHandle || 'left', false);
    }
  }

  // Prevenir auto-conexión
  if (source === target) {
    showToast('No se puede conectar un nodo consigo mismo', 'error');
    return;
  }

  // Si ya existe una transición entre estos dos estados, seleccionarla en vez de error abrupto
  const existingEdge = edges.value.find(e => e.source === source && e.target === target);
  if (existingEdge) {
    selectedEdge.value = { ...existingEdge };
    selectedNode.value = null;
    showToast(`Transición entre ${source} y ${target} ya existe (seleccionada en el panel)`, 'info');
    return;
  }

  const isObs = (target === 'observada' || (target || '').includes('obs'));
  const isDesest = (target === 'desestimada' || (target || '').includes('desest'));
  const defaultColor = isObs ? '#F59E0B' : isDesest ? '#EF4444' : '#4F5AF5';
  const defaultLabel = isObs ? 'Observar' : isDesest ? 'Desestimar' : 'Avanzar';

  const newEdge = {
    id: `e-${source}-${target}-${Date.now().toString().slice(-4)}`,
    source: source,
    target: target,
    sourceHandle: sourceHandle,
    targetHandle: targetHandle,
    type: 'workflow',
    label: defaultLabel,
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: defaultColor,
      width: 18,
      height: 18,
    },
    data: {
      condition_type: 'always',
      label: defaultLabel,
      style_config: {
        button_bg: defaultColor,
        button_color: defaultColor,
        label_color: '#ffffff',
      },
    },
  };
  edges.value.push(newEdge);
  selectedEdge.value = { ...newEdge };
  selectedNode.value = null;
  pushHistory();
  showToast(`Transición creada de ${source} hacia ${target}`, 'success');
};

const handleDeleteEdgeById = (edgeId: string) => {
  edges.value = edges.value.filter(e => e.id !== edgeId);
  if (selectedEdge.value?.id === edgeId) {
    selectedEdge.value = null;
  }
  pushHistory();
  showToast('Flecha eliminada exitosamente', 'success');
};

// Node updates from Right Inspector
const handleUpdateNode = (updatedData: any) => {
  if (!selectedNode.value) return;
  const idx = nodes.value.findIndex(n => n.id === selectedNode.value.id);
  if (idx !== -1) {
    nodes.value[idx].data = { ...nodes.value[idx].data, ...updatedData };
    selectedNode.value = { ...nodes.value[idx] };
    pushHistory();
  }
};

// Edge updates from Right Inspector
const handleUpdateEdge = (payload: any) => {
  if (!selectedEdge.value) return;
  const idx = edges.value.findIndex(e => e.id === selectedEdge.value.id);
  if (idx !== -1) {
    if (payload.label !== undefined) {
      edges.value[idx].label = payload.label;
    }
    const mergedData = {
      ...edges.value[idx].data,
      ...(payload.data || payload),
    };
    if (payload.label !== undefined) {
      mergedData.label = payload.label;
    }
    edges.value[idx].data = mergedData;
    const isObs = (edges.value[idx].target === 'observada' || (edges.value[idx].target || '').includes('obs') || (edges.value[idx].label || '').toLowerCase().includes('observa'));
    const isDesest = (edges.value[idx].target === 'desestimada' || (edges.value[idx].target || '').includes('desest') || (edges.value[idx].label || '').toLowerCase().includes('desestima'));
    const defaultColor = isObs ? '#F59E0B' : isDesest ? '#EF4444' : '#4F5AF5';
    const arrowColor = mergedData.style_config?.button_color || defaultColor;
    edges.value[idx].markerEnd = {
      type: MarkerType.ArrowClosed,
      color: arrowColor,
      width: 18,
      height: 18,
    };
    selectedEdge.value = { ...edges.value[idx] };
    pushHistory();
  }
};


// Delete selected node or edge
const handleDeleteSelected = () => {
  if (selectedNode.value) {
    const nodeId = selectedNode.value.id;
    nodes.value = nodes.value.filter(n => n.id !== nodeId);
    edges.value = edges.value.filter(e => e.source !== nodeId && e.target !== nodeId);
    selectedNode.value = null;
    pushHistory();
  } else if (selectedEdge.value) {
    const edgeId = selectedEdge.value.id;
    edges.value = edges.value.filter(e => e.id !== edgeId);
    selectedEdge.value = null;
    pushHistory();
  }
};

// Drag and Drop from Left Toolbar
const handleDragOver = (e: DragEvent) => {
  e.preventDefault();
  if (e.dataTransfer) {
    e.dataTransfer.dropEffect = 'move';
  }
};

const handleDrop = (e: DragEvent) => {
  e.preventDefault();
  if (!e.dataTransfer) return;

  const nodeType = e.dataTransfer.getData('application/vueflow-type');
  const payloadStr = e.dataTransfer.getData('application/vueflow-payload');
  if (!nodeType) return;

  let payload = { label: 'Nuevo Nodo', description: '', stateSubtype: 'standard', roles: [] };
  try {
    if (payloadStr) payload = JSON.parse(payloadStr);
  } catch (err) {}

  const mouseX = e.clientX;
  const mouseY = e.clientY;
  const flowPos = project ? project({ x: mouseX - 300, y: mouseY - 100 }) : { x: mouseX - 250, y: mouseY - 80 };

  const newId = `node_${Date.now().toString().slice(-6)}`;
  const mappedType = nodeType === 'gateway' ? 'gateway' : nodeType === 'start' ? 'start' : nodeType === 'end' ? 'end' : 'state';

  const newNode = {
    id: newId,
    type: mappedType,
    position: flowPos,
    data: {
      label: payload.label || 'Nuevo Estado',
      description: payload.description || '',
      stateSubtype: payload.stateSubtype || 'standard',
      roles: payload.roles || [],
      dispatch_mode: 'individual',
      custodian_role: 'registrador',
    },
  };

  nodes.value.push(newNode);
  selectedNode.value = newNode;
  pushHistory();
};

const handleAddNode = (item: any) => {
  const newId = `node_${Date.now().toString().slice(-6)}`;
  const mappedType = item.type === 'gateway' ? 'gateway' : item.type === 'start' ? 'start' : item.type === 'end' ? 'end' : 'state';

  const newNode = {
    id: newId,
    type: mappedType,
    position: { x: 500 + Math.random() * 80, y: 200 + Math.random() * 80 },
    data: {
      label: item.defaultLabel || item.label,
      description: item.desc || '',
      stateSubtype: item.stateSubtype || 'standard',
      roles: item.defaultRoles || [],
      dispatch_mode: 'individual',
      custodian_role: 'registrador',
    },
  };

  nodes.value.push(newNode);
  selectedNode.value = newNode;
  pushHistory();
};

// Auto Layout
const autoLayout = () => {
  let customIndex = 0;
  nodes.value = nodes.value.map(node => {
    let pos = DEFAULT_MASTER_COORDINATES[node.id];
    if (!pos) {
      const subtype = node.data?.stateSubtype;
      if (subtype === 'observada' || subtype === 'desestimada') {
        pos = { x: 2940 + customIndex * 380, y: 480 };
      } else {
        pos = { x: 5580 + customIndex * 380, y: 140 };
      }
      customIndex++;
    }
    return {
      ...node,
      position: { ...pos },
    };
  });
  pushHistory();
  setTimeout(() => {
    fitView({ padding: 0.15 });
  }, 200);
  showToast('Diagrama organizado con espaciado amplio y nombres completos legibles', 'success');
};

// Set as Default
const setAsDefaultLayout = () => {
  showToast('Plantilla de coordenadas fijada como predeterminada', 'success');
};

// Clone Draft
const cloneDraft = async () => {
  if (!workflow.value?.id) return;
  try {
    const res = await $fetch<any>(`${apiBase}/workflow/definitions`, {
      method: 'POST',
      body: {
        clone_from: workflow.value.id,
        name: `${workflow.value.name} (Borrador)`,
        description: `Clonado a partir de v${workflow.value.version}`,
      },
    });
    showToast('Borrador clonado exitosamente', 'success');
    await loadActiveWorkflow();
  } catch (err: any) {
    showToast('Error al clonar borrador: ' + (err.data?.detail || err.message), 'error');
  }
};

// 1. Guardar Coordenadas del gráfico como Favoritas
const saveFavoriteCoordinates = async () => {
  if (!workflow.value?.id) return;

  const coordsMap: Record<string, { x: number; y: number }> = {};
  nodes.value.forEach(node => {
    coordsMap[node.id] = {
      x: Math.round(node.position?.x ?? 0),
      y: Math.round(node.position?.y ?? 0),
    };
  });

  // Guardar en localStorage
  if (typeof window !== 'undefined') {
    try {
      localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(coordsMap));
    } catch (e) {}
  }

  // Guardar en base de datos dentro del graph_json
  if (!workflow.value.graph_json) workflow.value.graph_json = {};
  workflow.value.graph_json.favorite_coordinates = coordsMap;

  isSaving.value = true;
  try {
    const graphData = serializeGraph();
    graphData.favorite_coordinates = coordsMap;
    await $fetch(`${apiBase}/workflow/definitions/${workflow.value.id}`, {
      method: 'PATCH',
      body: {
        graph_json: graphData,
      },
    });
    isDirty.value = false;
    showToast('⭐ ¡Coordenadas favoritas guardadas exitosamente!', 'success');
  } catch (err: any) {
    showToast('Error al guardar favoritas: ' + (err.data?.detail || err.message), 'error');
  } finally {
    isSaving.value = false;
    isDirty.value = false;
  }
};

// 2. Aplicar Coordenadas Favoritas al diagrama
const applyFavoriteCoordinates = () => {
  let coords: Record<string, { x: number; y: number }> | null = null;

  // Intentar desde la base de datos
  if (workflow.value?.graph_json?.favorite_coordinates && Object.keys(workflow.value.graph_json.favorite_coordinates).length > 0) {
    coords = workflow.value.graph_json.favorite_coordinates;
  }

  // O desde localStorage
  if (!coords && typeof window !== 'undefined') {
    try {
      const raw = localStorage.getItem(FAVORITES_STORAGE_KEY);
      if (raw) coords = JSON.parse(raw);
    } catch (e) {}
  }

  if (!coords || Object.keys(coords).length === 0) {
    showToast('Aún no has guardado coordenadas favoritas. Ordena las cajas y haz clic en "Guardar Favoritas".', 'error');
    return;
  }

  // Ordenar las cajas de acuerdo a lo que dejaste guardado
  nodes.value = nodes.value.map(node => {
    if (coords && coords[node.id]) {
      return {
        ...node,
        position: { x: coords[node.id].x, y: coords[node.id].y },
      };
    }
    return node;
  });

  isDirty.value = true;
  pushHistory();
  showToast('🎯 Coordenadas favoritas aplicadas al diagrama', 'success');
};

// 3. Guardar y Publicar unificado en un solo botón
const saveAndPublishWorkflow = async () => {
  if (!workflow.value?.id) return;
  isSaving.value = true;
  try {
    const graphData = serializeGraph();

    // 1. Guardar estado actual
    await $fetch(`${apiBase}/workflow/definitions/${workflow.value.id}`, {
      method: 'PATCH',
      body: {
        graph_json: graphData,
      },
    });

    // 2. Publicar como versión activa
    await $fetch(`${apiBase}/workflow/definitions/${workflow.value.id}/publish`, {
      method: 'POST',
    });

    if (workflow.value) {
      workflow.value.status = 'published';
      workflow.value.graph_json = graphData;
    }

    // Resetear historia a partir de lo guardado
    history.value = [{
      nodes: JSON.parse(JSON.stringify(nodes.value)),
      edges: JSON.parse(JSON.stringify(edges.value)),
    }];
    historyIndex.value = 0;

    isDirty.value = false;
    showToast('🚀 ¡Flujo guardado y publicado como Activo en todo el sistema!', 'success');
  } catch (err: any) {
    showToast('Error al guardar y publicar: ' + (err.data?.detail || err.message), 'error');
  } finally {
    isSaving.value = false;
    isDirty.value = false;
  }
};

// MiniMap Node Color helper
const getNodeColor = (node: any) => {
  if (node.id === 'start') return '#10b981';
  if (node.id === 'end') return '#059669';
  if (node.type === 'gateway') return '#f59e0b';
  if (node.type === 'ai_agent') return '#8b5cf6';
  if (node.data?.stateSubtype === 'observada') return '#f59e0b';
  if (node.data?.stateSubtype === 'desestimada') return '#f43f5e';
  return '#4F5AF5';
};
</script>

<style>
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
  animation: fadeIn 0.2s ease-out;
}

/* Conectores / Handles: sutiles, ocultos por defecto y visibles al posar el ratón sobre la caja */
.vue-flow__handle {
  border-radius: 9999px !important;
  cursor: crosshair !important;
  z-index: 30 !important;
}

/* Manijas de mover flechas (Edge Updaters): OCULTAS por defecto para no saturar la vista */
.vue-flow__edgeupdater {
  display: none !important;
}

/* ÚNICAMENTE visibles cuando el usuario pasa el ratón sobre esa flecha o la selecciona */
.vue-flow__edge:hover .vue-flow__edgeupdater,
.vue-flow__edge.selected .vue-flow__edgeupdater {
  display: block !important;
  fill: #ffffff !important;
  stroke: #4F5AF5 !important;
  stroke-width: 3.5px !important;
  r: 9px !important;
  cursor: grab !important;
  filter: drop-shadow(0 2px 5px rgba(79, 90, 245, 0.45)) !important;
  transition: r 0.15s ease, fill 0.15s ease !important;
  z-index: 50 !important;
}

.vue-flow__edge:hover .vue-flow__edgeupdater:hover,
.vue-flow__edge.selected .vue-flow__edgeupdater:hover {
  r: 12px !important;
  fill: #EEF2FF !important;
  stroke: #3730A3 !important;
  cursor: grabbing !important;
}
</style>
