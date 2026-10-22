<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { 
  Menu, PlusCircle, LayoutDashboard, Inbox, Building2, ShieldAlert, 
  Workflow, FileCheck2, Play, GitBranch, Network, Users, BrainCircuit, 
  Upload, Mail, ChevronDown, LogOut, MessageSquarePlus, Bell, Trash2, 
  AlertTriangle, ShieldCheck, X 
} from 'lucide-vue-next';

const route = useRoute();
const router = useRouter();
const config = useRuntimeConfig();
const apiBase = config.public.apiBase;

import InstitutionalLoader from '~/components/common/InstitutionalLoader.vue';
import { useGlobalLoader } from '~/composables/useGlobalLoader';

const globalLoader = useGlobalLoader();
const isAppInitializing = ref(true);
const isPageNavigating = ref(false);

// Estado del Layout y Sidebar
const sidebarCollapsed = ref(false);
const adminOpen = ref(true);
const draftsOpen = ref(false);
const notificationsOpen = ref(false);
const showRolesModal = ref(false);
const showNavConfirmModal = ref(false);
const pendingNavPath = ref<string | null>(null);

// Usuario de prueba corporativo (Administrador por defecto en entorno local)
const user = ref({
  id: '',
  name: 'Administrador General',
  email: 'admin@iacs.empresa.com',
  roles: ['admin'],
  vpName: '',
  direcciones: [] as string[]
});

const userInitials = computed(() => {
  return (user.value.name || 'US').substring(0, 2).toUpperCase();
});

const isAdmin = computed(() => user.value.roles.includes('admin'));
const isRegistrador = computed(() => user.value.roles.includes('registrador'));
const isEntrenadorIA = computed(() => user.value.roles.includes('entrenador_ia'));

const primaryRoleLabel = computed(() => {
  if (!user.value.roles || user.value.roles.length === 0) return 'Invitado';
  if (isAdmin.value) return 'Admin';
  const roleNameMap: Record<string, string> = {
    registrador: 'Registrador',
    key_user: 'Key User',
    gerente_area: 'Gerente Área',
    comite: 'Comité',
    vp: 'Aprobador VP',
    vicepresidente_del_negocio: 'Aprobador VP',
    business_owner: 'Business Owner',
    estimador: 'Estimador TI',
    gobierno: 'Gobierno TI',
    finanzas: 'Finanzas',
    entrenador_ia: 'Entrenador IA',
    lider_de_dominio: 'Líder de Dominio',
    bp_ti: 'BP TI',
  };
  const firstRole = user.value.roles[0];
  return roleNameMap[firstRole] || firstRole.replace(/_/g, ' ');
});

const additionalRolesCount = computed(() => {
  if (!user.value.roles) return 0;
  return Math.max(0, user.value.roles.length - 1);
});

// Menú Principal
const navItems = computed(() => [
  ...(isRegistrador.value || isAdmin.value ? [{ name: 'Nueva necesidad', path: '/nueva', icon: PlusCircle }] : []),
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Bandeja de Revisión', path: '/bandeja', icon: Inbox },
]);

// Grupos Administrativos Idénticos al Proyecto Original
const adminGroups = [
  {
    name: 'Organización y Accesos',
    items: [
      { name: 'Estructura Organizativa', path: '/admin/estructura', icon: Building2 },
      { name: 'Gestión de Usuarios', path: '/admin/usuarios', icon: ShieldAlert },
    ]
  },
  {
    name: 'Personalización de Datos',
    items: [
      { name: 'Editor de Flujos', path: '/admin/workflow-editor', icon: Workflow },
      { name: 'Formularios y Consentimientos', path: '/admin/formularios-consentimientos', icon: FileCheck2 },
    ]
  },
  {
    name: 'Centro de Agentes e IA',
    items: [
      { name: 'Tablero de Agentes', path: '/admin/agentes', icon: Users },
      { name: 'Entrenamiento IA', path: '/admin/ia-training', icon: BrainCircuit },
      { name: 'Laboratorio Teo (Sandbox)', path: '/admin/sandbox-teo', icon: BrainCircuit },
    ]
  },
  {
    name: 'Gestión de Datos',
    items: [
      { name: 'Cargas Masivas', path: '/admin/cargas-masivas', icon: Upload },
    ]
  },
  {
    name: 'Comunicaciones',
    items: [
      { name: 'Bandeja de Correos', path: '/admin/correos', icon: Mail },
    ]
  }
];

