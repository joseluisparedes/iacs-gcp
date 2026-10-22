<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-[100] overflow-y-auto bg-slate-950/70 backdrop-blur-md flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-200"
    @click.self="$emit('close')"
  >
    <div
      class="bg-white rounded-2xl shadow-2xl max-w-4xl w-full border border-slate-200/90 overflow-hidden transform transition-all flex flex-col max-h-[90vh] my-auto animate-in zoom-in-95 duration-200 text-left"
    >
      <!-- ── HEADER INSTITUCIONAL ── -->
      <div class="px-6 py-4.5 bg-gradient-to-r from-[#0D253F] via-[#1E293B] to-[#0D253F] text-white flex items-center justify-between shrink-0 border-b border-slate-800 shadow-sm">
        <div class="flex items-center gap-3.5">
          <div class="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-indigo-300 shrink-0 shadow-inner">
            <Layers class="w-5 h-5 text-indigo-300" />
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h3 class="text-base font-bold text-white tracking-tight">
                Jerarquía de Macro-Etapas y Sub-Estados
              </h3>
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/30 text-indigo-200 font-mono font-semibold border border-indigo-400/30">
                Stepper Oficial
              </span>
            </div>
            <p class="text-xs text-slate-300/85 mt-0.5">
              Organiza los pasos principales del riel de avance y agrupa los sub-estados del flujo correspondientes a cada etapa.
            </p>
          </div>
        </div>

        <button
          type="button"
          @click="$emit('close')"
          class="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-white/10 transition-colors cursor-pointer"
          title="Cerrar ventana"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- ── BARRA RESUMEN DE ESTADÍSTICAS & BÚSQUEDA ── -->
      <div class="px-6 py-3 bg-slate-50 border-b border-slate-200/80 flex flex-wrap items-center justify-between gap-3 text-xs shrink-0">
        <!-- Indicadores de Conteo -->
        <div class="flex items-center gap-2 sm:gap-3 flex-wrap">
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 font-bold border border-indigo-200/80">
            <Layers class="w-3.5 h-3.5 text-indigo-600" />
            <span>{{ localStages.length }} Macro-Etapas</span>
          </span>

          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 font-bold border border-emerald-200/80">
            <GitCommit class="w-3.5 h-3.5 text-emerald-600" />
            <span>{{ totalSubStatesCount }} Sub-estados agrupados</span>
          </span>

          <span
            v-if="unassignedNodes.length > 0"
            class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-50 text-amber-700 font-bold border border-amber-200/80"
            title="Nodos del diagrama que no están asociados a ninguna etapa"
          >
            <AlertCircle class="w-3.5 h-3.5 text-amber-600" />
            <span>{{ unassignedNodes.length }} Independientes / Sueltos</span>
          </span>
        </div>

        <!-- Botones de Acción Rápida -->
        <div class="flex items-center gap-2">
          <button
            type="button"
            @click="toggleAllExpanded"
            class="px-2.5 py-1 text-[11px] font-semibold text-slate-600 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors cursor-pointer shadow-2xs"
          >
            {{ allExpanded ? 'Contraer todo' : 'Expandir todo' }}
          </button>
          <button
            type="button"
            @click="restoreDefaults"
            class="px-2.5 py-1 text-[11px] font-semibold text-slate-600 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors cursor-pointer shadow-2xs flex items-center gap-1"
            title="Restaurar las 7 etapas oficiales de IACS"
          >
            <RotateCcw class="w-3 h-3 text-slate-500" />
            <span>Restaurar Estándar</span>
          </button>
        </div>
      </div>

      <!-- ── BODY PRINCIPAL SCROLLABLE ── -->
      <div class="p-6 overflow-y-auto space-y-4 flex-1 custom-scrollbar bg-slate-50/50">

        <!-- Lista de Macro-Etapas -->
        <div class="space-y-3.5">
          <div
            v-for="(stage, idx) in localStages"
            :key="stage.id || idx"
            class="bg-white border rounded-xl transition-all shadow-xs overflow-hidden"
            :class="isStageExpanded(idx) ? 'border-indigo-300 ring-1 ring-indigo-100' : 'border-slate-200 hover:border-slate-300'"
          >
            <!-- Header de la Tarjeta de Etapa -->
            <div
              class="px-4 py-3 bg-white flex items-center justify-between gap-3 cursor-pointer select-none border-b"
              :class="isStageExpanded(idx) ? 'border-slate-100 bg-slate-50/40' : 'border-transparent'"
              @click="toggleStageExpanded(idx)"
            >
              <!-- Izquierda: Número de Orden, Nombre y Sub-estados conteo -->
              <div class="flex items-center gap-3 min-w-0 flex-1">
                <span class="w-7 h-7 rounded-lg bg-[#0D253F] text-white font-extrabold text-xs flex items-center justify-center shrink-0 shadow-2xs">
                  {{ idx + 1 }}
                </span>

                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span class="text-sm font-bold text-slate-900 truncate">
                      {{ stage.name || `Etapa ${idx + 1}` }}
                    </span>
                    <span class="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium border border-slate-200">
                      {{ stage.role || 'Sin rol asignado' }}
                    </span>
                    <span
                      class="text-[10px] px-2 py-0.5 rounded-full font-bold border"
                      :class="getSubNodesForStage(stage).length > 0 ? 'bg-indigo-50 text-indigo-700 border-indigo-200' : 'bg-slate-50 text-slate-400 border-slate-200'"
                    >
                      {{ getSubNodesForStage(stage).length }} sub-estado{{ getSubNodesForStage(stage).length !== 1 ? 's' : '' }}
                    </span>
                  </div>

                  <!-- Subtítulo con el nodo cabecera -->
                  <p class="text-[11px] text-slate-500 truncate mt-0.5">
                    Cabecera principal: <strong class="text-slate-700">{{ getNodeLabel(stage.id) }}</strong>
                    <span class="text-slate-400 text-[10px] font-mono">({{ stage.id }})</span>
                  </p>
                </div>
              </div>

              <!-- Derecha: Acciones (Mover arriba/abajo, Eliminar, Expandir) -->
              <div class="flex items-center gap-1 shrink-0" @click.stop>
                <button
                  type="button"
                  @click="moveUp(idx)"
                  :disabled="idx === 0"
                  class="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 disabled:opacity-25 disabled:hover:bg-transparent transition-colors cursor-pointer"
                  title="Mover arriba"
                >
                  <ArrowUp class="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  @click="moveDown(idx)"
                  :disabled="idx === localStages.length - 1"
                  class="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 disabled:opacity-25 disabled:hover:bg-transparent transition-colors cursor-pointer"
                  title="Mover abajo"
                >
                  <ArrowDown class="w-3.5 h-3.5" />
                </button>
                <div class="w-px h-4 bg-slate-200 mx-1"></div>
                <button
                  type="button"
                  @click="removeStage(idx)"
                  :disabled="localStages.length <= 1"
                  class="p-1.5 rounded-lg text-rose-500 hover:text-rose-700 hover:bg-rose-50 disabled:opacity-25 disabled:hover:bg-transparent transition-colors cursor-pointer"
                  title="Eliminar esta macro-etapa"
                >
                  <Trash2 class="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  @click="toggleStageExpanded(idx)"
                  class="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer ml-0.5"
                >
                  <ChevronDown
                    class="w-4 h-4 transition-transform duration-200"
                    :class="isStageExpanded(idx) ? 'rotate-180 text-indigo-600' : ''"
                  />
                </button>
              </div>
            </div>

            <!-- Cuerpo Expandido de la Etapa -->
            <div v-show="isStageExpanded(idx)" class="p-4 bg-white border-t border-slate-100 space-y-4 animate-in fade-in duration-150">
              <!-- Fila 1: Configuración de la Etapa Principal (3 Columnas Amplias) -->
              <div class="grid grid-cols-1 md:grid-cols-12 gap-3 text-xs">
                <!-- 1. Nombre Visible -->
                <div class="md:col-span-4 space-y-1">
                  <label class="block text-[10px] font-bold uppercase tracking-wider text-slate-600">
                    Nombre en el Stepper
                  </label>
                  <input
                    type="text"
                    v-model="stage.name"
                    placeholder="ej: Estimación, Viabilidad..."
                    class="w-full px-3 py-2 bg-slate-50/50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                  />
                </div>

                <!-- 2. Rol Responsable -->
                <div class="md:col-span-4 space-y-1">
                  <label class="block text-[10px] font-bold uppercase tracking-wider text-slate-600">
                    Rol Responsable
                  </label>
                  <input
                    type="text"
                    v-model="stage.role"
                    placeholder="ej: Business Partner, Key User..."
                    class="w-full px-3 py-2 bg-slate-50/50 border border-slate-200 rounded-lg text-xs text-slate-700 focus:bg-white focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                  />
                </div>

                <!-- 3. Nodo Cabecera / Principal -->
                <div class="md:col-span-4 space-y-1">
                  <label class="block text-[10px] font-bold uppercase tracking-wider text-slate-600 flex items-center justify-between">
                    <span>Nodo Cabecera Principal</span>
                    <span class="text-[9px] text-indigo-600 font-semibold lowercase">hito principal</span>
                  </label>
                  <select
                    v-model="stage.id"
                    @change="onStageIdChange(stage, $event)"
                    class="w-full px-3 py-2 bg-slate-50/50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:bg-white focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                  >
                    <option value="" disabled>Seleccionar nodo principal...</option>
                    <option
                      v-for="node in availableHeaderNodes(stage)"
                      :key="node.id"
                      :value="node.id"
                    >
                      {{ node.data?.label || node.id }} ({{ node.id }})
                    </option>
                  </select>
                </div>
              </div>

              <!-- Fila 2: Sub-estados subordinados a esta etapa con Roles y Reordenación -->
              <div class="p-3.5 bg-slate-50/80 rounded-xl border border-slate-200/80 space-y-3">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-1.5">
                    <GitCommit class="w-4 h-4 text-indigo-600" />
                    <span class="text-xs font-bold text-slate-800">
                      Sub-estados agrupados en esta Macro-Etapa ({{ getSubNodesForStage(stage).length }})
                    </span>
                  </div>
                  <span class="text-[10px] text-slate-400">
                    Avanzan la iniciativa dentro de este paso. Ordena la secuencia y asigna su rol responsable.
                  </span>
                </div>

                <!-- Lista de Sub-estados asignados (con Orden y Rol Responsable) -->
                <div v-if="getSubNodesForStage(stage).length > 0" class="space-y-2">
                  <div
                    v-for="(subNodeId, sIdx) in getSubNodesForStage(stage)"
                    :key="subNodeId"
                    class="flex flex-wrap sm:flex-nowrap items-center justify-between gap-2.5 p-2.5 rounded-xl bg-white border border-slate-200 hover:border-indigo-300 transition-all shadow-2xs group/sub"
                  >
                    <!-- Izquierda: Número de Orden + Nombre + ID -->
                    <div class="flex items-center gap-2.5 min-w-0 flex-1">
                      <span class="w-6 h-6 rounded-lg bg-indigo-50 text-indigo-700 font-extrabold text-[11px] flex items-center justify-center shrink-0 border border-indigo-200 shadow-2xs">
                        {{ sIdx + 1 }}
                      </span>
                      <div class="min-w-0 flex-1">
                        <span class="text-xs font-bold text-slate-900 truncate block" :title="getNodeLabel(subNodeId)">
                          {{ getNodeLabel(subNodeId) }}
                        </span>
                        <span class="text-[10px] font-mono text-slate-400">ID: {{ subNodeId }}</span>
                      </div>
                    </div>

                    <!-- Centro: Rol Responsable del Sub-estado -->
                    <div class="flex items-center gap-1.5 w-full sm:w-auto shrink-0">
                      <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider shrink-0">Rol:</span>
                      <input
                        type="text"
                        :value="getSubRole(stage, subNodeId)"
                        @input="setSubRole(stage, subNodeId, ($event.target as HTMLInputElement).value)"
                        placeholder="ej: Business Partner, Líder Dominio..."
                        class="w-full sm:w-52 px-2.5 py-1 text-xs bg-slate-50/70 border border-slate-200 rounded-lg text-slate-700 focus:bg-white focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all font-medium placeholder:text-slate-400"
                        title="Rol responsable de este sub-estado"
                      />
                    </div>

                    <!-- Derecha: Botones para Reordenar (Arriba/Abajo) y Eliminar -->
                    <div class="flex items-center gap-1 shrink-0 ml-auto sm:ml-0">
                      <button
                        type="button"
                        @click="moveSubNode(stage, sIdx, -1)"
                        :disabled="sIdx === 0"
                        class="p-1 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 disabled:opacity-20 disabled:hover:bg-transparent transition-colors cursor-pointer"
                        title="Mover antes en el orden"
                      >
                        <ArrowUp class="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        @click="moveSubNode(stage, sIdx, 1)"
                        :disabled="sIdx === getSubNodesForStage(stage).length - 1"
                        class="p-1 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 disabled:opacity-20 disabled:hover:bg-transparent transition-colors cursor-pointer"
                        title="Mover después en el orden"
                      >
                        <ArrowDown class="w-3.5 h-3.5" />
                      </button>
                      <div class="w-px h-3.5 bg-slate-200 mx-0.5"></div>
                      <button
                        type="button"
                        @click="removeSubNodeFromStage(stage, subNodeId)"
                        class="p-1 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
                        title="Desasociar este sub-estado"
                      >
                        <X class="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Mensaje si no tiene sub-estados -->
                <div
                  v-else
                  class="p-3 bg-white rounded-xl border border-dashed border-slate-200 text-xs text-slate-400 italic text-center"
                >
                  No tiene sub-estados subordinados (solo ejecuta el nodo cabecera principal).
                </div>

                <!-- Selector para agregar un nuevo sub-estado a esta etapa -->
                <div class="pt-1 flex items-center gap-2">
                  <div class="relative flex-1 max-w-sm">
                    <select
                      :value="''"
                      @change="onAddSubNodeSelect(stage, $event)"
                      class="w-full px-2.5 py-1.5 bg-white border border-dashed border-indigo-300 hover:border-indigo-400 rounded-lg text-xs font-medium text-indigo-700 hover:text-indigo-900 focus:ring-1 focus:ring-indigo-500 transition-all cursor-pointer"
                    >
                      <option value="" selected>+ Asociar un sub-estado a {{ stage.name || 'esta etapa' }}...</option>
                      <option
                        v-for="node in getAvailableSubNodesForStage(stage)"
                        :key="node.id"
                        :value="node.id"
                      >
                        {{ node.data?.label || node.id }} ({{ node.id }})
                      </option>
                    </select>
                  </div>
                  <span class="text-[10px] text-slate-400">
                    Solo muestra nodos disponibles del diagrama
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ── SECCIÓN DE ESTADOS INDEPENDIENTES / SIN AGRUPAR ── -->
        <div
          v-if="unassignedNodes.length > 0"
          class="p-4 bg-amber-50/70 border border-amber-200/80 rounded-xl space-y-2.5"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <AlertCircle class="w-4 h-4 text-amber-600 shrink-0" />
              <span class="text-xs font-bold text-amber-950">
                Estados Independientes o Transversales ({{ unassignedNodes.length }})
              </span>
            </div>
            <span class="text-[10px] text-amber-800/80">
              No pertenecen a ninguna etapa secuencial (ej: Observada, Desestimada)
            </span>
          </div>

          <div class="flex flex-wrap items-center gap-2 pt-1">
            <div
              v-for="uNode in unassignedNodes"
              :key="uNode.id"
              class="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-white border border-amber-200 text-slate-800 shadow-2xs"
            >
              <span class="w-2 h-2 rounded-full bg-amber-500"></span>
              <span class="font-bold">{{ uNode.data?.label || uNode.id }}</span>
              <span class="text-[10px] font-mono text-slate-400">({{ uNode.id }})</span>

              <!-- Selector rápido para asociar a una etapa si se desea -->
              <div class="border-l border-slate-200 pl-1.5 ml-1 flex items-center">
                <select
                  :value="''"
                  @change="onQuickAssignUnassigned(uNode.id, $event)"
                  class="text-[10px] font-semibold text-indigo-600 bg-transparent border-0 hover:underline cursor-pointer focus:ring-0 p-0"
                  title="Mover este estado como sub-estado de una etapa"
                >
                  <option value="" selected>Mover a etapa...</option>
                  <option
                    v-for="(stg, sIdx) in localStages"
                    :key="stg.id"
                    :value="stg.id"
                  >
                    {{ sIdx + 1 }}. {{ stg.name }}
                  </option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- Botón para añadir nueva macro-etapa -->
        <div class="pt-2">
          <button
            type="button"
            @click="addStage"
            class="w-full py-2.5 border-2 border-dashed border-indigo-200 hover:border-indigo-400 hover:bg-indigo-50/50 rounded-xl text-xs font-bold text-indigo-700 flex items-center justify-center gap-2 transition-all cursor-pointer"
          >
            <Plus class="w-4 h-4 text-indigo-600" />
            <span>Agregar Nueva Macro-Etapa al Stepper</span>
          </button>
        </div>
      </div>

      <!-- ── FOOTER ELEGANTE ── -->
      <div class="px-6 py-4 bg-slate-50 border-t border-slate-200/90 flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div class="flex items-center gap-2 text-xs text-slate-500 font-medium">
          <span class="font-bold text-slate-800">{{ localStages.length }}</span> etapas configuradas
          <span class="text-slate-300">•</span>
          <span class="font-bold text-slate-800">{{ totalSubStatesCount }}</span> sub-estados agrupados
          <span class="text-slate-300">•</span>
          <span class="text-slate-600 font-semibold">Sincronización automática de jerarquía</span>
        </div>

        <div class="flex items-center gap-2.5">
          <button
            type="button"
            @click="$emit('close')"
            class="px-4 py-2 text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-200/70 rounded-xl transition-colors cursor-pointer"
          >
            Cancelar
          </button>
          <button
            type="button"
            @click="handleSave"
            class="px-5 py-2 text-xs font-bold text-white bg-gradient-to-r from-[#EB5F46] to-[#d64f38] hover:from-[#d64f38] hover:to-[#bd412c] rounded-xl transition-all shadow-sm hover:shadow cursor-pointer flex items-center gap-1.5 transform active:scale-95"
          >
            <Check class="w-3.5 h-3.5" />
            <span>Guardar Configuración de Etapas</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import {
  Layers,
  X,
  ArrowUp,
  ArrowDown,
  Trash2,
  Plus,
  RotateCcw,
  Check,
  GitCommit,
  AlertCircle,
  ChevronDown
} from 'lucide-vue-next';
import { DEFAULT_MACRO_STAGES, type MacroStageDef } from '~/utils/macroStages';

