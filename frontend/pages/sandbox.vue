<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import {
  Brain, Mic, MicOff, Paperclip, Send, Sparkles, Copy,
  Download, FileCheck2, AlertTriangle, RotateCcw, CheckCircle2,
  ChevronRight, HelpCircle, Clock, Layers, Building2,
  SlidersHorizontal, X, FileText, ShieldAlert, ArrowRight,
  ExternalLink, Volume2, ListChecks, MessageSquare
} from 'lucide-vue-next';
import { useAiAssistant } from '~/composables/useAiAssistant';

definePageMeta({
  layout: false,
});

const config = useRuntimeConfig();
const apiBase = config.public.apiBase;
const router = useRouter();
const { aiName, aiAvatar, loadAiConfig } = useAiAssistant();

// ─── Interfaces ─────────────────────────────────────────────────────────────
interface DraftPreview {
  titulo_de_la_necesidad?: string;
  objetivo?: string;
  descripcion_de_la_necesidad?: string;
  beneficio_cuantitativo_anual?: string;
  proceso_y_areas_impactadas?: string;
  qu_pasa_si_no_lo_tenemos_en_esta_fecha?: string;
  sistemas_involucrados?: string[];
  institucion_sugerida?: string;
}

interface DimensionScore {
  score: number;
  comment: string;
}

interface Dimensions {
  problema_raiz?: DimensionScore;
  impacto_usuarios?: DimensionScore;
  metricas_exito?: DimensionScore;
  ecosistema_ti?: DimensionScore;
  restricciones_plazos?: DimensionScore;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'model';
  text: string;
  attachment?: {
    name: string;
    type?: string;
    size?: number;
  };
  options?: string[];
  timestamp: string;
}

// ─── Estado del Sandbox y Disponibilidad ───────────────────────────────────
const isEnabled = ref<boolean | null>(null);
const checkingStatus = ref(true);

// ─── Estado del Chat ────────────────────────────────────────────────────────
const messages = ref<ChatMessage[]>([
  {
    id: 'welcome-msg',
    role: 'model',
    text: '¡Hola! Soy **Teo**, tu **Business Partner de TI (BP TI) Senior** para **Laureate Perú** (UPC, UPN y Cibertec).\n\nMi misión es acompañarte a transformar tu idea o dolor operativo en una **necesidad técnica y funcional rigurosa**, lista para ser evaluada por los comités de TI.\n\nCuéntame con total libertad: **¿Qué situación, problema o mejora operativa deseas abordar en tu institución?** Puedes escribirlo, dictarlo por voz con el micrófono o arrastrar documentos con el clip 📎.',
    options: [
      'Optimización en los periodos pico de matrícula web',
      'Alerta temprana y predictiva para la retención estudiantil',
      'Automatización en convenios de pago y cobranzas con SAP'
    ],
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
]);

const inputMessage = ref('');
const isAiTyping = ref(false);
const activeViewTab = ref<'chat' | 'draft'>('chat');
const justUpdatedDraft = ref(false);

// ─── Estado de la Ficha Borrador y Dimensiones Socráticas ───────────────────
const draft = ref<DraftPreview>({
  titulo_de_la_necesidad: '',
  objetivo: '',
  descripcion_de_la_necesidad: '',
  beneficio_cuantitativo_anual: '',
  proceso_y_areas_impactadas: '',
  qu_pasa_si_no_lo_tenemos_en_esta_fecha: '',
  sistemas_involucrados: [],
  institucion_sugerida: 'Laureate Perú (Corporativo)'
});

const dimensions = ref<Dimensions>({
  problema_raiz: { score: 0, comment: 'Por iniciar conversación con Teo.' },
  impacto_usuarios: { score: 0, comment: 'Por iniciar conversación con Teo.' },
  metricas_exito: { score: 0, comment: 'Por iniciar conversación con Teo.' },
  ecosistema_ti: { score: 0, comment: 'Por iniciar conversación con Teo.' },
  restricciones_plazos: { score: 0, comment: 'Por iniciar conversación con Teo.' }
});

const readinessScore = ref(0);

// ─── Dispositivos de Audio y Grabación por Voz ─────────────────────────────
const audioDevices = ref<MediaDeviceInfo[]>([]);
const selectedDeviceId = ref('');
const isRecording = ref(false);
const recordingSeconds = ref(0);
const isTranscribing = ref(false);
const audioError = ref<string | null>(null);
const showMicSelector = ref(false);

let recognition: any = null;
let recordingTimer: any = null;

// ─── Adjuntos ───────────────────────────────────────────────────────────────
const attachedFile = ref<{
  file?: File;
  name: string;
  type: string;
  size: number;
  extractedText?: string;
} | null>(null);
const isUploadingFile = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);

// ─── Toast y Referencias ────────────────────────────────────────────────────
const toastMessage = ref<{ type: 'success' | 'info' | 'error'; text: string } | null>(null);
const officialDraftCreatedId = ref<string | null>(null);
const chatScrollRef = ref<HTMLDivElement | null>(null);
const textareaRef = ref<HTMLTextAreaElement | null>(null);

function showToast(text: string, type: 'success' | 'info' | 'error' = 'info') {
  toastMessage.value = { type, text };
  setTimeout(() => {
    toastMessage.value = null;
  }, 4000);
}

function scrollToBottom() {
  nextTick(() => {
    chatScrollRef.value?.scrollIntoView({ behavior: 'smooth' });
  });
}

