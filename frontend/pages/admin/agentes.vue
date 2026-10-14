<script setup lang="ts">
import { ref, onMounted } from 'vue';

const config = useRuntimeConfig();
const apiBase = config.public.apiBase;

interface AgentTask {
  id: string;
  agent_role: string;
  task_title: string;
  status: 'completed' | 'in_progress' | 'pending';
  progress: number;
  created_at?: string;
}

const AGENT_TEMPLATES = [
  { id: '1', name: 'PO Men', role: 'PO Men', title: 'Product Owner', description: 'Define requerimientos y prioriza tareas', icon: '🧭', color: 'text-emerald-600', bg: 'bg-emerald-50 border-emerald-200' },
  { id: '2', name: 'Seguridad TI', role: 'Seguridad TI', title: 'Seguridad', description: 'Analiza vulnerabilidades y aplica políticas', icon: '🛡️', color: 'text-red-600', bg: 'bg-red-50 border-red-200' },
  { id: '3', name: 'Arqui', role: 'Arqui', title: 'Arquitecto Frontend', description: 'Diseña la estructura y UI/UX', icon: '🎨', color: 'text-pink-600', bg: 'bg-pink-50 border-pink-200' },
  { id: '4', name: 'Programador', role: 'Programador', title: 'Ingeniero Backend', description: 'Implementa lógica y bases de datos', icon: '💻', color: 'text-indigo-600', bg: 'bg-indigo-50 border-indigo-200' },
  { id: '5', name: 'QA', role: 'QA', title: 'Tester', description: 'Verifica calidad y busca bugs', icon: '🐞', color: 'text-amber-600', bg: 'bg-amber-50 border-amber-200' },
  { id: '6', name: 'Documentador', role: 'Documentador', title: 'Investigador', description: 'Redacta guías y manuales técnicos', icon: '📖', color: 'text-sky-600', bg: 'bg-sky-50 border-sky-200' },
  { id: '7', name: 'Líder técnico', role: 'Líder técnico', title: 'Orquestador', description: 'Supervisa el flujo y toma decisiones', icon: '⚡', color: 'text-violet-600', bg: 'bg-violet-50 border-violet-200' },
  { id: '8', name: 'Auditor IA', role: 'Auditor IA', title: 'Regulador de Tokens', description: 'Monitorea el uso de recursos IA (Vertex)', icon: '📊', color: 'text-orange-600', bg: 'bg-orange-50 border-orange-200' }
];

const agentLogs = ref<AgentTask[]>([]);
const loading = ref(false);
const selectedTask = ref<AgentTask | null>(null);

async function fetchLogs() {
  loading.value = true;
  try {
    const res = await $fetch<AgentTask[]>(`${apiBase}/admin/agents/logs`).catch(() => []);
    agentLogs.value = Array.isArray(res) ? res : [];
  } catch (err) {
    console.error('Error al cargar logs de agentes:', err);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchLogs();
});

function getAgentTasks(role: string) {
  return agentLogs.value.filter(l => l.agent_role === role);
}

