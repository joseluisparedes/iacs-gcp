<script setup lang="ts">
import { CheckCircle2, ArrowRight, ShieldCheck, ExternalLink } from 'lucide-vue-next';

const props = withDefaults(
  defineProps<{
    isOpen: boolean;
    title?: string;
    actionLabel?: string;
    nextStatus?: string;
    message?: string;
    primaryButtonText?: string;
  }>(),
  {
    title: '¡Acción Completada con Éxito!',
    actionLabel: '',
    nextStatus: '',
    message: 'La iniciativa ha sido procesada correctamente y el cambio de estado ha quedado sellado en la cadena de custodia.',
    primaryButtonText: 'Ir al Dashboard',
  }
);

const emit = defineEmits<{
  (e: 'primary'): void;
  (e: 'close'): void;
}>();
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
          class="relative w-full max-w-md bg-white border shadow-2xl rounded-2xl sm:rounded-3xl border-slate-200 overflow-hidden text-center"
        >
          <!-- Barra superior esmeralda de éxito -->
          <div class="h-1.5 w-full bg-gradient-to-r from-emerald-500 via-teal-500 to-[#4F5AF5]" />

          <div class="p-6 sm:p-7 space-y-4">
            <!-- Icono animado de éxito -->
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200 shadow-sm animate-in zoom-in-75 duration-300">
              <CheckCircle2 class="w-9 h-9" />
            </div>

            <!-- Título y Mensaje -->
            <div class="space-y-1.5">
              <h3 class="text-xl font-bold tracking-tight text-slate-900">
                {{ title }}
              </h3>
              <p class="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed">
                {{ message }}
              </p>
            </div>

            <!-- Ficha resumen del nuevo estado -->
            <div v-if="nextStatus || actionLabel" class="p-3.5 bg-slate-50 rounded-2xl border border-slate-200/80 text-left space-y-2 text-xs">
              <div v-if="actionLabel" class="flex items-center justify-between">
                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Acción Registrada</span>
                <span class="font-bold text-slate-800">{{ actionLabel }}</span>
              </div>
              <div v-if="nextStatus" class="flex items-center justify-between pt-1.5 border-t border-slate-200/60">
                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Nuevo Estado Oficial</span>
                <span class="font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
                  {{ nextStatus }}
                </span>
              </div>
            </div>

            <!-- Indicador de firma criptográfica -->
            <div class="flex items-center justify-center gap-1.5 text-[11px] text-slate-400 font-medium">
              <ShieldCheck class="w-3.5 h-3.5 text-emerald-600" />
              <span>Sello digital y custodia registrados exitosamente</span>
            </div>
          </div>

          <!-- Botón de Continuar -->
          <div class="p-4 bg-slate-50/90 border-t border-slate-100 flex items-center justify-center">
            <button
              type="button"
              @click="emit('primary')"
              class="w-full py-3 px-5 text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 rounded-xl transition-all shadow-sm flex items-center justify-center gap-2 cursor-pointer"
            >
              <span>{{ primaryButtonText }}</span>
              <ArrowRight class="w-4 h-4" />
            </button>
          </div>
        </div>
      </Transition>
    </div>
  </Transition>
</template>
