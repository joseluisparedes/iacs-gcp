<script setup lang="ts">
import { ref } from 'vue';

type C4Level = 'context' | 'container' | 'component' | 'dependencies';
const activeLevel = ref<C4Level>('container');

const components = [
  {
    id: 'frontend',
    name: 'Frontend Nuxt 4 (Vue 3 + TypeScript)',
    category: 'frontend',
    tech: 'Node.js 24 LTS / Cloud Run (Serverless)',
    level: 'L2',
    summary: 'Interfaz SPA/SSR moderna desacoplada de la base de datos, con componentes modulares y diseño corporativo Montserrat.',
    responsibilities: [
      'Renderizado interactivo de dashboards, matriz de calor y formularios con Teo',
      'Consumo exclusivo de APIs REST expuestas por FastAPI',
      'Compatibilidad total con auditoría WCAG y responsive mobile-first'
    ],
    protocol: 'HTTPS / TLS 1.3',
    criticality: 'Crítica',
    resilience: 'Autoescalado horizontal de 0 a 10 instancias en Cloud Run con CDN global.'
  },
  {
    id: 'backend',
    name: 'Backend FastAPI (Python 3.13)',
    category: 'backend',
    tech: 'Python 3.13 + FastAPI 0.116.x / Cloud Run',
    level: 'L2',
    summary: 'Capa central de lógica de negocio, orquestación de flujos de aprobación y contratos REST.',
    responsibilities: [
      'Validación de esquemas Pydantic v2 y control de transacciones SQLAlchemy 2.0',
      'Orquestación de llamadas a Vertex AI (Gemini 2.5 Flash) y parsing de documentos',
      'Emisión de dictámenes técnicos y firma digital de cadena de custodia'
    ],
    protocol: 'REST / JSON / OAuth2',
    criticality: 'Crítica',
    resilience: 'Contenedores stateless con healthchecks automáticos y graceful shutdown.'
  },
  {
    id: 'database',
    name: 'Cloud SQL for PostgreSQL 17',
    category: 'database',
    tech: 'PostgreSQL 17.x Administrado en GCP',
    level: 'L2',
    summary: 'Fuente única de verdad relacional con soporte nativo de JSONB para formularios dinámicos.',
    responsibilities: [
      'Persistencia de 26 tablas: iniciativas, workflows, roles, carpetas y auditoría',
      'Conexión segura vía Cloud SQL Auth Proxy con SSL forzado',
      'Pool de conexiones asíncrono con pool_pre_ping'
    ],
    protocol: 'PostgreSQL Protocol (5432)',
    criticality: 'Crítica',
    resilience: 'Alta disponibilidad con conmutación por error multizona y backups continuos.'
  },
  {
    id: 'ai-vertex',
    name: 'Google Cloud Vertex AI (Gemini 2.5 Flash / Pro)',
    category: 'ai',
    tech: 'Vertex AI Generative API / Python SDK',
    level: 'L2',
    summary: 'Motor de Inteligencia Artificial para el asistente Teo, metodología Grill-Me y síntesis de fichas.',
    responsibilities: [
      'Indagación constructiva activa (Grill-Me) sobre iniciativas de negocio',
      'Extracción estructurada de campos de la ficha técnica desde el diálogo',
      'Transcripción de audio multimodal (Speech-to-Text en español)'
    ],
    protocol: 'gRPC / HTTPS REST',
    criticality: 'Alta',
    resilience: 'Manejo de cuotas, reintentos con backoff exponencial y fallback simulado.'
  }
];