function formatMarkdown(text: string): string {
  if (!text) return '';
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  html = html.replace(/```([\s\S]*?)```/g, '<pre class="bg-slate-100 p-2.5 rounded-xl text-xs font-mono my-2 overflow-x-auto border border-slate-200">$1</pre>');
  html = html.replace(/`([^`]+)`/g, '<code class="bg-slate-100 px-1.5 py-0.5 rounded text-xs font-mono text-indigo-600 font-semibold">$1</code>');
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-bold text-slate-900">$1</strong>');
  html = html.replace(/\*([^*]+)\*/g, '<em class="italic">$1</em>');
  html = html.replace(/^### (.*$)/gim, '<h4 class="font-bold text-slate-900 text-xs mt-2.5 mb-1">$1</h4>');
  html = html.replace(/^## (.*$)/gim, '<h3 class="font-bold text-slate-900 text-sm mt-3 mb-1">$1</h3>');
  html = html.replace(/^# (.*$)/gim, '<h2 class="font-bold text-slate-900 text-base mt-3 mb-1.5">$1</h2>');
  html = html.replace(/^\s*[-•]\s+(.*$)/gim, '<li class="ml-4 list-disc text-slate-800 my-0.5">$1</li>');
  html = html.replace(/\n\n/g, '<p class="my-2.5"></p>');
  html = html.replace(/\n/g, '<br/>');
  return html;
}

// ─── Carga Inicial y Disponibilidad del Sandbox ─────────────────────────────
onMounted(async () => {
  loadAiConfig();

  // Verificar estado del Sandbox
  checkingStatus.value = true;
  try {
    const res: any = await $fetch(`${apiBase}/sandbox/status`).catch(() => ({ enabled: true }));
    isEnabled.value = Boolean(res.enabled ?? true);
  } catch {
    isEnabled.value = true;
  } finally {
    checkingStatus.value = false;
  }

  // Detectar micrófonos disponibles
  try {
    if (navigator.mediaDevices?.enumerateDevices) {
      const devs = await navigator.mediaDevices.enumerateDevices();
      const inputs = devs.filter(d => d.kind === 'audioinput');
      audioDevices.value = inputs;
      if (inputs.length > 0) {
        selectedDeviceId.value = inputs[0].deviceId;
      }
    }
  } catch (err) {
    console.warn('Error enumerando dispositivos de audio:', err);
  }
});

onUnmounted(() => {
  if (recordingTimer) clearInterval(recordingTimer);
  if (recognition) {
    try { recognition.stop(); } catch {}
  }
});

// ─── Selector de Micrófonos con Permiso ─────────────────────────────────────
async function refreshDevicesWithPermission() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach(t => t.stop());
    const devs = await navigator.mediaDevices.enumerateDevices();
    const inputs = devs.filter(d => d.kind === 'audioinput');
    audioDevices.value = inputs;
    if (inputs.length > 0 && !selectedDeviceId.value) {
      selectedDeviceId.value = inputs[0].deviceId;
    }
    showMicSelector.value = !showMicSelector.value;
  } catch (err: any) {
    audioError.value = 'Permite el acceso al micrófono en el navegador para elegir el dispositivo.';
    showToast(audioError.value, 'error');
  }
}

// ─── Grabación por Voz (Web Speech API) ──────────────────────────────────────
function startRecording() {
  audioError.value = null;
  recordingSeconds.value = 0;
  const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (!SpeechRec) {
    audioError.value = 'El navegador no soporta reconocimiento de voz directo.';
    showToast(audioError.value, 'error');
    return;
  }

  try {
    recognition = new SpeechRec();
    recognition.lang = 'es-PE';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => {
      isRecording.value = true;
      recordingTimer = setInterval(() => {
        recordingSeconds.value++;
        if (recordingSeconds.value >= 60) stopRecording();
      }, 1000);
    };

    recognition.onresult = (event: any) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        finalTranscript += event.results[i][0].transcript;
      }
      if (finalTranscript) {
        inputMessage.value = (inputMessage.value ? inputMessage.value + ' ' : '') + finalTranscript;
      }
    };

    recognition.onerror = (event: any) => {
      audioError.value = event.error === 'not-allowed' ? 'Permiso de micrófono denegado.' : `Error: ${event.error}`;
      stopRecording();
    };

    recognition.onend = () => {
      stopRecording();
    };

    recognition.start();
  } catch (err: any) {
    audioError.value = 'No se pudo iniciar el micrófono: ' + (err.message || err);
    showToast(audioError.value, 'error');
  }
}

function stopRecording() {
  if (recordingTimer) {
    clearInterval(recordingTimer);
    recordingTimer = null;
  }
  isRecording.value = false;
  recordingSeconds.value = 0;
  if (recognition) {
    try { recognition.stop(); } catch {}
    recognition = null;
  }
}

// ─── Subida de Archivos Adjuntos ───────────────────────────────────────────
async function handleFileUpload(e: Event) {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  target.value = '';
  if (!file) return;

  if (file.size > 25 * 1024 * 1024) {
    showToast('El archivo supera el límite de 25 MB.', 'error');
    return;
  }

  isUploadingFile.value = true;
  try {
    const fd = new FormData();
    fd.append('file', file);
    const res: any = await $fetch(`${apiBase}/chat/attach-file`, {
      method: 'POST',
      body: fd,
    });

    attachedFile.value = {
      file,
      name: file.name,
      type: file.type || 'documento',
      size: file.size,
      extractedText: res.content || '',
    };
    showToast(`Archivo "${file.name}" cargado y listo para análisis.`, 'success');
  } catch (err: any) {
    showToast('No se pudo procesar el contenido del archivo.', 'error');
  } finally {
    isUploadingFile.value = false;
  }
}

// ─── Envío de Mensaje al Motor Socrático Teo ───────────────────────────────
async function handleSendMessage(textToSend?: string) {
  const message = textToSend !== undefined ? textToSend : inputMessage.value;
  if (!message.trim() && !attachedFile.value) return;

  const userText = message.trim();
  const currentAttachment = attachedFile.value ? { ...attachedFile.value } : undefined;

  inputMessage.value = '';
  attachedFile.value = null;

  const newChatHistory: ChatMessage[] = [
    ...messages.value,
    {
      id: 'user-' + Date.now(),
      role: 'user',
      text: userText,
      attachment: currentAttachment
        ? {
            name: currentAttachment.name,
            type: currentAttachment.type,
            size: currentAttachment.size
          }
        : undefined,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ];

  messages.value = newChatHistory;
  isAiTyping.value = true;
  scrollToBottom();

  try {
    const res: any = await $fetch(`${apiBase}/sandbox/chat`, {
      method: 'POST',
      body: {
        history: newChatHistory.map(m => ({ role: m.role, text: m.text })),
        message: userText,
        currentDraft: draft.value,
        attachment: currentAttachment
          ? {
              name: currentAttachment.name,
              type: currentAttachment.type,
              textContent: currentAttachment.extractedText
            }
          : undefined
      }
    });

    const aiData = res.data;

    const teoMsg: ChatMessage = {
      id: 'teo-' + Date.now(),
      role: 'model',
      text: aiData.text || 'Entendido. Sigamos profundizando en los detalles operativos.',
      options: aiData.options || [],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    messages.value.push(teoMsg);

    if (aiData.draftPreview) {
      draft.value = {
        ...draft.value,
        ...aiData.draftPreview,
        sistemas_involucrados: aiData.draftPreview.sistemas_involucrados || draft.value.sistemas_involucrados
      };
      justUpdatedDraft.value = true;
      setTimeout(() => {
        justUpdatedDraft.value = false;
      }, 5000);
    }

    if (aiData.dimensions) {
      dimensions.value = aiData.dimensions;
    }

    if (typeof aiData.readinessScore === 'number') {
      readinessScore.value = aiData.readinessScore;
    }
  } catch (err: any) {
    if (err.statusCode === 403) {
      isEnabled.value = false;
      showToast('El Sandbox ha sido desactivado por la Dirección de TI.', 'error');
      return;
    }

    const errorMsg: ChatMessage = {
      id: 'teo-err-' + Date.now(),
      role: 'model',
      text: 'Hubo una breve interrupción en la conexión con el motor cognitivo. Por favor, reformula o envía nuevamente tu mensaje.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    messages.value.push(errorMsg);
  } finally {
    isAiTyping.value = false;
    scrollToBottom();
  }
}

function handleQuickOption(opt: string) {
  handleSendMessage(opt);
}

function handleResetSession() {
  if (confirm('¿Deseas reiniciar la sesión de prueba del Sandbox? Se limpiará la conversación y la ficha actual.')) {
    messages.value = [
      {
        id: 'welcome-reset',
        role: 'model',
        text: '¡Sesión reiniciada! Soy **Teo**, tu **BP TI Senior** para **Laureate Perú**.\n\nPlantea cualquier nueva iniciativa o dolor operativo con total libertad. ¿Qué desafío abordamos hoy?',
        options: [
          'Optimización en los periodos pico de matrícula web',
          'Alerta temprana y predictiva para la retención estudiantil',
          'Automatización en convenios de pago y cobranzas con SAP'
        ],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ];
    draft.value = {
      titulo_de_la_necesidad: '',
      objetivo: '',
      descripcion_de_la_necesidad: '',
      beneficio_cuantitativo_anual: '',
      proceso_y_areas_impactadas: '',
      qu_pasa_si_no_lo_tenemos_en_esta_fecha: '',
      sistemas_involucrados: [],
      institucion_sugerida: 'Laureate Perú (Corporativo)'
    };
    dimensions.value = {
      problema_raiz: { score: 0, comment: 'Por iniciar conversación con Teo.' },
      impacto_usuarios: { score: 0, comment: 'Por iniciar conversación con Teo.' },
      metricas_exito: { score: 0, comment: 'Por iniciar conversación con Teo.' },
      ecosistema_ti: { score: 0, comment: 'Por iniciar conversación con Teo.' },
      restricciones_plazos: { score: 0, comment: 'Por iniciar conversación con Teo.' }
    };
    readinessScore.value = 0;
    officialDraftCreatedId.value = null;
    showToast('Sesión de Sandbox reiniciada.', 'info');
  }
}

// ─── Exportaciones ──────────────────────────────────────────────────────────
function handleCopyMarkdown() {
  const md = `
