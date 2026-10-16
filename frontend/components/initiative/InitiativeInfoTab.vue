<script setup lang="ts">
import { ref, computed, nextTick } from 'vue';
import {
  Target, Sparkles, Cpu, Layers, Calculator, HelpCircle,
  FileText, Image as ImageIcon, Paperclip, Download, Pencil,
  Save, X, AlertTriangle, Clock, Info, Check, Upload, Loader2,
  Lock, User, Tag, MessageSquare
} from 'lucide-vue-next';
import { formatDateDDMMYYYY, getValueCaseInsensitive } from '~/utils/initiativeHistory';

const props = defineProps<{
  initiative: any;
  isAdmin?: boolean;
  currentUserRole?: string;
  isSaving?: boolean;
  canEdit?: boolean;
}>();

const emit = defineEmits<{
  (e: 'save-edits', updatedFormData: Record<string, any>): void;
  (e: 'submit-subsanacion', payload: { comment: string; files: any[] }): void;
}>();

// Modo Edición
const isEditMode = ref(false);
const editedFormData = ref<Record<string, any>>({});

// Estado para Subsanación (cuando está Observada)
const subsanacionComment = ref('');
const subsanacionFiles = ref<any[]>([]);
const isUploadingSubsanacion = ref(false);

const isObservedState = computed(() => {
  const st = (props.initiative?.status || '').toLowerCase();
  return st.includes('observad');
});

const currentObservation = computed(() => {
  return props.initiative?.form_data?._current_observation || null;
});

// Inicializar edición
const startEditMode = () => {
  if (props.canEdit === false) return;
  editedFormData.value = JSON.parse(JSON.stringify(props.initiative?.form_data || {}));
  isEditMode.value = true;
};

const cancelEditMode = () => {
  isEditMode.value = false;
  editedFormData.value = {};
};

const saveEdits = () => {
  emit('save-edits', editedFormData.value);
  isEditMode.value = false;
};

// ─── Gestión de Archivos Adjuntos de Soporte para Subsanación ───
const fileInputRef = ref<HTMLInputElement | null>(null);
const isDragging = ref(false);

const formatFileSize = (bytes: number): string => {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const triggerFileInput = () => {
  fileInputRef.value?.click();
};

const processFiles = (files: FileList | File[]) => {
  Array.from(files).forEach((file) => {
    const isText = file.type.includes('text') || file.name.endsWith('.txt');
    const maxBytes = (isText ? 10 : 25) * 1024 * 1024;
    if (file.size > maxBytes) {
      alert(`El archivo "${file.name}" supera el tamaño máximo permitido (${isText ? '10 MB' : '25 MB'}).`);
      return;
    }

    if (subsanacionFiles.value.some(f => f.name === file.name && f.rawSize === file.size)) {
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      subsanacionFiles.value.push({
        name: file.name,
        size: formatFileSize(file.size),
        rawSize: file.size,
        type: file.type || 'application/octet-stream',
        url: e.target?.result as string,
      });
    };
    reader.readAsDataURL(file);
  });
};

const handleFileInput = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    processFiles(target.files);
    target.value = '';
  }
};

const handleDrop = (e: DragEvent) => {
  isDragging.value = false;
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
    processFiles(e.dataTransfer.files);
  }
};

const removeSubsanacionFile = (index: number) => {
  subsanacionFiles.value.splice(index, 1);
};

const getFileIcon = (fileName: string) => {
  const ext = fileName.split('.').pop()?.toLowerCase() || '';
  if (ext === 'pdf') return 'pdf';
  if (['doc', 'docx'].includes(ext)) return 'word';
  if (['xls', 'xlsx', 'csv'].includes(ext)) return 'excel';
  if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'].includes(ext)) return 'image';
  return 'file';
};

defineExpose({
  startEditMode,
  cancelEditMode,
  getSubsanacionData: () => ({
    comment: subsanacionComment.value.trim(),
    files: subsanacionFiles.value,
  }),
  clearSubsanacion: () => {
    subsanacionComment.value = '';
    subsanacionFiles.value = [];
  },
});

const submitSubsanacion = () => {
  if (!subsanacionComment.value.trim() && subsanacionFiles.value.length === 0) {
    alert('Por favor describe las correcciones realizadas o adjunta archivos de soporte.');
    return;
  }
  emit('submit-subsanacion', {
    comment: subsanacionComment.value.trim(),
    files: subsanacionFiles.value,
  });
  subsanacionComment.value = '';
  subsanacionFiles.value = [];
};

