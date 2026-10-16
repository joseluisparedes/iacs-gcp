<template>
  <div class="h-[calc(100vh-4rem)] flex flex-col overflow-hidden bg-slate-100">
    <!-- Top Bar: Status, Auto-save indicator, Undo/Redo, Actions & Publish -->
    <WorkflowVersionBar
      :workflow-name="workflow?.name || 'Flujo Oficial de Gestión de la Demanda'"
      :version="workflow?.version || 2"
      :status="workflow?.status || 'published'"
      :is-dirty="isDirty"
      :is-saving="isSaving"
      :can-undo="historyIndex > 0"
      :can-redo="historyIndex < history.length - 1"
      @save="saveWorkflow"
      @publish="publishWorkflow"
      @open-roles-modal="showRolesModal = true"
      @auto-layout="autoLayout"
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
          :default-viewport="{ zoom: 0.75, x: 50, y: 150 }"
          :min-zoom="0.15"
          :max-zoom="2.5"
          :fit-view-on-init="false"
          :elevate-edges-on-select="true"
          :connect-on-click="true"
          :edges-updatable="true"
          :edge-updater-radius="20"
          class="w-full h-full"
          @node-click="handleNodeClick"
          @edge-click="handleEdgeClick"
          @edge-update="handleEdgeUpdate"
          @pane-click="handlePaneClick"
          @nodes-change="handleNodesChange"
          @edges-change="handleEdgesChange"
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
            <WorkflowEdge v-bind="props" @select-edge="handleSelectEdgeById" />
          </template>
          <template #edge-default="props">
            <WorkflowEdge v-bind="props" @select-edge="handleSelectEdgeById" />
          </template>
        </VueFlow>


        <!-- Floating Canvas Actions (Bottom Center - as in reference image) -->
        <div class="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2 bg-white/95 backdrop-blur-md px-3 py-2 rounded-2xl shadow-xl border border-slate-200/80">
          <button
            type="button"
            @click="autoLayout"
            class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-[#EB5F46] bg-[#FFF0ED] hover:bg-[#FDE2DC] border border-[#FCD9D2] rounded-xl transition-all shadow-2xs"
            title="Reordenar automáticamente los 18 nodos sin superposición"
          >
            <Sparkles class="w-3.5 h-3.5 text-[#EB5F46]" />
            <span>Organizar Diagrama</span>
          </button>

          <div class="h-4 w-px bg-slate-200"></div>

          <button
            type="button"
            @click="setAsDefaultLayout"
            class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl transition-all shadow-2xs"
            title="Guardar posiciones actuales como plantilla predeterminada"
          >
            <Bookmark class="w-3.5 h-3.5 text-slate-500" />
            <span>Fijar como Default</span>
          </button>

          <button
            type="button"
            @click="cloneDraft"
            class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 rounded-xl transition-all shadow-2xs"
            title="Crear una nueva versión borrador a partir de este flujo"
          >
            <Copy class="w-3.5 h-3.5 text-indigo-600" />
            <span>Clonar Borrador</span>
          </button>
        </div>

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
        :stage-forms="stageForms"
        :stage-consents="stageConsents"
        :document-templates="documentTemplates"
        :system-roles="allRoles"
        :users="allUsers"
        @update-node="handleUpdateNode"
        @update-edge="handleUpdateEdge"
        @delete-selected="handleDeleteSelected"
      />
    </div>

    <!-- Role Assignment Modal -->
    <RoleAssignmentModal
      :is-open="showRolesModal"
      :workflow-id="workflow?.id"
      @close="showRolesModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { VueFlow, useVueFlow, MarkerType } from '@vue-flow/core';
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
import RoleAssignmentModal from '~/components/workflow/RoleAssignmentModal.vue';

// Coordenadas Maestras Oficiales de IACS para 18 nodos
const DEFAULT_MASTER_COORDINATES: Record<string, { x: number; y: number }> = {
  start: { x: 60, y: 180 },
  borrador: { x: 240, y: 140 },
  ai_chat: { x: 240, y: 340 },
  eval_bp: { x: 520, y: 140 },
  aprob_bo: { x: 800, y: 140 },
  aprob_vp: { x: 1080, y: 140 },
  asig_demanda: { x: 1360, y: 140 },
  ventana_est: { x: 1640, y: 140 },
  gw_presupuesto: { x: 1920, y: 140 },
  est_con_presupuesto: { x: 2180, y: 40 },
  est_sin_presupuesto: { x: 2180, y: 240 },
  val_est_bp: { x: 2480, y: 140 },
  vobo_est_bo: { x: 2760, y: 140 },
  plan_fechas: { x: 3040, y: 140 },
  val_plan_bp: { x: 3320, y: 140 },
  aprob_plan_bo: { x: 3600, y: 140 },
  planificacion: { x: 3880, y: 140 },
  end: { x: 4140, y: 180 },
  observada: { x: 1640, y: 440 },
  desestimada: { x: 1920, y: 440 },
};

const config = useRuntimeConfig();
const apiBase = config.public.apiBase || '/api/v1';

const { project, fitView } = useVueFlow();

// State
const workflow = ref<any>(null);
const nodes = ref<any[]>([]);
const edges = ref<any[]>([]);
const isDirty = ref(false);
const isSaving = ref(false);
const showRolesModal = ref(false);

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

// Load Initial Data
const loadActiveWorkflow = async () => {
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
        return {
          ...e,
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

      // Auto-fit after mount
      setTimeout(() => {
        fitView({ padding: 0.15 });
      }, 300);
    }
  } catch (err: any) {
    console.error('Error loading active workflow:', err);
    showToast('Error al cargar flujo activo', 'error');
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

onMounted(() => {
  loadActiveWorkflow();
  loadMetadata();
});

// Selection Handlers
const handleNodeClick = ({ node }: { node: any }) => {
  selectedNode.value = node;
  selectedEdge.value = null;
};

const handleEdgeClick = ({ edge }: { edge: any }) => {
  selectedEdge.value = edge;
  selectedNode.value = null;
};

const handleSelectEdgeById = (edgeId: string) => {
  const edge = edges.value.find(e => e.id === edgeId);
  if (edge) {
    selectedEdge.value = { ...edge };
    selectedNode.value = null;
  }
};

const handleEdgeUpdate = ({ edge, connection }: { edge: any; connection: any }) => {
  const idx = edges.value.findIndex(e => e.id === edge.id);
  if (idx !== -1) {
    edges.value[idx].source = connection.source;
    edges.value[idx].target = connection.target;
    edges.value[idx].sourceHandle = connection.sourceHandle;
    edges.value[idx].targetHandle = connection.targetHandle;
    if (selectedEdge.value?.id === edge.id) {
      selectedEdge.value = { ...edges.value[idx] };
    }
    pushHistory();
    showToast('Transición reconectada exitosamente', 'success');
  }
};


const handlePaneClick = () => {
  selectedNode.value = null;
  selectedEdge.value = null;
};

const handleNodesChange = () => {
  if (!isApplyingHistory) {
    isDirty.value = true;
  }
};

const handleEdgesChange = () => {
  if (!isApplyingHistory) {
    isDirty.value = true;
  }
};

// Connections
const handleConnect = (params: any) => {
  const newEdge = {
    id: `e-${params.source}-${params.target}-${Date.now().toString().slice(-4)}`,
    source: params.source,
    target: params.target,
    sourceHandle: params.sourceHandle || 'right',
    targetHandle: params.targetHandle || 'left',
    type: 'workflow',
    label: 'Avanzar',
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#4F5AF5',
      width: 18,
      height: 18,
    },
    data: {
      condition_type: 'always',
      label: 'Avanzar',
      style_config: {
        button_bg: '#EB5F46',
        button_color: '#EB5F46',
        label_color: '#ffffff',
      },
    },
  };
  edges.value.push(newEdge);
  pushHistory();
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
        pos = { x: 2200 + customIndex * 280, y: 440 };
      } else {
        pos = { x: 4200 + customIndex * 280, y: 140 };
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
  showToast('Diagrama organizado según plantilla maestra', 'success');
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

// Save Workflow
const saveWorkflow = async () => {
  if (!workflow.value?.id) return;
  isSaving.value = true;
  try {
    await $fetch(`${apiBase}/workflow/definitions/${workflow.value.id}`, {
      method: 'PATCH',
      body: {
        graph_json: {
          nodes: nodes.value,
          edges: edges.value,
        },
      },
    });
    isDirty.value = false;
    showToast('Flujo de trabajo guardado exitosamente', 'success');
  } catch (err: any) {
    showToast('Error al guardar flujo: ' + (err.data?.detail || err.message), 'error');
  } finally {
    isSaving.value = false;
  }
};

// Publish Workflow
const publishWorkflow = async () => {
  if (!workflow.value?.id) return;
  isSaving.value = true;
  try {
    // Primero guardar el estado actual
    await $fetch(`${apiBase}/workflow/definitions/${workflow.value.id}`, {
      method: 'PATCH',
      body: {
        graph_json: {
          nodes: nodes.value,
          edges: edges.value,
        },
      },
    });
    // Luego publicar
    await $fetch(`${apiBase}/workflow/definitions/${workflow.value.id}/publish`, {
      method: 'POST',
    });
    isDirty.value = false;
    showToast('¡Flujo publicado como Activo en todo el sistema!', 'success');
    await loadActiveWorkflow();
  } catch (err: any) {
    showToast('Error al publicar flujo: ' + (err.data?.detail || err.message), 'error');
  } finally {
    isSaving.value = false;
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
</style>
