<script setup lang="ts">
import { ref, onMounted } from 'vue';

const config = useRuntimeConfig();
const apiBase = config.public.apiBase;

interface WorkflowItem {
  id: string;
  name: string;
  version: number;
  status: 'draft' | 'published' | 'archived';
  description?: string;
  created_at?: string;
  published_at?: string;
}

const workflows = ref<WorkflowItem[]>([
  {
    id: '11111111-1111-1111-1111-111111111111',
    name: 'Flujo Canónico IACS Enterprise',
    version: 1,
    status: 'published',
    description: 'Flujo estándar con evaluación de BP TI, dictámenes técnicos y pase a demanda.',
    published_at: '2026-09-01T00:00:00Z',
  },
  {
    id: '22222222-2222-2222-2222-222222222222',
    name: 'Flujo Ágil - Iniciativas Menores (Fast-Track)',
    version: 1,
    status: 'draft',
    description: 'Flujo simplificado para proyectos con esfuerzo menor a 40 horas sin CAPEX.',
  }
]);

const loading = ref(false);

async function fetchWorkflows() {
  loading.value = true;
  try {
    const res = await $fetch<WorkflowItem[]>(`${apiBase}/workflow/definitions`).catch(() => []);
    if (Array.isArray(res) && res.length > 0) {
      workflows.value = res;
    }
  } catch (err) {
    console.error('Error al cargar catálogo de workflows:', err);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchWorkflows();
});
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center gap-2">
          <span class="p-2 rounded-xl bg-[#0D436C]/10 text-[#0D436C] font-bold text-lg">📑</span>
          <h1 class="text-2xl font-bold text-[#0D436C] tracking-tight">Catálogo de Flujos de Trabajo</h1>
        </div>
        <p class="text-sm text-slate-500 mt-1">
          Gobierno de versiones, activación de flujos canónicos y control de ciclo de vida.
        </p>
      </div>

      <NuxtLink
        to="/admin/workflow-editor"
        class="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-[#EB5F46] hover:bg-[#d94f38] rounded-lg transition-colors shadow-sm"
      >
        <span>+</span> Diseñar Nuevo Flujo
      </NuxtLink>
    </div>

    <!-- Lista de Flujos en Catálogo -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="wf in workflows"
        :key="wf.id"
        class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4 flex flex-col justify-between"
      >
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span
              :class="[
                'px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase',
                wf.status === 'published' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
              ]"
            >
              {{ wf.status === 'published' ? 'En Producción (Activo)' : 'Borrador' }}
            </span>
            <span class="text-xs font-mono text-slate-400">v{{ wf.version }}.0</span>
          </div>

          <h3 class="font-bold text-sm text-[#0D436C]">{{ wf.name }}</h3>
          <p class="text-xs text-slate-600 leading-relaxed">{{ wf.description }}</p>
        </div>

        <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
          <span class="text-[11px] text-slate-400">
            {{ wf.published_at ? 'Publicado: ' + new Date(wf.published_at).toLocaleDateString() : 'Sin publicar' }}
          </span>
          <div class="flex items-center gap-2">
            <NuxtLink
              :to="`/admin/workflow-editor?id=${wf.id}`"
              class="px-3 py-1.5 text-xs font-bold text-[#0D436C] bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors"
            >
              Abrir en Editor ➔
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
