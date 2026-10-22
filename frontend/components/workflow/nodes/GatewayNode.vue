<script setup lang="ts">
import { computed } from 'vue';
import { Handle, Position } from '@vue-flow/core';
import { GitFork } from 'lucide-vue-next';

const props = defineProps<{
  id: string;
  data: any;
  selected?: boolean;
}>();

const nodeData = computed(() => props.data || {});
const label = computed(() => nodeData.value.label || 'Compuerta Lógica');
const gatewayConfig = computed(() => nodeData.value.gatewayConfig || {});
const variable = computed(() => gatewayConfig.value.variable || (props.id === 'gw_presupuesto' ? 'requiere_presupuesto' : ''));
const rules = computed(() => gatewayConfig.value.rules || [
  { edgeId: 'e-gw-si', operator: 'equals', value: 'Sí', targetLabel: 'SÍ requiere presupuesto' },
  { edgeId: 'e-gw-no', operator: 'equals', value: 'No', targetLabel: 'NO requiere presupuesto' }
]);

const handleVisibleClass = computed(() =>
  props.selected
    ? 'opacity-100 scale-100 pointer-events-auto ring-2 ring-amber-300'
    : 'opacity-0 scale-90 pointer-events-none group-hover:opacity-100 group-hover:scale-100 group-hover:pointer-events-auto transition-all duration-150'
);
</script>

<template>
  <div
    :class="[
      'relative w-[280px] rounded-2xl bg-amber-50/95 border transition-all duration-150 group shadow-xs select-none text-left',
      selected ? 'ring-2 ring-amber-500 border-amber-500 shadow-md' : 'border-amber-300 hover:border-amber-400 hover:shadow-md'
    ]"
  >
    <!-- Top Handle (Input / Entrada Superior) -->
    <Handle
      type="target"
      :position="Position.Top"
      id="top"
      :class="['!w-4.5 !h-4.5 !bg-amber-500 !border-[3px] !border-white shadow-md z-30', handleVisibleClass]"
      title="Entrada Superior"
    />

    <!-- Left Handle (Input / Entrada Principal a la Compuerta) -->
    <Handle
      type="target"
      :position="Position.Left"
      id="left"
      :class="['!w-4.5 !h-4.5 !bg-amber-500 !border-[3px] !border-white shadow-md z-30', handleVisibleClass]"
      title="Entrada Principal (Destino)"
    />

    <!-- Header -->
    <div class="flex items-start gap-2 px-3.5 py-2.5 border-b border-amber-200/80 bg-gradient-to-r from-amber-100/90 to-orange-100/60 rounded-t-2xl">
      <div class="w-5 h-5 rounded-md bg-amber-200/80 flex items-center justify-center text-amber-800 shrink-0 mt-0.5">
        <GitFork class="w-3.5 h-3.5 text-amber-800 shrink-0" />
      </div>
      <div class="flex-1 min-w-0 pr-1">
        <span class="font-bold text-xs text-amber-950 leading-snug break-words block" :title="label">
          {{ label }}
        </span>
      </div>
      <span class="text-[9px] bg-amber-200/90 text-amber-900 px-2 py-0.5 rounded-full border border-amber-300 font-bold shrink-0 self-start mt-0.5">
        Decisión
      </span>
    </div>

    <!-- Body: Lógica dinámica de bifurcación -->
    <div className="p-3 space-y-2 text-[10px] text-amber-900">
      <!-- Variable -->
      <div className="flex items-center justify-between pb-1.5 border-b border-amber-200/60 text-[10px]">
        <span className="text-amber-800 font-medium">Variable:</span>
        <span
          v-if="variable"
          class="bg-white px-2 py-0.5 rounded-md border border-amber-300/80 font-mono font-bold text-amber-950 truncate max-w-[150px] shadow-2xs"
          :title="variable"
        >
          {{ variable }}
        </span>
        <span v-else class="bg-amber-100/80 text-amber-700 px-1.5 py-0.5 rounded text-[9px] italic border border-dashed border-amber-300">
          Seleccionar en panel
        </span>
      </div>

      <!-- Ramas dinámicas -->
      <div className="space-y-1.5 pt-0.5">
        <div
          v-for="(rule, idx) in rules"
          :key="idx"
          class="flex items-center justify-between p-1.5 rounded-lg bg-white/90 border border-amber-200/90 shadow-2xs"
        >
          <span class="text-amber-950 font-medium truncate max-w-[130px]">
            {{ rule.targetLabel || rule.value || `Rama ${idx + 1}` }}
          </span>
          <span
            :class="[
              'px-2 py-0.5 rounded-md text-[9px] font-bold border',
              rule.value?.toLowerCase() === 'sí' || rule.value?.toLowerCase() === 'si'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : rule.value?.toLowerCase() === 'no'
                ? 'bg-blue-50 text-blue-700 border-blue-200'
                : 'bg-slate-100 text-slate-700 border-slate-200'
            ]"
          >
            = {{ rule.value || 'True' }}
          </span>
        </div>
      </div>
    </div>

    <!-- Right Handle (Branch output / Salida Rama Sí) -->
    <Handle
      type="source"
      :position="Position.Right"
      id="right"
      :class="['!w-4.5 !h-4.5 !bg-amber-500 !border-[3px] !border-white shadow-md z-30', handleVisibleClass]"
      title="Salida Lateral (Origen Rama Sí / Positiva)"
    />

    <!-- Bottom Handle (Branch output / Salida Rama No) -->
    <Handle
      type="source"
      :position="Position.Bottom"
      id="bottom"
      :class="['!w-4.5 !h-4.5 !bg-amber-500 !border-[3px] !border-white shadow-md z-30', handleVisibleClass]"
      title="Salida Inferior (Origen Rama No / Alternativa)"
    />
  </div>
</template>
