<script setup lang="ts">
import { computed } from 'vue';
import {
  HelpCircle,
  ArrowRight,
  ShieldAlert,
  Check,
  X,
  Sparkles,
  FileText
} from 'lucide-vue-next';

const props = withDefaults(
  defineProps<{
    isOpen: boolean;
    title?: string;
    actionLabel?: string;
    currentState?: string;
    targetState?: string;
    initiativeTitle?: string;
    isSubmitting?: boolean;
    confirmText?: string;
    cancelText?: string;
    consentStatement?: string;
    consentTitle?: string;
    consentAccepted?: boolean;
  }>(),
  {
    title: '¿Estás seguro de la acción que estás realizando?',
    actionLabel: 'Avanzar iniciativa',
    currentState: 'Borrador',
    targetState: 'Siguiente estado',
    initiativeTitle: '',
    isSubmitting: false,
    confirmText: 'Aceptar',
    cancelText: 'Regresar',
    consentStatement: '',
    consentTitle: '',
    consentAccepted: false,
  }
);

const emit = defineEmits<{
  (e: 'confirm'): void;
  (e: 'cancel'): void;
  (e: 'update:consent', val: boolean): void;
}>();

const handleBackdropClick = (e: MouseEvent) => {
  if (e.target === e.currentTarget && !props.isSubmitting) {
    emit('cancel');
  }
};
</script>

