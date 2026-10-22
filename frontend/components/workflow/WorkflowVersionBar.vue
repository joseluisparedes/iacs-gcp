<script setup lang="ts">
import { 
  Send, 
  AlertCircle, 
  Loader2, 
  Check, 
  Undo2, 
  Redo2, 
  Sparkles,
  Layers,
  Bookmark
} from 'lucide-vue-next';

const props = defineProps<{
  workflowName: string;
  version: number;
  status: 'draft' | 'published' | 'archived';
  isDirty: boolean;
  isSaving: boolean;
  canUndo: boolean;
  canRedo: boolean;
  hasFavoriteCoordinates?: boolean;
}>();

const emit = defineEmits<{
  (e: 'save-and-publish'): void;
  (e: 'open-macro-stages-modal'): void;
  (e: 'save-favorite-coordinates'): void;
  (e: 'apply-favorite-coordinates'): void;
  (e: 'undo'): void;
  (e: 'redo'): void;
}>();
</script>

<template>
  <header class="h-14 bg-white border-b border-slate-200 px-4 flex items-center justify-between z-10 select-none shrink-0 shadow-2xs">
    <!-- Left: Info & Status -->
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-2">
        <h1 class="text-sm font-bold text-slate-800 truncate max-w-xs md:max-w-md" :title="workflowName">
          {{ workflowName || 'Flujo Oficial de Gestión de la Demanda' }}
        </h1>
        <span class="text-xs px-2 py-0.5 rounded-full font-mono bg-slate-100 text-slate-600 font-semibold border border-slate-200">
          v{{ version }}
        </span>
        <span
          class="text-xs px-2.5 py-0.5 rounded-full font-semibold border"
          :class="status === 'published' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-amber-50 text-amber-700 border-amber-200'"
        >
          {{ status === 'published' ? 'Publicado Activo' : 'Borrador' }}
        </span>
      </div>

      <!-- Separator -->
      <div class="h-4 w-px bg-slate-200"></div>

      <!-- Auto-save / Dirty Status -->
      <div class="flex items-center gap-1.5 text-xs">
        <span v-if="isSaving" class="text-indigo-600 flex items-center gap-1">
          <Loader2 class="w-3 h-3 animate-spin text-[#4F5AF5]" />
          <span>Guardando...</span>
        </span>
        <span v-else-if="isDirty" class="text-amber-600 flex items-center gap-1">
          <AlertCircle class="w-3 h-3 text-amber-500" />
          <span>Cambios sin guardar</span>
        </span>
        <span v-else class="text-slate-400 flex items-center gap-1">
          <Check class="w-3 h-3 text-emerald-600" />
          <span>Guardado</span>
        </span>
      </div>
    </div>

    <!-- Right: Actions -->
    <div class="flex items-center gap-2">
      <!-- Undo / Redo -->
      <div class="flex items-center bg-slate-100 p-0.5 rounded-xl border border-slate-200 shadow-2xs">
        <button
          type="button"
          @click="emit('undo')"
          :disabled="!canUndo"
          class="p-1.5 rounded-lg hover:bg-white text-slate-700 disabled:opacity-30 disabled:hover:bg-transparent transition-all cursor-pointer"
          title="Deshacer (Ctrl + Z)"
        >
          <Undo2 class="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          @click="emit('redo')"
          :disabled="!canRedo"
          class="p-1.5 rounded-lg hover:bg-white text-slate-700 disabled:opacity-30 disabled:hover:bg-transparent transition-all cursor-pointer"
          title="Rehacer (Ctrl + Y)"
        >
          <Redo2 class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- Configurar Macro-Etapas (Stepper) -->
      <button
        type="button"
        @click="emit('open-macro-stages-modal')"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-indigo-700 bg-indigo-50/90 border border-indigo-200 rounded-xl hover:bg-indigo-100 transition-colors shadow-2xs cursor-pointer"
        title="Configurar y ordenar las macro-etapas del stepper de la iniciativa"
      >
        <Layers class="w-3.5 h-3.5 text-indigo-600" />
        <span class="hidden md:inline">Macro-Etapas</span>
      </button>

      <!-- Separator -->
      <div class="h-4 w-px bg-slate-200"></div>

      <!-- Guardar Coordenadas Favoritas -->
      <button
        type="button"
        @click="emit('save-favorite-coordinates')"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-amber-800 bg-amber-50 hover:bg-amber-100 border border-amber-300 rounded-xl transition-colors shadow-2xs cursor-pointer"
        title="Guarda la posición actual de todas las cajas como tu distribución favorita"
      >
        <Bookmark class="w-3.5 h-3.5 text-amber-600" />
        <span class="hidden sm:inline">Guardar Favoritas</span>
      </button>

      <!-- Aplicar Coordenadas Favoritas -->
      <button
        type="button"
        @click="emit('apply-favorite-coordinates')"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 rounded-xl transition-colors shadow-2xs cursor-pointer"
        title="Reordena las cajas según la distribución favorita que guardaste"
      >
        <Sparkles class="w-3.5 h-3.5 text-emerald-600" />
        <span class="hidden sm:inline">Aplicar Favoritas</span>
      </button>

      <!-- Separator -->
      <div class="h-4 w-px bg-slate-200"></div>

      <!-- Guardar y Publicar (Unificado en un solo botón) -->
      <button
        type="button"
        @click="emit('save-and-publish')"
        :disabled="isSaving"
        class="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold text-white bg-gradient-to-r from-[#EB5F46] to-[#d64f38] hover:from-[#d64f38] hover:to-[#bd412c] rounded-xl shadow-xs transition-all cursor-pointer transform active:scale-95 disabled:opacity-50"
        title="Guarda los cambios y publica el flujo como modelo activo del sistema"
      >
        <Loader2 v-if="isSaving" class="w-3.5 h-3.5 animate-spin" />
        <Send v-else class="w-3.5 h-3.5" />
        <span>Guardar y Publicar</span>
      </button>
    </div>
  </header>
</template>
