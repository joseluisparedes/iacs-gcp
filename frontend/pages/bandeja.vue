<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import {
  Filter, Eye, User, Search, ArrowUpDown, ArrowUp, ArrowDown,
  ChevronDown, X, Building2, SlidersHorizontal, Copy, Check,
  RotateCcw, AlertCircle, Clock, ChevronLeft, ChevronRight,
  ArrowRight, RefreshCw, Layers, Sparkles, CheckCircle2,
  Calendar, FileText, Shield, ExternalLink
} from "lucide-vue-next";

const config = useRuntimeConfig();
const apiBase = config.public.apiBase;

import InstitutionalLoader from "~/components/common/InstitutionalLoader.vue";
import { DEFAULT_MACRO_STAGES, type MacroStageDef } from "~/utils/macroStages";
import { sanitizeCorruptedEncoding } from "~/utils/formatHtml";

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

type TabKey = string;

// Sincronización dinámica de Macro-Etapas con el Workflow Engine corporativo
const { data: activeWorkflowData } = await useFetch<any>(`${apiBase}/workflow/active`);
const activeWorkflow = computed(() => activeWorkflowData.value?.data);

const macroStages = computed<MacroStageDef[]>(() => {
  const custom = activeWorkflow.value?.graph_json?.macro_stages;
  if (Array.isArray(custom) && custom.length > 0) {
    return custom;
  }
  return DEFAULT_MACRO_STAGES;
});

const STAGE_DOT_COLORS: Record<string, string> = {
  borrador: "bg-slate-400",
  eval_bp: "bg-indigo-500",
  aprob_bo: "bg-blue-500",
  aprob_vp: "bg-purple-500",
  asig_demanda: "bg-cyan-500",
  ventana_est: "bg-amber-500",
  estimacion: "bg-amber-500",
  planificacion: "bg-emerald-500",
  observada: "bg-rose-500",
  desestimada: "bg-slate-500",
};

// Pestañas dinámicas y exactamente sincronizadas con el Stepper (Imagen 2 y 3)
const TABS = computed(() => {
  const tabsList = [
    { key: "todas", label: "Todas", dot: "bg-[#4F5AF5]" }
  ];

  macroStages.value.forEach((stage) => {
    tabsList.push({
      key: stage.id,
      label: sanitizeCorruptedEncoding(stage.name),
      dot: STAGE_DOT_COLORS[stage.id] || "bg-indigo-500",
    });
  });

  tabsList.push({ key: "observada", label: "Observadas", dot: "bg-rose-500" });
  tabsList.push({ key: "desestimada", label: "Desestimadas", dot: "bg-slate-500" });

  return tabsList;
});

const STATUS_BADGE_STYLE: Record<string, string> = {
  todas: "bg-slate-100 text-slate-700 border-slate-200",
  borrador: "bg-slate-50 text-slate-700 border-slate-200/80",
  eval_bp: "bg-indigo-50 text-indigo-700 border-indigo-200/80",
  aprob_bo: "bg-blue-50 text-blue-700 border-blue-200/80",
  aprob_vp: "bg-purple-50 text-purple-700 border-purple-200/80",
  asig_demanda: "bg-cyan-50 text-cyan-700 border-cyan-200/80",
  ventana_est: "bg-amber-50 text-amber-700 border-amber-200/80",
  estimacion: "bg-amber-50 text-amber-700 border-amber-200/80",
  planificacion: "bg-emerald-50 text-emerald-700 border-emerald-200/80",
  observada: "bg-rose-50 text-rose-700 border-rose-200/80",
  desestimada: "bg-slate-100 text-slate-600 border-slate-200",
};

const STATUS_DOT_STYLE: Record<string, string> = {
  todas: "bg-slate-400",
  borrador: "bg-slate-400",
  eval_bp: "bg-indigo-500 animate-pulse",
  aprob_bo: "bg-blue-500 animate-pulse",
  aprob_vp: "bg-purple-500 animate-pulse",
  asig_demanda: "bg-cyan-500 animate-pulse",
  ventana_est: "bg-amber-500",
  estimacion: "bg-amber-500",
  planificacion: "bg-emerald-500",
  observada: "bg-rose-500",
  desestimada: "bg-slate-400",
};

interface ColumnDef {
  id: string;
  label: string;
  defaultWidth: number;
  minWidth: number;
  canHide: boolean;
}

