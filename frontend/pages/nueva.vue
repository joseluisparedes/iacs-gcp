<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from "vue";
import {
  Check, CheckCircle2, Bot, ChevronRight, ChevronDown, Pencil, Save, Send,
  RotateCcw, ThumbsUp, ThumbsDown, Mic, MicOff, Paperclip, X,
  FileText, AlertCircle, Sparkles, Building2, User, HelpCircle,
  ArrowLeft, Eye, Download, Info, Image as ImageIcon, Volume2,
  Trash2, MessageSquare, ListChecks
} from "lucide-vue-next";

import { useAiAssistant } from '~/composables/useAiAssistant';
import { formatMarkdownToHtml, formatHtmlText } from '~/utils/formatHtml';

const config = useRuntimeConfig();
const apiBase = config.public.apiBase;
const router = useRouter();
const { showLoader, hideLoader } = useGlobalLoader();
const { aiName, aiAvatar, loadAiConfig } = useAiAssistant();

// ─── 7 Stages Workflow Timeline (Solo visible en Paso 3 de revisión) ──────────
const WORKFLOW_STAGES_TIMELINE = [
  { key: 'borrador', label: 'Registro', subtitle: 'Key User' },
  { key: 'eval_bp', label: 'Viabilidad BP TI', subtitle: 'Business Partner' },
  { key: 'aprob_bo', label: 'Patrocinio BO', subtitle: 'Business Owner' },
  { key: 'aprob_vp', label: 'Aprobación VP', subtitle: 'Vicepresidencia' },
  { key: 'asig_demanda', label: 'Demanda TI', subtitle: 'Gestor Demanda' },
  { key: 'ventana_est', label: 'Estimación', subtitle: 'Líder Dominio' },
  { key: 'planificacion', label: 'Planificación', subtitle: 'Producción' }
];

// Current step (1: Registro y Documentación, 2: Chat interactivo con Teo, 3: Resumen Ejecutivo)
const currentStep = ref(1);

// ─── Form Data ───────────────────────────────────────────────────────────────
const formData = ref<Record<string, any>>({
  vicepresidencia: '',
  direccion: '',
  institucion: '',
  registrador: 'Administrador General',
  titulo: '',
  objetivo: '',
  descripcion_de_la_necesidad: '',
  proceso_y_areas_impactadas: '',
  fecha_requerida: '',
  beneficio_cuantitativo_anual: '',
  es_necesidad_spo: 'No',
});

const vps = ref<any[]>([]);
const direcciones = ref<any[]>([]);
const filteredDirecciones = computed(() => {
  if (!formData.value.vicepresidencia) return [];
  const vpObj = vps.value.find(v => v.name === formData.value.vicepresidencia);
  if (!vpObj) return [];
  return direcciones.value.filter(d => d.vp_id === vpObj.id);
});

// File attachment state
const fileInputRef = ref<HTMLInputElement | null>(null);
const attachedFile = ref<{ name: string; size: number; content?: string } | null>(null);
const isUploadingFile = ref(false);

const handleFileUpload = async (e: Event) => {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  if (file.size > 25 * 1024 * 1024) {
    alert("El archivo supera el límite de 25 MB.");
    return;
  }

  isUploadingFile.value = true;
  attachedFile.value = {
    name: file.name,
    size: file.size,
    content: '',
  };

  try {
    const fd = new FormData();
    fd.append('file', file);
    const res: any = await $fetch(`${apiBase}/chat/attach-file`, {
      method: 'POST',
      body: fd,
    });
    if (res && (res.content || res.text)) {
      attachedFile.value = {
        name: file.name,
        size: file.size,
        content: res.content || res.text,
      };
    }
  } catch (err) {
    console.error("Error al extraer texto del documento adjunto:", err);
  } finally {
    isUploadingFile.value = false;
  }
};

// Form errors
const formErrors = ref<string[]>([]);

// ─── Chat with Teo State ─────────────────────────────────────────────────────
const chatHistory = ref<Array<{
  role: string;
  text: string;
  options?: string[];
  allowMultiple?: boolean;
}>>([]);
const currentMessage = ref('');
const isChatLoading = ref(false);
const suggestedOptions = ref<string[]>([]);
const selectedMultiOptions = ref<string[]>([]);
const ratedMessages = ref<Record<number, 'positive' | 'negative'>>({});
const chatEndRef = ref<HTMLDivElement | null>(null);
const chatInputRef = ref<HTMLTextAreaElement | null>(null);
const chatFileInputRef = ref<HTMLInputElement | null>(null);
const isRecording = ref(false);
const showChatModal = ref(false);

// Cuenta regresiva automática al finalizar la información recopilada
const countdownSeconds = ref<number | null>(null);
let countdownTimer: any = null;

const startCompletionCountdown = () => {
  if (countdownSeconds.value !== null) return;
  countdownSeconds.value = 3;
  if (countdownTimer) clearInterval(countdownTimer);
  countdownTimer = setInterval(() => {
    if (countdownSeconds.value !== null) {
      if (countdownSeconds.value > 1) {
        countdownSeconds.value--;
      } else {
        countdownSeconds.value = null;
        clearInterval(countdownTimer);
        goToStep3Summary();
      }
    }
  }, 1000);
};

const toHtmlDate = (val: string): string => {
  if (!val) return '';
  const trimmed = val.trim();
  const dmy = trimmed.match(/^(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{4})$/);
  if (dmy) {
    return `${dmy[3]}-${dmy[2].padStart(2, '0')}-${dmy[1].padStart(2, '0')}`;
  }
  return trimmed;
};

const toggleMultiOption = (opt: string) => {
  if (selectedMultiOptions.value.includes(opt)) {
    selectedMultiOptions.value = selectedMultiOptions.value.filter(x => x !== opt);
  } else {
    selectedMultiOptions.value.push(opt);
  }
};

const submitMultiOptions = () => {
  if (selectedMultiOptions.value.length === 0) return;
  const combined = selectedMultiOptions.value.join(', ');
  selectedMultiOptions.value = [];
  sendMessage(combined);
};

const toggleFormFieldMulti = (key: string, opt: string) => {
  if (!formData.value[key] || !Array.isArray(formData.value[key])) {
    formData.value[key] = [];
  }
  const idx = formData.value[key].indexOf(opt);
  if (idx > -1) {
    formData.value[key].splice(idx, 1);
  } else {
    formData.value[key].push(opt);
  }
};

const isFormFieldMultiSelected = (key: string, opt: string): boolean => {
  const current = formData.value[key];
  if (Array.isArray(current)) {
    return current.includes(opt);
  }
  if (typeof current === 'string') {
    return current.split(',').map(s => s.trim()).includes(opt);
  }
  return false;
};

const activeDropdownKey = ref<string | null>(null);

const toggleDropdown = (key: string) => {
  activeDropdownKey.value = activeDropdownKey.value === key ? null : key;
};

const closeDropdowns = (e: MouseEvent) => {
  const target = e.target as HTMLElement;
  if (!target?.closest?.('.multiselect-container')) {
    activeDropdownKey.value = null;
  }
};

const rateMessage = async (index: number, rating: 'positive' | 'negative') => {
  ratedMessages.value[index] = rating;
  try {
    await $fetch(`${apiBase}/training/feedback`, {
      method: 'POST',
      body: {
        message_index: index,
        agent_response: chatHistory.value[index]?.text,
        rating,
      },
    }).catch(() => null);
  } catch (e) {
    console.error('Error saving feedback', e);
  }
};

// ─── Dynamic Fields & Consent from DB (Sincronización Total con Configuración) ──
const allFields = ref<any[]>([]);
const consentStatement = ref<string>('Doy fe de que el levantamiento asistido por Teo representa fielmente la necesidad operativa de mi área y acepto los términos de alcance y fecha propuesta.');

const vpField = computed(() => allFields.value.find(f => f.key === 'vicepresidencia'));
const dirField = computed(() => allFields.value.find(f => f.key === 'direccion'));
const adjField = computed(() => allFields.value.find(f => f.key === 'adjuntos_sustento'));

const showVicepresidencia = computed(() => vpField.value ? vpField.value.ask_in_initial_form !== false : true);
const showDireccion = computed(() => dirField.value ? dirField.value.ask_in_initial_form !== false : true);
const showAdjuntos = computed(() => adjField.value ? adjField.value.ask_in_initial_form !== false : true);

const dynamicStep1Fields = computed(() => {
  return allFields.value.filter(f => 
    f.ask_in_initial_form === true && 
    !['vicepresidencia', 'direccion', 'registrador', 'adjuntos_sustento'].includes(f.key)
  );
});

const dynamicStep3Fields = computed(() => {
  return allFields.value.filter(f => 
    !['vicepresidencia', 'direccion', 'registrador', 'solicitante', 'adjuntos_sustento', 'titulo', 'objetivo', 'descripcion_de_la_necesidad', 'bp_ti_sugerido'].includes(f.key)
  );
});

// ─── Disclaimer Checkbox (Paso 3) ────────────────────────────────────────────
const disclaimerAccepted = ref(false);
const isSubmitting = ref(false);