const props = defineProps<{
  isOpen: boolean;
  macroStages?: MacroStageDef[];
  nodes?: any[];
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'save', stages: MacroStageDef[]): void;
}>();

const localStages = ref<MacroStageDef[]>([]);
const expandedStages = ref<Record<number, boolean>>({});

// Set de IDs reales de nodos que existen actualmente en el diagrama del canvas
const realNodeIdsSet = computed(() => {
  return new Set((props.nodes || []).map((n: any) => n.id));
});

// Todos los nodos válidos de estado (excluyendo compuertas lógicas gateway)
const allValidNodes = computed(() => {
  return (props.nodes || []).filter(
    (n: any) => n.type !== 'gateway' && !n.id.startsWith('gw_')
  );
});

// Obtener etiqueta legible de un nodo
const getNodeLabel = (nodeId: string): string => {
  const node = (props.nodes || []).find((n: any) => n.id === nodeId);
  return node?.data?.label || nodeId;
};

// Sincronizar estado local al abrir
watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      let baseStages: MacroStageDef[] = [];
      if (Array.isArray(props.macroStages) && props.macroStages.length > 0) {
        baseStages = JSON.parse(JSON.stringify(props.macroStages));
      } else {
        baseStages = JSON.parse(JSON.stringify(DEFAULT_MACRO_STAGES));
      }

      // Reconciliar sub-estados desde los nodos (data.parent_stage_id)
      const parentToNodesMap = new Map<string, Set<string>>();
      (props.nodes || []).forEach((n: any) => {
        const parentId = n.data?.parent_stage_id;
        if (parentId) {
          if (!parentToNodesMap.has(parentId)) {
            parentToNodesMap.set(parentId, new Set());
          }
          parentToNodesMap.get(parentId)!.add(n.id);
        }
      });

      // Asegurar que cada stage tenga únicamente nodos válidos y existentes en el diagrama
      baseStages.forEach((stg) => {
        const nodeSet = new Set<string>();
        if (!stg.subRoles) stg.subRoles = {};

        // Mantener solo IDs que realmente existan en el diagrama actual
        (stg.nodeIds || []).forEach(nid => {
          if (realNodeIdsSet.value.has(nid)) {
            nodeSet.add(nid);
          }
        });

        // Asegurar que el id cabecera esté presente si existe en los nodos
        if (stg.id && realNodeIdsSet.value.has(stg.id)) {
          nodeSet.add(stg.id);
        }

        // Añadir sub-estados que tengan parent_stage_id apuntando a esta etapa
        if (parentToNodesMap.has(stg.id)) {
          parentToNodesMap.get(stg.id)!.forEach(nid => {
            if (realNodeIdsSet.value.has(nid)) {
              nodeSet.add(nid);
            }
          });
        }

        // Separar cabecera de sub-estados para ordenar según sub_stage_order si existe
        const headerId = stg.id;
        const subIds = Array.from(nodeSet).filter(nid => nid !== headerId);
        
        // Ordenar subIds si los nodos tienen sub_stage_order configurado
        subIds.sort((a, b) => {
          const nodeA = (props.nodes || []).find((n: any) => n.id === a);
          const nodeB = (props.nodes || []).find((n: any) => n.id === b);
          const orderA = Number(nodeA?.data?.sub_stage_order) || 999;
          const orderB = Number(nodeB?.data?.sub_stage_order) || 999;
          return orderA - orderB;
        });

        stg.nodeIds = headerId ? [headerId, ...subIds] : subIds;

        // Pre-poblar subRoles desde los datos del nodo si no tiene definido
        stg.nodeIds.forEach(nid => {
          if (!stg.subRoles![nid]) {
            const nodeObj = (props.nodes || []).find((n: any) => n.id === nid);
            if (nodeObj?.data?.sub_stage_role) {
              stg.subRoles![nid] = nodeObj.data.sub_stage_role;
            } else if (nodeObj?.data?.roles?.[0]?.role_name) {
              stg.subRoles![nid] = nodeObj.data.roles[0].role_name;
            } else if (nodeObj?.data?.role) {
              stg.subRoles![nid] = nodeObj.data.role;
            }
          }
        });
      });

      localStages.value = baseStages;

      // Expandir todas las etapas por defecto para máxima claridad
      const exp: Record<number, boolean> = {};
      baseStages.forEach((_, idx) => { exp[idx] = true; });
      expandedStages.value = exp;
    }
  },
  { immediate: true }
);

