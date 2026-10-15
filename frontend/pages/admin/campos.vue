<script setup lang="ts">
import { ref, onMounted } from 'vue';

const config = useRuntimeConfig();
const apiBase = config.public.apiBase;

interface FieldItem {
  id: string;
  label: string;
  key: string;
  field_type: 'text' | 'date' | 'select' | 'file';
  options: string[];
  is_visible: boolean;
  is_required: boolean;
  sort_order: number;
  help_text?: string;
  ai_instructions?: string;
  ask_in_initial_form: boolean;
}

const fields = ref<FieldItem[]>([]);
const loading = ref(false);
const saving = ref(false);

const showModal = ref(false);
const editingId = ref<string | null>(null);
const form = ref<Partial<FieldItem>>({
  label: '',
  key: '',
  field_type: 'text',
  options: [],
  is_visible: true,
  is_required: false,
  help_text: '',
  ai_instructions: '',
  ask_in_initial_form: false,
});
const rawOptions = ref('');

async function fetchFields() {
  loading.value = true;
  try {
    const res = await $fetch<FieldItem[]>(`${apiBase}/fields`).catch(() => []);
    fields.value = Array.isArray(res) ? res : [];
  } catch (err) {
    console.error('Error cargando campos:', err);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchFields();
});

function openCreate() {
  editingId.value = null;
  form.value = {
    label: '',
    key: '',
    field_type: 'text',
    options: [],
    is_visible: true,
    is_required: false,
    help_text: '',
    ai_instructions: '',
    ask_in_initial_form: false,
  };
  rawOptions.value = '';
  showModal.value = true;
}

function openEdit(item: FieldItem) {
  editingId.value = item.id;
  form.value = { ...item };
  rawOptions.value = Array.isArray(item.options) ? item.options.join(', ') : '';
  showModal.value = true;
}

async function handleSave() {
  if (!form.value.label?.trim() || !form.value.key?.trim()) return;
  saving.value = true;
  try {
    const opts = (form.value.field_type === 'select' || form.value.field_type === 'multiselect')
      ? rawOptions.value.split(',').map(s => s.trim()).filter(Boolean)
      : [];

    const payload = {
      ...form.value,
      options: opts,
      allow_multiple: Boolean(form.value.allow_multiple || form.value.field_type === 'multiselect'),
    };

    if (editingId.value) {
      await $fetch(`${apiBase}/fields/${editingId.value}`, { method: 'PUT', body: payload });
    } else {
      await $fetch(`${apiBase}/fields`, { method: 'POST', body: payload });
    }
    showModal.value = false;
    await fetchFields();
  } catch (err: any) {
    alert(err?.data?.detail || 'Error al guardar campo');
  } finally {
    saving.value = false;
  }
}

async function toggleVisibility(item: FieldItem) {
  try {
    await $fetch(`${apiBase}/fields/${item.id}`, {
      method: 'PUT',
      body: { is_visible: !item.is_visible }
    });
    item.is_visible = !item.is_visible;
  } catch (err) {
    alert('Error al actualizar visibilidad');
  }
}

async function handleDelete(id: string) {
  if (!confirm('¿Deseas eliminar este campo dinámico?')) return;
  try {
    await $fetch(`${apiBase}/fields/${id}`, { method: 'DELETE' });
    fields.value = fields.value.filter(f => f.id !== id);
  } catch (err) {
    alert('Error al eliminar campo');
  }
}

