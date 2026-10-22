<script setup lang="ts">
import { computed } from 'vue';
import {
  ShieldCheck, FileCheck2, FileSignature, Lock, AlertTriangle,
  CheckCircle, Layers, Building2, Paperclip, X, User, ExternalLink,
  Calendar, Send, ArrowRight
} from 'lucide-vue-next';
import type { Initiative, InitiativeStageRecord, StageForm, StageConsent } from '~/types';

const props = defineProps<{
  initiative: Initiative;
  currentNode: any;
  activeNodeForm: StageForm | null;
  activeNodeConsent: StageConsent | null;
  canActOnCurrentStage: boolean;
  stageFormData: Record<string, any>;
  stageConsentAccepted: boolean;
  isStageReadyToApprove: boolean;
  missingStageFields: string[];
  eligibleRoleUsersMap: Record<string, Array<{ id: string; name: string; email: string }>>;
  stageRecords: InitiativeStageRecord[];
  nextApproversList?: any[];
  shouldShowNextApprovers?: boolean;
  nextApproversTitle?: string;
  isSubmitting?: boolean;
  forwardEdges?: any[];
}>();

const emit = defineEmits<{
  (e: 'update:field', key: string, value: any): void;
  (e: 'update:consent', accepted: boolean): void;
  (e: 'execute-transition', edge: any): void;
  (e: 'notify', payload: { message: string; type?: 'warning' | 'error' | 'success'; title?: string }): void;
}>();

// Estado actual
const currentStatusLabel = computed(() => {
  return props.currentNode?.data?.label || props.initiative.status || 'Etapa actual';
});

// Roles requeridos para este nodo de workflow
const roleBadgeLabel = computed(() => {
  const roles = props.currentNode?.data?.roles || [];
  if (!roles.length) return null;
  const firstRole = (roles[0]?.role_name || roles[0]?.name || roles[0] || '').toLowerCase();
  if (firstRole.includes('owner') || firstRole.includes('bo')) return 'Business Owner';
  if (firstRole.includes('bp')) return 'Business Partner TI';
  if (firstRole.includes('lider') || firstRole.includes('dominio')) return 'Líder de Dominio';
  if (firstRole.includes('admin')) return 'Administrador';
  if (firstRole.includes('vice')) return 'Vicepresidencia';
  return roles[0]?.role_name || roles[0]?.name || null;
});

// Helper para etiqueta de botón de transición
const getEdgeLabel = (edge: any) => {
  if (edge?.label && edge.label.trim()) return edge.label.trim();
  return 'Aprobar y Continuar';
};

// Helper para estilo de botón de transición
const getEdgeStyle = (edge: any) => {
  const style = edge?.data?.style_config || {};
  const bg = style.button_bg || (style.button_color ? 'transparent' : '#EB5F46');
  const border = style.button_color || '#EB5F46';
  const text = style.label_color || (bg === 'transparent' || bg === '#FFFFFF' ? border : '#FFFFFF');
  return {
    backgroundColor: bg,
    borderColor: border,
    color: text,
  };
};

// Helper de valores actuales
const getFieldValue = (key: string) => {
  if (props.stageFormData[key] !== undefined) {
    return props.stageFormData[key];
  }
  return props.initiative.form_data?.[key] ?? '';
};

// Formato legible DD/MM/AAAA para alertas de validación
const formatDateDisplay = (isoDate: string): string => {
  if (!isoDate) return '';
  try {
    const [year, month, day] = isoDate.split('-');
    if (year && month && day) return `${day}/${month}/${year}`;
    return isoDate;
  } catch {
    return isoDate;
  }
};

