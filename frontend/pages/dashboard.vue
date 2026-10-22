<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import {
  Activity, CheckCircle, Clock, TrendingUp, Ban, AlertTriangle,
  FileText, Filter, X, ChevronRight, ChevronLeft, ChevronDown, ChevronUp,
  ExternalLink, Building2, Users, BarChart3,
  Search, RefreshCw, Eye, Briefcase, Layers, UserCheck,
  FolderKanban, LayoutGrid, Sparkles
} from "lucide-vue-next";

const config = useRuntimeConfig();
const apiBase = config.public.apiBase;

import InstitutionalLoader from "~/components/common/InstitutionalLoader.vue";


// ─── Interfaces ──────────────────────────────────────────────────────────────
interface VP {
  id: string;
  name: string;
  bp_name: string | null;
}

interface Direccion {
  id: string;
  name: string;
  vp_id: string;
}

interface Initiative {
  id: string;
  created_at: string;
  status: string;
  form_data: Record<string, any>;
  summary?: Record<string, any>;
  rejection_reason?: string;
  current_node_id?: string;
}

type PerspectiveTab = "vp" | "direccion" | "bpti" | "ld" | "estado" | "tabla";

// ─── Constants ───────────────────────────────────────────────────────────────
const ALL_STATUSES = [
  "Borrador",
  "Pendiente de aprobación",
  "Observada",
  "Desestimada",
  "En demanda",
];

const STATUS_CONFIG: Record<string, { color: string; bg: string; bar: string; dot: string; border: string }> = {
  "Borrador":                 { color: "text-slate-600",   bg: "bg-slate-100",  bar: "bg-slate-400",   dot: "bg-slate-400",   border: "border-slate-200" },
  "Pendiente de aprobación":  { color: "text-[#4F5AF5]",   bg: "bg-[#EEF2FF]", bar: "bg-[#4F5AF5]",   dot: "bg-[#4F5AF5]",   border: "border-[#C7D2FE]" },
  "Observada":                { color: "text-amber-700",   bg: "bg-amber-50",   bar: "bg-amber-500",   dot: "bg-amber-500",   border: "border-amber-200" },
  "Desestimada":              { color: "text-red-700",     bg: "bg-red-50",     bar: "bg-red-500",     dot: "bg-red-500",     border: "border-red-200" },
  "En demanda":               { color: "text-emerald-700", bg: "bg-emerald-50", bar: "bg-emerald-500", dot: "bg-emerald-500", border: "border-emerald-200" },
};

const PAGE_SIZE = 10;

// ─── Helpers ─────────────────────────────────────────────────────────────────
function getTitle(initiative: Initiative): string {
  return (
    initiative.summary?.titulo ||
    initiative.form_data?.titulo ||
    Object.values(initiative.form_data ?? {})[0] ||
    initiative.id
  );
}

function getBPTI(initiative: Initiative): string {
  const fd = initiative.form_data ?? {};
  return (
    fd.bp_ti_asignado ||
    fd.bp_ti_responsable ||
    fd.business_partner ||
    fd.bp_ti ||
    fd.bp ||
    ""
  );
}

