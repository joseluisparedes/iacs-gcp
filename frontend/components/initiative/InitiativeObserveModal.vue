<script setup lang="ts">
import { ref } from 'vue';
import { AlertTriangle, X } from 'lucide-vue-next';

const props = defineProps<{
  isOpen: boolean;
  categories?: string[];
  isSubmitting?: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'confirm', payload: { category: string; details: string }): void;
}>();

const DEFAULT_CATEGORIES = [
  'No estoy de acuerdo con el tiempo estimado',
  'Falta información técnica o alcance incompleto',
  'Riesgo operativo o arquitectónico no mitigado',
  'Presupuesto o esfuerzo sobredimensionado',
  'Incompatibilidad con estándares de TI Laureate',
  'General',
  '__custom__'
];

const selectedCategory = ref(DEFAULT_CATEGORIES[0]);
const customCategory = ref('');
const details = ref('');

const handleConfirm = () => {
  if (!details.value.trim()) {
    return;
  }
  const categoryFinal = selectedCategory.value === '__custom__'
    ? (customCategory.value.trim() || 'General')
    : selectedCategory.value;

  emit('confirm', {
    category: categoryFinal,
    details: details.value.trim(),
  });
  details.value = '';
  customCategory.value = '';
};

const handleClose = () => {
  details.value = '';
  customCategory.value = '';
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
          <div class="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
            <AlertTriangle class="w-4 h-4 stroke-[2.5]" />
          </div>
          <div>
            <h3 class="font-bold text-slate-900 text-base">Formular Observación</h3>
            <p class="text-xs text-slate-400">Detalla los requerimientos o ajustes necesarios</p>
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
        <div>
          <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Categoría del Cuestionamiento
          </label>
          <select
            v-model="selectedCategory"
            class="w-full p-2.5 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-amber-500 focus:outline-none bg-white text-slate-800"
          >
            <option
              v-for="cat in (categories || DEFAULT_CATEGORIES)"
              :key="cat"
              :value="cat"
            >
              {{ cat === '__custom__' ? '✏️ Otra categoría personalizada...' : cat }}
            </option>
          </select>
        </div>

        <div v-if="selectedCategory === '__custom__'">
          <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Nombre de la Categoría Personalizada
          </label>
          <input
            v-model="customCategory"
            type="text"
            placeholder="Ej. Revisión de seguridad y accesos..."
            class="w-full p-2.5 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-amber-500 focus:outline-none"
          />
        </div>

        <div>
          <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
            Detalle del Cuestionamiento o Ajuste Solicitado
          </label>
          <textarea
            v-model="details"
            placeholder="Describe con precisión qué información falta, qué aspecto no es conforme o qué corrección debe realizarse..."
            rows="4"
            class="w-full p-3 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-amber-500 focus:outline-none resize-none leading-relaxed text-slate-800"
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
          :disabled="isSubmitting || !details.trim()"
          class="px-5 py-2 text-xs font-bold text-white bg-amber-600 hover:bg-amber-700 rounded-xl transition-colors shadow-2xs disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
        >
          <AlertTriangle class="w-3.5 h-3.5" />
          <span>{{ isSubmitting ? 'Registrando...' : 'Registrar Observación' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>
