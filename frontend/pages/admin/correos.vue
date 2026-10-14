<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';

const config = useRuntimeConfig();
const apiBase = config.public.apiBase;

interface EmailLog {
  id: string;
  initiative_id?: string;
  recipient: string;
  subject: string;
  body: string;
  status: 'sent' | 'failed';
  error_message?: string;
  created_at?: string;
}

const logs = ref<EmailLog[]>([]);
const loading = ref(false);
const search = ref('');
const statusFilter = ref<'all' | 'sent' | 'failed'>('all');
const selectedEmail = ref<EmailLog | null>(null);

async function fetchLogs() {
  loading.value = true;
  try {
    const res = await $fetch<EmailLog[]>(`${apiBase}/admin/emails/logs`).catch(() => []);
    logs.value = Array.isArray(res) ? res : [];
  } catch (err) {
    console.error('Error cargando logs de correos:', err);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchLogs();
});

const filteredLogs = computed(() => {
  return logs.value.filter(item => {
    const matchStatus = statusFilter.value === 'all' || item.status === statusFilter.value;
    const q = search.value.toLowerCase();
    const matchSearch = !q ||
      item.recipient.toLowerCase().includes(q) ||
      item.subject.toLowerCase().includes(q) ||
      (item.initiative_id && item.initiative_id.toLowerCase().includes(q));
    return matchStatus && matchSearch;
  });
});

function formatDate(dateStr?: string) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleString();
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center gap-2">
          <span class="p-2 rounded-xl bg-[#0D436C]/10 text-[#0D436C] font-bold text-lg">✉️</span>
          <h1 class="text-2xl font-bold text-[#0D436C] tracking-tight">Auditoría de Notificaciones por Correo</h1>
        </div>
        <p class="text-sm text-slate-500 mt-1">
          Registro y trazabilidad de correos corporativos despachados (Microsoft 365 / Exchange Online).
        </p>
      </div>

      <button
        @click="fetchLogs"
        class="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
      >
        <span>🔄</span> Actualizar
      </button>
    </div>

    <!-- Barra de Filtros -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
      <input
        v-model="search"
        type="text"
        placeholder="Buscar por destinatario, asunto o código..."
        class="w-full sm:w-80 px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0D436C]"
      />

      <div class="flex items-center gap-2">
        <span class="text-xs font-semibold text-slate-500">Estado:</span>
        <select
          v-model="statusFilter"
          class="px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0D436C]"
        >
          <option value="all">Todos los Estados</option>
          <option value="sent">Enviados con Éxito</option>
          <option value="failed">Fallidos</option>
        </select>
      </div>
    </div>

    <!-- Tabla de Logs -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div v-if="filteredLogs.length === 0" class="p-8 text-center text-xs text-slate-400">
        No se encontraron registros de correos enviados.
      </div>
      <table v-else class="w-full text-left text-xs">
        <thead class="bg-slate-50 text-slate-500 font-bold border-b border-slate-200">
          <tr>
            <th class="p-3.5">Fecha y Hora</th>
            <th class="p-3.5">Iniciativa</th>
            <th class="p-3.5">Destinatario</th>
            <th class="p-3.5">Asunto</th>
            <th class="p-3.5">Estado</th>
            <th class="p-3.5 text-right">Detalle</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="item in filteredLogs" :key="item.id" class="hover:bg-slate-50">
            <td class="p-3.5 text-slate-500 whitespace-nowrap">{{ formatDate(item.created_at) }}</td>
            <td class="p-3.5 font-bold text-[#0D436C]">{{ item.initiative_id || 'Global' }}</td>
            <td class="p-3.5 font-medium text-slate-800">{{ item.recipient }}</td>
            <td class="p-3.5 text-slate-700 font-semibold">{{ item.subject }}</td>
            <td class="p-3.5">
              <span
                :class="[
                  'px-2 py-0.5 rounded-full text-[10px] font-bold',
                  item.status === 'sent' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                ]"
              >
                {{ item.status === 'sent' ? 'Enviado' : 'Fallido' }}
              </span>
            </td>
            <td class="p-3.5 text-right">
              <button
                @click="selectedEmail = item"
                class="px-2.5 py-1 text-[11px] font-semibold text-[#0D436C] bg-blue-50 hover:bg-blue-100 rounded-lg border border-blue-200"
              >
                Ver Contenido
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal Ver Correo -->
    <div v-if="selectedEmail" class="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-xl w-full p-6 space-y-4 shadow-xl">
        <div class="flex items-center justify-between border-b pb-3">
          <h3 class="font-bold text-sm text-[#0D436C]">Detalle de Correo Notificado</h3>
          <button @click="selectedEmail = null" class="text-slate-400 hover:text-slate-600">✕</button>
        </div>

        <div class="space-y-2 text-xs">
          <div><strong class="text-slate-500">Para:</strong> {{ selectedEmail.recipient }}</div>
          <div><strong class="text-slate-500">Asunto:</strong> {{ selectedEmail.subject }}</div>
          <div><strong class="text-slate-500">Fecha:</strong> {{ formatDate(selectedEmail.created_at) }}</div>
          <div v-if="selectedEmail.error_message" class="p-2 bg-red-50 text-red-700 rounded-lg">
            <strong>Error:</strong> {{ selectedEmail.error_message }}
          </div>
        </div>

        <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 whitespace-pre-line leading-relaxed max-h-80 overflow-y-auto font-sans">
          {{ selectedEmail.body }}
        </div>

        <div class="flex justify-end pt-2">
          <button @click="selectedEmail = null" class="px-4 py-1.5 text-xs font-bold text-white bg-[#0D436C] rounded-lg">Cerrar</button>
        </div>
      </div>
    </div>
  </div>
</template>