// Toggle de acordeón
const isStageExpanded = (idx: number) => {
  return expandedStages.value[idx] ?? true;
};

const toggleStageExpanded = (idx: number) => {
  expandedStages.value[idx] = !isStageExpanded(idx);
};

const allExpanded = computed(() => {
  return localStages.value.length > 0 && localStages.value.every((_, idx) => isStageExpanded(idx));
});

const toggleAllExpanded = () => {
  const target = !allExpanded.value;
  const exp: Record<number, boolean> = {};
  localStages.value.forEach((_, idx) => { exp[idx] = target; });
  expandedStages.value = exp;
};

// Sub-estados pertenecientes a una etapa (excluyendo el nodo cabecera principal y filtrando solo nodos reales del diagrama)
const getSubNodesForStage = (stage: MacroStageDef): string[] => {
  if (!Array.isArray(stage.nodeIds)) return [];
  return stage.nodeIds.filter(nid => nid !== stage.id && realNodeIdsSet.value.has(nid));
};

// Total de sub-estados agrupados
const totalSubStatesCount = computed(() => {
  let count = 0;
  localStages.value.forEach(stg => {
    count += getSubNodesForStage(stg).length;
  });
  return count;
});

// Nodos disponibles para ser cabecera principal de una etapa
const availableHeaderNodes = (stage: MacroStageDef) => {
  // Excluye nodos que ya son cabecera de OTRA etapa
  const otherHeaderIds = new Set(
    localStages.value.filter(s => s !== stage).map(s => s.id)
  );
  return allValidNodes.value.filter(n => !otherHeaderIds.has(n.id));
};

