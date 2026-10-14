<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import {
  Filter, Eye, ChevronRight, User, Search, ArrowUpDown, ArrowUp, ArrowDown,
  ChevronDown, X, FileText, Building2, SlidersHorizontal, GripVertical, Copy,
  Check, RotateCcw, ExternalLink
} from "lucide-vue-next";

const config = useRuntimeConfig();
const apiBase = config.public.apiBase;

import InstitutionalLoader from "~/components/common/InstitutionalLoader.vue";

interface Initiative {
  id: string;
  created_at: string;
  status: string;
  form_data: Record<string, any>;
  summary?: Record<string, any>;
  rejection_reason?: string;
  user_id?: string;
  current_node_id?: string;
}

type TabKey =
  | "todas"
  | "borrador"
  | "eval_bp"
  | "aprob_bo"
  | "aprob_vp"
  | "asig_demanda"
  | "estimacion"
  | "planificacion"
  | "observada"
  | "desestimada";

const TABS: { key: TabKey; label: string; dot: string }[] = [
  { key: "todas", label: "Todas", dot: "bg-[#4F5AF5]" },
  { key: "borrador", label: "Borrador", dot: "bg-slate-400" },
  { key: "eval_bp", label: "Evaluación BP TI", dot: "bg-indigo-500" },
  { key: "aprob_bo", label: "Aprobación BO", dot: "bg-blue-500" },
  { key: "aprob_vp", label: "Aprobación VP", dot: "bg-purple-500" },
  { key: "asig_demanda", label: "Asignación Líder TI", dot: "bg-cyan-500" },
  { key: "estimacion", label: "Estimación", dot: "bg-amber-500" },
  { key: "planificacion", label: "Planificación", dot: "bg-emerald-500" },
  { key: "observada", label: "Observadas", dot: "bg-rose-500" },
  { key: "desestimada", label: "Desestimadas", dot: "bg-slate-500" },
];

const STATUS_BADGE_STYLE: Record<TabKey, string> = {
  todas: "bg-slate-100 text-slate-700",
  borrador: "bg-slate-100 text-slate-600 border border-slate-200",
  eval_bp: "bg-indigo-50 text-indigo-700 border border-indigo-200",
  aprob_bo: "bg-blue-50 text-blue-700 border border-blue-200",
  aprob_vp: "bg-purple-50 text-purple-700 border border-purple-200",
  asig_demanda: "bg-cyan-50 text-cyan-700 border border-cyan-200",
  estimacion: "bg-amber-50 text-amber-700 border border-amber-200",
  planificacion: "bg-emerald-50 text-emerald-700 border border-emerald-200",
  observada: "bg-rose-50 text-rose-700 border border-rose-200",
  desestimada: "bg-slate-100 text-slate-600 border border-slate-200",
};

interface ColumnDef {
  id: string;
  label: string;
  defaultWidth: number;
  minWidth: number;
  canHide: boolean;
}

const ALL_COLUMNS: ColumnDef[] = [
  { id: "codigo", label: "Código ID", defaultWidth: 130, minWidth: 110, canHide: true },
  { id: "solicitud", label: "Solicitud", defaultWidth: 290, minWidth: 200, canHide: false },
  { id: "vicepresidencia", label: "Vicepresidencia", defaultWidth: 160, minWidth: 120, canHide: true },
  { id: "direccion", label: "Dirección", defaultWidth: 160, minWidth: 120, canHide: true },
  { id: "fecha", label: "Fecha", defaultWidth: 120, minWidth: 95, canHide: true },
  { id: "key_user", label: "Key User", defaultWidth: 170, minWidth: 130, canHide: true },
  { id: "bp", label: "BP TI", defaultWidth: 160, minWidth: 120, canHide: true },
  { id: "estado", label: "Estado Actual", defaultWidth: 320, minWidth: 240, canHide: true },
  { id: "acciones", label: "Acciones", defaultWidth: 160, minWidth: 150, canHide: false }
];

const DEFAULT_COLUMN_ORDER = ALL_COLUMNS.map(c => c.id);
const DEFAULT_COLUMN_WIDTHS: Record<string, number> = ALL_COLUMNS.reduce(
  (acc, c) => ({ ...acc, [c.id]: c.defaultWidth }),
  {}
);

// ─── State ───────────────────────────────────────────────────────────────────
const initiatives = ref<Initiative[]>([]);
const loading = ref(true);
const activeTab = ref<TabKey>("todas");
const showOnlyMine = ref(false);
const searchQuery = ref("");

// Filters
const selectedRegistradores = ref<string[]>([]);
const selectedDirecciones = ref<string[]>([]);
const selectedBPs = ref<string[]>([]);
const selectedVicepresidencias = ref<string[]>([]);

// Dropdowns in filter bar
const filterDropdownOpen = ref<string | null>(null);
const filterSearch = ref("");

const toggleFilterDropdown = (key: string) => {
  if (filterDropdownOpen.value === key) {
    filterDropdownOpen.value = null;
    filterSearch.value = "";
  } else {
    filterDropdownOpen.value = key;
    filterSearch.value = "";
  }
};

