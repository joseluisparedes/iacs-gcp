<script setup lang="ts">
import { computed } from 'vue';
import { Clock, ArrowRight, Paperclip, AlertTriangle, GitBranch } from 'lucide-vue-next';
import { formatDateTimeDDMMYYYY, getHistoryStateInfo } from '~/utils/initiativeHistory';

const props = defineProps<{
  initiative: any;
  stageRecords?: any[];
}>();

// Historial consolidado cronológico
const consolidatedEvents = computed(() => {
  const history: any[] = props.initiative?.form_data?._observation_history || [];

  // Si no hay _observation_history pero existen stageRecords, transformar stageRecords en eventos
  if (history.length === 0 && props.stageRecords && props.stageRecords.length > 0) {
    return props.stageRecords.map((r, i) => {
      const prev = i > 0 ? props.stageRecords![i - 1].stage_name : '1. Borrador';
      const toState = r.stage_name || r.action_taken || 'Aprobado';
      return {
        date: r.submitted_at,
        user_name: r.user_name || 'Usuario del Sistema',
        user_role: r.user_role || 'Sistema',
        action: r.action_taken || 'Transición',
        details: `Se cambió el estado de '${prev}' a '${toState}'`,
        from_stage: prev,
        target_stage: toState,
      };
    });
  }

  return history;
});
</script>