// Helper para encontrar campo de inicio correspondiente (dinámico por convención o esquema)
const findRelatedStartField = (field: any) => {
  if (field.validation?.greater_than_or_equal) {
    return props.activeNodeForm?.fields?.find((f: any) => f.key === field.validation.greater_than_or_equal);
  }
  if (field.min_date_field) {
    return props.activeNodeForm?.fields?.find((f: any) => f.key === field.min_date_field);
  }
  const key = (field.key || '').toLowerCase();
  const label = (field.label || '').toLowerCase();
  if (key.includes('fin') || key.includes('limite') || key.includes('hasta') || key.includes('end') || label.includes('fin') || label.includes('límite') || label.includes('limite')) {
    return props.activeNodeForm?.fields?.find((f: any) => {
      if (f.key === field.key || f.type !== 'date') return false;
      const k = (f.key || '').toLowerCase();
      const l = (f.label || '').toLowerCase();
      return k.includes('ini') || k.includes('desde') || k.includes('start') || l.includes('inicio') || l.includes('desde');
    });
  }
  return null;
};

// Helper para encontrar campo de fin correspondiente (dinámico por convención o esquema)
const findRelatedEndField = (field: any) => {
  if (field.validation?.less_than_or_equal) {
    return props.activeNodeForm?.fields?.find((f: any) => f.key === field.validation.less_than_or_equal);
  }
  if (field.max_date_field) {
    return props.activeNodeForm?.fields?.find((f: any) => f.key === field.max_date_field);
  }
  const key = (field.key || '').toLowerCase();
  const label = (field.label || '').toLowerCase();
  if (key.includes('ini') || key.includes('desde') || key.includes('start') || label.includes('inicio') || label.includes('desde')) {
    return props.activeNodeForm?.fields?.find((f: any) => {
      if (f.key === field.key || f.type !== 'date') return false;
      const k = (f.key || '').toLowerCase();
      const l = (f.label || '').toLowerCase();
      return k.includes('fin') || k.includes('limite') || k.includes('hasta') || k.includes('end') || l.includes('fin') || l.includes('límite') || l.includes('limite');
    });
  }
  return null;
};

const getDateMin = (field: any): string | undefined => {
  const startField = findRelatedStartField(field);
  if (startField) {
    const val = getFieldValue(startField.key);
    if (val) return val;
  }
  return undefined;
};

const getDateMax = (field: any): string | undefined => {
  const endField = findRelatedEndField(field);
  if (endField) {
    const val = getFieldValue(endField.key);
    if (val) return val;
  }
  return undefined;
};

const getDateFieldError = (field: any): string | null => {
  const currentVal = getFieldValue(field.key);
  if (!currentVal) return null;

  // Validación de campo fin contra campo inicio
  const startField = findRelatedStartField(field);
  if (startField) {
    const startVal = getFieldValue(startField.key);
    if (startVal && currentVal < startVal) {
      return `La fecha límite no puede ser anterior a la fecha de inicio (${formatDateDisplay(startVal)}).`;
    }
  }

  // Validación de campo inicio contra campo fin
  const endField = findRelatedEndField(field);
  if (endField) {
    const endVal = getFieldValue(endField.key);
    if (endVal && currentVal > endVal) {
      return `La fecha de inicio no puede ser posterior a la fecha límite (${formatDateDisplay(endVal)}).`;
    }
  }

  return null;
};

// Determinar rol asignado al rol_user
const getRoleText = (field: any) => {
  if (field.target_role === 'bp_ti' || !field.target_role || /bp/i.test(field.label)) {
    return 'como BP TI';
  }
  if (field.target_role === 'lider_de_dominio' || /lider|dominio/i.test(field.label)) {
    return 'como Líder de Dominio';
  }
  if (field.target_role === 'business_owner' || /owner|bo/i.test(field.label)) {
    return 'como Business Owner';
  }
  return 'con este rol';
};