# LAUREATE PERÚ — FICHA DE NECESIDAD TI
**Generada y Articulada con Asistencia de Teo (BP TI Senior)**
*Nivel de Madurez / Claridad: ${readinessScore.value}%*

---

### 1. DATOS GENERALES
- **Título de la Necesidad:** ${draft.value.titulo_de_la_necesidad || 'Pendiente de definir'}
- **Institución / Alcance:** ${draft.value.institucion_sugerida || 'Laureate Perú (Corporativo)'}
- **Fecha de Articulación:** ${new Date().toLocaleDateString('es-PE')}

### 2. OBJETIVO SMART
${draft.value.objetivo || 'No especificado aún.'}

### 3. DESCRIPCIÓN DEL PROBLEMA DE NEGOCIO (DOLOR OPERATIVO)
${draft.value.descripcion_de_la_necesidad || 'No especificado aún.'}

### 4. IMPACTO Y BENEFICIOS
- **Beneficio Cuantitativo Anual:** ${draft.value.beneficio_cuantitativo_anual || 'En evaluación'}
- **Procesos y Áreas Impactadas:** ${draft.value.proceso_y_areas_impactadas || 'En evaluación'}

### 5. ARQUITECTURA Y ECOSISTEMA TI
- **Sistemas Involucrados:** ${draft.value.sistemas_involucrados?.join(', ') || 'Banner, Blackboard, etc.'}

### 6. RIESGOS Y PLAZOS
- **¿Qué pasa si no lo tenemos para esta fecha?:** ${draft.value.qu_pasa_si_no_lo_tenemos_en_esta_fecha || 'En evaluación'}