// Nodos disponibles para ser agregados como sub-estado de una etapa
const getAvailableSubNodesForStage = (stage: MacroStageDef) => {
  const currentAssigned = new Set<string>(stage.nodeIds || []);
  currentAssigned.add(stage.id);

  // También excluir nodos que son cabecera de cualquier etapa
  const allHeaderIds = new Set(localStages.value.map(s => s.id));

  return allValidNodes.value.filter(
    n => !currentAssigned.has(n.id) && !allHeaderIds.has(n.id)
  );
};

// Nodos independientes que no pertenecen a ninguna etapa ni como cabecera ni como sub-estado
const unassignedNodes = computed(() => {
  const assigned = new Set<string>();
  localStages.value.forEach(stg => {
    if (realNodeIdsSet.value.has(stg.id)) {
      assigned.add(stg.id);
    }
    (stg.nodeIds || []).forEach(nid => {
      if (realNodeIdsSet.value.has(nid)) {
        assigned.add(nid);
      }
    });
  });
  return allValidNodes.value.filter(n => !assigned.has(n.id));
});

// Gestión de Roles y Orden de Sub-estados
const getSubRole = (stage: MacroStageDef, nodeId: string): string => {
  if (stage.subRoles && stage.subRoles[nodeId]) {
    return stage.subRoles[nodeId];
  }
  const node = (props.nodes || []).find((n: any) => n.id === nodeId);
  return node?.data?.sub_stage_role || node?.data?.roles?.[0]?.role_name || node?.data?.role || '';
};