// Subida de archivos adjuntos para campos de tipo 'file'
const handleFileUpload = async (field: any, event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  const ft = field.fileOptions?.fileTypes;
  let typeKey = 'txt';
  const name = file.name.toLowerCase();
  if (name.endsWith('.pdf')) typeKey = 'pdf';
  else if (name.endsWith('.docx')) typeKey = 'docx';
  else if (name.endsWith('.xlsx') || name.endsWith('.xls')) typeKey = 'xlsx';
  else if (name.match(/\.(png|jpg|jpeg|webp)$/)) typeKey = 'image';

  const cfg = ft?.[typeKey] || { enabled: true, maxMb: 25 };
  if (ft && !cfg.enabled) {
    emit('notify', { message: `El formato ${typeKey.toUpperCase()} no está permitido.`, type: 'warning', title: 'Archivo No Permitido' });
    return;
  }
  if (file.size > (cfg.maxMb || 25) * 1024 * 1024) {
    emit('notify', { message: `El archivo supera el tamaño máximo de ${cfg.maxMb} MB.`, type: 'warning', title: 'Archivo Muy Pesado' });
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    emit('update:field', field.key, JSON.stringify({
      name: file.name,
      url: e.target?.result as string,
      type: file.type || 'application/octet-stream',
      size: file.size,
    }));
  };
  reader.readAsDataURL(file);
};

const parseFileData = (val: string) => {
  try {
    return JSON.parse(val);
  } catch {
    return null;
  }
};
</script>

