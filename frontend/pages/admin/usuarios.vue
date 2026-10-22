<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import {
  Users, Plus, Search, Trash2, Mail, Building, Shield, UserCog,
  Briefcase, Pencil, X, ChevronDown, Lock, Sparkles, Check,
  AlertTriangle, RefreshCw, Copy, UserCheck, Eye, Globe, Loader2
} from 'lucide-vue-next';

const config = useRuntimeConfig();
const apiBase = config.public.apiBase;

export interface AppRole {
  id: string;
  code: string;
  name: string;
  description: string | null;
  color: string;
  is_system: boolean;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
  user_count?: number;
}

export interface UserRoleWhitelist {
  id?: string;
  role: string;
  vp_id: string;
  direcciones_ids: string[];
  is_transversal?: boolean;
  vps?: { name: string };
}

export interface AllowedUser {
  id: string;
  email: string;
  name: string;
  created_at: string;
  is_active?: boolean;
  user_roles_whitelist?: UserRoleWhitelist[];
}

export interface VP {
  id: string;
  name: string;
}

export interface Direccion {
  id: string;
  name: string;
  vp_id: string;
}

const ROLE_COLORS: Record<string, { bg: string; text: string; border: string; dot: string; label: string; swatch: string }> = {
  indigo: { bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200', dot: 'bg-indigo-500', label: 'Índigo', swatch: '#6366F1' },
  blue: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', dot: 'bg-blue-500', label: 'Azul', swatch: '#3B82F6' },
  emerald: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', dot: 'bg-emerald-500', label: 'Esmeralda', swatch: '#10B981' },
  violet: { bg: 'bg-violet-50', text: 'text-violet-700', border: 'border-violet-200', dot: 'bg-violet-500', label: 'Violeta', swatch: '#8B5CF6' },
  amber: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', dot: 'bg-amber-500', label: 'Ámbar', swatch: '#F59E0B' },
  rose: { bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200', dot: 'bg-rose-500', label: 'Rosa', swatch: '#F43F5E' },
  cyan: { bg: 'bg-cyan-50', text: 'text-cyan-700', border: 'border-cyan-200', dot: 'bg-cyan-500', label: 'Cian', swatch: '#06B6D4' },
  slate: { bg: 'bg-slate-100', text: 'text-slate-700', border: 'border-slate-300', dot: 'bg-slate-500', label: 'Pizarra', swatch: '#64748B' },
  red: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', dot: 'bg-red-500', label: 'Rojo', swatch: '#EF4444' },
};

const toCleanSlug = (text: string): string => {
  if (!text) return '';
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[\s\/-]+/g, '_')
    .replace(/[^a-z0-9_]/g, '')
    .replace(/_+/g, '_');
};

// Tabs state
const activeTab = ref<'users' | 'roles'>('users');
const users = ref<AllowedUser[]>([]);
const vps = ref<VP[]>([]);
const direcciones = ref<Direccion[]>([]);
const loading = ref(true);

// Catálogo de Roles
const roles = ref<AppRole[]>([]);
const rolesLoading = ref(false);
const roleSearchQuery = ref('');
const roleModalOpen = ref(false);
const editingRole = ref<AppRole | null>(null);
const roleSaving = ref(false);
const roleForm = ref({
  code: '',
  name: '',
  description: '',
  color: 'indigo',
  is_active: true,
});
const roleFilterType = ref<'all' | 'system' | 'custom' | 'active'>('all');
const copiedSlug = ref<string | null>(null);

const handleCopySlug = (code: string) => {
  navigator.clipboard.writeText(code);
  copiedSlug.value = code;
  setTimeout(() => (copiedSlug.value = null), 1800);
};

// Filtros de usuarios
const searchQuery = ref('');
const selectedVPs = ref<string[]>([]);
const selectedDirs = ref<string[]>([]);
const selectedRoles = ref<string[]>([]);
const selectedActivation = ref<'all' | 'active' | 'pending'>('all');
const selectedConnection = ref<'all' | 'online' | 'offline'>('all');
const selectedTransversal = ref<'all' | 'transversal' | 'specific'>('all');

// Dropdowns de filtros
const vpDropdownOpen = ref(false);
const dirDropdownOpen = ref(false);
const roleDropdownOpen = ref(false);
const activationDropdownOpen = ref(false);
const connectionDropdownOpen = ref(false);
const transversalDropdownOpen = ref(false);

// Usuarios expandidos
const expandedUsers = ref<Record<string, boolean>>({});

// Correos conectados (online)
const onlineEmails = ref<Set<string>>(new Set(['admin@iacs.empresa.com']));

// Formulario manual de usuario
const newEmail = ref('');
const newName = ref('');
const assignments = ref<UserRoleWhitelist[]>([
  { role: 'registrador', vp_id: '', direcciones_ids: [], is_transversal: false }
]);
const editingId = ref<string | null>(null);
const saving = ref(false);

// Fetching inicial
async function fetchRoles() {
  rolesLoading.value = true;
  try {
    const res = await $fetch<AppRole[]>(`${apiBase}/admin/roles`);
    if (Array.isArray(res)) {
      roles.value = res;
    }
  } catch (err) {
    console.error('Error al cargar roles:', err);
  } finally {
    rolesLoading.value = false;
  }
}

async function fetchData() {
  loading.value = true;
  try {
    const [usersRes, vpsRes, dirRes] = await Promise.all([
      $fetch<AllowedUser[]>(`${apiBase}/admin/users`).catch(() => []),
      $fetch<VP[]>(`${apiBase}/admin/estructura/vps`).catch(() => []),
      $fetch<Direccion[]>(`${apiBase}/admin/estructura/direcciones`).catch(() => []),
    ]);
    users.value = Array.isArray(usersRes) ? usersRes : [];
    vps.value = Array.isArray(vpsRes) ? vpsRes : [];
    direcciones.value = Array.isArray(dirRes) ? dirRes : [];
  } catch (err) {
    console.error('Error al cargar datos:', err);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchData();
  fetchRoles();
});

// Roles Helpers
const activeRolesList = computed(() => {
  if (roles.value.length > 0) {
    return roles.value
      .filter(r => r.is_active || (editingId.value && assignments.value.some(a => a.role === r.code)))
      .map(r => ({ value: r.code, label: r.name }));
  }
  return [
    { value: 'registrador', label: 'Key user' },
    { value: 'bp_ti', label: 'Business Partner (BP)' },
    { value: 'entrenador_ia', label: 'Entrenador IA' },
    { value: 'invitado', label: 'Invitado (Solo lectura)' }
  ];
});

const roleFilterOptions = computed(() => {
  if (roles.value.length > 0) {
    return roles.value.map(r => ({ value: r.code, label: r.name }));
  }
  return [
    { value: 'registrador', label: 'Key user' },
    { value: 'bp_ti', label: 'Business Partner (BP)' },
    { value: 'entrenador_ia', label: 'Entrenador IA' },
    { value: 'invitado', label: 'Invitado (Solo lectura)' }
  ];
});

const filteredRolesCatalog = computed(() => {
  return roles.value.filter(r => {
    if (roleFilterType.value === 'system' && !r.is_system) return false;
    if (roleFilterType.value === 'custom' && r.is_system) return false;
    if (roleFilterType.value === 'active' && !r.is_active) return false;

    if (!roleSearchQuery.value.trim()) return true;
    const rawQ = roleSearchQuery.value.toLowerCase().trim();
    const cleanQ = toCleanSlug(roleSearchQuery.value);
    return (
      r.name.toLowerCase().includes(rawQ) ||
      r.code.toLowerCase().includes(rawQ) ||
      (r.description && r.description.toLowerCase().includes(rawQ)) ||
      toCleanSlug(r.name).includes(cleanQ) ||
      toCleanSlug(r.code).includes(cleanQ)
    );
  });
});

const filteredUsers = computed(() => {
  return users.value.filter(user => {
    if (searchQuery.value.trim() !== '') {
      const q = searchQuery.value.toLowerCase().trim();
      const matchesSearch = user.name.toLowerCase().includes(q) || user.email.toLowerCase().includes(q);
      if (!matchesSearch) return false;
    }

    const hasAssignments = user.user_roles_whitelist && user.user_roles_whitelist.length > 0;

    if (selectedVPs.value.length > 0) {
      if (!hasAssignments) return false;
      const matchesVP = user.user_roles_whitelist!.some(r => r.vp_id && selectedVPs.value.includes(r.vp_id));
      if (!matchesVP) return false;
    }

    if (selectedDirs.value.length > 0) {
      if (!hasAssignments) return false;
      const matchesDir = user.user_roles_whitelist!.some(r =>
        r.direcciones_ids && r.direcciones_ids.some(id => selectedDirs.value.includes(id))
      );
      if (!matchesDir) return false;
    }

    if (selectedRoles.value.length > 0) {
      if (!hasAssignments) return false;
      const matchesRole = user.user_roles_whitelist!.some(r => selectedRoles.value.includes(r.role));
      if (!matchesRole) return false;
    }

    if (selectedActivation.value !== 'all') {
      const isAct = !!user.is_active;
      if (selectedActivation.value === 'active' && !isAct) return false;
      if (selectedActivation.value === 'pending' && isAct) return false;
    }

    if (selectedConnection.value !== 'all') {
      const isOnline = onlineEmails.value.has(user.email.toLowerCase().trim());
      if (selectedConnection.value === 'online' && !isOnline) return false;
      if (selectedConnection.value === 'offline' && isOnline) return false;
    }

    if (selectedTransversal.value !== 'all') {
      const hasTrans = user.user_roles_whitelist?.some(
        r => !!r.is_transversal || r.role === 'admin' || r.role === 'entrenador_ia'
      );
      if (selectedTransversal.value === 'transversal' && !hasTrans) return false;
      if (selectedTransversal.value === 'specific' && (!hasAssignments || hasTrans)) return false;
    }

    return true;
  });
});

// User Form Actions
const handleAddAssignment = () => {
  assignments.value.push({ role: 'registrador', vp_id: '', direcciones_ids: [], is_transversal: false });
};

const handleRemoveAssignment = (index: number) => {
  assignments.value.splice(index, 1);
};

const updateAssignment = (index: number, field: keyof UserRoleWhitelist, value: any) => {
  const assig = assignments.value[index];
  if (!assig) return;
  (assig as any)[field] = value;

  if (field === 'role' && (value === 'admin' || value === 'entrenador_ia')) {
    assig.is_transversal = true;
    assig.vp_id = '';
    assig.direcciones_ids = [];
  }
  if (field === 'vp_id') {
    assig.direcciones_ids = [];
  }
  if (field === 'is_transversal' && value === true) {
    assig.vp_id = '';
    assig.direcciones_ids = [];
  }
};

const handleSaveUser = async () => {
  if (!newEmail.value || !newName.value || assignments.value.length === 0) return;

  if (
    assignments.value.some(
      a =>
        !a.role ||
        (!a.is_transversal &&
          a.role !== 'admin' &&
          a.role !== 'entrenador_ia' &&
          (!a.vp_id || a.direcciones_ids.length === 0))
    )
  ) {
    alert('Por favor completa la VP y Dirección(es) en cada asignación, o activa "Alcance Transversal".');
    return;
  }

  saving.value = true;
  try {
    const saveRes: any = await $fetch(`${apiBase}/admin/users`, {
      method: 'POST',
      body: {
        id: editingId.value,
        name: newName.value.trim(),
        email: newEmail.value.trim(),
        assignments: assignments.value.map(a => ({
          role: a.role,
          vp_id: a.is_transversal ? null : a.vp_id,
          direcciones_ids: a.is_transversal ? [] : a.direcciones_ids,
          is_transversal: !!a.is_transversal || a.role === 'admin' || a.role === 'entrenador_ia'
        }))
      }
    });

    await fetchData();
    await fetchRoles();

    if (process.client) {
      const savedUserStr = localStorage.getItem('iacs_user');
      if (savedUserStr) {
        try {
          const currentLoggedUser = JSON.parse(savedUserStr);
          if (
            currentLoggedUser.email?.toLowerCase() === newEmail.value.trim().toLowerCase() &&
            saveRes?.user
          ) {
            localStorage.setItem('iacs_user', JSON.stringify({
              ...currentLoggedUser,
              ...saveRes.user
            }));
          }
        } catch (e) {}
      }
      window.dispatchEvent(new CustomEvent('iacs_user_updated', {
        detail: { email: newEmail.value.trim(), user: saveRes?.user }
      }));
    }

    newEmail.value = '';
    newName.value = '';
    assignments.value = [{ role: 'registrador', vp_id: '', direcciones_ids: [], is_transversal: false }];
    editingId.value = null;
  } catch (err: any) {
    alert('Error al guardar: ' + (err.data?.detail || err.message || 'Error desconocido'));
  } finally {
    saving.value = false;
  }
};

const handleEdit = (user: AllowedUser) => {
  editingId.value = user.id;
  newEmail.value = user.email;
  newName.value = user.name;
  assignments.value = user.user_roles_whitelist?.length
    ? user.user_roles_whitelist.map(r => ({
        role: r.role,
        vp_id: r.vp_id || '',
        direcciones_ids: r.direcciones_ids || [],
        is_transversal: !!r.is_transversal || r.role === 'admin' || r.role === 'entrenador_ia'
      }))
    : [{ role: 'registrador', vp_id: '', direcciones_ids: [], is_transversal: false }];
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

const handleDelete = async (id: string) => {
  if (!confirm('¿Seguro que deseas eliminar este acceso completamente?')) return;
  try {
    await $fetch(`${apiBase}/admin/users/${id}`, { method: 'DELETE' });
    users.value = users.value.filter(u => u.id !== id);
    await fetchRoles();
  } catch (err: any) {
    alert('Error al eliminar: ' + (err.data?.detail || err.message));
  }
};

// Role Modal Actions
const handleOpenCreateRole = () => {
  editingRole.value = null;
  roleForm.value = {
    code: '',
    name: '',
    description: '',
    color: 'indigo',
    is_active: true,
  };
  roleModalOpen.value = true;
};

const handleOpenEditRole = (role: AppRole) => {
  editingRole.value = role;
  roleForm.value = {
    code: role.code,
    name: role.name,
    description: role.description || '',
    color: role.color || 'indigo',
    is_active: role.is_active,
  };
  roleModalOpen.value = true;
};

const handleSaveRole = async () => {
  const cleanCode = toCleanSlug(roleForm.value.code).replace(/^_+|_+$/g, '');
  const cleanName = roleForm.value.name.trim();

  if (!cleanName || (!editingRole.value && !cleanCode)) {
    alert('Por favor completa el nombre y el código técnico del rol.');
    return;
  }

  roleSaving.value = true;
  try {
    if (editingRole.value) {
      await $fetch(`${apiBase}/admin/roles/${editingRole.value.id}`, {
        method: 'PUT',
        body: {
          name: cleanName,
          description: roleForm.value.description.trim() || null,
          color: roleForm.value.color,
          is_active: roleForm.value.is_active,
        }
      });
    } else {
      await $fetch(`${apiBase}/admin/roles`, {
        method: 'POST',
        body: {
          code: cleanCode,
          name: cleanName,
          description: roleForm.value.description.trim() || null,
          color: roleForm.value.color,
          is_active: roleForm.value.is_active,
        }
      });
    }
    await fetchRoles();
    roleModalOpen.value = false;
    editingRole.value = null;
  } catch (err: any) {
    alert('Error: ' + (err.data?.detail || err.message || 'No se pudo guardar el rol.'));
  } finally {
    roleSaving.value = false;
  }
};

const handleDeleteRole = async (role: AppRole) => {
  if (role.is_system) {
    alert('Los roles base del sistema están protegidos y no pueden ser eliminados.');
    return;
  }
  if ((role.user_count || 0) > 0) {
    alert(`No es posible eliminar el rol "${role.name}" porque tiene ${role.user_count} usuario(s) asignado(s). Reasigna a los usuarios antes de eliminarlo.`);
    return;
  }
  if (!confirm(`¿Confirmas la eliminación permanente del rol "${role.name}" (${role.code})? Esta acción no se puede deshacer.`)) {
    return;
  }

  try {
    await $fetch(`${apiBase}/admin/roles/${role.id}`, { method: 'DELETE' });
    await fetchRoles();
  } catch (err: any) {
    alert('Error al eliminar rol: ' + (err.data?.detail || err.message));
  }
};

const handleToggleRoleStatus = async (role: AppRole) => {
  if (role.code === 'admin' && role.is_active) {
    alert('El rol Administrador debe permanecer siempre activo.');
    return;
  }

  const nextState = !role.is_active;
  try {
    await $fetch(`${apiBase}/admin/roles/${role.id}`, {
      method: 'PUT',
      body: { is_active: nextState }
    });
    await fetchRoles();
  } catch (err: any) {
    alert('Error al cambiar estado del rol: ' + (err.data?.detail || err.message));
  }
};

const getRoleBadgeClasses = (roleCode: string) => {
  const found = roles.value.find(r => r.code === roleCode);
  if (found && ROLE_COLORS[found.color]) {
    const c = ROLE_COLORS[found.color];
    return { bg: c.bg, text: c.text, border: c.border, dot: c.dot, name: found.name };
  }
  switch (roleCode) {
    case 'admin':
      return { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-200', dot: 'bg-red-500', name: 'ADMIN' };
    case 'bp_ti':
      return { bg: 'bg-indigo-100', text: 'text-indigo-700', border: 'border-indigo-200', dot: 'bg-indigo-500', name: 'BP TI' };
    case 'invitado':
      return { bg: 'bg-slate-100', text: 'text-slate-600', border: 'border-slate-200', dot: 'bg-slate-500', name: 'INVITADO' };
    default:
      return { bg: 'bg-emerald-100', text: 'text-emerald-700', border: 'border-emerald-200', dot: 'bg-emerald-500', name: roleCode.toUpperCase() };
  }
};

const getRoleIconComponent = (code: string, isSystem: boolean) => {
  switch (code) {
    case 'admin':
      return { icon: Shield, class: 'text-red-600' };
    case 'bp_ti':
      return { icon: Briefcase, class: 'text-indigo-600' };
    case 'registrador':
      return { icon: UserCheck, class: 'text-emerald-600' };
    case 'invitado':
      return { icon: Eye, class: 'text-slate-600' };
    default:
      return isSystem ? { icon: Lock, class: 'text-slate-600' } : { icon: Sparkles, class: 'text-violet-600' };
  }
};
</script>

<template>
  <div class="space-y-6">
    <!-- Header Principal -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-2xl shadow-xs border border-[#E2E8F0]">
      <div>
        <h1 class="text-2xl font-bold text-[#1E293B] flex items-center gap-3">
          <Users class="w-7 h-7 text-[#4F5AF5]" />
          Gestión de Accesos y Roles Multi-Asignación
        </h1>
        <p class="text-[#64748B] mt-1 text-sm">
          Un usuario puede tener diferentes roles dependiendo de la Vicepresidencia y Dirección.
        </p>
      </div>
    </div>

    <!-- Sub-tabs de Navegación -->
    <div class="bg-white p-2.5 rounded-2xl shadow-2xs border border-[#E2E8F0] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div class="flex bg-slate-100 p-1 rounded-xl gap-1">
        <button
          type="button"
          @click="activeTab = 'users'"
          :class="[
            'px-4 py-2 text-xs font-bold rounded-lg transition-all flex items-center gap-2 cursor-pointer',
            activeTab === 'users'
              ? 'bg-white text-slate-800 shadow-2xs ring-1 ring-slate-200/60'
              : 'text-slate-500 hover:text-slate-800'
          ]"
        >
          <Users class="w-4 h-4 text-[#4F5AF5]" />
          <span>Usuarios y Accesos</span>
          <span
            :class="[
              'px-2 py-0.5 rounded-full text-[10px] font-bold',
              activeTab === 'users' ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-200 text-slate-600'
            ]"
          >
            {{ users.length }}
          </span>
        </button>

        <button
          type="button"
          @click="activeTab = 'roles'"
          :class="[
            'px-4 py-2 text-xs font-bold rounded-lg transition-all flex items-center gap-2 cursor-pointer',
            activeTab === 'roles'
              ? 'bg-white text-slate-800 shadow-2xs ring-1 ring-slate-200/60'
              : 'text-slate-500 hover:text-slate-800'
          ]"
        >
          <Shield class="w-4 h-4 text-indigo-600" />
          <span>Catálogo de Roles</span>
          <span
            :class="[
              'px-2 py-0.5 rounded-full text-[10px] font-bold',
              activeTab === 'roles' ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-200 text-slate-600'
            ]"
          >
            {{ roles.length }}
          </span>
        </button>
      </div>

      <div v-if="activeTab === 'roles'">
        <button
          type="button"
          @click="handleOpenCreateRole"
          class="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-[#4F5AF5] to-[#6366F1] hover:from-[#3D47E0] hover:to-[#4F5AF5] text-white text-xs font-bold rounded-xl shadow-xs hover:shadow-md transition-all cursor-pointer transform active:scale-95 shrink-0"
        >
          <Plus class="w-4 h-4" />
          <span>Crear Nuevo Rol</span>
        </button>
      </div>
    </div>

    <!-- PESTAÑA 1: USUARIOS Y ACCESOS -->
    <div v-if="activeTab === 'users'" class="space-y-6">
      <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <!-- Columna Izquierda: Formulario Manual -->
        <div class="space-y-6 xl:col-span-1">
          <div class="bg-white p-6 rounded-2xl shadow-xs border border-[#E2E8F0]">
            <h2 class="text-lg font-bold text-[#1E293B] mb-4 flex items-center gap-2">
              <component :is="editingId ? Pencil : Plus" class="w-5 h-5 text-[#4F5AF5]" />
              {{ editingId ? 'Editar Usuario' : 'Agregar Usuario (Manual)' }}
            </h2>
            <form @submit.prevent="handleSaveUser" class="space-y-4">
              <div>
                <label class="block text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-1">
                  Nombre Completo
                </label>
                <input
                  required
                  v-model="newName"
                  class="w-full px-3 py-2 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl text-sm outline-none focus:border-[#4F5AF5] focus:bg-white transition-colors"
                  placeholder="Ej: Maria Lopez"
                />
              </div>

              <div>
                <label class="block text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-1">
                  Correo Electrónico
                </label>
                <input
                  required
                  type="email"
                  v-model="newEmail"
                  :disabled="!!editingId"
                  :class="[
                    'w-full px-3 py-2 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl text-sm outline-none focus:border-[#4F5AF5] focus:bg-white transition-colors',
                    editingId ? 'opacity-50 cursor-not-allowed' : ''
                  ]"
                  placeholder="maria@empresa.com"
                />
              </div>

              <div class="border-t border-[#E2E8F0] pt-4 mt-2">
                <div class="flex items-center justify-between mb-3">
                  <h3 class="text-sm font-bold text-[#1E293B]">Asignaciones de Rol</h3>
                  <button
                    type="button"
                    @click="handleAddAssignment"
                    class="text-xs font-bold text-[#4F5AF5] hover:underline flex items-center gap-1 cursor-pointer"
                  >
                    <Plus class="w-3 h-3" /> Añadir Bloque
                  </button>
                </div>

                <div class="space-y-4 max-h-[400px] overflow-y-auto pr-1">
                  <div
                    v-for="(assig, index) in assignments"
                    :key="index"
                    class="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl relative"
                  >
                    <button
                      v-if="assignments.length > 1"
                      type="button"
                      @click="handleRemoveAssignment(index)"
                      class="absolute top-2 right-2 text-[#94A3B8] hover:text-red-500 cursor-pointer"
                    >
                      <X class="w-4 h-4" />
                    </button>

                    <div class="space-y-3">
                      <div>
                        <label class="block text-[10px] font-semibold text-[#64748B] uppercase tracking-wider mb-1">
                          Rol
                        </label>
                        <select
                          required
                          :value="assig.role"
                          @change="(e: any) => updateAssignment(index, 'role', e.target.value)"
                          class="w-full px-2 py-2 bg-white border border-[#E2E8F0] rounded-xl text-xs outline-none focus:border-[#4F5AF5]"
                        >
                          <option v-for="r in activeRolesList" :key="r.value" :value="r.value">
                            {{ r.label }}
                          </option>
                        </select>
                      </div>

                      <!-- Opción Alcance Transversal -->
                      <div>
                        <div
                          @click="() => {
                            if (assig.role === 'admin' || assig.role === 'entrenador_ia') return;
                            updateAssignment(index, 'is_transversal', !assig.is_transversal);
                          }"
                          :class="[
                            'p-2.5 rounded-xl border transition-all select-none',
                            (assig.role === 'admin' || assig.role === 'entrenador_ia') ? 'cursor-default' : 'cursor-pointer',
                            (assig.is_transversal || assig.role === 'admin' || assig.role === 'entrenador_ia')
                              ? 'bg-indigo-50/90 border-indigo-300 ring-2 ring-indigo-500/10'
                              : 'bg-white border-[#E2E8F0] hover:border-indigo-200'
                          ]"
                        >
                          <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2.5">
                              <div
                                :class="[
                                  'w-7 h-7 rounded-lg flex items-center justify-center transition-colors shrink-0',
                                  (assig.is_transversal || assig.role === 'admin' || assig.role === 'entrenador_ia')
                                    ? 'bg-indigo-600 text-white'
                                    : 'bg-slate-100 text-slate-500'
                                ]"
                              >
                                <Globe class="w-4 h-4" />
                              </div>
                              <div>
                                <div class="flex items-center gap-1.5">
                                  <span class="text-xs font-bold text-[#1E293B]">Alcance Transversal</span>
                                  <span
                                    v-if="assig.is_transversal || assig.role === 'admin' || assig.role === 'entrenador_ia'"
                                    class="text-[9px] font-bold bg-indigo-100 text-indigo-700 px-1.5 py-0.2 rounded-full"
                                  >
                                    Global
                                  </span>
                                </div>
                                <span class="text-[10px] text-[#64748B] block">
                                  {{
                                    (assig.role === 'admin' || assig.role === 'entrenador_ia')
                                      ? 'El Administrador General opera siempre a nivel global en todo el sistema'
                                      : 'Aplica a todas las Vicepresidencias y Direcciones'
                                  }}
                                </span>
                              </div>
                            </div>
                            <input
                              type="checkbox"
                              :disabled="assig.role === 'admin' || assig.role === 'entrenador_ia'"
                              :checked="!!assig.is_transversal || assig.role === 'admin' || assig.role === 'entrenador_ia'"
                              @click.stop
                              @change="(e: any) => updateAssignment(index, 'is_transversal', e.target.checked)"
                              class="w-4 h-4 rounded border-[#CBD5E1] text-[#4F5AF5] focus:ring-[#4F5AF5] cursor-pointer"
                            />
                          </div>
                        </div>

                        <!-- Panel de Alcance Transversal Activo -->
                        <div
                          v-if="assig.is_transversal || assig.role === 'admin' || assig.role === 'entrenador_ia'"
                          class="mt-2.5 p-2.5 bg-indigo-50/60 border border-indigo-100 rounded-xl text-[11px] text-indigo-900 flex items-start gap-2"
                        >
                          <Sparkles class="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                          <span class="leading-snug">
                            <template v-if="assig.role === 'admin'">
                              El <strong>Administrador General</strong> cuenta con acceso irrestricto y facultades plenas sobre todas las iniciativas y áreas del sistema.
                            </template>
                            <template v-else-if="assig.role === 'entrenador_ia'">
                              El <strong>Entrenador IA</strong> cuenta con acceso transversal para gobernar las bases de conocimiento y parámetros de Teo.
                            </template>
                            <template v-else>
                              Permisos globales activos. Este usuario tendrá facultades para este rol sobre <strong>todas las iniciativas de la empresa</strong> sin restricción de dirección.
                            </template>
                          </span>
                        </div>

                        <!-- Selector VP y Direcciones si no es transversal -->
                        <div v-else class="space-y-3 mt-3">
                          <div>
                            <label class="block text-[10px] font-semibold text-[#64748B] uppercase tracking-wider mb-1">
                              Vicepresidencia
                            </label>
                            <select
                              required
                              :value="assig.vp_id"
                              @change="(e: any) => updateAssignment(index, 'vp_id', e.target.value)"
                              class="w-full px-2 py-2 bg-white border border-[#E2E8F0] rounded-xl text-xs outline-none focus:border-[#4F5AF5]"
                            >
                              <option value="">Selecciona VP</option>
                              <option v-for="vp in vps" :key="vp.id" :value="vp.id">{{ vp.name }}</option>
                            </select>
                          </div>

                          <div>
                            <div class="flex items-center justify-between mb-1">
                              <label class="block text-[10px] font-semibold text-[#64748B] uppercase tracking-wider">
                                Dirección(es)
                              </label>
                              <button
                                v-if="assig.vp_id && direcciones.filter(d => d.vp_id === assig.vp_id).length > 0"
                                type="button"
                                @click="() => {
                                  const avDirs = direcciones.filter(d => d.vp_id === assig.vp_id);
                                  if (assig.direcciones_ids.length === avDirs.length) {
                                    updateAssignment(index, 'direcciones_ids', []);
                                  } else {
                                    updateAssignment(index, 'direcciones_ids', avDirs.map(d => d.id));
                                  }
                                }"
                                class="text-[10px] text-[#4F5AF5] font-bold hover:underline cursor-pointer"
                              >
                                {{
                                  assig.direcciones_ids.length === direcciones.filter(d => d.vp_id === assig.vp_id).length
                                    ? 'Desmarcar'
                                    : 'Marcar todas'
                                }}
                              </button>
                            </div>

                            <div
                              :class="[
                                'w-full px-2 py-2 bg-white border border-[#E2E8F0] rounded-xl text-xs max-h-32 overflow-y-auto',
                                !assig.vp_id ? 'opacity-50 pointer-events-none' : ''
                              ]"
                            >
                              <p v-if="!assig.vp_id" class="text-slate-400 p-1">Selecciona VP</p>
                              <div v-else class="space-y-2 py-1">
                                <label
                                  v-for="dir in direcciones.filter(d => d.vp_id === assig.vp_id)"
                                  :key="dir.id"
                                  class="flex items-start gap-2 cursor-pointer group"
                                >
                                  <input
                                    type="checkbox"
                                    :checked="assig.direcciones_ids.includes(dir.id)"
                                    @change="(e: any) => {
                                      if (e.target.checked) {
                                        updateAssignment(index, 'direcciones_ids', [...assig.direcciones_ids, dir.id]);
                                      } else {
                                        updateAssignment(index, 'direcciones_ids', assig.direcciones_ids.filter(id => id !== dir.id));
                                      }
                                    }"
                                    class="mt-0.5 rounded border-[#CBD5E1] text-[#4F5AF5] focus:ring-[#4F5AF5]"
                                  />
                                  <span class="text-[#1E293B] group-hover:text-[#4F5AF5] transition-colors">
                                    {{ dir.name }}
                                  </span>
                                </label>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="flex gap-2 mt-4 pt-2 border-t border-[#E2E8F0]">
                <button
                  v-if="editingId"
                  type="button"
                  @click="() => {
                    editingId = null;
                    newEmail = '';
                    newName = '';
                    assignments = [{ role: 'registrador', vp_id: '', direcciones_ids: [] }];
                  }"
                  class="flex-1 bg-white border border-[#E2E8F0] hover:bg-[#F8FAFC] text-[#64748B] font-bold py-2 rounded-xl text-sm transition-colors cursor-pointer"
                >
                  Cancelar
                </button>
                <button
                  :disabled="saving"
                  type="submit"
                  class="flex-2 bg-[#4F5AF5] hover:bg-[#3F49E0] disabled:opacity-50 text-white font-bold py-2 rounded-xl text-sm transition-colors cursor-pointer"
                >
                  {{ saving ? 'Guardando...' : (editingId ? 'Actualizar Usuario' : 'Guardar Usuario') }}
                </button>
              </div>
            </form>
          </div>
        </div>

        <!-- Columna Derecha: Tabla de Usuarios de Lista Blanca -->
        <div class="xl:col-span-2 bg-white rounded-2xl shadow-xs border border-[#E2E8F0] overflow-hidden flex flex-col h-[800px]">
          <div class="p-6 border-b border-[#E2E8F0] flex flex-col md:flex-row gap-4 justify-between items-start md:items-center bg-[#F8FAFC]">
            <h2 class="text-lg font-bold text-[#1E293B] flex items-center gap-2">
              <Shield class="w-5 h-5 text-[#64748B]" /> Lista Blanca Activa
            </h2>
            <div class="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center w-full md:w-auto">
              <div class="relative flex-1 sm:w-60">
                <Search class="w-4 h-4 text-[#94A3B8] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  v-model="searchQuery"
                  placeholder="Buscar usuario o correo..."
                  class="w-full pl-9 pr-4 py-1.5 bg-white border border-[#E2E8F0] rounded-xl text-xs outline-none focus:border-[#4F5AF5]"
                />
              </div>

              <button
                v-if="selectedVPs.length > 0 || selectedDirs.length > 0 || selectedRoles.length > 0 || selectedActivation !== 'all' || selectedConnection !== 'all' || selectedTransversal !== 'all' || searchQuery !== ''"
                @click="() => {
                  selectedVPs = [];
                  selectedDirs = [];
                  selectedRoles = [];
                  selectedActivation = 'all';
                  selectedConnection = 'all';
                  selectedTransversal = 'all';
                  searchQuery = '';
                }"
                class="text-xs font-bold text-red-500 hover:text-red-700 transition-colors shrink-0 text-center cursor-pointer"
              >
                Limpiar filtros
              </button>
            </div>
          </div>

          <!-- Filtros Multiselectores -->
          <div class="px-6 py-3 border-b border-[#E2E8F0] bg-white flex flex-wrap gap-2 relative z-30">
            <!-- Dropdown VP -->
            <div class="relative">
              <button
                type="button"
                @click="() => {
                  vpDropdownOpen = !vpDropdownOpen;
                  dirDropdownOpen = false;
                  roleDropdownOpen = false;
                  transversalDropdownOpen = false;
                  activationDropdownOpen = false;
                  connectionDropdownOpen = false;
                }"
                :class="[
                  'px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer',
                  selectedVPs.length > 0 ? 'bg-violet-50 border-violet-200 text-violet-700' : 'bg-white border-[#E2E8F0] text-[#64748B]'
                ]"
              >
                <span>VP {{ selectedVPs.length > 0 ? `(${selectedVPs.length})` : '' }}</span>
                <ChevronDown class="w-3.5 h-3.5" />
              </button>
              <div v-if="vpDropdownOpen">
                <div class="fixed inset-0 z-40" @click="vpDropdownOpen = false" />
                <div class="absolute left-0 mt-1 w-56 bg-white border border-[#E2E8F0] rounded-xl shadow-lg z-50 p-2.5 max-h-60 overflow-y-auto">
                  <div class="space-y-1.5">
                    <p v-if="vps.length === 0" class="text-[10px] text-slate-400 italic">No hay VPs</p>
                    <label
                      v-for="vp in vps"
                      :key="vp.id"
                      class="flex items-center gap-2 cursor-pointer p-1 rounded hover:bg-slate-50 text-xs text-[#1E293B]"
                    >
                      <input
                        type="checkbox"
                        :checked="selectedVPs.includes(vp.id)"
                        @change="(e: any) => {
                          if (e.target.checked) selectedVPs.push(vp.id);
                          else selectedVPs = selectedVPs.filter(id => id !== vp.id);
                        }"
                        class="rounded border-[#CBD5E1] text-[#4F5AF5] focus:ring-[#4F5AF5] w-3.5 h-3.5"
                      />
                      <span>{{ vp.name }}</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <!-- Dropdown Dirección -->
            <div class="relative">
              <button
                type="button"
                @click="() => {
                  dirDropdownOpen = !dirDropdownOpen;
                  vpDropdownOpen = false;
                  roleDropdownOpen = false;
                  transversalDropdownOpen = false;
                  activationDropdownOpen = false;
                  connectionDropdownOpen = false;
                }"
                :class="[
                  'px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer',
                  selectedDirs.length > 0 ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'bg-white border-[#E2E8F0] text-[#64748B]'
                ]"
              >
                <span>Dirección {{ selectedDirs.length > 0 ? `(${selectedDirs.length})` : '' }}</span>
                <ChevronDown class="w-3.5 h-3.5" />
              </button>
              <div v-if="dirDropdownOpen">
                <div class="fixed inset-0 z-40" @click="dirDropdownOpen = false" />
                <div class="absolute left-0 mt-1 w-64 bg-white border border-[#E2E8F0] rounded-xl shadow-lg z-50 p-2.5 max-h-60 overflow-y-auto">
                  <div class="space-y-1.5">
                    <p
                      v-if="direcciones.filter(d => selectedVPs.length === 0 || selectedVPs.includes(d.vp_id)).length === 0"
                      class="text-[10px] text-slate-400 italic"
                    >
                      No hay direcciones disponibles
                    </p>
                    <label
                      v-for="dir in direcciones.filter(d => selectedVPs.length === 0 || selectedVPs.includes(d.vp_id))"
                      :key="dir.id"
                      class="flex items-start gap-2 cursor-pointer p-1 rounded hover:bg-slate-50 text-xs text-[#1E293B]"
                    >
                      <input
                        type="checkbox"
                        :checked="selectedDirs.includes(dir.id)"
                        @change="(e: any) => {
                          if (e.target.checked) selectedDirs.push(dir.id);
                          else selectedDirs = selectedDirs.filter(id => id !== dir.id);
                        }"
                        class="rounded border-[#CBD5E1] text-[#4F5AF5] focus:ring-[#4F5AF5] w-3.5 h-3.5 mt-0.5"
                      />
                      <div class="flex flex-col">
                        <span>{{ dir.name }}</span>
                        <span v-if="selectedVPs.length === 0" class="text-[9px] text-[#94A3B8] font-semibold">
                          {{ vps.find(v => v.id === dir.vp_id)?.name || '' }}
                        </span>
                      </div>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <!-- Dropdown Rol -->
            <div class="relative">
              <button
                type="button"
                @click="() => {
                  roleDropdownOpen = !roleDropdownOpen;
                  vpDropdownOpen = false;
                  dirDropdownOpen = false;
                  transversalDropdownOpen = false;
                  activationDropdownOpen = false;
                  connectionDropdownOpen = false;
                }"
                :class="[
                  'px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer',
                  selectedRoles.length > 0 ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : 'bg-white border-[#E2E8F0] text-[#64748B]'
                ]"
              >
                <span>Rol {{ selectedRoles.length > 0 ? `(${selectedRoles.length})` : '' }}</span>
                <ChevronDown class="w-3.5 h-3.5" />
              </button>
              <div v-if="roleDropdownOpen">
                <div class="fixed inset-0 z-40" @click="roleDropdownOpen = false" />
                <div class="absolute left-0 mt-1 w-56 bg-white border border-[#E2E8F0] rounded-xl shadow-lg z-50 p-2.5 max-h-60 overflow-y-auto">
                  <div class="space-y-1.5">
                    <label
                      v-for="r in roleFilterOptions"
                      :key="r.value"
                      class="flex items-center gap-2 cursor-pointer p-1 rounded hover:bg-slate-50 text-xs text-[#1E293B]"
                    >
                      <input
                        type="checkbox"
                        :checked="selectedRoles.includes(r.value)"
                        @change="(e: any) => {
                          if (e.target.checked) selectedRoles.push(r.value);
                          else selectedRoles = selectedRoles.filter(val => val !== r.value);
                        }"
                        class="rounded border-[#CBD5E1] text-[#4F5AF5] focus:ring-[#4F5AF5] w-3.5 h-3.5"
                      />
                      <span>{{ r.label }}</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <!-- Dropdown Alcance Transversal -->
            <div class="relative">
              <button
                type="button"
                @click="() => {
                  transversalDropdownOpen = !transversalDropdownOpen;
                  vpDropdownOpen = false;
                  dirDropdownOpen = false;
                  roleDropdownOpen = false;
                  activationDropdownOpen = false;
                  connectionDropdownOpen = false;
                }"
                :class="[
                  'px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer',
                  selectedTransversal !== 'all' ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : 'bg-white border-[#E2E8F0] text-[#64748B]'
                ]"
              >
                <Globe class="w-3.5 h-3.5 text-indigo-500" />
                <span>
                  Alcance:
                  {{ selectedTransversal === 'all' ? 'Todos' : selectedTransversal === 'transversal' ? 'Transversal' : 'Específico' }}
                </span>
                <ChevronDown class="w-3.5 h-3.5" />
              </button>
              <div v-if="transversalDropdownOpen">
                <div class="fixed inset-0 z-40" @click="transversalDropdownOpen = false" />
                <div class="absolute left-0 mt-1 w-56 bg-white border border-[#E2E8F0] rounded-xl shadow-lg z-50 p-2">
                  <div class="space-y-1">
                    <button
                      type="button"
                      @click="() => { selectedTransversal = 'all'; transversalDropdownOpen = false; }"
                      :class="[
                        'w-full text-left px-2.5 py-1.5 rounded text-xs transition-colors hover:bg-slate-50 cursor-pointer',
                        selectedTransversal === 'all' ? 'font-bold text-[#4F5AF5]' : 'text-[#1E293B]'
                      ]"
                    >
                      Todos los alcances
                    </button>
                    <button
                      type="button"
                      @click="() => { selectedTransversal = 'transversal'; transversalDropdownOpen = false; }"
                      :class="[
                        'w-full text-left px-2.5 py-1.5 rounded text-xs transition-colors hover:bg-slate-50 flex items-center gap-2 cursor-pointer',
                        selectedTransversal === 'transversal' ? 'font-bold text-[#4F5AF5]' : 'text-[#1E293B]'
                      ]"
                    >
                      <Globe class="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                      <span>Alcance Transversal (Global)</span>
                    </button>
                    <button
                      type="button"
                      @click="() => { selectedTransversal = 'specific'; transversalDropdownOpen = false; }"
                      :class="[
                        'w-full text-left px-2.5 py-1.5 rounded text-xs transition-colors hover:bg-slate-50 flex items-center gap-2 cursor-pointer',
                        selectedTransversal === 'specific' ? 'font-bold text-[#4F5AF5]' : 'text-[#1E293B]'
                      ]"
                    >
                      <Building class="w-3.5 h-3.5 text-slate-500 shrink-0" />
                      <span>Específico (Por Dirección)</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Dropdown Activación -->
            <div class="relative">
              <button
                type="button"
                @click="() => {
                  activationDropdownOpen = !activationDropdownOpen;
                  vpDropdownOpen = false;
                  dirDropdownOpen = false;
                  roleDropdownOpen = false;
                  transversalDropdownOpen = false;
                  connectionDropdownOpen = false;
                }"
                :class="[
                  'px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer',
                  selectedActivation !== 'all' ? 'bg-amber-50 border-amber-200 text-amber-700' : 'bg-white border-[#E2E8F0] text-[#64748B]'
                ]"
              >
                <span>Activación: {{ selectedActivation === 'all' ? 'Todos' : selectedActivation === 'active' ? 'Activos' : 'Pendientes' }}</span>
                <ChevronDown class="w-3.5 h-3.5" />
              </button>
              <div v-if="activationDropdownOpen">
                <div class="fixed inset-0 z-40" @click="activationDropdownOpen = false" />
                <div class="absolute left-0 mt-1 w-48 bg-white border border-[#E2E8F0] rounded-xl shadow-lg z-50 p-2">
                  <div class="space-y-1">
                    <button
                      type="button"
                      @click="() => { selectedActivation = 'all'; activationDropdownOpen = false; }"
                      :class="[
                        'w-full text-left px-2.5 py-1.5 rounded text-xs transition-colors hover:bg-slate-50 cursor-pointer',
                        selectedActivation === 'all' ? 'font-bold text-[#4F5AF5]' : 'text-[#1E293B]'
                      ]"
                    >
                      Todos
                    </button>
                    <button
                      type="button"
                      @click="() => { selectedActivation = 'active'; activationDropdownOpen = false; }"
                      :class="[
                        'w-full text-left px-2.5 py-1.5 rounded text-xs transition-colors hover:bg-slate-50 cursor-pointer',
                        selectedActivation === 'active' ? 'font-bold text-[#4F5AF5]' : 'text-[#1E293B]'
                      ]"
                    >
                      Activos (Cuenta activada)
                    </button>
                    <button
                      type="button"
                      @click="() => { selectedActivation = 'pending'; activationDropdownOpen = false; }"
                      :class="[
                        'w-full text-left px-2.5 py-1.5 rounded text-xs transition-colors hover:bg-slate-50 cursor-pointer',
                        selectedActivation === 'pending' ? 'font-bold text-[#4F5AF5]' : 'text-[#1E293B]'
                      ]"
                    >
                      Pendientes (No activada)
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Dropdown Conexión -->
            <div class="relative">
              <button
                type="button"
                @click="() => {
                  connectionDropdownOpen = !connectionDropdownOpen;
                  activationDropdownOpen = false;
                  vpDropdownOpen = false;
                  dirDropdownOpen = false;
                  roleDropdownOpen = false;
                  transversalDropdownOpen = false;
                }"
                :class="[
                  'px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer',
                  selectedConnection !== 'all' ? 'bg-green-50 border-green-200 text-green-700' : 'bg-white border-[#E2E8F0] text-[#64748B]'
                ]"
              >
                <span>Conexión: {{ selectedConnection === 'all' ? 'Todos' : selectedConnection === 'online' ? 'Online' : 'Offline' }}</span>
                <ChevronDown class="w-3.5 h-3.5" />
              </button>
              <div v-if="connectionDropdownOpen">
                <div class="fixed inset-0 z-40" @click="connectionDropdownOpen = false" />
                <div class="absolute left-0 mt-1 w-48 bg-white border border-[#E2E8F0] rounded-xl shadow-lg z-50 p-2">
                  <div class="space-y-1">
                    <button
                      type="button"
                      @click="() => { selectedConnection = 'all'; connectionDropdownOpen = false; }"
                      :class="[
                        'w-full text-left px-2.5 py-1.5 rounded text-xs transition-colors hover:bg-slate-50 cursor-pointer',
                        selectedConnection === 'all' ? 'font-bold text-[#4F5AF5]' : 'text-[#1E293B]'
                      ]"
                    >
                      Todos
                    </button>
                    <button
                      type="button"
                      @click="() => { selectedConnection = 'online'; connectionDropdownOpen = false; }"
                      :class="[
                        'w-full text-left px-2.5 py-1.5 rounded text-xs transition-colors hover:bg-slate-50 cursor-pointer',
                        selectedConnection === 'online' ? 'font-bold text-[#4F5AF5]' : 'text-[#1E293B]'
                      ]"
                    >
                      Online (Conectados)
                    </button>
                    <button
                      type="button"
                      @click="() => { selectedConnection = 'offline'; connectionDropdownOpen = false; }"
                      :class="[
                        'w-full text-left px-2.5 py-1.5 rounded text-xs transition-colors hover:bg-slate-50 cursor-pointer',
                        selectedConnection === 'offline' ? 'font-bold text-[#4F5AF5]' : 'text-[#1E293B]'
                      ]"
                    >
                      Offline (Desconectados)
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Contenedor con Scroll de la Tabla -->
          <div class="flex-1 overflow-auto p-0">
            <div v-if="loading" class="flex justify-center items-center h-full">
              <div class="animate-spin rounded-full h-8 w-8 border-2 border-[#4F5AF5] border-t-transparent"></div>
            </div>
            <div v-else-if="users.length === 0" class="flex flex-col items-center justify-center h-full text-[#94A3B8] p-6 text-center">
              <Users class="w-12 h-12 mb-3 text-[#E2E8F0]" />
              <p class="font-medium text-[#64748B]">Lista vacía</p>
            </div>
            <table v-else class="w-full text-left border-collapse">
              <thead class="bg-white sticky top-0 border-b border-[#E2E8F0] shadow-xs z-10">
                <tr>
                  <th class="px-6 py-3 text-xs font-bold text-[#64748B] uppercase tracking-wider">Usuario</th>
                  <th class="px-6 py-3 text-xs font-bold text-[#64748B] uppercase tracking-wider">Asignaciones (Rol, VP y Direcciones)</th>
                  <th class="px-6 py-3 text-xs font-bold text-[#64748B] uppercase tracking-wider w-24">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#F1F5F9]">
                <tr v-for="user in filteredUsers" :key="user.id" class="hover:bg-[#F8FAFC] transition-colors">
                  <!-- Columna Usuario -->
                  <td class="px-6 py-4 align-top">
                    <div class="flex items-center gap-3">
                      <div class="w-8 h-8 rounded-full bg-violet-100 flex items-center justify-center text-violet-600 font-bold text-xs shrink-0">
                        {{ user.name.substring(0, 2).toUpperCase() }}
                      </div>
                      <div>
                        <div class="flex items-center gap-2 flex-wrap">
                          <p class="text-sm font-bold text-[#1E293B]">{{ user.name }}</p>

                          <!-- Badge de Activación -->
                          <span
                            v-if="user.is_active"
                            class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0"
                          >
                            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                            Activo
                          </span>
                          <span
                            v-else
                            class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-semibold bg-amber-50 text-amber-600 border border-amber-200 shrink-0"
                          >
                            <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                            Pendiente
                          </span>

                          <!-- Badge de Conexión -->
                          <span
                            v-if="onlineEmails.has(user.email.toLowerCase().trim())"
                            class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-semibold bg-green-50 text-green-700 border border-green-200 shrink-0"
                          >
                            <span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                            Online
                          </span>
                          <span
                            v-else
                            class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-semibold bg-slate-100 text-slate-400 border border-slate-200 shrink-0"
                          >
                            Offline
                          </span>
                        </div>
                        <p class="text-xs text-[#64748B] flex items-center gap-1 mt-1">
                          <Mail class="w-3 h-3" /> {{ user.email }}
                        </p>
                      </div>
                    </div>
                  </td>

                  <!-- Columna Asignaciones -->
                  <td class="px-6 py-4 align-top">
                    <div class="space-y-2">
                      <span v-if="!user.user_roles_whitelist || user.user_roles_whitelist.length === 0" class="text-xs text-red-500 italic">
                        Sin roles asignados
                      </span>
                      <template v-else>
                        <div
                          v-for="(r, idx) in (expandedUsers[user.id] ? user.user_roles_whitelist : user.user_roles_whitelist.slice(0, 2))"
                          :key="idx"
                          class="bg-slate-50 border border-slate-100 rounded-lg p-2 flex flex-col gap-1.5"
                        >
                          <div class="flex items-center gap-2 flex-wrap">
                            <!-- Role Badge -->
                            <span
                              :class="[
                                getRoleBadgeClasses(r.role).bg,
                                getRoleBadgeClasses(r.role).text,
                                getRoleBadgeClasses(r.role).border,
                                'border px-2 py-0.5 rounded-full text-[10px] font-bold shrink-0 inline-flex items-center gap-1'
                              ]"
                            >
                              <span :class="['w-1.5 h-1.5 rounded-full', getRoleBadgeClasses(r.role).dot]" />
                              {{ getRoleBadgeClasses(r.role).name.toUpperCase() }}
                            </span>

                            <!-- Scope / VP Badge -->
                            <span
                              v-if="r.is_transversal || r.role === 'admin' || r.role === 'entrenador_ia'"
                              class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200"
                            >
                              <Globe class="w-3 h-3 text-indigo-600" /> Alcance Transversal
                            </span>
                            <span
                              v-else
                              class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-white text-slate-700 border border-slate-200"
                            >
                              <Building class="w-2.5 h-2.5" /> {{ r.vps?.name || 'Sin VP' }}
                            </span>
                          </div>

                          <!-- Subline Detail -->
                          <div
                            v-if="r.is_transversal || r.role === 'admin' || r.role === 'entrenador_ia'"
                            class="pl-1 border-l-2 border-indigo-300 ml-1"
                          >
                            <span class="text-[10px] text-indigo-700 font-medium flex items-center gap-1">
                              <Sparkles class="w-2.5 h-2.5 text-indigo-500" />
                              {{
                                r.role === 'admin'
                                  ? 'Acceso Global a todo el sistema (Super Administrador)'
                                  : r.role === 'entrenador_ia'
                                  ? 'Gestión Exclusiva de Entrenamiento IA'
                                  : 'Todas las Vicepresidencias y Direcciones'
                              }}
                            </span>
                          </div>
                          <div v-else class="flex flex-col gap-0.5 pl-1 border-l-2 border-slate-200 ml-1">
                            <span v-if="!r.direcciones_ids || r.direcciones_ids.length === 0" class="text-[10px] text-slate-400">
                              Ninguna dirección
                            </span>
                            <span
                              v-else-if="direcciones.filter(d => d.vp_id === r.vp_id).length > 0 && r.direcciones_ids.length === direcciones.filter(d => d.vp_id === r.vp_id).length"
                              class="text-[10px] text-[#4F5AF5] font-semibold flex items-center gap-1"
                            >
                              <Briefcase class="w-2.5 h-2.5" /> Todas las Direcciones ({{ r.direcciones_ids.length }})
                            </span>
                            <template v-else>
                              <span
                                v-for="id in r.direcciones_ids"
                                :key="id"
                                class="text-[10px] text-[#64748B] flex items-center gap-1"
                              >
                                <Briefcase class="w-2.5 h-2.5 text-slate-300" />
                                {{ direcciones.find(d => d.id === id)?.name || 'Desconocida' }}
                              </span>
                            </template>
                          </div>
                        </div>

                        <!-- Botón Ver más asignaciones -->
                        <button
                          v-if="user.user_roles_whitelist && user.user_roles_whitelist.length > 2"
                          type="button"
                          @click="expandedUsers[user.id] = !expandedUsers[user.id]"
                          class="text-[11px] text-[#4F5AF5] hover:text-[#3F49E0] font-semibold transition-colors flex items-center gap-1 mt-1 cursor-pointer"
                        >
                          {{ expandedUsers[user.id] ? 'Ver menos asignaciones' : `Ver ${user.user_roles_whitelist.length - 2} asignaciones más...` }}
                        </button>
                      </template>
                    </div>
                  </td>

                  <!-- Columna Acciones -->
                  <td class="px-6 py-4 align-top">
                    <div class="flex gap-2">
                      <button
                        @click="handleEdit(user)"
                        class="p-1.5 text-blue-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
                        title="Editar usuario"
                      >
                        <Pencil class="w-4 h-4" />
                      </button>
                      <button
                        @click="handleDelete(user.id)"
                        class="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
                        title="Eliminar usuario"
                      >
                        <Trash2 class="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Leyenda de Roles Inferior -->
      <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-5 rounded-2xl border border-blue-100 shadow-xs mt-6">
        <h3 class="text-sm font-bold text-blue-900 mb-3 flex items-center gap-2">
          <Shield class="w-4 h-4 text-blue-600" />
          Niveles de Acceso y Funciones por Rol
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-white p-4 rounded-xl border border-blue-50 shadow-xs">
            <span class="bg-red-100 text-red-700 px-2 py-0.5 rounded text-[10px] font-bold mb-2 inline-block">ADMIN</span>
            <ul class="text-xs text-[#64748B] leading-relaxed list-disc pl-4 space-y-1">
              <li>Control total de la plataforma.</li>
              <li>Configuración de formularios.</li>
              <li>Estructura organizacional y roles.</li>
              <li>Métricas globales.</li>
            </ul>
          </div>
          <div class="bg-white p-4 rounded-xl border border-blue-50 shadow-xs">
            <span class="bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded text-[10px] font-bold mb-2 inline-block">BP TI</span>
            <ul class="text-xs text-[#64748B] leading-relaxed list-disc pl-4 space-y-1">
              <li>Aprobador (Business Partner).</li>
              <li>Edita iniciativas y sugerencias.</li>
              <li>Decide aprobar u observar.</li>
              <li>Gestión de Track Changes.</li>
            </ul>
          </div>
          <div class="bg-white p-4 rounded-xl border border-blue-50 shadow-xs">
            <span class="bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded text-[10px] font-bold mb-2 inline-block">KEY USER</span>
            <ul class="text-xs text-[#64748B] leading-relaxed list-disc pl-4 space-y-1">
              <li>Crea iniciativas con IA.</li>
              <li>Gestiona iniciativas observadas.</li>
              <li>Acepta o rechaza cambios del BP.</li>
            </ul>
          </div>
          <div class="bg-white p-4 rounded-xl border border-blue-50 shadow-xs">
            <span class="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[10px] font-bold mb-2 inline-block">INVITADO</span>
            <ul class="text-xs text-[#64748B] leading-relaxed list-disc pl-4 space-y-1">
              <li>Acceso de solo lectura.</li>
              <li>Métricas de visualización.</li>
              <li>Acceso a iniciativas finalizadas de su VP.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- PESTAÑA 2: CATÁLOGO DE ROLES DINÁMICOS -->
    <div v-if="activeTab === 'roles'" class="space-y-4">
      <!-- 4 KPI Cards Resumen de Roles -->
      <div class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <!-- Total de Roles -->
        <div class="bg-white p-3.5 rounded-xl border border-slate-200/90 shadow-2xs relative overflow-hidden group hover:shadow-xs transition-all">
          <div class="h-0.5 w-full bg-gradient-to-r from-[#4F5AF5] to-[#6366F1] absolute top-0 left-0" />
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Total de Roles</span>
            <div class="w-7 h-7 rounded-lg bg-indigo-50 text-[#4F5AF5] flex items-center justify-center border border-indigo-100/60">
              <Shield class="w-3.5 h-3.5" />
            </div>
          </div>
          <p class="text-xl font-extrabold text-slate-900 mt-1 tracking-tight">{{ roles.length }}</p>
          <p class="text-[10px] text-slate-400 mt-0.5 flex items-center gap-1 font-medium">
            <span class="w-1.5 h-1.5 rounded-full bg-indigo-500" />
            Catálogo institucional activo
          </p>
        </div>

        <!-- Roles del Sistema -->
        <div class="bg-white p-3.5 rounded-xl border border-slate-200/90 shadow-2xs relative overflow-hidden group hover:shadow-xs transition-all">
          <div class="h-0.5 w-full bg-gradient-to-r from-slate-400 to-slate-500 absolute top-0 left-0" />
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Roles del Sistema</span>
            <div class="w-7 h-7 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center border border-slate-200/60">
              <Lock class="w-3.5 h-3.5" />
            </div>
          </div>
          <p class="text-xl font-extrabold text-slate-900 mt-1 tracking-tight">
            {{ roles.filter(r => r.is_system).length }}
          </p>
          <p class="text-[10px] text-slate-400 mt-0.5 flex items-center gap-1 font-medium">
            <span class="w-1.5 h-1.5 rounded-full bg-slate-400" />
            Protegidos e inmutables
          </p>
        </div>

        <!-- Roles Personalizados -->
        <div class="bg-white p-3.5 rounded-xl border border-slate-200/90 shadow-2xs relative overflow-hidden group hover:shadow-xs transition-all">
          <div class="h-0.5 w-full bg-gradient-to-r from-violet-500 to-indigo-500 absolute top-0 left-0" />
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Personalizados</span>
            <div class="w-7 h-7 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center border border-violet-100/60">
              <Sparkles class="w-3.5 h-3.5" />
            </div>
          </div>
          <p class="text-xl font-extrabold text-slate-900 mt-1 tracking-tight">
            {{ roles.filter(r => !r.is_system).length }}
          </p>
          <p class="text-[10px] text-slate-400 mt-0.5 flex items-center gap-1 font-medium">
            <span class="w-1.5 h-1.5 rounded-full bg-violet-500" />
            Habilitados para flujos
          </p>
        </div>

        <!-- Asignaciones -->
        <div class="bg-white p-3.5 rounded-xl border border-slate-200/90 shadow-2xs relative overflow-hidden group hover:shadow-xs transition-all">
          <div class="h-0.5 w-full bg-gradient-to-r from-emerald-500 to-teal-500 absolute top-0 left-0" />
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Asignaciones</span>
            <div class="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100/60">
              <Users class="w-3.5 h-3.5" />
            </div>
          </div>
          <p class="text-xl font-extrabold text-slate-900 mt-1 tracking-tight">
            {{ roles.reduce((acc, r) => acc + (r.user_count || 0), 0) }}
          </p>
          <p class="text-[10px] text-slate-400 mt-0.5 flex items-center gap-1 font-medium">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Usuarios asignados
          </p>
        </div>
      </div>

      <!-- Barra de Búsqueda y Filtros Rápidos -->
      <div class="bg-white p-2.5 rounded-xl shadow-2xs border border-slate-200/90 flex flex-col md:flex-row md:items-center justify-between gap-2.5">
        <div class="relative flex-1 md:max-w-md">
          <Search class="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            v-model="roleSearchQuery"
            placeholder="Buscar por nombre, código slug o descripción..."
            class="w-full pl-9 pr-8 py-1.5 bg-slate-50 hover:bg-slate-100/70 border border-slate-200 rounded-lg text-xs text-slate-800 outline-none focus:border-[#4F5AF5] focus:bg-white transition-all placeholder:text-slate-400"
          />
          <button
            v-if="roleSearchQuery"
            type="button"
            @click="roleSearchQuery = ''"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5 rounded-full cursor-pointer"
          >
            <X class="w-3 h-3" />
          </button>
        </div>

        <div class="flex items-center gap-2 flex-wrap justify-between sm:justify-end">
          <div class="flex bg-slate-100 p-0.5 rounded-lg gap-0.5 overflow-x-auto">
            <button
              v-for="tab in [
                { id: 'all', label: 'Todos', count: roles.length },
                { id: 'system', label: 'Sistema', count: roles.filter(r => r.is_system).length },
                { id: 'custom', label: 'Personalizados', count: roles.filter(r => !r.is_system).length },
                { id: 'active', label: 'Activos', count: roles.filter(r => r.is_active).length },
              ]"
              :key="tab.id"
              type="button"
              @click="roleFilterType = (tab.id as any)"
              :class="[
                'px-2.5 py-1 rounded-md text-[11px] font-bold transition-all cursor-pointer flex items-center gap-1.5 shrink-0',
                roleFilterType === tab.id
                  ? 'bg-white text-slate-800 shadow-2xs'
                  : 'text-slate-500 hover:text-slate-800'
              ]"
            >
              <span>{{ tab.label }}</span>
              <span
                :class="[
                  'px-1.5 py-0.2 rounded-full text-[9px] font-semibold',
                  roleFilterType === tab.id ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-200/80 text-slate-600'
                ]"
              >
                {{ tab.count }}
              </span>
            </button>
          </div>

          <button
            type="button"
            @click="fetchRoles"
            :disabled="rolesLoading"
            class="p-1.5 border border-slate-200 hover:bg-slate-50 text-slate-500 hover:text-slate-700 rounded-lg transition-colors disabled:opacity-50 cursor-pointer shadow-2xs"
            title="Actualizar lista de roles"
          >
            <RefreshCw :class="['w-3.5 h-3.5', rolesLoading ? 'animate-spin text-[#4F5AF5]' : '']" />
          </button>
        </div>
      </div>

      <!-- Grid de Tarjetas de Roles (10 Roles) -->
      <div v-if="rolesLoading && roles.length === 0" class="py-14 text-center bg-white rounded-xl border border-slate-200/90 shadow-2xs">
        <Loader2 class="w-6 h-6 text-[#4F5AF5] animate-spin mx-auto mb-2" />
        <p class="text-xs font-bold text-slate-700">Cargando catálogo de roles...</p>
        <p class="text-[10px] text-slate-400 mt-0.5">Sincronizando con base de datos</p>
      </div>
      <div v-else-if="filteredRolesCatalog.length === 0" class="py-14 text-center bg-white rounded-xl border border-slate-200/90 shadow-2xs">
        <div class="w-9 h-9 rounded-xl bg-slate-100 flex items-center justify-center text-slate-400 mx-auto mb-2">
          <Shield class="w-5 h-5" />
        </div>
        <p class="text-sm font-bold text-slate-800">No se encontraron roles</p>
        <p class="text-[11px] text-slate-500 mt-1 max-w-sm mx-auto">
          No hay ningún rol que coincida con los filtros seleccionados o el término de búsqueda.
        </p>
        <button
          type="button"
          @click="() => { roleSearchQuery = ''; roleFilterType = 'all'; }"
          class="mt-3 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-lg transition-colors cursor-pointer"
        >
          Limpiar filtros
        </button>
      </div>
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3.5">
        <div
          v-for="role in filteredRolesCatalog"
          :key="role.id"
          class="group relative bg-white rounded-xl border border-slate-200/90 shadow-2xs hover:shadow-xs hover:border-slate-300 transition-all duration-150 overflow-hidden flex flex-col justify-between"
        >
          <!-- Top Colored Accent Line -->
          <div
            class="h-1 w-full transition-all duration-200 group-hover:h-1.5"
            :style="{ backgroundColor: (ROLE_COLORS[role.color] || ROLE_COLORS.slate).swatch }"
          />

          <div class="p-3.5 flex-1 flex flex-col justify-between">
            <div>
              <!-- Header Row: Icon + Title + System/Custom Badge -->
              <div class="flex items-start justify-between gap-2">
                <div class="flex items-start gap-2.5 min-w-0 flex-1">
                  <div
                    class="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 border"
                    :style="{
                      backgroundColor: `${(ROLE_COLORS[role.color] || ROLE_COLORS.slate).swatch}15`,
                      borderColor: `${(ROLE_COLORS[role.color] || ROLE_COLORS.slate).swatch}35`
                    }"
                  >
                    <component
                      :is="getRoleIconComponent(role.code, role.is_system).icon"
                      :class="['w-4 h-4', getRoleIconComponent(role.code, role.is_system).class]"
                    />
                  </div>
                  <div class="min-w-0 flex-1">
                    <h3
                      class="text-xs font-bold text-slate-900 group-hover:text-[#4F5AF5] transition-colors leading-tight truncate"
                      :title="role.name"
                    >
                      {{ role.name }}
                    </h3>

                    <!-- Slug Chip with Copy Button -->
                    <div class="mt-1 flex items-center gap-1">
                      <button
                        type="button"
                        @click="handleCopySlug(role.code)"
                        class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-slate-100 hover:bg-slate-200/80 text-slate-600 font-mono text-[10px] font-medium border border-slate-200/70 transition-colors cursor-pointer group/code"
                        title="Copiar código técnico"
                      >
                        <span class="truncate max-w-[100px]">{{ role.code }}</span>
                        <Check v-if="copiedSlug === role.code" class="w-2.5 h-2.5 text-emerald-600 shrink-0" />
                        <Copy v-else class="w-2.5 h-2.5 text-slate-400 group-hover/code:text-slate-600 shrink-0" />
                      </button>
                      <span v-if="copiedSlug === role.code" class="text-[9px] text-emerald-600 font-bold">
                        ¡Copiado!
                      </span>
                    </div>
                  </div>
                </div>

                <!-- System vs Custom Badge -->
                <span
                  v-if="role.is_system"
                  class="inline-flex items-center gap-0.5 text-[9px] font-bold text-slate-600 bg-slate-100 border border-slate-200/80 px-1.5 py-0.5 rounded-md shrink-0"
                  title="Rol del sistema base"
                >
                  <Lock class="w-2.5 h-2.5 text-slate-500" />
                  Sistema
                </span>
                <span
                  v-else
                  class="inline-flex items-center gap-0.5 text-[9px] font-bold text-violet-700 bg-violet-50 border border-violet-200 px-1.5 py-0.5 rounded-md shrink-0"
                  title="Rol personalizado para flujos"
                >
                  <Sparkles class="w-2.5 h-2.5 text-violet-500" />
                  Personal
                </span>
              </div>

              <!-- Description -->
              <p class="text-[11px] text-slate-500 mt-2 line-clamp-2 min-h-[2rem] leading-relaxed">
                {{ role.description || 'Sin descripción detallada.' }}
              </p>
            </div>

            <!-- Footer: Users + Status + Actions -->
            <div class="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between gap-1">
              <div
                class="flex items-center gap-1.5 text-slate-600 text-[11px] font-semibold"
                :title="`${role.user_count || 0} usuario(s) asignado(s)`"
              >
                <Users class="w-3 h-3 text-slate-400 shrink-0" />
                <span>{{ role.user_count || 0 }} <span class="text-[10px] text-slate-400 font-normal">usr</span></span>
              </div>

              <div class="flex items-center gap-1.5">
                <button
                  type="button"
                  @click="handleToggleRoleStatus(role)"
                  :disabled="role.code === 'admin'"
                  :class="[
                    'text-[10px] font-bold px-1.5 py-0.5 rounded-md border transition-all inline-flex items-center gap-1 cursor-pointer',
                    role.is_active
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
                      : 'bg-slate-100 text-slate-500 border-slate-200 hover:bg-slate-200',
                    role.code === 'admin' ? 'cursor-not-allowed opacity-80' : ''
                  ]"
                  :title="role.code === 'admin' ? 'El rol administrador no puede desactivarse' : 'Clic para alternar estado'"
                >
                  <span :class="['w-1.5 h-1.5 rounded-full', role.is_active ? 'bg-emerald-500' : 'bg-slate-400']" />
                  {{ role.is_active ? 'Activo' : 'Inactivo' }}
                </button>

                <button
                  type="button"
                  @click="handleOpenEditRole(role)"
                  class="p-1 rounded-md text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 border border-transparent hover:border-indigo-100 transition-colors cursor-pointer"
                  title="Editar rol"
                >
                  <Pencil class="w-3 h-3" />
                </button>

                <button
                  type="button"
                  @click="handleDeleteRole(role)"
                  :disabled="role.is_system || (role.user_count || 0) > 0"
                  :class="[
                    'p-1 rounded-md border transition-all',
                    role.is_system || (role.user_count || 0) > 0
                      ? 'text-slate-300 border-transparent cursor-not-allowed'
                      : 'text-slate-400 hover:text-red-600 hover:bg-red-50 border-transparent hover:border-red-100 cursor-pointer'
                  ]"
                  :title="
                    role.is_system
                      ? 'Los roles del sistema base no se pueden eliminar'
                      : (role.user_count || 0) > 0
                      ? `No se puede eliminar: tiene ${role.user_count} usuario(s) asignado(s)`
                      : 'Eliminar rol'
                  "
                >
                  <Trash2 class="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL PARA CREAR / EDITAR ROL CON VISTA PREVIA EN VIVO -->
    <div v-if="roleModalOpen" class="fixed inset-0 bg-black/40 backdrop-blur-2xs flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95 duration-150">
        <div class="flex items-center justify-between pb-4 border-b border-[#E2E8F0]">
          <div class="flex items-center gap-2.5">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#4F5AF5] to-[#6366F1] text-white flex items-center justify-center shadow-xs">
              <Shield class="w-4.5 h-4.5" />
            </div>
            <div>
              <h3 class="text-base font-bold text-slate-900">
                {{ editingRole ? `Editar Rol: ${editingRole.name}` : 'Crear Nuevo Rol' }}
              </h3>
              <p class="text-xs text-slate-500">
                {{ editingRole ? 'Modifica los atributos visibles y estado del rol' : 'Define un nuevo rol institucional para flujos' }}
              </p>
            </div>
          </div>
          <button
            type="button"
            @click="roleModalOpen = false"
            class="text-slate-400 hover:text-slate-600 p-1.5 rounded-xl hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Vista Previa en Vivo del Badge -->
        <div class="bg-slate-50 p-3.5 rounded-2xl border border-slate-200/90 my-4">
          <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
            Vista previa del rol en tiempo real
          </span>
          <div class="flex items-center justify-between gap-3 bg-white p-3.5 rounded-xl border border-slate-200/90 shadow-2xs">
            <div class="flex items-center gap-3 min-w-0">
              <div
                class="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border"
                :style="{
                  backgroundColor: `${(ROLE_COLORS[roleForm.color] || ROLE_COLORS.indigo).swatch}15`,
                  borderColor: `${(ROLE_COLORS[roleForm.color] || ROLE_COLORS.indigo).swatch}35`
                }"
              >
                <UserCog class="w-4.5 h-4.5" :style="{ color: (ROLE_COLORS[roleForm.color] || ROLE_COLORS.indigo).swatch }" />
              </div>
              <div class="min-w-0">
                <p class="text-xs font-bold text-slate-900 truncate">
                  {{ roleForm.name.trim() || 'Nombre del rol' }}
                </p>
                <p class="text-[10px] font-mono text-slate-500 mt-0.5 truncate">
                  {{ roleForm.code ? toCleanSlug(roleForm.code) : 'codigo_tecnico' }}
                </p>
              </div>
            </div>

            <span
              :class="[
                'text-[10px] font-bold px-2.5 py-0.5 rounded-full border shrink-0',
                roleForm.is_active ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-500 border-slate-200'
              ]"
            >
              {{ roleForm.is_active ? '● Activo' : '○ Inactivo' }}
            </span>
          </div>
        </div>

        <form @submit.prevent="handleSaveRole" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1.5">
              Nombre del Rol <span class="text-red-500">*</span>
            </label>
            <input
              required
              type="text"
              v-model="roleForm.name"
              @input="() => {
                if (!editingRole) {
                  roleForm.code = toCleanSlug(roleForm.name).replace(/^_+|_+$/g, '');
                }
              }"
              placeholder="Ej: Comité de TI, Director de VP, Líder Técnico"
              class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 outline-none focus:border-[#4F5AF5] focus:bg-white transition-colors"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1.5">
              Código Técnico Identificador <span class="text-red-500">*</span>
            </label>
            <input
              required
              type="text"
              :value="roleForm.code"
              :disabled="!!editingRole"
              @input="(e: any) => roleForm.code = toCleanSlug(e.target.value)"
              placeholder="ej: comite_ti, director_vp, lider_dominio_ti"
              :class="[
                'w-full px-3.5 py-2.5 font-mono text-xs rounded-xl border',
                editingRole
                  ? 'bg-slate-100 border-slate-200 text-slate-500 cursor-not-allowed'
                  : 'bg-slate-50 border-slate-200 text-slate-800 outline-none focus:border-[#4F5AF5] focus:bg-white'
              ]"
            />
            <p class="text-[10px] text-slate-400 mt-1">
              {{
                editingRole
                  ? 'El código técnico es inmutable para garantizar la consistencia en el motor de flujos.'
                  : 'Sin tildes ni caracteres especiales. Se generará automáticamente y se utilizará en las reglas del flujo.'
              }}
            </p>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1.5">
              Descripción y Alcance
            </label>
            <textarea
              rows="3"
              v-model="roleForm.description"
              placeholder="Explica las responsabilidades de este rol en las iniciativas o revisiones..."
              class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 outline-none focus:border-[#4F5AF5] focus:bg-white transition-colors resize-none"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
              Color Distintivo del Badge
            </label>
            <div class="grid grid-cols-4 gap-2">
              <button
                v-for="[colorKey, cfg] in Object.entries(ROLE_COLORS).filter(([k]) => k !== 'red')"
                :key="colorKey"
                type="button"
                @click="roleForm.color = colorKey"
                :class="[
                  'flex items-center gap-2 p-2 rounded-xl border text-xs font-semibold transition-all cursor-pointer',
                  roleForm.color === colorKey
                    ? 'border-[#4F5AF5] bg-indigo-50/70 ring-2 ring-[#4F5AF5]/20 shadow-2xs'
                    : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-700'
                ]"
              >
                <span :class="['w-3.5 h-3.5 rounded-full shrink-0', cfg.dot]" />
                <span class="truncate text-[11px]">{{ cfg.label }}</span>
              </button>
            </div>
          </div>

          <div class="pt-2">
            <label class="flex items-center gap-2.5 cursor-pointer select-none">
              <input
                type="checkbox"
                v-model="roleForm.is_active"
                :disabled="editingRole?.code === 'admin'"
                class="rounded border-[#CBD5E1] text-[#4F5AF5] focus:ring-[#4F5AF5] w-4 h-4 cursor-pointer"
              />
              <span class="text-xs font-medium text-slate-700">
                Rol activo (disponible para asignaciones de usuarios y flujos de trabajo)
              </span>
            </label>
          </div>

          <div class="flex gap-2.5 pt-4 border-t border-slate-100">
            <button
              type="button"
              @click="roleModalOpen = false"
              class="flex-1 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 font-bold py-2.5 rounded-xl text-xs transition-colors cursor-pointer"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="roleSaving"
              class="flex-2 bg-gradient-to-r from-[#4F5AF5] to-[#6366F1] hover:from-[#3D47E0] hover:to-[#4F5AF5] disabled:opacity-50 text-white font-bold py-2.5 rounded-xl text-xs transition-all inline-flex items-center justify-center gap-2 shadow-md cursor-pointer"
            >
              <Loader2 v-if="roleSaving" class="w-4 h-4 animate-spin" />
              <span>{{ roleSaving ? 'Guardando...' : (editingRole ? 'Actualizar Rol' : 'Crear Rol') }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