const closeFilterDropdowns = () => {
  filterDropdownOpen.value = null;
  filterSearch.value = "";
};

// Sort state
const sortConfig = ref<{
  field: "codigo" | "solicitud" | "vicepresidencia" | "direccion" | "fecha" | "key_user" | "bp" | "estado";
  order: "asc" | "desc";
} | null>(null);

// Column customization
const columnOrder = ref<string[]>([...DEFAULT_COLUMN_ORDER]);
const columnWidths = ref<Record<string, number>>({ ...DEFAULT_COLUMN_WIDTHS });
const hiddenColumns = ref<string[]>([]);
const columnsMenuOpen = ref(false);
const copiedId = ref<string | null>(null);

// Quick Preview Modal
const selectedInitiative = ref<Initiative | null>(null);

// Current user mock profile
const profile = ref({
  id: "admin-1",
  name: "Administrador IACS",
  role: "admin",
});

// ─── Helpers ─────────────────────────────────────────────────────────────────
function getInitiativeStatusInfo(i: any): { label: string; tabKey: TabKey } {
  const label = i?.status || "Sin estado";
  const lower = String(label).toLowerCase();

  let tabKey: TabKey = "eval_bp";
  if (lower.includes("desestimad")) tabKey = "desestimada";
  else if (lower.includes("observad")) tabKey = "observada";
  else if (lower.includes("borrador")) tabKey = "borrador";
  else if (lower.includes("bp ti") || lower.includes("pendiente de aprobación")) tabKey = "eval_bp";
  else if (lower.includes("bo") || lower.includes("patrocinio")) tabKey = "aprob_bo";
  else if (lower.includes("vp") || lower.includes("vicepresiden")) tabKey = "aprob_vp";
  else if (lower.includes("líder ti") || lower.includes("lider ti") || lower.includes("dominio") || lower.includes("demanda ti")) tabKey = "asig_demanda";
  else if (lower.includes("estimaci")) tabKey = "estimacion";
  else if (lower.includes("planificaci") || lower.includes("en demanda") || lower.includes("planificada")) tabKey = "planificacion";

  return { label, tabKey };
}

function formatDate(iso: string) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    const day = String(d.getDate()).padStart(2, "0");
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const year = d.getFullYear();
    return `${day}/${month}/${year}`;
  } catch {
    return iso;
  }
}

function formatTime(iso: string) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleTimeString("es-PE", {
      hour: "2-digit",
      minute: "2-digit"
    });
  } catch {
    return "";
  }
}

const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text);
  copiedId.value = text;
  setTimeout(() => (copiedId.value = null), 2000);
};

// ─── Load Data ───────────────────────────────────────────────────────────────
const loadData = async () => {
  loading.value = true;
  try {
    const data = await $fetch<Initiative[]>(`${apiBase}/initiatives`).catch(() => []);
    if (Array.isArray(data)) {
      initiatives.value = data.filter((i: any) => {
        if (i.status === "Chat pendiente") return false;
        const isBorrador = !i.status || i.status === "Borrador" || i.status === "1. Borrador" || i.current_node_id === "borrador";
        if (isBorrador) {
          const reached = Boolean(i.form_data?._reached_summary);
          const hasSum = Boolean(i.summary && typeof i.summary === "object" && Object.keys(i.summary).length > 0 && (i.summary.titulo || i.summary.objetivo));
          if (!reached && !hasSum) return false;
        }
        return true;
      });
    }
  } catch (e) {
    console.error("Error loading initiatives for board:", e);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadData();
});

// ─── Derived Options for Filters ─────────────────────────────────────────────
const vicepresidenciasOptions = computed(() => {
  const set = new Set<string>();
  initiatives.value.forEach(i => {
    const vp = i.form_data?.vicepresidencia;
    if (vp) set.add(vp);
  });
  return Array.from(set).sort().map(val => ({ label: val, value: val }));
});

const registradoresOptions = computed(() => {
  const set = new Set<string>();
  initiatives.value.forEach(i => {
    const r = i.form_data?.registrador || i.form_data?.solicitante;
    if (r) set.add(r);
  });
  return Array.from(set).sort().map(val => ({ label: val, value: val }));
});

const direccionesOptions = computed(() => {
  const set = new Set<string>();
  initiatives.value.forEach(i => {
    const d = i.form_data?.direccion;
    if (d) set.add(d);
  });
  return Array.from(set).sort().map(val => ({ label: val, value: val }));
});

const bpsOptions = computed(() => {
  const set = new Set<string>();
  initiatives.value.forEach(i => {
    const bp = i.form_data?.bp_ti_asignado;
    if (bp) set.add(bp);
  });
  return Array.from(set).sort().map(val => ({ label: val, value: val }));
});

