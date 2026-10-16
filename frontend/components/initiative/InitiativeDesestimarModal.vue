<script setup lang="ts">
import { ref } from 'vue';
import { Ban, X } from 'lucide-vue-next';

const props = defineProps<{
  isOpen: boolean;
  isSubmitting?: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'confirm', reason: string): void;
}>();

const reason = ref('');

const handleConfirm = () => {
  if (!reason.value.trim()) {
    alert('Debes ingresar el motivo o dictamen de desestimación.');
    return;
  }
  emit('confirm', reason.value.trim());
  reason.value = '';
};

const handleClose = () => {
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
          <div class="w-8 h-8 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold">
            <Ban class="w-4 h-4 stroke-[2.5]" />
          </div>
          <div>
            <h3 class="font-bold text-slate-900 text-base">Desestimar Iniciativa</h3>
            <p class="text-xs text-slate-400">Dictamen formal de no viabilidad</p>
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
        <div class="p-3 bg-rose-50/50 rounded-xl border border-rose-100 text-xs text-rose-900">
          Esta acción desestimará formalmente el requerimiento y registrará el dictamen en la cadena de custodia.
        </div>

        <div>
          <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Motivo / Justificación Técnica de Desestimación
          </label>
          <textarea
            v-model="reason"
            placeholder="Describe las razones por las cuales se desestima la iniciativa (ej. duplicidad, inviabilidad técnica, cambio de prioridades del negocio)..."
            rows="4"
            class="w-full p-3 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-rose-500 focus:outline-none resize-none leading-relaxed text-slate-800"
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
          :disabled="isSubmitting || !reason.trim()"
          class="px-5 py-2 text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-xl transition-colors shadow-2xs disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
        >
          <Ban class="w-3.5 h-3.5" />
          <span>{{ isSubmitting ? 'Desestimando...' : 'Confirmar Desestimación' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>
