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
</script>

<template>
  <div
    :class="[
      'relative min-w-[210px] max-w-[250px] rounded-2xl bg-gradient-to-br from-violet-50/95 to-indigo-50/90 border transition-all duration-150 group shadow-xs select-none text-left',
      selected ? 'ring-2 ring-violet-500 border-violet-500 shadow-md' : 'border-violet-200 hover:border-violet-300'
    ]"
  >
    <!-- Top Handles (In & Out) -->
    <Handle
      type="target"
      :position="Position.Top"
      id="top"
      class="!w-4 !h-4 !bg-violet-600 !border-2 !border-white shadow-md z-30"
    />
    <Handle
      type="source"
      :position="Position.Top"
      id="top-out"
      class="!w-4 !h-4 !bg-violet-600 !border-2 !border-white shadow-md z-30"
    />

    <!-- Left Handles (In & Out) -->
    <Handle
      type="target"
      :position="Position.Left"
      id="left"
      class="!w-4 !h-4 !bg-violet-600 !border-2 !border-white shadow-md z-30"
    />
    <Handle
      type="source"
      :position="Position.Left"
      id="left-out"
      class="!w-4 !h-4 !bg-violet-600 !border-2 !border-white shadow-md z-30"
    />

    <div class="flex items-center gap-2 px-3 py-2 border-b border-violet-200/60 bg-violet-100/60 rounded-t-2xl">
      <div class="w-5 h-5 rounded-md bg-violet-200 flex items-center justify-center text-violet-700 shrink-0">
        <Sparkles class="w-3.5 h-3.5 text-violet-700" />
      </div>
      <span class="font-bold text-xs text-violet-950 truncate flex-1" :title="label">{{ label }}</span>
      <span class="text-[9px] bg-violet-200 text-violet-800 px-2 py-0.5 rounded-full font-bold">
        Teo IA
      </span>
    </div>

    <div class="p-2.5 text-[11px] text-violet-900/80 leading-tight">
      <p class="line-clamp-2">
        {{ nodeData.description || 'Asistente conversacional inteligente que guía al usuario en la captura y depuración.' }}
      </p>
    </div>

    <!-- Right Handles (In & Out) -->
    <Handle
      type="source"
      :position="Position.Right"
      id="right"
      class="!w-4 !h-4 !bg-violet-600 !border-2 !border-white shadow-md z-30"
    />
    <Handle
      type="target"
      :position="Position.Right"
      id="right-in"
      class="!w-4 !h-4 !bg-violet-600 !border-2 !border-white shadow-md z-30"
    />

    <!-- Bottom Handles (In & Out) -->
    <Handle
      type="source"
      :position="Position.Bottom"
      id="bottom"
      class="!w-4 !h-4 !bg-violet-600 !border-2 !border-white shadow-md z-30"
    />
    <Handle
      type="target"
      :position="Position.Bottom"
      id="bottom-in"
      class="!w-4 !h-4 !bg-violet-600 !border-2 !border-white shadow-md z-30"
    />
  </div>
</template>
