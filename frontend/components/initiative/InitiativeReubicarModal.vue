<script setup lang="ts">
import { ref } from 'vue';
import { Shuffle, X, ArrowRight } from 'lucide-vue-next';

const props = defineProps<{
  isOpen: boolean;
  currentStatus: string;
  availableNodes: Array<{ id: string; label: string }>;
  isSubmitting?: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'confirm', payload: { targetNodeId: string; targetStatus: string; reason: string }): void;
}>();

const targetNodeId = ref('');
const reason = ref('');

const handleConfirm = () => {
  if (!targetNodeId.value) {
    alert('Por favor selecciona el estado al cual deseas reubicar la iniciativa.');
    return;
  }
  if (!reason.value.trim()) {
    alert('Debes ingresar el motivo o justificación del salto de estado.');
    return;
  }

  const selectedNode = props.availableNodes.find(n => n.id === targetNodeId.value);
  const targetLabel = selectedNode?.label || targetNodeId.value;

  emit('confirm', {
    targetNodeId: targetNodeId.value,
    targetStatus: targetLabel,
    reason: reason.value.trim(),
  });

  targetNodeId.value = '';
  reason.value = '';
};

const handleClose = () => {
  targetNodeId.value = '';
  reason.value = '';
  emit('close');
};
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150"
  >
    <div class="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4">
      <div class="flex items-center justify-between border-b border-slate-100 pb-3">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center font-bold">
            <Shuffle class="w-4 h-4 stroke-[2.5]" />
          </div>
          <div>
            <h3 class="font-bold text-slate-900 text-base">Reubicación Manual de Estado</h3>
            <p class="text-xs text-slate-400">Salto administrativo controlado con auditoría</p>
          </div>
        </div>
        <button
          type="button"
          @click="handleClose"
          class="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-50 transition-colors"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <div class="space-y-3.5">
        <div class="p-3 bg-purple-50/50 rounded-xl border border-purple-100 text-xs text-purple-900 flex items-center gap-2">
          <span>Estado Actual: <strong>{{ currentStatus }}</strong></span>
        </div>

        <div>
          <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Seleccionar Estado Destino
          </label>
          <select
            v-model="targetNodeId"
            class="w-full p-2.5 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-purple-600 focus:outline-none bg-white text-slate-800"
          >
            <option value="" disabled>Selecciona un estado...</option>
            <option
              v-for="node in availableNodes"
              :key="node.id"
              :value="node.id"
            >
              {{ node.label }} ({{ node.id }})
            </option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Motivo / Justificación del Salto de Estado (Obligatorio)
          </label>
          <textarea
            v-model="reason"
            placeholder="Ingresa la justificación formal o acuerdo gerencial por el cual se reubica la iniciativa..."
            rows="3"
            class="w-full p-3 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-purple-600 focus:outline-none resize-none leading-relaxed text-slate-800"
          />
        </div>
      </div>

      <div class="flex justify-end gap-2.5 pt-3 border-t border-slate-100">
        <button
          type="button"
          @click="handleClose"
          class="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
        >
          Cancelar
        </button>
        <button
          type="button"
          @click="handleConfirm"
          :disabled="isSubmitting || !targetNodeId || !reason.trim()"
          class="px-5 py-2 text-xs font-bold text-white bg-purple-700 hover:bg-purple-800 rounded-xl transition-colors shadow-2xs disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
        >
          <Shuffle class="w-3.5 h-3.5" />
          <span>{{ isSubmitting ? 'Reubicando...' : 'Confirmar Reubicación' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>
