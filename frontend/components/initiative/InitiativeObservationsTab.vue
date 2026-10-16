<script setup lang="ts">
import { ref, computed } from 'vue';
import {
  MessageSquare, AlertTriangle, Shuffle, Ban, CheckCircle,
  Clock, ArrowRight, Paperclip, Download
} from 'lucide-vue-next';
import { formatDateTimeDDMMYYYY } from '~/utils/initiativeHistory';

const props = defineProps<{
  initiative: any;
}>();

// Tipo de filtro activo
const obsFilter = ref<'all' | 'observation' | 'movida' | 'desestimacion'>('all');

// Parsear threads de observación, desestimación y reubicación manual
const observationThreads = computed(() => {
  const history: any[] = props.initiative?.form_data?._observation_history || [];
  const currentObs = props.initiative?.form_data?._current_observation;
  const threads: Array<{
    id: string;
    roundNumber: number;
    type: 'observation' | 'desestimacion' | 'movida';
    stageName: string;
    targetStage?: string;
    nodeId?: string;
    category?: string;
    questionDate: string;
    questionBy: string;
    questionRole: string;
    questionDetails: string;
    isResolved: boolean;
    answerDate?: string;
    answerBy?: string;
    answerRole?: string;
    answerDetails?: string;
    answerFiles?: Array<{ name: string; url: string; size?: number }>;
  }> = [];

  let currentThread: any = null;
  let roundCounter = 1;

  history.forEach((h: any, idx: number) => {
    const act = (h.action || '').toLowerCase();

    // 1. Desestimación
    if (act.includes('desestimad')) {
      if (currentThread) {
        threads.push(currentThread);
        currentThread = null;
      }
      threads.push({
        id: `des_${idx}`,
        roundNumber: roundCounter++,
        type: 'desestimacion',
        stageName: h.from_stage || props.initiative?.status || 'Etapa no especificada',
        nodeId: h.from_node_id,
        questionDate: h.date,
        questionBy: h.user_name || 'Desconocido',
        questionRole: h.user_role || 'Rol no especificado',
        questionDetails: h.details || 'Iniciativa desestimada.',
        isResolved: true,
      });
    }
    // 2. Reubicación Manual / Salto Libre
    else if (act.includes('salto') || act.includes('mov') || act.includes('reubic')) {
      if (currentThread) {
        threads.push(currentThread);
        currentThread = null;
      }
      const matchStages = (h.details || '').match(/de\s+'([^']+)'\s+hacia\s+'([^']+)'/i);
      const fromStage = h.from_stage || (matchStages ? matchStages[1] : props.initiative?.status || 'Etapa no especificada');
      const targetStage = h.target_stage || (matchStages ? matchStages[2] : '');
      const reasonMatch = (h.details || '').match(/Motivo:\s*(.*)$/i);
      const reason = h.reason || (reasonMatch ? reasonMatch[1] : h.details || '');

      threads.push({
        id: `mov_${idx}`,
        roundNumber: roundCounter++,
        type: 'movida',
        stageName: fromStage,
        targetStage: targetStage,
        nodeId: h.from_node_id,
        questionDate: h.date,
        questionBy: h.user_name || 'Desconocido',
        questionRole: h.user_role || 'Rol no especificado',
        questionDetails: reason || h.details || 'Iniciativa reubicada manualmente.',
        isResolved: true,
      });
    }
    // 3. Observación formulada
    else if (act.includes('observad')) {
      if (currentThread) {
        threads.push(currentThread);
      }
      let cat = h.category;
      let det = (h.details || '').trim();
      const catMatch = det.match(/^\[([^\]]+)\]\s*(.*)$/);
      if (catMatch) {
        cat = cat || catMatch[1];
        det = catMatch[2];
      }
      det = det.replace(/\s*\(en etapa:\s*[^)]+\)$/i, '').trim();

      currentThread = {
        id: `obs_${idx}`,
        roundNumber: roundCounter++,
        type: 'observation',
        stageName: h.from_stage || 'Etapa no especificada',
        nodeId: h.from_node_id,
        category: cat || 'General',
        questionDate: h.date,
        questionBy: h.user_name || 'Desconocido',
        questionRole: h.user_role || 'Revisor',
        questionDetails: det || 'Observación registrada.',
        isResolved: false,
      };
    }
    // 4. Subsanación
    else if (act.includes('subsanad') || act.includes('reenviad')) {
      if (currentThread) {
        currentThread.isResolved = true;
        currentThread.answerDate = h.date;
        currentThread.answerBy = h.user_name || 'Responsable';
        currentThread.answerRole = h.user_role || 'BP TI';
        currentThread.answerDetails = (h.details || '').replace(/^Subsanación:\s*/i, '').trim() || 'Subsanación completada.';
        currentThread.answerFiles = h.files || [];
        threads.push(currentThread);
        currentThread = null;
      } else {
        threads.push({
          id: `sub_${idx}`,
          roundNumber: roundCounter++,
          type: 'observation',
          stageName: h.from_stage || 'Observada',
          category: 'General',
          questionDate: h.date,
          questionBy: 'Revisor',
          questionRole: 'Evaluador',
          questionDetails: 'Observación previa registrada.',
          isResolved: true,
          answerDate: h.date,
          answerBy: h.user_name,
          answerRole: h.user_role,
          answerDetails: (h.details || '').replace(/^Subsanación:\s*/i, '').trim() || 'Subsanación completada.',
          answerFiles: h.files || [],
        });
      }
    }
  });

  if (currentThread) {
    if (currentObs && currentObs.resolved) {
      currentThread.isResolved = true;
      currentThread.answerDate = currentObs.resolved_at || currentThread.answerDate;
      currentThread.answerBy = currentObs.resolved_by || currentThread.answerBy;
      currentThread.answerDetails = currentObs.resolution_comment || currentThread.answerDetails;
      currentThread.answerFiles = (currentObs.resolution_files && currentObs.resolution_files.length > 0)
        ? currentObs.resolution_files
        : currentThread.answerFiles;
    }
    threads.push(currentThread);
  } else if (currentObs) {
    const cleanObsDetails = (currentObs.details || '').replace(/\s*\(en etapa:\s*[^)]+\)$/i, '').trim();
    const alreadyIncluded = threads.some(t => {
      if (t.questionDate && currentObs.date && t.questionDate === currentObs.date) return true;
      if (t.id === currentObs.id) return true;
      const tClean = (t.questionDetails || '').trim();
      return Boolean(tClean && cleanObsDetails && (tClean.includes(cleanObsDetails) || cleanObsDetails.includes(tClean)));
    });

    if (!alreadyIncluded) {
      threads.push({
        id: currentObs.id || 'obs_active',
        roundNumber: roundCounter++,
        type: currentObs.action === 'Desestimada' ? 'desestimacion' : 'observation',
        stageName: currentObs.from_stage || props.initiative?.status || 'Etapa no especificada',
        nodeId: currentObs.from_node_id,
        category: currentObs.category || 'General',
        questionDate: currentObs.date,
        questionBy: currentObs.observed_by || 'Revisor',
        questionRole: currentObs.user_role || 'Evaluador',
        questionDetails: cleanObsDetails || currentObs.details || '',
        isResolved: Boolean(currentObs.resolved),
        answerDate: currentObs.resolved_at,
        answerBy: currentObs.resolved_by,
        answerDetails: currentObs.resolution_comment,
        answerFiles: currentObs.resolution_files || [],
      });
    }
  }

  return threads;
});

