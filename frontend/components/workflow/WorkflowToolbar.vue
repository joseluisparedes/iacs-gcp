<script setup lang="ts">
import { 
  Layers, 
  GitFork, 
  PlayCircle, 
  CheckCircle2, 
  AlertTriangle,
  Archive,
  Sparkles,
  GripVertical
} from 'lucide-vue-next';

interface NodeTypeOption {
  id: string;
  type: string;
  stateSubtype?: 'standard' | 'observada' | 'demanda' | 'desestimada';
  label: string;
  defaultLabel: string;
  desc: string;
  borderClass: string;
  bgClass: string;
  iconName: string;
  defaultRoles?: Array<{ role_name: string; can_edit: boolean; can_approve: boolean; can_reject: boolean }>;
}

const emit = defineEmits<{
  (e: 'add-node', item: NodeTypeOption): void;
  (e: 'auto-layout'): void;
}>();

const SECTIONS = [
  {
    title: 'Estados de la Iniciativa',
    items: [
      {
        id: 'state_standard',
        type: 'state',
        stateSubtype: 'standard',
        label: 'Estado Estándar',
        defaultLabel: 'Nuevo Estado',
        desc: 'Fase regular del ciclo de vida',
        borderClass: 'border-blue-200 hover:border-blue-400',
        bgClass: 'bg-blue-50/60 text-blue-700',
        iconName: 'Layers',
        defaultRoles: [{ role_name: 'registrador', can_edit: true, can_approve: true, can_reject: true }],
      },
      {
        id: 'state_observada',
        type: 'state',
        stateSubtype: 'observada',
        label: 'Estado Observada',
        defaultLabel: 'Observada',
        desc: 'Retorno para ajustes o subsanación',
        borderClass: 'border-amber-200 hover:border-amber-400',
        bgClass: 'bg-amber-50/60 text-amber-700',
        iconName: 'AlertTriangle',
        defaultRoles: [{ role_name: 'bp_ti', can_edit: true, can_approve: true, can_reject: true }],
      },
      {
        id: 'state_demanda',
        type: 'state',
        stateSubtype: 'demanda',
        label: 'Estado En Demanda',
        defaultLabel: 'En Demanda',
        desc: 'Gestión de demanda y estimación',
        borderClass: 'border-emerald-200 hover:border-emerald-400',
        bgClass: 'bg-emerald-50/60 text-emerald-700',
        iconName: 'Sparkles',
        defaultRoles: [{ role_name: 'admin', can_edit: true, can_approve: true, can_reject: true }],
      },
      {
        id: 'state_desestimada',
        type: 'state',
        stateSubtype: 'desestimada',
        label: 'Estado Desestimada',
        defaultLabel: 'Desestimada',
        desc: 'Cierre o rechazo definitivo',
        borderClass: 'border-rose-200 hover:border-rose-400',
        bgClass: 'bg-rose-50/60 text-rose-700',
        iconName: 'Archive',
        defaultRoles: [{ role_name: 'admin', can_edit: false, can_approve: false, can_reject: false }],
      },
    ],
  },
  {
    title: 'Control de Flujo',
    items: [
      {
        id: 'gateway',
        type: 'gateway',
        label: 'Compuerta Lógica',
        defaultLabel: 'Bifurcación Condicional',
        desc: 'División por reglas de negocio',
        borderClass: 'border-amber-200 hover:border-amber-400',
        bgClass: 'bg-amber-50/60 text-amber-700',
        iconName: 'GitFork',
      },
      {
        id: 'start',
        type: 'start',
        label: 'Inicio',
        defaultLabel: 'Inicio',
        desc: 'Punto de entrada del flujo',
        borderClass: 'border-emerald-200 hover:border-emerald-400',
        bgClass: 'bg-emerald-50/60 text-emerald-700',
        iconName: 'PlayCircle',
      },
      {
        id: 'end',
        type: 'end',
        label: 'Fin',
        defaultLabel: 'Fin',
        desc: 'Conclusión del flujo',
        borderClass: 'border-emerald-200 hover:border-emerald-400',
        bgClass: 'bg-emerald-50/60 text-emerald-700',
        iconName: 'CheckCircle2',
      },
    ],
  },
];

const handleDragStart = (e: DragEvent, item: NodeTypeOption) => {
  if (!e.dataTransfer) return;
  e.dataTransfer.setData('application/vueflow-type', item.type);
  e.dataTransfer.setData(
    'application/vueflow-payload',
    JSON.stringify({
      label: item.defaultLabel || item.label,
      description: item.desc,
      stateSubtype: item.stateSubtype,
      roles: item.defaultRoles || [],
    })
  );
  e.dataTransfer.effectAllowed = 'move';
};
</script>

<template>
  <aside class="w-64 bg-white border-r border-slate-200 flex flex-col h-full overflow-hidden select-none shrink-0 shadow-2xs">
    <!-- Header de organización rápida -->
    <div class="p-3 border-b border-slate-100">
      <button
        type="button"
        @click="emit('auto-layout')"
        class="w-full flex items-center justify-center gap-2 py-2 px-3 text-xs font-bold text-[#EB5F46] bg-[#FFF0ED] hover:bg-[#FDE2DC] border border-[#FCD9D2] rounded-xl transition-all shadow-2xs cursor-pointer group"
      >
        <Sparkles class="w-4 h-4 text-[#EB5F46] group-hover:rotate-12 transition-transform" />
        <span>Organizar Diagrama</span>
      </button>
    </div>

    <!-- Lista de componentes arrastrables -->
    <div class="flex-1 overflow-y-auto p-3 space-y-5 custom-scrollbar text-left">
      <div>
        <p class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Componentes</p>
        <p class="text-[11px] text-slate-500 mt-0.5">Arrastra o haz clic para añadir al lienzo</p>
      </div>

      <div v-for="section in SECTIONS" :key="section.title" class="space-y-2">
        <h3 class="text-[11px] font-bold text-slate-400 uppercase tracking-wider px-1">
          {{ section.title }}
        </h3>

        <div class="space-y-1.5">
          <div
            v-for="item in section.items"
            :key="item.id"
            draggable="true"
            @dragstart="handleDragStart($event, item as any)"
            @click="emit('add-node', item as any)"
            :class="[
              'group relative flex items-center gap-2.5 p-2.5 rounded-xl border transition-all cursor-grab active:cursor-grabbing hover:shadow-xs',
              item.borderClass,
              item.bgClass
            ]"
            title="Arrastra al lienzo o haz clic para añadir"
          >
            <GripVertical class="w-3.5 h-3.5 text-slate-300 group-hover:text-slate-500 shrink-0" />

            <div class="shrink-0">
              <Layers v-if="item.iconName === 'Layers'" class="w-4 h-4" />
              <AlertTriangle v-else-if="item.iconName === 'AlertTriangle'" class="w-4 h-4" />
              <Sparkles v-else-if="item.iconName === 'Sparkles'" class="w-4 h-4" />
              <Archive v-else-if="item.iconName === 'Archive'" class="w-4 h-4" />
              <GitFork v-else-if="item.iconName === 'GitFork'" class="w-4 h-4" />
              <PlayCircle v-else-if="item.iconName === 'PlayCircle'" class="w-4 h-4" />
              <CheckCircle2 v-else-if="item.iconName === 'CheckCircle2'" class="w-4 h-4" />
            </div>

            <div class="min-w-0 flex-1">
              <p class="text-xs font-bold text-slate-800 leading-snug truncate">{{ item.label }}</p>
              <p class="text-[10px] text-slate-500 leading-tight truncate mt-0.5">{{ item.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>