const setSubRole = (stage: MacroStageDef, nodeId: string, role: string) => {
  if (!stage.subRoles) stage.subRoles = {};
  stage.subRoles[nodeId] = role;
};

// Reordenar sub-estados dentro de la etapa
const moveSubNode = (stage: MacroStageDef, currentSubIdx: number, direction: number) => {
  const subNodes = getSubNodesForStage(stage);
  const targetSubIdx = currentSubIdx + direction;
  if (targetSubIdx < 0 || targetSubIdx >= subNodes.length) return;

  const movedId = subNodes[currentSubIdx];
  const targetId = subNodes[targetSubIdx];

  if (!Array.isArray(stage.nodeIds)) return;
  const idxA = stage.nodeIds.indexOf(movedId);
  const idxB = stage.nodeIds.indexOf(targetId);
  if (idxA !== -1 && idxB !== -1) {
    const temp = stage.nodeIds[idxA];
    stage.nodeIds[idxA] = stage.nodeIds[idxB];
    stage.nodeIds[idxB] = temp;
  }
};

// Cambiar nodo cabecera
const onStageIdChange = (stage: MacroStageDef, e: Event) => {
  const newId = (e.target as HTMLSelectElement).value;
  if (!newId) return;
  const oldId = stage.id;
  stage.id = newId;
  if (!stage.nodeIds) stage.nodeIds = [];
  // Asegurar que el nuevo id esté en nodeIds y remover el viejo si era solo cabecera
  if (!stage.nodeIds.includes(newId)) {
    stage.nodeIds.unshift(newId);
  }
};

