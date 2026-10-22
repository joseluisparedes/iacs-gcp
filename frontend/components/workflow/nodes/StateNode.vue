<script setup lang="ts">
import { computed } from 'vue';
import { Handle, Position } from '@vue-flow/core';
import { Layers, PlayCircle, CheckCircle2, AlertTriangle, Archive } from 'lucide-vue-next';

const props = defineProps<{
  id: string;
  data: any;
  selected?: boolean;
}>();

const nodeData = computed(() => props.data || {});
const isStart = computed(() => nodeData.value.nodeType === 'start' || props.id === 'start');
const isEnd = computed(() => nodeData.value.nodeType === 'end' || props.id === 'end');
const label = computed(() => nodeData.value.label || (isStart.value ? 'Inicio' : isEnd.value ? 'Fin' : 'Estado'));
const subtype = computed(() => (nodeData.value.stateSubtype as string) || '');
const isDemanda = computed(() => subtype.value === 'demanda' || label.value.toLowerCase().includes('demanda') || props.id === 'planificacion');
const isDesestimada = computed(() => subtype.value === 'desestimada' || label.value.toLowerCase().includes('desestimada') || props.id === 'desestimada');
const isObservada = computed(() => subtype.value === 'observada' || label.value.toLowerCase().includes('observada') || props.id === 'observada');

const badgeStyle = computed(() => {
  if (isStart.value || isDemanda.value) return 'bg-emerald-100 text-emerald-800 border-emerald-300';
  if (isDesestimada.value) return 'bg-rose-100 text-rose-800 border-rose-300';
  if (isObservada.value) return 'bg-amber-100 text-amber-800 border-amber-300';
  return 'bg-indigo-50 text-indigo-700 border-indigo-200';
});

const handleVisibleClass = computed(() =>
  props.selected
    ? 'opacity-100 scale-100 pointer-events-auto ring-2 ring-indigo-300'
    : 'opacity-0 scale-90 pointer-events-none group-hover:opacity-100 group-hover:scale-100 group-hover:pointer-events-auto transition-all duration-150'
);
</script>