// ─── Carga de Estructura Organizacional y Metadatos de Formulario ────────────
onMounted(async () => {
  loadAiConfig();
  try {
    const [vpRes, dirRes, fieldsRes, consentRes] = await Promise.all([
      $fetch<any[]>(`${apiBase}/vps`).catch(() => []),
      $fetch<any[]>(`${apiBase}/direcciones`).catch(() => []),
      $fetch<any[]>(`${apiBase}/fields`).catch(() => []),
      $fetch<any>(`${apiBase}/stage-consents/consent_key_user`).catch(() => null),
    ]);
    if (Array.isArray(vpRes)) vps.value = vpRes;
    if (Array.isArray(dirRes)) direcciones.value = dirRes;
    if (Array.isArray(fieldsRes) && fieldsRes.length > 0) {
      allFields.value = fieldsRes;
    }
    if (consentRes?.data?.statement) {
      consentStatement.value = consentRes.data.statement;
    }
  } catch (err) {
    console.error('Error fetching data in nueva.vue:', err);
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('click', closeDropdowns);
  }
});

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('click', closeDropdowns);
  }
});

// ─── Transiciones de Pasos con Validación Dinámica ───────────────────────────
const handleStartChatWithValidation = async () => {
  formErrors.value = [];

  if (showVicepresidencia.value && vpField.value?.is_required !== false && !formData.value.vicepresidencia) {
    formErrors.value.push("El campo Vicepresidencia es obligatorio.");
  }
  if (showDireccion.value && dirField.value?.is_required !== false && !formData.value.direccion) {
    formErrors.value.push("El campo Dirección es obligatorio.");
  }

  for (const f of dynamicStep1Fields.value) {
    if (f.is_required) {
      const val = formData.value[f.key];
      const isEmpty = val === undefined || val === null || (typeof val === 'string' && val.trim() === '') || (Array.isArray(val) && val.length === 0);
      if (isEmpty) {
        formErrors.value.push(`El campo "${f.label}" es obligatorio.`);
      }
    }
  }

  if (formErrors.value.length > 0) return;

  currentStep.value = 2;

  // Si el usuario adjuntó un documento en el Paso 1, Teo analiza de inmediato su contenido:
  if (attachedFile.value && (attachedFile.value.content || attachedFile.value.name)) {
    if (isUploadingFile.value) {
      showLoader({ title: 'Procesando documento', subtitle: 'Extrayendo contenido de sustento con Teo...', overlay: true });
      let attempts = 0;
      while (isUploadingFile.value && attempts < 25) {
        await new Promise(r => setTimeout(r, 200));
        attempts++;
      }
      hideLoader();
    }
    chatHistory.value = [];
    nextTick(() => {
      sendMessage();
    });
    return;
  }

  // Si no hay archivo adjunto previo, Teo inicia con su saludo oficial de bienvenida
  if (chatHistory.value.length === 0) {
    const welcomeText = `¡Hola! Soy Teo, tu asesor de arquitectura y proyectos de TI. Cuéntame qué necesidad, dolor operativo o mejora deseas abordar. También puedes adjuntar documentos o evidencias de sustento con el botón del clip 📎 para analizarlos y estructurar tu iniciativa en conjunto.`;
    chatHistory.value = [{
      role: 'model',
      text: welcomeText,
      options: [],
      allowMultiple: false,
    }];
    suggestedOptions.value = [];
    selectedMultiOptions.value = [];
  }

  nextTick(() => {
    chatInputRef.value?.focus();
    chatEndRef.value?.scrollIntoView({ behavior: 'smooth' });
  });
};

const sendMessage = async (overrideText?: string) => {
  const textToSend = (overrideText !== undefined ? overrideText : currentMessage.value).trim();
  const currentAttached = attachedFile.value;

  if ((!textToSend && !currentAttached) || isChatLoading.value) return;

  selectedMultiOptions.value = [];

  // Construir texto visible en el historial
  let displayText = textToSend;
  if (!displayText && currentAttached) {
    displayText = `[Adjunto: ${currentAttached.name}]`;
  }

  // Construir mensaje enviado a la IA (con contenido o indicación del adjunto)
  let aiMessage = textToSend;
  if (currentAttached) {
    if (currentAttached.content) {
      aiMessage = `[El usuario adjuntó el archivo: ${currentAttached.name}]\n---\n${currentAttached.content}\n---\n${aiMessage ? 'Mensaje del usuario: ' + aiMessage : 'Por favor analiza a fondo este documento técnico y funcional de la iniciativa, extrae el título propuesto y el objetivo principal, y preséntamelos para su validación.'}`;
    } else {
      aiMessage = `[El usuario adjuntó el archivo: ${currentAttached.name}]\n${aiMessage ? 'Mensaje del usuario: ' + aiMessage : 'Por favor analiza este archivo en el contexto de la iniciativa.'}`.trim();
    }
    // Una vez adjuntado y enviado con el mensaje, se desvincula de la barra de entrada
    attachedFile.value = null;
  }

  chatHistory.value.push({ role: 'user', text: displayText });
  currentMessage.value = '';
  if (chatInputRef.value) {
    chatInputRef.value.style.height = 'auto';
  }
  suggestedOptions.value = [];
  isChatLoading.value = true;

  nextTick(() => {
    chatEndRef.value?.scrollIntoView({ behavior: 'smooth' });
  });

  try {
    const res: any = await $fetch(`${apiBase}/chat`, {
      method: 'POST',
      body: {
        history: chatHistory.value.map(h => ({ role: h.role, text: h.text })),
        message: aiMessage || displayText,
        initialData: formData.value,
        aiFields: allFields.value,
      },
    });

    let text = (res.text || '') as string;
    const options = res.options || [];
    const allowMultiple = Boolean(res.allow_multiple || res.allowMultiple);

    const isComplete = text.includes('[INFORMACION_COMPLETA]');
    if (isComplete) {
      text = text.replace(/\[INFORMACION_COMPLETA\]/g, '').trim();
    }

    chatHistory.value.push({
      role: 'model',
      text,
      options: isComplete ? [] : options,
      allowMultiple,
    });
    suggestedOptions.value = isComplete ? [] : options;

    if (isComplete) {
      startCompletionCountdown();
    }

    if (res.extractedFields) {
      const ef = res.extractedFields;
      if (ef.titulo || ef.titulo_iniciativa || ef.titulo_iniciativa_propuesto) {
        formData.value.titulo = ef.titulo || ef.titulo_iniciativa || ef.titulo_iniciativa_propuesto;
      }
      if (ef.objetivo || ef.objetivo_principal || ef.objetivo_principal_propuesto) {
        formData.value.objetivo = ef.objetivo || ef.objetivo_principal || ef.objetivo_principal_propuesto;
      }
      Object.assign(formData.value, res.extractedFields);
    }
  } catch (err) {
    console.error('Error in chat:', err);
    chatHistory.value.push({
      role: 'model',
      text: 'Entendido. He incorporado esta información a la ficha preliminar. ¿Qué sistemas o áreas se verían impactadas con esta solución?',
      options: ['Banner y Blackboard', 'Salesforce CRM', 'Portal de Pagos', 'Sin impacto en otros sistemas'],
      allowMultiple: false,
    });
    suggestedOptions.value = ['Banner y Blackboard', 'Salesforce CRM', 'Portal de Pagos', 'Sin impacto en otros sistemas'];
  } finally {
    isChatLoading.value = false;
    nextTick(() => {
      chatEndRef.value?.scrollIntoView({ behavior: 'smooth' });
    });
  }
};