// ─── Filtering ───────────────────────────────────────────────────────────────
const filteredInitiatives = computed(() => {
  return initiatives.value.filter(i => {
    if (showOnlyMine.value && (i.user_id !== profile.value.id && i.form_data?.registrador !== profile.value.name)) {
      return false;
    }
    if (selectedRegistradores.value.length > 0) {
      const r = i.form_data?.registrador || i.form_data?.solicitante;
      if (!r || !selectedRegistradores.value.includes(r)) return false;
    }
    if (selectedDirecciones.value.length > 0) {
      const d = i.form_data?.direccion;
      if (!d || !selectedDirecciones.value.includes(d)) return false;
    }
    if (selectedBPs.value.length > 0) {
      const bp = i.form_data?.bp_ti_asignado;
      if (!bp || !selectedBPs.value.includes(bp)) return false;
    }
    if (selectedVicepresidencias.value.length > 0) {
      const vp = i.form_data?.vicepresidencia;
      if (!vp || !selectedVicepresidencias.value.includes(vp)) return false;
    }
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.toLowerCase();
      const title = (i.summary?.titulo ?? Object.values(i.form_data ?? {})[0] ?? "").toString().toLowerCase();
      const obj = (i.form_data?.descripcion_de_la_necesidad ?? "").toString().toLowerCase();
      const id = i.id.toLowerCase();
      if (!title.includes(q) && !obj.includes(q) && !id.includes(q)) return false;
    }
    return true;
  });
});

const countByTab = (tabKey: TabKey) => {
  if (tabKey === "todas") return filteredInitiatives.value.length;
  return filteredInitiatives.value.filter(i => getInitiativeStatusInfo(i).tabKey === tabKey).length;
};

const byTab = computed(() => {
  if (activeTab.value === "todas") return filteredInitiatives.value;
  return filteredInitiatives.value.filter(i => getInitiativeStatusInfo(i).tabKey === activeTab.value);
});

// ─── Sorting ─────────────────────────────────────────────────────────────────
const sortedAndFiltered = computed(() => {
  if (!sortConfig.value) return byTab.value;

  return [...byTab.value].sort((a, b) => {
    let valA: any = "";
    let valB: any = "";

    switch (sortConfig.value!.field) {
      case "codigo":
        valA = a.id || "";
        valB = b.id || "";
        break;
      case "solicitud":
        valA = a.summary?.titulo ?? Object.values(a.form_data ?? {})[0] ?? a.id;
        valB = b.summary?.titulo ?? Object.values(b.form_data ?? {})[0] ?? b.id;
        break;
      case "vicepresidencia":
        valA = a.form_data?.vicepresidencia || "";
        valB = b.form_data?.vicepresidencia || "";
        break;
      case "direccion":
        valA = a.form_data?.direccion || "";
        valB = b.form_data?.direccion || "";
        break;
      case "fecha":
        valA = a.created_at || "";
        valB = b.created_at || "";
        break;
      case "key_user":
        valA = a.form_data?.registrador || a.form_data?.solicitante || "";
        valB = b.form_data?.registrador || b.form_data?.solicitante || "";
        break;
      case "bp":
        valA = a.form_data?.bp_ti_asignado || "";
        valB = b.form_data?.bp_ti_asignado || "";
        break;
      case "estado":
        valA = getInitiativeStatusInfo(a).label || "";
        valB = getInitiativeStatusInfo(b).label || "";
        break;
    }

    let comparison = 0;
    if (typeof valA === "string" && typeof valB === "string") {
      comparison = valA.localeCompare(valB, "es", { sensitivity: "base", numeric: true });
    } else {
      if (valA < valB) comparison = -1;
      if (valA > valB) comparison = 1;
    }

    return sortConfig.value!.order === "asc" ? comparison : -comparison;
  });
});

const handleSort = (field: "codigo" | "solicitud" | "vicepresidencia" | "direccion" | "fecha" | "key_user" | "bp" | "estado") => {
  if (sortConfig.value && sortConfig.value.field === field) {
    if (sortConfig.value.order === "asc") {
      sortConfig.value = { field, order: "desc" };
    } else {
      sortConfig.value = null;
    }
  } else {
    sortConfig.value = { field, order: "asc" };
  }
};

// ─── Column customizer ───────────────────────────────────────────────────────
const visibleColumns = computed(() => {
  return columnOrder.value.filter(id => !hiddenColumns.value.includes(id));
});

const totalTableWidth = computed(() => {
  return visibleColumns.value.reduce((acc, colId) => {
    const colDef = ALL_COLUMNS.find(c => c.id === colId);
    return acc + (columnWidths.value[colId] || colDef?.defaultWidth || 150);
  }, 0);
});

const handleToggleColumn = (colId: string) => {
  const colDef = ALL_COLUMNS.find(c => c.id === colId);
  if (!colDef?.canHide) return;
  if (hiddenColumns.value.includes(colId)) {
    hiddenColumns.value = hiddenColumns.value.filter(id => id !== colId);
  } else {
    hiddenColumns.value = [...hiddenColumns.value, colId];
  }
};

const handleResetColumns = () => {
  columnOrder.value = [...DEFAULT_COLUMN_ORDER];
  columnWidths.value = { ...DEFAULT_COLUMN_WIDTHS };
  hiddenColumns.value = [];
};

const clearAllFilters = () => {
  selectedRegistradores.value = [];
  selectedDirecciones.value = [];
  selectedBPs.value = [];
  selectedVicepresidencias.value = [];
  showOnlyMine.value = false;
  searchQuery.value = "";
};

