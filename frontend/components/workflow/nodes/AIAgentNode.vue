<script setup lang="ts">
import { computed } from 'vue';
import { Handle, Position } from '@vue-flow/core';
import { Sparkles, BrainCircuit } from 'lucide-vue-next';

const props = defineProps<{
  id: string;
  data: any;
  selected?: boolean;
}>();

const nodeData = computed(() => props.data || {});
const label = computed(() => nodeData.value.label || 'Asistente IA (Chat)');

const handleVisibleClass = computed(() =>
  props.selected
    ? 'opacity-100 scale-100 pointer-events-auto ring-2 ring-violet-300'
    : 'opacity-0 scale-90 pointer-events-none group-hover:opacity-100 group-hover:scale-100 group-hover:pointer-events-auto transition-all duration-150'
);
</script>

<template>
  <div
    :class="[
      'relative w-[260px] rounded-2xl bg-gradient-to-br from-violet-50/95 to-indigo-50/90 border transition-all duration-150 group shadow-xs select-none text-left',
      selected ? 'ring-2 ring-violet-500 border-violet-500 shadow-md' : 'border-violet-200 hover:border-violet-300 hover:shadow-md'
    ]"
  >
    <!-- Top Handle (Input / Entrada) -->
    <Handle
      type="target"
      :position="Position.Top"
      id="top"
      :class="['!w-4 !h-4 !bg-violet-600 !border-2 !border-white shadow-md z-30', handleVisibleClass]"
      title="Entrada Superior"
    />

    <!-- Left Handle (Input / Entrada) -->
    <Handle
      type="target"
      :position="Position.Left"
      id="left"
      :class="['!w-4 !h-4 !bg-violet-600 !border-2 !border-white shadow-md z-30', handleVisibleClass]"
      title="Entrada Principal (Destino)"
    />

    <div class="flex items-start gap-2 px-3 py-2.5 border-b border-violet-200/60 bg-violet-100/60 rounded-t-2xl">
      <div class="w-5 h-5 rounded-md bg-violet-200 flex items-center justify-center text-violet-700 shrink-0 mt-0.5">
        <Sparkles class="w-3.5 h-3.5 text-violet-700" />
      </div>
      <div class="flex-1 min-w-0 pr-1">
        <span class="font-bold text-xs text-violet-950 leading-snug break-words block" :title="label">
          {{ label }}
        </span>
      </div>
      <span class="text-[9px] bg-violet-200 text-violet-800 px-2 py-0.5 rounded-full font-bold shrink-0 self-start mt-0.5">
        Teo IA
      </span>
    </div>

    <div class="p-2.5 text-[11px] text-violet-900/80 leading-relaxed">
      <p
        class="transition-all"
        :class="selected ? 'block' : 'line-clamp-2 group-hover:line-clamp-none'"
        :title="nodeData.description"
      >
        {{ nodeData.description || 'Asistente conversacional inteligente que guía al usuario en la captura y depuración.' }}
      </p>
    </div>

    <!-- Right Handle (Output / Salida) -->
    <Handle
      type="source"
      :position="Position.Right"
      id="right"
      :class="['!w-4 !h-4 !bg-violet-600 !border-2 !border-white shadow-md z-30', handleVisibleClass]"
      title="Salida Principal (Origen)"
    />

    <!-- Bottom Handle (Output / Salida) -->
    <Handle
      type="source"
      :position="Position.Bottom"
      id="bottom"
      :class="['!w-4 !h-4 !bg-violet-600 !border-2 !border-white shadow-md z-30', handleVisibleClass]"
      title="Salida Inferior (Origen)"
    />
  </div>
</template>
