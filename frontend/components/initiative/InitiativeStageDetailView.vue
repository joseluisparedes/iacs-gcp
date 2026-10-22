<script setup lang="ts">
import { computed } from 'vue';
import {
  Check, Lock, Clock, Eye, AlertTriangle, Layers, FileText,
  Paperclip, Building2, User, Sparkles, ChevronRight, Download
} from 'lucide-vue-next';
import type { InitiativeStageRecord, Initiative } from '~/types';
import { formatDateDDMMYYYY, formatDateTimeDDMMYYYY } from '~/utils/initiativeHistory';

const props = defineProps<{
  stage: {
    id: string;
    name: string;
    role: string;
    substepsCount?: number;
    substeps?: string[];
    nodeIds?: string[];
  };
  stageIndex: number;
  stageRecords: InitiativeStageRecord[];
  currentStageIndex: number;
  isEndWorkflow?: boolean;
  initiative: Initiative;
  selectedSubNodeId?: string | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'clear-subnode'): void;
}>();

const recordsToRender = computed(() => {
  if (!props.selectedSubNodeId) return props.stageRecords;
  return props.stageRecords.filter(r =>
    (r.node_id || '').toLowerCase() === props.selectedSubNodeId!.toLowerCase() ||
    (r.stage_name || '').toLowerCase().includes(props.selectedSubNodeId!.toLowerCase())
  );
});

// Helper de etiquetas legibles
const formatStageFieldLabel = (key: string): string => {
  const map: Record<string, string> = {
    presupuesto_estimado_usd: 'Presupuesto Estimado (USD)',
    monto_estimado_usd: 'Monto Estimado (USD)',
    tiempo_atencion_esfuerzo: 'Tiempo Estimado de Atención (Esfuerzo)',
    justificacion_presupuesto: 'Justificación del Presupuesto',
    analista_responsable: 'Analista de TI Asignado',
    fecha_inicio_estimacion: 'Fecha Inicio Estimación',
    fecha_fin_estimacion: 'Fecha Fin Estimación',
    fecha_estimacion_compromiso: 'Fecha Compromiso de Estimación',
    fecha_inicio_planificada: 'Fecha Inicio Planificada',
    fecha_fin_planificada: 'Fecha Fin Planificada',
    requiere_presupuesto: '¿Requiere Presupuesto?',
    lider_de_dominio_responsable: 'Líder de Dominio Responsable',
    lider_tecnico_asignado: 'Líder Técnico de Dominio',
    plataformas_de_iniciativa: 'Tipo de Plataforma',
    tipo_solucion: 'Tipo de Solución',
    tipo_iniciativa: 'Tipo de Iniciativa',
    observaciones_bp: 'Observaciones BP TI',
    bp_ti_asignado: 'BP TI Asignado',
    bp_ti_responsable: 'BP TI Responsable',
    sustento_negocio: 'Sustento del Negocio (BO)',
    prioridad_area: 'Prioridad del Área',
    kpi_impactado: 'KPI Impactado',
    business_owner: 'Business Owner',
    vicepresidente_asignado: 'Vicepresidente Asignado',
    titulo_iniciativa: 'Título de la Iniciativa',
    objetivo_iniciativa: 'Objetivo Principal',
    dolor_negocio: 'Dolor o Problema del Negocio',
    justificacion_iniciativa: 'Justificación del Negocio',
    tipo_requerimiento: 'Tipo de Requerimiento',
    institucion: 'Institución',
    vicepresidencia: 'Vicepresidencia',
    direccion: 'Dirección Solicitante',
    registrador: 'Líder Solicitante',
    impacto_esperado: 'Impacto Esperado',
    criterios_aceptacion: 'Criterios de Aceptación',
  };
  return map[key] || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
};