// Agregar un sub-estado a una etapa
const onAddSubNodeSelect = (stage: MacroStageDef, e: Event) => {
  const target = e.target as HTMLSelectElement;
  const nodeId = target.value;
  if (!nodeId) return;

  if (!stage.nodeIds) stage.nodeIds = [stage.id];

  // Si este nodo estaba asignado a otra etapa, desasociarlo de ella
  localStages.value.forEach(s => {
    if (s !== stage && Array.isArray(s.nodeIds)) {
      s.nodeIds = s.nodeIds.filter(nid => nid !== nodeId);
      if (s.subRoles && s.subRoles[nodeId]) {
        delete s.subRoles[nodeId];
      }
    }
  });

  if (!stage.nodeIds.includes(nodeId)) {
    stage.nodeIds.push(nodeId);
  }

  // Pre-poblar rol del nuevo sub-nodo si existe
  if (!stage.subRoles) stage.subRoles = {};
  if (!stage.subRoles[nodeId]) {
    const nodeObj = (props.nodes || []).find((n: any) => n.id === nodeId);
    stage.subRoles[nodeId] = nodeObj?.data?.sub_stage_role || nodeObj?.data?.roles?.[0]?.role_name || nodeObj?.data?.role || '';
  }

  // Reset select
  target.value = '';
};