const ALL_COLUMNS: ColumnDef[] = [
  { id: "codigo", label: "Código ID", defaultWidth: 125, minWidth: 110, canHide: true },
  { id: "solicitud", label: "Solicitud", defaultWidth: 320, minWidth: 220, canHide: false },
  { id: "vicepresidencia", label: "Vicepresidencia", defaultWidth: 145, minWidth: 120, canHide: true },
  { id: "direccion", label: "Dirección", defaultWidth: 165, minWidth: 130, canHide: true },
  { id: "fecha", label: "Fecha", defaultWidth: 115, minWidth: 95, canHide: true },
  { id: "key_user", label: "Key User", defaultWidth: 175, minWidth: 140, canHide: true },
  { id: "bp", label: "BP TI", defaultWidth: 145, minWidth: 120, canHide: true },
  { id: "estado", label: "Estado Actual", defaultWidth: 220, minWidth: 180, canHide: true },
  { id: "acciones", label: "Acciones", defaultWidth: 140, minWidth: 130, canHide: false }
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

// Pagination
const currentPage = ref(1);
const pageSize = ref(10);
const pageSizeOptions = [10, 25, 50];

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

// Quick Preview Slide-over Drawer
const selectedInitiative = ref<Initiative | null>(null);

// Current user profile
const profile = ref({
  id: "admin-1",
  name: "Administrador General",
  email: "admin@iacs.empresa.com",
  role: "admin",
  roles: ["admin"] as string[],
});

// ─── Helpers ─────────────────────────────────────────────────────────────────
function getInitiativeStatusInfo(i: any): { label: string; tabKey: TabKey } {
  const label = i?.status || "Sin estado";
  const lower = String(label).toLowerCase();
  const currNode = String(i?.current_node_id || "").toLowerCase();

  // 1. Estados transversales prioritarios
  if (lower.includes("desestimad") || currNode.includes("desestimad")) return { label, tabKey: "desestimada" };
  if (lower.includes("observad") || currNode.includes("observad")) return { label, tabKey: "observada" };

  // 2. FASE 1: Coincidencia EXACTA por current_node_id contra todas las Macro-Etapas (Cabecera o Sub-estados)
  if (currNode) {
    for (const stage of macroStages.value) {
      const sId = stage.id.toLowerCase();
      const stageNodes = (stage.nodeIds || []).map(nid => nid.toLowerCase());
      if (currNode === sId || stageNodes.includes(currNode)) {
        return { label, tabKey: stage.id };
      }
    }
  }

  // 3. FASE 2: Coincidencia por statusKeywords específicas (ignorando 'pendiente' genérico)
  for (const stage of macroStages.value) {
    if (Array.isArray(stage.statusKeywords)) {
      for (const kw of stage.statusKeywords) {
        if (!kw || kw.toLowerCase() === 'pendiente') continue;
        try {
          if (new RegExp(kw, 'i').test(lower)) {
            return { label, tabKey: stage.id };
          }
        } catch {
          if (lower.includes(kw.toLowerCase())) {
            return { label, tabKey: stage.id };
          }
        }
      }
    }
  }

  // 4. FASE 3: Coincidencia por nombre de etapa
  for (const stage of macroStages.value) {
    if (stage.name && (lower === stage.name.toLowerCase() || lower.includes(stage.name.toLowerCase()))) {
      return { label, tabKey: stage.id };
    }
  }

  // 5. Fallback si no hubo coincidencia dinámica previa
  if (lower.includes("borrador") || currNode === "borrador" || currNode === "start") return { label, tabKey: "borrador" };
  if (currNode === "eval_bp" || lower.includes("viabilidad")) return { label, tabKey: "eval_bp" };
  if (currNode === "aprob_bo" || lower.includes("patrocinio")) return { label, tabKey: "aprob_bo" };
  if (currNode === "aprob_vp" || lower.includes("vicepresiden")) return { label, tabKey: "aprob_vp" };
  if (currNode === "asig_demanda" || lower.includes("demanda") || lower.includes("líder ti")) return { label, tabKey: "asig_demanda" };
  if (currNode === "ventana_est" || currNode.includes("est_") || lower.includes("estimac")) return { label, tabKey: "ventana_est" };
  if (currNode === "planificacion" || currNode.includes("plan_") || lower.includes("planific") || currNode === "end") return { label, tabKey: "planificacion" };

  return { label, tabKey: "todas" };
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

function formatInstitucion(val: any): string {
  if (!val) return "";
  if (Array.isArray(val)) return val.join(", ");
  if (typeof val === "string") {
    const trimmed = val.trim();
    if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
      try {
        const parsed = JSON.parse(trimmed);
        if (Array.isArray(parsed)) return parsed.join(", ");
      } catch {
        return trimmed.replace(/[\[\]"']/g, "").trim();
      }
    }
    return trimmed;
  }
  return String(val);
}

function getKeyUserName(i: Initiative): string {
  const fd = i?.form_data || {};
  if (fd.registrador) return fd.registrador;
  if (fd.solicitante) return fd.solicitante;
  if (fd.lider_solicitante) return fd.lider_solicitante;
  if (fd.key_user) return fd.key_user;
  if (fd.nombre_solicitante) return fd.nombre_solicitante;
  if (fd.registrador_nombre) return fd.registrador_nombre;
  if (fd.registrador_email) return fd.registrador_email;

  if (Array.isArray(fd._observation_history) && fd._observation_history.length > 0) {
    const firstAction = fd._observation_history[0];
    if (firstAction?.user_name && firstAction.user_name !== "Sistema") {
      return firstAction.user_name;
    }
  }

  return "Sin registrador";
}

function getKeyUserInitials(i: Initiative): string {
  const name = getKeyUserName(i);
  const parts = name.trim().split(" ");
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return name.substring(0, 2).toUpperCase() || "US";
}

function getInitiativeBpTi(i: any): string {
  const fd = i?.form_data || {};
  return (
    fd.bp_ti_asignado ||
    fd.bp_ti_responsable ||
    fd.business_partner ||
    fd.bp_ti ||
    ""
  );
}

function getInitiativeTitle(i: Initiative): string {
  return i.summary?.titulo || i.form_data?.titulo || Object.values(i.form_data ?? {})[0] || i.id;
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
          // REGLA: Las iniciativas en estado borrador solo las puede visualizar el registrador de la misma
          const isMine = Boolean(
            (profile.value.id && i.user_id === profile.value.id) ||
            (profile.value.email && (i.form_data?.registrador_email === profile.value.email)) ||
            (profile.value.name && (i.form_data?.registrador === profile.value.name || i.form_data?.solicitante === profile.value.name))
          );
          if (!isMine) return false;

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
  if (process.client) {
    const saved = localStorage.getItem('iacs_user');
    if (saved) {
      try {
        const u = JSON.parse(saved);
        profile.value = {
          id: u.id || profile.value.id,
          name: u.name || profile.value.name,
          email: u.email || profile.value.email,
          role: u.roles?.[0] || u.role || profile.value.role,
          roles: u.roles || [profile.value.role],
        };
      } catch (e) {}
    }
  }
  loadData();
});

// ─── KPI Metrics ─────────────────────────────────────────────────────────────
const metrics = computed(() => {
  const total = initiatives.value.length;
  const enEvaluacion = initiatives.value.filter(i => {
    const k = getInitiativeStatusInfo(i).tabKey;
    return k === "eval_bp" || k === "aprob_bo" || k === "aprob_vp" || k === "asig_demanda";
  }).length;
  const enEstimacionPlan = initiatives.value.filter(i => {
    const k = getInitiativeStatusInfo(i).tabKey;
    return k === "estimacion" || k === "ventana_est" || k === "planificacion";
  }).length;
  const borradores = initiatives.value.filter(i => getInitiativeStatusInfo(i).tabKey === "borrador").length;

  return { total, enEvaluacion, enEstimacionPlan, borradores };
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
    const bp = getInitiativeBpTi(i);
    if (bp) set.add(bp);
  });
  return Array.from(set).sort().map(val => ({ label: val, value: val }));
});

// Filtered options within dropdown search
const filteredVpOptions = computed(() => {
  if (!filterSearch.value.trim()) return vicepresidenciasOptions.value;
  const q = filterSearch.value.toLowerCase();
  return vicepresidenciasOptions.value.filter(o => o.label.toLowerCase().includes(q));
});

const filteredRegistradoresOptions = computed(() => {
  if (!filterSearch.value.trim()) return registradoresOptions.value;
  const q = filterSearch.value.toLowerCase();
  return registradoresOptions.value.filter(o => o.label.toLowerCase().includes(q));
});

const filteredDireccionesOptions = computed(() => {
  if (!filterSearch.value.trim()) return direccionesOptions.value;
  const q = filterSearch.value.toLowerCase();
  return direccionesOptions.value.filter(o => o.label.toLowerCase().includes(q));
});

const filteredBpsOptions = computed(() => {
  if (!filterSearch.value.trim()) return bpsOptions.value;
  const q = filterSearch.value.toLowerCase();
  return bpsOptions.value.filter(o => o.label.toLowerCase().includes(q));
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
      const bp = getInitiativeBpTi(i);
      if (!bp || !selectedBPs.value.includes(bp)) return false;
    }
    if (selectedVicepresidencias.value.length > 0) {
      const vp = i.form_data?.vicepresidencia;
      if (!vp || !selectedVicepresidencias.value.includes(vp)) return false;
    }
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.toLowerCase();
      const title = (i.summary?.titulo ?? Object.values(i.form_data ?? {})[0] ?? "").toString().toLowerCase();
      const obj = (i.summary?.objetivo ?? i.form_data?.descripcion_de_la_necesidad ?? "").toString().toLowerCase();
      const id = i.id.toLowerCase();
      const idShort = (i.summary?.id_corta ?? "").toString().toLowerCase();
      const reg = (i.form_data?.registrador ?? "").toString().toLowerCase();
      const bp = getInitiativeBpTi(i).toLowerCase();
      if (!title.includes(q) && !obj.includes(q) && !id.includes(q) && !idShort.includes(q) && !reg.includes(q) && !bp.includes(q)) {
        return false;
      }
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
        valA = a.summary?.id_corta || a.id || "";
        valB = b.summary?.id_corta || b.id || "";
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
        valA = getInitiativeBpTi(a);
        valB = getInitiativeBpTi(b);
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

// ─── Pagination ──────────────────────────────────────────────────────────────
const totalFilteredCount = computed(() => sortedAndFiltered.value.length);
const totalPages = computed(() => Math.ceil(totalFilteredCount.value / pageSize.value) || 1);

const paginatedInitiatives = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return sortedAndFiltered.value.slice(start, start + pageSize.value);
});