const goToStep3Summary = async () => {
  if (countdownTimer) clearInterval(countdownTimer);
  countdownSeconds.value = null;
  showLoader({ title: 'Generando Resumen Ejecutivo', subtitle: 'Consolidando la ficha técnica estructurada con Teo...' });
  try {
    const summaryRes: any = await $fetch(`${apiBase}/summarize`, {
      method: 'POST',
      body: {
        history: chatHistory.value.map(h => ({ role: h.role, text: h.text })),
        initialData: formData.value,
        aiFields: allFields.value,
      },
    }).catch(() => null);

    if (summaryRes && typeof summaryRes === 'object') {
      for (const [key, val] of Object.entries(summaryRes)) {
        if (val !== undefined && val !== null && val !== '') {
          const matchedField = allFields.value.find(f => f.key === key);
          if (matchedField && matchedField.field_type === 'date') {
            formData.value[key] = toHtmlDate(String(val));
          } else {
            formData.value[key] = val;
          }
        }
      }
      if (summaryRes.titulo) formData.value.titulo = summaryRes.titulo;
      if (summaryRes.objetivo) formData.value.objetivo = summaryRes.objetivo;
      const desc = summaryRes.descripcion_de_la_necesidad || summaryRes.descripcion_necesidad;
      if (desc) {
        formData.value.descripcion_de_la_necesidad = desc;
        formData.value.descripcion_necesidad = desc;
      }
      if (summaryRes.justificacion) formData.value.justificacion = summaryRes.justificacion;
      if (summaryRes.impacto_esperado) formData.value.impacto_esperado = summaryRes.impacto_esperado;
      if (summaryRes.pilar_estrategico) formData.value.pilar_estrategico = summaryRes.pilar_estrategico;
      if (summaryRes.tipo_solucion) formData.value.tipo_solucion = summaryRes.tipo_solucion;
      if (summaryRes.requiere_presupuesto) formData.value.requiere_presupuesto = summaryRes.requiere_presupuesto;
    }
  } catch (err) {
    console.warn('Error in summarize:', err);
  } finally {
    hideLoader();
    if (!formData.value.titulo) {
      formData.value.titulo = `Iniciativa de modernización para ${formData.value.direccion || 'el área'}`;
    }
    if (!formData.value.objetivo) {
      formData.value.objetivo = `Optimización y automatización de procesos correspondientes a ${formData.value.direccion} en ${formData.value.institucion}.`;
    }
    if (!formData.value.descripcion_de_la_necesidad) {
      formData.value.descripcion_de_la_necesidad = formData.value.descripcion_necesidad || `Necesidad operativa identificada para agilizar tiempos de respuesta y trazabilidad tecnológica.`;
    }
    currentStep.value = 3;
    nextTick(() => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }
};

// ─── Guardar Borrador / Enviar a Aprobación ─────────────────────────────────
const handleSaveDraft = async () => {
  isSubmitting.value = true;
  try {
    await $fetch(`${apiBase}/initiatives`, {
      method: 'POST',
      body: {
        status: 'Borrador',
        form_data: { ...formData.value, _reached_summary: true },
        summary: {
          titulo: formData.value.titulo,
          objetivo: formData.value.objetivo,
          descripcionProblema: formData.value.descripcion_de_la_necesidad,
          complejidad: 'Media',
          riesgo: 'Bajo',
        },
        chat_history: chatHistory.value.map(h => ({ role: h.role, text: h.text })),
      },
    });
    alert('Borrador guardado exitosamente');
    await router.push('/dashboard');
  } catch (err: any) {
    alert('Error al guardar borrador: ' + (err.message || err));
  } finally {
    isSubmitting.value = false;
  }
};

const handleSubmitToBPTI = async () => {
  if (!disclaimerAccepted.value) {
    alert('Debes marcar la casilla de declaración y sustento del solicitante antes de enviar.');
    return;
  }
  isSubmitting.value = true;
  showLoader({
    title: 'Enviando Ficha de Iniciativa',
    subtitle: 'Registrando en la cadena de custodia y derivando al BP TI...',
    phrases: [
      'Conectando con el motor de gobernanza IACS...',
      'Validando directrices y políticas de TI...',
      'Generando expediente digital y sellado criptográfico...',
      'Notificando al Business Partner de TI asignado...'
    ],
    overlay: true,
  });
  try {
    await $fetch(`${apiBase}/initiatives`, {
      method: 'POST',
      body: {
        status: 'Pendiente de aprobación',
        form_data: { ...formData.value, _reached_summary: true },
        summary: {
          titulo: formData.value.titulo,
          objetivo: formData.value.objetivo,
          descripcionProblema: formData.value.descripcion_de_la_necesidad,
          complejidad: 'Media',
          riesgo: 'Bajo',
        },
        chat_history: chatHistory.value.map(h => ({ role: h.role, text: h.text })),
      },
    });
    alert('¡Iniciativa enviada exitosamente a la evaluación del Business Partner TI!');
    await router.push('/dashboard');
  } catch (err: any) {
    alert('Error al enviar iniciativa: ' + (err.message || err));
  } finally {
    isSubmitting.value = false;
    hideLoader();
  }
};

</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6 pb-16">
    <!-- ── LÍNEA DE TIEMPO CORPORATIVA (SOLO EN PASO 3 DE RESUMEN) ── -->
    <div v-if="currentStep === 3" class="bg-white rounded-2xl border border-slate-200/80 p-4 sm:p-5 shadow-xs space-y-3.5 mb-6">
      <div class="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-slate-100 text-xs">
        <div class="flex flex-wrap items-center gap-2">
          <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-800 border border-slate-200 shadow-2xs">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Estado: 1. Borrador
          </span>
          <span class="text-slate-300 hidden sm:inline">|</span>
          <span class="text-slate-500 font-medium text-[11px] sm:text-xs">
            Hasta antes de enviar al BP TI, la iniciativa permanece en borrador
          </span>
        </div>
        <div class="flex items-center gap-1.5 text-xs font-semibold text-[#4F5AF5] bg-[#EEF2FF] border border-[#E0E7FF] px-2.5 py-1 rounded-lg">
          <span class="text-slate-500">Paso 3 de 3:</span>
          <span class="font-bold text-[#4F5AF5]">Resumen y Validación de Ficha</span>
        </div>
      </div>

      <div class="overflow-x-auto pt-2 pb-2">
        <div class="flex items-start w-full min-w-[720px] relative">
          <div
            v-for="(stage, idx) in WORKFLOW_STAGES_TIMELINE"
            :key="stage.key"
            class="flex-1 relative flex flex-col items-center"
          >
            <div
              v-if="idx < WORKFLOW_STAGES_TIMELINE.length - 1"
              class="absolute top-[18px] left-1/2 w-full h-[3px] -translate-y-1/2 z-0 bg-slate-200"
            />
            <div class="flex flex-col items-center relative z-10 w-full px-1">
              <div
                :class="[
                  'w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-200',
                  idx === 0
                    ? 'bg-emerald-600 text-white ring-4 ring-emerald-100 shadow-sm'
                    : 'bg-white text-slate-400 border-2 border-slate-300'
                ]"
              >
                <Check v-if="idx === 0" class="w-4 h-4 stroke-[3]" />
                <div v-else class="w-2 h-2 rounded-full bg-slate-300" />
              </div>
              <span
                :class="[
                  'text-[11px] font-bold mt-2 text-center leading-tight px-1',
                  idx === 0 ? 'text-slate-900 font-black' : 'text-slate-400'
                ]"
              >
                {{ stage.label }}
              </span>
              <span class="text-[10px] font-medium text-center mt-0.5 leading-tight text-slate-400">
                {{ stage.subtitle }}
              </span>
              <span
                v-if="idx === 0"
                class="inline-flex items-center mt-1 px-2 py-0.5 rounded-full text-[9px] font-black tracking-tight bg-emerald-50 text-emerald-700 border border-emerald-200/80 shadow-2xs"
              >
                En edición
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── PASO 1: REGISTRO DE REQUERIMIENTO Y DOCUMENTACIÓN (IDÉNTICO A IMAGEN 1) ── -->
    <div v-if="currentStep === 1" class="bg-white rounded-2xl border border-[#E2E8F0] shadow-[0_1px_3px_rgba(0,0,0,.07)] overflow-hidden">
      <!-- Encabezado de la Tarjeta -->
      <div class="px-8 pt-8 pb-6 border-b border-[#F1F5F9] flex justify-between items-start gap-4">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-[#EEF2FF] flex items-center justify-center">
            <span class="text-[#4F5AF5] text-sm">📋</span>
          </div>
          <div>
            <h2 class="text-lg font-bold text-[#1E293B]">
              1. Registro de Requerimiento y Documentación
            </h2>
            <p class="text-xs text-[#94A3B8]">
              Ingresa los datos base y adjunta el documento de sustento para que Teo lo analice
            </p>
          </div>
        </div>
      </div>

      <!-- Errores de Validación -->
      <div v-if="formErrors.length > 0" class="mx-8 mt-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
        <AlertCircle class="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
        <div class="text-xs text-red-700 space-y-1">
          <p class="font-bold">Por favor completa los siguientes campos:</p>
          <ul class="list-disc list-inside">
            <li v-for="(err, i) in formErrors" :key="i">{{ err }}</li>
          </ul>
        </div>
      </div>

      <!-- Formulario Base en 2 Columnas -->
      <form @submit.prevent="handleStartChatWithValidation">
        <div class="px-8 py-6 grid grid-cols-1 sm:grid-cols-2 gap-5">
          <!-- 1. Vicepresidencia (Configurable) -->
          <div v-if="showVicepresidencia">
            <label class="block text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-1.5">
              {{ vpField?.label || 'VICEPRESIDENCIA' }} <span v-if="vpField?.is_required !== false" class="text-red-500">*</span>
            </label>
            <select
              v-model="formData.vicepresidencia"
              @change="formData.direccion = ''"
              class="w-full border border-[#E2E8F0] hover:border-[#CBD5E1] bg-white rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#EB5F46]/20 focus:border-[#EB5F46] transition-all cursor-pointer"
              :required="vpField?.is_required !== false"
            >
              <option value="" disabled>Selecciona...</option>
              <option v-for="vp in vps" :key="vp.id" :value="vp.name">{{ vp.name }}</option>
            </select>
          </div>

          <!-- 2. Dirección (Configurable y en Cascada) -->
          <div v-if="showDireccion">
            <label class="block text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-1.5">
              {{ dirField?.label || 'DIRECCIÓN' }} <span v-if="dirField?.is_required !== false" class="text-red-500">*</span>
            </label>
            <select
              v-model="formData.direccion"
              :disabled="!formData.vicepresidencia"
              class="w-full border border-[#E2E8F0] hover:border-[#CBD5E1] bg-white disabled:bg-[#F8FAFC] disabled:text-[#94A3B8] rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#EB5F46]/20 focus:border-[#EB5F46] transition-all cursor-pointer"
              :required="dirField?.is_required !== false"
            >
              <option value="" disabled>Selecciona...</option>
              <option v-for="d in filteredDirecciones" :key="d.id" :value="d.name">{{ d.name }}</option>
            </select>
          </div>

          <!-- 3. Campos Dinámicos de Paso 1 (Sincronizados con Catálogo de Formularios) -->
          <div
            v-for="field in dynamicStep1Fields"
            :key="field.key"
            :class="field.field_type === 'textarea' ? 'sm:col-span-2' : ''"
          >
            <label class="block text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-1.5">
              {{ field.label }} <span v-if="field.is_required" class="text-red-500">*</span>
              <span v-if="field.help_text" class="inline-block ml-1 text-[#94A3B8] cursor-help" :title="field.help_text">
                <HelpCircle class="w-3.5 h-3.5 inline align-middle" />
              </span>
            </label>

            <!-- MultiSelect (Dropdown Popover & Chips) -->
            <div
              v-if="field.field_type === 'multiselect' || field.allow_multiple || field.type === 'multiselect'"
              class="relative multiselect-container"
            >
              <!-- Trigger Input Box -->
              <div
                @click="toggleDropdown('step1_' + field.key)"
                class="min-h-[44px] w-full border border-[#E2E8F0] hover:border-[#CBD5E1] bg-white rounded-xl px-3 py-2 text-sm text-[#1E293B] cursor-pointer transition-all flex items-center justify-between gap-2 shadow-2xs"
                :class="{ 'ring-2 ring-[#EB5F46]/20 border-[#EB5F46]': activeDropdownKey === ('step1_' + field.key) }"
              >
                <!-- Selected badges or placeholder -->
                <div class="flex flex-wrap items-center gap-1.5 flex-1 min-w-0">
                  <span
                    v-if="!formData[field.key] || formData[field.key].length === 0"
                    class="text-[#94A3B8] text-sm select-none"
                  >
                    Seleccione una o más opciones...
                  </span>
                  <template v-else>
                    <span
                      v-for="opt in formData[field.key]"
                      :key="opt"
                      class="inline-flex items-center gap-1.5 bg-[#FFF1EE] text-[#EB5F46] border border-[#FCD9D2] font-medium text-xs px-2.5 py-1 rounded-lg select-none shadow-2xs"
                    >
                      <span class="truncate max-w-[200px]">{{ opt }}</span>
                      <button
                        type="button"
                        @click.stop="toggleFormFieldMulti(field.key, opt)"
                        class="hover:text-red-700 hover:bg-[#FCD9D2] rounded p-0.5 cursor-pointer transition-colors"
                        title="Quitar"
                      >
                        <X class="w-3 h-3" />
                      </button>
                    </span>
                  </template>
                </div>

                <!-- Right controls: clear all + divider + chevron -->
                <div class="flex items-center gap-1.5 text-slate-400 shrink-0">
                  <button
                    v-if="formData[field.key] && formData[field.key].length > 0"
                    type="button"
                    @click.stop="formData[field.key] = []"
                    class="p-1 hover:text-slate-600 rounded-md cursor-pointer hover:bg-slate-100 transition-colors"
                    title="Limpiar todo"
                  >
                    <X class="w-3.5 h-3.5" />
                  </button>
                  <div
                    v-if="formData[field.key] && formData[field.key].length > 0"
                    class="w-px h-4 bg-slate-200"
                  ></div>
                  <ChevronDown
                    class="w-4 h-4 transition-transform duration-200"
                    :class="{ 'rotate-180 text-[#EB5F46]': activeDropdownKey === ('step1_' + field.key) }"
                  />
                </div>
              </div>

              <!-- Floating Dropdown Popover -->
              <div
                v-if="activeDropdownKey === ('step1_' + field.key)"
                class="absolute left-0 right-0 top-full mt-1.5 bg-white border border-[#E2E8F0] rounded-xl shadow-xl z-50 overflow-hidden"
              >
                <!-- Header toolbar -->
                <div class="px-3.5 py-2 bg-[#F8FAFC] border-b border-[#F1F5F9] flex items-center justify-between text-xs">
                  <span class="text-slate-500 font-medium">
                    <span class="font-bold text-[#EB5F46]">{{ (formData[field.key] || []).length }}</span> de {{ (field.options || []).length }} seleccionadas
                  </span>
                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      @click.stop="formData[field.key] = (formData[field.key] || []).length === (field.options || []).length ? [] : [...(field.options || [])]"
                      class="text-xs font-semibold text-[#EB5F46] hover:text-[#d44830] cursor-pointer"
                    >
                      {{ (formData[field.key] || []).length === (field.options || []).length ? 'Deseleccionar todas' : 'Seleccionar todas' }}
                    </button>
                    <span class="text-slate-300">·</span>
                    <button
                      type="button"
                      @click.stop="formData[field.key] = []"
                      class="text-slate-400 hover:text-slate-600 font-medium cursor-pointer"
                    >
                      Limpiar
                    </button>
                  </div>
                </div>

                <!-- Options List -->
                <div class="max-h-60 overflow-y-auto p-1.5 space-y-0.5 divide-y divide-[#F8FAFC]">
                  <div
                    v-for="opt in (field.options || [])"
                    :key="opt"
                    @click.stop="toggleFormFieldMulti(field.key, opt)"
                    :class="[
                      'flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors text-xs select-none',
                      isFormFieldMultiSelected(field.key, opt)
                        ? 'bg-[#FFF8F6] text-[#EB5F46] font-semibold'
                        : 'text-[#334155] hover:bg-[#F8FAFC]'
                    ]"
                  >
                    <div class="flex items-center gap-2.5 min-w-0">
                      <div
                        :class="[
                          'w-4 h-4 rounded border flex items-center justify-center shrink-0 transition-colors',
                          isFormFieldMultiSelected(field.key, opt)
                            ? 'bg-[#EB5F46] border-[#EB5F46] text-white'
                            : 'border-slate-300 bg-white'
                        ]"
                      >
                        <Check v-if="isFormFieldMultiSelected(field.key, opt)" class="w-3 h-3 stroke-[3]" />
                      </div>
                      <span class="truncate">{{ opt }}</span>
                    </div>
                    <Check v-if="isFormFieldMultiSelected(field.key, opt)" class="w-3.5 h-3.5 text-[#EB5F46] shrink-0 stroke-[2.5]" />
                  </div>
                  <div v-if="(!field.options || field.options.length === 0)" class="p-3 text-center text-xs text-slate-400">
                    No hay opciones configuradas
                  </div>
                </div>
              </div>
            </div>

            <!-- Select (Simple) -->
            <select
              v-else-if="field.field_type === 'select' || field.type === 'select'"
              v-model="formData[field.key]"
              class="w-full border border-[#E2E8F0] hover:border-[#CBD5E1] bg-white rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#EB5F46]/20 focus:border-[#EB5F46] transition-all cursor-pointer"
              :required="field.is_required"
            >
              <option value="" disabled>{{ field.placeholder || 'Seleccionar...' }}</option>
              <option v-for="opt in (field.options || [])" :key="opt" :value="opt">{{ opt }}</option>
            </select>

            <!-- Date -->
            <input
              v-else-if="field.field_type === 'date'"
              type="date"
              v-model="formData[field.key]"
              class="w-full border border-[#E2E8F0] hover:border-[#CBD5E1] bg-white rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#EB5F46]/20 focus:border-[#EB5F46] transition-all"
              :required="field.is_required"
            />

            <!-- Number -->
            <input
              v-else-if="field.field_type === 'number'"
              type="number"
              v-model="formData[field.key]"
              :placeholder="field.placeholder || '0'"
              class="w-full border border-[#E2E8F0] hover:border-[#CBD5E1] bg-white rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#EB5F46]/20 focus:border-[#EB5F46] transition-all"
              :required="field.is_required"
            />

            <!-- Textarea -->
            <textarea
              v-else-if="field.field_type === 'textarea'"
              v-model="formData[field.key]"
              :placeholder="field.placeholder || 'Detalla la información...'"
              rows="3"
              class="w-full border border-[#E2E8F0] hover:border-[#CBD5E1] bg-white rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#EB5F46]/20 focus:border-[#EB5F46] transition-all"
              :required="field.is_required"
            ></textarea>

            <!-- Text / Default -->
            <input
              v-else
              type="text"
              v-model="formData[field.key]"
              :placeholder="field.placeholder || ''"
              class="w-full border border-[#E2E8F0] hover:border-[#CBD5E1] bg-white rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#EB5F46]/20 focus:border-[#EB5F46] transition-all"
              :required="field.is_required"
            />
          </div>

          <!-- 4. Archivos con la Necesidad (Configurable) -->
          <div v-if="showAdjuntos">
            <label class="block text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-1.5">
              ARCHIVOS CON LA NECESIDAD
              <span class="inline-block ml-1 text-[#94A3B8] cursor-help" title="Adjunta documentos de soporte como especificaciones, hojas de cálculo o diagramas.">
                <HelpCircle class="w-3.5 h-3.5 inline align-middle" />
              </span>
            </label>

            <input
              type="file"
              ref="fileInputRef"
              @change="handleFileUpload"
              class="hidden"
              accept=".pdf,.docx,.xlsx,.txt,.jpg,.jpeg,.png,.webp"
            />

            <div
              v-if="!attachedFile"
              @click="fileInputRef?.click()"
              class="w-full border border-dashed border-[#CBD5E1] hover:border-[#EB5F46] rounded-xl px-3.5 py-2.5 text-xs text-[#64748B] flex items-center justify-center gap-2 cursor-pointer bg-slate-50/50 hover:bg-[#FFF0ED]/30 transition-all font-medium min-h-[44px]"
            >
              <Paperclip class="w-4 h-4 text-slate-400" />
              <span>Subir archivo...</span>
            </div>

            <div
              v-else
              class="flex items-center justify-between p-2.5 bg-[#FFF0ED] border border-[#FCD9D2] rounded-xl text-xs text-[#EB5F46] font-semibold min-h-[44px]"
            >
              <div class="flex items-center gap-2 truncate">
                <Paperclip class="w-3.5 h-3.5 shrink-0" />
                <span class="truncate">{{ attachedFile.name }}</span>
              </div>
              <button
                type="button"
                @click="attachedFile = null"
                class="hover:bg-[#EB5F46]/20 p-1 rounded transition-colors text-[#EB5F46]"
                title="Eliminar archivo adjunto"
              >
                <X class="w-3.5 h-3.5" />
              </button>
            </div>

            <p class="text-[10px] text-[#94A3B8] mt-1.5 leading-relaxed">
              Formatos permitidos: PDF (máx. 25 MB) · DOCX (máx. 25 MB) · TXT (máx. 5 MB) · Imagen (máx. 25 MB)
            </p>
          </div>
        </div>

        <!-- Botón Centrado "Continuar con Teo >" -->
        <div class="px-8 py-5 border-t border-[#F1F5F9] bg-[#F8FAFC] flex justify-center">
          <button
            type="submit"
            :disabled="isUploadingFile"
            class="flex items-center justify-center gap-2 bg-[#EB5F46] hover:bg-[#c94a32] text-white px-8 py-3 rounded-xl text-sm font-semibold transition-all shadow-sm shadow-[#EB5F46]/20 cursor-pointer disabled:opacity-60"
          >
            <Bot class="w-4 h-4" />
            <span>{{ attachedFile ? 'Analizar documento y conversar con Teo' : 'Continuar con Teo' }}</span>
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>

    <!-- ── PASO 2: CHAT INTERACTIVO CON TEO ── -->
    <div
      v-if="currentStep === 2"
      class="bg-white rounded-2xl border border-[#E2E8F0] shadow-sm overflow-hidden flex flex-col transition-all"
      style="height: min(760px, calc(100vh - 200px)); min-height: 640px;"
    >
      <!-- Cabecera del Chat -->
      <div class="px-6 py-4 border-b border-[#F1F5F9] flex items-center gap-3 bg-[#EB5F46] text-white">
        <div class="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center overflow-hidden shrink-0 border border-white/20 shadow-xs">
          <img v-if="aiAvatar" :src="aiAvatar" :alt="aiName || 'Teo'" class="w-full h-full object-cover" />
          <Bot v-else class="w-5 h-5 text-white" />
        </div>
        <div>
          <p class="text-sm font-bold">{{ aiName || 'Teo' }}</p>
          <p class="text-[10px] text-white/80 uppercase tracking-wider font-semibold">Analista de Negocio Senior</p>
        </div>
        <div class="ml-auto flex items-center gap-3">
          <button
            type="button"
            @click="goToStep3Summary"
            class="text-xs text-white bg-white/20 hover:bg-white/30 px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors cursor-pointer font-medium shadow-xs"
            title="Generar resumen y avanzar a la ficha técnica"
          >
            <span>Finalizar y ver resumen</span>
            <ChevronRight class="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            @click="currentStep = 1"
            class="text-xs text-white/90 hover:text-white flex items-center gap-1.5 bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
          >
            <ArrowLeft class="w-3.5 h-3.5" /> Volver al formulario
          </button>
          <div class="flex items-center gap-1.5">
            <div class="w-2 h-2 rounded-full bg-emerald-300 animate-pulse" />
            <span class="text-xs text-white/90 font-medium">En línea</span>
          </div>
        </div>
      </div>

      <!-- Historial de Conversación -->
      <div class="flex-1 p-6 overflow-y-auto space-y-4 bg-[#F8FAFC]">
        <div
          v-for="(msg, i) in chatHistory"
          :key="i"
          :class="['flex gap-3 max-w-full', msg.role === 'user' ? 'justify-end' : 'justify-start']"
        >
          <!-- Avatar de Teo -->
          <div
            v-if="msg.role !== 'user'"
            class="w-8 h-8 rounded-full bg-white flex items-center justify-center text-[#EB5F46] shrink-0 mt-1 overflow-hidden border border-slate-200 shadow-xs"
          >
            <img v-if="aiAvatar" :src="aiAvatar" :alt="aiName || 'Teo'" class="w-full h-full object-cover" />
            <Bot v-else class="w-4 h-4" />
          </div>

          <!-- Contenedor del Mensaje, Feedback y Opciones -->
          <div :class="['flex flex-col gap-1.5 min-w-0', msg.role === 'user' ? 'items-end max-w-[85%]' : 'items-start max-w-[85%]']">
            <!-- Burbuja del Mensaje -->
            <div
              :class="[
                'px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-xs',
                msg.role === 'user'
                  ? 'bg-[#EB5F46] text-white rounded-tr-sm'
                  : 'bg-white text-[#1E293B] border border-[#E2E8F0] rounded-tl-sm w-full'
              ]"
            >
              <!-- Renderizado de Markdown Formateado para Teo (sin asteriscos crudos) -->
              <div
                v-if="msg.role === 'model'"
                class="prose prose-sm prose-slate max-w-none text-slate-800 leading-relaxed"
                v-html="formatMarkdownToHtml(msg.text)"
              />
              <p v-else class="whitespace-pre-line text-white leading-relaxed">{{ msg.text }}</p>

              <p :class="['text-[10px] mt-1.5 font-medium', msg.role === 'user' ? 'text-white/80 text-right' : 'text-[#94A3B8]']">
                {{ msg.role === 'user' ? 'Tú' : (aiName || 'Teo') }}
              </p>
            </div>

            <!-- Botones de Feedback 👍 / 👎 para mensajes de Teo -->
            <div v-if="msg.role === 'model' && !isChatLoading" class="flex gap-1 mt-0.5 px-1">
              <span v-if="ratedMessages[i]" class="text-[10px] text-[#94A3B8] italic">
                {{ ratedMessages[i] === 'positive' ? '✓ Calificado como útil' : '✓ Calificado como mejorable' }}
              </span>
              <template v-else>
                <button
                  type="button"
                  @click="rateMessage(i, 'positive')"
                  title="Respuesta útil"
                  class="flex items-center gap-1 text-[10px] text-[#94A3B8] hover:text-emerald-600 transition-colors px-2 py-0.5 rounded-md hover:bg-emerald-50 cursor-pointer"
                >
                  <ThumbsUp class="w-3 h-3" />
                  <span>Útil</span>
                </button>
                <button
                  type="button"
                  @click="rateMessage(i, 'negative')"
                  title="Respuesta mejorable"
                  class="flex items-center gap-1 text-[10px] text-[#94A3B8] hover:text-red-500 transition-colors px-2 py-0.5 rounded-md hover:bg-red-50 cursor-pointer"
                >
                  <ThumbsDown class="w-3 h-3" />
                  <span>Mejorable</span>
                </button>
              </template>
            </div>

            <!-- ── Tarjetas Interactivas de Opciones Sugeridas (Réplica Exacta Proyecto Original) ── -->
            <div
              v-if="msg.role === 'model' && msg.options && msg.options.length > 0 && i === chatHistory.length - 1 && !isChatLoading"
              class="w-full mt-2 p-3 sm:p-3.5 rounded-2xl bg-gradient-to-b from-slate-50 to-slate-100/70 border border-slate-200/80 shadow-xs animate-in fade-in-50 duration-200"
            >
              <!-- Cabecera explicativa de opciones -->
              <div class="flex items-center gap-1.5 text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2.5 px-0.5">
                <ListChecks class="w-3.5 h-3.5 text-[#EB5F46]" />
                <span>{{ msg.allowMultiple ? 'Selecciona una o más opciones:' : 'Selecciona una opción para responder:' }}</span>
              </div>

              <!-- Listado de tarjetas interactivas -->
              <div class="flex flex-col gap-2">
                <!-- Modo 1: Selección simple (responde inmediatamente) -->
                <template v-if="!msg.allowMultiple">
                  <button
                    v-for="(opt, optIndex) in msg.options"
                    :key="optIndex"
                    type="button"
                    @click="sendMessage(opt)"
                    class="w-full flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all shadow-xs cursor-pointer bg-white hover:bg-[#EB5F46] text-slate-700 hover:text-white border border-slate-200/90 hover:border-[#EB5F46] active:scale-[0.99] hover:shadow-md hover:shadow-[#EB5F46]/15 group text-left"
                  >
                    <div class="flex items-center gap-2.5 min-w-0 flex-1">
                      <span class="w-5 h-5 rounded-md bg-slate-100 text-slate-600 group-hover:bg-white group-hover:text-[#EB5F46] flex items-center justify-center text-[10px] font-bold shrink-0 border border-slate-200/80 group-hover:border-white transition-all shadow-2xs">
                        {{ String.fromCharCode(65 + (optIndex % 26)) }}
                      </span>
                      <span class="leading-snug transition-colors group-hover:text-white">
                        {{ opt }}
                      </span>
                    </div>
                    <ChevronRight class="w-4 h-4 text-slate-400 group-hover:text-white group-hover:translate-x-0.5 transition-all shrink-0 opacity-60 group-hover:opacity-100" />
                  </button>
                </template>

                <!-- Modo 2: Selección múltiple (acumulativa con checkbox) -->
                <template v-else>
                  <button
                    v-for="(opt, optIndex) in msg.options"
                    :key="optIndex"
                    type="button"
                    @click="toggleMultiOption(opt)"
                    :class="[
                      'w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all shadow-xs cursor-pointer active:scale-[0.99] text-left border',
                      selectedMultiOptions.includes(opt)
                        ? 'bg-[#EB5F46] text-white border-[#EB5F46] shadow-sm ring-2 ring-[#EB5F46]/20'
                        : 'bg-white hover:bg-[#FFF0ED] border-slate-200/90 hover:border-[#EB5F46] text-slate-700 hover:text-[#EB5F46]'
                    ]"
                  >
                    <input
                      type="checkbox"
                      :checked="selectedMultiOptions.includes(opt)"
                      class="w-4 h-4 rounded border-slate-300 pointer-events-none shrink-0"
                    />
                    <span class="flex-1 leading-snug">{{ opt }}</span>
                  </button>
                </template>
              </div>

              <!-- Barra de envío para selección múltiple -->
              <div v-if="msg.allowMultiple" class="flex items-center justify-between gap-2 mt-3 pt-2.5 border-t border-slate-200/60">
                <button
                  type="button"
                  :disabled="selectedMultiOptions.length === 0"
                  @click="submitMultiOptions"
                  :class="[
                    'flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold shadow-sm transition-all active:scale-98',
                    selectedMultiOptions.length > 0
                      ? 'bg-[#EB5F46] hover:bg-[#c94a32] text-white shadow-[#EB5F46]/20 cursor-pointer'
                      : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                  ]"
                >
                  <Send class="w-3.5 h-3.5" />
                  <span>Enviar opciones seleccionadas {{ selectedMultiOptions.length > 0 ? `(${selectedMultiOptions.length})` : '' }}</span>
                </button>
                <button
                  v-if="selectedMultiOptions.length > 0"
                  type="button"
                  @click="selectedMultiOptions = []"
                  class="text-xs text-slate-500 hover:text-slate-700 underline px-1 cursor-pointer"
                >
                  Limpiar selección
                </button>
              </div>
            </div>
          </div>

          <!-- Avatar del Usuario -->
          <div
            v-if="msg.role === 'user'"
            class="w-8 h-8 rounded-full bg-[#EB5F46] flex items-center justify-center shrink-0 mt-1 shadow-sm text-white text-[10px] font-bold"
          >
            {{ (formData.registrador || 'TU').substring(0, 2).toUpperCase() }}
          </div>
        </div>

        <!-- Indicador de Escritura de Teo -->
        <div v-if="isChatLoading" class="flex gap-3 max-w-[85%]">
          <div class="w-8 h-8 rounded-full bg-white flex items-center justify-center text-[#EB5F46] shrink-0 overflow-hidden border border-slate-200 shadow-xs">
            <img v-if="aiAvatar" :src="aiAvatar" :alt="aiName || 'Teo'" class="w-full h-full object-cover animate-pulse" />
            <Bot v-else class="w-4 h-4" />
          </div>
          <div class="bg-white border border-slate-200 p-3.5 rounded-2xl rounded-tl-sm shadow-xs flex items-center gap-1.5 h-11">
            <div class="w-2 h-2 rounded-full bg-[#EB5F46] animate-bounce" style="animation-delay: 0ms" />
            <div class="w-2 h-2 rounded-full bg-[#EB5F46] animate-bounce" style="animation-delay: 150ms" />
            <div class="w-2 h-2 rounded-full bg-[#EB5F46] animate-bounce" style="animation-delay: 300ms" />
          </div>
        </div>
        <div ref="chatEndRef" />
      </div>

      <!-- Barra Inferior de Entrada y Acción de Finalización -->
      <div class="px-4 py-3 bg-white border-t border-slate-200 space-y-2.5">
        <!-- Tira de archivo adjunto previo al envío -->
        <div v-if="attachedFile" class="flex items-center gap-2 bg-[#FFF0ED] border border-[#FCD9D2] rounded-xl px-3 py-2 animate-in fade-in duration-150">
          <FileText class="w-4 h-4 text-[#EB5F46] shrink-0" />
          <div class="flex flex-col min-w-0 flex-1">
            <div class="flex items-center gap-1.5">
              <span class="text-xs font-semibold text-[#EB5F46] truncate">{{ attachedFile.name }}</span>
              <span class="text-[10px] text-slate-500 shrink-0">({{ (attachedFile.size / 1024).toFixed(0) }} KB)</span>
            </div>
            <span class="text-[9.5px] text-slate-500">Se adjuntará con tu próximo mensaje a Teo</span>
          </div>
          <button
            type="button"
            @click="attachedFile = null"
            class="text-slate-400 hover:text-red-500 transition-colors ml-1 cursor-pointer"
            title="Quitar archivo"
          >
            <X class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- Banner de cuenta regresiva automática para resumen ejecutivo -->
        <div v-if="countdownSeconds !== null" class="animate-in fade-in slide-in-from-bottom-2 duration-300">
          <div class="flex flex-col items-center gap-2 py-3 px-4 bg-gradient-to-r from-[#EB5F46]/10 via-[#ff7860]/10 to-[#EB5F46]/10 border border-[#EB5F46]/30 rounded-xl">
            <div class="flex items-center gap-3 w-full">
              <div class="relative w-9 h-9 shrink-0">
                <svg class="w-9 h-9 -rotate-90" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="15" fill="none" stroke="#E2E8F0" stroke-width="3" />
                  <circle
                    cx="18" cy="18" r="15" fill="none"
                    stroke="#EB5F46" stroke-width="3"
                    stroke-dasharray="94.2477"
                    :stroke-dashoffset="94.2477 * (1 - (countdownSeconds || 0) / 3)"
                    stroke-linecap="round"
                    class="transition-all duration-1000 ease-linear"
                  />
                </svg>
                <span class="absolute inset-0 flex items-center justify-center text-sm font-bold text-[#EB5F46]">
                  {{ countdownSeconds }}
                </span>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-bold text-[#1E293B]">Preparando resumen ejecutivo...</p>
                <p class="text-[10px] text-[#64748B]">En {{ countdownSeconds }}s se generará la ficha resumen con toda la información recopilada.</p>
              </div>
              <button
                type="button"
                @click="goToStep3Summary"
                class="text-xs font-bold bg-[#EB5F46] hover:bg-[#c94a32] text-white px-3 py-1.5 rounded-lg transition-colors cursor-pointer shrink-0 shadow-xs"
              >
                Ir al resumen ahora
              </button>
            </div>
          </div>
        </div>

        <!-- Formulario con Textarea de Auto-Crecimiento, Clip y Botón Enviar -->
        <form @submit.prevent="sendMessage()" :class="['flex items-end gap-2', countdownSeconds !== null ? 'pointer-events-none opacity-40' : '']">
          <!-- Input oculto para adjuntar desde el chat -->
          <input
            type="file"
            ref="chatFileInputRef"
            @change="handleFileUpload"
            class="hidden"
            accept=".pdf,.docx,.xlsx,.txt,.jpg,.jpeg,.png,.webp"
          />
          <button
            type="button"
            @click="chatFileInputRef?.click()"
            :disabled="isChatLoading"
            title="Adjuntar archivo o evidencia"
            :class="[
              'w-10 h-10 rounded-xl border flex items-center justify-center transition-colors shrink-0 mb-0.5 cursor-pointer',
              attachedFile
                ? 'border-[#EB5F46] bg-[#FFF0ED] text-[#EB5F46]'
                : 'border-[#E2E8F0] text-[#94A3B8] hover:bg-[#F8FAFC] hover:text-[#EB5F46]'
            ]"
          >
            <Paperclip class="w-4 h-4" />
          </button>

          <!-- Textarea con auto-crecimiento y envío al presionar Enter -->
          <textarea
            ref="chatInputRef"
            v-model="currentMessage"
            @input="(e: any) => {
              e.target.style.height = 'auto';
              e.target.style.height = `${Math.min(e.target.scrollHeight, 150)}px`;
            }"
            @keydown.enter.exact.prevent="!isChatLoading && sendMessage()"
            rows="1"
            :disabled="isChatLoading"
            placeholder="Escribe tu respuesta a Teo... (Enter para enviar, Shift+Enter para salto de línea)"
            class="flex-1 border rounded-xl px-4 py-2.5 text-sm text-[#1E293B] placeholder-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#EB5F46]/20 focus:border-[#EB5F46] transition-colors leading-relaxed min-h-[42px] max-h-[150px] align-middle border-[#E2E8F0] resize-none"
          ></textarea>

          <!-- Botón Enviar -->
          <button
            type="submit"
            :disabled="(!currentMessage.trim() && !attachedFile) || isChatLoading"
            class="w-10 h-10 rounded-xl bg-[#EB5F46] hover:bg-[#c94a32] disabled:bg-[#E2E8F0] disabled:text-[#94A3B8] flex items-center justify-center text-white transition-colors shrink-0 mb-0.5 cursor-pointer shadow-xs"
          >
            <Send class="w-4 h-4" />
          </button>
        </form>

        <!-- Barra inferior para pasar al paso 3 de revisión -->
        <div class="flex items-center justify-between pt-1.5 border-t border-slate-100">
          <span class="text-xs text-slate-400">
            ¿Has completado la estructura con Teo?
          </span>
          <button
            type="button"
            @click="goToStep3Summary"
            class="flex items-center gap-2 text-xs font-bold text-[#EB5F46] hover:text-[#c94a32] bg-[#FFF0ED] hover:bg-[#fde2dc] px-4 py-2 rounded-xl transition-colors cursor-pointer"
          >
            <span>Revisar y validar resumen ejecutivo</span>
            <ChevronRight class="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>

    <!-- ── PASO 3: REVISIÓN Y ENVÍO A APROBACIÓN ── -->
    <div v-if="currentStep === 3" class="bg-white rounded-2xl border border-[#E2E8F0] shadow-[0_1px_3px_rgba(0,0,0,.07)] overflow-hidden space-y-0">
      <!-- Encabezado -->
      <div class="px-8 pt-8 pb-6 border-b border-[#F1F5F9] flex justify-between items-start gap-4">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-[#EEF2FF] flex items-center justify-center">
            <span class="text-[#4F5AF5] text-sm">📋</span>
          </div>
          <div>
            <h2 class="text-lg font-bold text-[#1E293B]">
              3. Revisión y Envío a Aprobación
            </h2>
            <p class="text-xs text-[#94A3B8]">
              Revisa y completa la información de la iniciativa validada por Teo.
            </p>
          </div>
        </div>
        <button
          type="button"
          @click="currentStep = 2"
          class="text-xs text-slate-600 hover:text-slate-900 border border-slate-200 px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors"
        >
          <ArrowLeft class="w-3.5 h-3.5" /> Volver al chat
        </button>
      </div>

      <div class="px-8 py-6 space-y-6">
        <!-- Aviso de Validación Humana Requerida -->
        <div class="p-4 bg-slate-50 border border-slate-200/80 rounded-xl flex items-start gap-3.5">
          <div class="w-8 h-8 rounded-lg bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600 shrink-0">
            <AlertCircle class="w-4 h-4 text-amber-600" />
          </div>
          <div class="flex-1 min-w-0">
            <h4 class="text-xs font-bold text-[#1E293B] mb-0.5">Validación de Información sugerida por la IA</h4>
            <p class="text-[11px] text-[#64748B] leading-relaxed">
              Este resumen y los campos asociados han sido completados de forma automática por el asistente de Inteligencia Artificial. Recuerde que la IA puede cometer errores o interpretar incorrectamente algunos datos, por lo que <span class="font-semibold text-amber-700">se requiere siempre una revisión y validación humana</span> de toda la información antes de guardar la iniciativa o enviarla a aprobación.
            </p>
          </div>
        </div>

        <!-- Campos de la Iniciativa -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label class="block text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-1.5">Vicepresidencia</label>
            <input type="text" :value="formData.vicepresidencia" readonly class="w-full border border-[#E2E8F0] bg-[#F8FAFC] rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] cursor-not-allowed" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-1.5">Dirección</label>
            <input type="text" :value="formData.direccion" readonly class="w-full border border-[#E2E8F0] bg-[#F8FAFC] rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] cursor-not-allowed" />
          </div>

          <div class="sm:col-span-2">
            <label class="block text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-1.5">Título de la Iniciativa <span class="text-red-500">*</span></label>
            <input type="text" v-model="formData.titulo" class="w-full border border-[#E2E8F0] focus:border-[#EB5F46] bg-white rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] outline-none" />
          </div>

          <div class="sm:col-span-2">
            <label class="block text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-1.5">Objetivo Principal <span class="text-red-500">*</span></label>
            <textarea rows="2" v-model="formData.objetivo" class="w-full border border-[#E2E8F0] focus:border-[#EB5F46] bg-white rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] outline-none" />
          </div>

          <div class="sm:col-span-2">
            <label class="block text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-1.5">Descripción de la Necesidad <span class="text-red-500">*</span></label>
            <textarea rows="3" v-model="formData.descripcion_de_la_necesidad" class="w-full border border-[#E2E8F0] focus:border-[#EB5F46] bg-white rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] outline-none" />
          </div>

          <!-- Campos Dinámicos Adicionales de la Ficha Técnica (p. ej. Institución, Pilar, etc.) -->
          <div
            v-for="field in dynamicStep3Fields"
            :key="field.key"
            :class="field.field_type === 'textarea' ? 'sm:col-span-2' : ''"
          >
            <label class="block text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-1.5">
              {{ field.label }} <span v-if="field.is_required" class="text-red-500">*</span>
            </label>
            <!-- MultiSelect (Dropdown Popover & Chips) -->
            <div
              v-if="field.field_type === 'multiselect' || field.allow_multiple || field.type === 'multiselect'"
              class="relative multiselect-container"
            >
              <!-- Trigger Input Box -->
              <div
                @click="toggleDropdown('step3_' + field.key)"
                class="min-h-[44px] w-full border border-[#E2E8F0] hover:border-[#CBD5E1] bg-white rounded-xl px-3 py-2 text-sm text-[#1E293B] cursor-pointer transition-all flex items-center justify-between gap-2 shadow-2xs"
                :class="{ 'ring-2 ring-[#EB5F46]/20 border-[#EB5F46]': activeDropdownKey === ('step3_' + field.key) }"
              >
                <!-- Selected badges or placeholder -->
                <div class="flex flex-wrap items-center gap-1.5 flex-1 min-w-0">
                  <span
                    v-if="!formData[field.key] || formData[field.key].length === 0"
                    class="text-[#94A3B8] text-sm select-none"
                  >
                    Seleccione una o más opciones...
                  </span>
                  <template v-else>
                    <span
                      v-for="opt in formData[field.key]"
                      :key="opt"
                      class="inline-flex items-center gap-1.5 bg-[#FFF1EE] text-[#EB5F46] border border-[#FCD9D2] font-medium text-xs px-2.5 py-1 rounded-lg select-none shadow-2xs"
                    >
                      <span class="truncate max-w-[200px]">{{ opt }}</span>
                      <button
                        type="button"
                        @click.stop="toggleFormFieldMulti(field.key, opt)"
                        class="hover:text-red-700 hover:bg-[#FCD9D2] rounded p-0.5 cursor-pointer transition-colors"
                        title="Quitar"
                      >
                        <X class="w-3 h-3" />
                      </button>
                    </span>
                  </template>
                </div>

                <!-- Right controls: clear all + divider + chevron -->
                <div class="flex items-center gap-1.5 text-slate-400 shrink-0">
                  <button
                    v-if="formData[field.key] && formData[field.key].length > 0"
                    type="button"
                    @click.stop="formData[field.key] = []"
                    class="p-1 hover:text-slate-600 rounded-md cursor-pointer hover:bg-slate-100 transition-colors"
                    title="Limpiar todo"
                  >
                    <X class="w-3.5 h-3.5" />
                  </button>
                  <div
                    v-if="formData[field.key] && formData[field.key].length > 0"
                    class="w-px h-4 bg-slate-200"
                  ></div>
                  <ChevronDown
                    class="w-4 h-4 transition-transform duration-200"
                    :class="{ 'rotate-180 text-[#EB5F46]': activeDropdownKey === ('step3_' + field.key) }"
                  />
                </div>
              </div>

              <!-- Floating Dropdown Popover -->
              <div
                v-if="activeDropdownKey === ('step3_' + field.key)"
                class="absolute left-0 right-0 top-full mt-1.5 bg-white border border-[#E2E8F0] rounded-xl shadow-xl z-50 overflow-hidden"
              >
                <!-- Header toolbar -->
                <div class="px-3.5 py-2 bg-[#F8FAFC] border-b border-[#F1F5F9] flex items-center justify-between text-xs">
                  <span class="text-slate-500 font-medium">
                    <span class="font-bold text-[#EB5F46]">{{ (formData[field.key] || []).length }}</span> de {{ (field.options || []).length }} seleccionadas
                  </span>
                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      @click.stop="formData[field.key] = (formData[field.key] || []).length === (field.options || []).length ? [] : [...(field.options || [])]"
                      class="text-xs font-semibold text-[#EB5F46] hover:text-[#d44830] cursor-pointer"
                    >
                      {{ (formData[field.key] || []).length === (field.options || []).length ? 'Deseleccionar todas' : 'Seleccionar todas' }}
                    </button>
                    <span class="text-slate-300">·</span>
                    <button
                      type="button"
                      @click.stop="formData[field.key] = []"
                      class="text-slate-400 hover:text-slate-600 font-medium cursor-pointer"
                    >
                      Limpiar
                    </button>
                  </div>
                </div>

                <!-- Options List -->
                <div class="max-h-60 overflow-y-auto p-1.5 space-y-0.5 divide-y divide-[#F8FAFC]">
                  <div
                    v-for="opt in (field.options || [])"
                    :key="opt"
                    @click.stop="toggleFormFieldMulti(field.key, opt)"
                    :class="[
                      'flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors text-xs select-none',
                      isFormFieldMultiSelected(field.key, opt)
                        ? 'bg-[#FFF8F6] text-[#EB5F46] font-semibold'
                        : 'text-[#334155] hover:bg-[#F8FAFC]'
                    ]"
                  >
                    <div class="flex items-center gap-2.5 min-w-0">
                      <div
                        :class="[
                          'w-4 h-4 rounded border flex items-center justify-center shrink-0 transition-colors',
                          isFormFieldMultiSelected(field.key, opt)
                            ? 'bg-[#EB5F46] border-[#EB5F46] text-white'
                            : 'border-slate-300 bg-white'
                        ]"
                      >
                        <Check v-if="isFormFieldMultiSelected(field.key, opt)" class="w-3 h-3 stroke-[3]" />
                      </div>
                      <span class="truncate">{{ opt }}</span>
                    </div>
                    <Check v-if="isFormFieldMultiSelected(field.key, opt)" class="w-3.5 h-3.5 text-[#EB5F46] shrink-0 stroke-[2.5]" />
                  </div>
                  <div v-if="(!field.options || field.options.length === 0)" class="p-3 text-center text-xs text-slate-400">
                    No hay opciones configuradas
                  </div>
                </div>
              </div>
            </div>

            <!-- Select (Simple) -->
            <select
              v-else-if="field.field_type === 'select' || field.type === 'select'"
              v-model="formData[field.key]"
              class="w-full border border-[#E2E8F0] focus:border-[#EB5F46] bg-white rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] outline-none cursor-pointer"
            >
              <option value="" disabled>{{ field.placeholder || 'Seleccionar...' }}</option>
              <option v-for="opt in (field.options || [])" :key="opt" :value="opt">{{ opt }}</option>
            </select>
            <input
              v-else-if="field.field_type === 'date'"
              type="date"
              v-model="formData[field.key]"
              class="w-full border border-[#E2E8F0] focus:border-[#EB5F46] bg-white rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] outline-none"
            />
            <input
              v-else-if="field.field_type === 'number'"
              type="number"
              v-model="formData[field.key]"
              class="w-full border border-[#E2E8F0] focus:border-[#EB5F46] bg-white rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] outline-none"
            />
            <textarea
              v-else-if="field.field_type === 'textarea'"
              v-model="formData[field.key]"
              rows="2"
              class="w-full border border-[#E2E8F0] focus:border-[#EB5F46] bg-white rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] outline-none"
            ></textarea>
            <input
              v-else
              type="text"
              v-model="formData[field.key]"
              class="w-full border border-[#E2E8F0] focus:border-[#EB5F46] bg-white rounded-xl px-3.5 py-2.5 text-sm text-[#1E293B] outline-none"
            />
          </div>
        </div>

        <!-- Archivos Adjuntos -->
        <div class="pt-4 border-t border-slate-200">
          <div class="flex items-center gap-2 mb-3">
            <Paperclip class="w-4 h-4 text-[#EB5F46]" />
            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-700">Archivos de Sustento y Evidencias</h3>
          </div>
          <div v-if="!attachedFile" class="p-4 rounded-xl border border-dashed border-slate-200 bg-slate-50/60 text-center text-xs text-slate-400">
            No se han adjuntado evidencias complementarias a esta iniciativa.
          </div>
          <div v-else class="p-3 bg-white border border-slate-200 rounded-xl flex items-center justify-between max-w-md">
            <div class="flex items-center gap-2">
              <FileText class="w-4 h-4 text-blue-600" />
              <span class="text-xs font-semibold text-slate-800">{{ attachedFile.name }}</span>
            </div>
            <span class="text-[10px] text-slate-400">{{ (attachedFile.size / 1024).toFixed(0) }} KB</span>
          </div>
        </div>
      </div>

      <!-- Disclaimer y Sustento del Solicitante -->
      <div class="px-8 py-5 border-t border-[#F1F5F9] bg-[#FFFBEB]/30">
        <div :class="['flex items-start gap-3 p-4 rounded-xl border transition-all', disclaimerAccepted ? 'bg-emerald-50/60 border-emerald-200' : 'bg-amber-50/80 border-amber-300 ring-2 ring-amber-400/30']">
          <input
            type="checkbox"
            id="disclaimer-checkbox"
            v-model="disclaimerAccepted"
            class="w-5 h-5 mt-0.5 rounded border-amber-400 text-[#EB5F46] focus:ring-[#EB5F46] transition-colors cursor-pointer shrink-0"
          />
          <label for="disclaimer-checkbox" class="text-xs text-amber-950 leading-relaxed select-none cursor-pointer flex-1">
            <span class="font-bold text-amber-900 block mb-0.5">
              Declaración y Sustento del Solicitante (Key User):
            </span>
            <span>
              {{ consentStatement }}
            </span>
          </label>
        </div>
      </div>

      <!-- Botones de Acción -->
      <div class="px-8 py-5 border-t border-[#F1F5F9] bg-[#F8FAFC] flex flex-wrap items-center justify-between gap-3">
        <button
          type="button"
          @click="showChatModal = true"
          class="flex items-center gap-2 border border-[#E2E8F0] bg-white hover:bg-[#F1F5F9] text-[#64748B] px-4 py-2.5 rounded-lg text-sm font-semibold transition-colors cursor-pointer"
        >
          <MessageSquare class="w-4 h-4" />
          Ver conversación
        </button>

        <div class="flex items-center gap-3">
          <button
            type="button"
            @click="handleSaveDraft"
            :disabled="isSubmitting"
            class="flex items-center gap-2 border border-[#EB5F46] text-[#EB5F46] hover:bg-[#FFF0ED] px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors cursor-pointer"
          >
            <Save class="w-4 h-4" />
            Guardar Cambios
          </button>

          <button
            type="button"
            @click="handleSubmitToBPTI"
            :disabled="isSubmitting"
            class="flex items-center gap-2 bg-[#EB5F46] hover:bg-[#c94a32] text-white px-5 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-sm shadow-[#EB5F46]/20 cursor-pointer"
          >
            <Send class="w-4 h-4" />
            Enviar a aprobación de BP TI
          </button>
        </div>
      </div>
    </div>

    <!-- ── MODAL: VER CONVERSACIÓN CON TEO ── -->
    <div v-if="showChatModal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col overflow-hidden">
        <div class="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <div class="flex items-center gap-2">
            <Bot class="w-4 h-4 text-[#EB5F46]" />
            <h3 class="text-sm font-bold text-slate-800">Transcripción de la Conversación con Teo</h3>
          </div>
          <button @click="showChatModal = false" class="p-1 hover:bg-slate-200 rounded-lg text-slate-500">
            <X class="w-4 h-4" />
          </button>
        </div>
        <div class="p-6 overflow-y-auto space-y-4 flex-1">
          <div v-for="(msg, i) in chatHistory" :key="i" :class="['p-3.5 rounded-xl text-xs leading-relaxed', msg.role === 'user' ? 'bg-[#FFF0ED] text-[#EB5F46] font-medium' : 'bg-slate-50 border border-slate-200 text-slate-800']">
            <span class="font-bold block mb-1 uppercase tracking-wider text-[10px]">{{ msg.role === 'user' ? 'Solicitante' : 'Teo (IA)' }}:</span>
            {{ msg.text }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