<template>
  <div class="space-y-4">
    <!-- ══════════════════════════════════════════════════════════════════ -->
    <!-- ── CASO A: FICHA DE DICTAMEN & CONSENTIMIENTO ACTIVA (EDITABLE) ── -->
    <!-- ══════════════════════════════════════════════════════════════════ -->
    <div
      v-if="(activeNodeForm || activeNodeConsent) && canActOnCurrentStage && initiative.status !== 'Desestimada' && initiative.status !== 'Borrador' && (initiative.current_node_id || currentNode?.id) !== 'borrador'"
      class="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden transition-all duration-200 hover:shadow-md"
    >
      <!-- Acento Superior Tricolor Corporativo Laureate -->
      <div class="h-1 bg-gradient-to-r from-[#0D436C] via-[#4F5AF5] to-[#EB5F46]" />

      <!-- Encabezado Ficha de Etapa / Formulario Activo -->
      <div class="p-5 bg-gradient-to-b from-slate-50/70 via-white to-white border-b border-slate-100 space-y-3.5">
        <!-- Meta Header: Etiqueta de tipo y Status dinámico -->
        <div class="flex items-center justify-between gap-2">
          <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-100 shadow-2xs">
            <ShieldCheck v-if="activeNodeConsent && !activeNodeForm" class="w-3.5 h-3.5 text-indigo-600" />
            <FileSignature v-else-if="activeNodeConsent" class="w-3.5 h-3.5 text-indigo-600" />
            <FileCheck2 v-else class="w-3.5 h-3.5 text-indigo-600" />
            <span>{{ activeNodeConsent && activeNodeForm ? 'Dictamen & Consentimiento' : (activeNodeConsent ? 'Consentimiento de Etapa' : 'Evaluación Técnica Requerida') }}</span>
          </div>

          <!-- Badge dinámico de requerimiento / conformidad -->
          <div
            :class="[
              'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider transition-all',
              isStageReadyToApprove
                ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                : 'bg-amber-50 text-amber-900 border border-amber-200/90'
            ]"
          >
            <span
              v-if="!isStageReadyToApprove"
              class="relative flex h-2 w-2"
            >
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
            </span>
            <CheckCircle v-else class="w-3 h-3 text-emerald-600" />
            <span>{{ isStageReadyToApprove ? 'Listo para emitir' : 'Requerido' }}</span>
          </div>
        </div>

        <!-- Título Principal y Contexto de Etapa -->
        <div class="flex items-start gap-3.5">
          <div class="w-11 h-11 rounded-2xl bg-gradient-to-tr from-[#0D436C] via-indigo-700 to-[#4F5AF5] flex items-center justify-center text-white shadow-md shadow-indigo-500/20 shrink-0 mt-0.5">
            <FileSignature v-if="activeNodeConsent" class="w-5 h-5" />
            <FileCheck2 v-else class="w-5 h-5" />
          </div>
          <div class="min-w-0 flex-1">
            <h3 class="text-[15px] font-extrabold text-slate-900 leading-snug tracking-tight break-words">
              {{ activeNodeForm?.name || activeNodeConsent?.title || 'Ficha de Evaluación de Etapa' }}
            </h3>

            <!-- Pill de Etapa + Rol Estructurado (Evita quiebres de texto sueltos) -->
            <div class="mt-2 flex flex-wrap items-center gap-1.5">
              <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 border border-slate-200/70 max-w-full">
                <Layers class="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                <span class="text-[10px] text-slate-400 font-extrabold uppercase tracking-wider shrink-0">Etapa:</span>
                <span class="text-xs font-bold text-slate-800 truncate" :title="currentStatusLabel">
                  {{ currentStatusLabel }}
                </span>
              </div>

              <div v-if="roleBadgeLabel" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-50/80 text-indigo-700 border border-indigo-100 text-[11px] font-bold">
                <User class="w-3 h-3 text-indigo-500 shrink-0" />
                <span>{{ roleBadgeLabel }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="p-5 sm:p-6 space-y-6">
        <!-- ── Dynamic Stage Form Fields ── -->
        <div v-if="activeNodeForm" class="space-y-4">
          <div class="border-b border-slate-100 pb-2">
            <h4 class="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Criterios y Evaluación Técnica
            </h4>
            <p v-if="activeNodeForm.description" class="text-xs text-slate-500 mt-0.5">
              {{ activeNodeForm.description }}
            </p>
          </div>

          <div class="space-y-4">
            <div
              v-for="field in (activeNodeForm.fields || [])"
              :key="field.id || field.key"
              class="w-full"
            >
              <label class="block text-xs font-bold text-slate-700 mb-1">
                {{ field.label }} <span v-if="field.required" class="text-rose-500">*</span>
              </label>

              <!-- Tipo: textarea -->
              <textarea
                v-if="field.type === 'textarea'"
                rows="3"
                :value="getFieldValue(field.key)"
                @input="emit('update:field', field.key, ($event.target as HTMLTextAreaElement).value)"
                :placeholder="field.placeholder || 'Detalla tus observaciones o sustento...'"
                class="w-full px-3.5 py-2 text-xs sm:text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
              ></textarea>

              <!-- Tipo: select -->
              <select
                v-else-if="field.type === 'select'"
                :value="getFieldValue(field.key)"
                @change="emit('update:field', field.key, ($event.target as HTMLSelectElement).value)"
                class="w-full px-3.5 py-2 text-xs sm:text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
              >
                <option value="">Selecciona una opción...</option>
                <option
                  v-for="opt in (field.options || [])"
                  :key="opt"
                  :value="opt"
                >
                  {{ opt }}
                </option>
              </select>

              <!-- Tipo: checkbox -->
              <label
                v-else-if="field.type === 'checkbox'"
                class="flex items-center gap-2.5 pt-2 cursor-pointer"
              >
                <input
                  type="checkbox"
                  :checked="Boolean(getFieldValue(field.key))"
                  @change="emit('update:field', field.key, ($event.target as HTMLInputElement).checked)"
                  class="w-4 h-4 rounded-md text-[#4F5AF5] focus:ring-[#4F5AF5] cursor-pointer"
                />
                <span class="text-xs font-semibold text-slate-700">
                  {{ field.placeholder || 'Confirmar verificación de este criterio' }}
                </span>
              </label>

              <!-- Tipo: date con Control Dinámico de Rango y Validación -->
              <div v-else-if="field.type === 'date'" class="space-y-1">
                <input
                  type="date"
                  :value="getFieldValue(field.key)"
                  :min="getDateMin(field)"
                  :max="getDateMax(field)"
                  @input="emit('update:field', field.key, ($event.target as HTMLInputElement).value)"
                  :class="[
                    'w-full px-3.5 py-2 text-xs sm:text-sm bg-slate-50 border rounded-xl focus:outline-none focus:ring-2 transition-all',
                    getDateFieldError(field)
                      ? 'border-rose-400 bg-rose-50/40 text-rose-950 focus:ring-rose-400/20 focus:border-rose-500'
                      : 'border-slate-200 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]'
                  ]"
                />
                <!-- Alerta visual de error de fechas si fecha fin < fecha inicio -->
                <p
                  v-if="getDateFieldError(field)"
                  class="text-[11px] text-rose-600 font-semibold flex items-center gap-1.5 animate-in fade-in duration-200 pt-0.5"
                >
                  <AlertTriangle class="w-3.5 h-3.5 text-rose-500 shrink-0" />
                  <span>{{ getDateFieldError(field) }}</span>
                </p>
              </div>

              <!-- Tipo: number -->
              <input
                v-else-if="field.type === 'number'"
                type="number"
                :value="getFieldValue(field.key)"
                @input="emit('update:field', field.key, ($event.target as HTMLInputElement).value)"
                :placeholder="field.placeholder || '0'"
                class="w-full px-3.5 py-2 text-xs sm:text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
              />

              <!-- Tipo: file -->
              <div v-else-if="field.type === 'file'" class="space-y-2">
                <input
                  type="file"
                  :id="`stage_file_${field.key}`"
                  class="hidden"
                  @change="handleFileUpload(field, $event)"
                />
                <div v-if="getFieldValue(field.key)" class="flex items-center gap-2 p-2 bg-indigo-50/70 border border-indigo-200 rounded-xl text-xs">
                  <Paperclip class="w-4 h-4 text-indigo-600 shrink-0" />
                  <span class="font-semibold text-slate-700 truncate flex-1">
                    {{ parseFileData(getFieldValue(field.key))?.name || getFieldValue(field.key) }}
                  </span>
                  <a
                    v-if="parseFileData(getFieldValue(field.key))?.url"
                    :href="parseFileData(getFieldValue(field.key))?.url"
                    target="_blank"
                    rel="noreferrer"
                    class="text-[11px] font-bold text-[#4F5AF5] hover:underline"
                  >
                    Ver
                  </a>
                  <button
                    type="button"
                    @click="emit('update:field', field.key, '')"
                    class="text-slate-400 hover:text-rose-600 p-1 cursor-pointer"
                  >
                    <X class="w-3.5 h-3.5" />
                  </button>
                </div>
                <label
                  v-else
                  :for="`stage_file_${field.key}`"
                  class="flex items-center justify-center gap-2 p-3 bg-slate-50 hover:bg-indigo-50/50 border border-dashed border-slate-300 hover:border-indigo-300 rounded-xl text-xs font-semibold text-slate-600 hover:text-indigo-600 cursor-pointer transition-all"
                >
                  <Paperclip class="w-4 h-4 text-indigo-500" />
                  <span>{{ field.placeholder || 'Adjuntar archivo de sustento' }}</span>
                </label>
              </div>

              <!-- Tipo: role_user (Selección y asignación automática con alcance) -->
              <div v-else-if="field.type === 'role_user'">
                <!-- Caso 1: Único usuario elegible (Asignación automática idéntica a la imagen del requerimiento) -->
                <div v-if="(eligibleRoleUsersMap[field.key] || []).length === 1" class="space-y-1.5">
                  <input
                    type="text"
                    :value="(eligibleRoleUsersMap[field.key] || [])[0].name"
                    disabled
                    readonly
                    class="w-full px-3.5 py-2 text-xs sm:text-sm bg-slate-100/80 border border-slate-200 text-slate-700 rounded-xl cursor-not-allowed font-medium select-none focus:outline-none"
                  />
                  <p class="text-[11px] text-slate-400 font-normal">
                    * Asignado automáticamente: única persona asociada {{ getRoleText(field) }} para esta dirección.
                  </p>
                </div>

                <!-- Caso 2: Sin usuarios registrados con este rol en el alcance -->
                <div v-else-if="(eligibleRoleUsersMap[field.key] || []).length === 0" class="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
                  <AlertTriangle class="w-4 h-4 text-rose-500 shrink-0" />
                  <span>No hay usuarios activos registrados con este rol con alcance en esta dirección o transversal.</span>
                </div>

                <!-- Caso 3: Múltiples candidatos para seleccionar -->
                <select
                  v-else
                  :value="getFieldValue(field.key)"
                  @change="emit('update:field', field.key, ($event.target as HTMLSelectElement).value)"
                  class="w-full px-3.5 py-2 text-xs sm:text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
                >
                  <option value="">{{ field.placeholder || 'Selecciona un responsable...' }}</option>
                  <option
                    v-for="u in (eligibleRoleUsersMap[field.key] || [])"
                    :key="u.id"
                    :value="u.name"
                  >
                    {{ u.name }}
                  </option>
                </select>
              </div>

              <!-- Fallback: input de texto genérico -->
              <input
                v-else
                type="text"
                :value="getFieldValue(field.key)"
                @input="emit('update:field', field.key, ($event.target as HTMLInputElement).value)"
                :placeholder="field.placeholder || ''"
                class="w-full px-3.5 py-2 text-xs sm:text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
              />

              <p v-if="field.helpText && field.type !== 'role_user'" class="text-[10px] text-slate-400 mt-1">
                {{ field.helpText }}
              </p>
            </div>
          </div>
        </div>

        <!-- ── Declaración de Consentimiento Legal de Etapa ── -->
        <div v-if="activeNodeConsent" class="pt-1">
          <div v-if="activeNodeForm" class="border-b border-slate-100 pb-2 mb-3">
            <h4 class="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck class="w-4 h-4 text-indigo-600" />
              <span>DECLARACIÓN DE CONSENTIMIENTO FORMAL</span>
            </h4>
          </div>

          <div
            :class="[
              'p-4 rounded-2xl border transition-all duration-200 space-y-3.5',
              stageConsentAccepted
                ? 'bg-gradient-to-br from-emerald-50/40 via-white to-emerald-50/20 border-emerald-300 shadow-xs'
                : 'bg-gradient-to-br from-indigo-50/60 via-slate-50/30 to-white border-indigo-200/80'
            ]"
          >
            <!-- Checkbox Interactivo y Enunciado Formal -->
            <label
              for="active_stage_consent_check"
              class="flex items-start gap-3.5 cursor-pointer group select-none"
            >
              <input
                type="checkbox"
                id="active_stage_consent_check"
                :checked="stageConsentAccepted"
                @change="emit('update:consent', ($event.target as HTMLInputElement).checked)"
                class="mt-1 w-5 h-5 rounded-md text-[#4F5AF5] border-indigo-300 focus:ring-[#4F5AF5] cursor-pointer shrink-0 transition-transform group-hover:scale-105"
              />
              <div class="space-y-1.5 flex-1 min-w-0">
                <span v-if="activeNodeForm" class="block text-xs font-bold text-slate-900 leading-tight">
                  {{ activeNodeConsent.title }}
                </span>
                <p class="text-xs text-slate-700 leading-relaxed font-sans italic bg-white/80 p-3 rounded-xl border border-indigo-100/70 shadow-2xs">
                  “{{ activeNodeConsent.statement }}”
                </p>
                <p v-if="stageConsentAccepted" class="text-[11px] font-bold text-emerald-700 flex items-center gap-1 pt-0.5">
                  <CheckCircle class="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>Has otorgado tu conformidad formal</span>
                </p>
                <p v-else class="text-[11px] text-slate-400 font-medium">
                  Marca esta casilla para validar y otorgar tu visto bueno.
                </p>
              </div>
            </label>

            <!-- Metadata de Custodia Digital -->
            <div class="pt-2.5 border-t border-indigo-100/70 flex items-center justify-between text-[11px] text-slate-500 font-medium">
              <span class="flex items-center gap-1.5 text-indigo-700 font-semibold">
                <Lock class="w-3.5 h-3.5 text-indigo-600" /> Custodia Digital IACS
              </span>
              <span class="font-mono text-[10px] text-slate-400">Versión v{{ activeNodeConsent.version || '1.0' }}</span>
            </div>
          </div>
        </div>

        <!-- ── Banner de Alerta: Requisitos de Etapa Pendientes ── -->
        <div v-if="!isStageReadyToApprove" class="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-2.5 text-xs text-amber-800">
          <AlertTriangle class="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span class="font-bold block">Requisitos de etapa pendientes:</span>
            <span v-if="missingStageFields.length > 0">
              • Campos obligatorios sin completar: <strong>{{ missingStageFields.join(', ') }}</strong>.
            </span>
            <span v-if="activeNodeConsent && !stageConsentAccepted">
              • Debes marcar la casilla de aceptación de la declaración legal.
            </span>
          </div>
        </div>

        <!-- ── Botones de Transición Directos (Aprobación / Continuar) ── -->
        <div v-if="forwardEdges && forwardEdges.length > 0" class="pt-2 space-y-2">
          <button
            v-for="edge in forwardEdges"
            :key="edge.id"
            type="button"
            :disabled="!isStageReadyToApprove || isSubmitting"
            @click="emit('execute-transition', edge)"
            :style="isStageReadyToApprove ? getEdgeStyle(edge) : undefined"
            :class="[
              'w-full py-3 px-4 rounded-xl font-bold text-xs sm:text-sm shadow-sm flex items-center justify-center gap-2 transition-all cursor-pointer',
              isStageReadyToApprove
                ? 'hover:shadow-md hover:scale-[1.01] active:scale-[0.99] text-white bg-[#EB5F46]'
                : 'bg-slate-100 border border-slate-200 text-slate-400 cursor-not-allowed opacity-80'
            ]"
          >
            <Send v-if="!isSubmitting" class="w-4 h-4 shrink-0" />
            <span v-if="isSubmitting">Procesando firma y avance...</span>
            <span v-else>{{ getEdgeLabel(edge) }}</span>
          </button>
          <p v-if="!isStageReadyToApprove" class="text-[11px] text-center text-amber-700 font-medium">
            {{ activeNodeConsent && !stageConsentAccepted ? 'Marca la casilla de consentimiento para habilitar este botón.' : 'Completa los requisitos indicados para continuar.' }}
          </p>
        </div>

        <!-- ── Footer Info de la Ficha ── -->
        <div class="pt-2 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs">
          <span class="text-[11px] text-slate-400">
            * Los datos y firmas se guardan automáticamente.
          </span>
          <span v-if="isStageReadyToApprove" class="text-[11px] font-semibold text-emerald-600 flex items-center gap-1.5">
            <CheckCircle class="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>Listo para avanzar</span>
          </span>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════════════ -->
    <!-- ── CASO B: RESUMEN EJECUTIVO / ESTADO DEL REQUERIMIENTO ────────── -->
    <!-- (Se muestra cuando no aplica formulario activo para el rol actual) -->
    <!-- ══════════════════════════════════════════════════════════════════ -->
    <div
      v-else
      class="bg-white rounded-3xl border border-slate-200/90 shadow-sm p-6 space-y-4"
    >
      <div class="flex items-center gap-3 pb-3 border-b border-slate-100">
        <div class="w-10 h-10 rounded-2xl bg-indigo-50 text-[#4F5AF5] flex items-center justify-center font-bold shadow-2xs">
          <Layers class="w-5 h-5" />
        </div>
        <div>
          <h3 class="text-sm font-bold text-slate-900">Estado del Requerimiento</h3>
          <span class="text-xs font-semibold text-slate-500">Resumen y trazabilidad de flujo</span>
        </div>
      </div>

      <div class="space-y-2.5 text-xs">
        <div class="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
          <span class="font-semibold text-slate-500">Estado Actual:</span>
          <span class="font-bold text-slate-800">{{ initiative.status }}</span>
        </div>
        <div v-if="initiative.form_data?.bp_ti_asignado || initiative.form_data?.bp_ti_responsable" class="flex items-center justify-between p-3 rounded-xl bg-indigo-50/60 border border-indigo-100">
          <span class="font-semibold text-indigo-700">BP TI Responsable:</span>
          <span class="font-bold text-indigo-900">{{ initiative.form_data?.bp_ti_asignado || initiative.form_data?.bp_ti_responsable }}</span>
        </div>

        <!-- Aprobadores Siguientes (Configurado en el Diseñador de Workflow) -->
        <div
          v-if="shouldShowNextApprovers"
          class="p-3.5 rounded-2xl bg-gradient-to-br from-indigo-50/50 via-slate-50 to-white border border-indigo-100/90 shadow-2xs space-y-2.5"
        >
          <div class="flex items-center justify-between">
            <span class="font-bold text-slate-800 text-xs flex items-center gap-1.5">
              <Building2 class="w-3.5 h-3.5 text-[#4F5AF5]" />
              {{ nextApproversTitle || 'Aprobadores siguientes:' }}
            </span>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-[#4F5AF5] border border-indigo-200/70">
              {{ (nextApproversList || []).length }} {{ (nextApproversList || []).length === 1 ? 'aprobador' : 'aprobadores' }}
            </span>
          </div>

          <div class="bg-white border border-slate-200/80 rounded-xl overflow-hidden divide-y divide-slate-100 shadow-2xs">
            <div v-if="!nextApproversList || nextApproversList.length === 0" class="p-3 text-center text-slate-400 italic text-[11px]">
              Sin aprobadores asignados para esta etapa
            </div>
            <div v-else class="max-h-56 overflow-y-auto divide-y divide-slate-100">
              <div
                v-for="vp in nextApproversList"
                :key="(typeof vp === 'object' ? (vp.id || vp.name) : vp)"
                class="p-2.5 px-3 flex items-center justify-between hover:bg-slate-50 transition-colors"
              >
                <div class="min-w-0 pr-2">
                  <div class="flex items-center gap-1.5">
                    <span class="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" />
                    <span class="font-bold text-slate-800 truncate text-xs">
                      {{ typeof vp === 'object' ? vp.name : vp }}
                    </span>
                  </div>
                  <p v-if="typeof vp === 'object' && vp.role && vp.role !== vp.name" class="text-[10px] text-slate-400 pl-3">
                    {{ vp.role }}
                  </p>
                </div>
                <span v-if="typeof vp === 'object' && vp.email" class="text-[10px] text-slate-400 shrink-0">
                  {{ vp.email }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Quick Help / Info Pill Institucional (Custodia Digital) ── -->
    <div class="p-4 rounded-2xl bg-slate-50/80 border border-slate-200/60 text-[11px] text-slate-500 space-y-1">
      <div class="flex items-center gap-1.5 font-bold text-slate-700">
        <ShieldCheck class="w-4 h-4 text-[#4F5AF5]" />
        <span>Custodia Digital IACS</span>
      </div>
      <p class="leading-relaxed">
        Las aprobaciones, consentimientos y evaluaciones técnicas son registradas con firma electrónica e inmutabilidad en base de datos.
      </p>
    </div>
  </div>
</template>
