<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import {
  User, Bot, BookOpen, MessageSquare, ShieldAlert,
  ThumbsUp, Send, RotateCcw, Plus, Trash2,
  CheckCircle2, X, ChevronDown, ChevronRight, ChevronUp,
  Pencil, Save, AlertCircle, Loader2, Mic, MicOff,
  Paperclip, Image as ImageIcon, Sparkles, Copy,
  ExternalLink, Folder, FolderPlus, FolderOpen, FolderTree,
  FileText, Check, ShieldCheck, FolderInput, Brain,
  Layers, Search, GripVertical, ToggleLeft, ToggleRight,
  BrainCircuit, RefreshCw, Upload
} from 'lucide-vue-next';

import { useAiAssistant } from '~/composables/useAiAssistant';

const config = useRuntimeConfig();
const apiBase = config.public.apiBase;
const { aiName, aiAvatar, loadAiConfig, setAiConfig } = useAiAssistant();

// ─── Interfaces ─────────────────────────────────────────────────────────────
interface TrainingFolder {
  id: string;
  name: string;
  parent_id: string | null;
  level: number;
  sort_order: number;
  created_at?: string;
  updated_at?: string;
}

interface TrainingEntry {
  id: string;
  layer: 'identity' | 'appearance' | 'context' | 'examples' | 'guardrails' | 'settings';
  title: string;
  content: string;
  is_active: boolean;
  sort_order: number;
  source: string;
  folder_id?: string | null;
  created_at?: string;
}

interface FeedbackEntry {
  id: string;
  initiative_id: string;
  message_index: number;
  user_message: string;
  agent_response: string;
  rating: 'positive' | 'negative';
  admin_approved: boolean;
  created_at: string;
}

interface ChatMsg {
  role: 'user' | 'model';
  text: string;
  options?: string[];
}

interface FolderTreeNode extends TrainingFolder {
  children: FolderTreeNode[];
  itemCount: number;
}

// ─── Pestañas Oficiales de AITraining ────────────────────────────────────────
const TABS = [
  { id: 'identity',   label: 'Identidad',        icon: User },
  { id: 'appearance', label: 'Apariencia',       icon: Bot },
  { id: 'context',    label: 'Contexto',         icon: BookOpen },
  { id: 'examples',   label: 'Ejemplos',         icon: MessageSquare },
  { id: 'guardrails', label: 'Guardarraíles',     icon: ShieldAlert },
  { id: 'settings',   label: 'Funciones',         icon: ToggleLeft },
  { id: 'feedback',   label: 'Retroalimentación', icon: ThumbsUp },
] as const;

type TabId = typeof TABS[number]['id'];

const activeTab = ref<TabId>('identity');
const loading = ref(true);
const saving = ref(false);
const saveMsg = ref('');

const entries = ref<TrainingEntry[]>([]);
const folders = ref<TrainingFolder[]>([]);
const feedback = ref<FeedbackEntry[]>([]);

// Executive Sandbox State (Fase 1 CIO)
const sandboxEnabled = ref(true);
const togglingSandbox = ref(false);

// Default prompt de identidad
const DEFAULT_IDENTITY = 'Eres un Analista de Negocio Senior de TI. Tu tarea es ayudar a los colaboradores a aterrizar y estructurar sus iniciativas o requerimientos de negocio mediante una conversación fluida y profesional. Tu tono es cercano pero formal. Haz preguntas concretas, de una en una, para recopilar toda la información necesaria. No termines la conversación hasta tener respuestas claras para todos los campos requeridos.';
const identityText = ref(DEFAULT_IDENTITY);
const identitySaved = ref(true);

// ─── Funciones y Toggles State ──────────────────────────────────────────────
const useMic = ref(true);
const useAttachments = ref(true);
const fileTypes = ref({
  pdf: { enabled: true, maxMb: 25.0 },
  docx: { enabled: true, maxMb: 25.0 },
  txt: { enabled: true, maxMb: 5.0 },
  image: { enabled: true, maxMb: 10.0 },
});

// ─── Contexto (Carpetas) State ──────────────────────────────────────────────
const selectedFolderId = ref<string>('all');
const expandedFolderIds = ref<Set<string>>(new Set());
const folderSearchTerm = ref('');
const entrySearchTerm = ref('');

const showFolderModal = ref(false);
const folderModalMode = ref<'create' | 'edit'>('create');
const folderParent = ref<TrainingFolder | null>(null);
const folderToEdit = ref<TrainingFolder | null>(null);
const folderNameInput = ref('');

const showDeleteFolderModal = ref(false);
const deletingFolder = ref<TrainingFolder | null>(null);
const deleteFolderWithItems = ref(false);

const showMoveEntryModal = ref(false);
const movingEntry = ref<TrainingEntry | null>(null);
const targetFolderIdForMove = ref<string>('');

const showContextForm = ref(false);
const editingContextEntry = ref<TrainingEntry | null>(null);
const contextForm = ref({ title: '', content: '', folder_id: '' });

const showGuide = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);
const uploading = ref(false);
const uploadingFileName = ref('');
const showUploadModal = ref(false);
const extractedChunks = ref<{ title: string; content: string }[]>([]);
const uploadTargetFolderId = ref<string>('');

// ─── Ejemplos State ─────────────────────────────────────────────────────────
const showExampleForm = ref(false);
const editingExample = ref<TrainingEntry | null>(null);
const exampleForm = ref({ title: '', content: '' });

// ─── Guardarraíles State ────────────────────────────────────────────────────
const newGuardrailText = ref('');
const editingGuardrail = ref<{ id: string; text: string } | null>(null);

// ─── Retroalimentación State ────────────────────────────────────────────────
const feedbackFilter = ref<'all' | 'negative' | 'positive'>('all');
const feedbackEdits = ref<Record<string, string>>({});
const approvingFeedbackId = ref<string | null>(null);

// ─── Preview Chat State ─────────────────────────────────────────────────────
const chatMessages = ref<ChatMsg[]>([]);
const chatInput = ref('');
const chatLoading = ref(false);

// Helper Toast
function showSave(msg = 'Guardado ✓') {
  saveMsg.value = msg;
  setTimeout(() => {
    if (saveMsg.value === msg) saveMsg.value = '';
  }, 2500);
}

// ─── Carga de Datos ─────────────────────────────────────────────────────────
async function loadAll() {
  loading.value = true;
  try {
    const [trainRes, fbRes, folderRes, sRes] = await Promise.all([
      $fetch<TrainingEntry[]>(`${apiBase}/admin/ai-training`).catch(() => []),
      $fetch<FeedbackEntry[]>(`${apiBase}/ai-feedback`).catch(() => []),
      $fetch<TrainingFolder[]>(`${apiBase}/admin/ai-training/folders`).catch(() => []),
      $fetch<{ enabled: boolean }>(`${apiBase}/sandbox/status`).catch(() => ({ enabled: true })),
    ]);

    entries.value = Array.isArray(trainRes) ? trainRes : [];
    feedback.value = Array.isArray(fbRes) ? fbRes : [];
    folders.value = Array.isArray(folderRes) ? folderRes : [];
    sandboxEnabled.value = Boolean(sRes?.enabled);

    // Mapear Identidad
    const idEntry = entries.value.find(e => e.layer === 'identity');
    if (idEntry) {
      identityText.value = idEntry.content;
      identitySaved.value = true;
    }

    // Mapear Apariencia
    const nameEntry = entries.value.find(e => e.layer === 'settings' && e.title === 'ai_name');
    if (nameEntry?.content) aiName.value = nameEntry.content;

    const avatarEntry = entries.value.find(e => e.layer === 'settings' && e.title === 'ai_avatar');
    if (avatarEntry?.content) aiAvatar.value = avatarEntry.content;

    // Mapear Toggles
    const micEntry = entries.value.find(e => e.layer === 'settings' && e.title === 'use_mic');
    useMic.value = micEntry ? micEntry.content !== 'false' : true;

    const attachEntry = entries.value.find(e => e.layer === 'settings' && e.title === 'use_attachments');
    useAttachments.value = attachEntry ? attachEntry.content !== 'false' : true;

    // Mapear tipos de archivo
    for (const type of ['pdf', 'docx', 'txt', 'image'] as const) {
      const enSetting = entries.value.find(e => e.layer === 'settings' && e.title === `enable_${type}`);
      const limSetting = entries.value.find(e => e.layer === 'settings' && e.title === `max_size_${type}`);
      fileTypes.value[type].enabled = enSetting ? enSetting.content !== 'false' : true;
      if (limSetting?.content) {
        fileTypes.value[type].maxMb = parseFloat(limSetting.content);
      }
    }

    // Expandir carpetas de Nivel 1 por defecto
    folders.value.filter(f => !f.parent_id || f.level === 1).forEach(f => {
      expandedFolderIds.value.add(f.id);
    });
  } catch (err) {
    console.error('Error cargando configuración:', err);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadAiConfig();
  loadAll();
});

// ─── Helpers de Capas ───────────────────────────────────────────────────────
const byLayer = (layer: TrainingEntry['layer']) =>
  entries.value.filter(e => e.layer === layer).sort((a, b) => a.sort_order - b.sort_order);

const pendingFeedback = computed(() => feedback.value.filter(f => !f.admin_approved));

// ─── CRUD Entradas ──────────────────────────────────────────────────────────
async function createEntry(payload: Partial<TrainingEntry>) {
  saving.value = true;
  try {
    const data = await $fetch<TrainingEntry>(`${apiBase}/admin/ai-training`, {
      method: 'POST',
      body: payload,
    });
    entries.value.push(data);
    showSave();
    return data;
  } catch (err) {
    showSave('Error al guardar');
    throw err;
  } finally {
    saving.value = false;
  }
}

async function updateEntry(id: string, payload: Partial<TrainingEntry>) {
  saving.value = true;
  try {
    const data = await $fetch<TrainingEntry>(`${apiBase}/admin/ai-training/${id}`, {
      method: 'PATCH',
      body: payload,
    });
    entries.value = entries.value.map(e => e.id === id ? data : e);
    showSave();
    return data;
  } catch (err) {
    showSave('Error al actualizar');
    throw err;
  } finally {
    saving.value = false;
  }
}

async function deleteEntry(id: string) {
  try {
    await $fetch(`${apiBase}/admin/ai-training/${id}`, { method: 'DELETE' });
    entries.value = entries.value.filter(e => e.id !== id);
    showSave('Eliminado');
  } catch {
    showSave('Error al eliminar');
  }
}

function toggleEntry(id: string) {
  const entry = entries.value.find(e => e.id === id);
  if (entry) updateEntry(id, { is_active: !entry.is_active });
}

// ─── Executive Sandbox Toggle ───────────────────────────────────────────────
async function handleToggleSandbox() {
  togglingSandbox.value = true;
  const nextVal = !sandboxEnabled.value;
  try {
    await $fetch(`${apiBase}/sandbox/toggle`, {
      method: 'POST',
      body: { enabled: nextVal },
    });
    sandboxEnabled.value = nextVal;
    showSave(nextVal ? 'Sandbox de Teo ACTIVO ✓' : 'Sandbox de Teo DESACTIVADO ✓');
  } catch {
    showSave('Error al cambiar estado');
  } finally {
    togglingSandbox.value = false;
  }
}

function copySandboxLink() {
  const url = `${window.location.origin}/sandbox`;
  navigator.clipboard.writeText(url);
  showSave('¡Enlace Sandbox copiado para el CIO! ✓');
}

// ─── Tab 1: Identidad ───────────────────────────────────────────────────────
const wordCount = computed(() =>
  identityText.value.trim().split(/\s+/).filter(Boolean).length
);

async function saveIdentity() {
  const existing = entries.value.find(e => e.layer === 'identity');
  if (existing) {
    await updateEntry(existing.id, { content: identityText.value });
  } else {
    await createEntry({
      layer: 'identity',
      title: 'Identidad del Agente',
      content: identityText.value,
      is_active: true,
      sort_order: 0,
    });
  }
  identitySaved.value = true;
  showSave('Identidad guardada ✓');
}

