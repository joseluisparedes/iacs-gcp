<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { Building2, Network, Trash2, Save, X, Edit2 } from 'lucide-vue-next';

const config = useRuntimeConfig();
const apiBase = config.public.apiBase;

interface VP {
  id: string;
  name: string;
  bp_name?: string;
}

interface Direccion {
  id: string;
  name: string;
  vp_id: string;
}

const vps = ref<VP[]>([]);
const direcciones = ref<Direccion[]>([]);
const loading = ref(true);
const selectedVP = ref<string | null>(null);

// Forms
const vpName = ref('');
const editingVP = ref<string | null>(null);

const dirName = ref('');
const editingDir = ref<string | null>(null);

async function fetchData() {
  loading.value = true;
  try {
    const [vpRes, dirRes] = await Promise.all([
      $fetch<VP[]>(`${apiBase}/admin/estructura/vps`).catch(() => []),
      $fetch<Direccion[]>(`${apiBase}/admin/estructura/direcciones`).catch(() => [])
    ]);
    vps.value = Array.isArray(vpRes) ? vpRes : [];
    direcciones.value = Array.isArray(dirRes) ? dirRes : [];

    if (vps.value.length > 0 && !selectedVP.value) {
      // Default select "Comercial" if available, else first
      const com = vps.value.find(v => v.name === 'Comercial');
      selectedVP.value = com ? com.id : vps.value[0].id;
    }
  } catch (err) {
    console.error('Error al cargar estructura:', err);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchData();
});

const currentVP = computed(() => vps.value.find(v => v.id === selectedVP.value));
const currentDirecciones = computed(() => {
  if (!selectedVP.value) return [];
  return direcciones.value.filter(d => d.vp_id === selectedVP.value);
});

async function handleSaveVP() {
  if (!vpName.value.trim()) return;
  try {
    const res = await $fetch<VP>(`${apiBase}/admin/estructura/vps`, {
      method: 'POST',
      body: {
        id: editingVP.value,
        name: vpName.value.trim(),
      }
    });
    if (editingVP.value) {
      vps.value = vps.value.map(v => v.id === editingVP.value ? res : v);
    } else {
      vps.value.push(res);
      selectedVP.value = res.id;
    }
    cancelEditVP();
  } catch (err: any) {
    alert(err?.data?.detail || 'Error al guardar VP');
  }
}

function handleEditVP(vp: VP) {
  editingVP.value = vp.id;
  vpName.value = vp.name;
}

function cancelEditVP() {
  editingVP.value = null;
  vpName.value = '';
}

async function handleDeleteVP(id: string) {
  if (!confirm('Eliminar esta VP eliminará todas sus Direcciones. ¿Continuar?')) return;
  try {
    await $fetch(`${apiBase}/admin/estructura/vps/${id}`, { method: 'DELETE' });
    vps.value = vps.value.filter(v => v.id !== id);
    if (selectedVP.value === id) {
      selectedVP.value = vps.value.length > 0 ? vps.value[0].id : null;
    }
  } catch (err) {
    alert('Error al eliminar Vicepresidencia');
  }
}

async function handleSaveDir() {
  if (!dirName.value.trim() || !selectedVP.value) return;
  try {
    const res = await $fetch<Direccion>(`${apiBase}/admin/estructura/direcciones`, {
      method: 'POST',
      body: {
        id: editingDir.value,
        name: dirName.value.trim(),
        vp_id: selectedVP.value,
      }
    });
    if (editingDir.value) {
      direcciones.value = direcciones.value.map(d => d.id === editingDir.value ? res : d);
    } else {
      direcciones.value.push(res);
    }
    cancelEditDir();
  } catch (err: any) {
    alert(err?.data?.detail || 'Error al guardar Dirección');
  }
}

function handleEditDir(dir: Direccion) {
  editingDir.value = dir.id;
  dirName.value = dir.name;
}

function cancelEditDir() {
  editingDir.value = null;
  dirName.value = '';
}