// Helper de valores legibles
const formatStageFieldValue = (key: string, val: any): string => {
  if (val === null || val === undefined || val === '') return '—';
  if (typeof val === 'boolean') return val ? 'Sí' : 'No';
  if (key === 'presupuesto_estimado_usd' || key === 'monto_estimado_usd') {
    const num = Number(val);
    if (!isNaN(num)) {
      return `$ ${num.toLocaleString('en-US')} USD`;
    }
  }

  // Fechas
  const keyLower = (key || '').toLowerCase();
  const isDateKey = keyLower.includes('fecha') || keyLower.includes('date') || keyLower.includes('plazo');
  const isDatePattern = typeof val === 'string' && (
    /^\d{4}[-\/.]\d{1,2}[-\/.]\d{1,2}/.test(val.trim()) ||
    /^\d{1,2}[-\/.]\d{1,2}[-\/.]\d{4}/.test(val.trim())
  );
  if (isDateKey || isDatePattern) {
    const formatted = formatDateDDMMYYYY(val);
    if (formatted && formatted !== '—') return formatted;
  }

  if (typeof val === 'object') {
    if (val.name) return String(val.name);
    return JSON.stringify(val);
  }

  return String(val);
};

// Parser para detectar si un valor es archivo adjunto
const parseFileAttachment = (val: any): { name: string; size?: number } | null => {
  if (!val) return null;
  if (typeof val === 'object' && val.name) return val;
  if (typeof val === 'string' && val.startsWith('{') && val.includes('"name"')) {
    try {
      const parsed = JSON.parse(val);
      if (parsed && parsed.name) return parsed;
    } catch {}
  }
  return null;
};

// Filtrar campos de expediente según etapa si no hay records
const fallbackStageFields = computed(() => {
  const fd = props.initiative?.form_data || {};
  const s = props.initiative?.summary || {};

  if (props.stage.id === 'registro') {
    return [
      { key: 'titulo_iniciativa', label: 'Título de la Iniciativa', value: s.titulo || fd.titulo_iniciativa },
      { key: 'objetivo_iniciativa', label: 'Objetivo Principal', value: s.objetivo || fd.objetivo_iniciativa },
      { key: 'dolor_negocio', label: 'Dolor o Problema del Negocio', value: s.dolor || fd.dolor_negocio },
      { key: 'justificacion_iniciativa', label: 'Justificación del Negocio', value: s.justificacion || fd.justificacion_iniciativa },
      { key: 'institucion', label: 'Institución', value: fd.institucion },
      { key: 'vicepresidencia', label: 'Vicepresidencia', value: fd.vicepresidencia },
      { key: 'direccion', label: 'Dirección Solicitante', value: fd.direccion },
      { key: 'registrador', label: 'Líder Solicitante (Key User)', value: fd.registrador },
      { key: 'tipo_requerimiento', label: 'Tipo de Requerimiento', value: fd.tipo_requerimiento },
    ].filter(item => item.value !== undefined && item.value !== null && item.value !== '');
  }

  if (props.stage.id === 'eval_bp' || props.stage.id === 'viabilidad_bp') {
    return [
      { key: 'bp_ti_asignado', label: 'Business Partner TI Asignado', value: fd.bp_ti_asignado || fd.bp_ti_responsable },
      { key: 'tipo_solucion', label: 'Tipo de Solución', value: fd.tipo_solucion },
      { key: 'tipo_iniciativa', label: 'Tipo de Iniciativa', value: fd.tipo_iniciativa },
      { key: 'observaciones_bp', label: 'Observaciones / Dictamen Técnico', value: fd.observaciones_bp },
      { key: 'plataformas_de_iniciativa', label: 'Plataforma Evaluada', value: fd.plataformas_de_iniciativa },
    ].filter(item => item.value !== undefined && item.value !== null && item.value !== '');
  }

  if (props.stage.id === 'aprob_bo' || props.stage.id === 'patrocinio_bo') {
    return [
      { key: 'business_owner', label: 'Business Owner Asignado', value: fd.business_owner || fd.bo_asignado },
      { key: 'sustento_negocio', label: 'Sustento del Negocio (BO)', value: fd.sustento_negocio },
      { key: 'prioridad_area', label: 'Prioridad Asignada por el Área', value: fd.prioridad_area },
      { key: 'kpi_impactado', label: 'KPI Impactado', value: fd.kpi_impactado },
    ].filter(item => item.value !== undefined && item.value !== null && item.value !== '');
  }

  if (props.stage.id === 'aprob_vp' || props.stage.id === 'aprobacion_vp') {
    return [
      { key: 'vicepresidente_asignado', label: 'Vicepresidente Asignado', value: fd.vicepresidente_asignado || fd.vp_asignado },
      { key: 'prioridad_area', label: 'Prioridad Estratégica VP', value: fd.prioridad_area },
      { key: 'vobo_vp', label: 'Visto Bueno de Vicepresidencia', value: fd.vobo_vp },
    ].filter(item => item.value !== undefined && item.value !== null && item.value !== '');
  }

  if (props.stage.id === 'demanda' || props.stage.id === 'demanda_ti') {
    return [
      { key: 'lider_tecnico_asignado', label: 'Líder de Dominio Asignado', value: fd.lider_tecnico_asignado || fd.lider_de_dominio_responsable },
      { key: 'analista_responsable', label: 'Gestor de Demanda / Analista', value: fd.analista_responsable },
    ].filter(item => item.value !== undefined && item.value !== null && item.value !== '');
  }

  if (props.stage.id === 'estimacion') {
    return [
      { key: 'lider_tecnico_asignado', label: 'Líder Técnico de Dominio', value: fd.lider_tecnico_asignado || fd.lider_de_dominio_responsable },
      { key: 'presupuesto_estimado_usd', label: 'Presupuesto Estimado (USD)', value: fd.presupuesto_estimado_usd || fd.monto_estimado_usd },
      { key: 'tiempo_atencion_esfuerzo', label: 'Tiempo Estimado de Atención', value: fd.tiempo_atencion_esfuerzo },
      { key: 'requiere_presupuesto', label: '¿Requiere Presupuesto?', value: fd.requiere_presupuesto },
      { key: 'analista_responsable', label: 'Analista de TI Asignado', value: fd.analista_responsable },
      { key: 'fecha_inicio_estimacion', label: 'Fecha Inicio Estimación', value: fd.fecha_inicio_estimacion },
      { key: 'fecha_fin_estimacion', label: 'Fecha Fin Estimación', value: fd.fecha_fin_estimacion },
    ].filter(item => item.value !== undefined && item.value !== null && item.value !== '');
  }

  if (props.stage.id === 'planificacion') {
    return [
      { key: 'fecha_inicio_planificada', label: 'Fecha Inicio Planificada', value: fd.fecha_inicio_planificada },
      { key: 'fecha_fin_planificada', label: 'Fecha Fin Planificada', value: fd.fecha_fin_planificada },
      { key: 'pase_cartera', label: 'Pase a Cartera TI', value: fd.pase_cartera },
    ].filter(item => item.value !== undefined && item.value !== null && item.value !== '');
  }

  return [];
});
</script>

