<script setup lang="ts">
import { ref } from 'vue';

const phases = [
  {
    phase: 'Fase 1: Levantamiento y Registro',
    actor: 'Key User (Solicitante) + Teo (IA Vertex)',
    color: 'border-blue-500 bg-blue-50/40',
    badge: 'bg-blue-100 text-blue-800',
    states: [
      {
        name: 'Borrador (Draft)',
        desc: 'El usuario interactúa con Teo mediante la metodología Grill-Me. Se estructuran título, objetivo, dolor operativo y fechas tentativas.',
        rules: ['Obligatorio validar impacto y beneficio cuantificable', 'No se emiten aprobaciones en este punto']
      }
    ]
  },
  {
    phase: 'Fase 2: Evaluación Técnica y Dictamen',
    actor: 'Business Partner de TI (BP TI)',
    color: 'border-indigo-500 bg-indigo-50/40',
    badge: 'bg-indigo-100 text-indigo-800',
    states: [
      {
        name: 'Pendiente de Aprobación (Under Review)',
        desc: 'La iniciativa pasa formalmente a la bandeja del BP TI de la Vicepresidencia para emitir dictamen de viabilidad técnica y arquitectura.',
        rules: ['Dictamen técnico firmado digitalmente', 'Revisión de dependencias con Banner, Salesforce y SAP']
      },
      {
        name: 'Observada (Returned for Revision)',
        desc: 'El BP TI solicita aclaraciones técnicas o financieras al solicitante. El solicitante puede subsanar y reenviar.',
        rules: ['Comentarios de observación obligatorios', 'Notificación automática vía correo']
      }
    ]
  },
  {
    phase: 'Fase 3: Pase a Demanda y Ejecución',
    actor: 'Comité de TI / Oficina de Proyectos (PMO)',
    color: 'border-emerald-500 bg-emerald-50/40',
    badge: 'bg-emerald-100 text-emerald-800',
    states: [
      {
        name: 'En Demanda (Approved to Demand)',
        desc: 'Iniciativa aprobada con dictamen favorable para ingresar al portafolio priorizado de proyectos.',
        rules: ['Generación de Ficha Técnica Ejecutiva PDF oficial', 'Cierre de cadena de custodia']
      },
      {
        name: 'Desestimada (Rejected)',
        desc: 'Iniciativa rechazada o duplicada con sustento formal.',
        rules: ['Motivo de desestimación obligatorio', 'Estado terminal']
      }
    ]
  }
];
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center gap-2">
          <span class="p-2 rounded-xl bg-[#0D436C]/10 text-[#0D436C] font-bold text-lg">🔀</span>
          <h1 class="text-2xl font-bold text-[#0D436C] tracking-tight">Mapa Canónico de Estados del Ciclo de Vida</h1>
        </div>
        <p class="text-sm text-slate-500 mt-1">
          Gobernanza integral de transiciones, actores responsables y reglas de negocio del proceso de aprobación.
        </p>
      </div>

      <NuxtLink
        to="/admin/workflow-editor"
        class="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-[#0D436C] hover:bg-[#082942] rounded-lg transition-colors shadow-sm"
      >
        <span>📐</span> Abrir Editor Visual
      </NuxtLink>
    </div>

    <!-- Fases del Flujo Canónico -->
    <div class="space-y-6">
      <div
        v-for="(p, idx) in phases"
        :key="idx"
        :class="['p-6 rounded-2xl border-l-4 border bg-white shadow-sm space-y-4', p.color]"
      >
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div>
            <h3 class="text-base font-bold text-[#0D436C]">{{ p.phase }}</h3>
            <p class="text-xs text-slate-500 font-semibold mt-0.5">Responsables: {{ p.actor }}</p>
          </div>
          <span :class="['px-3 py-1 rounded-full text-xs font-bold w-fit', p.badge]">
            Etapa {{ idx + 1 }}
          </span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-for="(st, stIdx) in p.states"
            :key="stIdx"
            class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-2"
          >
            <h4 class="font-bold text-xs text-[#0D436C] flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-[#EB5F46]"></span>
              {{ st.name }}
            </h4>
            <p class="text-xs text-slate-600 leading-relaxed">{{ st.desc }}</p>

            <div class="pt-2 border-t border-slate-100 space-y-1">
              <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Reglas Innegociables:</span>
              <ul class="text-[11px] text-slate-500 space-y-0.5 list-disc list-inside">
                <li v-for="(rule, rIdx) in st.rules" :key="rIdx">{{ rule }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