// Resolver valor del campo de forma insensible a mayúsculas
const getVal = (key: string) => {
  if (isEditMode.value) {
    return getValueCaseInsensitive(editedFormData.value, key) ?? '';
  }
  const fdVal = getValueCaseInsensitive(props.initiative?.form_data, key);
  if (fdVal !== undefined && fdVal !== null && fdVal !== '') return fdVal;
  return getValueCaseInsensitive(props.initiative?.summary, key) ?? '';
};

const setVal = (key: string, val: any) => {
  editedFormData.value[key] = val;
};

// Helper para descargar archivos
const downloadFile = (url: string, filename: string) => {
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.target = '_blank';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// Tooltips descriptivos
const TOOLTIPS: Record<string, string> = {
  titulo: 'Título formal: Verbo en infinitivo + objeto + impacto de negocio',
  objetivo: 'Propósito medible y principal que alcanzará esta iniciativa',
  descripcion_de_la_necesidad: 'Contexto detallado de la problemática y necesidad que impulsa el proyecto',
  fecha_requerida: 'Fecha objetivo institucional requerida por el negocio',
  qu_pasa_si_no_lo_tenemos_en_esta_fecha: 'Consecuencias operativas, comerciales o de cumplimiento si se retrasa la entrega',
  descripcin_del_problema_o_desafo_situacin_actual: 'Situación operativa actual, fricciones y dolor existente en el proceso',
  pilar_estrategico: 'Alineación con los pilares del plan estratégico institucional',
  beneficio_cuantitativo_anual: 'Ahorro proyectado, incremento de ingresos o reducción de horas/hombre',
  beneficio_cualitativo: 'Mejora en experiencia del estudiante, calidad o satisfacción',
  es_necesidad_spo: 'Indica si clasifica como un proyecto de Strategic Planning & Operations',
  proceso_y_areas_impactadas: 'Áreas operativas, sedes o procesos transversales involucrados',
  es_un_proceso_nuevo: 'Define si el flujo es una creación desde cero o una optimización de uno existente',
  usuarios_beneficiados: 'Cantidad estimada de usuarios finales o colaboradores impactados',
  qu_escenarios_de_pruebas_debemos_considerar: 'Criterios de aceptación y escenarios críticos para la validación funcional',
};

// Campos de Sección 1: Propósito & Caso de Negocio
const section1Fields = [
  { key: 'titulo', label: 'TÍTULO DE LA INICIATIVA', type: 'text' },
  { key: 'objetivo', label: 'OBJETIVO PRINCIPAL', type: 'textarea' },
  { key: 'descripcion_de_la_necesidad', label: 'DESCRIPCIÓN DE LA NECESIDAD', type: 'textarea' },
  { key: 'fecha_requerida', label: 'FECHA REQUERIDA DE ENTREGA', type: 'date' },
  { key: 'qu_pasa_si_no_lo_tenemos_en_esta_fecha', label: '¿QUÉ PASA SI NO LO TENEMOS EN ESTA FECHA?', type: 'textarea' },
  { key: 'descripcin_del_problema_o_desafo_situacin_actual', label: 'DESCRIPCIÓN DEL PROBLEMA O DESAFÍO (SITUACIÓN ACTUAL)', type: 'textarea' },
];

// Campos de Sección 2: Retorno & Alineación Estratégica
const section2Fields = [
  { key: 'pilar_estrategico', label: 'PILAR ESTRATÉGICO', type: 'text' },
  { key: 'beneficio_cuantitativo_anual', label: 'BENEFICIO CUANTITATIVO ANUAL', type: 'text' },
  { key: 'beneficio_cualitativo', label: 'BENEFICIO CUALITATIVO', type: 'textarea' },
  { key: 'es_necesidad_spo', label: '¿ES NECESIDAD SPO?', type: 'text' },
];

// Campos de Sección 3: Alcance Operativo & Escenarios de Prueba
const section3Fields = [
  { key: 'proceso_y_areas_impactadas', label: 'PROCESO Y ÁREAS IMPACTADAS', type: 'text' },
  { key: 'es_un_proceso_nuevo', label: '¿ES UN PROCESO NUEVO?', type: 'text' },
  { key: 'usuarios_beneficiados', label: 'USUARIOS BENEFICIADOS', type: 'number' },
  { key: 'qu_escenarios_de_pruebas_debemos_considerar', label: '¿QUÉ ESCENARIOS DE PRUEBAS DEBEMOS CONSIDERAR?', type: 'textarea' },
];

// Datos complementarios
const hasAdditionalData = computed(() => {
  const fd = props.initiative?.form_data || {};
  return Boolean(
    fd.sistemas_afectados ||
    fd.tipo_solucion ||
    fd.observaciones_adicionales ||
    fd.adjuntos_sustento ||
    fd.attached_file
  );
});

// Datos de estimación (Sección 5)
const hasEstimationData = computed(() => {
  const fd = props.initiative?.form_data || {};
  return Boolean(
    fd.presupuesto_estimado_usd ||
    fd.monto_estimado_usd ||
    fd.tiempo_atencion_esfuerzo ||
    fd.justificacion_presupuesto ||
    fd.analista_responsable ||
    fd.fecha_fin_estimacion
  );
});
</script>

<template>
  <div class="space-y-6">
    <!-- ── BARRA DE SECCIÓN: EXPEDIENTE FORMAL DE REQUERIMIENTO ── -->
    <div class="flex items-center justify-between bg-white p-3.5 px-5 rounded-2xl border border-slate-200/90 shadow-2xs">
      <div class="flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center font-bold">
          <FileText class="w-4 h-4 text-slate-600" />
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-slate-800">Expediente Formal de Requerimiento</span>
          <span v-if="isEditMode" class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200 animate-pulse">
            Modo Edición Activo
          </span>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <template v-if="canEdit">
          <template v-if="isEditMode">
            <button
              type="button"
              @click="cancelEditMode"
              class="px-3 py-1.5 rounded-xl text-xs font-bold text-slate-600 bg-white hover:bg-slate-50 border border-slate-200 transition-all cursor-pointer shadow-2xs"
            >
              Cancelar
            </button>
            <button
              type="button"
              @click="saveEdits"
              :disabled="isSaving"
              class="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-xs font-bold text-white bg-[#4F5AF5] hover:bg-[#3F49E0] transition-all cursor-pointer shadow-2xs disabled:opacity-50"
            >
              <Save class="w-3.5 h-3.5" />
              <span>{{ isSaving ? 'Guardando...' : 'Guardar Cambios' }}</span>
            </button>
          </template>
        </template>
        <template v-else>
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold bg-slate-100 text-slate-500 border border-slate-200/80">
            <Lock class="w-3 h-3 text-slate-400" />
            Solo Lectura
          </span>
        </template>
      </div>
    </div>

    <!-- ── PANEL DE OBSERVACIÓN ACTIVA (Diseño Ejecutivo y Alta UX) ── -->
    <div v-if="isObservedState" class="bg-white rounded-2xl border border-amber-200/90 shadow-[0_4px_24px_-4px_rgba(245,158,11,0.08)] overflow-hidden transition-all">
      <!-- Línea superior de acento con gradiente -->
      <div class="h-1 bg-gradient-to-r from-amber-500 via-orange-400 to-amber-500"></div>

      <!-- Cabecera de la Observación -->
      <div class="px-6 py-4.5 bg-gradient-to-b from-amber-50/40 to-white border-b border-amber-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="flex items-center gap-3.5">
          <div class="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-600 border border-amber-200/90 flex items-center justify-center shrink-0 shadow-2xs">
            <AlertTriangle class="w-5 h-5 stroke-[2.2]" />
          </div>
          <div>
            <div class="flex items-center gap-2.5 flex-wrap">
              <h3 class="text-sm sm:text-base font-bold text-slate-900 tracking-tight">Observación Activa</h3>
              <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100/90 text-amber-900 border border-amber-200 shadow-2xs">
                <Tag class="w-3 h-3 text-amber-700" />
                {{ currentObservation?.category || 'General' }}
              </span>
            </div>
            <p class="text-xs text-slate-500 mt-1 flex items-center gap-2 flex-wrap">
              <span>Formulada por <strong class="text-slate-800 font-semibold">{{ currentObservation?.observed_by || 'Responsable' }}</strong> ({{ (currentObservation?.user_role || 'BP TI').toUpperCase() }})</span>
              <span class="text-slate-300">•</span>
              <span class="inline-flex items-center gap-1 text-slate-500">
                <Clock class="w-3 h-3 text-slate-400" />
                {{ currentObservation?.date ? formatDateDDMMYYYY(currentObservation.date) : '' }}
              </span>
            </p>
          </div>
        </div>

        <div class="shrink-0 self-start sm:self-center">
          <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500 text-white shadow-2xs">
            <span class="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></span>
            Pendiente de Subsanación
          </span>
        </div>
      </div>

      <div class="p-6 space-y-6">
        <!-- 1. Detalle del Cuestionamiento (Bloque Dictamen Ejecutivo) -->
        <div class="rounded-xl border border-amber-200/80 bg-gradient-to-r from-amber-50/40 via-[#FFFDF7] to-white p-4 sm:p-5 shadow-2xs">
          <div class="flex items-start gap-3">
            <div class="w-7 h-7 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center shrink-0 mt-0.5 shadow-2xs">
              <MessageSquare class="w-3.5 h-3.5" />
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex items-center justify-between mb-1.5">
                <span class="text-[11px] font-bold uppercase tracking-wider text-amber-900 flex items-center gap-1.5">
                  Detalle del cuestionamiento o ajuste solicitado
                </span>
                <span class="text-[10px] text-amber-800 font-semibold bg-amber-100/70 px-2 py-0.5 rounded border border-amber-200/60">
                  Dictamen Oficial
                </span>
              </div>
              <div class="text-sm text-slate-800 leading-relaxed font-normal whitespace-pre-wrap bg-white p-3.5 rounded-xl border border-amber-200/60 shadow-2xs">
                {{ currentObservation?.details || 'Se requiere subsanar la iniciativa para continuar con el flujo de aprobación.' }}
              </div>
            </div>
          </div>
        </div>

        <!-- 2. Respuesta de Subsanación / Justificación Técnica -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <label class="block text-xs font-bold text-slate-800 uppercase tracking-wider">
                Respuesta de Subsanación y Justificación Técnica
              </label>
              <span class="text-[10px] text-slate-400 font-normal hidden sm:inline">
                (Aclaraciones, correcciones o sustento técnico)
              </span>
            </div>
            <div class="flex items-center gap-2">
              <span
                :class="[
                  'text-[11px] font-mono font-semibold px-2 py-0.5 rounded-md transition-colors',
                  subsanacionComment.length > 0 ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'text-slate-400 bg-slate-100'
                ]"
              >
                {{ subsanacionComment.length }} caracteres
              </span>
            </div>
          </div>

          <textarea
            v-model="subsanacionComment"
            placeholder="Describe de forma detallada las acciones tomadas para resolver la observación, los acuerdos alcanzados o las aclaraciones pertinentes..."
            rows="3"
            class="w-full p-4 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5] text-xs sm:text-sm text-slate-800 placeholder:text-slate-400 leading-relaxed resize-y min-h-[90px] transition-all bg-slate-50/40 focus:bg-white shadow-2xs"
          />
        </div>

        <!-- 3. Archivos Adjuntos de Soporte (Dropzone Elegante & Compacto) -->
        <div class="space-y-2.5">
          <div class="flex items-center justify-between">
            <div>
              <label class="block text-xs font-bold text-slate-800 uppercase tracking-wider">
                Archivos Adjuntos de Soporte
              </label>
              <p class="text-[11px] text-slate-500">
                Documentos, diagramas o evidencias que sustentan el levantamiento de la observación.
              </p>
            </div>
            <span class="text-[10px] text-slate-500 font-medium bg-slate-100 px-2 py-0.5 rounded-md hidden sm:inline">
              Máx. 25 MB por archivo
            </span>
          </div>

          <!-- Input File Oculto -->
          <input
            ref="fileInputRef"
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.png,.jpg,.jpeg,.gif,.svg,.webp,.txt"
            class="hidden"
            @change="handleFileInput"
          />

          <!-- Dropzone Interactivo con Animación y Feedback -->
          <div
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
            @click="triggerFileInput"
            :class="[
              'border border-dashed rounded-xl p-4 sm:p-5 transition-all cursor-pointer group flex flex-col sm:flex-row items-center justify-between gap-4',
              isDragging
                ? 'border-indigo-500 bg-indigo-50/40 shadow-inner'
                : 'border-slate-300 hover:border-indigo-400 bg-slate-50/50 hover:bg-indigo-50/20'
            ]"
          >
            <div class="flex items-center gap-3.5 text-center sm:text-left">
              <div class="w-10 h-10 rounded-xl bg-white border border-slate-200 shadow-2xs flex items-center justify-center text-slate-500 group-hover:text-[#4F5AF5] group-hover:border-indigo-200 group-hover:scale-105 transition-all shrink-0">
                <Upload class="w-5 h-5 stroke-[2]" />
              </div>
              <div>
                <p class="text-xs sm:text-[13px] text-slate-700 font-medium">
                  <span class="text-[#4F5AF5] font-bold group-hover:underline">Haz clic para examinar</span>
                  <span class="text-slate-500"> o arrastra archivos aquí</span>
                </p>
                <div class="flex items-center gap-1.5 mt-1 flex-wrap justify-center sm:justify-start">
                  <span class="text-[10px] font-bold px-1.5 py-0.2 rounded bg-rose-50 text-rose-700 border border-rose-100">PDF</span>
                  <span class="text-[10px] font-bold px-1.5 py-0.2 rounded bg-blue-50 text-blue-700 border border-blue-100">Word</span>
                  <span class="text-[10px] font-bold px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-700 border border-emerald-100">Excel</span>
                  <span class="text-[10px] font-bold px-1.5 py-0.2 rounded bg-purple-50 text-purple-700 border border-purple-100">Imágenes</span>
                  <span class="text-[10px] font-bold px-1.5 py-0.2 rounded bg-slate-100 text-slate-600">Texto</span>
                </div>
              </div>
            </div>
            
            <button
              type="button"
              @click.stop="triggerFileInput"
              class="px-3.5 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs group-hover:border-indigo-200 group-hover:text-indigo-600 transition-all shrink-0 cursor-pointer"
            >
              Seleccionar archivos
            </button>
          </div>

          <!-- Lista de Archivos Adjuntos Seleccionados con Tarjetas Modernas -->
          <div v-if="subsanacionFiles.length > 0" class="space-y-2 pt-1">
            <div class="text-[11px] font-bold text-slate-700 flex items-center justify-between">
              <span class="flex items-center gap-1.5">
                <Check class="w-3.5 h-3.5 text-emerald-600" />
                Archivos adjuntados para la subsanación ({{ subsanacionFiles.length }}):
              </span>
              <span class="text-[10px] text-slate-400">Se registrarán en la cadena de custodia</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div
                v-for="(f, fIdx) in subsanacionFiles"
                :key="fIdx"
                class="flex items-center justify-between p-2.5 rounded-xl bg-white border border-slate-200 hover:border-indigo-200 shadow-2xs transition-all group"
              >
                <div class="flex items-center gap-2.5 min-w-0 pr-2">
                  <div class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 shadow-2xs"
                    :class="{
                      'bg-red-50 text-red-600 border border-red-100': getFileIcon(f.name) === 'pdf',
                      'bg-blue-50 text-blue-600 border border-blue-100': getFileIcon(f.name) === 'word',
                      'bg-emerald-50 text-emerald-600 border border-emerald-100': getFileIcon(f.name) === 'excel',
                      'bg-purple-50 text-purple-600 border border-purple-100': getFileIcon(f.name) === 'image',
                      'bg-slate-100 text-slate-600 border border-slate-200': getFileIcon(f.name) === 'file',
                    }"
                  >
                    <FileText v-if="getFileIcon(f.name) === 'pdf' || getFileIcon(f.name) === 'word'" class="w-4 h-4" />
                    <Layers v-else-if="getFileIcon(f.name) === 'excel'" class="w-4 h-4" />
                    <ImageIcon v-else-if="getFileIcon(f.name) === 'image'" class="w-4 h-4" />
                    <Paperclip v-else class="w-4 h-4" />
                  </div>
                  <div class="min-w-0">
                    <p class="font-bold text-slate-800 truncate text-xs leading-tight" :title="f.name">
                      {{ f.name }}
                    </p>
                    <div class="flex items-center gap-2 mt-0.5">
                      <span class="text-[10px] text-slate-400 font-mono">{{ f.size }}</span>
                      <span class="text-[9px] px-1.5 py-0.2 rounded font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Listo
                      </span>
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-1 shrink-0">
                  <a
                    v-if="f.url"
                    :href="f.url"
                    target="_blank"
                    class="w-7 h-7 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 flex items-center justify-center transition-colors"
                    title="Ver / Descargar"
                  >
                    <Download class="w-3.5 h-3.5" />
                  </a>
                  <button
                    type="button"
                    @click.stop="removeSubsanacionFile(fIdx)"
                    class="w-7 h-7 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 flex items-center justify-center transition-colors cursor-pointer"
                    title="Quitar archivo"
                  >
                    <X class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 1. PROPÓSITO & CASO DE NEGOCIO (IDÉNTICO A IMAGEN 2) ── -->
    <div class="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <!-- Encabezado de la Card -->
      <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-gradient-to-r from-slate-50 to-white">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-xl bg-[#FFF0ED] text-[#EB5F46] border border-[#FCD9D2] flex items-center justify-center font-bold">
            <Target class="w-4 h-4" />
          </div>
          <div>
            <h3 class="text-sm font-extrabold text-slate-900 tracking-tight">
              1. Propósito & Caso de Negocio
            </h3>
            <p class="text-[11px] text-slate-500">
              Definición del dolor del negocio, objetivos y justificación de impacto.
            </p>
          </div>
        </div>
        <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FFF0ED] text-[#EB5F46] border border-[#FCD9D2]">
          Estratégico
        </span>
      </div>

      <!-- Filas de datos tabulares -->
      <div class="px-6 py-2 divide-y divide-slate-100">
        <div
          v-for="f in section1Fields"
          :key="f.key"
          class="flex gap-4 py-3.5 border-b border-[#F8FAFC] last:border-0 flex-col sm:flex-row sm:items-start"
        >
          <!-- Label Col -->
          <p class="text-xs font-semibold text-[#94A3B8] uppercase tracking-wider w-full sm:w-64 shrink-0 mt-0.5 break-words flex items-center gap-1.5">
            <span class="align-middle">{{ f.label }}</span>
            <span
              v-if="TOOLTIPS[f.key]"
              class="relative group inline-block align-middle cursor-help"
            >
              <HelpCircle class="w-3.5 h-3.5 text-[#94A3B8] hover:text-[#64748B] transition-colors shrink-0" />
              <span class="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block w-52 p-2.5 bg-[#1E293B] text-white text-[10px] font-normal normal-case leading-normal rounded-lg shadow-lg z-[999] text-center">
                {{ TOOLTIPS[f.key] }}
                <span class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-[#1E293B]" />
              </span>
            </span>
          </p>

          <!-- Value Col -->
          <div class="flex-1 min-w-0">
            <template v-if="!isEditMode">
              <div v-if="f.type === 'date'" class="text-sm text-[#334155] font-medium">
                {{ formatDateDDMMYYYY(getVal(f.key)) }}
              </div>
              <div v-else class="text-sm text-[#334155] leading-relaxed whitespace-pre-line font-normal">
                {{ getVal(f.key) || '—' }}
              </div>
            </template>
            <template v-else>
              <textarea
                v-if="f.type === 'textarea'"
                :value="getVal(f.key)"
                @input="setVal(f.key, ($event.target as HTMLTextAreaElement).value)"
                rows="2"
                class="w-full p-2.5 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-[#4F5AF5] focus:outline-none"
              />
              <input
                v-else-if="f.type === 'date'"
                type="date"
                :value="getVal(f.key)"
                @input="setVal(f.key, ($event.target as HTMLInputElement).value)"
                class="w-full p-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-[#4F5AF5] focus:outline-none"
              />
              <input
                v-else
                type="text"
                :value="getVal(f.key)"
                @input="setVal(f.key, ($event.target as HTMLInputElement).value)"
                class="w-full p-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-[#4F5AF5] focus:outline-none"
              />
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 2. RETORNO & ALINEACIÓN ESTRATÉGICA ── -->
    <div class="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-gradient-to-r from-emerald-50/40 to-white">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-100 flex items-center justify-center font-bold">
            <Sparkles class="w-4 h-4" />
          </div>
          <div>
            <h3 class="text-sm font-extrabold text-slate-900 tracking-tight">
              2. Retorno & Alineación Estratégica
            </h3>
            <p class="text-[11px] text-slate-500">
              Pilar institucional, retorno financiero estimado y clasificación SPO.
            </p>
          </div>
        </div>
        <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
          Retorno & Valor
        </span>
      </div>

      <div class="px-6 py-2 divide-y divide-slate-100">
        <div
          v-for="f in section2Fields"
          :key="f.key"
          class="flex gap-4 py-3.5 border-b border-[#F8FAFC] last:border-0 flex-col sm:flex-row sm:items-start"
        >
          <p class="text-xs font-semibold text-[#94A3B8] uppercase tracking-wider w-full sm:w-64 shrink-0 mt-0.5 break-words flex items-center gap-1.5">
            <span class="align-middle">{{ f.label }}</span>
            <span
              v-if="TOOLTIPS[f.key]"
              class="relative group inline-block align-middle cursor-help"
            >
              <HelpCircle class="w-3.5 h-3.5 text-[#94A3B8] hover:text-[#64748B] transition-colors shrink-0" />
              <span class="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block w-52 p-2.5 bg-[#1E293B] text-white text-[10px] font-normal normal-case leading-normal rounded-lg shadow-lg z-[999] text-center">
                {{ TOOLTIPS[f.key] }}
                <span class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-[#1E293B]" />
              </span>
            </span>
          </p>

          <div class="flex-1 min-w-0">
            <template v-if="!isEditMode">
              <div class="text-sm text-[#334155] leading-relaxed whitespace-pre-line font-normal">
                {{ getVal(f.key) || '—' }}
              </div>
            </template>
            <template v-else>
              <textarea
                v-if="f.type === 'textarea'"
                :value="getVal(f.key)"
                @input="setVal(f.key, ($event.target as HTMLTextAreaElement).value)"
                rows="2"
                class="w-full p-2.5 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-[#4F5AF5] focus:outline-none"
              />
              <input
                v-else
                type="text"
                :value="getVal(f.key)"
                @input="setVal(f.key, ($event.target as HTMLInputElement).value)"
                class="w-full p-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-[#4F5AF5] focus:outline-none"
              />
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 3. ALCANCE OPERATIVO & ESCENARIOS DE PRUEBA ── -->
    <div class="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-gradient-to-r from-purple-50/40 to-white">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 border border-purple-100 flex items-center justify-center font-bold">
            <Cpu class="w-4 h-4" />
          </div>
          <div>
            <h3 class="text-sm font-extrabold text-slate-900 tracking-tight">
              3. Alcance Operativo & Escenarios de Prueba
            </h3>
            <p class="text-[11px] text-slate-500">
              Procesos afectados, usuarios impactados y criterios de validación operativa.
            </p>
          </div>
        </div>
        <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
          Operación
        </span>
      </div>

      <div class="px-6 py-2 divide-y divide-slate-100">
        <div
          v-for="f in section3Fields"
          :key="f.key"
          class="flex gap-4 py-3.5 border-b border-[#F8FAFC] last:border-0 flex-col sm:flex-row sm:items-start"
        >
          <p class="text-xs font-semibold text-[#94A3B8] uppercase tracking-wider w-full sm:w-64 shrink-0 mt-0.5 break-words flex items-center gap-1.5">
            <span class="align-middle">{{ f.label }}</span>
            <span
              v-if="TOOLTIPS[f.key]"
              class="relative group inline-block align-middle cursor-help"
            >
              <HelpCircle class="w-3.5 h-3.5 text-[#94A3B8] hover:text-[#64748B] transition-colors shrink-0" />
              <span class="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block w-52 p-2.5 bg-[#1E293B] text-white text-[10px] font-normal normal-case leading-normal rounded-lg shadow-lg z-[999] text-center">
                {{ TOOLTIPS[f.key] }}
                <span class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-[#1E293B]" />
              </span>
            </span>
          </p>

          <div class="flex-1 min-w-0">
            <template v-if="!isEditMode">
              <div class="text-sm text-[#334155] leading-relaxed whitespace-pre-line font-normal">
                {{ getVal(f.key) || '—' }}
              </div>
            </template>
            <template v-else>
              <textarea
                v-if="f.type === 'textarea'"
                :value="getVal(f.key)"
                @input="setVal(f.key, ($event.target as HTMLTextAreaElement).value)"
                rows="2"
                class="w-full p-2.5 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-[#4F5AF5] focus:outline-none"
              />
              <input
                v-else-if="f.type === 'number'"
                type="number"
                :value="getVal(f.key)"
                @input="setVal(f.key, Number(($event.target as HTMLInputElement).value))"
                class="w-full p-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-[#4F5AF5] focus:outline-none"
              />
              <input
                v-else
                type="text"
                :value="getVal(f.key)"
                @input="setVal(f.key, ($event.target as HTMLInputElement).value)"
                class="w-full p-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-[#4F5AF5] focus:outline-none"
              />
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 4. DATOS COMPLEMENTARIOS & ARCHIVOS ADJUNTOS ── -->
    <div v-if="hasAdditionalData" class="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/60">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-xl bg-slate-100 text-slate-600 border border-slate-200 flex items-center justify-center font-bold">
            <Layers class="w-4 h-4" />
          </div>
          <div>
            <h3 class="text-sm font-extrabold text-slate-900 tracking-tight">
              4. Datos Complementarios & Evidencias
            </h3>
            <p class="text-[11px] text-slate-500">
              Sistemas core integrados, tipos de solución y documentos de sustento.
            </p>
          </div>
        </div>
      </div>

      <div class="px-6 py-4 space-y-4">
        <!-- Sistemas Afectados -->
        <div v-if="getVal('sistemas_afectados')" class="flex gap-4 py-2 border-b border-slate-100 flex-col sm:flex-row">
          <p class="text-xs font-semibold text-[#94A3B8] uppercase tracking-wider w-full sm:w-64 shrink-0">
            Sistemas Core Afectados
          </p>
          <div class="flex-1 flex flex-wrap gap-1.5">
            <template v-if="Array.isArray(getVal('sistemas_afectados'))">
              <span
                v-for="sis in getVal('sistemas_afectados')"
                :key="sis"
                class="px-2.5 py-1 bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200"
              >
                {{ sis }}
              </span>
            </template>
            <span v-else class="text-sm text-slate-700">{{ getVal('sistemas_afectados') }}</span>
          </div>
        </div>

        <!-- Archivos Adjuntos / Sustento -->
        <div v-if="getVal('adjuntos_sustento') || getVal('attached_file')" class="flex gap-4 py-2 flex-col sm:flex-row">
          <p class="text-xs font-semibold text-[#94A3B8] uppercase tracking-wider w-full sm:w-64 shrink-0">
            Documentos y Archivos de Sustento
          </p>
          <div class="flex-1 flex flex-wrap gap-2">
            <!-- Caso Array de Adjuntos -->
            <template v-if="Array.isArray(getVal('adjuntos_sustento'))">
              <div
                v-for="(file, idx) in getVal('adjuntos_sustento')"
                :key="idx"
                class="inline-flex items-center gap-2 px-3 py-1.5 bg-[#F1F5F9] border border-[#E2E8F0] rounded-xl text-xs font-semibold text-[#334155] shadow-2xs"
              >
                <Paperclip class="w-3.5 h-3.5 text-[#4F5AF5]" />
                <span class="truncate max-w-[220px]">{{ file.name }}</span>
                <span v-if="file.size" class="text-[10px] text-slate-400">
                  ({{ (file.size / 1024).toFixed(0) }} KB)
                </span>
                <button
                  v-if="file.url"
                  type="button"
                  @click="downloadFile(file.url, file.name)"
                  class="text-[#4F5AF5] hover:text-[#3F49E0] ml-1 p-0.5 rounded cursor-pointer"
                  title="Descargar"
                >
                  <Download class="w-3.5 h-3.5" />
                </button>
              </div>
            </template>

            <!-- Caso Archivo Único -->
            <template v-else-if="getVal('attached_file')">
              <div class="inline-flex items-center gap-2 px-3 py-1.5 bg-[#F1F5F9] border border-[#E2E8F0] rounded-xl text-xs font-semibold text-[#334155] shadow-2xs">
                <Paperclip class="w-3.5 h-3.5 text-[#4F5AF5]" />
                <span class="truncate max-w-[220px]">{{ getVal('attached_file')?.name || 'Documento de sustento' }}</span>
                <button
                  v-if="getVal('attached_file')?.url"
                  type="button"
                  @click="downloadFile(getVal('attached_file').url, getVal('attached_file').name)"
                  class="text-[#4F5AF5] hover:text-[#3F49E0] ml-1 p-0.5 rounded cursor-pointer"
                  title="Descargar"
                >
                  <Download class="w-3.5 h-3.5" />
                </button>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 5. ESTIMACIÓN TÉCNICA & PRESUPUESTO (LÍDER DE DOMINIO) ── -->
    <div v-if="hasEstimationData" class="bg-white rounded-2xl border-2 border-indigo-200/90 shadow-sm overflow-hidden">
      <div class="px-6 py-4 border-b border-indigo-100 flex items-center justify-between bg-gradient-to-r from-indigo-50/80 via-white to-indigo-50/30">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-xl bg-[#4F5AF5] text-white flex items-center justify-center font-bold shadow-xs">
            <Calculator class="w-4 h-4" />
          </div>
          <div>
            <h3 class="text-sm font-extrabold text-slate-900 tracking-tight">
              Estimación Técnica & Presupuesto (Líder de Dominio)
            </h3>
            <p class="text-[11px] text-slate-500">
              Evaluación técnica, esfuerzo de desarrollo y sustento presupuestal de TI.
            </p>
          </div>
        </div>
        <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-[#4F5AF5] border border-indigo-200">
          Etapa 6: Estimación TI
        </span>
      </div>

      <div class="p-6">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div v-if="getVal('presupuesto_estimado_usd') || getVal('monto_estimado_usd')" class="p-4 rounded-xl bg-gradient-to-br from-indigo-50/60 to-white border border-indigo-100/80 shadow-2xs">
            <span class="text-[10px] uppercase font-extrabold text-indigo-600 block mb-1">
              Presupuesto Estimado Necesario
            </span>
            <span class="text-xl font-black text-indigo-950 block">
              ${{ Number(getVal('presupuesto_estimado_usd') || getVal('monto_estimado_usd') || 0).toLocaleString() }} USD
            </span>
          </div>

          <div v-if="getVal('tiempo_atencion_esfuerzo')" class="p-4 rounded-xl bg-slate-50 border border-slate-100">
            <span class="text-[10px] uppercase font-bold text-slate-400 block mb-1">
              Tiempo Estimado de Atención
            </span>
            <span class="text-base font-black text-slate-800 block">
              {{ getVal('tiempo_atencion_esfuerzo') }}
            </span>
            <span class="text-[10px] text-slate-400">Esfuerzo estimado de TI</span>
          </div>

          <div v-if="getVal('requiere_presupuesto')" class="p-4 rounded-xl bg-slate-50 border border-slate-100">
            <span class="text-[10px] uppercase font-bold text-slate-400 block mb-1">
              ¿Requiere Presupuesto?
            </span>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-700">
              {{ getVal('requiere_presupuesto') }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