async function handleDeleteDir(id: string) {
  if (!confirm('¿Eliminar esta Dirección?')) return;
  try {
    await $fetch(`${apiBase}/admin/estructura/direcciones/${id}`, { method: 'DELETE' });
    direcciones.value = direcciones.value.filter(d => d.id !== id);
  } catch (err) {
    alert('Error al eliminar Dirección');
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Encabezado Superior (Idéntico a Imagen 1) -->
    <div class="bg-white p-6 rounded-2xl shadow-sm border border-[#E2E8F0]">
      <h1 class="text-2xl font-bold text-[#1E293B] flex items-center gap-3">
        <Network class="w-7 h-7 text-[#EB5F46]" />
        Estructura Organizativa
      </h1>
      <p class="text-[#64748B] mt-1 text-sm">
        Configura las Vicepresidencias y sus Direcciones respectivas para la organización institucional.
      </p>
    </div>

    <!-- Layout 2 Columnas Iguales -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-[600px]">
      <!-- Columna Izquierda: Vicepresidencias (VPs) -->
      <div class="bg-white rounded-2xl shadow-sm border border-[#E2E8F0] flex flex-col overflow-hidden">
        <div class="p-5 border-b border-[#E2E8F0] bg-[#F8FAFC]">
          <h2 class="font-bold text-[#1E293B] flex items-center gap-2">
            <Building2 class="w-5 h-5 text-[#EB5F46]" />
            Vicepresidencias (VPs)
          </h2>
        </div>

        <!-- Formulario VP -->
        <form @submit.prevent="handleSaveVP" class="p-4 border-b border-[#E2E8F0] bg-white space-y-3">
          <div>
            <label class="block text-[10px] font-semibold text-[#94A3B8] uppercase tracking-wider mb-1">
              NOMBRE DE LA VICEPRESIDENCIA
            </label>
            <input 
              required 
              v-model="vpName" 
              class="w-full px-3 py-2 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl text-sm outline-none focus:border-[#EB5F46] text-[#1E293B]" 
              placeholder="Ej: VP Finanzas" 
            />
          </div>
          <div class="flex gap-2">
            <button 
              type="submit" 
              class="flex-1 bg-[#EB5F46] hover:bg-[#c94a32] text-white text-sm font-semibold py-2 rounded-xl transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-xs"
            >
              <Save class="w-4 h-4" />
              <span>{{ editingVP ? 'Guardar Cambios' : 'Añadir VP' }}</span>
            </button>
            <button 
              v-if="editingVP" 
              type="button" 
              @click="cancelEditVP" 
              class="px-3 py-2 border border-[#E2E8F0] text-[#64748B] hover:bg-[#F8FAFC] rounded-xl transition-colors cursor-pointer"
            >
              <X class="w-4 h-4" />
            </button>
          </div>
        </form>

        <!-- Lista VPs -->
        <div class="flex-1 overflow-y-auto p-4 space-y-2 bg-[#F8FAFC]">
          <div v-if="loading" class="flex justify-center p-4">
            <div class="animate-spin rounded-full h-6 w-6 border-2 border-[#EB5F46] border-t-transparent"></div>
          </div>
          <p v-else-if="vps.length === 0" class="text-center text-sm text-[#94A3B8] italic p-4">
            No hay VPs registradas.
          </p>
          <div 
            v-else
            v-for="vp in vps" 
            :key="vp.id" 
            @click="selectedVP = vp.id"
            :class="[
              'flex items-center justify-between p-3.5 rounded-xl border cursor-pointer transition-all',
              selectedVP === vp.id 
                ? 'bg-[#FFF0ED] border-[#FCD9D2] shadow-xs' 
                : 'bg-white border-[#E2E8F0] hover:border-[#FCD9D2] hover:bg-[#FFF0ED]/40'
            ]"
          >
            <div class="min-w-0">
              <p :class="['font-semibold text-sm truncate', selectedVP === vp.id ? 'text-[#EB5F46]' : 'text-[#1E293B]']">
                {{ vp.name }}
              </p>
            </div>
            <div class="flex items-center gap-1 shrink-0 ml-2" @click.stop>
              <button 
                @click="handleEditVP(vp)" 
                class="p-1.5 text-[#94A3B8] hover:text-[#EB5F46] hover:bg-[#FFF0ED] rounded-lg transition-colors cursor-pointer"
                title="Editar"
              >
                <Edit2 class="w-4 h-4" />
              </button>
              <button 
                @click="handleDeleteVP(vp.id)" 
                class="p-1.5 text-[#94A3B8] hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
                title="Eliminar"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Columna Derecha: Direcciones de [VP] -->
      <div class="bg-white rounded-2xl shadow-sm border border-[#E2E8F0] flex flex-col overflow-hidden">
        <div class="p-5 border-b border-[#E2E8F0] bg-[#F8FAFC]">
          <h2 class="font-bold text-[#1E293B] flex items-center gap-2">
            <Network class="w-5 h-5 text-emerald-500" />
            Direcciones de {{ currentVP?.name || 'la VP' }}
          </h2>
        </div>

        <div v-if="!selectedVP" class="flex-1 flex items-center justify-center p-6 text-center text-[#94A3B8]">
          <p>Selecciona una Vicepresidencia en la lista izquierda para administrar sus Direcciones.</p>
        </div>
        <template v-else>
          <!-- Formulario Dirección -->
          <form @submit.prevent="handleSaveDir" class="p-4 border-b border-[#E2E8F0] bg-white space-y-3">
            <div>
              <label class="block text-[10px] font-semibold text-[#94A3B8] uppercase tracking-wider mb-1">
                NOMBRE DE LA DIRECCIÓN
              </label>
              <input 
                required 
                v-model="dirName" 
                class="w-full px-3 py-2 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl text-sm outline-none focus:border-emerald-500 text-[#1E293B]" 
                placeholder="Ej: Dirección de TI" 
              />
            </div>
            <div class="flex gap-2">
              <button 
                type="submit" 
                class="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-semibold py-2 rounded-xl transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-xs"
              >
                <Save class="w-4 h-4" />
                <span>{{ editingDir ? 'Guardar Cambios' : 'Añadir Dirección' }}</span>
              </button>
              <button 
                v-if="editingDir" 
                type="button" 
                @click="cancelEditDir" 
                class="px-3 py-2 border border-[#E2E8F0] text-[#64748B] hover:bg-[#F8FAFC] rounded-xl transition-colors cursor-pointer"
              >
                <X class="w-4 h-4" />
              </button>
            </div>
          </form>

          <!-- Lista de Direcciones -->
          <div class="flex-1 overflow-y-auto p-4 space-y-2 bg-[#F8FAFC]">
            <div v-if="loading" class="flex justify-center p-4">
              <div class="animate-spin rounded-full h-6 w-6 border-2 border-emerald-500 border-t-transparent"></div>
            </div>
            <p v-else-if="currentDirecciones.length === 0" class="text-center text-sm text-[#94A3B8] italic p-4">
              No hay Direcciones en esta VP.
            </p>
            <div 
              v-else
              v-for="dir in currentDirecciones" 
              :key="dir.id" 
              class="flex items-center justify-between p-3.5 rounded-xl bg-white border border-[#E2E8F0] shadow-xs hover:border-slate-300 transition-all"
            >
              <div class="min-w-0">
                <p class="font-semibold text-sm text-[#1E293B] truncate">{{ dir.name }}</p>
              </div>
              <div class="flex items-center gap-1 shrink-0 ml-2">
                <button 
                  @click="handleEditDir(dir)" 
                  class="p-1.5 text-[#94A3B8] hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors cursor-pointer"
                  title="Editar"
                >
                  <Edit2 class="w-4 h-4" />
                </button>
                <button 
                  @click="handleDeleteDir(dir.id)" 
                  class="p-1.5 text-[#94A3B8] hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
                  title="Eliminar"
                >
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