<template>
  <div class="space-y-6">
    <div v-if="consolidatedEvents.length > 0" class="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <!-- ── Encabezado del Historial (Idéntico a Imagen 3) ── -->
      <div class="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50/80 via-white to-orange-50/10 flex items-center justify-between gap-4">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-xl bg-[#FFF0ED] border border-[#FCD9D2] flex items-center justify-center text-[#EB5F46] shrink-0 font-bold">
            <Clock class="w-4 h-4 stroke-[2.2]" />
          </div>
          <div>
            <h3 class="text-sm font-black text-slate-900 tracking-tight">
              Historial de Revisiones y Transiciones
            </h3>
            <p class="text-[11px] text-slate-400 font-medium">
              Auditoría cronológica del flujo y cambios de estado
            </p>
          </div>
        </div>

        <span class="px-3 py-1 rounded-full text-xs font-black bg-[#FFF0ED] text-[#EB5F46] border border-[#FCD9D2] shrink-0">
          {{ consolidatedEvents.length }} {{ consolidatedEvents.length === 1 ? 'transición' : 'transiciones' }}
        </span>
      </div>

      <!-- ── Timeline Vertical con Círculos Numerados Conectados ── -->
      <div class="px-6 py-6 space-y-6">
        <div
          v-for="(h, i) in consolidatedEvents"
          :key="i"
          class="flex gap-4 relative group"
        >
          <!-- Línea conectora vertical -->
          <div
            v-if="i !== consolidatedEvents.length - 1"
            class="absolute top-9 left-[17px] bottom-[-24px] w-[2.5px] bg-gradient-to-b from-slate-200 via-slate-200 to-slate-100 rounded-full z-0"
          />

          <!-- ── Bolita Numérica Correlativa (Idéntica a Imagen 3) ── -->
          <div
            :class="[
              'w-9 h-9 shrink-0 rounded-full flex items-center justify-center font-black text-xs relative z-10 transition-transform duration-200 group-hover:scale-110 cursor-default select-none shadow-2xs',
              getHistoryStateInfo(h.target_stage || h.action || '', i).circleClass
            ]"
            :title="`Movimiento #${i + 1}`"
          >
            <span>{{ i + 1 }}</span>
            <span
              v-if="(h.action || '').toLowerCase().includes('observad')"
              class="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-amber-700 text-white flex items-center justify-center ring-2 ring-white"
            >
              <AlertTriangle class="w-2 h-2" />
            </span>
          </div>

          <!-- ── Contenido de la Transición ── -->
          <div class="flex-1 min-w-0 bg-slate-50/60 hover:bg-slate-50 border border-slate-200/70 hover:border-slate-300 rounded-xl p-4 transition-all duration-200 shadow-2xs">
            <!-- Header del evento: Usuario, Rol, Fecha -->
            <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
              <div class="flex items-center gap-2 flex-wrap">
                <div class="w-6 h-6 rounded-full bg-slate-200 text-slate-700 text-[10px] font-bold flex items-center justify-center shrink-0">
                  {{ (h.user_name || 'U').substring(0, 2).toUpperCase() }}
                </div>
                <span class="text-xs font-black text-slate-900">
                  {{ h.user_name || 'Usuario' }}
                </span>
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50/80 text-indigo-700 border border-indigo-100/80">
                  {{ h.user_role || 'Sistema' }}
                </span>
              </div>

              <span class="flex items-center gap-1 text-[11px] font-medium text-slate-400 shrink-0">
                <Clock class="w-3 h-3 text-slate-400" />
                {{ formatDateTimeDDMMYYYY(h.date) }}
              </span>
            </div>

            <!-- Fila de Transición DE: -> A: -->
            <div class="flex items-center gap-2 flex-wrap pt-0.5">
              <template v-if="h.details && h.details.match(/de\s+'([^']+)'\s+a\s+'([^']+)'/i)">
                <!-- Match regex de cambio de estado -->
                <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-white text-slate-700 border border-slate-200/90 shadow-2xs">
                  <span class="text-[9px] text-slate-400 font-bold uppercase tracking-wider">DE:</span>
                  <span class="w-1.5 h-1.5 rounded-full bg-slate-400" />
                  <span>{{ h.details.match(/de\s+'([^']+)'\s+a\s+'([^']+)'/i)[1] }}</span>
                </div>

                <ArrowRight class="w-3.5 h-3.5 text-slate-400 shrink-0" />

                <div :class="['inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold border shadow-2xs', getHistoryStateInfo(h.details.match(/de\s+'([^']+)'\s+a\s+'([^']+)'/i)[2], i).badgeClass]">
                  <span class="text-[9px] opacity-70 font-black uppercase tracking-wider">A:</span>
                  <span :class="['w-1.5 h-1.5 rounded-full', getHistoryStateInfo(h.details.match(/de\s+'([^']+)'\s+a\s+'([^']+)'/i)[2], i).dotColor]" />
                  <span>{{ h.details.match(/de\s+'([^']+)'\s+a\s+'([^']+)'/i)[2] }}</span>
                </div>
              </template>

              <template v-else-if="h.from_stage && h.target_stage">
                <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-white text-slate-700 border border-slate-200/90 shadow-2xs">
                  <span class="text-[9px] text-slate-400 font-bold uppercase tracking-wider">DE:</span>
                  <span class="w-1.5 h-1.5 rounded-full bg-slate-400" />
                  <span>{{ h.from_stage }}</span>
                </div>

                <ArrowRight class="w-3.5 h-3.5 text-slate-400 shrink-0" />

                <div :class="['inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold border shadow-2xs', getHistoryStateInfo(h.target_stage, i).badgeClass]">
                  <span class="text-[9px] opacity-70 font-black uppercase tracking-wider">A:</span>
                  <span :class="['w-1.5 h-1.5 rounded-full', getHistoryStateInfo(h.target_stage, i).dotColor]" />
                  <span>{{ h.target_stage }}</span>
                </div>
              </template>

              <template v-else>
                <span :class="['inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold border shadow-2xs', getHistoryStateInfo(h.action || 'Transición', i).badgeClass]">
                  <span :class="['w-1.5 h-1.5 rounded-full', getHistoryStateInfo(h.action || 'Transición', i).dotColor]" />
                  <span>{{ h.action || 'Acción formalizada' }}</span>
                </span>
              </template>
            </div>

            <!-- Comentarios o motivos adicionales si existen -->
            <div
              v-if="h.details && !h.details.toLowerCase().startsWith('se cambi')"
              class="mt-2.5 p-3 rounded-xl bg-white border border-slate-200/80 text-xs text-slate-700 leading-relaxed shadow-2xs"
            >
              <p class="font-medium text-slate-800">{{ h.details }}</p>
            </div>

            <!-- Archivos adjuntos en la transición si existen -->
            <div
              v-if="h.files && Array.isArray(h.files) && h.files.length > 0"
              class="mt-2.5 flex flex-wrap gap-2"
            >
              <a
                v-for="(f, fIdx) in h.files"
                :key="fIdx"
                :href="f.url"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-indigo-50/50 border border-slate-200 hover:border-indigo-200 text-xs font-semibold text-slate-700 hover:text-indigo-600 transition-colors shadow-2xs"
              >
                <Paperclip class="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                <span class="truncate max-w-[200px]">{{ f.name }}</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Estado Vacío Institucional ── -->
    <div v-else class="bg-white rounded-2xl border border-slate-200/80 p-12 text-center shadow-xs">
      <div class="w-12 h-12 rounded-2xl bg-[#FFF0ED] border border-[#FCD9D2] flex items-center justify-center text-[#EB5F46] mx-auto mb-3">
        <Clock class="w-6 h-6" />
      </div>
      <h4 class="text-sm font-bold text-slate-800">Sin historial de cambios registrado aún</h4>
      <p class="text-xs text-slate-400 mt-1 max-w-md mx-auto leading-relaxed">
        Los cambios de estado, observaciones y dictámenes aprobados aparecerán aquí cronológicamente en la cadena de custodia institucional.
      </p>
    </div>
  </div>
</template>
