<script setup lang="ts">
import { ref } from 'vue';
import { 
  Save, 
  Send, 
  Play, 
  Users, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  Loader2, 
  Check, 
  Undo2, 
  Redo2, 
  Sparkles 
} from 'lucide-vue-next';

const props = defineProps<{
  workflowName: string;
  version: number;
  status: 'draft' | 'published' | 'archived';
  isDirty: boolean;
  isSaving: boolean;
  canUndo: boolean;
  canRedo: boolean;
}>();

const emit = defineEmits<{
  (e: 'save'): void;
  (e: 'publish'): void;
  (e: 'open-roles-modal'): void;
  (e: 'auto-layout'): void;
  (e: 'undo'): void;
  (e: 'redo'): void;
}>();

const showPublishModal = ref(false);
const isPublishing = ref(false);

const handleConfirmPublish = async () => {
  isPublishing.value = true;
  try {
    emit('publish');
    showPublishModal.value = false;
  } finally {
    isPublishing.value = false;
  }
};
</script>

<template>
  <header class="h-14 bg-white border-b border-slate-200 px-4 flex items-center justify-between z-10 select-none shrink-0 shadow-2xs">
    <!-- Left: Info & Status -->
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-2">
        <h1 class="text-sm font-bold text-slate-800 truncate max-w-xs md:max-w-md" :title="workflowName">
          {{ workflowName || 'Flujo Oficial de Gestión de la Demanda' }}
        </h1>
        <span class="text-[10px] font-mono px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md border border-slate-200 font-bold">
          v{{ version }}
        </span>
      </div>

      <!-- Status Badge -->
      <span
        v-if="status === 'published'"
        class="text-[10px] font-semibold px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-full border border-emerald-200 flex items-center gap-1 shadow-2xs"
      >
        <CheckCircle2 class="w-3 h-3 text-emerald-600" />
        Publicado Activo
      </span>
      <span
        v-else-if="status === 'archived'"
        class="text-[10px] font-semibold px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full border border-slate-300 shadow-2xs"
      >
        Archivado
      </span>
      <span
        v-else
        class="text-[10px] font-semibold px-2 py-0.5 bg-amber-50 text-amber-800 rounded-full border border-amber-300 flex items-center gap-1 shadow-2xs"
      >
        <Clock class="w-3 h-3 text-amber-600" />
        Borrador en Edición
      </span>

      <!-- Autosave Status -->
      <div class="hidden sm:flex items-center gap-1 text-[11px] text-slate-400 pl-2">
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

      <!-- Asignación de Roles -->
      <button
        type="button"
        @click="emit('open-roles-modal')"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition-colors shadow-2xs cursor-pointer"
      >
        <Users class="w-3.5 h-3.5 text-slate-500" />
        <span class="hidden md:inline">Asignación de Roles</span>
      </button>

      <!-- Organizar Diagrama -->
      <button
        type="button"
        @click="emit('auto-layout')"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-[#EB5F46] bg-[#FFF0ED] border border-[#FCD9D2] hover:bg-[#FDE2DC] rounded-xl transition-colors shadow-2xs cursor-pointer"
        title="Reorganizar automáticamente todas las cajas sin sobreposiciones"
      >
        <Sparkles class="w-3.5 h-3.5 text-[#EB5F46]" />
        <span class="hidden sm:inline">Organizar Diagrama</span>
      </button>

      <!-- Simular -->
      <NuxtLink
        to="/admin/workflow-simulator"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition-colors shadow-2xs"
      >
        <Play class="w-3.5 h-3.5 text-[#EB5F46]" />
        <span class="hidden md:inline">Simular</span>
      </NuxtLink>

      <!-- Guardar -->
      <button
        type="button"
        @click="emit('save')"
        :disabled="isSaving"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition-colors shadow-2xs disabled:opacity-50 cursor-pointer"
      >
        <Save class="w-3.5 h-3.5 text-slate-600" />
        <span class="hidden sm:inline">Guardar</span>
      </button>

      <!-- Publicar Flujo -->
      <button
        type="button"
        @click="showPublishModal = true"
        class="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-white bg-gradient-to-r from-[#EB5F46] to-[#d64f38] hover:from-[#d64f38] hover:to-[#bd412c] rounded-xl shadow-xs transition-all cursor-pointer transform active:scale-95"
      >
        <Send class="w-3.5 h-3.5" />
        <span>Publicar Flujo</span>
      </button>
    </div>

    <!-- Modal de Publicación -->
    <div v-if="showPublishModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in duration-150 text-left">
        <h3 class="text-base font-bold text-slate-900 mb-2">¿Publicar este Flujo de Trabajo?</h3>
        <p class="text-xs text-slate-600 leading-relaxed mb-4">
          Al publicar, este flujo se convertirá en el <strong>modelo activo del sistema</strong>. Las nuevas iniciativas seguirán este esquema de estados, roles, validaciones e IA. El flujo activo anterior pasará a estado archivado automáticamente.
        </p>

        <div class="p-3 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-900 mb-5 flex items-start gap-2">
          <AlertCircle class="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <span>Las iniciativas que ya se encuentran en curso continuarán con su flujo histórico sin verse afectadas.</span>
        </div>

        <div class="flex items-center justify-end gap-2.5">
          <button
            type="button"
            @click="showPublishModal = false"
            :disabled="isPublishing"
            class="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
          >
            Cancelar
          </button>
          <button
            type="button"
            @click="handleConfirmPublish"
            :disabled="isPublishing"
            class="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-[#EB5F46] hover:bg-[#d64f38] rounded-xl transition-colors shadow-xs cursor-pointer"
          >
            <Loader2 v-if="isPublishing" class="w-3.5 h-3.5 animate-spin" />
            <Send v-else class="w-3.5 h-3.5" />
            <span>Confirmar y Publicar</span>
          </button>
        </div>
      </div>
    </div>
  </header>
</template>
