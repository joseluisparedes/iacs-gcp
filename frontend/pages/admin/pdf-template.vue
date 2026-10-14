<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';

const config = useRuntimeConfig();
const apiBase = config.public.apiBase;

interface Margins {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

const templateName = ref('Plantilla Ejecutiva Oficial IACS');
const templateHtml = ref(`
<div style="font-family: 'Montserrat', sans-serif; color: #1E293B;">
  <div style="border-bottom: 2px solid #0D436C; padding-bottom: 12px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
    <div>
      <h1 style="color: #0D436C; font-size: 18pt; margin: 0; font-weight: bold;">IACS ENTERPRISE</h1>
      <p style="color: #64748B; font-size: 9pt; margin: 2px 0 0 0;">Ficha Oficial de Levantamiento de Iniciativa</p>
    </div>
    <div style="text-align: right;">
      <span style="background: #EB5F46; color: white; padding: 4px 10px; border-radius: 4px; font-size: 9pt; font-weight: bold;">{{id_corta}}</span>
      <p style="color: #64748B; font-size: 8pt; margin: 4px 0 0 0;">{{fecha_actual}}</p>
    </div>
  </div>

  <h2 style="color: #0D436C; font-size: 13pt; margin-bottom: 8px;">{{titulo}}</h2>
  <p style="font-size: 10pt; line-height: 1.5; color: #334155; margin-bottom: 16px;"><strong>Objetivo:</strong> {{objetivo}}</p>

  <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 9pt;">
    <tr style="background: #F8FAFC;">
      <td style="padding: 8px; border: 1px solid #E2E8F0; width: 25%;"><strong>Institución:</strong></td>
      <td style="padding: 8px; border: 1px solid #E2E8F0; width: 25%;">{{institucion}}</td>
      <td style="padding: 8px; border: 1px solid #E2E8F0; width: 25%;"><strong>Vicepresidencia:</strong></td>
      <td style="padding: 8px; border: 1px solid #E2E8F0; width: 25%;">{{vicepresidencia}}</td>
    </tr>
    <tr>
      <td style="padding: 8px; border: 1px solid #E2E8F0;"><strong>Dirección:</strong></td>
      <td style="padding: 8px; border: 1px solid #E2E8F0;">{{direccion}}</td>
      <td style="padding: 8px; border: 1px solid #E2E8F0;"><strong>Key User:</strong></td>
      <td style="padding: 8px; border: 1px solid #E2E8F0;">{{registrador}}</td>
    </tr>
    <tr style="background: #F8FAFC;">
      <td style="padding: 8px; border: 1px solid #E2E8F0;"><strong>BP TI Asignado:</strong></td>
      <td style="padding: 8px; border: 1px solid #E2E8F0;">{{bp_ti_asignado}}</td>
      <td style="padding: 8px; border: 1px solid #E2E8F0;"><strong>Fecha Requerida:</strong></td>
      <td style="padding: 8px; border: 1px solid #E2E8F0;">{{fecha_requerida}}</td>
    </tr>
  </table>

  <h3 style="color: #0D436C; font-size: 11pt; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px;">Descripción de la Necesidad</h3>
  <p style="font-size: 9.5pt; line-height: 1.6; color: #475569;">{{descripcion_de_la_necesidad}}</p>
</div>
`.trim());

const margins = ref<Margins>({ top: 20, right: 20, bottom: 20, left: 20 });
const saving = ref(false);

const variables = [
  { key: '{{titulo}}', desc: 'Título de la iniciativa' },
  { key: '{{id_corta}}', desc: 'ID corto (ej. COM-001)' },
  { key: '{{objetivo}}', desc: 'Objetivo principal de la solución' },
  { key: '{{institucion}}', desc: 'Institución (UPC, UPN, etc.)' },
  { key: '{{vicepresidencia}}', desc: 'Vicepresidencia solicitante' },
  { key: '{{direccion}}', desc: 'Dirección o departamento' },
  { key: '{{registrador}}', desc: 'Nombre del Key User' },
  { key: '{{bp_ti_asignado}}', desc: 'Business Partner de TI' },
  { key: '{{fecha_requerida}}', desc: 'Fecha límite de entrega' },
  { key: '{{fecha_actual}}', desc: 'Fecha de emisión del PDF' },
  { key: '{{descripcion_de_la_necesidad}}', desc: 'Detalle del problema' },
];

function insertVariable(vKey: string) {
  templateHtml.value += ` ${vKey} `;
}

const renderedPreview = computed(() => {
  let html = templateHtml.value;
  const mockVals: Record<string, string> = {
    '{{titulo}}': 'Automatización del proceso de captura de prospectos digitales',
    '{{id_corta}}': 'COM-001',
    '{{objetivo}}': 'Optimizar el embudo de admisión e integrar leads de Meta/Google al CRM Salesforce.',
    '{{institucion}}': 'UPC',
    '{{vicepresidencia}}': 'Comercial',
    '{{direccion}}': 'Dirección de Admisiones y Ventas',
    '{{registrador}}': 'Administrador General',
    '{{bp_ti_asignado}}': 'Carlos Mendoza',
    '{{fecha_requerida}}': '30/11/2026',
    '{{fecha_actual}}': new Date().toLocaleDateString(),
    '{{descripcion_de_la_necesidad}}': 'Demoras operativas de hasta 48 horas en la distribución de prospectos a los asesores comerciales.',
  };

  for (const [k, v] of Object.entries(mockVals)) {
    html = html.replaceAll(k, v);
  }
  return html;
});

async function saveTemplate() {
  saving.value = true;
  try {
    await $fetch(`${apiBase}/admin/pdf-templates`, {
      method: 'POST',
      body: {
        name: templateName.value,
        template_html: templateHtml.value,
        margins: margins.value,
      },
    });
    alert('Plantilla guardada con éxito.');
  } catch (err: any) {
    alert(err?.data?.detail || 'Error al guardar plantilla.');
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center gap-2">
          <span class="p-2 rounded-xl bg-[#0D436C]/10 text-[#0D436C] font-bold text-lg">📄</span>
          <h1 class="text-2xl font-bold text-[#0D436C] tracking-tight">Diseñador de Plantilla PDF</h1>
        </div>
        <p class="text-sm text-slate-500 mt-1">
          Configuración del formato imprimible oficial y exportación de fichas ejecutivas de iniciativas.
        </p>
      </div>

      <button
        @click="saveTemplate"
        :disabled="saving"
        class="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-[#EB5F46] hover:bg-[#d94f38] disabled:opacity-50 rounded-lg transition-colors shadow-sm"
      >
        <span>💾</span> {{ saving ? 'Guardando...' : 'Guardar Plantilla' }}
      </button>
    </div>

    <!-- Variables Disponibles -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-2">
      <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Variables Dinámicas Disponibles (Haz clic para insertar):</span>
      <div class="flex flex-wrap gap-1.5">
        <button
          v-for="v in variables"
          :key="v.key"
          @click="insertVariable(v.key)"
          class="px-2.5 py-1 text-[11px] font-mono font-semibold text-[#0D436C] bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors"
          :title="v.desc"
        >
          {{ v.key }}
        </button>
      </div>
    </div>

    <!-- Editor y Vista Previa A4 (Split View) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <!-- Editor HTML / CSS (6 cols) -->
      <div class="lg:col-span-6 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 class="text-sm font-bold text-[#0D436C]">Código HTML / Estilos</h3>
        <textarea
          v-model="templateHtml"
          rows="22"
          class="w-full p-3 font-mono text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-[#0D436C] bg-slate-50"
        ></textarea>

        <!-- Márgenes en MM -->
        <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
          <span class="text-xs font-bold text-slate-700">Márgenes de Impresión (mm)</span>
          <div class="grid grid-cols-4 gap-2 text-xs">
            <div>
              <label class="block text-[10px] text-slate-500">Sup.</label>
              <input v-model.number="margins.top" type="number" class="w-full px-2 py-1 border rounded" />
            </div>
            <div>
              <label class="block text-[10px] text-slate-500">Der.</label>
              <input v-model.number="margins.right" type="number" class="w-full px-2 py-1 border rounded" />
            </div>
            <div>
              <label class="block text-[10px] text-slate-500">Inf.</label>
              <input v-model.number="margins.bottom" type="number" class="w-full px-2 py-1 border rounded" />
            </div>
            <div>
              <label class="block text-[10px] text-slate-500">Izq.</label>
              <input v-model.number="margins.left" type="number" class="w-full px-2 py-1 border rounded" />
            </div>
          </div>
        </div>
      </div>

      <!-- Vista Previa Visual A4 (6 cols) -->
      <div class="lg:col-span-6 space-y-2">
        <h3 class="text-sm font-bold text-[#0D436C] flex items-center justify-between">
          <span>Vista Previa en Hoja A4</span>
          <span class="text-xs text-slate-400 font-normal">Escala 100%</span>
        </h3>
        <div class="bg-slate-200 p-6 rounded-2xl overflow-x-auto shadow-inner flex justify-center">
          <div
            class="bg-white shadow-xl rounded min-h-[600px] w-full max-w-[550px] p-8"
            :style="{
              paddingTop: `${margins.top}px`,
              paddingRight: `${margins.right}px`,
              paddingBottom: `${margins.bottom}px`,
              paddingLeft: `${margins.left}px`,
            }"
            v-html="renderedPreview"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>
