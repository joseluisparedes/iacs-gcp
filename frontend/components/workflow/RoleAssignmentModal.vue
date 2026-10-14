<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full border border-slate-200 overflow-hidden transform transition-all">
      <!-- Modal Header -->
      <div class="px-6 py-4 bg-gradient-to-r from-slate-900 to-indigo-950 text-white flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-indigo-300">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>
          <div>
            <h3 class="text-base font-bold text-white">Asignación de Roles por Etapa / Flujo</h3>
            <p class="text-xs text-indigo-200/70">Asigna usuarios específicos a los roles operativos de este flujo</p>
          </div>
        </div>
        <button @click="$emit('close')" class="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-6 space-y-6">
        <!-- New Assignment Form -->
        <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
          <h4 class="text-xs font-bold uppercase tracking-wider text-slate-700">Nueva Asignación</h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Rol Operativo</label>
              <select v-model="selectedRole" class="w-full text-xs rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 py-2">
                <option value="" disabled>Seleccione un rol...</option>
                <option v-for="r in workflowRoles" :key="r.value" :value="r.value">
                  {{ r.label }}
                </option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Usuario Asignado</label>
              <select v-model="selectedUserId" class="w-full text-xs rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 py-2">
                <option value="" disabled>Seleccione un usuario...</option>
                <option v-for="u in profiles" :key="u.id" :value="u.id">
                  {{ u.name }} ({{ u.email }})
                </option>
              </select>
            </div>
          </div>

          <div class="flex justify-end pt-1">
            <button
              @click="assignRole"
              :disabled="!selectedRole || !selectedUserId || isAssigning"
              class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors flex items-center gap-1.5"
            >
              <svg v-if="isAssigning" class="animate-spin -ml-1 mr-1 h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
              <span>{{ isAssigning ? 'Asignando...' : '+ Asignar Rol' }}</span>
            </button>
          </div>
        </div>

        <!-- Current Assignments List -->
        <div>
          <div class="flex items-center justify-between mb-3">
            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-700">
              Asignaciones Vigentes ({{ assignments.length }})
            </h4>
            <span class="text-[11px] text-slate-500">Total autorizaciones registradas en este flujo</span>
          </div>

          <div v-if="isLoading" class="py-8 text-center text-slate-400 text-xs">
            Cargando asignaciones...
          </div>

          <div v-else-if="assignments.length === 0" class="py-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
            <p class="text-xs text-slate-500">No hay asignaciones específicas configuradas para este flujo.</p>
            <p class="text-[11px] text-slate-400 mt-0.5">Los usuarios con los roles correspondientes en su perfil actuarán de forma transversal.</p>
          </div>

          <div v-else class="space-y-2 max-h-60 overflow-y-auto pr-1">
            <div
              v-for="a in assignments"
              :key="a.id"
              class="flex items-center justify-between p-3 rounded-lg border border-slate-200 hover:border-slate-300 bg-white transition-colors"
            >
              <div class="flex items-center gap-3">
                <span :class="getRoleBadgeClass(a.role_name)" class="text-[11px] font-bold px-2 py-0.5 rounded-full border">
                  {{ getRoleLabel(a.role_name) }}
                </span>
                <div>
                  <div class="text-xs font-semibold text-slate-800">{{ a.user_name }}</div>
                  <div class="text-[11px] text-slate-500">{{ a.user_email }}</div>
                </div>
              </div>
              <button
                @click="removeAssignment(a.id)"
                class="p-1.5 text-slate-400 hover:text-red-600 rounded-md hover:bg-red-50 transition-colors"
                title="Eliminar asignación"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="px-6 py-3 bg-slate-50 border-t border-slate-200 flex justify-end">
        <button
          @click="$emit('close')"
          class="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
        >
          Cerrar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

const props = defineProps<{
  isOpen: boolean
  workflowId?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const selectedRole = ref('')
const selectedUserId = ref('')
const isAssigning = ref(false)
const isLoading = ref(false)

const profiles = ref<any[]>([])
const assignments = ref<any[]>([])

const workflowRoles = [
  { value: 'registrador', label: 'Registrador / Solicitante', color: 'indigo' },
  { value: 'bp_ti', label: 'Business Partner de TI (BP)', color: 'blue' },
  { value: 'business_owner', label: 'Business Owner / Patrocinador', color: 'purple' },
  { value: 'vicepresidente_del_negocio', label: 'Vicepresidencia de Negocio (VP)', color: 'amber' },
  { value: 'gestor_de_la_demanda', label: 'Gestor de la Demanda / Priorizador', color: 'teal' },
  { value: 'lider_de_dominio', label: 'Líder de Dominio TI / Arquitecto', color: 'emerald' },
  { value: 'admin', label: 'Administrador de Gobierno TI', color: 'rose' },
]

const getRoleLabel = (roleKey: string) => {
  const r = workflowRoles.find(x => x.value === roleKey)
  return r ? r.label : roleKey
}

const getRoleBadgeClass = (roleKey: string) => {
  switch (roleKey) {
    case 'registrador': return 'bg-indigo-50 text-indigo-700 border-indigo-200'
    case 'bp_ti': return 'bg-blue-50 text-blue-700 border-blue-200'
    case 'business_owner': return 'bg-purple-50 text-purple-700 border-purple-200'
    case 'vicepresidente_del_negocio': return 'bg-amber-50 text-amber-700 border-amber-200'
    case 'gestor_de_la_demanda': return 'bg-teal-50 text-teal-700 border-teal-200'
    case 'lider_de_dominio': return 'bg-emerald-50 text-emerald-700 border-emerald-200'
    case 'admin': return 'bg-rose-50 text-rose-700 border-rose-200'
    default: return 'bg-slate-50 text-slate-700 border-slate-200'
  }
}

const loadProfiles = async () => {
  try {
    const res = await $fetch<any[]>('/api/v1/profiles')
    profiles.value = res || []
  } catch (err) {
    console.warn('Error loading profiles:', err)
  }
}

const loadAssignments = async () => {
  if (!props.workflowId) return
  isLoading.value = true
  try {
    const res = await $fetch<{ data: any[] }>(`/api/v1/workflow/definitions/${props.workflowId}/role-assignments`)
    assignments.value = res?.data || []
  } catch (err) {
    console.warn('Error loading role assignments:', err)
  } finally {
    isLoading.value = false
  }
}

const assignRole = async () => {
  if (!props.workflowId || !selectedRole.value || !selectedUserId.value) return
  isAssigning.value = true
  try {
    await $fetch(`/api/v1/workflow/definitions/${props.workflowId}/role-assignments`, {
      method: 'POST',
      body: {
        role_name: selectedRole.value,
        user_id: selectedUserId.value,
      },
    })
    selectedRole.value = ''
    selectedUserId.value = ''
    await loadAssignments()
  } catch (err: any) {
    alert(err?.data?.detail || 'Error al asignar el rol')
  } finally {
    isAssigning.value = false
  }
}

const removeAssignment = async (assignmentId: string) => {
  if (!props.workflowId) return
  try {
    await $fetch(`/api/v1/workflow/definitions/${props.workflowId}/role-assignments/${assignmentId}`, {
      method: 'DELETE',
    })
    await loadAssignments()
  } catch (err) {
    console.warn('Error removing assignment:', err)
  }
}

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    loadProfiles()
    loadAssignments()
  }
})
</script>
