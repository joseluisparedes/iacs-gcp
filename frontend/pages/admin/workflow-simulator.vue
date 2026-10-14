<script setup lang="ts">
import { ref } from 'vue';

const nodes = [
  { id: 'node_borrador', label: 'Borrador', role: 'registrador', color: 'bg-slate-100 text-slate-700' },
  { id: 'node_pendiente', label: 'Pendiente de aprobación', role: 'bp_ti', color: 'bg-blue-100 text-blue-700' },
  { id: 'node_observada', label: 'Observada', role: 'registrador', color: 'bg-amber-100 text-amber-700' },
  { id: 'node_demanda', label: 'En demanda', role: 'admin', color: 'bg-emerald-100 text-emerald-700' },
  { id: 'node_desestimada', label: 'Desestimada', role: 'admin', color: 'bg-red-100 text-red-700' },
];

const currentNode = ref(nodes[0].id);
const selectedRole = ref('registrador');
const simulationLogs = ref<Array<{ from: string; to: string; action: string; allowed: boolean; role: string; time: string }>>([]);

const availableRoles = [
  { code: 'registrador', name: 'Key User (Registrador)' },
  { code: 'bp_ti', name: 'Business Partner TI (BP TI)' },
  { code: 'admin', name: 'Administrador General' },
  { code: 'invitado', name: 'Invitado' },
];

function simulateTransition(targetId: string, action: string) {
  const current = nodes.find(n => n.id === currentNode.value);
  const target = nodes.find(n => n.id === targetId);
  const now = new Date().toLocaleTimeString();

  // Rule verification
  let allowed = false;
  if (currentNode.value === 'node_borrador' && targetId === 'node_pendiente') {
    allowed = ['registrador', 'admin'].includes(selectedRole.value);
  } else if (currentNode.value === 'node_pendiente' && ['node_demanda', 'node_observada', 'node_desestimada'].includes(targetId)) {
    allowed = ['bp_ti', 'admin'].includes(selectedRole.value);
  } else if (currentNode.value === 'node_observada' && targetId === 'node_pendiente') {
    allowed = ['registrador', 'admin'].includes(selectedRole.value);
  }

  simulationLogs.value.unshift({
    from: current?.label || currentNode.value,
    to: target?.label || targetId,
    action,
    allowed,
    role: selectedRole.value,
    time: now,
  });

  if (allowed) {
    currentNode.value = targetId;
  }
}

