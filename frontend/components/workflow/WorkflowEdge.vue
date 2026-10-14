<script setup lang="ts">
import { computed } from 'vue';
import { BaseEdge, EdgeLabelRenderer, getSmoothStepPath, Position, useVueFlow } from '@vue-flow/core';
import { ArrowRight, X } from 'lucide-vue-next';

const props = defineProps<{
  id: string;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  sourcePosition: Position;
  targetPosition: Position;
  style?: any;
  markerEnd?: string;
  label?: string;
  selected?: boolean;
  data?: any;
}>();

const emit = defineEmits<{
  (e: 'select-edge', id: string): void;
}>();

const { removeEdges, findEdge } = useVueFlow();

const pathData = computed(() => {
  return getSmoothStepPath({
    sourceX: props.sourceX,
    sourceY: props.sourceY,
    sourcePosition: props.sourcePosition,
    targetX: props.targetX,
    targetY: props.targetY,
    targetPosition: props.targetPosition,
    borderRadius: 16,
  });
});

const edgePath = computed(() => pathData.value[0]);
const labelX = computed(() => pathData.value[1]);
const labelY = computed(() => pathData.value[2]);

const conditionType = computed(() => props.data?.condition_type);
const styleConfig = computed(() => props.data?.style_config || {});

const customBg = computed(() => styleConfig.value.button_bg);
const customColor = computed(() => styleConfig.value.button_color);
const customTextColor = computed(() => styleConfig.value.label_color);

const arrowColor = computed(() => {
  if (customColor.value) return customColor.value;
  if (props.selected) return '#4F5AF5';
  return props.style?.stroke || '#94a3b8';
});

const handleChipClick = (e: MouseEvent) => {
  e.stopPropagation();
  const edge = findEdge(props.id);
  if (edge) {
    edge.selected = true;
  }
  emit('select-edge', props.id);
};

const handleDelete = (e: MouseEvent) => {
  e.stopPropagation();
  removeEdges([props.id]);
};
</script>

<template>
  <svg
    style="position: absolute; width: 0; height: 0; pointer-events: none; overflow: hidden;"
    aria-hidden="true"
  >
    <defs>
      <marker
        :id="`wf-arrow-${id}`"
        viewBox="-10 -10 20 20"
        refX="0"
        refY="0"
        markerWidth="16"
        markerHeight="16"
        markerUnits="strokeWidth"
        orient="auto-start-reverse"
      >
        <polyline
          points="-5,-4 0,0 -5,4 -5,-4"
          :fill="arrowColor"
          :stroke="arrowColor"
          stroke-width="1"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </marker>
    </defs>
  </svg>

  <BaseEdge
    :path="edgePath"
    :marker-end="markerEnd || `url(#wf-arrow-${id})`"
    :interaction-width="selected ? 25 : 14"
    :style="{
      ...style,
      stroke: arrowColor,
      strokeWidth: selected ? 3 : 2,
      zIndex: selected ? 50 : 1,
      transition: 'stroke 0.2s, stroke-width 0.2s',
      filter: selected ? `drop-shadow(0 0 6px ${arrowColor})` : undefined,
    }"
  />

  <EdgeLabelRenderer>
    <div
      :style="{
        position: 'absolute',
        transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
        pointerEvents: 'all',
        zIndex: selected ? 100 : 10,
      }"
      class="nodrag nopan"
    >
      <!-- Chip interactivo que se convierte en el botón del flujo -->
      <div
        @click="handleChipClick"
        :style="{
          backgroundColor: customBg || '#FFFFFF',
          borderColor: customColor || (selected ? '#4F5AF5' : '#CBD5E1'),
          color: customTextColor || (customColor || (selected ? '#4F5AF5' : '#334155')),
        }"
        :class="[
          'flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold border shadow-xs transition-all cursor-pointer select-none group',
          selected
            ? 'ring-2 ring-offset-1 scale-105 shadow-md font-extrabold'
            : 'hover:scale-102 hover:shadow-sm'
        ]"
        :title="'Transición: ' + (label || 'Avanzar') + ' (Clic para configurar botón y roles)'"
      >
        <ArrowRight
          class="w-3 h-3 shrink-0 transition-transform group-hover:translate-x-0.5"
          :style="{ color: customTextColor || customColor || (selected ? '#4F5AF5' : '#64748B') }"
        />
        <span class="truncate max-w-[140px] font-semibold">
          {{ label || 'Avanzar' }}
        </span>

        <span
          v-if="conditionType && conditionType !== 'always'"
          class="text-[9px] px-1.5 py-0.2 bg-amber-100 text-amber-900 rounded font-mono font-bold"
        >
          {{ conditionType === 'field_required' ? 'Req' : conditionType === 'vobo_check' ? 'VoBo' : conditionType.includes('presupuesto') ? 'Cond' : 'Rol' }}
        </span>

        <!-- Botón circular rojo (x) para desconectar/eliminar -->
        <button
          type="button"
          @click="handleDelete"
          class="w-4 h-4 ml-0.5 rounded-full bg-red-500 hover:bg-red-600 text-white flex items-center justify-center transition-colors shadow-2xs"
          title="Eliminar o desconectar esta flecha"
        >
          <X class="w-2.5 h-2.5" />
        </button>
      </div>
    </div>
  </EdgeLabelRenderer>
</template>