// ─── Tab 2: Apariencia ──────────────────────────────────────────────────────
const presets = [
  { name: 'Bot Azul', url: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=100&auto=format&fit=crop&q=60' },
  { name: 'Bot Morado', url: 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=100&auto=format&fit=crop&q=60' },
  { name: 'Bot Moderno', url: 'https://images.unsplash.com/photo-1614741118887-7a4ee193a5fa?w=100&auto=format&fit=crop&q=60' },
];

function handleAvatarSelect(e: Event) {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  if (file.size > 2 * 1024 * 1024) {
    alert('La imagen no debe superar 2 MB');
    return;
  }
  const reader = new FileReader();
  reader.onload = (event) => {
    aiAvatar.value = event.target?.result as string;
  };
  reader.readAsDataURL(file);
}

async function saveAppearance() {
  saving.value = true;
  try {
    const nameEntry = entries.value.find(e => e.layer === 'settings' && e.title === 'ai_name');
    if (nameEntry) {
      await updateEntry(nameEntry.id, { content: aiName.value });
    } else {
      await createEntry({ layer: 'settings', title: 'ai_name', content: aiName.value, is_active: true, sort_order: 0, source: 'manual' });
    }

    const avatarEntry = entries.value.find(e => e.layer === 'settings' && e.title === 'ai_avatar');
    if (avatarEntry) {
      await updateEntry(avatarEntry.id, { content: aiAvatar.value });
    } else {
      await createEntry({ layer: 'settings', title: 'ai_avatar', content: aiAvatar.value, is_active: true, sort_order: 0, source: 'manual' });
    }

    setAiConfig(aiName.value, aiAvatar.value);
    showSave('¡Configuración de la IA guardada correctamente!');
  } catch {
    showSave('Error al guardar apariencia');
  } finally {
    saving.value = false;
  }
}

// ─── Tab 3: Contexto y Carpetas ─────────────────────────────────────────────
const folderById = computed(() => new Map(folders.value.map(f => [f.id, f])));

const folderPathMap = computed(() => {
  const map = new Map<string, string>();
  const getPath = (id: string | null): string => {
    if (!id) return '';
    const f = folderById.value.get(id);
    if (!f) return '';
    const parent = getPath(f.parent_id);
    return parent ? `${parent} > ${f.name}` : f.name;
  };
  folders.value.forEach(f => {
    map.set(f.id, getPath(f.id));
  });
  return map;
});

const folderTree = computed<FolderTreeNode[]>(() => {
  const nodeMap = new Map<string, FolderTreeNode>();
  folders.value.forEach(f => {
    nodeMap.set(f.id, { ...f, children: [], itemCount: 0 });
  });

  entries.value.forEach(e => {
    if (e.layer === 'context' && e.folder_id && nodeMap.has(e.folder_id)) {
      nodeMap.get(e.folder_id)!.itemCount += 1;
    }
  });

  const roots: FolderTreeNode[] = [];
  folders.value.forEach(f => {
    const node = nodeMap.get(f.id)!;
    if (f.parent_id && nodeMap.has(f.parent_id)) {
      nodeMap.get(f.parent_id)!.children.push(node);
    } else {
      roots.push(node);
    }
  });

  return roots;
});

const rootCount = computed(() =>
  entries.value.filter(e => e.layer === 'context' && !e.folder_id).length
);

const activeFolder = computed(() =>
  selectedFolderId.value !== 'all' && selectedFolderId.value !== 'root'
    ? folderById.value.get(selectedFolderId.value)
    : null
);

const flattenedFolderOptions = computed(() => {
  const result: { id: string; name: string; level: number; path: string }[] = [];
  const traverse = (node: FolderTreeNode, depth: number) => {
    result.push({
      id: node.id,
      name: node.name,
      level: node.level,
      path: folderPathMap.value.get(node.id) || node.name,
    });
    node.children.forEach(c => traverse(c, depth + 1));
  };
  folderTree.value.forEach(r => traverse(r, 1));
  return result;
});

const filteredContextEntries = computed(() => {
  let list = entries.value.filter(e => e.layer === 'context');
  if (selectedFolderId.value === 'root') {
    list = list.filter(e => !e.folder_id);
  } else if (selectedFolderId.value !== 'all') {
    list = list.filter(e => e.folder_id === selectedFolderId.value);
  }
  if (entrySearchTerm.value.trim()) {
    const q = entrySearchTerm.value.toLowerCase();
    list = list.filter(e => e.title.toLowerCase().includes(q) || e.content.toLowerCase().includes(q));
  }
  return list;
});

function toggleFolderExpand(folderId: string) {
  if (expandedFolderIds.value.has(folderId)) {
    expandedFolderIds.value.delete(folderId);
  } else {
    expandedFolderIds.value.add(folderId);
  }
}

function handleOpenCreateFolder(parent: TrainingFolder | null = null) {
  if (parent && parent.level >= 3) {
    alert('Límite alcanzado: máximo se permiten 3 niveles de carpetas.');
    return;
  }
  folderModalMode.value = 'create';
  folderParent.value = parent;
  folderToEdit.value = null;
  folderNameInput.value = '';
  showFolderModal.value = true;
}

function handleOpenEditFolder(folder: TrainingFolder) {
  folderModalMode.value = 'edit';
  folderParent.value = null;
  folderToEdit.value = folder;
  folderNameInput.value = folder.name;
  showFolderModal.value = true;
}

async function handleSaveFolderSubmit() {
  const name = folderNameInput.value.trim();
  if (!name) return;
  saving.value = true;
  try {
    if (folderModalMode.value === 'edit' && folderToEdit.value) {
      const updated = await $fetch<TrainingFolder>(`${apiBase}/admin/ai-training/folders/${folderToEdit.value.id}`, {
        method: 'PATCH',
        body: { name },
      });
      folders.value = folders.value.map(f => f.id === updated.id ? updated : f);
      showSave(`Carpeta renombrada a "${name}" ✓`);
    } else {
      let level = 1;
      if (folderParent.value) {
        level = Math.min(3, folderParent.value.level + 1);
      }
      const created = await $fetch<TrainingFolder>(`${apiBase}/admin/ai-training/folders`, {
        method: 'POST',
        body: {
          name,
          parent_id: folderParent.value ? folderParent.value.id : null,
          level,
          sort_order: folders.value.length + 1,
        },
      });
      folders.value.push(created);
      selectedFolderId.value = created.id;
      if (folderParent.value) {
        expandedFolderIds.value.add(folderParent.value.id);
      }
      showSave(`Carpeta "${name}" creada exitosamente ✓`);
    }
    showFolderModal.value = false;
  } catch (err: any) {
    alert(err?.data?.detail || 'Error al guardar carpeta');
  } finally {
    saving.value = false;
  }
}

function handleOpenDeleteFolder(folder: TrainingFolder) {
  deletingFolder.value = folder;
  deleteFolderWithItems.value = false;
  showDeleteFolderModal.value = true;
}

async function handleConfirmDeleteFolder() {
  if (!deletingFolder.value) return;
  saving.value = true;
  try {
    const fid = deletingFolder.value.id;
    await $fetch(`${apiBase}/admin/ai-training/folders/${fid}?deleteItems=${deleteFolderWithItems.value}`, {
      method: 'DELETE',
    });
    if (selectedFolderId.value === fid) {
      selectedFolderId.value = 'all';
    }
    await loadAll();
    showSave('Carpeta eliminada ✓');
    showDeleteFolderModal.value = false;
    deletingFolder.value = null;
  } catch {
    showSave('Error al eliminar');
  } finally {
    saving.value = false;
  }
}

// Fichas Contexto CRUD
function openNewContext() {
  contextForm.value = {
    title: '',
    content: '',
    folder_id: selectedFolderId.value !== 'all' && selectedFolderId.value !== 'root' ? selectedFolderId.value : '',
  };
  editingContextEntry.value = null;
  showContextForm.value = true;
}

function openEditContext(e: TrainingEntry) {
  contextForm.value = {
    title: e.title,
    content: e.content,
    folder_id: e.folder_id || '',
  };
  editingContextEntry.value = e;
  showContextForm.value = true;
}

async function saveContextEntry() {
  if (!contextForm.value.title.trim() || !contextForm.value.content.trim()) return;
  if (editingContextEntry.value) {
    await updateEntry(editingContextEntry.value.id, {
      title: contextForm.value.title.trim(),
      content: contextForm.value.content.trim(),
      folder_id: contextForm.value.folder_id || null,
    });
  } else {
    await createEntry({
      layer: 'context',
      title: contextForm.value.title.trim(),
      content: contextForm.value.content.trim(),
      folder_id: contextForm.value.folder_id || null,
      is_active: true,
      sort_order: entries.value.length,
      source: 'manual',
    });
  }
  showContextForm.value = false;
  editingContextEntry.value = null;
}

function openMoveEntry(e: TrainingEntry) {
  movingEntry.value = e;
  targetFolderIdForMove.value = e.folder_id || '';
  showMoveEntryModal.value = true;
}

async function confirmMoveEntry() {
  if (!movingEntry.value) return;
  try {
    await updateEntry(movingEntry.value.id, { folder_id: targetFolderIdForMove.value || null });
    showSave('Ficha movida ✓');
    showMoveEntryModal.value = false;
    movingEntry.value = null;
  } catch {
    showSave('Error al mover');
  }
}

// Carga de Documentos / Diagramas
async function handleFileUpload(e: Event) {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  uploading.value = true;
  uploadingFileName.value = file.name;

  try {
    const fd = new FormData();
    fd.append('file', file);
    const res: any = await $fetch(`${apiBase}/admin/ai-training/upload-document`, {
      method: 'POST',
      body: fd,
    });
    extractedChunks.value = res.chunks || [];
    uploadTargetFolderId.value = selectedFolderId.value !== 'all' && selectedFolderId.value !== 'root' ? selectedFolderId.value : '';
    showUploadModal.value = true;
  } catch (err: any) {
    alert(err?.data?.detail || 'Error al procesar archivo');
  } finally {
    uploading.value = false;
    target.value = '';
  }
}

async function approveChunk(chunk: { title: string; content: string }) {
  await createEntry({
    layer: 'context',
    ...chunk,
    folder_id: uploadTargetFolderId.value || null,
    is_active: true,
    sort_order: entries.value.length,
    source: 'document',
  });
  extractedChunks.value = extractedChunks.value.filter(c => c.title !== chunk.title);
  showSave(`Ficha "${chunk.title}" agregada ✓`);
}

async function approveAllChunks() {
  for (const c of extractedChunks.value) {
    await createEntry({
      layer: 'context',
      ...c,
      folder_id: uploadTargetFolderId.value || null,
      is_active: true,
      sort_order: entries.value.length,
      source: 'document',
    });
  }
  extractedChunks.value = [];
  showUploadModal.value = false;
  showSave('Todas las fichas agregadas a la Base de Conocimiento ✓');
}

// ─── Tab 4: Ejemplos ────────────────────────────────────────────────────────
function openNewExample() {
  exampleForm.value = { title: '', content: '' };
  editingExample.value = null;
  showExampleForm.value = true;
}

function openEditExample(e: TrainingEntry) {
  exampleForm.value = { title: e.title, content: e.content };
  editingExample.value = e;
  showExampleForm.value = true;
}

async function saveExample() {
  if (!exampleForm.value.title.trim() || !exampleForm.value.content.trim()) return;
  if (editingExample.value) {
    await updateEntry(editingExample.value.id, {
      title: exampleForm.value.title.trim(),
      content: exampleForm.value.content.trim(),
    });
  } else {
    await createEntry({
      layer: 'examples',
      title: exampleForm.value.title.trim(),
      content: exampleForm.value.content.trim(),
      is_active: true,
      sort_order: entries.value.length,
    });
  }
  showExampleForm.value = false;
  editingExample.value = null;
}

// ─── Tab 5: Guardarraíles ───────────────────────────────────────────────────
async function addGuardrail() {
  if (!newGuardrailText.value.trim()) return;
  await createEntry({
    layer: 'guardrails',
    title: `Regla ${byLayer('guardrails').length + 1}`,
    content: newGuardrailText.value.trim(),
    is_active: true,
    sort_order: byLayer('guardrails').length,
  });
  newGuardrailText.value = '';
}

async function saveEditingGuardrail() {
  if (!editingGuardrail.value) return;
  await updateEntry(editingGuardrail.value.id, { content: editingGuardrail.value.text });
  editingGuardrail.value = null;
}

// ─── Tab 6: Funciones y Toggles ─────────────────────────────────────────────
async function toggleMicSetting() {
  const nextVal = !useMic.value;
  useMic.value = nextVal;
  const existing = entries.value.find(e => e.layer === 'settings' && e.title === 'use_mic');
  if (existing) {
    await updateEntry(existing.id, { content: String(nextVal) });
  } else {
    await createEntry({ layer: 'settings', title: 'use_mic', content: String(nextVal), is_active: true, sort_order: 0, source: 'manual' });
  }
}

async function toggleAttachmentsSetting() {
  const nextVal = !useAttachments.value;
  useAttachments.value = nextVal;
  const existing = entries.value.find(e => e.layer === 'settings' && e.title === 'use_attachments');
  if (existing) {
    await updateEntry(existing.id, { content: String(nextVal) });
  } else {
    await createEntry({ layer: 'settings', title: 'use_attachments', content: String(nextVal), is_active: true, sort_order: 0, source: 'manual' });
  }
}

async function toggleFileTypeSetting(type: keyof typeof fileTypes.value) {
  const nextVal = !fileTypes.value[type].enabled;
  fileTypes.value[type].enabled = nextVal;
  const existing = entries.value.find(e => e.layer === 'settings' && e.title === `enable_${type}`);
  if (existing) {
    await updateEntry(existing.id, { content: String(nextVal) });
  } else {
    await createEntry({ layer: 'settings', title: `enable_${type}`, content: String(nextVal), is_active: true, sort_order: 0, source: 'manual' });
  }
}

async function updateFileSizeLimit(type: keyof typeof fileTypes.value, val: number) {
  fileTypes.value[type].maxMb = val;
  const existing = entries.value.find(e => e.layer === 'settings' && e.title === `max_size_${type}`);
  if (existing) {
    await updateEntry(existing.id, { content: String(val) });
  } else {
    await createEntry({ layer: 'settings', title: `max_size_${type}`, content: String(val), is_active: true, sort_order: 0, source: 'manual' });
  }
}

// ─── Tab 7: Retroalimentación ───────────────────────────────────────────────
const filteredFeedbackList = computed(() => {
  if (feedbackFilter.value === 'all') return feedback.value;
  return feedback.value.filter(f => f.rating === feedbackFilter.value);
});

async function approveFeedback(fb: FeedbackEntry) {
  approvingFeedbackId.value = fb.id;
  const ideal = feedbackEdits.value[fb.id] || fb.agent_response;
  try {
    await $fetch(`${apiBase}/ai-feedback/${fb.id}/approve`, {
      method: 'POST',
      body: { ideal_response: ideal },
    });
    await loadAll();
    showSave('Aprobado como ejemplo de entrenamiento ✓');
  } catch {
    showSave('Error al aprobar');
  } finally {
    approvingFeedbackId.value = null;
  }
}

async function discardFeedback(id: string) {
  try {
    await $fetch(`${apiBase}/ai-feedback/${id}`, { method: 'DELETE' });
    feedback.value = feedback.value.filter(f => f.id !== id);
    showSave('Retroalimentación descartada ✓');
  } catch {
    showSave('Error al descartar');
  }
}

// ─── Preview Chat (Columna Derecha) ─────────────────────────────────────────
const attachedChatFile = ref<{ name: string; type: string; size: number; content: string } | null>(null);
const isProcessingFile = ref(false);
const attachError = ref<string | null>(null);
const chatFileInputRef = ref<HTMLInputElement | null>(null);

const isRecording = ref(false);
const isTranscribing = ref(false);
const recordingSeconds = ref(0);
const voiceError = ref<string | null>(null);
let recognition: any = null;
let recordingTimer: any = null;

function formatMarkdown(text: string): string {
  if (!text) return '';
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  html = html.replace(/```([\s\S]*?)```/g, '<pre class="bg-slate-100 p-2 rounded text-[11px] font-mono my-2 overflow-x-auto">$1</pre>');
  html = html.replace(/`([^`]+)`/g, '<code class="bg-slate-100 px-1 py-0.5 rounded text-[11px] font-mono text-indigo-600">$1</code>');
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  html = html.replace(/^### (.*$)/gim, '<h4 class="font-bold text-slate-800 text-xs mt-2 mb-1">$1</h4>');
  html = html.replace(/^## (.*$)/gim, '<h3 class="font-bold text-slate-900 text-sm mt-2 mb-1">$1</h3>');
  html = html.replace(/^# (.*$)/gim, '<h2 class="font-bold text-slate-900 text-sm mt-2 mb-1">$1</h2>');
  html = html.replace(/^\s*[-•]\s+(.*$)/gim, '<li class="ml-3 list-disc">$1</li>');
  html = html.replace(/\n/g, '<br/>');
  return html;
}

function startRecording() {
  voiceError.value = null;
  recordingSeconds.value = 0;
  const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (!SpeechRec) {
    voiceError.value = 'El navegador no soporta reconocimiento de voz directo.';
    return;
  }
  try {
    recognition = new SpeechRec();
    recognition.lang = 'es-PE';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => {
      isRecording.value = true;
      recordingTimer = setInterval(() => {
        recordingSeconds.value++;
        if (recordingSeconds.value >= 60) stopRecording();
      }, 1000);
    };

    recognition.onresult = (event: any) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        finalTranscript += event.results[i][0].transcript;
      }
      if (finalTranscript) {
        chatInput.value = (chatInput.value ? chatInput.value + ' ' : '') + finalTranscript;
      }
    };

    recognition.onerror = (event: any) => {
      voiceError.value = event.error === 'not-allowed' ? 'Permiso de micrófono denegado.' : `Error: ${event.error}`;
      stopRecording();
    };

    recognition.onend = () => {
      stopRecording();
    };

    recognition.start();
  } catch (err: any) {
    voiceError.value = 'No se pudo activar el micrófono: ' + (err.message || err);
  }
}

function stopRecording() {
  if (recordingTimer) {
    clearInterval(recordingTimer);
    recordingTimer = null;
  }
  isRecording.value = false;
  recordingSeconds.value = 0;
  if (recognition) {
    try { recognition.stop(); } catch {}
    recognition = null;
  }
}

async function handleChatFileAttach(e: Event) {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  target.value = '';
  if (!file) return;

  attachError.value = null;
  let typeKey: 'pdf' | 'docx' | 'txt' | 'image' = 'txt';
  const name = file.name.toLowerCase();
  const mime = file.type;

  if (mime === 'application/pdf' || name.endsWith('.pdf')) typeKey = 'pdf';
  else if (mime.includes('word') || name.endsWith('.docx')) typeKey = 'docx';
  else if (mime.startsWith('image/') || name.match(/\.(jpg|jpeg|png|webp)$/i)) typeKey = 'image';

  const typeConfig = fileTypes.value[typeKey];
  if (!typeConfig.enabled) {
    attachError.value = `La subida de archivos ${typeKey.toUpperCase()} está deshabilitada.`;
    return;
  }

  if (file.size > typeConfig.maxMb * 1024 * 1024) {
    attachError.value = `El archivo supera el límite de ${typeConfig.maxMb} MB.`;
    return;
  }

  isProcessingFile.value = true;
  try {
    const fd = new FormData();
    fd.append('file', file);
    const res: any = await $fetch(`${apiBase}/chat/attach-file`, {
      method: 'POST',
      body: fd,
    });
    attachedChatFile.value = {
      name: file.name,
      type: typeKey,
      size: file.size,
      content: res.content,
    };
  } catch (err: any) {
    attachError.value = err.data?.detail || err.message || 'Error al procesar archivo';
  } finally {
    isProcessingFile.value = false;
  }
}

function removeChatAttachment() {
  attachedChatFile.value = null;
  attachError.value = null;
}

async function sendPreviewMessage(overrideText?: string) {
  const msg = overrideText || chatInput.value.trim();
  if ((!msg && !attachedChatFile.value) || chatLoading.value || isProcessingFile.value) return;

  const displayMsg = msg || (attachedChatFile.value ? `📎 ${attachedChatFile.value.name}` : '');
  const attachedContent = attachedChatFile.value?.content;
  attachedChatFile.value = null;

  chatMessages.value.push({ role: 'user', text: displayMsg });
  chatInput.value = '';
  chatLoading.value = true;

  try {
    const res: any = await $fetch(`${apiBase}/ai-training/preview-chat`, {
      method: 'POST',
      body: {
        message: msg,
        attached_content: attachedContent,
        history: chatMessages.value.map(m => ({ role: m.role, text: m.text })),
      },
    });
    chatMessages.value.push({
      role: 'model',
      text: res.text,
      options: res.options || [],
    });
  } catch {
    chatMessages.value.push({
      role: 'model',
      text: 'Error al conectar con el agente. Verifica tu conexión o configuración.',
    });
  } finally {
    chatLoading.value = false;
  }
}

function resetPreviewChat() {
  chatMessages.value = [];
  attachedChatFile.value = null;
}
</script>

<template>
  <div class="flex flex-col lg:flex-row gap-6 min-h-[calc(100vh-8rem)]">
    <!-- ── Main Panel Izquierdo ── -->
    <div class="flex-1 min-w-0 space-y-4">
      <!-- ── Header Principal con Banner CIO y Pestañas ── -->
      <div class="bg-white rounded-2xl shadow-sm border border-[#E2E8F0] p-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center">
              <BrainCircuit class="w-5 h-5 text-violet-600" />
            </div>
            <div>
              <h1 class="text-xl font-bold text-[#1E293B]">Entrenamiento del Agente IA</h1>
              <p class="text-xs text-[#64748B] mt-0.5">Configura el comportamiento, contexto y ejemplos del asistente de iniciativas</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <Loader2 v-if="saving" class="w-4 h-4 text-[#4F5AF5] animate-spin" />
            <span v-if="saveMsg" class="text-xs text-emerald-600 font-semibold">{{ saveMsg }}</span>
          </div>
        </div>

        <!-- ── Executive Sandbox Control Card (Fase 1 CIO) ── -->
        <div class="mt-5 p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white shadow-lg border border-indigo-500/20 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div class="flex items-start sm:items-center gap-3.5">
            <div class="w-11 h-11 rounded-xl bg-[#EB5F46] flex items-center justify-center text-white shadow-md shrink-0 ring-2 ring-white/20">
              <Brain class="w-6 h-6" />
            </div>
            <div class="space-y-0.5">
              <div class="flex items-center gap-2">
                <span class="text-sm font-bold text-white tracking-wide">
                  Laboratorio Teo — Sandbox Ejecutivo
                </span>
                <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-[#EB5F46]/20 text-[#EB5F46] border border-[#EB5F46]/30">
                  FASE 1 • CIO
                </span>
              </div>
              <p class="text-xs text-slate-300">
                URL dedicada para que el CIO y jefaturas prueben a Teo capturando y articulando necesidades en vivo.
              </p>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <!-- Switch Toggle -->
            <div class="flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-xl border border-white/10">
              <span class="text-xs font-semibold text-slate-200">
                Estado: <strong :class="sandboxEnabled ? 'text-emerald-400' : 'text-rose-400'">{{ sandboxEnabled ? 'ACTIVO' : 'INACTIVO' }}</strong>
              </span>
              <button
                type="button"
                @click="handleToggleSandbox"
                :disabled="togglingSandbox"
                :class="[
                  'w-11 h-6 flex items-center rounded-full p-1 cursor-pointer transition-colors duration-200 ease-in-out',
                  sandboxEnabled ? 'bg-emerald-500' : 'bg-slate-600'
                ]"
                :title="sandboxEnabled ? 'Desactivar Sandbox' : 'Activar Sandbox'"
              >
                <div
                  :class="[
                    'bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-200 ease-in-out',
                    sandboxEnabled ? 'translate-x-5' : 'translate-x-0'
                  ]"
                />
              </button>
            </div>

            <!-- Copy Link Button -->
            <button
              type="button"
              @click="copySandboxLink"
              class="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white/10 hover:bg-white/20 border border-white/15 text-white text-xs font-bold transition-colors cursor-pointer"
              title="Copiar enlace directo para enviar al CIO"
            >
              <Copy class="w-3.5 h-3.5" />
              <span>Copiar Enlace CIO</span>
            </button>

            <!-- Open in New Tab Button -->
            <NuxtLink
              to="/sandbox"
              target="_blank"
              class="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-[#EB5F46] hover:bg-[#D94F37] text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
            >
              <span>Probar Sandbox</span>
              <ExternalLink class="w-3.5 h-3.5" />
            </NuxtLink>
          </div>
        </div>

        <!-- ── 7 Tabs Oficiales con Barra de Selección ── -->
        <div class="flex gap-1 mt-6 border-b border-[#E2E8F0] overflow-x-auto">
          <button
            v-for="tab in TABS"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'flex items-center gap-2 px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors whitespace-nowrap -mb-px cursor-pointer',
              activeTab === tab.id
                ? 'border-[#4F5AF5] text-[#4F5AF5]'
                : 'border-transparent text-[#64748B] hover:text-[#1E293B]'
            ]"
          >
            <component :is="tab.icon" class="w-4 h-4" />
            <span>{{ tab.label }}</span>
            <span
              v-if="tab.id === 'feedback' && pendingFeedback.length > 0"
              class="bg-red-500 text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center"
            >
              {{ pendingFeedback.length }}
            </span>
          </button>
        </div>
      </div>

      <!-- ── Loading Skeleton ── -->
      <div v-if="loading" class="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs space-y-4 animate-pulse">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center text-[#4F5AF5]">
            <Loader2 class="w-5 h-5 animate-spin" />
          </div>
          <div class="space-y-1.5">
            <div class="h-4 bg-slate-200 rounded w-48" />
            <div class="h-3 bg-slate-100 rounded w-72" />
          </div>
        </div>
      </div>

      <!-- ── CONTENIDO DE PESTAÑAS ── -->
      <div v-else class="space-y-4">
        <!-- ── TAB 1: IDENTIDAD (IdentityTab) ── -->
        <div v-if="activeTab === 'identity'" class="bg-white rounded-2xl shadow-sm border border-[#E2E8F0] p-6 space-y-4">
          <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div>
              <h2 class="font-bold text-[#1E293B]">Identidad y Personalidad</h2>
              <p class="text-xs text-[#64748B] mt-0.5">Define quién es el agente: su nombre, rol, tono y restricciones de comportamiento base.</p>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-[#94A3B8]">{{ wordCount }} palabras</span>
              <button
                type="button"
                @click="identityText = DEFAULT_IDENTITY; identitySaved = false;"
                class="text-xs text-[#64748B] hover:text-[#1E293B] border border-[#E2E8F0] px-3 py-1.5 rounded-lg hover:bg-[#F8FAFC] transition-colors cursor-pointer"
              >
                Restaurar por defecto
              </button>
              <button
                type="button"
                @click="saveIdentity"
                :disabled="identitySaved"
                class="flex items-center gap-1.5 bg-[#4F5AF5] hover:bg-[#3F49E0] disabled:bg-[#E2E8F0] disabled:text-[#94A3B8] text-white px-4 py-1.5 rounded-lg text-sm font-semibold transition-colors cursor-pointer"
              >
                <Save class="w-3.5 h-3.5" />
                <span>Guardar</span>
              </button>
            </div>
          </div>

          <textarea
            v-model="identityText"
            @input="identitySaved = false"
            rows="12"
            class="w-full border border-[#E2E8F0] rounded-xl px-4 py-3 text-sm text-[#1E293B] placeholder-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#4F5AF5] focus:border-[#4F5AF5] resize-none font-mono leading-relaxed"
            placeholder="Describe la identidad del agente..."
          ></textarea>

          <div class="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 flex items-start gap-2">
            <AlertCircle class="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <p class="text-xs text-amber-800">
              Este texto se inyecta al inicio de cada conversación con Gemini. Sé específico con el tono y las restricciones para mejores resultados.
            </p>
          </div>
        </div>

        <!-- ── TAB 2: APARIENCIA (AppearanceTab) ── -->
        <div v-if="activeTab === 'appearance'" class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Formulario de Configuración -->
          <div class="bg-white rounded-2xl shadow-sm border border-[#E2E8F0] p-6 space-y-6">
            <div>
              <h2 class="font-bold text-[#1E293B]">Personalización del Asistente</h2>
              <p class="text-xs text-[#64748B] mt-0.5">Configura el nombre y la foto de perfil que tus colaboradores verán en los chats y pantallas de carga.</p>
            </div>

            <!-- Nombre de la IA -->
            <div class="space-y-2">
              <label class="text-xs font-bold text-[#475569]">Nombre del Asistente</label>
              <input
                v-model="aiName"
                type="text"
                placeholder="Ej. Asistente IA, Analista de TI..."
                class="w-full border border-[#E2E8F0] rounded-lg px-3 py-2 text-sm text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#4F5AF5] focus:border-[#4F5AF5] transition-colors"
              />
            </div>

            <!-- Avatar Picker -->
            <div class="space-y-3">
              <label class="text-xs font-bold text-[#475569] block">Foto de Perfil (Avatar)</label>
              <div class="flex items-center gap-4">
                <div class="w-16 h-16 rounded-full border border-[#E2E8F0] bg-[#F8FAFC] flex items-center justify-center overflow-hidden shrink-0 shadow-sm relative group">
                  <template v-if="aiAvatar">
                    <img :src="aiAvatar" alt="Vista previa" class="w-full h-full object-cover" />
                    <button
                      type="button"
                      @click="aiAvatar = ''"
                      class="absolute inset-0 bg-black/50 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity text-[10px] font-bold cursor-pointer"
                    >
                      Eliminar
                    </button>
                  </template>
                  <Bot v-else class="w-8 h-8 text-[#94A3B8]" />
                </div>

                <div class="space-y-1.5 flex-1">
                  <label class="inline-flex items-center gap-1.5 bg-[#F1F5F9] hover:bg-[#E2E8F0] text-[#475569] px-3.5 py-2 rounded-lg text-xs font-bold transition-colors cursor-pointer border border-[#E2E8F0]">
                    <Upload class="w-3.5 h-3.5" />
                    <span>Subir imagen</span>
                    <input type="file" accept="image/*" @change="handleAvatarSelect" class="hidden" />
                  </label>
                  <p class="text-[10px] text-[#94A3B8]">Formatos recomendados: PNG, JPG o SVG. Máx 2MB.</p>
                </div>
              </div>

              <!-- Galería de Presets -->
              <div class="space-y-1.5 pt-2">
                <span class="text-[10px] font-bold text-[#64748B] block uppercase tracking-wider">O preseleccionar de la galería</span>
                <div class="flex gap-2">
                  <button
                    v-for="(preset, idx) in presets"
                    :key="idx"
                    type="button"
                    @click="aiAvatar = preset.url"
                    :class="[
                      'w-10 h-10 rounded-full border overflow-hidden transition-all cursor-pointer',
                      aiAvatar === preset.url ? 'ring-2 ring-[#4F5AF5] border-transparent scale-105' : 'border-[#E2E8F0] hover:scale-105'
                    ]"
                    :title="preset.name"
                  >
                    <img :src="preset.url" :alt="preset.name" class="w-full h-full object-cover" />
                  </button>
                  <button
                    type="button"
                    @click="aiAvatar = ''"
                    :class="[
                      'w-10 h-10 rounded-full border border-[#E2E8F0] bg-[#F8FAFC] flex items-center justify-center text-xs font-bold text-[#64748B] hover:scale-105 transition-all cursor-pointer',
                      !aiAvatar ? 'ring-2 ring-[#4F5AF5] border-transparent scale-105' : ''
                    ]"
                    title="Avatar por defecto (Bot)"
                  >
                    <Bot class="w-4 h-4 text-[#94A3B8]" />
                  </button>
                </div>
              </div>
            </div>

            <!-- Guardar -->
            <div class="flex justify-end pt-2">
              <button
                type="button"
                @click="saveAppearance"
                :disabled="saving"
                class="flex items-center gap-1.5 bg-[#4F5AF5] hover:bg-[#3F49E0] disabled:bg-[#E2E8F0] disabled:text-[#94A3B8] text-white px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors shadow-sm cursor-pointer"
              >
                <Save class="w-4 h-4" />
                <span>Guardar Cambios</span>
              </button>
            </div>
          </div>

          <!-- Previsualización en Tiempo Real -->
          <div class="bg-[#F8FAFC] rounded-2xl border border-[#E2E8F0] p-6 flex flex-col justify-between h-full min-h-[350px]">
            <div class="mb-4">
              <h3 class="text-sm font-bold text-[#1E293B]">Vista previa en tiempo real</h3>
              <p class="text-[10px] text-[#64748B]">Así se verá la IA en la interfaz de chat de tus usuarios.</p>
            </div>

            <div class="flex-grow flex items-center justify-center">
              <div class="bg-white rounded-xl border border-[#E2E8F0] shadow-sm flex flex-col overflow-hidden max-w-sm w-full">
                <!-- Mock Header -->
                <div class="px-4 py-3 border-b border-[#F1F5F9] flex items-center gap-2.5 bg-[#4F5AF5]">
                  <div class="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center overflow-hidden shrink-0">
                    <img v-if="aiAvatar" :src="aiAvatar" alt="Avatar" class="w-full h-full object-cover" />
                    <Bot v-else class="w-3.5 h-3.5 text-white" />
                  </div>
                  <div>
                    <p class="text-xs font-semibold text-white">{{ aiName }}</p>
                    <p class="text-[9px] text-blue-200">En línea</p>
                  </div>
                </div>

                <!-- Mock Mensaje -->
                <div class="p-4 space-y-3 bg-[#F8FAFC] h-32 flex flex-col justify-end">
                  <div class="flex gap-2">
                    <div class="w-6 h-6 rounded-full bg-white border border-[#E2E8F0] flex items-center justify-center shrink-0 mt-0.5 overflow-hidden">
                      <img v-if="aiAvatar" :src="aiAvatar" alt="Avatar" class="w-full h-full object-cover" />
                      <Bot v-else class="w-3.5 h-3.5 text-[#4F5AF5]" />
                    </div>
                    <div class="p-3 bg-white border border-[#E2E8F0] rounded-xl rounded-tl-none shadow-sm text-[11px] text-[#334155] leading-relaxed max-w-[80%]">
                      Hola. Cuéntame sobre tu iniciativa de negocio.
                      <p class="text-[9px] text-[#94A3B8] mt-1 font-semibold">{{ aiName }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ── TAB 3: CONTEXTO Y CARPETAS (ContextTab) ── -->
        <div v-if="activeTab === 'context'" class="space-y-4">
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
            <!-- Columna Izquierda: Árbol de Carpetas (4 cols) -->
            <div class="lg:col-span-4 bg-white rounded-2xl border border-[#E2E8F0] shadow-sm p-4 space-y-3.5">
              <div class="flex items-center justify-between pb-3 border-b border-[#F1F5F9]">
                <div class="flex items-center gap-2">
                  <FolderTree class="w-5 h-5 text-[#4F5AF5]" />
                  <div>
                    <h3 class="font-bold text-sm text-[#1E293B]">Carpetas de Base</h3>
                    <p class="text-[11px] text-[#64748B]">Jerarquía hasta 3 niveles</p>
                  </div>
                </div>
                <button
                  type="button"
                  @click="handleOpenCreateFolder(null)"
                  class="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-[#4F5AF5] text-xs font-bold transition-colors cursor-pointer"
                  title="Crear una nueva carpeta raíz"
                >
                  <FolderPlus class="w-3.5 h-3.5" />
                  <span>+ Raíz</span>
                </button>
              </div>

              <!-- Quick Nav: Todas y Sin Carpeta -->
              <div class="space-y-1">
                <button
                  type="button"
                  @click="selectedFolderId = 'all'"
                  :class="[
                    'w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer',
                    selectedFolderId === 'all'
                      ? 'bg-[#4F5AF5] text-white shadow-sm'
                      : 'text-slate-600 hover:bg-slate-100'
                  ]"
                >
                  <div class="flex items-center gap-2">
                    <BookOpen class="w-4 h-4" />
                    <span>Todas las Fichas</span>
                  </div>
                  <span :class="['text-[10px] font-bold px-2 py-0.5 rounded-full', selectedFolderId === 'all' ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-500']">
                    {{ entries.filter(e => e.layer === 'context').length }}
                  </span>
                </button>

                <button
                  type="button"
                  @click="selectedFolderId = 'root'"
                  :class="[
                    'w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer',
                    selectedFolderId === 'root'
                      ? 'bg-[#4F5AF5] text-white shadow-sm'
                      : 'text-slate-600 hover:bg-slate-100'
                  ]"
                >
                  <div class="flex items-center gap-2">
                    <Layers class="w-4 h-4" />
                    <span>Sin Carpeta (General)</span>
                  </div>
                  <span :class="['text-[10px] font-bold px-2 py-0.5 rounded-full', selectedFolderId === 'root' ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-500']">
                    {{ rootCount }}
                  </span>
                </button>
              </div>

              <!-- Buscador de Carpetas -->
              <div v-if="folders.length > 5" class="relative">
                <Search class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  v-model="folderSearchTerm"
                  type="text"
                  placeholder="Buscar carpeta..."
                  class="w-full pl-8 pr-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-[#4F5AF5]"
                />
              </div>

              <!-- Árbol Recursivo de Carpetas -->
              <div class="pt-2 border-t border-[#F1F5F9] max-h-[58vh] overflow-y-auto space-y-1 pr-1">
                <div v-if="folders.length === 0" class="text-center py-6 text-slate-400">
                  <Folder class="w-7 h-7 mx-auto mb-1.5 text-slate-300" />
                  <p class="text-xs">Aún no hay carpetas creadas.</p>
                </div>
                <template v-else>
                  <div v-for="node in folderTree" :key="node.id" class="space-y-0.5">
                    <!-- Nivel 1 -->
                    <div
                      @click="selectedFolderId = node.id"
                      :class="[
                        'group flex items-center justify-between px-2.5 py-1.5 rounded-xl text-xs transition-all cursor-pointer',
                        selectedFolderId === node.id ? 'bg-[#EEF2FF] text-[#4F5AF5] font-bold border border-[#4F5AF5]/30' : 'text-slate-700 hover:bg-slate-100 font-medium'
                      ]"
                    >
                      <div class="flex items-center gap-1.5 min-w-0">
                        <button
                          v-if="node.children.length > 0"
                          type="button"
                          @click.stop="toggleFolderExpand(node.id)"
                          class="p-0.5 hover:bg-slate-200 rounded text-slate-400 hover:text-slate-600"
                        >
                          <ChevronDown v-if="expandedFolderIds.has(node.id)" class="w-3.5 h-3.5" />
                          <ChevronRight v-else class="w-3.5 h-3.5" />
                        </button>
                        <span v-else class="w-3.5"></span>
                        <FolderOpen v-if="expandedFolderIds.has(node.id)" class="w-4 h-4 shrink-0 text-[#4F5AF5]" />
                        <Folder v-else class="w-4 h-4 shrink-0 text-amber-500" />
                        <span class="truncate max-w-[140px]">{{ node.name }}</span>
                        <span class="text-[9px] font-black uppercase text-slate-400">L{{ node.level }}</span>
                      </div>

                      <div class="flex items-center gap-1">
                        <span :class="['text-[10px] font-bold px-1.5 py-0.2 rounded-full', selectedFolderId === node.id ? 'bg-indigo-100 text-[#4F5AF5]' : 'bg-slate-100 text-slate-500']">
                          {{ node.itemCount }}
                        </span>
                        <div class="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            v-if="node.level < 3"
                            type="button"
                            @click.stop="handleOpenCreateFolder(node)"
                            class="p-1 rounded bg-indigo-50 hover:bg-indigo-100 text-[#4F5AF5]"
                            title="Crear subcarpeta"
                          >
                            <Plus class="w-3 h-3 stroke-[2.5]" />
                          </button>
                          <button
                            type="button"
                            @click.stop="handleOpenEditFolder(node)"
                            class="p-1 rounded hover:bg-slate-200 text-slate-500"
                            title="Renombrar"
                          >
                            <Pencil class="w-3 h-3" />
                          </button>
                          <button
                            type="button"
                            @click.stop="handleOpenDeleteFolder(node)"
                            class="p-1 rounded hover:bg-red-100 text-slate-400 hover:text-red-600"
                            title="Eliminar"
                          >
                            <Trash2 class="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    </div>

                    <!-- Nivel 2 y 3 Anidados -->
                    <div v-if="node.children.length > 0 && expandedFolderIds.has(node.id)" class="border-l border-slate-200 ml-4 space-y-0.5 pl-2">
                      <div v-for="child in node.children" :key="child.id" class="space-y-0.5">
                        <div
                          @click="selectedFolderId = child.id"
                          :class="[
                            'group flex items-center justify-between px-2 py-1 rounded-xl text-xs transition-all cursor-pointer',
                            selectedFolderId === child.id ? 'bg-[#EEF2FF] text-[#4F5AF5] font-bold border border-[#4F5AF5]/30' : 'text-slate-700 hover:bg-slate-100 font-medium'
                          ]"
                        >
                          <div class="flex items-center gap-1.5 min-w-0">
                            <button
                              v-if="child.children.length > 0"
                              type="button"
                              @click.stop="toggleFolderExpand(child.id)"
                              class="p-0.5 hover:bg-slate-200 rounded text-slate-400"
                            >
                              <ChevronDown v-if="expandedFolderIds.has(child.id)" class="w-3 h-3" />
                              <ChevronRight v-else class="w-3 h-3" />
                            </button>
                            <span v-else class="w-3"></span>
                            <Folder class="w-3.5 h-3.5 text-amber-500 shrink-0" />
                            <span class="truncate max-w-[120px]">{{ child.name }}</span>
                            <span class="text-[9px] font-black uppercase text-slate-400">L{{ child.level }}</span>
                          </div>
                          <div class="flex items-center gap-1">
                            <span class="text-[10px] font-bold px-1.5 py-0.2 rounded-full bg-slate-100 text-slate-500">{{ child.itemCount }}</span>
                            <div class="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button v-if="child.level < 3" type="button" @click.stop="handleOpenCreateFolder(child)" class="p-1 rounded bg-indigo-50 text-[#4F5AF5]"><Plus class="w-3 h-3" /></button>
                              <button type="button" @click.stop="handleOpenEditFolder(child)" class="p-1 rounded hover:bg-slate-200 text-slate-500"><Pencil class="w-3 h-3" /></button>
                              <button type="button" @click.stop="handleOpenDeleteFolder(child)" class="p-1 rounded hover:bg-red-100 text-slate-400 hover:text-red-600"><Trash2 class="w-3 h-3" /></button>
                            </div>
                          </div>
                        </div>

                        <!-- Nivel 3 -->
                        <div v-if="child.children.length > 0 && expandedFolderIds.has(child.id)" class="border-l border-slate-200 ml-4 space-y-0.5 pl-2">
                          <div
                            v-for="sub in child.children"
                            :key="sub.id"
                            @click="selectedFolderId = sub.id"
                            :class="[
                              'group flex items-center justify-between px-2 py-1 rounded-xl text-xs transition-all cursor-pointer',
                              selectedFolderId === sub.id ? 'bg-[#EEF2FF] text-[#4F5AF5] font-bold border border-[#4F5AF5]/30' : 'text-slate-600 hover:bg-slate-100'
                            ]"
                          >
                            <div class="flex items-center gap-1.5 min-w-0">
                              <FileText class="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                              <span class="truncate max-w-[110px]">{{ sub.name }}</span>
                              <span class="text-[9px] font-black uppercase text-slate-400">L3</span>
                            </div>
                            <div class="flex items-center gap-1">
                              <span class="text-[10px] font-bold px-1.5 py-0.2 rounded-full bg-slate-100 text-slate-500">{{ sub.itemCount }}</span>
                              <div class="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button type="button" @click.stop="handleOpenEditFolder(sub)" class="p-1 rounded hover:bg-slate-200 text-slate-500"><Pencil class="w-3 h-3" /></button>
                                <button type="button" @click.stop="handleOpenDeleteFolder(sub)" class="p-1 rounded hover:bg-red-100 text-slate-400 hover:text-red-600"><Trash2 class="w-3 h-3" /></button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </div>

            <!-- Columna Derecha: Fichas de la Carpeta (8 cols) -->
            <div class="lg:col-span-8 space-y-4">
              <!-- Header Panel Derecho con Breadcrumbs y Acciones -->
              <div class="bg-white rounded-2xl border border-[#E2E8F0] shadow-sm p-4 sm:p-5">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#F1F5F9]">
                  <div class="min-w-0">
                    <div class="flex items-center gap-1.5 text-xs text-slate-400 font-medium overflow-x-auto whitespace-nowrap">
                      <span @click="selectedFolderId = 'all'" class="hover:text-[#4F5AF5] cursor-pointer font-semibold text-slate-500">Base de Conocimiento</span>
                      <span>/</span>
                      <span v-if="selectedFolderId === 'all'" class="text-slate-800 font-bold">Todas las Fichas</span>
                      <span v-else-if="selectedFolderId === 'root'" class="text-slate-800 font-bold">Sin Carpeta (General)</span>
                      <span v-else-if="activeFolder" class="text-slate-900 font-bold flex items-center gap-1">
                        <Folder class="w-3.5 h-3.5 text-amber-500 shrink-0" />
                        {{ activeFolder.name }}
                        <span class="text-[10px] font-black uppercase px-1.5 py-0.2 rounded bg-amber-50 text-amber-700 border border-amber-200">
                          Nivel {{ activeFolder.level }}
                        </span>
                      </span>
                    </div>
                    <h2 class="text-base font-bold text-slate-900 mt-1">
                      {{ selectedFolderId === 'all' ? 'Todas las Fichas Institucionales' : selectedFolderId === 'root' ? 'Fichas sin Carpeta Asignada' : activeFolder?.name || 'Carpeta' }}
                    </h2>
                  </div>

                  <!-- Botones de Acción -->
                  <div class="flex items-center gap-2 shrink-0">
                    <button
                      type="button"
                      @click="showGuide = !showGuide"
                      class="p-2 rounded-xl text-slate-500 hover:text-[#4F5AF5] hover:bg-slate-100 transition-colors border border-slate-200 cursor-pointer"
                      title="Guía de Formatos e Interpretación"
                    >
                      <Sparkles class="w-4 h-4" />
                    </button>
                    <button
                      v-if="activeFolder && activeFolder.level < 3"
                      type="button"
                      @click="handleOpenCreateFolder(activeFolder)"
                      class="flex items-center gap-1.5 border border-indigo-200 bg-indigo-50/80 hover:bg-indigo-100 text-[#4F5AF5] px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer shadow-xs"
                    >
                      <FolderPlus class="w-3.5 h-3.5" />
                      <span>+ Subcarpeta</span>
                    </button>
                    <input ref="fileInputRef" type="file" accept=".pdf,.docx,.txt,.png,.jpg,.jpeg,.webp" class="hidden" @change="handleFileUpload" />
                    <button
                      type="button"
                      @click="fileInputRef?.click()"
                      :disabled="uploading"
                      class="flex items-center gap-1.5 border border-[#E2E8F0] hover:bg-slate-50 text-[#64748B] px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer"
                    >
                      <Upload class="w-3.5 h-3.5" />
                      <span>{{ uploading ? 'Procesando...' : 'Subir Doc' }}</span>
                    </button>
                    <button
                      type="button"
                      @click="openNewContext"
                      class="flex items-center gap-1.5 bg-[#4F5AF5] hover:bg-[#3F49E0] text-white px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all shadow-xs cursor-pointer"
                    >
                      <Plus class="w-3.5 h-3.5" />
                      <span>Nueva Ficha</span>
                    </button>
                  </div>
                </div>

                <!-- Buscador de Fichas -->
                <div class="mt-3.5 relative">
                  <Search class="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    v-model="entrySearchTerm"
                    type="text"
                    placeholder="Buscar fichas por título o contenido..."
                    class="w-full pl-9 pr-8 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
                  />
                </div>
              </div>

              <!-- Guía Desplegable -->
              <div v-if="showGuide" class="bg-gradient-to-br from-[#F8FAFC] via-[#F1F5F9] to-[#EEF2FF] border border-[#E2E8F0] rounded-2xl p-4 text-xs text-[#334155] shadow-xs">
                <div class="flex items-center justify-between pb-2.5 mb-3 border-b border-[#E2E8F0]">
                  <div class="flex items-center gap-2">
                    <Sparkles class="w-4 h-4 text-[#4F5AF5]" />
                    <span class="font-bold text-sm text-[#1E293B]">Guía de Formatos e Interpretación de TEO</span>
                  </div>
                  <button @click="showGuide = false" class="text-[#94A3B8] hover:text-[#1E293B] cursor-pointer">
                    <X class="w-4 h-4" />
                  </button>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  <div class="bg-white rounded-xl p-3 border border-[#E2E8F0] space-y-1">
                    <div class="flex items-center gap-1.5 font-bold text-[#1E293B]">
                      <FileText class="w-4 h-4 text-blue-600" />
                      <span>Documentos de Texto (.pdf, .docx, .txt)</span>
                    </div>
                    <p class="text-[#64748B] leading-relaxed">Extrae fragmentos temáticos para alimentar políticas, glosarios y reglas de negocio por carpeta.</p>
                  </div>
                  <div class="bg-white rounded-xl p-3 border border-[#E2E8F0] space-y-1">
                    <div class="flex items-center gap-1.5 font-bold text-[#1E293B]">
                      <ImageIcon class="w-4 h-4 text-purple-600" />
                      <span>Diagramas con IA Vision (.png, .jpg)</span>
                    </div>
                    <p class="text-[#64748B] leading-relaxed">Gemini Vision transcribe esquemas C4, BPMN y arquitecturas Cloud generando fichas detalladas.</p>
                  </div>
                </div>
              </div>

              <!-- Formulario de Ficha (Crear o Editar) -->
              <div v-if="showContextForm" class="bg-[#EEF2FF] border border-[#4F5AF5]/30 rounded-2xl p-4 sm:p-5 space-y-3.5 shadow-sm">
                <div class="flex items-center justify-between pb-2 border-b border-[#4F5AF5]/20">
                  <h4 class="font-bold text-sm text-[#1E293B]">
                    {{ editingContextEntry ? 'Editar Ficha de Conocimiento' : 'Nueva Ficha de Conocimiento' }}
                  </h4>
                  <button @click="showContextForm = false; editingContextEntry = null;" class="text-slate-400 hover:text-slate-600 cursor-pointer">
                    <X class="w-4 h-4" />
                  </button>
                </div>

                <div>
                  <label class="block text-[11px] font-bold text-[#475569] uppercase tracking-wider mb-1">Título de la Ficha</label>
                  <input
                    v-model="contextForm.title"
                    type="text"
                    placeholder="Ej: Lineamientos de Arquitectura Corporativa"
                    class="w-full border border-[#CBD5E1] bg-white rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]"
                  />
                </div>

                <div>
                  <label class="block text-[11px] font-bold text-[#475569] uppercase tracking-wider mb-1">Carpeta de Destino</label>
                  <select
                    v-model="contextForm.folder_id"
                    class="w-full border border-[#CBD5E1] bg-white rounded-xl px-3.5 py-2 text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]"
                  >
                    <option value="">📂 Sin carpeta (Raíz / General)</option>
                    <option v-for="f in flattenedFolderOptions" :key="f.id" :value="f.id">
                      {{ '  '.repeat(f.level - 1) + (f.level > 1 ? '↳ ' : '') + `📁 ${f.name} (Nivel ${f.level})` }}
                    </option>
                  </select>
                </div>

                <div>
                  <label class="block text-[11px] font-bold text-[#475569] uppercase tracking-wider mb-1">Contenido de la Ficha</label>
                  <textarea
                    v-model="contextForm.content"
                    rows="6"
                    placeholder="Redacta la política, regla, estándar o definición técnica que TEO debe recordar..."
                    class="w-full border border-[#CBD5E1] bg-white rounded-xl px-3.5 py-2.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#4F5AF5] resize-none leading-relaxed"
                  ></textarea>
                </div>

                <div class="flex justify-end gap-2 pt-1">
                  <button
                    type="button"
                    @click="showContextForm = false; editingContextEntry = null;"
                    class="px-4 py-1.5 rounded-xl border border-slate-300 bg-white text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    @click="saveContextEntry"
                    class="px-4 py-1.5 rounded-xl bg-[#4F5AF5] hover:bg-indigo-600 text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
                  >
                    Guardar Ficha
                  </button>
                </div>
              </div>

              <!-- Lista de Fichas (ContextCards) -->
              <div class="space-y-3">
                <div v-if="filteredContextEntries.length === 0 && !showContextForm" class="bg-white rounded-2xl border border-dashed border-slate-300 p-12 text-center">
                  <BookOpen class="w-10 h-10 text-slate-300 mx-auto mb-2" />
                  <h3 class="text-sm font-bold text-slate-700">No hay fichas en esta vista</h3>
                  <p class="text-xs text-slate-400 max-w-sm mx-auto mt-1">
                    Esta carpeta aún no tiene fichas de conocimiento. Puedes crear una ficha o subir un documento.
                  </p>
                  <div class="mt-4 flex flex-wrap items-center justify-center gap-2">
                    <button
                      type="button"
                      @click="openNewContext"
                      class="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#4F5AF5] hover:bg-indigo-600 text-white rounded-xl text-xs font-bold transition-colors cursor-pointer shadow-xs"
                    >
                      <Plus class="w-3.5 h-3.5" />
                      <span>Crear Ficha</span>
                    </button>
                  </div>
                </div>

                <!-- Tarjeta de Ficha Idéntica a ContextCard -->
                <div
                  v-for="entry in filteredContextEntries"
                  :key="entry.id"
                  :class="[
                    'border rounded-xl overflow-hidden transition-opacity bg-white',
                    entry.is_active ? 'border-[#E2E8F0]' : 'border-dashed border-[#E2E8F0] bg-slate-50 opacity-60'
                  ]"
                >
                  <div class="flex items-center justify-between px-4 py-3">
                    <div class="flex items-center gap-2 min-w-0">
                      <FileText class="w-4 h-4 text-blue-500 shrink-0" />
                      <p class="text-sm font-semibold text-[#1E293B] truncate">{{ entry.title }}</p>
                      <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                        {{ entry.source === 'document' ? '📄 Doc' : entry.source === 'feedback' ? '💬 Feedback' : 'Manual' }}
                      </span>
                    </div>
                    <div class="flex items-center gap-1 shrink-0">
                      <button
                        type="button"
                        @click="openMoveEntry(entry)"
                        class="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-[#4F5AF5] cursor-pointer"
                        title="Mover a otra carpeta"
                      >
                        <FolderInput class="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        @click="openEditContext(entry)"
                        class="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-[#4F5AF5] cursor-pointer"
                        title="Editar"
                      >
                        <Pencil class="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        @click="toggleEntry(entry.id)"
                        class="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-emerald-600 cursor-pointer"
                        :title="entry.is_active ? 'Desactivar' : 'Activar'"
                      >
                        <ToggleRight v-if="entry.is_active" class="w-4 h-4 text-emerald-500" />
                        <ToggleLeft v-else class="w-4 h-4" />
                      </button>
                      <button
                        type="button"
                        @click="deleteEntry(entry.id)"
                        class="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500 cursor-pointer"
                        title="Eliminar"
                      >
                        <Trash2 class="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                  <div class="px-4 pb-4 text-sm text-[#64748B] border-t border-[#F1F5F9] pt-3 whitespace-pre-wrap leading-relaxed">
                    {{ entry.content }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ── TAB 4: EJEMPLOS (ExamplesTab) ── -->
        <div v-if="activeTab === 'examples'" class="bg-white rounded-2xl shadow-sm border border-[#E2E8F0] p-6 space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="font-bold text-[#1E293B]">Ejemplos de Conversación (Few-shot)</h2>
              <p class="text-xs text-[#64748B] mt-0.5">Pares de "el usuario dice → el agente responde" que sirven de guía al modelo.</p>
            </div>
            <button
              type="button"
              @click="openNewExample"
              class="flex items-center gap-2 bg-[#4F5AF5] hover:bg-[#3F49E0] text-white px-3 py-1.5 rounded-lg text-sm font-semibold cursor-pointer"
            >
              <Plus class="w-4 h-4" />
              <span>Nuevo Ejemplo</span>
            </button>
          </div>

          <!-- Formulario Nuevo / Editar Ejemplo -->
          <div v-if="showExampleForm" class="border border-[#4F5AF5]/30 bg-[#EEF2FF] rounded-xl p-4 space-y-3">
            <div>
              <label class="block text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-1">El usuario dice...</label>
              <input
                v-model="exampleForm.title"
                type="text"
                placeholder="Ej: Quiero automatizar los reportes de ventas"
                class="w-full border border-[#E2E8F0] bg-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]"
              />
            </div>
            <div>
              <label class="block text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-1">El agente debería responder...</label>
              <textarea
                v-model="exampleForm.content"
                rows="4"
                placeholder="Ej: Entendido. ¿Con qué frecuencia se generan esos reportes y quién los consume actualmente?"
                class="w-full border border-[#E2E8F0] bg-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#4F5AF5] resize-none"
              ></textarea>
            </div>
            <div class="flex justify-end gap-2">
              <button
                type="button"
                @click="showExampleForm = false; editingExample = null;"
                class="border border-[#E2E8F0] bg-white px-3 py-1.5 rounded-lg text-sm font-semibold text-[#64748B] hover:bg-[#F8FAFC] cursor-pointer"
              >
                Cancelar
              </button>
              <button
                type="button"
                @click="saveExample"
                class="bg-[#4F5AF5] text-white px-4 py-1.5 rounded-lg text-sm font-semibold hover:bg-[#3F49E0] cursor-pointer"
              >
                Guardar Ejemplo
              </button>
            </div>
          </div>

          <!-- Lista de Ejemplos en 2 Columnas -->
          <div class="space-y-2">
            <div v-if="byLayer('examples').length === 0 && !showExampleForm" class="text-center py-12 text-[#94A3B8]">
              <MessageSquare class="w-8 h-8 mx-auto mb-2 text-slate-300" />
              <p class="text-sm">No hay ejemplos. Agrega pares de conversación ideal.</p>
            </div>

            <div
              v-for="e in byLayer('examples')"
              :key="e.id"
              :class="[
                'rounded-xl border overflow-hidden',
                e.is_active ? 'border-[#E2E8F0]' : 'border-dashed border-[#E2E8F0] opacity-50'
              ]"
            >
              <div class="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#E2E8F0]">
                <div class="p-3 bg-blue-50">
                  <p class="text-[10px] font-bold text-blue-600 uppercase tracking-wider mb-1">Usuario dice</p>
                  <p class="text-sm text-[#1E293B]">{{ e.title }}</p>
                </div>
                <div class="p-3 bg-emerald-50">
                  <p class="text-[10px] font-bold text-emerald-600 uppercase tracking-wider mb-1">Agente responde</p>
                  <p class="text-sm text-[#1E293B]">{{ e.content }}</p>
                </div>
              </div>
              <div class="flex items-center justify-between px-3 py-2 bg-white border-t border-[#E2E8F0]">
                <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                  {{ e.source === 'feedback' ? '💬 Feedback' : 'Manual' }}
                </span>
                <div class="flex items-center gap-1">
                  <button type="button" @click="openEditExample(e)" class="p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-[#4F5AF5] cursor-pointer">
                    <Pencil class="w-3.5 h-3.5" />
                  </button>
                  <button type="button" @click="toggleEntry(e.id)" class="p-1 rounded hover:bg-slate-100 text-slate-400 cursor-pointer">
                    <ToggleRight v-if="e.is_active" class="w-4 h-4 text-emerald-500" />
                    <ToggleLeft v-else class="w-4 h-4" />
                  </button>
                  <button type="button" @click="deleteEntry(e.id)" class="p-1 rounded hover:bg-red-50 text-slate-400 hover:text-red-500 cursor-pointer">
                    <Trash2 class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ── TAB 5: GUARDARRAÍLES (GuardrailsTab) ── -->
        <div v-if="activeTab === 'guardrails'" class="bg-white rounded-2xl shadow-sm border border-[#E2E8F0] p-6 space-y-4">
          <div>
            <h2 class="font-bold text-[#1E293B]">Guardarraíles</h2>
            <p class="text-xs text-[#64748B] mt-0.5">Restricciones absolutas de comportamiento. Prioriza directivas críticas.</p>
          </div>

          <!-- Input Agregar Regla Rápida -->
          <div class="flex gap-2">
            <input
              v-model="newGuardrailText"
              @keyup.enter="addGuardrail"
              type="text"
              placeholder="Ej: No revelar datos de otros usuarios ni iniciativas"
              class="flex-1 border border-[#E2E8F0] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]"
            />
            <button
              type="button"
              @click="addGuardrail"
              :disabled="!newGuardrailText.trim()"
              class="flex items-center gap-2 bg-[#4F5AF5] hover:bg-[#3F49E0] disabled:bg-[#E2E8F0] text-white px-4 py-2 rounded-lg text-sm font-semibold cursor-pointer"
            >
              <Plus class="w-4 h-4" />
              <span>Agregar</span>
            </button>
          </div>

          <!-- Lista de Guardarraíles -->
          <div class="space-y-2">
            <div v-if="byLayer('guardrails').length === 0" class="text-center py-12 text-[#94A3B8]">
              <ShieldAlert class="w-8 h-8 mx-auto mb-2 text-slate-300" />
              <p class="text-sm">No hay reglas definidas. Agrega restricciones de comportamiento.</p>
            </div>

            <template v-else>
              <div
                v-for="entry in byLayer('guardrails')"
                :key="entry.id"
              >
                <!-- Modo Edición Inline -->
                <div v-if="editingGuardrail?.id === entry.id" class="flex gap-2 p-3 rounded-xl border border-[#4F5AF5]/40 bg-[#EEF2FF]">
                  <textarea
                    v-model="editingGuardrail.text"
                    rows="2"
                    class="flex-1 border border-[#E2E8F0] bg-white rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#4F5AF5] resize-y"
                  ></textarea>
                  <button type="button" @click="saveEditingGuardrail" class="bg-[#4F5AF5] text-white px-3 py-1.5 rounded-lg text-sm font-semibold cursor-pointer">Guardar</button>
                  <button type="button" @click="editingGuardrail = null" class="border border-[#E2E8F0] bg-white px-3 py-1.5 rounded-lg text-sm font-semibold text-[#64748B] cursor-pointer">Cancelar</button>
                </div>

                <!-- Modo Tarjeta -->
                <div
                  v-else
                  :class="[
                    'flex items-start gap-3 p-4 rounded-xl border bg-white shadow-xs transition-opacity',
                    entry.is_active ? '' : 'opacity-50'
                  ]"
                >
                  <GripVertical class="w-4 h-4 text-slate-300 mt-0.5 shrink-0" />
                  <p class="flex-1 text-sm text-[#1E293B]">{{ entry.content }}</p>
                  <div class="flex items-center gap-1 shrink-0">
                    <button type="button" @click="editingGuardrail = { id: entry.id, text: entry.content }" class="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-[#4F5AF5] cursor-pointer">
                      <Pencil class="w-3.5 h-3.5" />
                    </button>
                    <button type="button" @click="toggleEntry(entry.id)" class="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-emerald-600 cursor-pointer">
                      <ToggleRight v-if="entry.is_active" class="w-4 h-4 text-emerald-500" />
                      <ToggleLeft v-else class="w-4 h-4" />
                    </button>
                    <button type="button" @click="deleteEntry(entry.id)" class="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500 cursor-pointer">
                      <Trash2 class="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- ── TAB 6: FUNCIONES Y TOGGLES (SettingsTab) ── -->
        <div v-if="activeTab === 'settings'" class="bg-white rounded-2xl shadow-sm border border-[#E2E8F0] p-6 space-y-6">
          <div>
            <h2 class="font-bold text-[#1E293B]">Configuración de Funciones en el Chat</h2>
            <p class="text-xs text-[#64748B] mt-0.5">Activa o desactiva las capacidades adicionales del chat para los usuarios y pruebas.</p>
          </div>

          <div class="divide-y divide-[#E2E8F0]">
            <!-- Toggle 1: Micrófono -->
            <div class="py-4 flex items-center justify-between">
              <div class="space-y-1">
                <span class="text-sm font-semibold text-[#1E293B] flex items-center gap-2">
                  <Mic class="w-4 h-4 text-violet-500" />
                  Entrada por Micrófono (Voz a Texto)
                </span>
                <p class="text-xs text-[#64748B]">Permite a los usuarios grabar audio con su micrófono y transcribirlo automáticamente.</p>
              </div>
              <button
                type="button"
                @click="toggleMicSetting"
                :class="[
                  'w-12 h-6 rounded-full p-1 transition-colors duration-200 cursor-pointer',
                  useMic ? 'bg-violet-600' : 'bg-slate-200'
                ]"
              >
                <div :class="['bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-200', useMic ? 'translate-x-6' : 'translate-x-0']" />
              </button>
            </div>

            <!-- Toggle 2: Archivos adjuntos -->
            <div class="py-4 flex items-center justify-between">
              <div class="space-y-1">
                <span class="text-sm font-semibold text-[#1E293B] flex items-center gap-2">
                  <Paperclip class="w-4 h-4 text-[#4F5AF5]" />
                  Subida de Archivos Adjuntos
                </span>
                <p class="text-xs text-[#64748B]">Permite adjuntar y leer archivos (PDF, DOCX, TXT e imágenes) para alimentar el contexto de la conversación.</p>
              </div>
              <button
                type="button"
                @click="toggleAttachmentsSetting"
                :class="[
                  'w-12 h-6 rounded-full p-1 transition-colors duration-200 cursor-pointer',
                  useAttachments ? 'bg-[#4F5AF5]' : 'bg-slate-200'
                ]"
              >
                <div :class="['bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-200', useAttachments ? 'translate-x-6' : 'translate-x-0']" />
              </button>
            </div>
          </div>

          <!-- Configuración de Formatos y Límites -->
          <div v-if="useAttachments" class="pt-6 border-t border-[#E2E8F0] space-y-4">
            <div>
              <h3 class="text-sm font-semibold text-[#1E293B]">Formatos de Archivo y Límites de Tamaño</h3>
              <p class="text-xs text-[#64748B] mt-0.5">Habilita los formatos permitidos y define el tamaño máximo en Megabytes (MB) para cada uno.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- PDF -->
              <div :class="['flex flex-col bg-slate-50 border border-[#E2E8F0] rounded-xl p-4 space-y-3 transition-opacity', !fileTypes.pdf.enabled ? 'opacity-65' : '']">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold text-[#475569] flex items-center gap-1.5">
                    <FileText class="w-4 h-4 text-red-500" /> Archivos PDF (.pdf)
                  </span>
                  <button
                    type="button"
                    @click="toggleFileTypeSetting('pdf')"
                    :class="['w-10 h-5 rounded-full p-0.5 transition-colors cursor-pointer', fileTypes.pdf.enabled ? 'bg-red-500' : 'bg-slate-300']"
                  >
                    <div :class="['bg-white w-4 h-4 rounded-full shadow-md transform transition-transform', fileTypes.pdf.enabled ? 'translate-x-5' : 'translate-x-0']" />
                  </button>
                </div>
                <div class="flex items-center justify-between text-xs pt-1 border-t border-dashed border-[#E2E8F0]">
                  <span class="text-[#64748B]">Tamaño máximo:</span>
                  <div class="flex items-center gap-1.5">
                    <input
                      type="number"
                      min="0.1"
                      max="50"
                      step="0.5"
                      :disabled="!fileTypes.pdf.enabled"
                      :value="fileTypes.pdf.maxMb"
                      @change="e => updateFileSizeLimit('pdf', parseFloat((e.target as HTMLInputElement).value))"
                      class="w-16 bg-white border border-[#E2E8F0] rounded-lg px-2.5 py-0.5 text-xs font-semibold text-right"
                    />
                    <span class="text-[#64748B] font-semibold">MB</span>
                  </div>
                </div>
              </div>

              <!-- Word DOCX -->
              <div :class="['flex flex-col bg-slate-50 border border-[#E2E8F0] rounded-xl p-4 space-y-3 transition-opacity', !fileTypes.docx.enabled ? 'opacity-65' : '']">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold text-[#475569] flex items-center gap-1.5">
                    <FileText class="w-4 h-4 text-blue-500" /> Documentos Word (.docx)
                  </span>
                  <button
                    type="button"
                    @click="toggleFileTypeSetting('docx')"
                    :class="['w-10 h-5 rounded-full p-0.5 transition-colors cursor-pointer', fileTypes.docx.enabled ? 'bg-blue-500' : 'bg-slate-300']"
                  >
                    <div :class="['bg-white w-4 h-4 rounded-full shadow-md transform transition-transform', fileTypes.docx.enabled ? 'translate-x-5' : 'translate-x-0']" />
                  </button>
                </div>
                <div class="flex items-center justify-between text-xs pt-1 border-t border-dashed border-[#E2E8F0]">
                  <span class="text-[#64748B]">Tamaño máximo:</span>
                  <div class="flex items-center gap-1.5">
                    <input
                      type="number"
                      min="0.1"
                      max="50"
                      step="0.5"
                      :disabled="!fileTypes.docx.enabled"
                      :value="fileTypes.docx.maxMb"
                      @change="e => updateFileSizeLimit('docx', parseFloat((e.target as HTMLInputElement).value))"
                      class="w-16 bg-white border border-[#E2E8F0] rounded-lg px-2.5 py-0.5 text-xs font-semibold text-right"
                    />
                    <span class="text-[#64748B] font-semibold">MB</span>
                  </div>
                </div>
              </div>

              <!-- Plain Text TXT -->
              <div :class="['flex flex-col bg-slate-50 border border-[#E2E8F0] rounded-xl p-4 space-y-3 transition-opacity', !fileTypes.txt.enabled ? 'opacity-65' : '']">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold text-[#475569] flex items-center gap-1.5">
                    <FileText class="w-4 h-4 text-slate-500" /> Archivos de Texto (.txt)
                  </span>
                  <button
                    type="button"
                    @click="toggleFileTypeSetting('txt')"
                    :class="['w-10 h-5 rounded-full p-0.5 transition-colors cursor-pointer', fileTypes.txt.enabled ? 'bg-slate-500' : 'bg-slate-300']"
                  >
                    <div :class="['bg-white w-4 h-4 rounded-full shadow-md transform transition-transform', fileTypes.txt.enabled ? 'translate-x-5' : 'translate-x-0']" />
                  </button>
                </div>
                <div class="flex items-center justify-between text-xs pt-1 border-t border-dashed border-[#E2E8F0]">
                  <span class="text-[#64748B]">Tamaño máximo:</span>
                  <div class="flex items-center gap-1.5">
                    <input
                      type="number"
                      min="0.1"
                      max="20"
                      step="0.5"
                      :disabled="!fileTypes.txt.enabled"
                      :value="fileTypes.txt.maxMb"
                      @change="e => updateFileSizeLimit('txt', parseFloat((e.target as HTMLInputElement).value))"
                      class="w-16 bg-white border border-[#E2E8F0] rounded-lg px-2.5 py-0.5 text-xs font-semibold text-right"
                    />
                    <span class="text-[#64748B] font-semibold">MB</span>
                  </div>
                </div>
              </div>

              <!-- Imágenes -->
              <div :class="['flex flex-col bg-slate-50 border border-[#E2E8F0] rounded-xl p-4 space-y-3 transition-opacity', !fileTypes.image.enabled ? 'opacity-65' : '']">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold text-[#475569] flex items-center gap-1.5">
                    <ImageIcon class="w-4 h-4 text-emerald-500" /> Imágenes (JPG, PNG, WEBP)
                  </span>
                  <button
                    type="button"
                    @click="toggleFileTypeSetting('image')"
                    :class="['w-10 h-5 rounded-full p-0.5 transition-colors cursor-pointer', fileTypes.image.enabled ? 'bg-emerald-500' : 'bg-slate-300']"
                  >
                    <div :class="['bg-white w-4 h-4 rounded-full shadow-md transform transition-transform', fileTypes.image.enabled ? 'translate-x-5' : 'translate-x-0']" />
                  </button>
                </div>
                <div class="flex items-center justify-between text-xs pt-1 border-t border-dashed border-[#E2E8F0]">
                  <span class="text-[#64748B]">Tamaño máximo:</span>
                  <div class="flex items-center gap-1.5">
                    <input
                      type="number"
                      min="0.1"
                      max="20"
                      step="0.5"
                      :disabled="!fileTypes.image.enabled"
                      :value="fileTypes.image.maxMb"
                      @change="e => updateFileSizeLimit('image', parseFloat((e.target as HTMLInputElement).value))"
                      class="w-16 bg-white border border-[#E2E8F0] rounded-lg px-2.5 py-0.5 text-xs font-semibold text-right"
                    />
                    <span class="text-[#64748B] font-semibold">MB</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ── TAB 7: RETROALIMENTACIÓN (FeedbackTab) ── -->
        <div v-if="activeTab === 'feedback'" class="bg-white rounded-2xl shadow-sm border border-[#E2E8F0] p-6 space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="font-bold text-[#1E293B]">Retroalimentación de Conversaciones</h2>
              <p class="text-xs text-[#64748B] mt-0.5">Mensajes calificados por usuarios en conversaciones reales. Apruébalos como ejemplos de entrenamiento.</p>
            </div>
            <div class="flex gap-1 bg-[#F8FAFC] rounded-lg p-1 border border-[#E2E8F0]">
              <button
                v-for="f in (['all', 'negative', 'positive'] as const)"
                :key="f"
                @click="feedbackFilter = f"
                :class="[
                  'px-3 py-1 rounded-md text-xs font-semibold transition-colors cursor-pointer',
                  feedbackFilter === f ? 'bg-white shadow-sm text-[#1E293B]' : 'text-[#64748B] hover:text-[#1E293B]'
                ]"
              >
                {{ f === 'all' ? 'Todos' : f === 'negative' ? '👎 Negativos' : '👍 Positivos' }}
              </button>
            </div>
          </div>

          <div v-if="filteredFeedbackList.length === 0" class="text-center py-12 text-[#94A3B8]">
            <ThumbsUp class="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <p class="text-sm">No hay retroalimentación pendiente de revisión.</p>
            <p class="text-xs mt-1">Los usuarios deben calificar mensajes del agente en el chat de iniciativas.</p>
          </div>

          <div v-else class="space-y-4">
            <div
              v-for="fb in filteredFeedbackList"
              :key="fb.id"
              :class="[
                'rounded-xl border overflow-hidden',
                fb.rating === 'negative' ? 'border-red-200 bg-red-50/30' : 'border-emerald-200 bg-emerald-50/30'
              ]"
            >
              <div class="px-4 py-2 flex items-center gap-2 border-b border-[#E2E8F0] bg-white text-xs">
                <span class="text-base">{{ fb.rating === 'negative' ? '👎' : '👍' }}</span>
                <span class="text-[#64748B]">Iniciativa: <span class="font-semibold text-[#1E293B]">{{ fb.initiative_id || 'Prueba' }}</span></span>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#E2E8F0]">
                <div class="p-4">
                  <p class="text-[10px] font-bold text-[#64748B] uppercase tracking-wider mb-2">Usuario dijo</p>
                  <p class="text-sm text-[#1E293B]">{{ fb.user_message }}</p>
                </div>
                <div class="p-4">
                  <p class="text-[10px] font-bold text-[#64748B] uppercase tracking-wider mb-2">Agente respondió</p>
                  <p class="text-sm text-[#64748B]">{{ fb.agent_response }}</p>
                </div>
              </div>
              <!-- Si es negativo, permitir editar respuesta ideal -->
              <div v-if="fb.rating === 'negative'" class="px-4 py-3 bg-white border-t border-[#E2E8F0]">
                <p class="text-xs font-semibold text-[#64748B] mb-1.5">Respuesta ideal (edita antes de aprobar):</p>
                <textarea
                  v-model="feedbackEdits[fb.id]"
                  rows="3"
                  :placeholder="fb.agent_response"
                  class="w-full border border-[#E2E8F0] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#4F5AF5] resize-none"
                ></textarea>
              </div>
              <div class="flex gap-2 px-4 py-3 bg-white border-t border-[#E2E8F0] justify-end">
                <button
                  type="button"
                  @click="discardFeedback(fb.id)"
                  class="flex items-center gap-1.5 border border-[#E2E8F0] hover:bg-red-50 hover:border-red-200 text-[#64748B] hover:text-red-600 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer"
                >
                  <Trash2 class="w-3.5 h-3.5" />
                  <span>Descartar</span>
                </button>
                <button
                  type="button"
                  @click="approveFeedback(fb)"
                  :disabled="approvingFeedbackId === fb.id"
                  class="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors disabled:opacity-60 cursor-pointer"
                >
                  <Loader2 v-if="approvingFeedbackId === fb.id" class="w-3.5 h-3.5 animate-spin" />
                  <CheckCircle2 v-else class="w-3.5 h-3.5" />
                  <span>Aprobar como Ejemplo</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── PREVIEW CHAT DERECHO (Idéntico a AITraining.tsx) ── -->
    <div class="w-full lg:w-80 shrink-0 flex flex-col bg-white rounded-2xl shadow-sm border border-[#E2E8F0] overflow-hidden h-[680px]">
      <!-- Header degradado -->
      <div class="px-4 py-3 border-b border-[#E2E8F0] bg-gradient-to-r from-violet-600 to-[#4F5AF5] flex items-center justify-between">
        <div class="flex items-center gap-2 min-w-0">
          <div class="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center overflow-hidden shrink-0">
            <img v-if="aiAvatar" :src="aiAvatar" :alt="aiName" class="w-full h-full object-cover" />
            <Bot v-else class="w-3.5 h-3.5 text-white" />
          </div>
          <span class="text-xs font-semibold text-white truncate">{{ aiName }} (Prueba)</span>
        </div>
        <button
          type="button"
          @click="resetPreviewChat"
          title="Reiniciar chat"
          class="text-white/70 hover:text-white transition-colors cursor-pointer"
        >
          <RefreshCw class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- Banner de configuración activa -->
      <div class="px-3 py-2 bg-violet-50 border-b border-[#E2E8F0]">
        <p class="text-[10px] text-violet-700 font-semibold">Usa la configuración activa guardada</p>
      </div>

      <!-- Mensajes -->
      <div class="flex-1 overflow-y-auto p-3 space-y-3 bg-[#F8FAFC]">
        <div v-if="chatMessages.length === 0" class="text-center py-8 text-slate-400">
          <div class="w-10 h-10 rounded-full border border-slate-200 bg-white flex items-center justify-center mx-auto mb-2 overflow-hidden shrink-0 shadow-sm">
            <img v-if="aiAvatar" :src="aiAvatar" :alt="aiName" class="w-full h-full object-cover" />
            <Bot v-else class="w-5 h-5 text-slate-300" />
          </div>
          <p class="text-xs">Escribe algo para probar el agente con la configuración actual</p>
        </div>

        <div
          v-for="(msg, i) in chatMessages"
          :key="i"
          :class="['flex gap-2', msg.role === 'user' ? 'flex-row-reverse' : '']"
        >
          <div :class="[
            'w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-1 overflow-hidden',
            msg.role === 'model' ? 'bg-white border border-[#E2E8F0] shadow-sm' : 'bg-[#4F5AF5]'
          ]">
            <template v-if="msg.role === 'model'">
              <img v-if="aiAvatar" :src="aiAvatar" :alt="aiName" class="w-full h-full object-cover" />
              <Bot v-else class="w-3 h-3 text-[#4F5AF5]" />
            </template>
            <span v-else class="text-white text-[8px] font-bold">TU</span>
          </div>

          <div :class="[
            'px-3 py-2 rounded-xl text-xs leading-relaxed max-w-[calc(100%-2.5rem)] shadow-sm',
            msg.role === 'user' ? 'bg-[#4F5AF5] text-white rounded-tr-sm' : 'bg-white border border-[#E2E8F0] text-[#1E293B] rounded-tl-sm'
          ]">
            <p v-if="msg.role === 'user'" class="whitespace-pre-wrap">{{ msg.text }}</p>
            <div v-else class="prose prose-xs max-w-none text-[#1E293B] leading-relaxed break-words" v-html="formatMarkdown(msg.text)"></div>

            <!-- Opciones sugeridas -->
            <div v-if="msg.options && msg.options.length > 0 && i === chatMessages.length - 1" class="mt-2 pt-2 border-t border-slate-100 flex flex-col gap-1">
              <span class="text-[9px] font-semibold text-slate-400 uppercase tracking-wider">Sugerencias:</span>
              <div class="flex flex-wrap gap-1">
                <button
                  v-for="(opt, optIdx) in msg.options"
                  :key="optIdx"
                  type="button"
                  @click="sendPreviewMessage(opt)"
                  class="text-left text-[10px] bg-violet-50 hover:bg-violet-100 text-violet-700 px-2 py-1 rounded-md transition-colors border border-violet-100 font-medium cursor-pointer"
                >
                  {{ opt }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="chatLoading" class="flex gap-2">
          <div class="w-6 h-6 rounded-full bg-white border border-[#E2E8F0] flex items-center justify-center shrink-0 overflow-hidden shadow-sm">
            <img v-if="aiAvatar" :src="aiAvatar" :alt="aiName" class="w-full h-full object-cover" />
            <Bot v-else class="w-3 h-3 text-[#4F5AF5]" />
          </div>
          <div class="bg-white border border-[#E2E8F0] px-3 py-2 rounded-xl rounded-tl-sm flex gap-1">
            <span v-for="d in [0, 150, 300]" :key="d" class="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce" :style="{ animationDelay: `${d}ms` }" />
          </div>
        </div>
      </div>

      <!-- Barra de entrada inferior -->
      <div class="p-3 border-t border-[#E2E8F0] bg-white space-y-2">
        <!-- Preview de archivo adjunto -->
        <div v-if="attachedChatFile" class="flex items-center gap-2 bg-[#EEF2FF] border border-[#C7D2FE] rounded-lg px-2.5 py-1.5">
          <ImageIcon v-if="attachedChatFile.type === 'image'" class="w-3.5 h-3.5 text-[#4F5AF5] shrink-0" />
          <FileText v-else class="w-3.5 h-3.5 text-[#4F5AF5] shrink-0" />
          <span class="text-[10px] font-semibold text-[#4F5AF5] flex-1 truncate">{{ attachedChatFile.name }}</span>
          <span v-if="isProcessingFile" class="text-[10px] text-[#94A3B8] animate-pulse">...</span>
          <span v-else class="text-[10px] text-emerald-600 font-bold">✓</span>
          <button type="button" @click="removeChatAttachment" class="text-[#94A3B8] hover:text-red-500 cursor-pointer">
            <X class="w-3 h-3" />
          </button>
        </div>

        <!-- Barra de Grabación -->
        <div v-if="isRecording" class="flex items-center gap-2 bg-red-50 border border-red-200 rounded-lg px-2.5 py-1.5">
          <span class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
          <span class="text-[10px] font-semibold text-red-600">Grabando audio</span>
          <span class="text-[10px] text-red-500 font-mono">0:{{ String(recordingSeconds).padStart(2, '0') }}</span>
          <button type="button" @click="stopRecording" class="ml-auto text-red-400 hover:text-red-600 cursor-pointer">
            <X class="w-3 h-3" />
          </button>
        </div>

        <!-- Alertas de Error -->
        <div v-if="voiceError || attachError" class="flex items-center gap-2 bg-red-50 border border-red-200 rounded-lg px-2.5 py-1.5">
          <AlertCircle class="w-3 h-3 text-red-500 shrink-0" />
          <span class="text-[10px] text-red-600 flex-1">{{ voiceError || attachError }}</span>
          <button type="button" @click="voiceError = null; attachError = null" class="text-red-400 hover:text-red-600 cursor-pointer">
            <X class="w-3 h-3" />
          </button>
        </div>

        <!-- Formulario de Entrada -->
        <form @submit.prevent="sendPreviewMessage()" class="flex items-center gap-1.5">
          <input
            ref="chatFileInputRef"
            type="file"
            accept=".pdf,.docx,.txt,.jpg,.jpeg,.png,.webp"
            class="hidden"
            @change="handleChatFileAttach"
          />

          <!-- Botón Adjuntar Archivo -->
          <button
            v-if="useAttachments"
            type="button"
            @click="chatFileInputRef?.click()"
            :disabled="chatLoading || isProcessingFile"
            :class="[
              'w-8 h-8 rounded-lg border flex items-center justify-center shrink-0 transition-colors cursor-pointer',
              attachedChatFile ? 'border-[#4F5AF5] bg-[#EEF2FF] text-[#4F5AF5]' : 'border-[#E2E8F0] text-[#94A3B8] hover:text-[#4F5AF5] hover:bg-[#F8FAFC]'
            ]"
            title="Adjuntar archivo"
          >
            <Paperclip class="w-3.5 h-3.5" />
          </button>

          <!-- Input de Texto -->
          <input
            v-model="chatInput"
            :placeholder="isRecording ? '🎙️ Grabando audio...' : isProcessingFile ? 'Procesando archivo...' : 'Escribe un mensaje...'"
            :disabled="chatLoading || isRecording || isProcessingFile"
            :class="[
              'flex-1 border rounded-lg px-3 py-2 text-xs focus:outline-none transition-colors',
              isRecording ? 'border-red-300 bg-red-50' : 'border-[#E2E8F0] text-[#1E293B] placeholder-[#94A3B8] focus:ring-2 focus:ring-[#4F5AF5] focus:border-[#4F5AF5]'
            ]"
          />

          <!-- Botón de Micrófono -->
          <button
            v-if="useMic"
            type="button"
            @click="isRecording ? stopRecording() : startRecording()"
            :disabled="chatLoading"
            :class="[
              'relative w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-all cursor-pointer',
              isRecording ? 'bg-red-500 hover:bg-red-600 text-white shadow-sm shadow-red-200' : 'border border-[#E2E8F0] text-[#94A3B8] hover:text-[#4F5AF5] hover:bg-[#F8FAFC]'
            ]"
            :title="isRecording ? 'Detener grabación' : 'Grabar voz'"
          >
            <MicOff v-if="isRecording" class="w-3.5 h-3.5" />
            <Mic v-else class="w-3.5 h-3.5" />
          </button>

          <!-- Botón Enviar -->
          <button
            type="submit"
            :disabled="(!chatInput.trim() && !attachedChatFile) || chatLoading || isProcessingFile || isRecording"
            class="w-8 h-8 rounded-lg bg-[#4F5AF5] hover:bg-[#3F49E0] disabled:bg-[#E2E8F0] flex items-center justify-center text-white shrink-0 cursor-pointer"
          >
            <Send class="w-3.5 h-3.5" />
          </button>
        </form>

        <p class="text-[9px] text-[#94A3B8] text-center">
          <span v-if="useMic">🎙️ Voz local</span>
          <span v-if="useMic && useAttachments"> · </span>
          <span v-if="useAttachments">📎 PDF ({{ fileTypes.pdf.maxMb }} MB), DOCX ({{ fileTypes.docx.maxMb }} MB), TXT, imagen</span>
        </p>
      </div>
    </div>

    <!-- ── MODAL: CREAR / EDITAR CARPETA ── -->
    <div v-if="showFolderModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4 border border-[#E2E8F0]">
        <h3 class="font-bold text-base text-[#1E293B]">
          {{ folderModalMode === 'edit' ? 'Renombrar Carpeta' : folderParent ? `Nueva Subcarpeta en "${folderParent.name}"` : 'Nueva Carpeta Raíz' }}
        </h3>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Nombre de la carpeta</label>
          <input
            v-model="folderNameInput"
            @keyup.enter="handleSaveFolderSubmit"
            type="text"
            placeholder="Ej: Políticas de Ciberseguridad"
            class="w-full border border-slate-300 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-[#4F5AF5]"
          />
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showFolderModal = false" class="px-4 py-1.5 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 cursor-pointer">Cancelar</button>
          <button @click="handleSaveFolderSubmit" :disabled="saving" class="px-4 py-1.5 rounded-xl text-xs font-bold text-white bg-[#4F5AF5] hover:bg-indigo-600 cursor-pointer">Guardar</button>
        </div>
      </div>
    </div>

    <!-- ── MODAL: ELIMINAR CARPETA ── -->
    <div v-if="showDeleteFolderModal && deletingFolder" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4 border border-[#E2E8F0]">
        <h3 class="font-bold text-base text-rose-600">Eliminar Carpeta</h3>
        <p class="text-xs text-slate-600">¿Estás seguro de que deseas eliminar la carpeta <strong>"{{ deletingFolder.name }}"</strong>?</p>
        <div class="space-y-2 text-xs">
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="radio" :value="false" v-model="deleteFolderWithItems" />
            <span>Conservar fichas (mover a la Raíz)</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer text-rose-600">
            <input type="radio" :value="true" v-model="deleteFolderWithItems" />
            <span>Eliminar carpeta y todas sus fichas</span>
          </label>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showDeleteFolderModal = false" class="px-4 py-1.5 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 cursor-pointer">Cancelar</button>
          <button @click="handleConfirmDeleteFolder" :disabled="saving" class="px-4 py-1.5 rounded-xl text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 cursor-pointer">Sí, eliminar</button>
        </div>
      </div>
    </div>

    <!-- ── MODAL: MOVER FICHA A OTRA CARPETA ── -->
    <div v-if="showMoveEntryModal && movingEntry" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4 border border-[#E2E8F0]">
        <h3 class="font-bold text-base text-[#1E293B]">Mover Ficha a Carpeta</h3>
        <p class="text-xs text-slate-500">"{{ movingEntry.title }}"</p>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Selecciona la carpeta de destino:</label>
          <select
            v-model="targetFolderIdForMove"
            class="w-full border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]"
          >
            <option value="">📂 Sin carpeta (Raíz / General)</option>
            <option v-for="f in flattenedFolderOptions" :key="f.id" :value="f.id">
              {{ '  '.repeat(f.level - 1) + (f.level > 1 ? '↳ ' : '') + `📁 ${f.name} (Nivel ${f.level})` }}
            </option>
          </select>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showMoveEntryModal = false" class="px-4 py-1.5 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 cursor-pointer">Cancelar</button>
          <button @click="confirmMoveEntry" class="px-4 py-1.5 rounded-xl text-xs font-bold text-white bg-[#4F5AF5] hover:bg-indigo-600 cursor-pointer">Mover Ficha</button>
        </div>
      </div>
    </div>

    <!-- ── MODAL: PRELIMINAR DE FICHAS EXTRAÍDAS ── -->
    <div v-if="showUploadModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden border border-[#E2E8F0]">
        <div class="px-6 py-4 border-b border-[#E2E8F0] flex items-center justify-between">
          <div>
            <h3 class="font-bold text-base text-[#1E293B]">Preliminar de Fichas Extraídas</h3>
            <p class="text-xs text-[#64748B]">Revisa el contenido antes de integrarlo a la Base de Conocimiento.</p>
          </div>
          <button @click="showUploadModal = false" class="text-slate-400 hover:text-slate-600 cursor-pointer">
            <X class="w-5 h-5" />
          </button>
        </div>

        <div class="mx-6 mt-4 p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between gap-4">
          <span class="text-xs font-semibold text-slate-700">Carpeta de destino:</span>
          <select
            v-model="uploadTargetFolderId"
            class="bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-800"
          >
            <option value="">📂 Sin carpeta (Raíz / General)</option>
            <option v-for="f in flattenedFolderOptions" :key="f.id" :value="f.id">
              {{ '  '.repeat(f.level - 1) + (f.level > 1 ? '↳ ' : '') + `📁 ${f.name} (Nivel ${f.level})` }}
            </option>
          </select>
        </div>

        <div class="flex-1 overflow-y-auto p-6 space-y-4">
          <div
            v-for="(chunk, idx) in extractedChunks"
            :key="idx"
            class="border border-[#E2E8F0] rounded-xl p-4 space-y-2 bg-white shadow-2xs"
          >
            <div class="flex items-center justify-between">
              <h4 class="font-bold text-sm text-[#1E293B]">{{ chunk.title }}</h4>
              <button
                type="button"
                @click="approveChunk(chunk)"
                class="flex items-center gap-1 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 px-3 py-1.5 rounded-lg cursor-pointer"
              >
                <Check class="w-3.5 h-3.5" />
                <span>Agregar</span>
              </button>
            </div>
            <p class="text-xs text-slate-600 leading-relaxed whitespace-pre-wrap">{{ chunk.content }}</p>
          </div>
        </div>

        <div class="px-6 py-3 border-t border-[#E2E8F0] bg-slate-50 flex items-center justify-between">
          <span class="text-xs text-slate-500">{{ extractedChunks.length }} fichas pendientes</span>
          <div class="flex gap-2">
            <button
              v-if="extractedChunks.length > 1"
              type="button"
              @click="approveAllChunks"
              class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-1.5 rounded-lg text-xs font-bold cursor-pointer"
            >
              Agregar todas ({{ extractedChunks.length }})
            </button>
            <button
              type="button"
              @click="showUploadModal = false"
              class="border border-slate-300 bg-white text-slate-700 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