function resetSimulation() {
  currentNode.value = nodes[0].id;
  simulationLogs.value = [];
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center gap-2">
          <span class="p-2 rounded-xl bg-[#0D436C]/10 text-[#0D436C] font-bold text-lg">⚡</span>
          <h1 class="text-2xl font-bold text-[#0D436C] tracking-tight">Simulador de Flujos de Trabajo</h1>
        </div>
        <p class="text-sm text-slate-500 mt-1">
          Prueba interactiva de transiciones de estado, permisos RBAC y guardas condicionales en el motor canónico.
        </p>
      </div>

      <button
        @click="resetSimulation"
        class="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
      >
        <span>🔄</span> Reiniciar Simulación
      </button>
    </div>

    <!-- Panel de Control del Simulador -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <!-- Columna Izquierda: Nodos y Acciones (7 cols) -->
      <div class="lg:col-span-7 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-5">
        <!-- Selector de Rol Activo para la prueba -->
        <div class="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-200">
          <div>
            <span class="text-xs font-bold text-slate-700">Simular Rol Activo:</span>
            <p class="text-[11px] text-slate-500">Determina qué acciones están autorizadas</p>
          </div>
          <select
            v-model="selectedRole"
            class="px-3 py-1.5 text-xs font-bold bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0D436C]"
          >
            <option v-for="r in availableRoles" :key="r.code" :value="r.code">{{ r.name }}</option>
          </select>
        </div>

        <!-- Visualización del Pipeline de Estados -->
        <div class="space-y-3">
          <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider">Estado Actual en la Máquina de Estados</h3>
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div
              v-for="n in nodes"
              :key="n.id"
              :class="[
                'p-4 rounded-xl border transition-all text-center space-y-1',
                currentNode === n.id
                  ? 'border-[#0D436C] ring-2 ring-[#0D436C]/20 bg-blue-50/50 shadow'
                  : 'border-slate-200 opacity-60 bg-white'
              ]"
            >
              <div v-if="currentNode === n.id" class="text-[10px] font-bold text-[#EB5F46] uppercase">● Posición Actual</div>
              <h4 class="font-bold text-xs text-slate-900">{{ n.label }}</h4>
              <span class="text-[10px] text-slate-500">Rol: {{ n.role }}</span>
            </div>
          </div>
        </div>

        <!-- Botones de Acción Disponibles -->
        <div class="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
          <h4 class="text-xs font-bold text-[#0D436C]">Disparar Transición de Estado</h4>
          <div class="flex flex-wrap gap-2">
            <button
              v-if="currentNode === 'node_borrador'"
              @click="simulateTransition('node_pendiente', 'Enviar a Revisión')"
              class="px-4 py-2 text-xs font-bold text-white bg-[#0D436C] hover:bg-[#082942] rounded-xl shadow-sm transition-colors"
            >
              Enviar a Revisión (BP TI) ➔
            </button>

            <template v-if="currentNode === 'node_pendiente'">
              <button
                @click="simulateTransition('node_demanda', 'Aprobar VoBo')"
                class="px-4 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-sm transition-colors"
              >
                ✓ Aprobar (Pase a Demanda)
              </button>
              <button
                @click="simulateTransition('node_observada', 'Observar')"
                class="px-4 py-2 text-xs font-bold text-amber-800 bg-amber-100 hover:bg-amber-200 rounded-xl transition-colors"
              >
                ⚠️ Observar Iniciativa
              </button>
              <button
                @click="simulateTransition('node_desestimada', 'Desestimar')"
                class="px-4 py-2 text-xs font-bold text-red-700 bg-red-100 hover:bg-red-200 rounded-xl transition-colors"
              >
                ✕ Desestimar
              </button>
            </template>

            <button
              v-if="currentNode === 'node_observada'"
              @click="simulateTransition('node_pendiente', 'Subsanar Observación')"
              class="px-4 py-2 text-xs font-bold text-white bg-[#0D436C] hover:bg-[#082942] rounded-xl shadow-sm transition-colors"
            >
              Subsanar y Reenviar a BP TI ➔
            </button>

            <div v-if="['node_demanda', 'node_desestimada'].includes(currentNode)" class="text-xs text-slate-500 italic">
              Estado terminal alcanzado. Puedes reiniciar la simulación con el botón superior.
            </div>
          </div>
        </div>
      </div>

      <!-- Columna Derecha: Trazabilidad y Logs del Simulador (5 cols) -->
      <div class="lg:col-span-5 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 class="text-sm font-bold text-[#0D436C] flex items-center justify-between">
          <span>Bitácora de Eventos de Simulación</span>
          <span class="text-xs text-slate-400 font-normal">{{ simulationLogs.length }} eventos</span>
        </h3>

        <div v-if="simulationLogs.length === 0" class="p-8 text-center text-xs text-slate-400 border border-dashed border-slate-200 rounded-xl">
          Ejecuta alguna transición para registrar la validación de reglas de negocio en tiempo real.
        </div>

        <div v-else class="space-y-2 max-h-[450px] overflow-y-auto">
          <div
            v-for="(log, idx) in simulationLogs"
            :key="idx"
            :class="[
              'p-3 rounded-xl border text-xs leading-relaxed',
              log.allowed ? 'bg-emerald-50/50 border-emerald-200 text-emerald-900' : 'bg-red-50/50 border-red-200 text-red-900'
            ]"
          >
            <div class="flex items-center justify-between font-bold">
              <span>{{ log.allowed ? '✓ Transición Permitida' : '✕ Bloqueado por RBAC' }}</span>
              <span class="text-[10px] opacity-70">{{ log.time }}</span>
            </div>
            <p class="text-[11px] mt-1">
              Acción: <strong>{{ log.action }}</strong> | Rol simulado: <strong>{{ log.role }}</strong>
            </p>
            <p class="text-[10px] text-slate-500 mt-0.5">
              {{ log.from }} ➔ {{ log.to }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