// Contadores de filtros
const obsOnlyCount = computed(() => observationThreads.value.filter(t => t.type === 'observation').length);
const movOnlyCount = computed(() => observationThreads.value.filter(t => t.type === 'movida').length);
const desOnlyCount = computed(() => observationThreads.value.filter(t => t.type === 'desestimacion').length);

const filteredObservationThreads = computed(() => {
  if (obsFilter.value === 'all') return observationThreads.value;
  return observationThreads.value.filter(t => t.type === obsFilter.value);
});
</script>

<template>
  <div class="space-y-6">
    <div class="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <!-- ── Encabezado del Tab (Idéntico a Imagen 4) ── -->
      <div class="px-6 py-4 bg-white border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-amber-50 border border-amber-200/80 text-amber-700 flex items-center justify-center shrink-0">
            <MessageSquare class="w-4 h-4 stroke-[2.2]" />
          </div>
          <div>
            <h3 class="text-sm font-bold text-slate-900 tracking-tight">
              Historial de Observaciones, Desestimaciones y Reubicaciones
            </h3>
            <p class="text-xs text-slate-400 font-normal">
              Trazabilidad de cuestionamientos, acuerdos, reubicaciones de estado y respuestas de subsanación
            </p>
          </div>
        </div>

        <div class="flex items-center gap-2 shrink-0">
          <span class="px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200/70">
            {{ observationThreads.length }} {{ observationThreads.length === 1 ? 'registro' : 'registros' }}
          </span>
        </div>
      </div>

      <!-- ── Barra de Filtros (Idéntica a Imagen 4) ── -->
      <div v-if="observationThreads.length > 0" class="px-6 py-2.5 bg-slate-50/70 border-b border-slate-100 flex items-center gap-2 overflow-x-auto">
        <span class="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider shrink-0 mr-1">
          FILTRAR:
        </span>

        <!-- Botón Todos -->
        <button
          type="button"
          @click="obsFilter = 'all'"
          :class="[
            'px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 shrink-0',
            obsFilter === 'all'
              ? 'bg-slate-900 text-white shadow-2xs'
              : 'bg-white text-slate-600 border border-slate-200/80 hover:bg-slate-50'
          ]"
        >
          <span>Todos</span>
          <span :class="['px-1.5 py-0.2 rounded-full text-[10px] font-black', obsFilter === 'all' ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-600']">
            {{ observationThreads.length }}
          </span>
        </button>

        <!-- Botón Observaciones -->
        <button
          v-if="obsOnlyCount > 0"
          type="button"
          @click="obsFilter = 'observation'"
          :class="[
            'px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 shrink-0',
            obsFilter === 'observation'
              ? 'bg-amber-600 text-white shadow-2xs'
              : 'bg-white text-amber-800 border border-amber-200/80 hover:bg-amber-50/50'
          ]"
        >
          <AlertTriangle class="w-3 h-3 text-amber-500" />
          <span>Observaciones</span>
          <span :class="['px-1.5 py-0.2 rounded-full text-[10px] font-black', obsFilter === 'observation' ? 'bg-white/20 text-white' : 'bg-amber-100 text-amber-800']">
            {{ obsOnlyCount }}
          </span>
        </button>

        <!-- Botón Reubicaciones -->
        <button
          v-if="movOnlyCount > 0"
          type="button"
          @click="obsFilter = 'movida'"
          :class="[
            'px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 shrink-0',
            obsFilter === 'movida'
              ? 'bg-purple-700 text-white shadow-2xs'
              : 'bg-white text-purple-700 border border-purple-200/80 hover:bg-purple-50/50'
          ]"
        >
          <Shuffle class="w-3 h-3 text-purple-500" />
          <span>Reubicaciones</span>
          <span :class="['px-1.5 py-0.2 rounded-full text-[10px] font-black', obsFilter === 'movida' ? 'bg-white/20 text-white' : 'bg-purple-100 text-purple-700']">
            {{ movOnlyCount }}
          </span>
        </button>

        <!-- Botón Desestimaciones -->
        <button
          v-if="desOnlyCount > 0"
          type="button"
          @click="obsFilter = 'desestimacion'"
          :class="[
            'px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 shrink-0',
            obsFilter === 'desestimacion'
              ? 'bg-rose-600 text-white shadow-2xs'
              : 'bg-white text-rose-700 border border-rose-200/80 hover:bg-rose-50/50'
          ]"
        >
          <Ban class="w-3 h-3 text-rose-500" />
          <span>Desestimaciones</span>
          <span :class="['px-1.5 py-0.2 rounded-full text-[10px] font-black', obsFilter === 'desestimacion' ? 'bg-white/20 text-white' : 'bg-rose-100 text-rose-700']">
            {{ desOnlyCount }}
          </span>
        </button>
      </div>

      <!-- ── Listado de Rondas y Dictámenes (Idéntico a Imagen 4) ── -->
      <div class="p-6 space-y-6">
        <div v-if="filteredObservationThreads.length === 0" class="text-center py-12 px-4 space-y-3">
          <div class="w-12 h-12 mx-auto rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-400">
            <CheckCircle class="w-6 h-6 text-emerald-500" />
          </div>
          <h4 class="text-sm font-bold text-slate-800">
            {{ obsFilter === 'all' ? 'Sin observaciones ni reubicaciones registradas' : 'Sin eventos para este filtro' }}
          </h4>
          <p class="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
            Esta iniciativa no presenta cuestionamientos, desestimaciones ni reubicaciones manuales de estado.
          </p>
        </div>

        <template v-else>
          <div
            v-for="(thread, tIdx) in filteredObservationThreads"
            :key="thread.id || tIdx"
            class="space-y-4"
          >
            <!-- ── CASO 1: REUBICACIÓN MANUAL DE ESTADO (Idéntico a Imagen 4 arriba) ── -->
            <div
              v-if="thread.type === 'movida'"
              class="rounded-2xl border border-purple-200/90 bg-white overflow-hidden shadow-xs hover:border-purple-300 transition-all"
            >
              <!-- Header Movida -->
              <div class="px-5 py-3 bg-gradient-to-r from-purple-50/90 via-indigo-50/40 to-white border-b border-purple-100 flex flex-wrap items-center justify-between gap-2">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="px-2.5 py-0.5 rounded-md bg-purple-700 text-white text-xs font-bold flex items-center gap-1.5 shadow-2xs">
                    <Shuffle class="w-3 h-3" /> Reubicación Manual de Estado
                  </span>
                  <span class="text-xs text-slate-600 font-medium flex items-center gap-1">
                    <span>De: <strong class="text-slate-800">{{ thread.stageName }}</strong></span>
                    <template v-if="thread.targetStage">
                      <ArrowRight class="w-3 h-3 text-purple-500 shrink-0 inline mx-0.5" />
                      <span>Hacia: <strong class="text-purple-700">{{ thread.targetStage }}</strong></span>
                    </template>
                  </span>
                </div>

                <span v-if="thread.questionDate" class="text-[11px] text-slate-400 font-medium">
                  {{ formatDateTimeDDMMYYYY(thread.questionDate) }}
                </span>
              </div>

              <!-- Contenido Movida -->
              <div class="p-5 space-y-3">
                <div class="flex items-center gap-2 text-xs text-slate-600">
                  <div class="w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-[10px] font-bold">
                    {{ (thread.questionBy || 'U').substring(0, 2).toUpperCase() }}
                  </div>
                  <span>Movido por: <strong class="text-slate-900">{{ thread.questionBy }}</strong></span>
                  <span class="px-2 py-0.5 rounded text-[10px] font-medium bg-purple-50 text-purple-700 border border-purple-200/60">
                    {{ thread.questionRole }}
                  </span>
                </div>

                <div class="p-4 rounded-xl bg-purple-50/40 border border-purple-200/70 text-xs sm:text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
                  <span class="text-[10px] font-extrabold uppercase tracking-wider text-purple-800 block mb-1">
                    MOTIVO / JUSTIFICACIÓN DEL SALTO DE ESTADO:
                  </span>
                  <p class="font-normal text-slate-700">{{ thread.questionDetails }}</p>
                </div>
              </div>
            </div>

            <!-- ── CASO 2: RONDA DE OBSERVACIÓN & SUBSANACIÓN (Idéntico a Imagen 4 abajo) ── -->
            <div
              v-else-if="thread.type === 'observation'"
              class="rounded-2xl border border-slate-200/90 bg-white overflow-hidden shadow-xs hover:border-slate-300 transition-all"
            >
              <!-- Encabezado de la Ronda -->
              <div class="px-5 py-3 bg-slate-50/70 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
                <div class="flex items-center gap-2.5 flex-wrap">
                  <span class="px-2.5 py-0.5 rounded-md bg-slate-900 text-white text-xs font-bold shadow-2xs">
                    Ronda {{ thread.roundNumber }}
                  </span>
                  <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200/70">
                    {{ thread.category || 'General' }}
                  </span>
                  <span class="text-xs text-slate-500 font-medium">
                    Origen: <strong class="text-slate-700">{{ thread.stageName }}</strong>
                  </span>
                </div>

                <div>
                  <span
                    v-if="thread.isResolved"
                    class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/80"
                  >
                    <CheckCircle class="w-3.5 h-3.5 text-emerald-600" /> Subsanada
                  </span>
                  <span
                    v-else
                    class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200/80 animate-pulse"
                  >
                    <Clock class="w-3.5 h-3.5 text-amber-600" /> Pendiente de Subsanación
                  </span>
                </div>
              </div>

              <!-- Conversación en Hilo -->
              <div class="p-5 sm:p-6 space-y-4">
                <!-- Mensaje 1: Cuestionamiento formulado por el Revisor -->
                <div class="flex gap-3.5 items-start">
                  <div class="w-8 h-8 rounded-full bg-amber-100 border border-amber-200 text-amber-800 font-bold text-xs flex items-center justify-center shrink-0 shadow-2xs">
                    {{ (thread.questionBy || 'BO').substring(0, 2).toUpperCase() }}
                  </div>

                  <div class="flex-1 min-w-0 space-y-1.5">
                    <div class="flex flex-wrap items-center justify-between gap-2">
                      <div class="flex items-center gap-2 flex-wrap">
                        <span class="text-xs font-bold text-slate-900">{{ thread.questionBy }}</span>
                        <span class="px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 text-slate-600 border border-slate-200/80">
                          {{ thread.questionRole }}
                        </span>
                      </div>
                      <span v-if="thread.questionDate" class="text-[11px] text-slate-400 font-medium">
                        {{ formatDateTimeDDMMYYYY(thread.questionDate) }}
                      </span>
                    </div>

                    <div class="p-4 rounded-2xl rounded-tl-sm bg-slate-50/90 border border-slate-200/80 text-xs sm:text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
                      <p class="font-normal text-slate-700">{{ thread.questionDetails }}</p>
                    </div>
                  </div>
                </div>

                <!-- Conector vertical de conversación -->
                <div class="ml-4 pl-0.5 border-l-2 border-slate-200/80 h-3" />

                <!-- Mensaje 2: Respuesta y Evidencias de Subsanación (si resuelta) -->
                <div v-if="thread.isResolved" class="flex gap-3.5 items-start">
                  <div class="w-8 h-8 rounded-full bg-emerald-100 border border-emerald-200 text-emerald-800 font-bold text-xs flex items-center justify-center shrink-0 shadow-2xs">
                    {{ (thread.answerBy || 'BP').substring(0, 2).toUpperCase() }}
                  </div>

                  <div class="flex-1 min-w-0 space-y-1.5">
                    <div class="flex flex-wrap items-center justify-between gap-2">
                      <div class="flex items-center gap-2 flex-wrap">
                        <span class="text-xs font-bold text-slate-900">{{ thread.answerBy || 'Responsable de Subsanación' }}</span>
                        <span class="px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/80">
                          {{ thread.answerRole || 'BP TI' }}
                        </span>
                      </div>
                      <span v-if="thread.answerDate" class="text-[11px] text-slate-400 font-medium">
                        {{ formatDateTimeDDMMYYYY(thread.answerDate) }}
                      </span>
                    </div>

                    <div class="p-4 rounded-2xl rounded-tl-sm bg-emerald-50/30 border border-emerald-200/80 text-xs sm:text-sm text-slate-800 leading-relaxed whitespace-pre-wrap space-y-3">
                      <p class="font-normal text-slate-700">{{ thread.answerDetails || 'Subsanación técnica registrada.' }}</p>

                      <!-- Archivos adjuntos de sustento -->
                      <div v-if="thread.answerFiles && thread.answerFiles.length > 0" class="pt-3 border-t border-emerald-200/60 space-y-2">
                        <span class="text-[11px] font-semibold text-emerald-900 block">
                          Documentos de sustento adjuntos ({{ thread.answerFiles.length }}):
                        </span>
                        <div class="flex flex-wrap gap-2">
                          <a
                            v-for="(file, fIdx) in thread.answerFiles"
                            :key="fIdx"
                            :href="file.url"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white border border-emerald-200 text-xs text-slate-700 shadow-2xs hover:border-emerald-400 transition-colors"
                          >
                            <Paperclip class="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                            <span class="truncate max-w-[200px] font-medium">{{ file.name }}</span>
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- ── CASO 3: DICTAMEN DE DESESTIMACIÓN ── -->
            <div
              v-else-if="thread.type === 'desestimacion'"
              class="rounded-2xl border border-rose-200/90 bg-white overflow-hidden shadow-xs hover:border-rose-300 transition-all"
            >
              <div class="px-5 py-3 bg-rose-50/70 border-b border-rose-100 flex flex-wrap items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                  <span class="px-2.5 py-0.5 rounded-md bg-rose-600 text-white text-xs font-bold flex items-center gap-1.5 shadow-2xs">
                    <Ban class="w-3 h-3" /> Dictamen de Desestimación
                  </span>
                  <span class="text-xs text-slate-500 font-medium">
                    Etapa: <strong class="text-slate-700">{{ thread.stageName }}</strong>
                  </span>
                </div>
                <span v-if="thread.questionDate" class="text-[11px] text-slate-400 font-medium">
                  {{ formatDateTimeDDMMYYYY(thread.questionDate) }}
                </span>
              </div>

              <div class="p-5 space-y-3">
                <div class="flex items-center gap-2 text-xs text-slate-600">
                  <div class="w-6 h-6 rounded-full bg-rose-100 text-rose-700 flex items-center justify-center text-[10px] font-bold">
                    {{ (thread.questionBy || 'U').substring(0, 2).toUpperCase() }}
                  </div>
                  <span>Desestimado por: <strong class="text-slate-900">{{ thread.questionBy }}</strong></span>
                  <span class="px-2 py-0.5 rounded text-[10px] font-medium bg-rose-50 text-rose-700 border border-rose-200/60">
                    {{ thread.questionRole }}
                  </span>
                </div>
                <div class="p-4 rounded-xl bg-rose-50/30 border border-rose-200/70 text-xs sm:text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
                  <p class="font-normal text-slate-700">{{ thread.questionDetails }}</p>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