const selectedComp = ref(components[0]);
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center gap-2">
          <span class="p-2 rounded-xl bg-[#0D436C]/10 text-[#0D436C] font-bold text-lg">🏛️</span>
          <h1 class="text-2xl font-bold text-[#0D436C] tracking-tight">Arquitectura de Solución (Modelo C4 GCP)</h1>
        </div>
        <p class="text-sm text-slate-500 mt-1">
          Gobernanza arquitectónica del Golden Path corporativo adaptado a Google Cloud Platform y Clean Architecture.
        </p>
      </div>

      <!-- Selector de Niveles C4 -->
      <div class="flex items-center gap-1 bg-slate-100 p-1 rounded-xl">
        <button
          v-for="lvl in [
            { id: 'context', label: 'L1: Contexto' },
            { id: 'container', label: 'L2: Contenedores GCP' },
            { id: 'component', label: 'L3: Componentes' },
            { id: 'dependencies', label: 'L4: Resiliencia' }
          ]"
          :key="lvl.id"
          @click="activeLevel = lvl.id as C4Level"
          :class="[
            'px-3 py-1.5 text-xs font-bold rounded-lg transition-all',
            activeLevel === lvl.id ? 'bg-white text-[#0D436C] shadow-sm' : 'text-slate-500 hover:text-slate-800'
          ]"
        >
          {{ lvl.label }}
        </button>
      </div>
    </div>

    <!-- Diagrama y Ficha de Detalle (Split View) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <!-- Diagrama de Bloques (7 cols) -->
      <div class="lg:col-span-7 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 class="text-sm font-bold text-[#0D436C]">Topología de Componentes Cloud Run y Datos</h3>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div
            v-for="c in components"
            :key="c.id"
            @click="selectedComp = c"
            :class="[
              'p-4 rounded-xl border-2 cursor-pointer transition-all space-y-2',
              selectedComp.id === c.id
                ? 'border-[#0D436C] bg-blue-50/50 shadow'
                : 'border-slate-200 hover:border-slate-300 bg-white'
            ]"
          >
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-[#0D436C]">{{ c.name }}</span>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">{{ c.level }}</span>
            </div>
            <p class="text-[11px] text-slate-500 font-semibold">{{ c.tech }}</p>
            <p class="text-xs text-slate-600 line-clamp-2 leading-relaxed">{{ c.summary }}</p>
          </div>
        </div>

        <!-- Banner de Reglas Innegociables -->
        <div class="p-4 bg-amber-50 border border-amber-200 rounded-xl space-y-1 text-xs text-amber-900">
          <strong class="font-bold flex items-center gap-1.5">
            <span>🛡️</span> Principios del Golden Path Corporativo:
          </strong>
          <p>1. El frontend Nuxt nunca conecta directamente a la DB (desacoplamiento total).</p>
          <p>2. Todos los servicios externos (Vertex AI, Cloud Storage, M365) residen tras interfaces abstractas.</p>
          <p>3. Contenedores stateless sin privilegios de root optimizados para Cloud Run.</p>
        </div>
      </div>

      <!-- Ficha de Detalle de Componente (5 cols) -->
      <div class="lg:col-span-5 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div class="border-b border-slate-100 pb-3">
          <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Detalle Arquitectónico</span>
          <h3 class="text-base font-bold text-[#0D436C] mt-0.5">{{ selectedComp.name }}</h3>
          <p class="text-xs text-slate-500 font-semibold">{{ selectedComp.tech }}</p>
        </div>

        <div class="space-y-3 text-xs leading-relaxed">
          <div>
            <strong class="text-slate-700 block mb-1">Descripción:</strong>
            <p class="text-slate-600">{{ selectedComp.summary }}</p>
          </div>

          <div>
            <strong class="text-slate-700 block mb-1">Responsabilidades Primarias:</strong>
            <ul class="list-disc list-inside space-y-1 text-slate-600">
              <li v-for="(r, idx) in selectedComp.responsibilities" :key="idx">{{ r }}</li>
            </ul>
          </div>

          <div class="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100">
            <div>
              <strong class="text-slate-500 block text-[10px] uppercase">Protocolo:</strong>
              <span class="font-semibold text-slate-800">{{ selectedComp.protocol }}</span>
            </div>
            <div>
              <strong class="text-slate-500 block text-[10px] uppercase">Criticidad:</strong>
              <span class="font-bold text-red-600">{{ selectedComp.criticality }}</span>
            </div>
          </div>

          <div class="pt-2 border-t border-slate-100">
            <strong class="text-slate-700 block mb-1">Estrategia de Resiliencia:</strong>
            <p class="text-slate-600">{{ selectedComp.resilience }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