const hasAnyFilterActive = computed(() => {
  return (
    selectedRegistradores.value.length > 0 ||
    selectedDirecciones.value.length > 0 ||
    selectedBPs.value.length > 0 ||
    selectedVicepresidencias.value.length > 0 ||
    showOnlyMine.value ||
    searchQuery.value !== ""
  );
});
</script>

<template>
  <div class="space-y-6" @click="closeFilterDropdowns">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-4">
      <div>
        <h2 class="text-2xl font-bold text-[#1E293B]">Bandeja de Revisión y Aprobación</h2>
        <p class="text-sm text-[#64748B]">Gestión, evaluación y seguimiento de solicitudes de necesidades de TI.</p>
      </div>
    </div>

    <!-- Top Filter Bar -->
    <div class="bg-white rounded-2xl border border-[#E2E8F0] p-4 space-y-3 shadow-sm" @click.stop>
      <div class="flex items-center justify-between flex-wrap gap-2 pb-2 border-b border-[#F1F5F9]">
        <h3 class="font-bold text-xs text-[#1E293B] uppercase tracking-wider flex items-center gap-1.5">
          <Filter class="w-4 h-4 text-[#4F5AF5]" />
          Filtros y Búsqueda
        </h3>
        <button
          v-if="hasAnyFilterActive"
          @click="clearAllFilters"
          class="text-xs font-semibold text-[#4F5AF5] hover:text-[#3F49E0] transition-colors"
        >
          Limpiar Todo
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-12 gap-2.5 items-center">
        <!-- Search query input -->
        <div class="relative md:col-span-4">
          <Search class="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Buscar por título, objetivo, ID..."
            v-model="searchQuery"
            class="w-full text-xs pl-9 pr-8 py-2.5 rounded-xl border border-[#E2E8F0] focus:border-[#4F5AF5] focus:ring-1 focus:ring-[#4F5AF5] focus:outline-none placeholder-[#94A3B8] bg-white font-medium"
          />
          <button
            v-if="searchQuery"
            type="button"
            @click="searchQuery = ''"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
          >
            <X class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- Solo mías button -->
        <button
          type="button"
          @click="showOnlyMine = !showOnlyMine"
          :class="[
            'md:col-span-2 flex items-center justify-center gap-1.5 px-3 py-2.5 text-xs font-semibold rounded-xl border transition-all cursor-pointer',
            showOnlyMine
              ? 'bg-[#EEF2FF] text-[#4F5AF5] border-[#4F5AF5] shadow-xs'
              : 'bg-white text-[#1E293B] border-[#E2E8F0] hover:bg-[#F8FAFC]'
          ]"
        >
          <User class="w-3.5 h-3.5 shrink-0" />
          <span class="truncate">Ver solo mías</span>
        </button>

        <!-- Dropdowns VP, Key user, Dirección, BP TI -->
        <div class="md:col-span-6 grid grid-cols-2 sm:grid-cols-4 gap-2">
          <!-- Vicepresidencia -->
          <div class="relative">
            <button
              type="button"
              @click.stop="toggleFilterDropdown('vp')"
              :class="[
                'w-full flex items-center justify-between gap-1.5 px-3 py-2.5 text-xs font-semibold rounded-xl border transition-all',
                selectedVicepresidencias.length > 0 ? 'bg-[#EEF2FF] text-[#4F5AF5] border-[#4F5AF5] shadow-xs' : 'bg-white text-[#1E293B] border-[#E2E8F0] hover:bg-[#F8FAFC]'
              ]"
            >
              <span class="truncate">Vicepresidencia</span>
              <div class="flex items-center gap-1 shrink-0">
                <span v-if="selectedVicepresidencias.length > 0" class="bg-[#4F5AF5] text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full leading-none">
                  {{ selectedVicepresidencias.length }}
                </span>
                <ChevronDown :class="['w-3.5 h-3.5 text-slate-400 transition-transform', filterDropdownOpen === 'vp' ? 'rotate-180 text-[#4F5AF5]' : '']" />
              </div>
            </button>
            <div v-if="filterDropdownOpen === 'vp'" class="absolute left-0 mt-1.5 w-64 bg-white rounded-xl border border-[#E2E8F0] shadow-xl z-50 p-2.5 space-y-2 animate-in fade-in duration-150">
              <div class="max-h-48 overflow-y-auto space-y-0.5 pr-1">
                <label v-for="opt in vicepresidenciasOptions" :key="opt.value" class="flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs hover:bg-[#F8FAFC] cursor-pointer text-[#1E293B]">
                  <input
                    type="checkbox"
                    :checked="selectedVicepresidencias.includes(opt.value)"
                    @change="selectedVicepresidencias.includes(opt.value) ? selectedVicepresidencias = selectedVicepresidencias.filter(x => x !== opt.value) : selectedVicepresidencias = [...selectedVicepresidencias, opt.value]"
                    class="rounded border-slate-300 text-[#4F5AF5] focus:ring-[#4F5AF5]"
                  />
                  <span class="truncate">{{ opt.label }}</span>
                </label>
              </div>
            </div>
          </div>

          <!-- Key User -->
          <div class="relative">
            <button
              type="button"
              @click.stop="toggleFilterDropdown('key_user')"
              :class="[
                'w-full flex items-center justify-between gap-1.5 px-3 py-2.5 text-xs font-semibold rounded-xl border transition-all',
                selectedRegistradores.length > 0 ? 'bg-[#EEF2FF] text-[#4F5AF5] border-[#4F5AF5] shadow-xs' : 'bg-white text-[#1E293B] border-[#E2E8F0] hover:bg-[#F8FAFC]'
              ]"
            >
              <span class="truncate">Key user</span>
              <div class="flex items-center gap-1 shrink-0">
                <span v-if="selectedRegistradores.length > 0" class="bg-[#4F5AF5] text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full leading-none">
                  {{ selectedRegistradores.length }}
                </span>
                <ChevronDown :class="['w-3.5 h-3.5 text-slate-400 transition-transform', filterDropdownOpen === 'key_user' ? 'rotate-180 text-[#4F5AF5]' : '']" />
              </div>
            </button>
            <div v-if="filterDropdownOpen === 'key_user'" class="absolute left-0 mt-1.5 w-64 bg-white rounded-xl border border-[#E2E8F0] shadow-xl z-50 p-2.5 space-y-2 animate-in fade-in duration-150">
              <div class="max-h-48 overflow-y-auto space-y-0.5 pr-1">
                <label v-for="opt in registradoresOptions" :key="opt.value" class="flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs hover:bg-[#F8FAFC] cursor-pointer text-[#1E293B]">
                  <input
                    type="checkbox"
                    :checked="selectedRegistradores.includes(opt.value)"
                    @change="selectedRegistradores.includes(opt.value) ? selectedRegistradores = selectedRegistradores.filter(x => x !== opt.value) : selectedRegistradores = [...selectedRegistradores, opt.value]"
                    class="rounded border-slate-300 text-[#4F5AF5] focus:ring-[#4F5AF5]"
                  />
                  <span class="truncate">{{ opt.label }}</span>
                </label>
              </div>
            </div>
          </div>

          <!-- Dirección -->
          <div class="relative">
            <button
              type="button"
              @click.stop="toggleFilterDropdown('dir')"
              :class="[
                'w-full flex items-center justify-between gap-1.5 px-3 py-2.5 text-xs font-semibold rounded-xl border transition-all',
                selectedDirecciones.length > 0 ? 'bg-[#EEF2FF] text-[#4F5AF5] border-[#4F5AF5] shadow-xs' : 'bg-white text-[#1E293B] border-[#E2E8F0] hover:bg-[#F8FAFC]'
              ]"
            >
              <span class="truncate">Dirección</span>
              <div class="flex items-center gap-1 shrink-0">
                <span v-if="selectedDirecciones.length > 0" class="bg-[#4F5AF5] text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full leading-none">
                  {{ selectedDirecciones.length }}
                </span>
                <ChevronDown :class="['w-3.5 h-3.5 text-slate-400 transition-transform', filterDropdownOpen === 'dir' ? 'rotate-180 text-[#4F5AF5]' : '']" />
              </div>
            </button>
            <div v-if="filterDropdownOpen === 'dir'" class="absolute left-0 mt-1.5 w-64 bg-white rounded-xl border border-[#E2E8F0] shadow-xl z-50 p-2.5 space-y-2 animate-in fade-in duration-150">
              <div class="max-h-48 overflow-y-auto space-y-0.5 pr-1">
                <label v-for="opt in direccionesOptions" :key="opt.value" class="flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs hover:bg-[#F8FAFC] cursor-pointer text-[#1E293B]">
                  <input
                    type="checkbox"
                    :checked="selectedDirecciones.includes(opt.value)"
                    @change="selectedDirecciones.includes(opt.value) ? selectedDirecciones = selectedDirecciones.filter(x => x !== opt.value) : selectedDirecciones = [...selectedDirecciones, opt.value]"
                    class="rounded border-slate-300 text-[#4F5AF5] focus:ring-[#4F5AF5]"
                  />
                  <span class="truncate">{{ opt.label }}</span>
                </label>
              </div>
            </div>
          </div>

          <!-- BP TI -->
          <div class="relative">
            <button
              type="button"
              @click.stop="toggleFilterDropdown('bpti')"
              :class="[
                'w-full flex items-center justify-between gap-1.5 px-3 py-2.5 text-xs font-semibold rounded-xl border transition-all',
                selectedBPs.length > 0 ? 'bg-[#EEF2FF] text-[#4F5AF5] border-[#4F5AF5] shadow-xs' : 'bg-white text-[#1E293B] border-[#E2E8F0] hover:bg-[#F8FAFC]'
              ]"
            >
              <span class="truncate">BP TI</span>
              <div class="flex items-center gap-1 shrink-0">
                <span v-if="selectedBPs.length > 0" class="bg-[#4F5AF5] text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full leading-none">
                  {{ selectedBPs.length }}
                </span>
                <ChevronDown :class="['w-3.5 h-3.5 text-slate-400 transition-transform', filterDropdownOpen === 'bpti' ? 'rotate-180 text-[#4F5AF5]' : '']" />
              </div>
            </button>
            <div v-if="filterDropdownOpen === 'bpti'" class="absolute left-0 mt-1.5 w-64 bg-white rounded-xl border border-[#E2E8F0] shadow-xl z-50 p-2.5 space-y-2 animate-in fade-in duration-150">
              <div class="max-h-48 overflow-y-auto space-y-0.5 pr-1">
                <label v-for="opt in bpsOptions" :key="opt.value" class="flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs hover:bg-[#F8FAFC] cursor-pointer text-[#1E293B]">
                  <input
                    type="checkbox"
                    :checked="selectedBPs.includes(opt.value)"
                    @change="selectedBPs.includes(opt.value) ? selectedBPs = selectedBPs.filter(x => x !== opt.value) : selectedBPs = [...selectedBPs, opt.value]"
                    class="rounded border-slate-300 text-[#4F5AF5] focus:ring-[#4F5AF5]"
                  />
                  <span class="truncate">{{ opt.label }}</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Board Table -->
    <div class="bg-white rounded-2xl border border-[#E2E8F0] shadow-sm relative">
      <!-- Tabs Navigation & Column Customizer -->
      <div class="border-b border-[#F1F5F9] px-6 pt-4 flex items-center justify-between gap-3 flex-wrap rounded-t-2xl bg-white relative z-20">
        <div class="flex gap-1 overflow-x-auto pb-1 sm:pb-0">
          <button
            v-for="tab in TABS"
            :key="tab.key"
            @click="activeTab = tab.key"
            :class="[
              'pb-3 px-4 text-xs font-semibold border-b-2 flex items-center gap-2 transition-all whitespace-nowrap cursor-pointer',
              activeTab === tab.key
                ? 'border-[#4F5AF5] text-[#4F5AF5]'
                : 'border-transparent text-[#64748B] hover:text-[#1E293B]'
            ]"
          >
            <span>{{ tab.label }}</span>
            <span
              :class="[
                'text-[10px] px-1.5 py-0.5 rounded-full font-bold',
                activeTab === tab.key
                  ? 'bg-[#EEF2FF] text-[#4F5AF5]'
                  : 'bg-[#F1F5F9] text-[#64748B]'
              ]"
            >
              {{ countByTab(tab.key) }}
            </span>
          </button>
        </div>

        <!-- Column Customizer Menu -->
        <div class="relative mb-2.5 sm:mb-2">
          <button
            type="button"
            @click="columnsMenuOpen = !columnsMenuOpen"
            class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border border-[#E2E8F0] bg-white hover:bg-[#F8FAFC] text-[#1E293B] shadow-xs transition-colors cursor-pointer"
          >
            <SlidersHorizontal class="w-3.5 h-3.5 text-[#4F5AF5]" />
            <span>Columnas</span>
            <span class="text-[10px] font-bold bg-[#EEF2FF] text-[#4F5AF5] px-1.5 py-0.5 rounded-full">
              {{ visibleColumns.length }}/{{ ALL_COLUMNS.length }}
            </span>
            <ChevronDown :class="['w-3 h-3 text-slate-400 transition-transform', columnsMenuOpen ? 'rotate-180' : '']" />
          </button>

          <div v-if="columnsMenuOpen" class="absolute right-0 top-full mt-2 w-72 bg-white rounded-xl border border-[#E2E8F0] shadow-2xl z-50 p-3 space-y-2.5 animate-in fade-in duration-150">
            <div class="flex items-center justify-between border-b border-[#F1F5F9] pb-2">
              <div>
                <h4 class="text-xs font-bold text-[#1E293B]">Columnas de la tabla</h4>
                <p class="text-[10px] text-slate-400">Marca las visibles</p>
              </div>
              <button
                type="button"
                @click="handleResetColumns"
                class="text-[11px] font-medium text-slate-500 hover:text-[#4F5AF5] flex items-center gap-1 transition-colors"
              >
                <RotateCcw class="w-3 h-3" />
                Reset
              </button>
            </div>
            <div class="max-h-72 overflow-y-auto space-y-1 pr-1">
              <div v-for="col in ALL_COLUMNS" :key="col.id" class="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-[#F8FAFC] text-xs">
                <label class="flex items-center gap-2 cursor-pointer select-none min-w-0 flex-1">
                  <input
                    type="checkbox"
                    :checked="!hiddenColumns.includes(col.id)"
                    :disabled="!col.canHide"
                    @change="handleToggleColumn(col.id)"
                    class="rounded border-slate-300 text-[#4F5AF5] focus:ring-[#4F5AF5] w-3.5 h-3.5 cursor-pointer disabled:opacity-50"
                  />
                  <span :class="['truncate font-medium', !hiddenColumns.includes(col.id) ? 'text-slate-800' : 'text-slate-400 line-through']">
                    {{ col.label }}
                  </span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Table Content -->
      <div class="p-0 overflow-x-auto rounded-b-2xl">
        <div v-if="loading" class="py-16 bg-white rounded-b-2xl flex items-center justify-center">
          <InstitutionalLoader 
            title="Cargando Bandeja de Iniciativas" 
            subtitle="Sincronizando expedientes y dictámenes de la cartera..."
            :phrases="[
              'Consultando iniciativas en base de datos PostgreSQL 17...',
              'Verificando autorizaciones y roles operativos...',
              'Calculando filtros y agrupaciones por etapa...',
              'Sincronizando estado con la cadena de custodia...'
            ]"
          />
        </div>
        <div v-else-if="sortedAndFiltered.length === 0" class="p-12 text-center text-[#64748B] text-sm">

          No hay solicitudes en esta sección.
        </div>
        <table v-else class="w-full text-left border-collapse table-fixed" :style="{ minWidth: `${Math.max(totalTableWidth, 1200)}px` }">
          <thead>
            <tr class="border-b border-[#F1F5F9] bg-[#F8FAFC] text-[11px] font-bold text-[#64748B] uppercase tracking-wider relative">
              <th
                v-for="colId in visibleColumns"
                :key="colId"
                :style="{ width: `${columnWidths[colId] || 150}px` }"
                :class="[
                  'px-4 py-3 select-none relative',
                  colId === 'acciones' ? 'sticky right-0 bg-[#F8FAFC] z-20 shadow-[-4px_0_8px_-2px_rgba(0,0,0,0.06)]' : ''
                ]"
              >
                <div
                  @click="colId !== 'acciones' && handleSort(colId as any)"
                  :class="['flex items-center gap-1.5 min-w-0', colId !== 'acciones' ? 'cursor-pointer hover:text-[#4F5AF5]' : '']"
                >
                  <span class="truncate">{{ ALL_COLUMNS.find(c => c.id === colId)?.label }}</span>
                  <component
                    v-if="colId !== 'acciones' && sortConfig?.field === colId"
                    :is="sortConfig.order === 'asc' ? ArrowUp : ArrowDown"
                    class="w-3 h-3 text-[#4F5AF5] shrink-0"
                  />
                  <ArrowUpDown v-else-if="colId !== 'acciones'" class="w-3 h-3 text-slate-300 shrink-0" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[#F1F5F9]">
            <tr v-for="i in sortedAndFiltered" :key="i.id" class="hover:bg-[#F8FAFC] transition-colors group">
              <td v-for="colId in visibleColumns" :key="colId" class="px-4 py-4">
                <!-- Código ID -->
                <div v-if="colId === 'codigo'" class="flex items-center gap-1.5 whitespace-nowrap">
                  <span class="text-[11px] font-mono font-semibold text-[#4F5AF5] bg-[#EEF2FF] px-2 py-1 rounded-md border border-[#4F5AF5]/20">
                    #{{ i.summary?.id_corta || i.id.slice(0, 8) }}
                  </span>
                  <button
                    type="button"
                    @click="copyToClipboard(i.id)"
                    class="p-1 text-slate-400 hover:text-[#4F5AF5] hover:bg-slate-100 rounded transition-colors"
                    title="Copiar ID Completo"
                  >
                    <Check v-if="copiedId === i.id" class="w-3.5 h-3.5 text-emerald-600" />
                    <Copy v-else class="w-3.5 h-3.5" />
                  </button>
                </div>

                <!-- Solicitud -->
                <div v-else-if="colId === 'solicitud'">
                  <NuxtLink
                    :to="i.status === 'Borrador' ? `/nueva/${i.id}` : `/iniciativa/${i.id}`"
                    class="font-semibold text-[#1E293B] hover:text-[#4F5AF5] text-sm leading-snug line-clamp-2 transition-colors block"
                  >
                    {{ i.summary?.titulo || i.form_data?.titulo || Object.values(i.form_data ?? {})[0] || i.id }}
                  </NuxtLink>
                </div>

                <!-- Vicepresidencia -->
                <div v-else-if="colId === 'vicepresidencia'">
                  <span v-if="i.form_data?.vicepresidencia" class="text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-100/70 px-2.5 py-1 rounded-md inline-block max-w-[170px] truncate" :title="i.form_data.vicepresidencia">
                    {{ i.form_data.vicepresidencia }}
                  </span>
                  <span v-else class="text-xs text-slate-400 italic">-</span>
                </div>

                <!-- Dirección -->
                <div v-else-if="colId === 'direccion'">
                  <span v-if="i.form_data?.direccion" class="text-xs font-medium text-slate-700 bg-slate-100 border border-slate-200/70 px-2.5 py-1 rounded-md inline-block max-w-[170px] truncate" :title="i.form_data.direccion">
                    {{ i.form_data.direccion }}
                  </span>
                  <span v-else class="text-xs text-slate-400 italic">-</span>
                </div>

                <!-- Fecha -->
                <div v-else-if="colId === 'fecha'" class="whitespace-nowrap">
                  <p class="text-sm text-[#1E293B] font-medium">{{ formatDate(i.created_at) }}</p>
                  <p class="text-[11px] text-[#94A3B8]">{{ formatTime(i.created_at) }}</p>
                </div>

                <!-- Key user -->
                <div v-else-if="colId === 'key_user'">
                  <div class="flex items-center gap-2">
                    <div class="w-7 h-7 rounded-full bg-gradient-to-br from-[#4F5AF5] to-violet-500 flex items-center justify-center text-[10px] font-bold text-white shrink-0 uppercase">
                      {{ (i.form_data?.registrador || i.form_data?.solicitante || 'US').substring(0, 2).toUpperCase() }}
                    </div>
                    <div class="min-w-0">
                      <p class="text-sm text-[#1E293B] font-medium truncate">{{ i.form_data?.registrador || i.form_data?.solicitante || 'Sin registrador' }}</p>
                      <p v-if="i.form_data?.institucion" class="text-[10px] text-slate-400 font-semibold">{{ i.form_data.institucion }}</p>
                    </div>
                  </div>
                </div>

                <!-- BP TI -->
                <div v-else-if="colId === 'bp'">
                  <span :class="['text-xs font-semibold', i.form_data?.bp_ti_asignado ? 'text-slate-800' : 'text-amber-600']">
                    {{ i.form_data?.bp_ti_asignado || 'Sin asignar' }}
                  </span>
                </div>

                <!-- Estado -->
                <div v-else-if="colId === 'estado'">
                  <span
                    :class="[
                      'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold',
                      STATUS_BADGE_STYLE[getInitiativeStatusInfo(i).tabKey] || 'bg-slate-100 text-slate-600'
                    ]"
                  >
                    <span class="w-2 h-2 rounded-full bg-current" />
                    {{ getInitiativeStatusInfo(i).label }}
                  </span>
                </div>

                <!-- Acciones -->
                <div v-else-if="colId === 'acciones'" class="sticky right-0 bg-white group-hover:bg-[#F8FAFC] z-20 flex items-center gap-2 whitespace-nowrap shadow-[-4px_0_8px_-2px_rgba(0,0,0,0.06)]">
                  <button
                    type="button"
                    @click="selectedInitiative = i"
                    class="p-1.5 text-slate-500 hover:text-[#4F5AF5] hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                    title="Vista previa rápida"
                  >
                    <Eye class="w-4 h-4" />
                  </button>
                  <NuxtLink
                    :to="i.status === 'Borrador' ? `/nueva/${i.id}` : `/iniciativa/${i.id}`"
                    class="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#4F5AF5] hover:bg-[#3F49E0] text-xs font-semibold text-white transition-colors cursor-pointer shadow-2xs"
                  >
                    {{ i.status === 'Borrador' ? 'Editar' : 'Abrir' }}
                    <ExternalLink class="w-3 h-3" />
                  </NuxtLink>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Quick Preview Modal -->
    <div v-if="selectedInitiative" class="fixed inset-0 z-[200] flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" @click="selectedInitiative = null" />
      <div class="relative bg-white rounded-2xl shadow-2xl border border-[#E2E8F0] w-full max-w-2xl max-h-[88vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div class="px-6 py-4 border-b border-[#F1F5F9] flex items-start justify-between gap-4 shrink-0 bg-gradient-to-r from-slate-50 to-white">
          <div class="min-w-0">
            <span class="text-xs font-semibold text-[#4F5AF5] bg-[#EEF2FF] px-2 py-0.5 rounded-md mb-1 inline-block">
              {{ getInitiativeStatusInfo(selectedInitiative).label }}
            </span>
            <h3 class="text-base font-bold text-[#1E293B] leading-snug line-clamp-2">
              {{ selectedInitiative.summary?.titulo || selectedInitiative.form_data?.titulo || selectedInitiative.id }}
            </h3>
          </div>
          <button @click="selectedInitiative = null" class="w-8 h-8 rounded-lg border border-[#E2E8F0] flex items-center justify-center text-[#94A3B8] hover:bg-[#F1F5F9]">
            <X class="w-4 h-4" />
          </button>
        </div>
        <div class="overflow-y-auto flex-1 p-6 space-y-4 text-sm text-slate-700">
          <div class="grid grid-cols-2 gap-3 bg-slate-50 p-4 rounded-xl">
            <div><strong>VP:</strong> {{ selectedInitiative.form_data?.vicepresidencia || '—' }}</div>
            <div><strong>Dirección:</strong> {{ selectedInitiative.form_data?.direccion || '—' }}</div>
            <div><strong>Key user:</strong> {{ selectedInitiative.form_data?.registrador || '—' }}</div>
            <div><strong>BP TI:</strong> {{ selectedInitiative.form_data?.bp_ti_asignado || '—' }}</div>
          </div>
          <div v-if="selectedInitiative.summary?.objetivo">
            <h4 class="font-bold text-xs uppercase tracking-wider text-slate-500 mb-1">Objetivo</h4>
            <p class="bg-indigo-50/50 p-3 rounded-xl border border-indigo-100 text-slate-800">{{ selectedInitiative.summary.objetivo }}</p>
          </div>
        </div>
        <div class="px-6 py-4 border-t border-[#F1F5F9] bg-[#F8FAFC] flex justify-end">
          <NuxtLink
            :to="selectedInitiative.status === 'Borrador' ? `/nueva/${selectedInitiative.id}` : `/iniciativa/${selectedInitiative.id}`"
            class="bg-[#4F5AF5] text-white px-4 py-2 rounded-xl text-xs font-semibold"
          >
            Abrir Expediente Completo
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>