const expandedGroups = ref<Record<string, boolean>>({
  'Organización y Accesos': true,
  'Personalización de Datos': false,
  'Centro de Agentes e IA': false,
  'Gestión de Datos': false,
  'Comunicaciones': false
});

const toggleGroup = (groupName: string) => {
  expandedGroups.value[groupName] = !expandedGroups.value[groupName];
};

// Borradores / Chats pendientes (Solo chats en curso que no llegaron a resumen)
const drafts = ref<any[]>([]);
const fetchDrafts = async () => {
  try {
    const data: any[] = await $fetch(`${apiBase}/initiatives`);
    // REGLA: Las iniciativas en estado borrador solo las puede visualizar el registrador de la misma
    drafts.value = (data || []).filter((init: any) => {
      const isMine = Boolean(
        (user.value.id && init.user_id === user.value.id) ||
        (user.value.email && init.form_data?.registrador_email === user.value.email) ||
        (user.value.name && (init.form_data?.registrador === user.value.name || init.form_data?.solicitante === user.value.name))
      );
      if (!isMine) return false;

      const reachedSummary = init.form_data?._reached_summary === true;
      const isChat = init.status === 'Chat' || (init.status === 'Borrador' && !reachedSummary);
      return !reachedSummary && isChat;
    });
  } catch (e) {
    drafts.value = [];
  }
};

const syncUserWithBackend = async () => {
  if (!process.client) return;
  try {
    const savedUserStr = localStorage.getItem('iacs_user');
    const token = localStorage.getItem('iacs_token');
    const u = savedUserStr ? JSON.parse(savedUserStr) : null;
    const emailToQuery = u?.email || user.value.email;
    if (!emailToQuery) return;

    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const fresh: any = await $fetch(`${apiBase}/auth/me?email=${encodeURIComponent(emailToQuery)}`, {
      headers
    });

    if (fresh && fresh.email) {
      user.value = {
        id: fresh.id || user.value.id,
        name: fresh.name || user.value.name,
        email: fresh.email || user.value.email,
        roles: (fresh.roles && fresh.roles.length > 0) ? fresh.roles : user.value.roles,
        vpName: fresh.vp_name || fresh.vpName || '',
        direcciones: Array.isArray(fresh.direcciones) ? fresh.direcciones : [],
      };
      localStorage.setItem('iacs_user', JSON.stringify({
        ...(u || {}),
        ...fresh
      }));
    }
  } catch (err) {
    console.warn('No se pudo sincronizar perfil de usuario:', err);
  }
};

onMounted(() => {
  if (process.client) {
    const savedUser = localStorage.getItem('iacs_user');
    if (savedUser) {
      try {
        const u = JSON.parse(savedUser);
        user.value = {
          id: u.id || user.value.id,
          name: u.name || user.value.name,
          email: u.email || user.value.email,
          roles: (u.roles && u.roles.length > 0) ? u.roles : (u.role ? [u.role] : user.value.roles),
          vpName: u.vp_name || u.vpName || '',
          direcciones: Array.isArray(u.direcciones) ? u.direcciones : [],
        };
      } catch (e) {}
    }

    // Sincronizar reactivamente con el backend en segundo plano
    syncUserWithBackend();

    // Escuchar eventos globales de actualización de usuario (e.g. desde el panel admin)
    window.addEventListener('iacs_user_updated', (e: any) => {
      const updatedUser = e?.detail?.user;
      if (updatedUser && updatedUser.email?.toLowerCase() === user.value.email?.toLowerCase()) {
        user.value = {
          id: updatedUser.id || user.value.id,
          name: updatedUser.name || user.value.name,
          email: updatedUser.email || user.value.email,
          roles: (updatedUser.roles && updatedUser.roles.length > 0) ? updatedUser.roles : user.value.roles,
          vpName: updatedUser.vp_name || updatedUser.vpName || '',
          direcciones: Array.isArray(updatedUser.direcciones) ? updatedUser.direcciones : [],
        };
      } else {
        syncUserWithBackend();
      }
    });
  }
  fetchDrafts();
  if (route.path === '/bandeja') {
    sidebarCollapsed.value = true;
  }

  // Finalizar inicialización con animación institucional
  setTimeout(() => {
    isAppInitializing.value = false;
  }, 600);
});