<template>
  <Transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition duration-150 ease-in"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="isOpen"
      @click="handleBackdropClick"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs"
    >
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0 scale-95 translate-y-2"
        enter-to-class="opacity-100 scale-100 translate-y-0"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100 scale-100 translate-y-0"
        leave-to-class="opacity-0 scale-95 translate-y-2"
      >
        <div
          class="relative w-full max-w-md bg-white border shadow-2xl rounded-2xl sm:rounded-3xl border-slate-200 overflow-hidden"
          @click.stop
        >
          <!-- Barra superior decorativa corporativa -->
          <div class="h-1.5 w-full bg-gradient-to-r from-amber-500 via-[#EB5F46] to-indigo-600" />

          <!-- Botón cerrar X -->
          <button
            type="button"
            @click="emit('cancel')"
            :disabled="isSubmitting"
            class="absolute top-3.5 right-3.5 p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
            title="Cerrar y regresar"
          >
            <X class="w-4 h-4" />
          </button>

          <div class="p-6 text-center space-y-4">
            <!-- Icono con halo pulsante suave -->
            <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-amber-50 text-amber-600 border border-amber-200/80 shadow-xs mb-1">
              <HelpCircle class="w-7 h-7" />
            </div>

            <!-- Título Principal Exacto Solicitado -->
            <div class="space-y-1">
              <h3 class="text-lg font-bold tracking-tight text-slate-900">
                {{ title }}
              </h3>
              <p class="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed">
                Revisa los detalles de la transición antes de confirmar. Si regresas, la iniciativa permanecerá en su estado actual sin ningún cambio.
              </p>
            </div>

            <!-- Tarjeta de Resumen de Transición -->
            <div class="p-4 text-left border rounded-2xl bg-slate-50/80 border-slate-200/80 space-y-3">
              <!-- Acción Seleccionada -->
              <div>
                <span class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  Acción a Ejecutar (Botón)
                </span>
                <div class="mt-1 flex items-center gap-1.5 font-bold text-sm text-[#EB5F46]">
                  <Sparkles class="w-4 h-4 shrink-0 text-[#EB5F46]" />
                  <span>{{ actionLabel }}</span>
                </div>
              </div>

              <!-- Ruta de Estados: Origen ➔ Destino -->
              <div>
                <span class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                  Cambio de Estado del Requerimiento
                </span>
                <div class="flex items-center gap-2 text-xs font-semibold">
                  <div class="flex-1 p-2 bg-white border border-slate-200 rounded-xl truncate text-slate-700 text-center shadow-2xs">
                    <span class="block text-[9px] text-slate-400 uppercase font-medium">Actual</span>
                    <span class="truncate block font-bold text-slate-800">{{ currentState }}</span>
                  </div>

                  <ArrowRight class="w-4 h-4 text-slate-400 shrink-0" />

                  <div class="flex-1 p-2 bg-indigo-50 border border-indigo-200 rounded-xl truncate text-indigo-700 text-center shadow-2xs">
                    <span class="block text-[9px] text-indigo-400 uppercase font-medium">Nuevo Estado</span>
                    <span class="truncate block font-bold text-indigo-900">{{ targetState }}</span>
                  </div>
                </div>
              </div>

              <!-- Título de la iniciativa (si aplica) -->
              <div v-if="initiativeTitle" class="pt-2 border-t border-slate-200/60 text-[11px] text-slate-500 truncate flex items-center gap-1.5">
                <FileText class="w-3.5 h-3.5 shrink-0 text-slate-400" />
                <span class="truncate font-medium text-slate-600">{{ initiativeTitle }}</span>
              </div>
            </div>

            <!-- Consentimiento de Etapa Formal Integrado (si aplica) -->
            <div
              v-if="consentStatement"
              :class="[
                'p-3.5 rounded-2xl border text-left transition-all space-y-2',
                consentAccepted
                  ? 'bg-emerald-50/50 border-emerald-300'
                  : 'bg-indigo-50/60 border-indigo-200'
              ]"
            >
              <label class="flex items-start gap-3 cursor-pointer select-none">
                <input
                  type="checkbox"
                  :checked="consentAccepted"
                  @change="emit('update:consent', ($event.target as HTMLInputElement).checked)"
                  class="mt-1 w-5 h-5 rounded-md text-[#4F5AF5] border-indigo-300 focus:ring-[#4F5AF5] cursor-pointer shrink-0"
                />
                <div class="space-y-1 min-w-0 flex-1">
                  <span class="block text-xs font-bold text-slate-900 leading-tight">
                    {{ consentTitle || 'Declaración de Consentimiento y Visto Bueno' }}
                  </span>
                  <p class="text-[11px] text-slate-700 italic bg-white/80 p-2.5 rounded-xl border border-indigo-100">
                    “{{ consentStatement }}”
                  </p>
                  <p v-if="consentAccepted" class="text-[11px] font-bold text-emerald-700 flex items-center gap-1">
                    <Check class="w-3.5 h-3.5 text-emerald-600" />
                    <span>Conformidad otorgada</span>
                  </p>
                  <p v-else class="text-[11px] text-slate-400 font-medium">
                    Marca esta casilla para validar y otorgar tu conformidad.
                  </p>
                </div>
              </label>
            </div>

            <!-- Advertencia Institucional de Custodia -->
            <div class="flex items-start gap-2 p-2.5 bg-amber-50/70 border border-amber-200/70 rounded-xl text-left">
              <ShieldAlert class="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <p class="text-[11px] text-amber-900 leading-tight">
                Al confirmar, se registrará una entrada formal e inmutable en el historial y cadena de custodia de la iniciativa.
              </p>
            </div>
          </div>

          <!-- Botones del Modal -->
          <div class="p-4 bg-slate-50/90 border-t border-slate-100 flex items-center gap-3">
            <button
              type="button"
              @click="emit('cancel')"
              :disabled="isSubmitting"
              class="flex-1 py-2.5 px-4 text-xs font-bold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 rounded-xl transition-all cursor-pointer shadow-2xs disabled:opacity-50"
            >
              {{ cancelText }}
            </button>

            <button
              type="button"
              @click="emit('confirm')"
              :disabled="isSubmitting || (Boolean(consentStatement) && !consentAccepted)"
              class="flex-1 py-2.5 px-4 text-xs font-bold text-white bg-[#EB5F46] hover:bg-[#d44830] border border-transparent rounded-xl transition-all shadow-sm shadow-[#EB5F46]/30 flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Check class="w-4 h-4" />
              <span>{{ confirmText }}</span>
            </button>
          </div>
        </div>
      </Transition>
    </div>
  </Transition>
</template>