<template>
  <div
    :class="[
      'relative w-[260px] rounded-xl bg-white shadow-sm border transition-all duration-150 group select-none text-left',
      selected ? 'ring-2 ring-[#4F5AF5] border-[#4F5AF5] shadow-md' : 'border-slate-200 hover:border-slate-300 hover:shadow-md'
    ]"
  >
    <!-- Top Handles -->
    <Handle
      type="target"
      :position="Position.Top"
      id="top-left"
      style="left: 25%"
      :class="['!w-3.5 !h-3.5 !bg-[#4F5AF5] !border-2 !border-white shadow-sm hover:!scale-150 !transition-all z-30', handleVisibleClass]"
      title="Conexión Superior Izquierda"
    />
    <Handle
      type="target"
      :position="Position.Top"
      id="top"
      style="left: 50%"
      :class="['!w-4.5 !h-4.5 !bg-[#4F5AF5] !border-[3px] !border-white shadow-md hover:!scale-125 !transition-all z-30', handleVisibleClass]"
      title="Entrada Superior Centro (Retorno / Bucle)"
    />
    <Handle
      type="target"
      :position="Position.Top"
      id="top-right"
      style="left: 75%"
      :class="['!w-3.5 !h-3.5 !bg-[#4F5AF5] !border-2 !border-white shadow-sm hover:!scale-150 !transition-all z-30', handleVisibleClass]"
      title="Conexión Superior Derecha"
    />

    <!-- Left Handles (Inputs / Entradas) -->
    <Handle
      type="target"
      :position="Position.Left"
      id="left-top"
      style="top: 25%"
      :class="['!w-3.5 !h-3.5 !bg-[#4F5AF5] !border-2 !border-white shadow-sm hover:!scale-150 !transition-all z-30', handleVisibleClass]"
      title="Entrada Superior Izquierda"
    />
    <Handle
      type="target"
      :position="Position.Left"
      id="left"
      style="top: 50%"
      :class="['!w-4.5 !h-4.5 !bg-[#4F5AF5] !border-[3px] !border-white shadow-md hover:!scale-125 !transition-all z-30', handleVisibleClass]"
      title="Entrada Principal (Destino)"
    />
    <Handle
      type="target"
      :position="Position.Left"
      id="left-bottom"
      style="top: 75%"
      :class="['!w-3.5 !h-3.5 !bg-[#4F5AF5] !border-2 !border-white shadow-sm hover:!scale-150 !transition-all z-30', handleVisibleClass]"
      title="Entrada Inferior Izquierda"
    />


    <!-- Header con visualización de nombre completo sin truncado forzado -->
    <div class="flex items-start gap-2 px-3 py-2.5 border-b border-slate-100 bg-slate-50/70 rounded-t-xl">
      <div class="pt-0.5 shrink-0">
        <PlayCircle v-if="isStart" class="w-4 h-4 text-emerald-600" />
        <CheckCircle2 v-else-if="isEnd || isDemanda" class="w-4 h-4 text-emerald-600" />
        <Archive v-else-if="isDesestimada" class="w-4 h-4 text-rose-600" />
        <AlertTriangle v-else-if="isObservada" class="w-4 h-4 text-amber-600" />
        <Layers v-else class="w-4 h-4 text-[#4F5AF5]" />
      </div>

      <div class="flex-1 min-w-0 pr-1">
        <span
          class="font-semibold text-xs text-slate-800 leading-snug break-words block"
          :title="label"
        >
          {{ label }}
        </span>
      </div>

      <span :class="['text-[9px] px-1.5 py-0.5 rounded-full border font-medium shrink-0 self-start mt-0.5', badgeStyle]">
        {{ isStart ? 'Inicio' : isEnd ? 'Fin' : isObservada ? 'Observada' : isDesestimada ? 'Desestimada' : isDemanda ? 'En Demanda' : 'Estado' }}
      </span>
    </div>

    <!-- Body -->
    <div class="p-2.5 text-[11px] text-slate-600 space-y-1.5">
      <p
        v-if="nodeData.description"
        class="text-slate-500 text-[11px] leading-relaxed transition-all"
        :class="selected ? 'block' : 'line-clamp-2 group-hover:line-clamp-none'"
        :title="nodeData.description"
      >
        {{ nodeData.description }}
      </p>

      <!-- Roles list -->
      <div v-if="Array.isArray(nodeData.roles) && nodeData.roles.length > 0" class="flex flex-wrap gap-1 pt-1">
        <span
          v-for="(r, i) in nodeData.roles"
          :key="i"
          :class="[
            'text-[9px] px-1.5 py-0.5 rounded border font-medium flex items-center gap-1',
            r.can_edit ? 'bg-indigo-50 text-indigo-700 border-indigo-200' : 'bg-slate-100 text-slate-600 border-slate-200'
          ]"
          :title="`Rol: ${r.role_name} (${r.can_edit ? 'Edición Habilitada' : 'Solo Lectura'})`"
        >
          <span>{{ r.role_name }}</span>
          <span v-if="r.can_edit" class="text-[8px] text-indigo-500 font-bold">✏️</span>
        </span>
      </div>

      <!-- Badges de formulario o consentimiento si están configurados -->
      <div v-if="nodeData.form_id || nodeData.consent_id || nodeData.document_template_id || nodeData.allowManualStateMove" class="flex flex-wrap items-center gap-1 pt-0.5 text-[9px] text-slate-400">
        <span v-if="nodeData.form_id" class="bg-slate-100 text-slate-700 px-1.5 py-0.2 rounded border border-slate-200 font-mono" title="Formulario asociado">
          📋 Form
        </span>
        <span v-if="nodeData.consent_id" class="bg-amber-50 text-amber-700 px-1.5 py-0.2 rounded border border-amber-200 font-mono" title="Consentimiento asociado">
          ⚖️ Legal
        </span>
        <span v-if="nodeData.document_template_id" class="bg-rose-50 text-rose-700 px-1.5 py-0.2 rounded border border-rose-200 font-mono" title="Documento PDF asociado">
          📄 PDF
        </span>
        <span v-if="nodeData.allowManualStateMove" class="bg-purple-50 text-purple-700 px-1.5 py-0.2 rounded border border-purple-200 font-mono" title="Salto manual de estado habilitado">
          🔀 Salto
        </span>
      </div>
    </div>

    <!-- Right Handles (Outputs / Salidas) -->
    <Handle
      type="source"
      :position="Position.Right"
      id="right-top"
      style="top: 25%"
      :class="['!w-3.5 !h-3.5 !bg-[#4F5AF5] !border-2 !border-white shadow-sm hover:!scale-150 !transition-all z-30', handleVisibleClass]"
      title="Salida Superior Derecha"
    />
    <Handle
      type="source"
      :position="Position.Right"
      id="right"
      style="top: 50%"
      :class="['!w-4.5 !h-4.5 !bg-[#4F5AF5] !border-[3px] !border-white shadow-md hover:!scale-125 !transition-all z-30', handleVisibleClass]"
      title="Salida Principal (Origen)"
    />
    <Handle
      type="source"
      :position="Position.Right"
      id="right-bottom"
      style="top: 75%"
      :class="['!w-3.5 !h-3.5 !bg-[#4F5AF5] !border-2 !border-white shadow-sm hover:!scale-150 !transition-all z-30', handleVisibleClass]"
      title="Salida Inferior Derecha"
    />

    <!-- Bottom Handles (Outputs / Salidas hacia abajo: Observada, Desestimada) -->
    <Handle
      type="source"
      :position="Position.Bottom"
      id="bottom-left"
      style="left: 25%"
      :class="['!w-3.5 !h-3.5 !bg-[#4F5AF5] !border-2 !border-white shadow-sm hover:!scale-150 !transition-all z-30', handleVisibleClass]"
      title="Salida Inferior Izquierda"
    />
    <Handle
      type="source"
      :position="Position.Bottom"
      id="bottom"
      style="left: 50%"
      :class="['!w-4.5 !h-4.5 !bg-[#4F5AF5] !border-[3px] !border-white shadow-md hover:!scale-125 !transition-all z-30', handleVisibleClass]"
      title="Salida Inferior Principal"
    />
    <Handle
      type="source"
      :position="Position.Bottom"
      id="bottom-right"
      style="left: 75%"
      :class="['!w-3.5 !h-3.5 !bg-[#4F5AF5] !border-2 !border-white shadow-sm hover:!scale-150 !transition-all z-30', handleVisibleClass]"
      title="Salida Inferior Derecha"
    />

  </div>
</template>