function getLD(initiative: Initiative): string {
  const fd = initiative.form_data ?? {};
  return (
    fd.lider_de_dominio_responsable ||
    fd.lider_dominio ||
    fd.ld_asignado ||
    fd.lider_de_dominio ||
    ""
  );
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

// ─── State ───────────────────────────────────────────────────────────────────
const initiatives = ref<Initiative[]>([]);
const vps = ref<VP[]>([]);
const direcciones = ref<Direccion[]>([]);
const loading = ref(true);

const activeTab = ref<PerspectiveTab>("vp");
const expandedGroup = ref<string | null>(null);

// Filters
const filterBP = ref<string[]>([]);
const filterVP = ref<string[]>([]);
const filterDir = ref<string[]>([]);
const filterBPTI = ref<string[]>([]);
const filterLD = ref<string[]>([]);
const filterStatus = ref<string[]>([]);
const searchText = ref("");

// Pagination for Table view
const page = ref(1);

// Detail Modal
const selectedInitiative = ref<Initiative | null>(null);

// Open dropdowns in filter bar
const openDropdown = ref<string | null>(null);

const toggleDropdown = (key: string) => {
  openDropdown.value = openDropdown.value === key ? null : key;
};

const closeDropdowns = () => {
  openDropdown.value = null;
};

// Current user profile
const currentUser = ref({
  id: "admin-1",
  name: "Administrador General",
  email: "admin@iacs.empresa.com",
  roles: ["admin"] as string[],
});

// ─── Load Data ───────────────────────────────────────────────────────────────
const loadData = async () => {
  loading.value = true;
  try {
    const [initRes, vpRes, dirRes] = await Promise.all([
      $fetch<Initiative[]>(`${apiBase}/initiatives`).catch(() => []),
      $fetch<VP[]>(`${apiBase}/admin/estructura/vps`).catch(() => $fetch<VP[]>(`${apiBase}/vps`).catch(() => [])),
      $fetch<Direccion[]>(`${apiBase}/admin/estructura/direcciones`).catch(() => $fetch<Direccion[]>(`${apiBase}/direcciones`).catch(() => [])),
    ]);

    if (Array.isArray(initRes)) {
      initiatives.value = initRes.filter((i: any) => {
        if (i.status === "Chat pendiente") return false;
        const isBorrador = !i.status || i.status === "Borrador" || i.status === "1. Borrador" || i.current_node_id === "borrador";
        if (isBorrador) {
          // REGLA: Las iniciativas en estado borrador solo las puede visualizar el registrador de la misma
          const isMine = Boolean(
            (currentUser.value.id && i.user_id === currentUser.value.id) ||
            (currentUser.value.email && (i.form_data?.registrador_email === currentUser.value.email)) ||
            (currentUser.value.name && (i.form_data?.registrador === currentUser.value.name || i.form_data?.solicitante === currentUser.value.name))
          );
          if (!isMine) return false;

          const reached = Boolean(i.form_data?._reached_summary);
          const hasSum = Boolean(i.summary && typeof i.summary === "object" && Object.keys(i.summary).length > 0 && (i.summary.titulo || i.summary.objetivo));
          if (!reached && !hasSum) return false;
        }
        return true;
      });
    }
    if (Array.isArray(vpRes)) vps.value = vpRes;
    if (Array.isArray(dirRes)) direcciones.value = dirRes;
  } catch (e) {
    console.error("Error loading dashboard data:", e);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  if (process.client) {
    const saved = localStorage.getItem('iacs_user');
    if (saved) {
      try {
        const u = JSON.parse(saved);
        currentUser.value = {
          id: u.id || currentUser.value.id,
          name: u.name || currentUser.value.name,
          email: u.email || currentUser.value.email,
          roles: u.roles || [u.role || 'admin'],
        };
      } catch (e) {}
    }
  }
  loadData();
});

// ─── Derived Filter Options ──────────────────────────────────────────────────
const bpOptions = computed(() => {
  const names = initiatives.value.map(ini => {
    const vpName = ini.form_data?.vicepresidencia;
    const vp = vps.value.find(v => v.name === vpName);
    return vp?.bp_name;
  }).filter(Boolean) as string[];
  return Array.from(new Set(names)).sort();
});

const vpOptions = computed(() => {
  const names = initiatives.value.map(ini => ini.form_data?.vicepresidencia).filter(Boolean) as string[];
  return Array.from(new Set(names)).sort();
});

const dirOptions = computed(() => {
  const names = initiatives.value.map(ini => ini.form_data?.direccion).filter(Boolean) as string[];
  return Array.from(new Set(names)).sort();
});

const bpTiOptions = computed(() => {
  const names = initiatives.value.map(i => getBPTI(i)).filter(Boolean) as string[];
  const list = Array.from(new Set(names)).sort();
  if (initiatives.value.some(i => !getBPTI(i))) {
    list.push("Sin asignar");
  }
  return list;
});

const ldOptions = computed(() => {
  const names = initiatives.value.map(i => getLD(i)).filter(Boolean) as string[];
  const list = Array.from(new Set(names)).sort();
  if (initiatives.value.some(i => !getLD(i))) {
    list.push("Sin asignar");
  }
  return list;
});

const statusOptions = computed(() => {
  const statuses = initiatives.value.map(i => i.status).filter(Boolean) as string[];
  return Array.from(new Set(statuses)).sort();
});

const hasActiveFilters = computed(() => {
  return (
    filterBP.value.length > 0 ||
    filterVP.value.length > 0 ||
    filterDir.value.length > 0 ||
    filterBPTI.value.length > 0 ||
    filterLD.value.length > 0 ||
    filterStatus.value.length > 0 ||
    searchText.value.trim() !== ""
  );
});

const clearFilters = () => {
  filterBP.value = [];
  filterVP.value = [];
  filterDir.value = [];
  filterBPTI.value = [];
  filterLD.value = [];
  filterStatus.value = [];
  searchText.value = "";
  page.value = 1;
};

// ─── Filtered Initiatives ────────────────────────────────────────────────────
const filtered = computed(() => {
  return initiatives.value.filter(ini => {
    const fd = ini.form_data ?? {};
    const vpName = fd.vicepresidencia ?? "";
    const dirName = fd.direccion ?? "";
    const bpTi = getBPTI(ini);
    const ld = getLD(ini);

    if (filterBP.value.length > 0) {
      const vp = vps.value.find(v => v.name === vpName);
      const bpName = vp?.bp_name ?? "";
      if (!filterBP.value.includes(bpName)) return false;
    }
    if (filterVP.value.length > 0) {
      if (!filterVP.value.includes(vpName)) return false;
    }
    if (filterDir.value.length > 0) {
      if (!filterDir.value.includes(dirName)) return false;
    }
    if (filterBPTI.value.length > 0) {
      if (!bpTi) {
        if (!filterBPTI.value.includes("Sin asignar")) return false;
      } else {
        if (!filterBPTI.value.includes(bpTi)) return false;
      }
    }
    if (filterLD.value.length > 0) {
      if (!ld) {
        if (!filterLD.value.includes("Sin asignar")) return false;
      } else {
        if (!filterLD.value.includes(ld)) return false;
      }
    }
    if (filterStatus.value.length > 0) {
      if (!filterStatus.value.includes(ini.status)) return false;
    }
    if (searchText.value.trim()) {
      const q = searchText.value.toLowerCase();
      const title = getTitle(ini).toLowerCase();
      if (
        !title.includes(q) &&
        !ini.id.toLowerCase().includes(q) &&
        !vpName.toLowerCase().includes(q) &&
        !dirName.toLowerCase().includes(q) &&
        !bpTi.toLowerCase().includes(q) &&
        !ld.toLowerCase().includes(q)
      ) {
        return false;
      }
    }
    return true;
  });
});

// ─── Global KPIs ─────────────────────────────────────────────────────────────
const kpis = computed(() => {
  const counts: Record<string, number> = {};
  ALL_STATUSES.forEach(s => { counts[s] = 0; });
  filtered.value.forEach(i => {
    if (counts[i.status] !== undefined) counts[i.status]++;
  });
  return {
    total: filtered.value.length,
    enDemanda: counts["En demanda"] ?? 0,
    pendientes: counts["Pendiente de aprobación"] ?? 0,
    observadas: counts["Observada"] ?? 0,
    desestimadas: counts["Desestimada"] ?? 0,
    borradores: counts["Borrador"] ?? 0,
  };
});

const kpiCards = computed(() => [
  {
    label: "Total Iniciativas", value: kpis.value.total, icon: Activity,
    color: "text-[#4F5AF5]", bg: "bg-[#EEF2FF]", border: "border-[#C7D2FE]",
    gradient: "from-[#4F5AF5]/10 to-transparent"
  },
  {
    label: "En demanda", value: kpis.value.enDemanda, icon: CheckCircle,
    color: "text-emerald-700", bg: "bg-emerald-50", border: "border-emerald-200",
    gradient: "from-emerald-500/10 to-transparent"
  },
  {
    label: "Pendientes de aprobación", value: kpis.value.pendientes, icon: Clock,
    color: "text-[#4F5AF5]", bg: "bg-[#EEF2FF]", border: "border-[#C7D2FE]",
    gradient: "from-[#4F5AF5]/10 to-transparent"
  },
  {
    label: "Observadas", value: kpis.value.observadas, icon: AlertTriangle,
    color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200",
    gradient: "from-amber-500/10 to-transparent"
  },
  {
    label: "Desestimadas", value: kpis.value.desestimadas, icon: Ban,
    color: "text-red-600", bg: "bg-red-50", border: "border-red-200",
    gradient: "from-red-500/10 to-transparent"
  },
  {
    label: "Borradores", value: kpis.value.borradores, icon: FileText,
    color: "text-slate-500", bg: "bg-slate-100", border: "border-slate-200",
    gradient: "from-slate-500/10 to-transparent"
  },
]);

// ─── Groupings for Perspectives ──────────────────────────────────────────────
const vpGroups = computed(() => {
  const map = new Map<string, Initiative[]>();
  filtered.value.forEach(i => {
    const key = i.form_data?.vicepresidencia || "Sin Vicepresidencia";
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(i);
  });
  return Array.from(map.entries()).map(([name, inits]) => {
    const vpObj = vps.value.find(v => v.name === name);
    const statusCount: Record<string, number> = {};
    inits.forEach(i => { statusCount[i.status] = (statusCount[i.status] ?? 0) + 1; });
    return {
      key: name,
      title: name,
      subtitle: vpObj?.bp_name ? `Vicepresidente: ${vpObj.bp_name}` : undefined,
      total: inits.length,
      statusCount,
      inits,
      isUnassigned: false,
      pct: filtered.value.length > 0 ? Math.round((inits.length / filtered.value.length) * 100) : 0,
    };
  }).sort((a, b) => b.total - a.total);
});

const dirGroups = computed(() => {
  const map = new Map<string, Initiative[]>();
  filtered.value.forEach(i => {
    const key = i.form_data?.direccion || "Sin Dirección Asignada";
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(i);
  });
  return Array.from(map.entries()).map(([name, inits]) => {
    const parentVP = inits[0]?.form_data?.vicepresidencia || "Vicepresidencia no especificada";
    const statusCount: Record<string, number> = {};
    inits.forEach(i => { statusCount[i.status] = (statusCount[i.status] ?? 0) + 1; });
    return {
      key: name,
      title: name,
      subtitle: `Vicepresidencia: ${parentVP}`,
      total: inits.length,
      statusCount,
      inits,
      isUnassigned: false,
      pct: filtered.value.length > 0 ? Math.round((inits.length / filtered.value.length) * 100) : 0,
    };
  }).sort((a, b) => b.total - a.total);
});

const bptiGroups = computed(() => {
  const map = new Map<string, Initiative[]>();
  filtered.value.forEach(i => {
    const bp = getBPTI(i);
    const key = bp ? bp : "Pendiente de Asignación BP TI";
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(i);
  });
  return Array.from(map.entries()).map(([name, inits]) => {
    const statusCount: Record<string, number> = {};
    inits.forEach(i => { statusCount[i.status] = (statusCount[i.status] ?? 0) + 1; });
    const isUnassigned = name.includes("Pendiente");
    return {
      key: name,
      title: name,
      subtitle: isUnassigned ? "Iniciativas en espera de asignación de Business Partner TI" : "Business Partner de TI Responsable",
      total: inits.length,
      statusCount,
      inits,
      isUnassigned,
      pct: filtered.value.length > 0 ? Math.round((inits.length / filtered.value.length) * 100) : 0,
    };
  }).sort((a, b) => {
    if (a.isUnassigned) return -1;
    if (b.isUnassigned) return 1;
    return b.total - a.total;
  });
});

const ldGroups = computed(() => {
  const map = new Map<string, Initiative[]>();
  filtered.value.forEach(i => {
    const ld = getLD(i);
    const key = ld ? ld : "Sin Asignar / Pendiente de LD";
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(i);
  });
  return Array.from(map.entries()).map(([name, inits]) => {
    const statusCount: Record<string, number> = {};
    inits.forEach(i => { statusCount[i.status] = (statusCount[i.status] ?? 0) + 1; });
    const isUnassigned = name.includes("Sin Asignar");
    return {
      key: name,
      title: name,
      subtitle: isUnassigned ? "Iniciativas en etapa de Demanda TI sin Líder de Dominio designado" : "Líder Técnico de Dominio Asignado",
      total: inits.length,
      statusCount,
      inits,
      isUnassigned,
      pct: filtered.value.length > 0 ? Math.round((inits.length / filtered.value.length) * 100) : 0,
    };
  }).sort((a, b) => {
    if (a.isUnassigned) return -1;
    if (b.isUnassigned) return 1;
    return b.total - a.total;
  });
});

const estadoGroups = computed(() => {
  return ALL_STATUSES.map(status => {
    const inits = filtered.value.filter(i => i.status === status);
    const statusCount: Record<string, number> = { [status]: inits.length };
    return {
      key: status,
      title: status,
      subtitle: "Etapa del ciclo de vida en IACS",
      total: inits.length,
      statusCount,
      inits,
      isUnassigned: false,
      pct: filtered.value.length > 0 ? Math.round((inits.length / filtered.value.length) * 100) : 0,
    };
  });
});

// ─── Table Pagination ────────────────────────────────────────────────────────
const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / PAGE_SIZE)));
const paginated = computed(() => filtered.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE));