<template>
  <div class="space-y-5 animate-in fade-in duration-200">
    <!-- ── Encabezado de la Etapa Seleccionada ── -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 sm:p-5 bg-gradient-to-r from-indigo-50/90 via-white to-slate-50 border border-indigo-100 rounded-2xl shadow-xs">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-[#4F5AF5] text-white flex items-center justify-center text-sm font-black shadow-xs shrink-0">
          {{ stageIndex + 1 }}
        </div>
        <div>
          <span class="text-[10px] uppercase tracking-wider font-extrabold text-[#4F5AF5] block">
            Detalle de Etapa Seleccionada
          </span>
          <h3 class="text-sm sm:text-base font-black text-slate-900 leading-tight">
            {{ stage.name }} <span class="text-slate-500 font-semibold text-xs sm:text-sm">({{ stage.role }})</span>
          </h3>
        </div>
      </div>

      <button
        type="button"
        @click="emit('close')"
        class="text-xs font-bold text-[#4F5AF5] hover:text-indigo-800 hover:underline flex items-center gap-1.5 cursor-pointer bg-white px-3.5 py-2 rounded-xl border border-indigo-200 shadow-2xs transition-all shrink-0 self-start sm:self-auto"
      >
        <Eye class="w-3.5 h-3.5" />
        <span>Ver solicitud completa</span>
      </button>
    </div>

    <!-- ── Sub-pasos informativos (para Estimación y Planificación) ── -->
    <div
      v-if="stage.substeps && stage.substeps.length > 0"
      class="p-4 bg-slate-50/80 rounded-2xl border border-slate-200/80 space-y-2.5"
    >
      <div class="flex items-center justify-between">
        <span class="text-xs font-bold text-slate-800 flex items-center gap-1.5">
          <Layers class="w-3.5 h-3.5 text-[#4F5AF5]" />
          Alcance y actividades de esta etapa ({{ stage.substeps.length }} pasos)
        </span>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        <div
          v-for="(substep, sIdx) in stage.substeps"
          :key="sIdx"
          class="flex items-start gap-2 p-2.5 rounded-xl bg-white border border-slate-200/60 text-xs text-slate-700"
        >
          <span class="w-4 h-4 rounded-full bg-indigo-50 text-[#4F5AF5] font-black text-[10px] flex items-center justify-center shrink-0 mt-0.5">
            {{ sIdx + 1 }}
          </span>
          <span class="text-[11px] leading-snug">{{ substep }}</span>
        </div>
      </div>
    </div>

    <!-- ── CASO A: Registros de Certificados y Custodia Digital Existentes ── -->
    <div v-if="recordsToRender.length > 0" class="space-y-4">
      <div v-if="selectedSubNodeId" class="flex items-center justify-between text-xs px-1">
        <span class="font-bold text-[#4F5AF5] flex items-center gap-1.5">
          <Layers class="w-3.5 h-3.5" />
          Filtrando por sub-estado específico
        </span>
        <button
          type="button"
          @click="emit('clear-subnode')"
          class="text-xs font-bold text-[#4F5AF5] hover:underline cursor-pointer flex items-center gap-1"
        >
          <span>Ver consolidado completo de la etapa</span>
          <ChevronRight class="w-3 h-3" />
        </button>
      </div>

      <div
        v-for="record in recordsToRender"
        :key="record.id"
        class="p-5 rounded-2xl border border-indigo-200/80 bg-white shadow-xs space-y-4"
      >
        <!-- Header del Registro -->
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3 text-xs">
          <div class="flex items-center gap-2">
            <span class="w-6 h-6 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center text-xs font-bold shrink-0">
              <Check class="w-3.5 h-3.5 stroke-[3]" />
            </span>
            <h4 class="text-sm font-bold text-slate-900">
              {{ record.stage_name || stage.name }}
            </h4>
            <span
              v-if="record.action_taken"
              class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-[#4F5AF5] border border-indigo-200/70"
            >
              {{ record.action_taken }}
            </span>
          </div>

          <div class="text-[11px] text-slate-500 flex items-center gap-1.5 flex-wrap">
            <span>
              Completado por: <strong class="text-slate-800 font-semibold">{{ record.user_name || 'Responsable' }}</strong>
              <span v-if="record.user_role"> ({{ record.user_role }})</span>
            </span>
            <span>•</span>
            <span class="font-medium text-slate-700">
              {{ formatDateTimeDDMMYYYY(record.submitted_at) }}
            </span>
          </div>
        </div>

        <!-- Declaración Legal y Consentimiento Certificado -->
        <div
          v-if="record.consent_text_snapshot || record.consent_accepted"
          class="p-3.5 bg-emerald-50/70 border border-emerald-200/80 rounded-xl text-xs text-emerald-950 space-y-1"
        >
          <div class="flex items-center gap-1.5 font-bold text-emerald-800 text-[11px]">
            <Lock class="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>Declaración Legal y Consentimiento Certificado Digitalmente:</span>
          </div>
          <p class="italic font-sans text-slate-700 text-[11px] leading-relaxed">
            "{{ record.consent_text_snapshot || 'Declaración legal aceptada y firmada en conformidad con las normas de gobernanza TI.' }}"
          </p>
        </div>

        <!-- Campos de Datos Completados en este Record -->
        <div
          v-if="record.form_data && Object.keys(record.form_data).length > 0"
          class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 pt-1"
        >
          <template v-for="(v, k) in record.form_data" :key="k">
            <div
              v-if="v !== undefined && v !== null && v !== '' && typeof v !== 'object'"
              class="p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs"
            >
              <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">
                {{ formatStageFieldLabel(String(k)) }}
              </span>
              <span
                :class="[
                  'font-semibold block break-words',
                  k === 'presupuesto_estimado_usd' || k === 'monto_estimado_usd'
                    ? 'text-indigo-900 font-black text-sm'
                    : 'text-slate-800'
                ]"
              >
                {{ formatStageFieldValue(String(k), v) }}
              </span>
            </div>

            <!-- Archivo Adjunto en form_data -->
            <div
              v-else-if="parseFileAttachment(v)"
              class="p-3 bg-indigo-50/60 rounded-xl border border-indigo-100 text-xs flex items-center justify-between gap-2"
            >
              <div class="min-w-0">
                <span class="text-[10px] font-bold text-indigo-500 uppercase tracking-wider block mb-0.5">
                  {{ formatStageFieldLabel(String(k)) }}
                </span>
                <span class="font-bold text-indigo-950 truncate block text-[11px]">
                  {{ parseFileAttachment(v)?.name }}
                </span>
              </div>
              <Paperclip class="w-4 h-4 text-indigo-600 shrink-0" />
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- ── CASO B: Sin Records aún pero con datos del expediente (Fallback o Etapa de Registro) ── -->
    <div
      v-else-if="fallbackStageFields.length > 0"
      class="p-5 rounded-2xl border border-slate-200/90 bg-white shadow-xs space-y-4"
    >
      <div class="flex items-center justify-between border-b border-slate-100 pb-3 text-xs">
        <div class="flex items-center gap-2">
          <span class="w-6 h-6 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center text-xs font-bold shrink-0">
            <Check class="w-3.5 h-3.5 stroke-[3]" />
          </span>
          <h4 class="text-sm font-bold text-slate-900">
            {{ stage.id === 'registro' ? 'Ficha Oficial de Registro de la Necesidad' : `Información Registrada de ${stage.name}` }}
          </h4>
        </div>
        <div class="text-[11px] text-slate-500">
          Registrado: <strong class="text-slate-700">{{ formatDateTimeDDMMYYYY(initiative.created_at) }}</strong>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 pt-1">
        <div
          v-for="item in fallbackStageFields"
          :key="item.key"
          class="p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs"
        >
          <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">
            {{ item.label }}
          </span>
          <span
            :class="[
              'font-semibold block break-words',
              item.key === 'presupuesto_estimado_usd' || item.key === 'monto_estimado_usd'
                ? 'text-indigo-900 font-black text-sm'
                : 'text-slate-800'
            ]"
          >
            {{ formatStageFieldValue(item.key, item.value) }}
          </span>
        </div>
      </div>
    </div>

    <!-- ── CASO C: Etapa en Curso Activa Actualmente ── -->
    <div
      v-else-if="stageIndex === currentStageIndex"
      class="p-6 bg-white border border-indigo-100 rounded-2xl shadow-xs space-y-3"
    >
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-indigo-50 text-[#4F5AF5] flex items-center justify-center font-bold shadow-2xs">
          <Clock class="w-5 h-5" />
        </div>
        <div>
          <h4 class="text-sm font-bold text-slate-900">
            Etapa en Curso: {{ stage.name }}
          </h4>
          <p class="text-xs text-slate-500">
            Responsable: <strong>{{ stage.role }}</strong>
          </p>
        </div>
      </div>
      <p class="text-xs text-slate-600 leading-relaxed">
        Esta etapa se encuentra actualmente activa en el ciclo de vida de la iniciativa. Los evaluadores y responsables designados están tramitando las validaciones técnicas o completando los formularios correspondientes para avanzar el requerimiento.
      </p>
    </div>

    <!-- ── CASO D: Etapa Futura no alcanzada aún ── -->
    <div
      v-else
      class="p-6 bg-slate-50/70 border border-slate-200/80 rounded-2xl text-center space-y-2"
    >
      <div class="w-10 h-10 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
        <Clock class="w-5 h-5" />
      </div>
      <h5 class="text-xs font-bold text-slate-700">
        Etapa futura: {{ stage.name }}
      </h5>
      <p class="text-xs text-slate-400 max-w-md mx-auto">
        Esta etapa aún no ha sido alcanzada en el ciclo de vida de la iniciativa. Se activará cuando se completen satisfactoriamente las etapas previas.
      </p>
    </div>
  </div>
</template>