const typeBadges: Record<string, string> = {
  text: 'bg-blue-50 text-blue-700 border-blue-200',
  date: 'bg-amber-50 text-amber-700 border-amber-200',
  select: 'bg-purple-50 text-purple-700 border-purple-200',
  file: 'bg-emerald-50 text-emerald-700 border-emerald-200',
};
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center gap-2">
          <span class="p-2 rounded-xl bg-[#0D436C]/10 text-[#0D436C] font-bold text-lg">📋</span>
          <h1 class="text-2xl font-bold text-[#0D436C] tracking-tight">Campos de Iniciativas</h1>
        </div>
        <p class="text-sm text-slate-500 mt-1">
          Gobernanza de campos dinámicos para formularios, extracción de IA y reportes ejecutivos.
        </p>
      </div>

      <div class="flex gap-2">
        <button
          @click="fetchFields"
          class="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
        >
          <span>🔄</span> Recargar
        </button>
        <button
          @click="openCreate"
          class="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-[#EB5F46] hover:bg-[#d94f38] rounded-lg transition-colors shadow-sm"
        >
          <span>+</span> Nuevo Campo
        </button>
      </div>
    </div>

    <!-- Tabla de Campos -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <table class="w-full text-left text-xs">
        <thead class="bg-slate-50 text-slate-500 font-bold border-b border-slate-200">
          <tr>
            <th class="p-3.5">Etiqueta (Label)</th>
            <th class="p-3.5">Clave (Key)</th>
            <th class="p-3.5">Tipo</th>
            <th class="p-3.5">¿Obligatorio?</th>
            <th class="p-3.5">Paso Inicial</th>
            <th class="p-3.5">Estado</th>
            <th class="p-3.5 text-right">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="item in fields" :key="item.id" class="hover:bg-slate-50/80 transition-colors">
            <td class="p-3.5 font-bold text-[#0D436C]">{{ item.label }}</td>
            <td class="p-3.5 font-mono text-[11px] text-slate-500">{{ item.key }}</td>
            <td class="p-3.5">
              <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold border', typeBadges[item.field_type] || 'bg-slate-100']">
                {{ item.field_type }}
              </span>
            </td>
            <td class="p-3.5">
              <span :class="item.is_required ? 'text-red-600 font-bold' : 'text-slate-400'">
                {{ item.is_required ? 'Sí' : 'No' }}
              </span>
            </td>
            <td class="p-3.5">
              <span :class="item.ask_in_initial_form ? 'text-blue-600 font-semibold' : 'text-slate-400'">
                {{ item.ask_in_initial_form ? 'En formulario inicial' : 'Extraído por Teo' }}
              </span>
            </td>
            <td class="p-3.5">
              <button
                @click="toggleVisibility(item)"
                :class="[
                  'px-2 py-0.5 rounded-full text-[10px] font-bold transition-colors',
                  item.is_visible ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
                ]"
              >
                {{ item.is_visible ? 'Visible' : 'Oculto' }}
              </button>
            </td>
            <td class="p-3.5 text-right space-x-2">
              <button @click="openEdit(item)" class="text-slate-400 hover:text-[#0D436C]">✏️</button>
              <button @click="handleDelete(item.id)" class="text-slate-400 hover:text-red-600">🗑️</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal Formulario Campo -->
    <div v-if="showModal" class="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-xl">
        <h3 class="font-bold text-sm text-[#0D436C]">
          {{ editingId ? 'Editar Campo' : 'Nuevo Campo Dinámico' }}
        </h3>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-[11px] font-bold text-slate-700 mb-1">Etiqueta Visible</label>
            <input
              v-model="form.label"
              type="text"
              placeholder="Ej. Nivel de Urgencia"
              class="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0D436C]"
            />
          </div>
          <div>
            <label class="block text-[11px] font-bold text-slate-700 mb-1">Clave Única (key)</label>
            <input
              v-model="form.key"
              type="text"
              placeholder="Ej. nivel_urgencia"
              class="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0D436C]"
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-[11px] font-bold text-slate-700 mb-1">Tipo de Dato</label>
            <select
              v-model="form.field_type"
              @change="if (form.field_type === 'multiselect') form.allow_multiple = true; else if (form.field_type === 'select' && form.allow_multiple === undefined) form.allow_multiple = false;"
              class="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0D436C]"
            >
              <option value="text">Texto Libre</option>
              <option value="select">Selector (Dropdown)</option>
              <option value="multiselect">Selección Múltiple (Chips / Tags)</option>
              <option value="date">Fecha (DD/MM/AAAA)</option>
              <option value="file">Archivo Adjunto</option>
            </select>
          </div>
          <div class="flex items-center gap-3 pt-5 flex-wrap">
            <label class="flex items-center gap-1.5 text-xs font-semibold text-slate-700 cursor-pointer">
              <input type="checkbox" v-model="form.is_required" class="rounded text-[#0D436C]" />
              Obligatorio
            </label>
            <label class="flex items-center gap-1.5 text-xs font-semibold text-slate-700 cursor-pointer">
              <input type="checkbox" v-model="form.ask_in_initial_form" class="rounded text-[#0D436C]" />
              Form. Inicial
            </label>
            <label v-if="form.field_type === 'select' || form.field_type === 'multiselect'" class="flex items-center gap-1.5 text-xs font-bold text-indigo-700 cursor-pointer">
              <input
                type="checkbox"
                :checked="form.field_type === 'multiselect' || form.allow_multiple === true"
                @change="form.allow_multiple = ($event.target as HTMLInputElement).checked; form.field_type = form.allow_multiple ? 'multiselect' : 'select'"
                class="rounded text-indigo-600"
              />
              Multiselección
            </label>
          </div>
        </div>

        <div v-if="form.field_type === 'select' || form.field_type === 'multiselect'">
          <label class="block text-[11px] font-bold text-slate-700 mb-1">Opciones (separadas por coma)</label>
          <input
            v-model="rawOptions"
            type="text"
            placeholder="Alta, Media, Baja"
            class="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0D436C]"
          />
        </div>

        <div>
          <label class="block text-[11px] font-bold text-slate-700 mb-1">Instrucciones para Teo (IA)</label>
          <textarea
            v-model="form.ai_instructions"
            rows="2"
            placeholder="Cómo Teo debe deducir o cuestionar este campo..."
            class="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0D436C]"
          ></textarea>
        </div>

        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showModal = false" class="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg">Cancelar</button>
          <button @click="handleSave" :disabled="saving" class="px-4 py-1.5 text-xs font-bold text-white bg-[#0D436C] rounded-lg">Guardar</button>
        </div>
      </div>
    </div>
  </div>
</template>