// Transición suave institucional entre rutas
router.beforeEach((to, from, next) => {
  if (to.path !== from.path) {
    isPageNavigating.value = true;
  }
  next();
});

router.afterEach(() => {
  setTimeout(() => {
    isPageNavigating.value = false;
  }, 250);
});

const handleLogout = () => {
  if (process.client) {
    localStorage.removeItem('iacs_token');
    localStorage.removeItem('iacs_user');
  }
  router.push('/login');
};

</script>

<template>
  <!-- Pantalla de Carga Inicial Institucional (Bootstrap / Verificación de credenciales) -->
  <div v-if="isAppInitializing && route.path !== '/login'" class="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
    <InstitutionalLoader 
      title="Iniciando IACS Enterprise" 
      subtitle="Verificando credenciales de seguridad y sesión activa..." 
    />
  </div>

  <div v-else-if="route.path === '/login'" class="min-h-screen bg-[#F7F8FC]">
    <NuxtPage />
  </div>

  <div v-else class="flex flex-col h-screen overflow-hidden bg-[#F0F4FF] text-[#1E293B] font-sans">
    <!-- Modal de Detalle de Roles -->
    <div v-if="showRolesModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" @click="showRolesModal = false" />
      <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200 border border-slate-100">
        <div class="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-[#FFF0ED] text-[#EB5F46] flex items-center justify-center">
              <ShieldCheck class="w-4 h-4" />
            </div>
            <div>
              <h3 class="text-sm font-bold text-slate-900">Detalle de Perfil y Roles</h3>
              <p class="text-[11px] text-slate-500">Permisos y adscripción en IACS</p>
            </div>
          </div>
          <button 
            @click="showRolesModal = false" 
            class="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-200/60 transition-colors"
          >
            <X class="w-4 h-4" />
          </button>
        </div>

        <div class="p-6 max-h-[65vh] overflow-y-auto space-y-4">
          <!-- Cabecera de Identidad -->
          <div class="flex items-center gap-3.5 p-3.5 bg-slate-50/80 rounded-xl border border-slate-200/80">
            <div class="w-11 h-11 rounded-full bg-gradient-to-br from-[#EB5F46] to-[#0D436C] flex items-center justify-center text-sm font-black text-white uppercase shadow-sm shrink-0">
              {{ userInitials }}
            </div>
            <div class="min-w-0 flex-1">
              <p class="text-sm font-bold text-slate-900 truncate">{{ user.name }}</p>
              <p class="text-xs text-slate-500 truncate">{{ user.email }}</p>
            </div>
          </div>

          <!-- Listado Dinámico de Roles -->
          <div>
            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 px-1">Roles Asignados</p>
            <div class="space-y-2">
              <div 
                v-for="role in (user.roles || [])" 
                :key="role"
                class="p-3 rounded-xl border transition-all"
                :class="role === 'admin' ? 'bg-[#FFF0ED]/70 border-[#FCD9D2]' : 'bg-white border-slate-200'"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full" :class="role === 'admin' ? 'bg-[#EB5F46]' : 'bg-emerald-500'"></span>
                    <span class="text-xs font-bold uppercase tracking-wider" :class="role === 'admin' ? 'text-[#EB5F46]' : 'text-slate-800'">
                      {{ role.replace(/_/g, ' ') }}
                    </span>
                  </div>
                  <span class="text-[10px] px-2 py-0.5 rounded-full font-semibold" :class="role === 'admin' ? 'bg-[#EB5F46]/10 text-[#EB5F46]' : 'bg-slate-100 text-slate-600'">
                    Activo
                  </span>
                </div>
                <p v-if="role === 'admin'" class="text-[11px] text-slate-500 mt-1 pl-4">
                  Acceso y gobernanza global del sistema y sus configuraciones.
                </p>
              </div>
            </div>
          </div>

          <!-- Estructura Organizativa si aplica -->
          <div v-if="user.vpName || (user.direcciones && user.direcciones.length > 0)" class="bg-white border border-slate-200 p-4 rounded-xl shadow-2xs space-y-2">
            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Estructura Organizacional</p>
            <p v-if="user.vpName" class="text-xs text-slate-700"><strong>VP:</strong> {{ user.vpName }}</p>
            <div v-if="user.direcciones && user.direcciones.length > 0">
              <p class="text-xs font-semibold text-slate-700 mb-1">Direcciones Asignadas:</p>
              <ul class="text-xs text-slate-600 list-disc pl-4 space-y-0.5">
                <li v-for="(d, i) in user.direcciones" :key="i">{{ d }}</li>
              </ul>
            </div>
          </div>
        </div>

        <div class="px-6 py-4 border-t border-slate-100 bg-slate-50 flex justify-end">
          <button
            @click="showRolesModal = false"
            class="bg-white border border-slate-200 hover:bg-slate-100 text-slate-700 px-4 py-2 rounded-lg text-xs font-semibold transition-colors shadow-2xs"
          >
            Entendido
          </button>
        </div>
      </div>
    </div>

    <!-- Header Corporativo Idéntico (100% de ancho con degradado institucional) -->
    <header class="corp-header shrink-0 shadow-[0_2px_12px_rgba(13,67,108,.05)] relative z-[60]">
      <div class="corp-header-bg" />
      <div class="h-16 flex items-center justify-between px-8 relative z-10">
        <div class="flex items-center gap-4">
          <button 
            @click="sidebarCollapsed = !sidebarCollapsed"
            class="p-2 rounded-lg text-white hover:bg-white/10 transition-colors"
            title="Colapsar / Desplegar menú"
          >
            <Menu class="w-5 h-5" />
          </button>
          <div class="flex items-center gap-2">
            <span class="text-xs font-bold uppercase tracking-wider text-white">Laureate Perú</span>
            <span class="text-xs text-white/30">|</span>
            <h2 class="text-xs font-extrabold uppercase tracking-widest text-white/90">IT Needs Manager</h2>
          </div>
        </div>

        <div class="flex items-center gap-3 relative z-50">
          <!-- Botón de Chats Pendientes / Borradores -->
          <div class="relative z-50">
            <button 
              @click="draftsOpen = !draftsOpen; notificationsOpen = false"
              class="relative w-9 h-9 rounded-lg border border-white/20 flex items-center justify-center text-white/90 hover:bg-white/10 transition-colors"
              title="Chats pendientes"
            >
              <MessageSquarePlus class="w-4 h-4" />
              <span v-if="drafts.length > 0" class="absolute -top-1.5 -right-1.5 bg-[#EB5F46] text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center border-2 border-white">
                {{ drafts.length }}
              </span>
            </button>

            <div v-if="draftsOpen" class="absolute right-0 mt-2 w-72 bg-white rounded-xl shadow-lg border border-[#e4e6ea] z-50 overflow-hidden">
              <div class="px-4 py-3 border-b border-[#e4e6ea] bg-[#f7f8fc]">
                <h3 class="text-xs font-bold text-[#1a1a2e] uppercase tracking-wider">Chats pendientes</h3>
              </div>
              <div class="max-h-64 overflow-y-auto p-2">
                <p v-if="drafts.length === 0" class="text-xs text-[#9ca3af] text-center py-4">No hay chats pendientes.</p>
                <div 
                  v-for="d in drafts" 
                  :key="d.id"
                  class="group flex items-center justify-between p-2 rounded-lg hover:bg-[#f7f8fc] transition-colors border border-transparent hover:border-[#e4e6ea] mb-1"
                >
                  <NuxtLink :to="`/nueva?id=${d.id}`" @click="draftsOpen = false" class="flex-1 min-w-0 pr-2">
                    <p class="text-sm font-semibold text-[#1a1a2e] truncate">
                      {{ d.form_data?.titulo || 'Chat en curso con Teo' }}
                    </p>
                    <p class="text-[10px] text-[#9ca3af] mt-0.5">
                      {{ new Date(d.created_at).toLocaleDateString() }}
                    </p>
                  </NuxtLink>
                </div>
              </div>
            </div>
          </div>

          <!-- Botón de Notificaciones -->
          <div class="relative z-50">
            <button 
              @click="notificationsOpen = !notificationsOpen; draftsOpen = false"
              class="w-9 h-9 rounded-lg border border-white/20 flex items-center justify-center text-white/90 hover:bg-white/10 transition-colors relative"
            >
              <Bell class="w-4 h-4" />
            </button>
          </div>

          <!-- Botón Destacado Nueva Necesidad -->
          <NuxtLink
            to="/nueva"
            class="bg-white hover:bg-white/90 text-[#EB5F46] px-4 py-2 rounded-lg text-sm font-semibold transition-colors shadow-sm hidden sm:flex items-center gap-2"
          >
            <PlusCircle class="w-4 h-4" />
            Nueva necesidad
          </NuxtLink>
        </div>
      </div>
      <!-- Línea Divisoria Degradada Identitaria -->
      <div class="h-1 w-full bg-gradient-to-r from-[#EB5F46] via-[#007FB1] to-[#00B8B2]" />
    </header>

    <!-- Cuerpo Principal con Sidebar y Área de Contenido -->
    <div class="flex-grow flex flex-row overflow-hidden relative">
      <!-- Sidebar -->
      <aside 
        :class="[
          'bg-white border-r border-[#e4e6ea] shadow-[1px_0_4px_rgba(13,67,108,.03)] transition-all duration-300 ease-in-out flex flex-col h-full shrink-0',
          sidebarCollapsed ? 'w-0 -translate-x-full overflow-hidden opacity-0' : 'w-64 translate-x-0 opacity-100'
        ]"
      >
        <!-- Navegación Principal -->
        <nav class="flex-grow p-4 space-y-1 overflow-y-auto">
          <p class="text-[10px] uppercase font-bold text-[#9ca3af] tracking-widest px-3 mb-2">Principal</p>
          <NuxtLink
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition-all',
              route.path === item.path
                ? 'bg-[#fff0ed] text-[#EB5F46] shadow-sm'
                : 'text-[#4a5568] hover:bg-[#f7f8fc] hover:text-[#1a1a2e]'
            ]"
          >
            <component :is="item.icon" class="w-4 h-4 shrink-0" />
            {{ item.name }}
          </NuxtLink>

          <!-- Divisor -->
          <div class="pt-4 pb-1">
            <div class="border-t border-[#e4e6ea]" />
          </div>

          <!-- Menú Colapsable de Administración -->
          <div v-if="isAdmin">
            <button
              @click="adminOpen = !adminOpen"
              class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-semibold transition-colors text-[#9ca3af] hover:text-[#4a5568] hover:bg-[#f7f8fc]"
            >
              <span class="text-[10px] uppercase tracking-widest font-bold">Administración</span>
              <ChevronDown :class="['w-3.5 h-3.5 transition-transform duration-200', adminOpen ? 'rotate-180' : '']" />
            </button>

            <div :class="['overflow-hidden transition-all duration-300 ease-in-out', adminOpen ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0']">
              <div class="pt-1 pl-1 space-y-2 pb-2">
                <div v-for="group in adminGroups" :key="group.name" class="space-y-0.5">
                  <button
                    @click="toggleGroup(group.name)"
                    class="w-full flex items-center justify-between text-[10px] uppercase font-bold text-[#9ca3af] tracking-wider px-3 py-1.5 mt-1 hover:text-[#1a1a2e] transition-colors rounded-md hover:bg-[#f8fafc]"
                  >
                    <span class="truncate">{{ group.name }}</span>
                    <ChevronDown :class="['w-3 h-3 transition-transform duration-200 shrink-0', expandedGroups[group.name] ? 'rotate-180' : '']" />
                  </button>

                  <div :class="['overflow-hidden transition-all duration-300 ease-in-out', expandedGroups[group.name] ? 'max-h-[600px] opacity-100' : 'max-h-0 opacity-0']">
                    <div class="space-y-0.5 pl-2 py-0.5">
                      <NuxtLink
                        v-for="sub in group.items"
                        :key="sub.path"
                        :to="sub.path"
                        :class="[
                          'flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs transition-all',
                          route.path === sub.path
                            ? 'bg-[#fff0ed] text-[#EB5F46] font-bold shadow-xs'
                            : 'text-[#4a5568] hover:bg-[#f7f8fc] hover:text-[#1a1a2e] font-medium'
                        ]"
                      >
                        <component :is="sub.icon" class="w-4 h-4 shrink-0" />
                        <span class="truncate leading-snug">{{ sub.name }}</span>
                      </NuxtLink>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </nav>

        <!-- Tarjeta de Usuario al Fondo (UX Pulida y Moderna) -->
        <div class="p-3 border-t border-[#e4e6ea] bg-white shrink-0">
          <div class="rounded-xl border border-slate-200/90 bg-slate-50/70 p-3 space-y-2.5 transition-all hover:border-slate-300 shadow-2xs">
            <!-- Fila de Identidad del Usuario -->
            <div class="flex items-center gap-3">
              <div class="relative shrink-0">
                <div class="w-10 h-10 rounded-full bg-gradient-to-br from-[#EB5F46] to-[#0D436C] flex items-center justify-center text-xs font-black text-white uppercase shadow-sm">
                  {{ userInitials }}
                </div>
                <span class="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white" title="Sesión activa"></span>
              </div>

              <div class="min-w-0 flex-1">
                <p class="text-xs font-bold text-slate-900 truncate leading-snug" :title="user.name">
                  {{ user.name }}
                </p>
                <div class="flex items-center gap-1.5 mt-0.5">
                  <button 
                    @click="showRolesModal = true; syncUserWithBackend()"
                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#FFF0ED] text-[#EB5F46] border border-[#FCD9D2] hover:bg-[#FDE2DC] transition-colors"
                    title="Ver detalles de roles asignados"
                  >
                    <span class="w-1.5 h-1.5 rounded-full bg-[#EB5F46]"></span>
                    <span>{{ primaryRoleLabel }}</span>
                    <span v-if="additionalRolesCount > 0" class="text-[9px] font-semibold text-[#EB5F46]/80">(+{{ additionalRolesCount }})</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- Botón de Cerrar Sesión estilizado -->
            <button 
              @click="handleLogout"
              class="w-full flex items-center justify-center gap-2 py-2 px-3 text-xs font-semibold text-slate-600 hover:text-red-600 bg-white hover:bg-red-50/80 border border-slate-200 hover:border-red-200 rounded-lg transition-all shadow-2xs group/logout"
            >
              <LogOut class="w-3.5 h-3.5 text-slate-400 group-hover/logout:text-red-600 transition-colors" />
              <span>Cerrar Sesión</span>
            </button>
          </div>
        </div>
      </aside>

      <!-- Área de Contenido de la Página -->
      <main class="flex-1 flex flex-col min-w-0 h-full overflow-y-auto">
        <div class="p-4 md:p-8 flex-grow">
          <NuxtPage />
        </div>
      </main>
    </div>
  </div>

  <!-- Global Overlay Loader para navegación o tareas asíncronas / IA / exportación -->
  <InstitutionalLoader
    v-if="globalLoader.isLoading.value || isPageNavigating"
    :title="globalLoader.isLoading.value ? globalLoader.title.value : 'Cargando módulo...'"
    :subtitle="globalLoader.isLoading.value ? globalLoader.subtitle.value : 'Sincronizando estado con la cadena de custodia...'"
    :phrases="globalLoader.phrases.value"
    :overlay="true"
  />
</template>