function formatDate(dateStr?: string) {
  if (!dateStr) return 'Reciente';
  const d = new Date(dateStr);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' ' + d.toLocaleDateString();
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center gap-2">
          <span class="p-2 rounded-xl bg-[#0D436C]/10 text-[#0D436C] font-bold text-lg">🤖</span>
          <h1 class="text-2xl font-bold text-[#0D436C] tracking-tight">Tablero de Agentes IA</h1>
        </div>
        <p class="text-sm text-slate-500 mt-1">
          Supervisión operativa y registro de tareas ejecutadas por los 8 roles de agentes autónomos.
        </p>
      </div>

      <button
        @click="fetchLogs"
        class="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
      >
        <span>🔄</span> Actualizar Estado
      </button>
    </div>

    <!-- Grid de los 8 Agentes -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="agent in AGENT_TEMPLATES"
        :key="agent.id"
        class="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm flex flex-col justify-between space-y-3"
      >
        <!-- Info del Agente -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-2xl">{{ agent.icon }}</span>
            <span class="px-2 py-0.5 text-[10px] font-bold uppercase rounded-full bg-slate-100 text-slate-600">
              Activo
            </span>
          </div>
          <h3 class="font-bold text-sm text-[#0D436C]">{{ agent.name }}</h3>
          <p class="text-[11px] font-semibold text-slate-500">{{ agent.title }}</p>
          <p class="text-xs text-slate-600 mt-1 line-clamp-2">{{ agent.description }}</p>
        </div>

        <!-- Tareas Recientes del Agente -->
        <div class="pt-3 border-t border-slate-100 space-y-2">
          <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Últimas Tareas</span>
          <div v-if="getAgentTasks(agent.role).length === 0" class="text-[11px] text-slate-400 italic">
            Sin ejecuciones registradas
          </div>
          <div
            v-for="task in getAgentTasks(agent.role).slice(0, 2)"
            :key="task.id"
            @click="selectedTask = task"
            class="p-2 rounded-lg bg-slate-50 border border-slate-100 cursor-pointer hover:bg-blue-50/50 transition-colors"
          >
            <div class="flex items-center justify-between text-[11px] font-medium text-slate-800 truncate">
              <span class="truncate">{{ task.task_title }}</span>
              <span class="text-emerald-600 text-[10px] font-bold shrink-0">100%</span>
            </div>
            <!-- Progress Bar -->
            <div class="w-full bg-slate-200 rounded-full h-1 mt-1.5 overflow-hidden">
              <div class="bg-emerald-500 h-1 rounded-full" :style="{ width: `${task.progress || 100}%` }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Historial Detallado de Logs -->
    <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
      <h3 class="font-bold text-sm text-[#0D436C]">Historial Consolidado de Acciones</h3>
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-slate-50 text-slate-500 font-bold border-b border-slate-200">
            <tr>
              <th class="p-3">Agente</th>
              <th class="p-3">Tarea Realizada</th>
              <th class="p-3">Estado</th>
              <th class="p-3">Progreso</th>
              <th class="p-3">Fecha y Hora</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="log in agentLogs" :key="log.id" class="hover:bg-slate-50">
              <td class="p-3 font-bold text-[#0D436C]">{{ log.agent_role }}</td>
              <td class="p-3 text-slate-800">{{ log.task_title }}</td>
              <td class="p-3">
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700">
                  {{ log.status }}
                </span>
              </td>
              <td class="p-3 font-semibold">{{ log.progress }}%</td>
              <td class="p-3 text-slate-400">{{ formatDate(log.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Detalle Tarea -->
    <div v-if="selectedTask" class="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
        <div class="flex items-center justify-between border-b pb-3">
          <h3 class="font-bold text-sm text-[#0D436C]">Detalle de Ejecución</h3>
          <button @click="selectedTask = null" class="text-slate-400 hover:text-slate-600">✕</button>
        </div>
        <div class="space-y-2 text-xs">
          <div><strong class="text-slate-500">Agente:</strong> <span class="font-bold text-slate-800">{{ selectedTask.agent_role }}</span></div>
          <div><strong class="text-slate-500">Tarea:</strong> <span class="text-slate-800">{{ selectedTask.task_title }}</span></div>
          <div><strong class="text-slate-500">Estado:</strong> <span class="text-emerald-600 font-bold uppercase">{{ selectedTask.status }}</span></div>
          <div><strong class="text-slate-500">Progreso:</strong> {{ selectedTask.progress }}%</div>
        </div>
        <div class="flex justify-end pt-2">
          <button @click="selectedTask = null" class="px-4 py-1.5 text-xs font-bold text-white bg-[#0D436C] rounded-lg">Cerrar</button>
        </div>
      </div>
    </div>
  </div>
</template>