---
*Documento exportado desde el Laboratorio Teo (IACS)*
`.trim();

  navigator.clipboard.writeText(md);
  showToast('¡Ficha copiada al portapapeles en formato Markdown!', 'success');
}

function handleDownloadSummary() {
  const htmlContent = `
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Ficha Ejecutiva — ${draft.value.titulo_de_la_necesidad || 'Iniciativa TI'}</title>
  <style>
    body { font-family: 'Segoe UI', Arial, sans-serif; color: #1E293B; margin: 40px; line-height: 1.6; }
    .header { text-align: center; border-bottom: 2px solid #E2E8F0; padding-bottom: 20px; margin-bottom: 25px; }
    .header h1 { font-size: 20px; color: #EB5F46; margin: 0; text-transform: uppercase; letter-spacing: 1.5px; }
    .header h2 { font-size: 16px; color: #0F172A; margin: 5px 0 10px; }
    .score-badge { display: inline-block; background: #EEF2FF; color: #4338CA; padding: 4px 12px; border-radius: 9999px; font-weight: bold; font-size: 13px; }
    .section { margin-bottom: 22px; }
    .section-title { font-size: 13px; font-weight: bold; color: #FFFFFF; background: #EB5F46; padding: 6px 12px; border-radius: 4px; text-transform: uppercase; margin-bottom: 10px; }
    .box { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 12px 16px; font-size: 14px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
    .footer { margin-top: 40px; font-size: 11px; color: #94A3B8; text-align: center; border-top: 1px solid #E2E8F0; padding-top: 12px; }
  </style>
</head>
<body>
  <div class="header">
    <h1>LAUREATE PERÚ — TECNOLOGÍAS DE LA INFORMACIÓN</h1>
    <h2>Ficha Ejecutiva de Articulación de Necesidad</h2>
    <div class="score-badge">Índice de Madurez Teo: ${readinessScore.value}%</div>
  </div>

  <div class="section">
    <div class="section-title">1. Título de la Necesidad e Institución</div>
    <div class="box">
      <strong>Título:</strong> ${draft.value.titulo_de_la_necesidad || 'Pendiente'}<br>
      <strong>Institución:</strong> ${draft.value.institucion_sugerida || 'Laureate Perú'}
    </div>
  </div>

  <div class="section">
    <div class="section-title">2. Objetivo SMART</div>
    <div class="box">${draft.value.objetivo || 'Pendiente'}</div>
  </div>

  <div class="section">
    <div class="section-title">3. Descripción del Problema Operativo</div>
    <div class="box">${draft.value.descripcion_de_la_necesidad || 'Pendiente'}</div>
  </div>

  <div class="section">
    <div class="section-title">4. Impacto y Beneficio Cuantitativo</div>
    <div class="grid">
      <div class="box">
        <strong>Beneficio Anual:</strong><br>${draft.value.beneficio_cuantitativo_anual || 'En evaluación'}
      </div>
      <div class="box">
        <strong>Áreas y Procesos:</strong><br>${draft.value.proceso_y_areas_impactadas || 'En evaluación'}
      </div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">5. Ecosistema de Sistemas TI Involucrados</div>
    <div class="box">${draft.value.sistemas_involucrados?.join(', ') || 'Por definir'}</div>
  </div>

  <div class="section">
    <div class="section-title">6. ¿Qué pasa si no lo tenemos en la fecha requerida?</div>
    <div class="box">${draft.value.qu_pasa_si_no_lo_tenemos_en_esta_fecha || 'En evaluación'}</div>
  </div>

  <div class="footer">
    Documento oficial generado por el Asistente Inteligente Teo (IACS) • Laureate Perú
  </div>
</body>
</html>
`;

  const blob = new Blob([htmlContent], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Ficha_Teo_${(draft.value.titulo_de_la_necesidad || 'Iniciativa').replace(/\s+/g, '_')}.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast('Ficha Ejecutiva descargada con éxito.', 'success');
}
</script>

<template>
  <!-- ── Pantalla de Mantenimiento si el Sandbox está desactivado ── -->
  <div v-if="!checkingStatus && isEnabled === false" class="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 flex items-center justify-center p-6">
    <div class="max-w-md w-full bg-white rounded-3xl shadow-xl border border-slate-200 p-8 text-center space-y-6">
      <div class="w-16 h-16 rounded-2xl bg-amber-50 border border-amber-200 text-amber-600 flex items-center justify-center mx-auto shadow-sm">
        <ShieldAlert class="w-8 h-8" />
      </div>

      <div class="space-y-2">
        <span class="text-xs font-bold uppercase tracking-widest text-slate-400">
          Laureate Perú • IACS
        </span>
        <h2 class="text-xl font-bold text-slate-900">
          Laboratorio Teo en Mantenimiento
        </h2>
        <p class="text-sm text-slate-600 leading-relaxed">
          Esta sesión de prueba del Sandbox ha sido <strong>pausada temporalmente</strong> por la Dirección de TI.
        </p>
      </div>

      <div class="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-500 text-left space-y-1">
        <div class="font-semibold text-slate-700">¿Eres Administrador o evaluador?</div>
        <div>Activa nuevamente el servicio desde el panel de Administración de IACS para reanudar el acceso.</div>
      </div>

      <button
        @click="router.push('/')"
        class="w-full py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm transition-colors shadow-sm cursor-pointer"
      >
        Ir al Portal Principal
      </button>
    </div>
  </div>

  <!-- ── Sandbox Ejecutivo Completo (Split-Screen) ── -->
  <div v-else class="min-h-screen bg-[#F8FAFC] flex flex-col font-sans text-slate-800">
    <!-- ── Header Ejecutivo ── -->
    <header class="bg-white border-b border-slate-200/80 sticky top-0 z-30 shadow-xs">
      <div class="max-w-[1720px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full overflow-hidden border-2 border-slate-200 shadow-sm flex items-center justify-center bg-slate-100 shrink-0">
            <img v-if="aiAvatar" :src="aiAvatar" :alt="aiName || 'Teo'" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full bg-gradient-to-tr from-[#EB5F46] to-[#F2826E] flex items-center justify-center text-white">
              <Brain class="w-5 h-5" />
            </div>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h1 class="font-bold text-base text-slate-900 tracking-tight">
                Sandbox Ejecutivo — Teo BP TI
              </h1>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-100 text-emerald-700 border border-emerald-200">
                Fase 1 • CIO
              </span>
            </div>
            <p class="text-xs text-slate-500 hidden sm:block">
              Laureate Perú • Articulación Socrática de Necesidades TI
            </p>
          </div>
        </div>

        <div class="flex items-center gap-2 sm:gap-3">
          <!-- Selector de Micrófono -->
          <div class="relative">
            <button
              type="button"
              @click="refreshDevicesWithPermission"
              title="Configurar dispositivo de micrófono"
              :class="[
                'flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all cursor-pointer',
                selectedDeviceId
                  ? 'border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700'
                  : 'border-amber-200 bg-amber-50 text-amber-700'
              ]"
            >
              <SlidersHorizontal class="w-3.5 h-3.5" />
              <span class="hidden md:inline">
                {{ audioDevices.find(d => d.deviceId === selectedDeviceId)?.label.slice(0, 20) || 'Micrófono' }}
              </span>
            </button>

            <!-- Dropdown de Dispositivos -->
            <div
              v-if="showMicSelector"
              class="absolute right-0 mt-2 w-72 bg-white rounded-2xl border border-slate-200 shadow-xl p-3 z-50 animate-in fade-in zoom-in-95"
            >
              <div class="flex items-center justify-between pb-2 border-b border-slate-100 mb-2">
                <span class="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Seleccionar Micrófono
                </span>
                <button @click="showMicSelector = false" class="p-1 text-slate-400 hover:text-slate-600 rounded">
                  <X class="w-3.5 h-3.5" />
                </button>
              </div>
              <div class="space-y-1 max-h-48 overflow-y-auto">
                <p v-if="audioDevices.length === 0" class="text-xs text-slate-400 p-2">
                  No se encontraron dispositivos de audio.
                </p>
                <button
                  v-for="(dev, idx) in audioDevices"
                  :key="dev.deviceId || idx"
                  type="button"
                  @click="selectedDeviceId = dev.deviceId; showMicSelector = false; showToast(`Micrófono cambiado a: ${dev.label || `Dispositivo ${idx + 1}`}`, 'info')"
                  :class="[
                    'w-full text-left px-2.5 py-1.5 rounded-lg text-xs transition-colors flex items-center justify-between cursor-pointer',
                    selectedDeviceId === dev.deviceId
                      ? 'bg-[#FFF0ED] text-[#EB5F46] font-semibold'
                      : 'hover:bg-slate-50 text-slate-700'
                  ]"
                >
                  <span class="truncate">{{ dev.label || `Micrófono ${idx + 1}` }}</span>
                  <CheckCircle2 v-if="selectedDeviceId === dev.deviceId" class="w-3.5 h-3.5 shrink-0 text-[#EB5F46]" />
                </button>
              </div>
            </div>
          </div>

          <!-- Reiniciar Sesión -->
          <button
            @click="handleResetSession"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 hover:border-slate-300 bg-white hover:bg-slate-50 text-slate-600 text-xs font-semibold transition-colors cursor-pointer"
            title="Reiniciar prueba del Sandbox"
          >
            <RotateCcw class="w-3.5 h-3.5" />
            <span class="hidden sm:inline">Nueva Sesión</span>
          </button>

          <!-- Cerrar / Volver -->
          <button
            @click="router.push('/admin/ia-training')"
            class="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors cursor-pointer"
          >
            Cerrar
          </button>
        </div>
      </div>
    </header>

    <!-- ── Toast Flotante ── -->
    <div v-if="toastMessage" class="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-5 duration-200">
      <div
        :class="[
          'px-4 py-3 rounded-2xl shadow-lg border text-xs font-semibold flex items-center gap-2',
          toastMessage.type === 'success'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
            : toastMessage.type === 'error'
            ? 'bg-rose-50 border-rose-200 text-rose-800'
            : 'bg-indigo-50 border-indigo-200 text-indigo-800'
        ]"
      >
        <CheckCircle2 v-if="toastMessage.type === 'success'" class="w-4 h-4 text-emerald-600" />
        <AlertTriangle v-if="toastMessage.type === 'error'" class="w-4 h-4 text-rose-600" />
        <Sparkles v-if="toastMessage.type === 'info'" class="w-4 h-4 text-indigo-600" />
        <span>{{ toastMessage.text }}</span>
      </div>
    </div>

    <!-- ── Contenido Principal Dividido (Split-Screen) ── -->
    <main class="flex-1 max-w-[1720px] w-full mx-auto p-3 sm:p-5 grid grid-cols-1 lg:grid-cols-12 gap-5 min-h-0">
      <!-- Pestañas para Móviles/Tablets -->
      <div class="lg:hidden col-span-12 flex items-center p-1 bg-slate-100/90 rounded-2xl border border-slate-200">
        <button
          type="button"
          @click="activeViewTab = 'chat'"
          :class="[
            'flex-1 flex items-center justify-center gap-2 py-2 text-xs font-bold rounded-xl transition-all',
            activeViewTab === 'chat' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-700'
          ]"
        >
          <MessageSquare class="w-3.5 h-3.5 text-[#4F5AF5]" />
          <span>Diálogo con Teo</span>
        </button>
        <button
          type="button"
          @click="activeViewTab = 'draft'"
          :class="[
            'flex-1 flex items-center justify-center gap-2 py-2 text-xs font-bold rounded-xl transition-all relative',
            activeViewTab === 'draft' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-700'
          ]"
        >
          <FileText class="w-3.5 h-3.5 text-[#EB5F46]" />
          <span>Ficha IACS en Vivo</span>
          <span v-if="draft.titulo_de_la_necesidad" class="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
        </button>
      </div>

      <!-- ── COLUMNA IZQUIERDA: Diálogo Socrático con Teo (Cols 1-6) ── -->
      <div
        :class="[
          'lg:col-span-6 xl:col-span-6 flex flex-col bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden h-[calc(100vh-6.8rem)]',
          activeViewTab === 'chat' ? 'flex' : 'hidden lg:flex'
        ]"
      >
        <!-- Cabecera del Panel Izquierdo -->
        <div class="p-4 border-b border-slate-100 bg-slate-50/70 flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-full overflow-hidden border border-slate-200 shadow-2xs flex items-center justify-center bg-slate-100 shrink-0">
              <img v-if="aiAvatar" :src="aiAvatar" :alt="aiName || 'Teo'" class="w-full h-full object-cover" />
              <div v-else class="w-full h-full bg-gradient-to-tr from-[#EB5F46] to-[#F2826E] text-white flex items-center justify-center font-bold text-xs">
                T
              </div>
            </div>
            <div>
              <span class="text-xs font-bold text-slate-900 block leading-tight">
                Entrevista con Teo (BP TI Senior)
              </span>
              <span class="text-[10px] text-emerald-600 font-semibold flex items-center gap-1">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Especialista Laureate Perú • UPC, UPN, Cibertec
              </span>
            </div>
          </div>
          <span class="text-[10px] font-medium text-slate-400 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200/60 hidden sm:inline-block">
            Método Socrático
          </span>
        </div>

        <!-- Contenedor de Mensajes -->
        <div class="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4">
          <div
            v-for="(msg, idx) in messages"
            :key="msg.id"
            :class="['flex gap-3', msg.role === 'user' ? 'justify-end' : 'justify-start']"
          >
            <div
              v-if="msg.role !== 'user'"
              class="w-8 h-8 rounded-full overflow-hidden border border-slate-200 shadow-2xs flex items-center justify-center bg-slate-100 shrink-0 mt-0.5"
            >
              <img v-if="aiAvatar" :src="aiAvatar" :alt="aiName || 'Teo'" class="w-full h-full object-cover" />
              <div v-else class="w-full h-full bg-gradient-to-tr from-[#EB5F46] to-[#F2826E] text-white flex items-center justify-center font-bold text-xs">
                T
              </div>
            </div>

            <div class="max-w-[85%] space-y-2">
              <div
                :class="[
                  'px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm',
                  msg.role === 'user'
                    ? 'bg-[#4F5AF5] text-white rounded-tr-sm font-normal'
                    : 'bg-white border border-[#E2E8F0] text-[#1E293B] rounded-tl-sm'
                ]"
              >
                <!-- Archivo adjunto dentro de la burbuja -->
                <div
                  v-if="msg.attachment"
                  :class="[
                    'mb-2.5 p-2 rounded-xl border flex items-center gap-2 text-xs',
                    msg.role === 'user'
                      ? 'bg-white/15 border-white/20 text-white'
                      : 'bg-slate-50 border-slate-200 text-slate-700'
                  ]"
                >
                  <FileText class="w-4 h-4 shrink-0 opacity-90" />
                  <span class="font-semibold truncate flex-1">{{ msg.attachment.name }}</span>
                </div>

                <!-- Contenido del Mensaje -->
                <div v-if="msg.role === 'user'" class="whitespace-pre-wrap text-white text-sm font-normal leading-relaxed">
                  {{ msg.text }}
                </div>
                <div
                  v-else
                  class="prose prose-sm prose-slate max-w-none text-[#1E293B] leading-relaxed"
                  v-html="formatMarkdown(msg.text)"
                />

                <div
                  :class="[
                    'text-[10px] mt-1.5 font-medium',
                    msg.role === 'user' ? 'text-white/80 text-right' : 'text-[#94A3B8]'
                  ]"
                >
                  {{ msg.role === 'user' ? `Tú • ${msg.timestamp}` : `Teo (BP TI) • ${msg.timestamp}` }}
                </div>
              </div>

              <!-- Bloque de Opciones Rápidas Sugeridas (Último mensaje de Teo) -->
              <div
                v-if="msg.role !== 'user' && msg.options && msg.options.length > 0 && idx === messages.length - 1 && !isAiTyping"
                class="mt-2.5 p-3 sm:p-3.5 rounded-2xl bg-gradient-to-b from-slate-50 to-slate-100/70 border border-slate-200/80 shadow-xs animate-in fade-in-50 duration-200"
              >
                <div class="flex items-center gap-1.5 text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2.5 px-0.5">
                  <ListChecks class="w-3.5 h-3.5 text-[#EB5F46]" />
                  <span>Selecciona una opción sugerida o escribe libremente:</span>
                </div>
                <div class="flex flex-col gap-2">
                  <button
                    v-for="(opt, optIndex) in msg.options"
                    :key="optIndex"
                    type="button"
                    @click="handleQuickOption(opt)"
                    class="w-full flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all shadow-xs cursor-pointer bg-white hover:bg-[#EB5F46] text-slate-700 hover:text-white border border-slate-200/90 hover:border-[#EB5F46] active:scale-[0.99] group text-left"
                  >
                    <div class="flex items-center gap-2.5 min-w-0 flex-1">
                      <span class="w-5 h-5 rounded-md bg-slate-100 text-slate-600 group-hover:bg-white group-hover:text-[#EB5F46] flex items-center justify-center text-[10px] font-bold shrink-0 border border-slate-200/80 group-hover:border-white transition-all">
                        {{ String.fromCharCode(65 + (optIndex % 26)) }}
                      </span>
                      <span class="leading-snug transition-colors group-hover:text-white font-medium">
                        {{ opt }}
                      </span>
                    </div>
                    <ChevronRight class="w-4 h-4 text-slate-400 group-hover:text-white group-hover:translate-x-0.5 transition-all shrink-0 opacity-60 group-hover:opacity-100" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Indicador de Teo Pensando -->
          <div v-if="isAiTyping" class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full overflow-hidden border border-slate-200 shadow-2xs flex items-center justify-center bg-slate-100 shrink-0">
              <img v-if="aiAvatar" :src="aiAvatar" :alt="aiName || 'Teo'" class="w-full h-full object-cover animate-pulse" />
              <div v-else class="w-full h-full bg-[#EB5F46]/10 text-[#EB5F46] flex items-center justify-center">
                <Brain class="w-4 h-4 animate-pulse" />
              </div>
            </div>
            <div class="px-4 py-3 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-500 flex items-center gap-2 shadow-2xs">
              <span class="w-2 h-2 rounded-full bg-[#EB5F46] animate-ping" />
              <span>Teo está analizando y articulando la necesidad...</span>
            </div>
          </div>

          <div ref="chatScrollRef" />
        </div>

        <!-- Vista Previa de Archivo Adjunto en el Input -->
        <div v-if="attachedFile" class="px-4 py-2 bg-indigo-50/80 border-t border-indigo-100 flex items-center justify-between">
          <div class="flex items-center gap-2 text-xs text-indigo-900 truncate">
            <FileText class="w-4 h-4 text-indigo-600 shrink-0" />
            <span class="font-semibold truncate">{{ attachedFile.name }}</span>
            <span class="text-[10px] text-indigo-500">
              ({{ (attachedFile.size / 1024).toFixed(0) }} KB)
            </span>
          </div>
          <button
            type="button"
            @click="attachedFile = null"
            class="p-1 hover:bg-indigo-200 text-indigo-700 rounded-md transition-colors cursor-pointer"
            title="Quitar archivo"
          >
            <X class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- Alerta de Transcripción / Error de Audio -->
        <div v-if="isTranscribing" class="px-4 py-2 bg-amber-50 border-t border-amber-100 flex items-center gap-2 text-xs text-amber-800">
          <span class="w-2 h-2 rounded-full bg-amber-500 animate-ping" />
          <span>Transcribiendo audio del micrófono con el motor STT...</span>
        </div>
        <div v-if="audioError" class="px-4 py-2 bg-rose-50 border-t border-rose-100 flex items-center justify-between text-xs text-rose-700">
          <div class="flex items-center gap-1.5">
            <AlertTriangle class="w-3.5 h-3.5 text-rose-600 shrink-0" />
            <span>{{ audioError }}</span>
          </div>
          <button @click="audioError = null" class="text-rose-500 hover:text-rose-700 cursor-pointer">
            <X class="w-3 h-3" />
          </button>
        </div>

        <!-- Área de Entrada de Mensaje -->
        <div class="p-3 sm:p-4 border-t border-slate-200 bg-white">
          <form @submit.prevent="handleSendMessage()" class="space-y-2">
            <div class="relative border border-slate-200 focus-within:border-[#4F5AF5] focus-within:ring-2 focus-within:ring-[#4F5AF5]/20 rounded-2xl bg-white transition-all">
              <textarea
                ref="textareaRef"
                v-model="inputMessage"
                @keydown.enter.exact.prevent="handleSendMessage()"
                rows="2"
                :disabled="isAiTyping"
                placeholder="Escribe la necesidad con total libertad, o presiona el micrófono para hablar..."
                class="w-full px-4 pt-3 pb-10 text-xs sm:text-sm text-slate-800 placeholder-slate-400 bg-transparent resize-none focus:outline-none"
              ></textarea>

              <!-- Barra de Herramientas Inferior dentro del Input -->
              <div class="absolute bottom-2 left-3 right-3 flex items-center justify-between">
                <div class="flex items-center gap-1.5">
                  <!-- Botón Adjuntar Archivo -->
                  <input
                    ref="fileInputRef"
                    type="file"
                    @change="handleFileUpload"
                    class="hidden"
                    accept=".pdf,.docx,.xlsx,.xls,.txt,image/*"
                  />
                  <button
                    type="button"
                    @click="fileInputRef?.click()"
                    :disabled="isUploadingFile || isAiTyping"
                    class="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                    title="Adjuntar documento o evidencia (PDF, Excel, Word, Imagen)"
                  >
                    <Paperclip class="w-4 h-4" />
                  </button>

                  <!-- Botón Micrófono -->
                  <button
                    type="button"
                    @click="isRecording ? stopRecording() : startRecording()"
                    :disabled="isTranscribing || isAiTyping"
                    :class="[
                      'flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer',
                      isRecording
                        ? 'bg-rose-600 text-white animate-pulse'
                        : 'text-slate-500 hover:text-rose-600 hover:bg-rose-50'
                    ]"
                    :title="isRecording ? 'Detener grabación' : 'Grabar audio con micrófono'"
                  >
                    <MicOff v-if="isRecording" class="w-3.5 h-3.5" />
                    <Mic v-else class="w-3.5 h-3.5" />
                    <span v-if="isRecording">{{ recordingSeconds }}s</span>
                  </button>
                </div>

                <!-- Botón Enviar Coral/Indigo -->
                <button
                  type="submit"
                  :disabled="(!inputMessage.trim() && !attachedFile) || isAiTyping"
                  class="inline-flex items-center gap-1 px-3.5 py-1.5 rounded-xl bg-[#EB5F46] hover:bg-[#D94F37] disabled:opacity-40 disabled:hover:bg-[#EB5F46] text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
                >
                  <span>Enviar</span>
                  <Send class="w-3 h-3" />
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>

      <!-- ── COLUMNA DERECHA: Ficha Oficial IACS en Tiempo Real (Cols 7-12) ── -->
      <div
        :class="[
          'lg:col-span-6 xl:col-span-6 flex flex-col bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden h-[calc(100vh-6.8rem)]',
          activeViewTab === 'draft' ? 'flex' : 'hidden lg:flex'
        ]"
      >
        <!-- Cabecera del Panel con Indicador de Madurez -->
        <div class="p-4 sm:p-5 border-b border-slate-100 bg-slate-50/80">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <FileCheck2 class="w-4 h-4 text-[#EB5F46]" />
              <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Ficha Oficial IACS — Laureate Perú
              </span>
              <span
                v-if="justUpdatedDraft"
                class="flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-100/90 px-2 py-0.5 rounded-full animate-pulse border border-emerald-300"
              >
                <Sparkles class="w-3 h-3 text-emerald-600" />
                ¡Sincronizada en vivo!
              </span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="text-xs font-bold text-slate-500">Madurez:</span>
              <span
                :class="[
                  'text-xs font-extrabold px-2 py-0.5 rounded-full',
                  readinessScore >= 80
                    ? 'bg-emerald-100 text-emerald-700'
                    : readinessScore >= 50
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-slate-200 text-slate-700'
                ]"
              >
                {{ readinessScore }}%
              </span>
            </div>
          </div>

          <!-- Barra de Progreso General -->
          <div class="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
            <div
              :class="[
                'h-2 rounded-full transition-all duration-500',
                readinessScore >= 80
                  ? 'bg-emerald-500'
                  : readinessScore >= 50
                  ? 'bg-amber-500'
                  : readinessScore > 0
                  ? 'bg-[#EB5F46]'
                  : 'bg-transparent'
              ]"
              :style="{ width: `${Math.min(100, Math.max(0, readinessScore))}%` }"
            />
          </div>

          <!-- 5 Dimensiones Socráticas de Madurez -->
          <div class="grid grid-cols-5 gap-1.5 mt-3 text-center">
            <div
              v-for="dim in [
                { key: 'problema_raiz', label: 'Problema', data: dimensions.problema_raiz },
                { key: 'impacto_usuarios', label: 'Usuarios', data: dimensions.impacto_usuarios },
                { key: 'metricas_exito', label: 'Métricas', data: dimensions.metricas_exito },
                { key: 'ecosistema_ti', label: 'Sistemas', data: dimensions.ecosistema_ti },
                { key: 'restricciones_plazos', label: 'Plazos', data: dimensions.restricciones_plazos }
              ]"
              :key="dim.key"
              class="p-1.5 rounded-xl bg-white border border-slate-200/80 shadow-2xs"
              :title="dim.data?.comment || dim.label"
            >
              <div class="text-[10px] font-bold text-slate-500 uppercase truncate">
                {{ dim.label }}
              </div>
              <div class="text-xs font-bold text-slate-900 mt-0.5">
                {{ dim.data?.score ?? 0 }}%
              </div>
            </div>
          </div>

          <p v-if="readinessScore === 0" class="text-[11px] text-slate-400 mt-2 text-center italic">
            El avance de madurez iniciará en 0% e irá aumentando conforme Teo evalúe el rigor y detalle de la necesidad durante la conversación.
          </p>
        </div>

        <!-- Campos de la Ficha Borrador en Tiempo Real -->
        <div class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          <!-- Campo 1: Título -->
          <div
            :class="[
              'p-3.5 rounded-2xl bg-slate-50/70 border space-y-1 transition-all duration-500',
              justUpdatedDraft && draft.titulo_de_la_necesidad ? 'ring-2 ring-emerald-400 border-emerald-400 bg-emerald-50/50' : 'border-slate-200'
            ]"
          >
            <div class="flex items-center justify-between">
              <label class="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                Título de la Necesidad
              </label>
              <span v-if="draft.titulo_de_la_necesidad" class="text-[10px] font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200 flex items-center gap-1">
                <Sparkles class="w-2.5 h-2.5" /> Articulado en vivo por Teo
              </span>
            </div>
            <p class="text-sm font-bold text-slate-900">
              {{ draft.titulo_de_la_necesidad || 'Esperando que Teo sintetice el título a partir del diálogo...' }}
            </p>
          </div>

          <!-- Campo 2: Objetivo SMART -->
          <div
            :class="[
              'p-3.5 rounded-2xl bg-slate-50/70 border space-y-1 transition-all duration-500',
              justUpdatedDraft && draft.objetivo ? 'ring-2 ring-emerald-400 border-emerald-400 bg-emerald-50/50' : 'border-slate-200'
            ]"
          >
            <div class="flex items-center justify-between">
              <label class="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                Objetivo SMART
              </label>
              <span v-if="draft.objetivo" class="text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-200">
                Estructura SMART
              </span>
            </div>
            <p :class="['text-xs sm:text-sm leading-relaxed', draft.objetivo ? 'text-slate-800' : 'text-slate-400 italic']">
              {{ draft.objetivo || 'Teo estructurará un objetivo con verbo en infinitivo, impacto y medición cuantitativa.' }}
            </p>
          </div>

          <!-- Campo 3: Descripción del Dolor Operativo -->
          <div
            :class="[
              'p-3.5 rounded-2xl bg-slate-50/70 border space-y-1 transition-all duration-500',
              justUpdatedDraft && draft.descripcion_de_la_necesidad ? 'ring-2 ring-emerald-400 border-emerald-400 bg-emerald-50/50' : 'border-slate-200'
            ]"
          >
            <label class="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Descripción del Problema Operativo
            </label>
            <p :class="['text-xs sm:text-sm leading-relaxed whitespace-pre-line', draft.descripcion_de_la_necesidad ? 'text-slate-800' : 'text-slate-400 italic']">
              {{ draft.descripcion_de_la_necesidad || 'El problema de fondo será delimitado conforme el usuario responda a las repreguntas.' }}
            </p>
          </div>

          <!-- Campos 4 & 5: Beneficios y Procesos (Grid de 2 columnas con bordes de color) -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div class="p-3 rounded-2xl bg-emerald-50/60 border border-emerald-300 space-y-1">
              <label class="text-[10px] font-bold uppercase tracking-wider text-emerald-800">
                Beneficio Cuantitativo Anual
              </label>
              <p class="text-xs text-emerald-950 font-medium">
                {{ draft.beneficio_cuantitativo_anual || 'Por cuantificar...' }}
              </p>
            </div>

            <div class="p-3 rounded-2xl bg-indigo-50/60 border border-indigo-300 space-y-1">
              <label class="text-[10px] font-bold uppercase tracking-wider text-indigo-800">
                Procesos y Áreas Impactadas
              </label>
              <p class="text-xs text-indigo-950 font-medium">
                {{ draft.proceso_y_areas_impactadas || 'Por determinar...' }}
              </p>
            </div>
          </div>

          <!-- Campo 6: Sistemas Involucrados -->
          <div class="p-3.5 rounded-2xl bg-slate-50/70 border border-slate-200 space-y-1.5">
            <label class="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Sistemas y Ecosistema TI Identificados
            </label>
            <div class="flex flex-wrap gap-1.5">
              <template v-if="draft.sistemas_involucrados && draft.sistemas_involucrados.length > 0">
                <span
                  v-for="(sys, idx) in draft.sistemas_involucrados"
                  :key="idx"
                  class="px-2.5 py-1 rounded-lg text-xs font-semibold bg-white border border-slate-200 text-slate-800 shadow-2xs"
                >
                  {{ sys }}
                </span>
              </template>
              <span v-else class="text-xs text-slate-400 italic">
                Banner, Blackboard, Salesforce, SAP u otros según el diálogo.
              </span>
            </div>
          </div>

          <!-- Campo 7: Plazos y Riesgos -->
          <div class="p-3.5 rounded-2xl bg-slate-50/70 border border-slate-200 space-y-1">
            <label class="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              ¿Qué pasa si no lo tenemos para esta fecha?
            </label>
            <p :class="['text-xs sm:text-sm leading-relaxed', draft.qu_pasa_si_no_lo_tenemos_en_esta_fecha ? 'text-slate-800' : 'text-slate-400 italic']">
              {{ draft.qu_pasa_si_no_lo_tenemos_en_esta_fecha || 'Riesgo institucional o cuello de botella si se retrasa.' }}
            </p>
          </div>
        </div>

        <!-- Pie del Panel: Acciones Ejecutivas -->
        <div class="p-4 border-t border-slate-200 bg-slate-50/90 space-y-2">
          <div class="grid grid-cols-2 gap-2">
            <!-- Copiar Markdown -->
            <button
              type="button"
              @click="handleCopyMarkdown"
              class="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 font-semibold text-xs transition-colors shadow-2xs cursor-pointer"
              title="Copiar contenido de la ficha al portapapeles"
            >
              <Copy class="w-3.5 h-3.5" />
              <span>Copiar Ficha</span>
            </button>

            <!-- Descargar Resumen -->
            <button
              type="button"
              @click="handleDownloadSummary"
              class="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 font-semibold text-xs transition-colors shadow-2xs cursor-pointer"
              title="Descargar resumen ejecutivo en HTML imprimible"
            >
              <Download class="w-3.5 h-3.5" />
              <span>Descargar</span>
            </button>
          </div>

          <!-- Enlace Directo si fue guardada -->
          <div v-if="officialDraftCreatedId" class="p-2.5 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-between text-xs text-emerald-800">
            <span>Iniciativa guardada como borrador oficial.</span>
            <button
              @click="router.push(`/nueva/${officialDraftCreatedId}`)"
              class="font-bold underline flex items-center gap-1 text-emerald-900 hover:text-emerald-700 cursor-pointer"
            >
              <span>Abrir Ficha</span>
              <ExternalLink class="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