// Remover un sub-estado de una etapa
const removeSubNodeFromStage = (stage: MacroStageDef, nodeId: string) => {
  if (!Array.isArray(stage.nodeIds)) return;
  stage.nodeIds = stage.nodeIds.filter(nid => nid !== nodeId);
  if (stage.subRoles && stage.subRoles[nodeId]) {
    delete stage.subRoles[nodeId];
  }
};

// Asignación rápida de un nodo suelto a una etapa
const onQuickAssignUnassigned = (nodeId: string, e: Event) => {
  const target = e.target as HTMLSelectElement;
  const stageId = target.value;
  if (!stageId) return;

  const stage = localStages.value.find(s => s.id === stageId);
  if (stage) {
    if (!stage.nodeIds) stage.nodeIds = [stage.id];
    if (!stage.nodeIds.includes(nodeId)) {
      stage.nodeIds.push(nodeId);
    }
    if (!stage.subRoles) stage.subRoles = {};
    if (!stage.subRoles[nodeId]) {
      const nodeObj = (props.nodes || []).find((n: any) => n.id === nodeId);
      stage.subRoles[nodeId] = nodeObj?.data?.sub_stage_role || nodeObj?.data?.roles?.[0]?.role_name || nodeObj?.data?.role || '';
    }
  }
  target.value = '';
};