const toggleGroup = (key: string) => {
  expandedGroup.value = expandedGroup.value === key ? null : key;
};

// Toggle helper for multi-selects
const toggleMultiSelectOption = (listRef: any, val: string) => {
  if (listRef.value.includes(val)) {
    listRef.value = listRef.value.filter((x: string) => x !== val);
  } else {
    listRef.value = [...listRef.value, val];
  }
  page.value = 1;
};

const selectAllMultiSelect = (listRef: any, allOptions: string[]) => {
  if (listRef.value.length === allOptions.length) {
    listRef.value = [];
  } else {
    listRef.value = [...allOptions];
  }
  page.value = 1;
};

const getMultiSelectDisplayText = (selected: string[], options: string[], placeholder: string) => {
  if (selected.length === 0) return placeholder;
  if (selected.length === options.length) return `Todos (${options.length})`;
  if (selected.length === 1) return selected[0];
  return `${selected.length} seleccionados`;
};
</script>

<template>
  <div class="space-y-6 pb-12" @click="closeDropdowns">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
      <div>
        <div class="flex items-center gap-2 mb-1">
          <span class="text-[10px] uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-md bg-indigo-50 text-[#4F5AF5] border border-indigo-100">
            Centro de Control Estratégico
          </span>
          <span class="text-[10px] text-slate-400 font-semibold">• 5 Perspectivas Ejecutivas</span>
        </div>
        <h2 class="text-2xl font-bold tracking-tight text-[#1E293B]">Dashboard Ejecutivo</h2>
        <p class="text-[#64748B] text-sm mt-0.5">
          Gobernanza y trazabilidad estratégica de iniciativas por Vicepresidencia, Dirección, BP TI, Líder de Dominio y Estados.
        </p>
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <button
          @click="loadData"
          class="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-[#64748B] bg-white border border-[#E2E8F0] rounded-xl hover:bg-[#F8FAFC] transition-colors shadow-2xs cursor-pointer"
        >
          <RefreshCw :class="['w-3.5 h-3.5', loading ? 'animate-spin' : '']" />
          Actualizar datos
        </button>
        <NuxtLink
          to="/bandeja"
          class="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-[#4F5AF5] hover:bg-[#3F49E0] rounded-xl transition-colors shadow-sm cursor-pointer"
        >
          <FolderKanban class="w-3.5 h-3.5" />
          Bandeja
        </NuxtLink>
      </div>
    </div>

    <!-- ── Filter Bar ── -->
    <div class="bg-white rounded-2xl border border-[#E2E8F0] shadow-[0_1px_3px_rgba(0,0,0,.04)] p-4 space-y-3" @click.stop>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Filter class="w-4 h-4 text-[#4F5AF5]" />
          <span class="text-xs font-bold text-[#1E293B] uppercase tracking-wider">Filtros Cruzados</span>
          <span class="text-[11px] text-slate-400 font-medium">({{ filtered.length }} iniciativas filtradas)</span>
        </div>
        <button
          v-if="hasActiveFilters"
          @click="clearFilters"
          class="flex items-center gap-1 text-xs font-semibold text-rose-600 hover:text-rose-700 transition-colors cursor-pointer"
        >
          <X class="w-3.5 h-3.5" /> Limpiar filtros
        </button>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-7 gap-2.5">
        <!-- Search Input -->
        <div class="relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#94A3B8]" />
          <input
            type="text"
            v-model="searchText"
            @input="page = 1"
            placeholder="Buscar por texto..."
            class="w-full pl-8 pr-3 py-2 text-xs border border-[#E2E8F0] rounded-xl bg-[#F8FAFC] outline-none focus:border-[#4F5AF5] focus:bg-white transition-colors text-slate-800"
          />
        </div>

        <!-- 1. Sponsor / Vicepresidente Negocio -->
        <div class="relative">
          <button
            type="button"
            @click.stop="toggleDropdown('bp')"
            class="w-full flex items-center justify-between px-3 py-2 text-xs border border-[#E2E8F0] rounded-xl bg-[#F8FAFC] outline-none hover:bg-white focus:border-[#4F5AF5] focus:bg-white transition-all text-[#1E293B] cursor-pointer text-left font-medium shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
          >
            <span class="truncate pr-2">{{ getMultiSelectDisplayText(filterBP, bpOptions, 'Todos los Sponsors') }}</span>
            <ChevronDown :class="['w-3.5 h-3.5 text-[#94A3B8] transition-transform duration-200 shrink-0', openDropdown === 'bp' ? 'rotate-180' : '']" />
          </button>
          <div v-if="openDropdown === 'bp'" class="absolute left-0 mt-1.5 w-64 bg-white border border-[#E2E8F0] rounded-xl shadow-lg z-50 py-2 max-h-60 overflow-y-auto animate-in fade-in duration-100">
            <div class="px-3 py-1.5 border-b border-[#F1F5F9] mb-1 flex items-center justify-between">
              <span class="text-[10px] font-bold text-[#94A3B8] uppercase tracking-wider">Vicepresidente Negocio</span>
              <button type="button" @click="selectAllMultiSelect(filterBP, bpOptions)" class="text-[10px] font-semibold text-[#4F5AF5] hover:text-[#3F49E0]">
                {{ filterBP.length === bpOptions.length ? 'Deseleccionar' : 'Todos' }}
              </button>
            </div>
            <div class="divide-y divide-[#F8FAFC]">
              <label v-for="opt in bpOptions" :key="opt" class="flex items-center gap-2 px-3 py-2 text-xs text-[#334155] hover:bg-[#F8FAFC] cursor-pointer">
                <input type="checkbox" :checked="filterBP.includes(opt)" @change="toggleMultiSelectOption(filterBP, opt)" class="w-3.5 h-3.5 rounded border-[#E2E8F0] text-[#4F5AF5]" />
                <span :class="['truncate', filterBP.includes(opt) ? 'font-semibold text-[#4F5AF5]' : '']">{{ opt }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- 2. Vicepresidencia -->
        <div class="relative">
          <button
            type="button"
            @click.stop="toggleDropdown('vp')"
            class="w-full flex items-center justify-between px-3 py-2 text-xs border border-[#E2E8F0] rounded-xl bg-[#F8FAFC] outline-none hover:bg-white focus:border-[#4F5AF5] focus:bg-white transition-all text-[#1E293B] cursor-pointer text-left font-medium shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
          >
            <span class="truncate pr-2">{{ getMultiSelectDisplayText(filterVP, vpOptions, 'Todas las VPs') }}</span>
            <ChevronDown :class="['w-3.5 h-3.5 text-[#94A3B8] transition-transform duration-200 shrink-0', openDropdown === 'vp' ? 'rotate-180' : '']" />
          </button>
          <div v-if="openDropdown === 'vp'" class="absolute left-0 mt-1.5 w-64 bg-white border border-[#E2E8F0] rounded-xl shadow-lg z-50 py-2 max-h-60 overflow-y-auto animate-in fade-in duration-100">
            <div class="px-3 py-1.5 border-b border-[#F1F5F9] mb-1 flex items-center justify-between">
              <span class="text-[10px] font-bold text-[#94A3B8] uppercase tracking-wider">Vicepresidencia</span>
              <button type="button" @click="selectAllMultiSelect(filterVP, vpOptions)" class="text-[10px] font-semibold text-[#4F5AF5] hover:text-[#3F49E0]">
                {{ filterVP.length === vpOptions.length ? 'Deseleccionar' : 'Todos' }}
              </button>
            </div>
            <div class="divide-y divide-[#F8FAFC]">
              <label v-for="opt in vpOptions" :key="opt" class="flex items-center gap-2 px-3 py-2 text-xs text-[#334155] hover:bg-[#F8FAFC] cursor-pointer">
                <input type="checkbox" :checked="filterVP.includes(opt)" @change="toggleMultiSelectOption(filterVP, opt)" class="w-3.5 h-3.5 rounded border-[#E2E8F0] text-[#4F5AF5]" />
                <span :class="['truncate', filterVP.includes(opt) ? 'font-semibold text-[#4F5AF5]' : '']">{{ opt }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- 3. Dirección -->
        <div class="relative">
          <button
            type="button"
            @click.stop="toggleDropdown('dir')"
            class="w-full flex items-center justify-between px-3 py-2 text-xs border border-[#E2E8F0] rounded-xl bg-[#F8FAFC] outline-none hover:bg-white focus:border-[#4F5AF5] focus:bg-white transition-all text-[#1E293B] cursor-pointer text-left font-medium shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
          >
            <span class="truncate pr-2">{{ getMultiSelectDisplayText(filterDir, dirOptions, 'Todas las Direcciones') }}</span>
            <ChevronDown :class="['w-3.5 h-3.5 text-[#94A3B8] transition-transform duration-200 shrink-0', openDropdown === 'dir' ? 'rotate-180' : '']" />
          </button>
          <div v-if="openDropdown === 'dir'" class="absolute left-0 mt-1.5 w-64 bg-white border border-[#E2E8F0] rounded-xl shadow-lg z-50 py-2 max-h-60 overflow-y-auto animate-in fade-in duration-100">
            <div class="px-3 py-1.5 border-b border-[#F1F5F9] mb-1 flex items-center justify-between">
              <span class="text-[10px] font-bold text-[#94A3B8] uppercase tracking-wider">Dirección</span>
              <button type="button" @click="selectAllMultiSelect(filterDir, dirOptions)" class="text-[10px] font-semibold text-[#4F5AF5] hover:text-[#3F49E0]">
                {{ filterDir.length === dirOptions.length ? 'Deseleccionar' : 'Todos' }}
              </button>
            </div>
            <div class="divide-y divide-[#F8FAFC]">
              <label v-for="opt in dirOptions" :key="opt" class="flex items-center gap-2 px-3 py-2 text-xs text-[#334155] hover:bg-[#F8FAFC] cursor-pointer">
                <input type="checkbox" :checked="filterDir.includes(opt)" @change="toggleMultiSelectOption(filterDir, opt)" class="w-3.5 h-3.5 rounded border-[#E2E8F0] text-[#4F5AF5]" />
                <span :class="['truncate', filterDir.includes(opt) ? 'font-semibold text-[#4F5AF5]' : '']">{{ opt }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- 4. BP TI Asignado -->
        <div class="relative">
          <button
            type="button"
            @click.stop="toggleDropdown('bpti')"
            class="w-full flex items-center justify-between px-3 py-2 text-xs border border-[#E2E8F0] rounded-xl bg-[#F8FAFC] outline-none hover:bg-white focus:border-[#4F5AF5] focus:bg-white transition-all text-[#1E293B] cursor-pointer text-left font-medium shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
          >
            <span class="truncate pr-2">{{ getMultiSelectDisplayText(filterBPTI, bpTiOptions, 'Todos los BP TI') }}</span>
            <ChevronDown :class="['w-3.5 h-3.5 text-[#94A3B8] transition-transform duration-200 shrink-0', openDropdown === 'bpti' ? 'rotate-180' : '']" />
          </button>
          <div v-if="openDropdown === 'bpti'" class="absolute left-0 mt-1.5 w-64 bg-white border border-[#E2E8F0] rounded-xl shadow-lg z-50 py-2 max-h-60 overflow-y-auto animate-in fade-in duration-100">
            <div class="px-3 py-1.5 border-b border-[#F1F5F9] mb-1 flex items-center justify-between">
              <span class="text-[10px] font-bold text-[#94A3B8] uppercase tracking-wider">BP TI Asignado</span>
              <button type="button" @click="selectAllMultiSelect(filterBPTI, bpTiOptions)" class="text-[10px] font-semibold text-[#4F5AF5] hover:text-[#3F49E0]">
                {{ filterBPTI.length === bpTiOptions.length ? 'Deseleccionar' : 'Todos' }}
              </button>
            </div>
            <div class="divide-y divide-[#F8FAFC]">
              <label v-for="opt in bpTiOptions" :key="opt" class="flex items-center gap-2 px-3 py-2 text-xs text-[#334155] hover:bg-[#F8FAFC] cursor-pointer">
                <input type="checkbox" :checked="filterBPTI.includes(opt)" @change="toggleMultiSelectOption(filterBPTI, opt)" class="w-3.5 h-3.5 rounded border-[#E2E8F0] text-[#4F5AF5]" />
                <span :class="['truncate', filterBPTI.includes(opt) ? 'font-semibold text-[#4F5AF5]' : '']">{{ opt }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- 5. Líder de Dominio (LD) -->
        <div class="relative">
          <button
            type="button"
            @click.stop="toggleDropdown('ld')"
            class="w-full flex items-center justify-between px-3 py-2 text-xs border border-[#E2E8F0] rounded-xl bg-[#F8FAFC] outline-none hover:bg-white focus:border-[#4F5AF5] focus:bg-white transition-all text-[#1E293B] cursor-pointer text-left font-medium shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
          >
            <span class="truncate pr-2">{{ getMultiSelectDisplayText(filterLD, ldOptions, 'Todos los LDs') }}</span>
            <ChevronDown :class="['w-3.5 h-3.5 text-[#94A3B8] transition-transform duration-200 shrink-0', openDropdown === 'ld' ? 'rotate-180' : '']" />
          </button>
          <div v-if="openDropdown === 'ld'" class="absolute left-0 mt-1.5 w-64 bg-white border border-[#E2E8F0] rounded-xl shadow-lg z-50 py-2 max-h-60 overflow-y-auto animate-in fade-in duration-100">
            <div class="px-3 py-1.5 border-b border-[#F1F5F9] mb-1 flex items-center justify-between">
              <span class="text-[10px] font-bold text-[#94A3B8] uppercase tracking-wider">Líder de Dominio</span>
              <button type="button" @click="selectAllMultiSelect(filterLD, ldOptions)" class="text-[10px] font-semibold text-[#4F5AF5] hover:text-[#3F49E0]">
                {{ filterLD.length === ldOptions.length ? 'Deseleccionar' : 'Todos' }}
              </button>
            </div>
            <div class="divide-y divide-[#F8FAFC]">
              <label v-for="opt in ldOptions" :key="opt" class="flex items-center gap-2 px-3 py-2 text-xs text-[#334155] hover:bg-[#F8FAFC] cursor-pointer">
                <input type="checkbox" :checked="filterLD.includes(opt)" @change="toggleMultiSelectOption(filterLD, opt)" class="w-3.5 h-3.5 rounded border-[#E2E8F0] text-[#4F5AF5]" />
                <span :class="['truncate', filterLD.includes(opt) ? 'font-semibold text-[#4F5AF5]' : '']">{{ opt }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- 6. Estado del Ciclo -->
        <div class="relative">
          <button
            type="button"
            @click.stop="toggleDropdown('status')"
            class="w-full flex items-center justify-between px-3 py-2 text-xs border border-[#E2E8F0] rounded-xl bg-[#F8FAFC] outline-none hover:bg-white focus:border-[#4F5AF5] focus:bg-white transition-all text-[#1E293B] cursor-pointer text-left font-medium shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
          >
            <span class="truncate pr-2">{{ getMultiSelectDisplayText(filterStatus, statusOptions, 'Todos los Estados') }}</span>
            <ChevronDown :class="['w-3.5 h-3.5 text-[#94A3B8] transition-transform duration-200 shrink-0', openDropdown === 'status' ? 'rotate-180' : '']" />
          </button>
          <div v-if="openDropdown === 'status'" class="absolute left-0 mt-1.5 w-64 bg-white border border-[#E2E8F0] rounded-xl shadow-lg z-50 py-2 max-h-60 overflow-y-auto animate-in fade-in duration-100">
            <div class="px-3 py-1.5 border-b border-[#F1F5F9] mb-1 flex items-center justify-between">
              <span class="text-[10px] font-bold text-[#94A3B8] uppercase tracking-wider">Estado del Ciclo</span>
              <button type="button" @click="selectAllMultiSelect(filterStatus, statusOptions)" class="text-[10px] font-semibold text-[#4F5AF5] hover:text-[#3F49E0]">
                {{ filterStatus.length === statusOptions.length ? 'Deseleccionar' : 'Todos' }}
              </button>
            </div>
            <div class="divide-y divide-[#F8FAFC]">
              <label v-for="opt in statusOptions" :key="opt" class="flex items-center gap-2 px-3 py-2 text-xs text-[#334155] hover:bg-[#F8FAFC] cursor-pointer">
                <input type="checkbox" :checked="filterStatus.includes(opt)" @change="toggleMultiSelectOption(filterStatus, opt)" class="w-3.5 h-3.5 rounded border-[#E2E8F0] text-[#4F5AF5]" />
                <span :class="['truncate', filterStatus.includes(opt) ? 'font-semibold text-[#4F5AF5]' : '']">{{ opt }}</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Active Filter Tags -->
      <div v-if="hasActiveFilters" class="pt-2 border-t border-[#F1F5F9] flex items-center gap-1.5 flex-wrap">
        <span class="text-[10px] text-[#94A3B8] font-bold uppercase tracking-wider mr-1">Activos:</span>
        <span v-for="bp in filterBP" :key="bp" class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-indigo-50 border border-indigo-100 text-[#4F5AF5] text-[11px] font-semibold">
          Sponsor: {{ bp }}
          <button @click="toggleMultiSelectOption(filterBP, bp)" class="hover:text-red-500"><X class="w-3 h-3" /></button>
        </span>
        <span v-for="vp in filterVP" :key="vp" class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-indigo-50 border border-indigo-100 text-[#4F5AF5] text-[11px] font-semibold">
          VP: {{ vp }}
          <button @click="toggleMultiSelectOption(filterVP, vp)" class="hover:text-red-500"><X class="w-3 h-3" /></button>
        </span>
        <span v-for="dir in filterDir" :key="dir" class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-indigo-50 border border-indigo-100 text-[#4F5AF5] text-[11px] font-semibold">
          Dir: {{ dir }}
          <button @click="toggleMultiSelectOption(filterDir, dir)" class="hover:text-red-500"><X class="w-3 h-3" /></button>
        </span>
        <span v-for="bpti in filterBPTI" :key="bpti" class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-indigo-50 border border-indigo-100 text-[#4F5AF5] text-[11px] font-semibold">
          BP TI: {{ bpti }}
          <button @click="toggleMultiSelectOption(filterBPTI, bpti)" class="hover:text-red-500"><X class="w-3 h-3" /></button>
        </span>
        <span v-for="ld in filterLD" :key="ld" class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-indigo-50 border border-indigo-100 text-[#4F5AF5] text-[11px] font-semibold">
          LD: {{ ld }}
          <button @click="toggleMultiSelectOption(filterLD, ld)" class="hover:text-red-500"><X class="w-3 h-3" /></button>
        </span>
        <span v-for="st in filterStatus" :key="st" class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-slate-100 border border-slate-200 text-slate-700 text-[11px] font-semibold">
          Estado: {{ st }}
          <button @click="toggleMultiSelectOption(filterStatus, st)" class="hover:text-red-500"><X class="w-3 h-3" /></button>
        </span>
      </div>
    </div>

    <!-- ── KPI Cards ── -->
    <div v-if="loading" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      <div v-for="i in 6" :key="i" class="h-24 bg-white rounded-xl border border-[#E2E8F0] animate-pulse" />
    </div>
    <div v-else class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      <div
        v-for="k in kpiCards"
        :key="k.label"
        :class="['bg-white rounded-xl border shadow-[0_1px_3px_rgba(0,0,0,.04)] p-4 relative overflow-hidden group hover:shadow-md transition-all', k.border]"
      >
        <div :class="['absolute inset-0 bg-gradient-to-br opacity-60', k.gradient]" />
        <div class="relative">
          <div :class="['w-8 h-8 rounded-lg flex items-center justify-center mb-2.5', k.bg]">
            <component :is="k.icon" :class="['w-4 h-4', k.color]" />
          </div>
          <p :class="['text-2xl font-black', k.color]">{{ k.value }}</p>
          <p class="text-[10px] font-bold text-[#94A3B8] uppercase tracking-wider mt-0.5 leading-tight">{{ k.label }}</p>
        </div>
      </div>
    </div>

    <!-- ── Navigation Tabs: 5 Executive Perspectives + Matriz General ── -->
    <div class="bg-white rounded-2xl border border-[#E2E8F0] shadow-[0_1px_3px_rgba(0,0,0,.04)] p-1.5 flex items-center gap-1.5 overflow-x-auto">
      <button
        type="button"
        @click="activeTab = 'vp'; expandedGroup = null"
        :class="[
          'flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer',
          activeTab === 'vp' ? 'bg-[#4F5AF5] text-white shadow-sm' : 'text-slate-600 hover:text-[#4F5AF5] hover:bg-slate-50'
        ]"
      >
        <Building2 class="w-4 h-4" />
        Por Vicepresidencia
        <span :class="['text-[10px] px-1.5 py-0.2 rounded-full font-black', activeTab === 'vp' ? 'bg-white/25 text-white' : 'bg-slate-100 text-slate-600']">
          {{ vpGroups.length }}
        </span>
      </button>

      <button
        type="button"
        @click="activeTab = 'direccion'; expandedGroup = null"
        :class="[
          'flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer',
          activeTab === 'direccion' ? 'bg-[#4F5AF5] text-white shadow-sm' : 'text-slate-600 hover:text-[#4F5AF5] hover:bg-slate-50'
        ]"
      >
        <Layers class="w-4 h-4" />
        Por Dirección
        <span :class="['text-[10px] px-1.5 py-0.2 rounded-full font-black', activeTab === 'direccion' ? 'bg-white/25 text-white' : 'bg-slate-100 text-slate-600']">
          {{ dirGroups.length }}
        </span>
      </button>

      <button
        type="button"
        @click="activeTab = 'bpti'; expandedGroup = null"
        :class="[
          'flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer',
          activeTab === 'bpti' ? 'bg-[#4F5AF5] text-white shadow-sm' : 'text-slate-600 hover:text-[#4F5AF5] hover:bg-slate-50'
        ]"
      >
        <Briefcase class="w-4 h-4" />
        Por BP TI Asignado
        <span :class="['text-[10px] px-1.5 py-0.2 rounded-full font-black', activeTab === 'bpti' ? 'bg-white/25 text-white' : 'bg-slate-100 text-slate-600']">
          {{ bptiGroups.length }}
        </span>
      </button>

      <button
        type="button"
        @click="activeTab = 'ld'; expandedGroup = null"
        :class="[
          'flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer',
          activeTab === 'ld' ? 'bg-[#4F5AF5] text-white shadow-sm' : 'text-slate-600 hover:text-[#4F5AF5] hover:bg-slate-50'
        ]"
      >
        <UserCheck class="w-4 h-4" />
        Por Líder de Dominio (LD)
        <span :class="['text-[10px] px-1.5 py-0.2 rounded-full font-black', activeTab === 'ld' ? 'bg-white/25 text-white' : 'bg-slate-100 text-slate-600']">
          {{ ldGroups.length }}
        </span>
      </button>

      <button
        type="button"
        @click="activeTab = 'estado'; expandedGroup = null"
        :class="[
          'flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer',
          activeTab === 'estado' ? 'bg-[#4F5AF5] text-white shadow-sm' : 'text-slate-600 hover:text-[#4F5AF5] hover:bg-slate-50'
        ]"
      >
        <BarChart3 class="w-4 h-4" />
        Por Estados (Ciclo)
        <span :class="['text-[10px] px-1.5 py-0.2 rounded-full font-black', activeTab === 'estado' ? 'bg-white/25 text-white' : 'bg-slate-100 text-slate-600']">
          {{ ALL_STATUSES.length }}
        </span>
      </button>

      <button
        type="button"
        @click="activeTab = 'tabla'; expandedGroup = null"
        :class="[
          'flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer ml-auto',
          activeTab === 'tabla' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
        ]"
      >
        <LayoutGrid class="w-4 h-4" />
        Matriz Completa
      </button>
    </div>

    <!-- ── Content: Perspectives Accordion Groups ── -->
    <div v-if="loading" class="py-16 bg-white rounded-2xl border border-slate-200 flex items-center justify-center">
      <InstitutionalLoader 
        title="Cargando Tablero de Control" 
        subtitle="Analizando métricas corporativas y distribución de la cartera..."
        :phrases="[
          'Consolidando datos de Vicepresidencias y Direcciones...',
          'Calculando indicadores clave de rendimiento (KPIs)...',
          'Agrupando iniciativas por estados y líderes técnicos...',
          'Generando perspectivas de gobernanza TI...'
        ]"
      />
    </div>

    <div v-else-if="filtered.length === 0" class="py-20 text-center bg-white rounded-2xl border border-slate-200 p-8 shadow-xs">
      <Activity class="w-10 h-10 mx-auto mb-3 text-slate-300" />
      <h4 class="text-base font-bold text-slate-700">No hay iniciativas para los filtros seleccionados</h4>
      <p class="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
        Intenta cambiar los parámetros en la barra superior o limpiar los filtros activos.
      </p>
      <button
        v-if="hasActiveFilters"
        @click="clearFilters"
        class="mt-4 inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-50 text-[#4F5AF5] text-xs font-bold hover:bg-indigo-100 transition-colors cursor-pointer"
      >
        Limpiar todos los filtros
      </button>
    </div>

    <div v-else class="space-y-4">
      <!-- Perspectives: VP, Dirección, BP TI, LD, Estado -->
      <div v-if="activeTab !== 'tabla'" class="space-y-3.5">
        <div
          v-for="grp in (activeTab === 'vp' ? vpGroups : activeTab === 'direccion' ? dirGroups : activeTab === 'bpti' ? bptiGroups : activeTab === 'ld' ? ldGroups : estadoGroups)"
          :key="grp.key"
          :class="[
            'bg-white rounded-2xl border transition-all duration-200 overflow-hidden shadow-xs hover:shadow-md',
            grp.isUnassigned ? 'border-amber-300 bg-amber-50/20' : expandedGroup === grp.key ? 'border-[#4F5AF5]/50 ring-1 ring-[#4F5AF5]/20 shadow-md' : 'border-[#E2E8F0] hover:border-[#CBD5E1]'
          ]"
        >
          <!-- Group Header -->
          <div
            @click="toggleGroup(grp.key)"
            class="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer select-none transition-colors hover:bg-slate-50/60"
          >
            <div class="flex items-start sm:items-center gap-3.5 min-w-0">
              <div :class="[
                'w-11 h-11 rounded-xl flex items-center justify-center shrink-0',
                grp.isUnassigned ? 'bg-amber-100 text-amber-700' : 'bg-indigo-50 text-[#4F5AF5]'
              ]">
                <Building2 v-if="activeTab === 'vp'" class="w-5 h-5" />
                <Layers v-else-if="activeTab === 'direccion'" class="w-5 h-5" />
                <Briefcase v-else-if="activeTab === 'bpti'" class="w-5 h-5" />
                <UserCheck v-else-if="activeTab === 'ld'" class="w-5 h-5" />
                <BarChart3 v-else class="w-5 h-5" />
              </div>
              <div class="min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <h4 class="text-base font-bold text-[#1E293B] truncate leading-tight">{{ grp.title }}</h4>
                  <span v-if="grp.isUnassigned" class="text-[10px] font-bold uppercase tracking-wider bg-amber-100 text-amber-800 border border-amber-300 px-2 py-0.5 rounded-md">
                    Atención Requerida
                  </span>
                </div>
                <p v-if="grp.subtitle" class="text-xs text-[#64748B] mt-0.5 truncate">{{ grp.subtitle }}</p>
              </div>
            </div>

            <div class="flex items-center gap-4 shrink-0 justify-between sm:justify-end">
              <div class="text-right">
                <div class="flex items-baseline gap-1.5 justify-end">
                  <span class="text-xl font-black text-[#1E293B]">{{ grp.total }}</span>
                  <span class="text-xs font-semibold text-[#94A3B8]">({{ grp.pct }}%)</span>
                </div>
                <p class="text-[10px] text-[#94A3B8] font-medium uppercase tracking-wider">Iniciativas</p>
              </div>
              <button
                type="button"
                :class="[
                  'w-8 h-8 rounded-lg border border-slate-200 flex items-center justify-center text-slate-500 hover:bg-slate-100 transition-transform duration-200',
                  expandedGroup === grp.key ? 'rotate-180 bg-indigo-50 text-[#4F5AF5] border-indigo-200' : ''
                ]"
              >
                <ChevronDown class="w-4 h-4" />
              </button>
            </div>
          </div>

          <!-- Status Distribution Pills -->
          <div class="px-5 pb-3.5 pt-1 border-t border-slate-100 flex items-center justify-between gap-2 flex-wrap bg-slate-50/40">
            <div class="flex items-center gap-1.5 flex-wrap">
              <span
                v-for="(cnt, st) in grp.statusCount"
                :key="st"
                :class="[
                  'inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold border',
                  STATUS_CONFIG[st]?.bg || 'bg-slate-100',
                  STATUS_CONFIG[st]?.color || 'text-slate-600',
                  STATUS_CONFIG[st]?.border || 'border-slate-200'
                ]"
              >
                <span :class="['w-1.5 h-1.5 rounded-full', STATUS_CONFIG[st]?.dot || 'bg-slate-400']" />
                {{ cnt }} {{ st }}
              </span>
            </div>
            <span class="text-[11px] font-semibold text-[#4F5AF5] hover:text-[#3F49E0] transition-colors cursor-pointer" @click="toggleGroup(grp.key)">
              {{ expandedGroup === grp.key ? 'Ocultar iniciativas ↑' : `Ver ${grp.total} iniciativas ↓` }}
            </span>
          </div>

          <!-- Accordion List of Initiatives -->
          <div v-if="expandedGroup === grp.key" class="border-t border-slate-200 bg-white p-4 space-y-2 animate-in fade-in duration-150">
            <div class="grid grid-cols-1 divide-y divide-slate-100">
              <div
                v-for="ini in grp.inits"
                :key="ini.id"
                class="py-3 px-3 hover:bg-slate-50/80 rounded-xl transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 group"
              >
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2 mb-1 flex-wrap">
                    <span :class="[
                      'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border',
                      STATUS_CONFIG[ini.status]?.bg || 'bg-slate-100',
                      STATUS_CONFIG[ini.status]?.color || 'text-slate-600',
                      STATUS_CONFIG[ini.status]?.border || 'border-slate-200'
                    ]">
                      <span :class="['w-1.5 h-1.5 rounded-full', STATUS_CONFIG[ini.status]?.dot || 'bg-slate-400']" />
                      {{ ini.status }}
                    </span>
                    <span class="text-[11px] text-slate-400 font-mono">#{{ ini.summary?.id_corta || ini.id.slice(0, 8) }}</span>
                    <span class="text-xs text-slate-400">• {{ formatDate(ini.created_at) }}</span>
                  </div>
                  <h5
                    @click="selectedInitiative = ini"
                    class="text-sm font-semibold text-slate-800 hover:text-[#4F5AF5] transition-colors cursor-pointer line-clamp-1"
                  >
                    {{ getTitle(ini) }}
                  </h5>
                  <div class="flex items-center gap-3 mt-1 text-[11px] text-slate-500 flex-wrap">
                    <span v-if="ini.form_data?.vicepresidencia">VP: <strong class="text-slate-700">{{ ini.form_data.vicepresidencia }}</strong></span>
                    <span v-if="ini.form_data?.direccion">Dir: <strong class="text-slate-700">{{ ini.form_data.direccion }}</strong></span>
                    <span>BP TI: <strong :class="getBPTI(ini) ? 'text-slate-700' : 'text-amber-600'">{{ getBPTI(ini) || 'Sin Asignar' }}</strong></span>
                    <span>LD: <strong :class="getLD(ini) ? 'text-indigo-700' : 'text-slate-400 italic'">{{ getLD(ini) || 'Sin Asignar' }}</strong></span>
                  </div>
                </div>

                <div class="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    @click="selectedInitiative = ini"
                    class="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-100 hover:text-[#4F5AF5] transition-colors cursor-pointer"
                    title="Ver vista previa rápida"
                  >
                    <Eye class="w-3.5 h-3.5" />
                    Vista rápida
                  </button>
                  <NuxtLink
                    :to="ini.status === 'Borrador' ? `/nueva?id=${ini.id}` : `/iniciativa/${ini.id}`"
                    class="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#4F5AF5] hover:bg-[#3F49E0] text-xs font-semibold text-white transition-colors cursor-pointer shadow-2xs"
                  >
                    {{ ini.status === 'Borrador' ? 'Editar' : 'Abrir' }}
                    <ExternalLink class="w-3 h-3" />
                  </NuxtLink>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab 6: Matriz General / Tabla -->
      <div v-else class="bg-white rounded-2xl border border-[#E2E8F0] shadow-[0_1px_3px_rgba(0,0,0,.06)] overflow-hidden">
        <div class="px-6 py-4 border-b border-[#F1F5F9] flex items-center justify-between">
          <div class="flex items-center gap-2">
            <TrendingUp class="w-4 h-4 text-[#4F5AF5]" />
            <h3 class="text-sm font-bold text-[#1E293B]">
              Iniciativas Consolidadas
              <span class="ml-2 text-xs font-normal text-[#94A3B8]">({{ filtered.length }} totales)</span>
            </h3>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="border-b border-[#F1F5F9] bg-[#F8FAFC] text-[11px] font-bold text-[#64748B] uppercase tracking-wider">
                <th class="px-4 py-3">Código</th>
                <th class="px-4 py-3">Iniciativa</th>
                <th class="px-4 py-3">Vicepresidencia</th>
                <th class="px-4 py-3">Dirección</th>
                <th class="px-4 py-3">BP TI</th>
                <th class="px-4 py-3">Líder Dominio</th>
                <th class="px-4 py-3">Estado</th>
                <th class="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[#F1F5F9]">
              <tr v-for="ini in paginated" :key="ini.id" class="hover:bg-[#F8FAFC] transition-colors">
                <td class="px-4 py-3 text-xs font-mono font-semibold text-[#4F5AF5]">
                  #{{ ini.summary?.id_corta || ini.id.slice(0, 8) }}
                </td>
                <td class="px-4 py-3 max-w-xs">
                  <NuxtLink :to="`/iniciativa/${ini.id}`" class="text-xs font-semibold text-slate-800 hover:text-[#4F5AF5] line-clamp-1">
                    {{ getTitle(ini) }}
                  </NuxtLink>
                </td>
                <td class="px-4 py-3 text-xs text-slate-600 truncate max-w-[150px]">{{ ini.form_data?.vicepresidencia || '—' }}</td>
                <td class="px-4 py-3 text-xs text-slate-600 truncate max-w-[150px]">{{ ini.form_data?.direccion || '—' }}</td>
                <td class="px-4 py-3 text-xs font-medium" :class="getBPTI(ini) ? 'text-slate-800' : 'text-amber-600'">{{ getBPTI(ini) || 'Sin asignar' }}</td>
                <td class="px-4 py-3 text-xs font-medium" :class="getLD(ini) ? 'text-indigo-700' : 'text-slate-400 italic'">{{ getLD(ini) || 'Sin asignar' }}</td>
                <td class="px-4 py-3">
                  <span :class="[
                    'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border',
                    STATUS_CONFIG[ini.status]?.bg || 'bg-slate-100',
                    STATUS_CONFIG[ini.status]?.color || 'text-slate-600',
                    STATUS_CONFIG[ini.status]?.border || 'border-slate-200'
                  ]">
                    <span :class="['w-1.5 h-1.5 rounded-full', STATUS_CONFIG[ini.status]?.dot || 'bg-slate-400']" />
                    {{ ini.status }}
                  </span>
                </td>
                <td class="px-4 py-3 text-right">
                  <NuxtLink
                    :to="ini.status === 'Borrador' ? `/nueva?id=${ini.id}` : `/iniciativa/${ini.id}`"
                    class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#4F5AF5] hover:bg-[#3F49E0] text-[11px] font-semibold text-white transition-colors"
                  >
                    Abrir
                    <ExternalLink class="w-3 h-3" />
                  </NuxtLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination Controls -->
        <div class="px-6 py-3 border-t border-[#F1F5F9] bg-[#F8FAFC] flex items-center justify-between text-xs text-slate-500">
          <span>Página {{ page }} de {{ totalPages }}</span>
          <div class="flex items-center gap-1">
            <button
              :disabled="page <= 1"
              @click="page--"
              class="px-2.5 py-1 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40"
            >
              Anterior
            </button>
            <button
              :disabled="page >= totalPages"
              @click="page++"
              class="px-2.5 py-1 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40"
            >
              Siguiente
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── DetailModal Component (Vista rápida) ── -->
    <div v-if="selectedInitiative" class="fixed inset-0 z-[200] flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" @click="selectedInitiative = null" />
      <div class="relative bg-white rounded-2xl shadow-2xl border border-[#E2E8F0] w-full max-w-2xl max-h-[88vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <!-- Modal Header -->
        <div class="px-6 py-4 border-b border-[#F1F5F9] flex items-start justify-between gap-4 shrink-0 bg-gradient-to-r from-slate-50 to-white">
          <div class="min-w-0">
            <div class="flex items-center gap-2 mb-1.5 flex-wrap">
              <span :class="[
                'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border',
                STATUS_CONFIG[selectedInitiative.status]?.bg || 'bg-slate-100',
                STATUS_CONFIG[selectedInitiative.status]?.color || 'text-slate-600',
                STATUS_CONFIG[selectedInitiative.status]?.border || 'border-slate-200'
              ]">
                <span :class="['w-1.5 h-1.5 rounded-full', STATUS_CONFIG[selectedInitiative.status]?.dot || 'bg-slate-400']" />
                {{ selectedInitiative.status }}
              </span>
              <span class="text-xs text-[#94A3B8] font-mono">#{{ selectedInitiative.summary?.id_corta || selectedInitiative.id.slice(0, 8) }}</span>
            </div>
            <h3 class="text-base font-bold text-[#1E293B] leading-snug line-clamp-2">
              {{ getTitle(selectedInitiative) }}
            </h3>
          </div>
          <button
            @click="selectedInitiative = null"
            class="w-8 h-8 rounded-lg border border-[#E2E8F0] flex items-center justify-center text-[#94A3B8] hover:bg-[#F1F5F9] hover:text-[#1E293B] transition-colors shrink-0"
          >
            <X class="w-4 h-4" />
          </button>
        </div>

        <!-- Modal Body -->
        <div class="overflow-y-auto flex-1 p-6 space-y-5">
          <!-- Gobernanza y Asignación -->
          <section>
            <p class="text-[10px] font-bold uppercase tracking-widest text-[#94A3B8] mb-2.5 flex items-center gap-1.5">
              <Briefcase class="w-3.5 h-3.5 text-[#4F5AF5]" />
              Gobernanza y Asignación
            </p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div class="bg-[#F8FAFC] border border-slate-200/70 rounded-xl p-3">
                <p class="text-[10px] font-semibold text-[#94A3B8] uppercase tracking-wider mb-1">Business Partner TI (BP TI)</p>
                <p :class="['text-sm font-semibold', getBPTI(selectedInitiative) ? 'text-slate-800' : 'text-amber-600']">
                  {{ getBPTI(selectedInitiative) || 'Pendiente de Asignación' }}
                </p>
              </div>
              <div class="bg-[#F8FAFC] border border-slate-200/70 rounded-xl p-3">
                <p class="text-[10px] font-semibold text-[#94A3B8] uppercase tracking-wider mb-1">Líder de Dominio (LD)</p>
                <p :class="['text-sm font-semibold', getLD(selectedInitiative) ? 'text-indigo-700' : 'text-slate-500 italic']">
                  {{ getLD(selectedInitiative) || 'Sin Asignar (Etapa de Demanda TI)' }}
                </p>
              </div>
            </div>
          </section>

          <!-- Estructura Organizacional -->
          <section>
            <p class="text-[10px] font-bold uppercase tracking-widest text-[#94A3B8] mb-2.5 flex items-center gap-1.5">
              <Building2 class="w-3.5 h-3.5 text-slate-500" />
              Estructura Organizacional
            </p>
            <div class="grid grid-cols-2 gap-3">
              <div class="bg-[#F8FAFC] border border-slate-100 rounded-xl p-3">
                <p class="text-[10px] font-semibold text-[#94A3B8] uppercase tracking-wider mb-1">Vicepresidencia</p>
                <p class="text-sm font-medium text-[#1E293B]">{{ selectedInitiative.form_data?.vicepresidencia || '—' }}</p>
              </div>
              <div class="bg-[#F8FAFC] border border-slate-100 rounded-xl p-3">
                <p class="text-[10px] font-semibold text-[#94A3B8] uppercase tracking-wider mb-1">Dirección</p>
                <p class="text-sm font-medium text-[#1E293B]">{{ selectedInitiative.form_data?.direccion || '—' }}</p>
              </div>
              <div class="bg-[#F8FAFC] border border-slate-100 rounded-xl p-3">
                <p class="text-[10px] font-semibold text-[#94A3B8] uppercase tracking-wider mb-1">Key user / Solicitante</p>
                <p class="text-sm font-medium text-[#1E293B]">{{ selectedInitiative.form_data?.registrador || '—' }}</p>
              </div>
              <div class="bg-[#F8FAFC] border border-slate-100 rounded-xl p-3">
                <p class="text-[10px] font-semibold text-[#94A3B8] uppercase tracking-wider mb-1">Fecha de Registro</p>
                <p class="text-sm font-medium text-[#1E293B]">{{ formatDate(selectedInitiative.created_at) }}</p>
              </div>
            </div>
          </section>

          <!-- Resumen Ejecutivo IA -->
          <section v-if="selectedInitiative.summary?.objetivo || selectedInitiative.summary?.descripcionProblema">
            <p class="text-[10px] font-bold uppercase tracking-widest text-[#94A3B8] mb-2.5 flex items-center gap-1.5">
              <Sparkles class="w-3.5 h-3.5 text-indigo-500" />
              Resumen Ejecutivo IA (Teo)
            </p>
            <div class="space-y-3">
              <div v-if="selectedInitiative.summary?.objetivo" class="bg-[#F8FAFF] border border-[#EEF2FF] rounded-xl p-4">
                <p class="text-[10px] font-semibold text-[#4F5AF5] uppercase tracking-wider mb-1.5">Objetivo</p>
                <p class="text-sm text-[#334155] leading-relaxed">{{ selectedInitiative.summary.objetivo }}</p>
              </div>
              <div v-if="selectedInitiative.summary?.descripcionProblema" class="bg-[#FFFBF5] border border-amber-100 rounded-xl p-4">
                <p class="text-[10px] font-semibold text-amber-600 uppercase tracking-wider mb-1.5">Problema que resuelve</p>
                <p class="text-sm text-[#334155] leading-relaxed">{{ selectedInitiative.summary.descripcionProblema }}</p>
              </div>
            </div>
          </section>

          <!-- Observaciones / Dictámenes -->
          <section v-if="selectedInitiative.rejection_reason">
            <div class="bg-red-50 border border-red-200 rounded-xl p-4">
              <p class="text-[10px] font-semibold text-red-600 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <AlertTriangle class="w-3.5 h-3.5" />
                Observación / Dictamen
              </p>
              <p class="text-sm text-red-800 leading-relaxed">{{ selectedInitiative.rejection_reason }}</p>
            </div>
          </section>
        </div>

        <!-- Modal Footer -->
        <div class="px-6 py-4 border-t border-[#F1F5F9] bg-[#F8FAFC] flex items-center justify-between shrink-0">
          <p class="text-xs text-[#94A3B8]">Registrado el {{ formatDate(selectedInitiative.created_at) }}</p>
          <NuxtLink
            :to="selectedInitiative.status === 'Borrador' ? `/nueva?id=${selectedInitiative.id}` : `/iniciativa/${selectedInitiative.id}`"
            @click="selectedInitiative = null"
            class="flex items-center gap-2 bg-[#4F5AF5] hover:bg-[#3F49E0] text-white px-4 py-2 rounded-xl text-sm font-semibold transition-colors shadow-sm cursor-pointer"
          >
            {{ selectedInitiative.status === 'Borrador' ? 'Editar Borrador' : 'Abrir Expediente Completo' }}
            <ExternalLink class="w-3.5 h-3.5" />
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>