// Reset page when filters change
watch([activeTab, searchQuery, showOnlyMine, selectedRegistradores, selectedDirecciones, selectedBPs, selectedVicepresidencias, pageSize], () => {
  currentPage.value = 1;
});

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
  activeTab.value = "todas";
};

const hasAnyFilterActive = computed(() => {
  return (
    selectedRegistradores.value.length > 0 ||
    selectedDirecciones.value.length > 0 ||
    selectedBPs.value.length > 0 ||
    selectedVicepresidencias.value.length > 0 ||
    showOnlyMine.value ||
    searchQuery.value.trim() !== ""
  );
});

const activeFilterCount = computed(() => {
  let count = 0;
  if (selectedRegistradores.value.length > 0) count += selectedRegistradores.value.length;
  if (selectedDirecciones.value.length > 0) count += selectedDirecciones.value.length;
  if (selectedBPs.value.length > 0) count += selectedBPs.value.length;
  if (selectedVicepresidencias.value.length > 0) count += selectedVicepresidencias.value.length;
  if (showOnlyMine.value) count += 1;
  if (searchQuery.value.trim() !== "") count += 1;
  return count;
});
</script>

<template>
  <div class="space-y-6" @click="closeFilterDropdowns">
    <!-- Header Section with Title & KPI Quick Cards -->
    <div class="space-y-4">
      <div class="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div class="flex items-center gap-2">
            <h2 class="text-2xl font-bold text-[#1E293B] tracking-tight">Bandeja de Revisión y Aprobación</h2>
            <span class="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#EEF2FF] text-[#4F5AF5] border border-[#4F5AF5]/20">
              Cartera TI
            </span>
          </div>
          <p class="text-sm text-[#64748B] mt-0.5">Gestión, evaluación y seguimiento de solicitudes de necesidades de TI.</p>
        </div>

        <div class="flex items-center gap-2.5">
          <button
            type="button"
            @click="loadData"
            :disabled="loading"
            class="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 transition-colors shadow-2xs cursor-pointer disabled:opacity-60"
            title="Sincronizar iniciativas con la base de datos"
          >
            <RefreshCw :class="['w-3.5 h-3.5 text-slate-500', loading ? 'animate-spin text-[#4F5AF5]' : '']" />
            <span>Actualizar</span>
          </button>

          <NuxtLink
            to="/nueva"
            class="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-xl bg-[#4F5AF5] hover:bg-[#3F49E0] text-white transition-all shadow-xs hover:shadow active:scale-[0.98] cursor-pointer"
          >
            <Sparkles class="w-3.5 h-3.5" />
            <span>Nueva Necesidad</span>
          </NuxtLink>
        </div>
      </div>

      <!-- KPI Summary Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <!-- Total -->
        <button
          type="button"
          @click="activeTab = 'todas'"
          :class="[
            'text-left p-3.5 rounded-2xl border transition-all cursor-pointer relative overflow-hidden group',
            activeTab === 'todas'
              ? 'bg-[#EEF2FF]/60 border-[#4F5AF5] ring-2 ring-[#4F5AF5]/20'
              : 'bg-white border-[#E2E8F0] hover:border-slate-300 hover:shadow-xs'
          ]"
        >
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-slate-500">Total en Cartera</span>
            <div class="w-7 h-7 rounded-xl bg-slate-100 group-hover:bg-[#EEF2FF] text-slate-600 group-hover:text-[#4F5AF5] flex items-center justify-center transition-colors">
              <Layers class="w-3.5 h-3.5" />
            </div>
          </div>
          <div class="mt-2 flex items-baseline gap-2">
            <span class="text-2xl font-bold text-slate-900">{{ metrics.total }}</span>
            <span class="text-[11px] text-slate-400">iniciativas</span>
          </div>
        </button>

        <!-- En Evaluación -->
        <button
          type="button"
          @click="activeTab = 'eval_bp'"
          :class="[
            'text-left p-3.5 rounded-2xl border transition-all cursor-pointer relative overflow-hidden group',
            activeTab === 'eval_bp' || activeTab === 'aprob_bo' || activeTab === 'aprob_vp'
              ? 'bg-indigo-50/60 border-indigo-500 ring-2 ring-indigo-500/20'
              : 'bg-white border-[#E2E8F0] hover:border-slate-300 hover:shadow-xs'
          ]"
        >
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-slate-500">En Evaluación / Aprobación</span>
            <div class="w-7 h-7 rounded-xl bg-indigo-50 group-hover:bg-indigo-100 text-indigo-600 flex items-center justify-center transition-colors">
              <Shield class="w-3.5 h-3.5" />
            </div>
          </div>
          <div class="mt-2 flex items-baseline gap-2">
            <span class="text-2xl font-bold text-indigo-700">{{ metrics.enEvaluacion }}</span>
            <span class="text-[11px] text-indigo-500/80">requieren dictamen</span>
          </div>
        </button>

        <!-- En Estimación y Plan -->
        <button
          type="button"
          @click="activeTab = 'planificacion'"
          :class="[
            'text-left p-3.5 rounded-2xl border transition-all cursor-pointer relative overflow-hidden group',
            activeTab === 'estimacion' || activeTab === 'planificacion'
              ? 'bg-emerald-50/60 border-emerald-500 ring-2 ring-emerald-500/20'
              : 'bg-white border-[#E2E8F0] hover:border-slate-300 hover:shadow-xs'
          ]"
        >
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-slate-500">Estimación y Plan</span>
            <div class="w-7 h-7 rounded-xl bg-emerald-50 group-hover:bg-emerald-100 text-emerald-600 flex items-center justify-center transition-colors">
              <CheckCircle2 class="w-3.5 h-3.5" />
            </div>
          </div>
          <div class="mt-2 flex items-baseline gap-2">
            <span class="text-2xl font-bold text-emerald-700">{{ metrics.enEstimacionPlan }}</span>
            <span class="text-[11px] text-emerald-600/80">en dimensionamiento</span>
          </div>
        </button>

        <!-- Borradores -->
        <button
          type="button"
          @click="activeTab = 'borrador'"
          :class="[
            'text-left p-3.5 rounded-2xl border transition-all cursor-pointer relative overflow-hidden group',
            activeTab === 'borrador'
              ? 'bg-amber-50/60 border-amber-500 ring-2 ring-amber-500/20'
              : 'bg-white border-[#E2E8F0] hover:border-slate-300 hover:shadow-xs'
          ]"
        >
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-slate-500">Borradores en Curso</span>
            <div class="w-7 h-7 rounded-xl bg-amber-50 group-hover:bg-amber-100 text-amber-600 flex items-center justify-center transition-colors">
              <FileText class="w-3.5 h-3.5" />
            </div>
          </div>
          <div class="mt-2 flex items-baseline gap-2">
            <span class="text-2xl font-bold text-amber-700">{{ metrics.borradores }}</span>
            <span class="text-[11px] text-amber-600/80">por enviar</span>
          </div>
        </button>
      </div>
    </div>

    <!-- Top Filter Bar -->
    <div class="bg-white rounded-2xl border border-[#E2E8F0] p-4 space-y-3.5 shadow-sm" @click.stop>
      <div class="flex items-center justify-between flex-wrap gap-2 pb-2.5 border-b border-[#F1F5F9]">
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 rounded-lg bg-[#EEF2FF] flex items-center justify-center text-[#4F5AF5]">
            <Filter class="w-3.5 h-3.5" />
          </div>
          <h3 class="font-bold text-xs text-[#1E293B] uppercase tracking-wider">
            Filtros y Búsqueda Avanzada
          </h3>
          <span v-if="activeFilterCount > 0" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#4F5AF5] text-white">
            {{ activeFilterCount }} activo{{ activeFilterCount > 1 ? 's' : '' }}
          </span>
        </div>
        <button
          v-if="hasAnyFilterActive"
          @click="clearAllFilters"
          class="text-xs font-semibold text-[#4F5AF5] hover:text-[#3F49E0] transition-colors flex items-center gap-1 cursor-pointer"
        >
          <RotateCcw class="w-3 h-3" />
          Limpiar Todos los Filtros
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-12 gap-2.5 items-center">
        <!-- Search query input -->
        <div class="relative md:col-span-5">
          <Search class="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Buscar por título, objetivo, código ID o responsable..."
            v-model="searchQuery"
            class="w-full text-xs pl-9 pr-8 py-2.5 rounded-xl border border-[#E2E8F0] focus:border-[#4F5AF5] focus:ring-1 focus:ring-[#4F5AF5] focus:outline-none placeholder-[#94A3B8] bg-white font-medium transition-all"
          />
          <button
            v-if="searchQuery"
            type="button"
            @click="searchQuery = ''"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5 rounded-md hover:bg-slate-100"
            title="Limpiar búsqueda"
          >
            <X class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- Solo mías button -->
        <button
          type="button"
          @click="showOnlyMine = !showOnlyMine"
          :class="[
            'md:col-span-2 flex items-center justify-center gap-1.5 px-3 py-2.5 text-xs font-semibold rounded-xl border transition-all cursor-pointer select-none',
            showOnlyMine
              ? 'bg-[#4F5AF5] text-white border-[#4F5AF5] shadow-xs'
              : 'bg-white text-[#1E293B] border-[#E2E8F0] hover:bg-[#F8FAFC]'
          ]"
        >
          <User class="w-3.5 h-3.5 shrink-0" />
          <span class="truncate">Ver solo mías</span>
        </button>

        <!-- Dropdowns VP, Key user, Dirección, BP TI -->
        <div class="md:col-span-5 grid grid-cols-2 sm:grid-cols-4 gap-2">
          <!-- Vicepresidencia -->
          <div class="relative">
            <button
              type="button"
              @click.stop="toggleFilterDropdown('vp')"
              :class="[
                'w-full flex items-center justify-between gap-1.5 px-2.5 py-2.5 text-xs font-semibold rounded-xl border transition-all cursor-pointer',
                selectedVicepresidencias.length > 0 ? 'bg-[#EEF2FF] text-[#4F5AF5] border-[#4F5AF5] shadow-xs' : 'bg-white text-[#1E293B] border-[#E2E8F0] hover:bg-[#F8FAFC]'
              ]"
            >
              <span class="truncate text-[11px]">Vicepresidencia</span>
              <div class="flex items-center gap-1 shrink-0">
                <span v-if="selectedVicepresidencias.length > 0" class="bg-[#4F5AF5] text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full leading-none">
                  {{ selectedVicepresidencias.length }}
                </span>
                <ChevronDown :class="['w-3.5 h-3.5 text-slate-400 transition-transform duration-150', filterDropdownOpen === 'vp' ? 'rotate-180 text-[#4F5AF5]' : '']" />
              </div>
            </button>
            <div v-if="filterDropdownOpen === 'vp'" class="absolute left-0 mt-1.5 w-64 bg-white rounded-xl border border-[#E2E8F0] shadow-xl z-50 p-2.5 space-y-2 animate-in fade-in duration-150">
              <input
                type="text"
                v-model="filterSearch"
                placeholder="Buscar vicepresidencia..."
                class="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:border-[#4F5AF5] focus:outline-none"
              />
              <div class="max-h-48 overflow-y-auto space-y-0.5 pr-1 divide-y divide-slate-100">
                <label v-for="opt in filteredVpOptions" :key="opt.value" class="flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs hover:bg-[#F8FAFC] cursor-pointer text-[#1E293B]">
                  <input
                    type="checkbox"
                    :checked="selectedVicepresidencias.includes(opt.value)"
                    @change="selectedVicepresidencias.includes(opt.value) ? selectedVicepresidencias = selectedVicepresidencias.filter(x => x !== opt.value) : selectedVicepresidencias = [...selectedVicepresidencias, opt.value]"
                    class="rounded border-slate-300 text-[#4F5AF5] focus:ring-[#4F5AF5]"
                  />
                  <span class="truncate font-medium">{{ opt.label }}</span>
                </label>
                <div v-if="filteredVpOptions.length === 0" class="text-[11px] text-slate-400 py-2 text-center">
                  Sin coincidencias
                </div>
              </div>
              <div v-if="selectedVicepresidencias.length > 0" class="pt-1 border-t border-slate-100 text-right">
                <button @click="selectedVicepresidencias = []" class="text-[10px] font-semibold text-rose-600 hover:underline">Limpiar selección</button>
              </div>
            </div>
          </div>

          <!-- Key User -->
          <div class="relative">
            <button
              type="button"
              @click.stop="toggleFilterDropdown('key_user')"
              :class="[
                'w-full flex items-center justify-between gap-1.5 px-2.5 py-2.5 text-xs font-semibold rounded-xl border transition-all cursor-pointer',
                selectedRegistradores.length > 0 ? 'bg-[#EEF2FF] text-[#4F5AF5] border-[#4F5AF5] shadow-xs' : 'bg-white text-[#1E293B] border-[#E2E8F0] hover:bg-[#F8FAFC]'
              ]"
            >
              <span class="truncate text-[11px]">Key user</span>
              <div class="flex items-center gap-1 shrink-0">
                <span v-if="selectedRegistradores.length > 0" class="bg-[#4F5AF5] text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full leading-none">
                  {{ selectedRegistradores.length }}
                </span>
                <ChevronDown :class="['w-3.5 h-3.5 text-slate-400 transition-transform duration-150', filterDropdownOpen === 'key_user' ? 'rotate-180 text-[#4F5AF5]' : '']" />
              </div>
            </button>
            <div v-if="filterDropdownOpen === 'key_user'" class="absolute left-0 mt-1.5 w-64 bg-white rounded-xl border border-[#E2E8F0] shadow-xl z-50 p-2.5 space-y-2 animate-in fade-in duration-150">
              <input
                type="text"
                v-model="filterSearch"
                placeholder="Buscar key user..."
                class="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:border-[#4F5AF5] focus:outline-none"
              />
              <div class="max-h-48 overflow-y-auto space-y-0.5 pr-1 divide-y divide-slate-100">
                <label v-for="opt in filteredRegistradoresOptions" :key="opt.value" class="flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs hover:bg-[#F8FAFC] cursor-pointer text-[#1E293B]">
                  <input
                    type="checkbox"
                    :checked="selectedRegistradores.includes(opt.value)"
                    @change="selectedRegistradores.includes(opt.value) ? selectedRegistradores = selectedRegistradores.filter(x => x !== opt.value) : selectedRegistradores = [...selectedRegistradores, opt.value]"
                    class="rounded border-slate-300 text-[#4F5AF5] focus:ring-[#4F5AF5]"
                  />
                  <span class="truncate font-medium">{{ opt.label }}</span>
                </label>
                <div v-if="filteredRegistradoresOptions.length === 0" class="text-[11px] text-slate-400 py-2 text-center">
                  Sin coincidencias
                </div>
              </div>
              <div v-if="selectedRegistradores.length > 0" class="pt-1 border-t border-slate-100 text-right">
                <button @click="selectedRegistradores = []" class="text-[10px] font-semibold text-rose-600 hover:underline">Limpiar selección</button>
              </div>
            </div>
          </div>

          <!-- Dirección -->
          <div class="relative">
            <button
              type="button"
              @click.stop="toggleFilterDropdown('dir')"
              :class="[
                'w-full flex items-center justify-between gap-1.5 px-2.5 py-2.5 text-xs font-semibold rounded-xl border transition-all cursor-pointer',
                selectedDirecciones.length > 0 ? 'bg-[#EEF2FF] text-[#4F5AF5] border-[#4F5AF5] shadow-xs' : 'bg-white text-[#1E293B] border-[#E2E8F0] hover:bg-[#F8FAFC]'
              ]"
            >
              <span class="truncate text-[11px]">Dirección</span>
              <div class="flex items-center gap-1 shrink-0">
                <span v-if="selectedDirecciones.length > 0" class="bg-[#4F5AF5] text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full leading-none">
                  {{ selectedDirecciones.length }}
                </span>
                <ChevronDown :class="['w-3.5 h-3.5 text-slate-400 transition-transform duration-150', filterDropdownOpen === 'dir' ? 'rotate-180 text-[#4F5AF5]' : '']" />
              </div>
            </button>
            <div v-if="filterDropdownOpen === 'dir'" class="absolute left-0 mt-1.5 w-64 bg-white rounded-xl border border-[#E2E8F0] shadow-xl z-50 p-2.5 space-y-2 animate-in fade-in duration-150">
              <input
                type="text"
                v-model="filterSearch"
                placeholder="Buscar dirección..."
                class="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:border-[#4F5AF5] focus:outline-none"
              />
              <div class="max-h-48 overflow-y-auto space-y-0.5 pr-1 divide-y divide-slate-100">
                <label v-for="opt in filteredDireccionesOptions" :key="opt.value" class="flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs hover:bg-[#F8FAFC] cursor-pointer text-[#1E293B]">
                  <input
                    type="checkbox"
                    :checked="selectedDirecciones.includes(opt.value)"
                    @change="selectedDirecciones.includes(opt.value) ? selectedDirecciones = selectedDirecciones.filter(x => x !== opt.value) : selectedDirecciones = [...selectedDirecciones, opt.value]"
                    class="rounded border-slate-300 text-[#4F5AF5] focus:ring-[#4F5AF5]"
                  />
                  <span class="truncate font-medium">{{ opt.label }}</span>
                </label>
                <div v-if="filteredDireccionesOptions.length === 0" class="text-[11px] text-slate-400 py-2 text-center">
                  Sin coincidencias
                </div>
              </div>
              <div v-if="selectedDirecciones.length > 0" class="pt-1 border-t border-slate-100 text-right">
                <button @click="selectedDirecciones = []" class="text-[10px] font-semibold text-rose-600 hover:underline">Limpiar selección</button>
              </div>
            </div>
          </div>

          <!-- BP TI -->
          <div class="relative">
            <button
              type="button"
              @click.stop="toggleFilterDropdown('bpti')"
              :class="[
                'w-full flex items-center justify-between gap-1.5 px-2.5 py-2.5 text-xs font-semibold rounded-xl border transition-all cursor-pointer',
                selectedBPs.length > 0 ? 'bg-[#EEF2FF] text-[#4F5AF5] border-[#4F5AF5] shadow-xs' : 'bg-white text-[#1E293B] border-[#E2E8F0] hover:bg-[#F8FAFC]'
              ]"
            >
              <span class="truncate text-[11px]">BP TI</span>
              <div class="flex items-center gap-1 shrink-0">
                <span v-if="selectedBPs.length > 0" class="bg-[#4F5AF5] text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full leading-none">
                  {{ selectedBPs.length }}
                </span>
                <ChevronDown :class="['w-3.5 h-3.5 text-slate-400 transition-transform duration-150', filterDropdownOpen === 'bpti' ? 'rotate-180 text-[#4F5AF5]' : '']" />
              </div>
            </button>
            <div v-if="filterDropdownOpen === 'bpti'" class="absolute right-0 sm:left-0 mt-1.5 w-64 bg-white rounded-xl border border-[#E2E8F0] shadow-xl z-50 p-2.5 space-y-2 animate-in fade-in duration-150">
              <input
                type="text"
                v-model="filterSearch"
                placeholder="Buscar BP TI..."
                class="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:border-[#4F5AF5] focus:outline-none"
              />
              <div class="max-h-48 overflow-y-auto space-y-0.5 pr-1 divide-y divide-slate-100">
                <label v-for="opt in filteredBpsOptions" :key="opt.value" class="flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs hover:bg-[#F8FAFC] cursor-pointer text-[#1E293B]">
                  <input
                    type="checkbox"
                    :checked="selectedBPs.includes(opt.value)"
                    @change="selectedBPs.includes(opt.value) ? selectedBPs = selectedBPs.filter(x => x !== opt.value) : selectedBPs = [...selectedBPs, opt.value]"
                    class="rounded border-slate-300 text-[#4F5AF5] focus:ring-[#4F5AF5]"
                  />
                  <span class="truncate font-medium">{{ opt.label }}</span>
                </label>
                <div v-if="filteredBpsOptions.length === 0" class="text-[11px] text-slate-400 py-2 text-center">
                  Sin coincidencias
                </div>
              </div>
              <div v-if="selectedBPs.length > 0" class="pt-1 border-t border-slate-100 text-right">
                <button @click="selectedBPs = []" class="text-[10px] font-semibold text-rose-600 hover:underline">Limpiar selección</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Active Filters Tray / Chips -->
      <div v-if="hasAnyFilterActive" class="flex items-center gap-2 flex-wrap pt-2 border-t border-slate-100 text-xs">
        <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Filtros aplicados:</span>

        <span v-if="searchQuery.trim()" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-medium">
          Texto: "{{ searchQuery }}"
          <button @click="searchQuery = ''" class="hover:text-rose-500"><X class="w-3 h-3" /></button>
        </span>

        <span v-if="showOnlyMine" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200/60 font-medium">
          Solo mías
          <button @click="showOnlyMine = false" class="hover:text-rose-500"><X class="w-3 h-3" /></button>
        </span>

        <span v-for="vp in selectedVicepresidencias" :key="vp" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200/60 font-medium">
          VP: {{ vp }}
          <button @click="selectedVicepresidencias = selectedVicepresidencias.filter(x => x !== vp)" class="hover:text-rose-500"><X class="w-3 h-3" /></button>
        </span>

        <span v-for="dir in selectedDirecciones" :key="dir" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-medium">
          Dir: {{ dir }}
          <button @click="selectedDirecciones = selectedDirecciones.filter(x => x !== dir)" class="hover:text-rose-500"><X class="w-3 h-3" /></button>
        </span>

        <span v-for="ku in selectedRegistradores" :key="ku" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-medium">
          Key: {{ ku }}
          <button @click="selectedRegistradores = selectedRegistradores.filter(x => x !== ku)" class="hover:text-rose-500"><X class="w-3 h-3" /></button>
        </span>

        <span v-for="bp in selectedBPs" :key="bp" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-medium">
          BP: {{ bp }}
          <button @click="selectedBPs = selectedBPs.filter(x => x !== bp)" class="hover:text-rose-500"><X class="w-3 h-3" /></button>
        </span>
      </div>
    </div>

    <!-- Main Board Table -->
    <div class="bg-white rounded-2xl border border-[#E2E8F0] shadow-sm relative overflow-hidden">
      <!-- Tabs Navigation & Column Customizer -->
      <div class="border-b border-[#F1F5F9] px-6 pt-3 flex items-center justify-between gap-3 flex-wrap rounded-t-2xl bg-white relative z-20">
        <!-- Tabs strip with smooth scroll -->
        <div class="flex gap-1 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          <button
            v-for="tab in TABS"
            :key="tab.key"
            @click="activeTab = tab.key"
            :class="[
              'pb-3 px-3.5 text-xs font-semibold border-b-2 flex items-center gap-2 transition-all whitespace-nowrap cursor-pointer select-none',
              activeTab === tab.key
                ? 'border-[#4F5AF5] text-[#4F5AF5]'
                : countByTab(tab.key) > 0
                  ? 'border-transparent text-slate-600 hover:text-slate-900'
                  : 'border-transparent text-slate-400 hover:text-slate-600 opacity-70'
            ]"
          >
            <span :class="['w-1.5 h-1.5 rounded-full shrink-0', tab.dot, countByTab(tab.key) === 0 ? 'opacity-40' : '']" />
            <span>{{ tab.label }}</span>
            <span
              :class="[
                'text-[10px] px-1.5 py-0.5 rounded-full font-bold transition-colors',
                activeTab === tab.key
                  ? 'bg-[#EEF2FF] text-[#4F5AF5]'
                  : countByTab(tab.key) > 0
                    ? 'bg-slate-100 text-slate-700 font-semibold'
                    : 'bg-slate-50 text-slate-400'
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
            class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border border-[#E2E8F0] bg-white hover:bg-[#F8FAFC] text-[#1E293B] shadow-2xs transition-colors cursor-pointer"
          >
            <SlidersHorizontal class="w-3.5 h-3.5 text-[#4F5AF5]" />
            <span>Columnas</span>
            <span class="text-[10px] font-bold bg-[#EEF2FF] text-[#4F5AF5] px-1.5 py-0.5 rounded-full">
              {{ visibleColumns.length }}/{{ ALL_COLUMNS.length }}
            </span>
            <ChevronDown :class="['w-3 h-3 text-slate-400 transition-transform duration-150', columnsMenuOpen ? 'rotate-180' : '']" />
          </button>

          <div v-if="columnsMenuOpen" class="absolute right-0 top-full mt-2 w-72 bg-white rounded-xl border border-[#E2E8F0] shadow-2xl z-50 p-3 space-y-2.5 animate-in fade-in duration-150" @click.stop>
            <div class="flex items-center justify-between border-b border-[#F1F5F9] pb-2">
              <div>
                <h4 class="text-xs font-bold text-[#1E293B]">Columnas de la tabla</h4>
                <p class="text-[10px] text-slate-400">Personaliza las columnas visibles</p>
              </div>
              <button
                type="button"
                @click="handleResetColumns"
                class="text-[11px] font-medium text-slate-500 hover:text-[#4F5AF5] flex items-center gap-1 transition-colors cursor-pointer"
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

      <!-- Table Content Area -->
      <div class="p-0 overflow-x-auto relative">
        <div v-if="loading" class="py-20 bg-white flex items-center justify-center">
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

        <!-- Empty State -->
        <div v-else-if="sortedAndFiltered.length === 0" class="py-16 px-6 text-center space-y-3">
          <div class="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
            <Search class="w-6 h-6" />
          </div>
          <div class="max-w-md mx-auto">
            <h4 class="text-sm font-bold text-slate-800">No se encontraron solicitudes</h4>
            <p class="text-xs text-slate-500 mt-1">
              No hay iniciativas que coincidan con la búsqueda o los filtros aplicados en esta sección.
            </p>
          </div>
          <div class="pt-2">
            <button
              type="button"
              @click="clearAllFilters"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-50 text-[#4F5AF5] hover:bg-indigo-100 transition-colors cursor-pointer"
            >
              <RotateCcw class="w-3 h-3" />
              Restablecer filtros
            </button>
          </div>
        </div>

        <!-- Data Table -->
        <table v-else class="w-full text-left border-collapse table-fixed" :style="{ minWidth: `${Math.max(totalTableWidth, 1150)}px` }">
          <thead>
            <tr class="border-b border-[#F1F5F9] bg-[#F8FAFC] text-[11px] font-bold text-[#64748B] uppercase tracking-wider relative">
              <th
                v-for="colId in visibleColumns"
                :key="colId"
                :style="{ width: `${columnWidths[colId] || 150}px` }"
                :class="[
                  'px-4 py-3.5 select-none relative',
                  colId === 'acciones'
                    ? 'sticky right-0 bg-[#F8FAFC] z-20 text-center'
                    : ''
                ]"
              >
                <div
                  @click="colId !== 'acciones' && handleSort(colId as any)"
                  :class="[
                    'flex items-center gap-1.5 min-w-0',
                    colId !== 'acciones' ? 'cursor-pointer hover:text-[#4F5AF5]' : 'justify-center'
                  ]"
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
            <tr
              v-for="i in paginatedInitiatives"
              :key="i.id"
              class="hover:bg-[#F8FAFC]/80 transition-colors group cursor-pointer"
              @click="selectedInitiative = i"
            >
              <td
                v-for="colId in visibleColumns"
                :key="colId"
                :class="[
                  'px-4 py-3.5 text-xs align-middle',
                  colId === 'acciones'
                    ? 'sticky right-0 bg-white group-hover:bg-[#F8FAFC] z-10 text-center'
                    : ''
                ]"
              >
                <!-- Código ID -->
                <div v-if="colId === 'codigo'" class="flex items-center gap-1.5 whitespace-nowrap">
                  <span class="text-[11px] font-mono font-semibold text-[#4F5AF5] bg-[#EEF2FF] px-2 py-0.5 rounded-md border border-[#4F5AF5]/20">
                    #{{ i.summary?.id_corta || i.id.slice(0, 8) }}
                  </span>
                  <button
                    type="button"
                    @click.stop="copyToClipboard(i.id)"
                    class="p-1 text-slate-400 hover:text-[#4F5AF5] hover:bg-slate-100 rounded transition-colors cursor-pointer"
                    :title="copiedId === i.id ? '¡ID Copiado!' : 'Copiar ID completo'"
                  >
                    <Check v-if="copiedId === i.id" class="w-3.5 h-3.5 text-emerald-600 animate-in zoom-in-75 duration-150" />
                    <Copy v-else class="w-3.5 h-3.5" />
                  </button>
                </div>

                <!-- Solicitud -->
                <div v-else-if="colId === 'solicitud'" class="min-w-0 pr-2">
                  <NuxtLink
                    :to="i.status === 'Borrador' ? `/nueva?id=${i.id}` : `/iniciativa/${i.id}`"
                    @click.stop
                    class="font-semibold text-[#1E293B] hover:text-[#4F5AF5] text-xs leading-snug line-clamp-2 transition-colors block"
                    :title="getInitiativeTitle(i)"
                  >
                    {{ getInitiativeTitle(i) }}
                  </NuxtLink>
                  <p v-if="i.summary?.objetivo" class="text-[11px] text-slate-400 line-clamp-1 mt-0.5" :title="i.summary.objetivo">
                    {{ i.summary.objetivo }}
                  </p>
                </div>

                <!-- Vicepresidencia -->
                <div v-else-if="colId === 'vicepresidencia'">
                  <span
                    v-if="i.form_data?.vicepresidencia"
                    class="text-[11px] font-semibold text-indigo-700 bg-indigo-50/80 border border-indigo-100 px-2.5 py-0.5 rounded-md inline-block max-w-[135px] truncate"
                    :title="i.form_data.vicepresidencia"
                  >
                    {{ i.form_data.vicepresidencia }}
                  </span>
                  <span v-else class="text-xs text-slate-400 italic">—</span>
                </div>

                <!-- Dirección -->
                <div v-else-if="colId === 'direccion'">
                  <span
                    v-if="i.form_data?.direccion"
                    class="text-[11px] font-medium text-slate-700 bg-slate-100/80 border border-slate-200/80 px-2 py-0.5 rounded-md inline-block max-w-[155px] truncate"
                    :title="i.form_data.direccion"
                  >
                    {{ i.form_data.direccion }}
                  </span>
                  <span v-else class="text-xs text-slate-400 italic">—</span>
                </div>

                <!-- Fecha -->
                <div v-else-if="colId === 'fecha'" class="whitespace-nowrap">
                  <p class="text-xs text-[#1E293B] font-medium">{{ formatDate(i.created_at) }}</p>
                  <p class="text-[10px] text-slate-400 flex items-center gap-1">
                    <Clock class="w-2.5 h-2.5" />
                    {{ formatTime(i.created_at) }}
                  </p>
                </div>

                <!-- Key user -->
                <div v-else-if="colId === 'key_user'">
                  <div class="flex items-center gap-2">
                    <div class="w-7 h-7 rounded-full bg-gradient-to-br from-[#4F5AF5] to-indigo-600 flex items-center justify-center text-[10px] font-bold text-white shrink-0 shadow-2xs uppercase">
                      {{ getKeyUserInitials(i) }}
                    </div>
                    <div class="min-w-0 flex-1">
                      <p class="text-xs text-[#1E293B] font-semibold truncate" :title="getKeyUserName(i)">
                        {{ getKeyUserName(i) }}
                      </p>
                      <div v-if="formatInstitucion(i.form_data?.institucion)" class="mt-0.5">
                        <span class="inline-block text-[10px] font-medium text-slate-600 bg-slate-100 border border-slate-200/80 px-1.5 py-0.2 rounded leading-tight">
                          {{ formatInstitucion(i.form_data?.institucion) }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- BP TI -->
                <div v-else-if="colId === 'bp'">
                  <div v-if="getInitiativeBpTi(i)" class="flex items-center gap-1.5 text-xs font-medium text-slate-800">
                    <div class="w-5 h-5 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-[9px] font-bold text-slate-600 shrink-0">
                      {{ getInitiativeBpTi(i).substring(0, 2).toUpperCase() }}
                    </div>
                    <span class="truncate" :title="getInitiativeBpTi(i)">{{ getInitiativeBpTi(i) }}</span>
                  </div>
                  <div v-else class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-amber-50 text-amber-700 border border-amber-200/70">
                    <AlertCircle class="w-3 h-3 text-amber-600 shrink-0" />
                    <span>Sin asignar</span>
                  </div>
                </div>

                <!-- Estado Actual -->
                <div v-else-if="colId === 'estado'">
                  <span
                    :class="[
                      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap shadow-2xs border',
                      STATUS_BADGE_STYLE[getInitiativeStatusInfo(i).tabKey] || 'bg-slate-100 text-slate-600 border-slate-200'
                    ]"
                  >
                    <span :class="['w-2 h-2 rounded-full shrink-0', STATUS_DOT_STYLE[getInitiativeStatusInfo(i).tabKey] || 'bg-slate-400']" />
                    <span class="truncate max-w-[180px]" :title="getInitiativeStatusInfo(i).label">
                      {{ getInitiativeStatusInfo(i).label }}
                    </span>
                  </span>
                </div>

                <!-- Acciones (Centradas y sin línea divisoria) -->
                <div v-else-if="colId === 'acciones'" class="flex items-center justify-center gap-1.5 whitespace-nowrap">
                  <button
                    type="button"
                    @click.stop="selectedInitiative = i"
                    class="p-2 text-slate-400 hover:text-[#4F5AF5] hover:bg-indigo-50/80 rounded-lg transition-colors cursor-pointer"
                    title="Vista rápida del expediente"
                  >
                    <Eye class="w-4 h-4" />
                  </button>
                  <NuxtLink
                    :to="i.status === 'Borrador' ? `/nueva?id=${i.id}` : `/iniciativa/${i.id}`"
                    @click.stop
                    class="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[#4F5AF5] hover:bg-[#3F49E0] text-xs font-semibold text-white transition-all cursor-pointer shadow-2xs hover:shadow-xs active:scale-[0.98]"
                  >
                    <span>{{ i.status === 'Borrador' ? 'Editar' : 'Abrir' }}</span>
                    <ArrowRight class="w-3 h-3" />
                  </NuxtLink>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination & Results Bar -->
      <div v-if="!loading && totalFilteredCount > 0" class="border-t border-[#F1F5F9] px-6 py-3.5 bg-[#F8FAFC] flex items-center justify-between flex-wrap gap-3 text-xs text-slate-600">
        <div class="flex items-center gap-2">
          <span>Mostrando</span>
          <span class="font-bold text-slate-800">
            {{ (currentPage - 1) * pageSize + 1 }} - {{ Math.min(currentPage * pageSize, totalFilteredCount) }}
          </span>
          <span>de</span>
          <span class="font-bold text-slate-800">{{ totalFilteredCount }}</span>
          <span>iniciativas</span>
        </div>

        <div class="flex items-center gap-3">
          <!-- Page Size Selector -->
          <div class="flex items-center gap-1.5">
            <span class="text-slate-400">Filas:</span>
            <select
              v-model="pageSize"
              class="border border-slate-200 rounded-lg px-2 py-1 bg-white text-xs font-semibold text-slate-700 focus:outline-none focus:border-[#4F5AF5]"
            >
              <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}</option>
            </select>
          </div>

          <!-- Page Navigation -->
          <div class="flex items-center gap-1">
            <button
              type="button"
              :disabled="currentPage <= 1"
              @click="currentPage--"
              class="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              title="Página anterior"
            >
              <ChevronLeft class="w-3.5 h-3.5" />
            </button>

            <span class="px-2 font-semibold text-slate-700">
              {{ currentPage }} / {{ totalPages }}
            </span>

            <button
              type="button"
              :disabled="currentPage >= totalPages"
              @click="currentPage++"
              class="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              title="Página siguiente"
            >
              <ChevronRight class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Preview Slide-over Drawer -->
    <div v-if="selectedInitiative" class="fixed inset-0 z-[150] overflow-hidden" @click="selectedInitiative = null">
      <div class="absolute inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity animate-in fade-in duration-200" />
      
      <div class="fixed inset-y-0 right-0 max-w-full flex pl-10" @click.stop>
        <div class="w-screen max-w-lg bg-white shadow-2xl border-l border-slate-200 flex flex-col animate-in slide-in-from-right duration-200">
          <!-- Drawer Header -->
          <div class="px-6 py-5 border-b border-slate-100 flex items-start justify-between gap-4 bg-gradient-to-r from-slate-50 to-white">
            <div class="min-w-0 space-y-1.5">
              <div class="flex items-center gap-2">
                <span class="text-xs font-mono font-bold text-[#4F5AF5] bg-[#EEF2FF] px-2.5 py-0.5 rounded-md border border-[#4F5AF5]/20">
                  #{{ selectedInitiative.summary?.id_corta || selectedInitiative.id.slice(0, 8) }}
                </span>
                <span
                  :class="[
                    'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border',
                    STATUS_BADGE_STYLE[getInitiativeStatusInfo(selectedInitiative).tabKey] || 'bg-slate-100 text-slate-600'
                  ]"
                >
                  <span :class="['w-1.5 h-1.5 rounded-full', STATUS_DOT_STYLE[getInitiativeStatusInfo(selectedInitiative).tabKey] || 'bg-slate-400']" />
                  {{ getInitiativeStatusInfo(selectedInitiative).label }}
                </span>
              </div>
              <h3 class="text-base font-bold text-[#1E293B] leading-snug">
                {{ getInitiativeTitle(selectedInitiative) }}
              </h3>
            </div>
            <button
              type="button"
              @click="selectedInitiative = null"
              class="w-8 h-8 rounded-xl border border-slate-200 flex items-center justify-center text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer shrink-0"
            >
              <X class="w-4 h-4" />
            </button>
          </div>

          <!-- Drawer Body -->
          <div class="overflow-y-auto flex-1 p-6 space-y-5 text-sm text-slate-700">
            <!-- Metadata Cards -->
            <div class="grid grid-cols-2 gap-3 p-4 rounded-2xl bg-slate-50 border border-slate-200/70 text-xs">
              <div class="space-y-1">
                <span class="text-slate-400 font-medium">Vicepresidencia</span>
                <p class="font-bold text-slate-800">{{ selectedInitiative.form_data?.vicepresidencia || '—' }}</p>
              </div>
              <div class="space-y-1">
                <span class="text-slate-400 font-medium">Dirección</span>
                <p class="font-bold text-slate-800">{{ selectedInitiative.form_data?.direccion || '—' }}</p>
              </div>
              <div class="space-y-1 pt-2 border-t border-slate-200/50">
                <span class="text-slate-400 font-medium">Key User / Solicitante</span>
                <p class="font-bold text-slate-800">{{ getKeyUserName(selectedInitiative) }}</p>
                <p v-if="formatInstitucion(selectedInitiative.form_data?.institucion)" class="text-[10px] text-indigo-600 font-semibold">
                  Institución: {{ formatInstitucion(selectedInitiative.form_data?.institucion) }}
                </p>
              </div>
              <div class="space-y-1 pt-2 border-t border-slate-200/50">
                <span class="text-slate-400 font-medium">BP TI Asignado</span>
                <p :class="['font-bold', getInitiativeBpTi(selectedInitiative) ? 'text-slate-800' : 'text-amber-600']">
                  {{ getInitiativeBpTi(selectedInitiative) || 'Sin asignar' }}
                </p>
              </div>
              <div class="space-y-1 pt-2 border-t border-slate-200/50 col-span-2">
                <span class="text-slate-400 font-medium">Fecha de Registro</span>
                <p class="font-medium text-slate-700">
                  {{ formatDate(selectedInitiative.created_at) }} a las {{ formatTime(selectedInitiative.created_at) }}
                </p>
              </div>
            </div>

            <!-- Objective Section -->
            <div v-if="selectedInitiative.summary?.objetivo" class="space-y-1.5">
              <h4 class="font-bold text-xs uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <Sparkles class="w-3.5 h-3.5 text-[#4F5AF5]" />
                Objetivo de la Solicitud
              </h4>
              <div class="bg-indigo-50/50 p-4 rounded-2xl border border-indigo-100 text-slate-800 text-xs leading-relaxed">
                {{ selectedInitiative.summary.objetivo }}
              </div>
            </div>

            <!-- Problem / Need Description -->
            <div v-if="selectedInitiative.form_data?.descripcion_de_la_necesidad || selectedInitiative.summary?.descripcionProblema" class="space-y-1.5">
              <h4 class="font-bold text-xs uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <FileText class="w-3.5 h-3.5 text-slate-400" />
                Descripción del Problema / Necesidad
              </h4>
              <div class="bg-slate-50 p-4 rounded-2xl border border-slate-200/80 text-slate-700 text-xs leading-relaxed">
                {{ selectedInitiative.form_data?.descripcion_de_la_necesidad || selectedInitiative.summary?.descripcionProblema }}
              </div>
            </div>

            <!-- Complexity / Risk Badges if present -->
            <div v-if="selectedInitiative.summary?.complejidad || selectedInitiative.summary?.riesgo" class="flex gap-2">
              <div v-if="selectedInitiative.summary?.complejidad" class="flex-1 p-3 rounded-xl border border-slate-200 bg-white">
                <span class="text-[10px] text-slate-400 font-medium uppercase">Complejidad</span>
                <p class="font-bold text-xs text-slate-800">{{ selectedInitiative.summary.complejidad }}</p>
              </div>
              <div v-if="selectedInitiative.summary?.riesgo" class="flex-1 p-3 rounded-xl border border-slate-200 bg-white">
                <span class="text-[10px] text-slate-400 font-medium uppercase">Riesgo</span>
                <p class="font-bold text-xs text-slate-800">{{ selectedInitiative.summary.riesgo }}</p>
              </div>
            </div>
          </div>

          <!-- Drawer Footer -->
          <div class="px-6 py-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between gap-3">
            <button
              type="button"
              @click="selectedInitiative = null"
              class="px-4 py-2 text-xs font-semibold rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 transition-colors cursor-pointer"
            >
              Cerrar
            </button>

            <NuxtLink
              :to="selectedInitiative.status === 'Borrador' ? `/nueva?id=${selectedInitiative.id}` : `/iniciativa/${selectedInitiative.id}`"
              class="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-xl bg-[#4F5AF5] hover:bg-[#3F49E0] text-white transition-all shadow-xs hover:shadow cursor-pointer"
            >
              <span>{{ selectedInitiative.status === 'Borrador' ? 'Continuar Edición' : 'Abrir Expediente Completo' }}</span>
              <ExternalLink class="w-3.5 h-3.5" />
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