// Reordenar etapas
const moveUp = (idx: number) => {
  if (idx <= 0) return;
  const temp = localStages.value[idx];
  localStages.value[idx] = localStages.value[idx - 1];
  localStages.value[idx - 1] = temp;
};

const moveDown = (idx: number) => {
  if (idx >= localStages.value.length - 1) return;
  const temp = localStages.value[idx];
  localStages.value[idx] = localStages.value[idx + 1];
  localStages.value[idx + 1] = temp;
};

const removeStage = (idx: number) => {
  if (localStages.value.length <= 1) return;
  localStages.value.splice(idx, 1);
};

const addStage = () => {
  const nextNum = localStages.value.length + 1;
  const newId = `etapa_${Date.now().toString().slice(-4)}`;
  localStages.value.push({
    id: newId,
    name: `Nueva Etapa ${nextNum}`,
    role: 'Responsable',
    nodeIds: [newId],
    subRoles: {},
    statusKeywords: [],
  });
  expandedStages.value[localStages.value.length - 1] = true;
};

const restoreDefaults = () => {
  const defaults: MacroStageDef[] = JSON.parse(JSON.stringify(DEFAULT_MACRO_STAGES));
  defaults.forEach(stg => {
    stg.nodeIds = (stg.nodeIds || []).filter(nid => realNodeIdsSet.value.has(nid));
    if (realNodeIdsSet.value.has(stg.id) && !stg.nodeIds.includes(stg.id)) {
      stg.nodeIds.unshift(stg.id);
    }
  });
  localStages.value = defaults;
  const exp: Record<number, boolean> = {};
  localStages.value.forEach((_, idx) => { exp[idx] = true; });
  expandedStages.value = exp;
};

const handleSave = () => {
  // Asegurar que cada etapa tenga su id en nodeIds y solo contenga IDs reales del diagrama
  localStages.value.forEach(stg => {
    if (!stg.nodeIds) stg.nodeIds = [];
    if (stg.id && !stg.nodeIds.includes(stg.id) && realNodeIdsSet.value.has(stg.id)) {
      stg.nodeIds.unshift(stg.id);
    }
    // Filtrar cualquier ID fantasma que no exista en el canvas
    stg.nodeIds = stg.nodeIds.filter(nid => realNodeIdsSet.value.has(nid));

    // Limpiar subRoles para IDs que ya no estén
    if (stg.subRoles) {
      const cleanSubRoles: Record<string, string> = {};
      stg.nodeIds.forEach(nid => {
        if (stg.subRoles?.[nid]) {
          cleanSubRoles[nid] = stg.subRoles[nid];
        }
      });
      stg.subRoles = cleanSubRoles;
    }
  });

  emit('save', JSON.parse(JSON.stringify(localStages.value)));
  emit('close');
};
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f5f9;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
