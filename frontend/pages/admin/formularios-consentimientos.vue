<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 tracking-tight">Formularios y consentimientos</h1>
        <p class="text-xs sm:text-sm text-slate-500 mt-1">
          Administra formularios dinámicos, términos legales y plantillas oficiales
        </p>
      </div>
      <div>
        <button
          v-if="activeTab === 'forms'"
          @click="handleOpenNewForm"
          class="inline-flex items-center gap-2 px-4 py-2 text-xs sm:text-sm font-semibold text-white bg-[#4F5AF5] hover:bg-indigo-600 rounded-xl transition-all shadow-sm cursor-pointer"
        >
          <Plus class="w-4 h-4" />
          <span>+ Nuevo formulario</span>
        </button>
        <button
          v-else-if="activeTab === 'consents'"
          @click="handleOpenNewConsent"
          class="inline-flex items-center gap-2 px-4 py-2 text-xs sm:text-sm font-semibold text-white bg-[#4F5AF5] hover:bg-indigo-600 rounded-xl transition-all shadow-sm cursor-pointer"
        >
          <Plus class="w-4 h-4" />
          <span>+ Nuevo consentimiento</span>
        </button>
        <button
          v-else
          @click="openNewTemplateModal"
          class="inline-flex items-center gap-2 px-4 py-2 text-xs sm:text-sm font-semibold text-white bg-[#4F5AF5] hover:bg-indigo-600 rounded-xl transition-all shadow-sm cursor-pointer"
        >
          <Plus class="w-4 h-4" />
          <span>+ Nueva plantilla</span>
        </button>
      </div>
    </div>

    <!-- Tabs Navigation -->
    <div class="flex border-b border-slate-200 space-x-8">
      <button
        type="button"
        @click="activeTab = 'forms'"
        :class="[
          'pb-3 text-sm font-bold flex items-center gap-2 border-b-2 transition-colors cursor-pointer',
          activeTab === 'forms'
            ? 'border-[#4F5AF5] text-[#4F5AF5]'
            : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
        ]"
      >
        <FileCheck2 class="w-4 h-4" />
        <span>Formularios de Etapa ({{ forms.length }})</span>
      </button>

      <button
        type="button"
        @click="activeTab = 'consents'"
        :class="[
          'pb-3 text-sm font-bold flex items-center gap-2 border-b-2 transition-colors cursor-pointer',
          activeTab === 'consents'
            ? 'border-[#4F5AF5] text-[#4F5AF5]'
            : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
        ]"
      >
        <ShieldCheck class="w-4 h-4" />
        <span>Consentimientos & Declaraciones ({{ consents.length }})</span>
      </button>

      <button
        type="button"
        @click="activeTab = 'documents'"
        :class="[
          'pb-3 text-sm font-bold flex items-center gap-2 border-b-2 transition-colors cursor-pointer',
          activeTab === 'documents'
            ? 'border-[#4F5AF5] text-[#4F5AF5]'
            : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
        ]"
      >
        <FileText class="w-4 h-4" />
        <span>Generador de documentos ({{ templates.length }})</span>
      </button>
    </div>

    <!-- Controls: Search & Filter (Matching original WorkflowCatalogManager) -->
    <div class="bg-white p-3 rounded-2xl border border-slate-200 shadow-xs flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
      <!-- Search Input -->
      <div class="relative w-full sm:w-80">
        <Search class="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="
            activeTab === 'forms'
              ? 'Buscar formulario por nombre, código...'
              : activeTab === 'consents'
              ? 'Buscar consentimiento...'
              : 'Buscar formato PDF por nombre, código...'
          "
          class="w-full pl-9 pr-8 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
        />
        <button
          v-if="searchQuery"
          type="button"
          @click="searchQuery = ''"
          class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
        >
          <X class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- Filters & Sort -->
      <div class="flex flex-wrap items-center gap-2.5 w-full sm:w-auto justify-end">
        <!-- Stage Filter (for forms & consents) -->
        <div v-if="activeTab !== 'documents'" class="flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl text-xs">
          <Workflow class="w-3.5 h-3.5 text-[#4F5AF5] shrink-0" />
          <select
            v-model="selectedStageFilter"
            class="bg-transparent text-slate-800 font-semibold focus:outline-none cursor-pointer pr-1 text-xs"
          >
            <option value="all">Todas las etapas</option>
            <option v-for="st in STAGES_LIST" :key="st.key" :value="st.key">
              {{ st.label }}
            </option>
          </select>
        </div>

        <!-- Sort Selector -->
        <div class="flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl text-xs">
          <ArrowUpDown class="w-3.5 h-3.5 text-[#4F5AF5] shrink-0" />
          <span class="text-slate-500 font-medium">Ordenar:</span>
          <select
            v-model="sortOrder"
            class="bg-transparent text-slate-800 font-bold focus:outline-none cursor-pointer pr-1 text-xs"
          >
            <option value="workflow_asc">⚡ Secuencia del Flujo (Borrador ➔ Fin)</option>
            <option value="workflow_desc">🔄 Secuencia del Flujo (Fin ➔ Borrador)</option>
            <option value="name_asc">🔤 Nombre (A ➔ Z)</option>
            <option value="name_desc">🔤 Nombre (Z ➔ A)</option>
            <option v-if="activeTab === 'forms'" value="fields_count">📊 Cantidad de campos</option>
          </select>
        </div>

        <!-- Status Filter Buttons -->
        <div class="flex items-center gap-1.5">
          <span class="text-xs font-semibold text-slate-400">Estado:</span>
          <div class="flex bg-slate-100 p-0.5 rounded-xl text-xs font-semibold">
            <button
              type="button"
              @click="statusFilter = 'all'"
              :class="[
                'px-3 py-1.5 rounded-lg transition-colors cursor-pointer',
                statusFilter === 'all' ? 'bg-white text-slate-800 shadow-xs' : 'text-slate-500 hover:text-slate-700'
              ]"
            >
              Todos
            </button>
            <button
              type="button"
              @click="statusFilter = 'active'"
              :class="[
                'px-3 py-1.5 rounded-lg transition-colors cursor-pointer',
                statusFilter === 'active' ? 'bg-white text-emerald-700 shadow-xs' : 'text-slate-500 hover:text-slate-700'
              ]"
            >
              Activos
            </button>
            <button
              type="button"
              @click="statusFilter = 'inactive'"
              :class="[
                'px-3 py-1.5 rounded-lg transition-colors cursor-pointer',
                statusFilter === 'inactive' ? 'bg-white text-slate-700 shadow-xs' : 'text-slate-500 hover:text-slate-700'
              ]"
            >
              Inactivos
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 1: FORMULARIOS DE ETAPA (Cards Grid matching original) -->
    <div v-if="activeTab === 'forms'">
      <div v-if="isLoading" class="py-16 text-center text-slate-400 text-xs">
        Cargando formularios...
      </div>

      <div v-else-if="filteredForms.length === 0" class="py-16 text-center bg-white rounded-2xl border border-dashed border-slate-200 p-8">
        <FileCheck2 class="w-10 h-10 text-slate-300 mx-auto mb-3" />
        <p class="text-sm font-bold text-slate-700">No se encontraron formularios</p>
        <p class="text-xs text-slate-400 mt-1">Prueba ajustando los filtros de búsqueda o etapa.</p>
        <button
          type="button"
          @click="handleOpenNewForm"
          class="mt-4 inline-flex items-center gap-1.5 px-4 py-2 bg-[#4F5AF5] hover:bg-indigo-600 text-white rounded-xl text-xs font-bold transition-colors cursor-pointer"
        >
          <Plus class="w-3.5 h-3.5" />
          <span>Crear Formulario</span>
        </button>
      </div>

      <!-- 3-Column Grid Matching WorkflowCatalogManager -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="form in filteredForms"
          :key="form.id"
          class="bg-white rounded-2xl border border-slate-200 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between overflow-hidden group"
        >
          <!-- Card Top Content -->
          <div class="p-5 space-y-3">
            <!-- Stage Tag, Code & Status -->
            <div class="flex items-center justify-between gap-2">
              <div class="flex items-center gap-2 min-w-0 flex-wrap">
                <span
                  v-if="getAssociatedNodesForForm(form.id, form.code).length > 0"
                  class="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-md bg-indigo-50 text-[#4F5AF5] border border-indigo-200 shrink-0"
                >
                  Etapa {{ getAssociatedNodesForForm(form.id, form.code)[0].data?.label?.split('.')[0]?.trim() || getStageShortTag(form.stage_id) }}
                </span>
                <span
                  v-else
                  class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-slate-50 text-slate-500 border border-slate-200 shrink-0"
                >
                  ETAPA
                </span>
                <span class="text-[11px] font-mono font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200 truncate" :title="form.code">
                  {{ form.code }}
                </span>
              </div>

              <div class="flex items-center gap-1.5 shrink-0">
                <span
                  class="text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 border"
                  :class="form.is_active ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-500 border-slate-200'"
                >
                  <span class="w-1.5 h-1.5 rounded-full" :class="form.is_active ? 'bg-emerald-500' : 'bg-slate-400'"></span>
                  {{ form.is_active ? 'Activo' : 'Inactivo' }}
                </span>

                <!-- Action Buttons matching original WorkflowCatalogManager -->
                <div class="flex items-center gap-1">
                  <button
                    type="button"
                    @click="openLivePreview(form)"
                    title="Vista previa del formulario"
                    class="p-1.5 text-slate-400 hover:text-[#4F5AF5] hover:bg-indigo-50 rounded-lg transition-colors cursor-pointer"
                  >
                    <Eye class="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    @click="handleDuplicateForm(form)"
                    title="Duplicar formulario"
                    class="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                  >
                    <Copy class="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    @click="handleEditForm(form)"
                    title="Editar formulario"
                    class="p-1.5 text-slate-400 hover:text-[#4F5AF5] hover:bg-indigo-50 rounded-lg transition-colors cursor-pointer"
                  >
                    <Edit3 class="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    @click="handleDeleteForm(form)"
                    title="Eliminar formulario"
                    class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                  >
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            <!-- Title & Description -->
            <div>
              <h3 class="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors line-clamp-1" :title="form.name">
                {{ form.name }}
              </h3>
              <p class="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed" :title="form.description">
                {{ form.description || 'Sin descripción detallada proporcionada.' }}
              </p>
            </div>

            <!-- Pills Info: Configured Fields & Associated Stage -->
            <div class="pt-2 flex flex-wrap items-center gap-2">
              <span class="text-[11px] font-semibold text-slate-600 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-lg flex items-center gap-1.5">
                <Sliders class="w-3 h-3 text-slate-400" />
                <span>{{ (form.fields || []).length }} {{ (form.fields || []).length === 1 ? 'campo configurado' : 'campos configurados' }}</span>
              </span>

              <span class="text-[11px] font-semibold text-slate-600 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-lg flex items-center gap-1.5">
                <Workflow class="w-3 h-3 text-slate-400" />
                <span v-if="getAssociatedNodesForForm(form.id, form.code).length > 0" class="truncate max-w-[140px]">
                  Asociado a: {{ getAssociatedNodesForForm(form.id, form.code)[0].data?.label || getAssociatedNodesForForm(form.id, form.code)[0].id }}
                </span>
                <span v-else class="text-slate-400 italic">
                  Asociado a: Sin asociar
                </span>
              </span>
            </div>
          </div>

          <!-- Card Bottom Action Bar -->
          <div class="px-5 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
            <button
              type="button"
              @click="openLivePreview(form)"
              class="text-xs font-bold text-indigo-600 hover:text-indigo-800 transition-colors flex items-center gap-1 cursor-pointer"
            >
              <span>Probar en vivo</span>
              <ChevronRight class="w-3.5 h-3.5" />
            </button>

            <button
              type="button"
              @click="handleEditForm(form)"
              class="text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-xl transition-all shadow-2xs flex items-center gap-1.5 cursor-pointer"
            >
              <Sliders class="w-3 h-3 text-slate-500" />
              <span>Configurar campos</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: CONSENTIMIENTOS & DECLARACIONES -->
    <div v-else-if="activeTab === 'consents'">
      <div v-if="isLoading" class="py-16 text-center text-slate-400 text-xs">
        Cargando consentimientos...
      </div>

      <div v-else-if="filteredConsents.length === 0" class="py-16 text-center bg-white rounded-2xl border border-dashed border-slate-200 p-8">
        <ShieldCheck class="w-10 h-10 text-slate-300 mx-auto mb-3" />
        <p class="text-sm font-bold text-slate-700">No se encontraron declaraciones o consentimientos</p>
        <button
          type="button"
          @click="handleOpenNewConsent"
          class="mt-4 inline-flex items-center gap-1.5 px-4 py-2 bg-[#4F5AF5] hover:bg-indigo-600 text-white rounded-xl text-xs font-bold transition-colors cursor-pointer"
        >
          <Plus class="w-3.5 h-3.5" />
          <span>Crear Consentimiento</span>
        </button>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="consent in filteredConsents"
          :key="consent.id"
          class="bg-white rounded-2xl border border-slate-200 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between overflow-hidden"
        >
          <div class="p-5 space-y-3">
            <div class="flex items-center justify-between gap-2">
              <div class="flex items-center gap-2 min-w-0 flex-wrap">
                <span
                  v-if="getAssociatedNodesForConsent(consent.id, consent.code).length > 0"
                  class="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-md bg-indigo-50 text-[#4F5AF5] border border-indigo-200 shrink-0"
                >
                  Etapa {{ getAssociatedNodesForConsent(consent.id, consent.code)[0].data?.label?.split('.')[0]?.trim() || getStageShortTag(consent.stage_id) }}
                </span>
                <span
                  v-else
                  class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200 shrink-0"
                >
                  {{ getStageShortTag(consent.stage_id) }}
                </span>
                <span class="text-[11px] font-mono font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200">
                  {{ consent.code }}
                </span>
                <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100 font-bold">
                  v{{ consent.version || 1 }}
                </span>
                <span
                  class="text-[10px] font-bold px-2 py-0.5 rounded-full border"
                  :class="consent.is_active ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-500 border-slate-200'"
                >
                  {{ consent.is_active ? 'Activo' : 'Inactivo' }}
                </span>
              </div>

              <!-- Action buttons for consent -->
              <div class="flex items-center gap-1 shrink-0">
                <button
                  type="button"
                  @click="openLiveConsentPreview(consent)"
                  title="Vista previa del consentimiento"
                  class="p-1.5 text-slate-400 hover:text-[#4F5AF5] hover:bg-indigo-50 rounded-lg transition-colors cursor-pointer"
                >
                  <Eye class="w-4 h-4" />
                </button>
                <button
                  type="button"
                  @click="handleDuplicateConsent(consent)"
                  title="Duplicar consentimiento"
                  class="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                >
                  <Copy class="w-4 h-4" />
                </button>
                <button
                  type="button"
                  @click="handleEditConsent(consent)"
                  title="Editar consentimiento"
                  class="p-1.5 text-slate-400 hover:text-[#4F5AF5] hover:bg-indigo-50 rounded-lg transition-colors cursor-pointer"
                >
                  <Edit3 class="w-4 h-4" />
                </button>
                <button
                  type="button"
                  @click="handleDeleteConsent(consent)"
                  title="Eliminar consentimiento"
                  class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                >
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </div>

            <div>
              <h3 class="text-sm font-bold text-slate-900 line-clamp-1" :title="consent.title">
                {{ consent.title }}
              </h3>
              <p class="text-xs text-slate-500 font-mono mt-0.5">{{ consent.code }}</p>
            </div>

            <!-- Legal statement preview -->
            <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <p class="text-[11px] text-slate-700 italic line-clamp-3 leading-relaxed">
                "{{ consent.statement }}"
              </p>
            </div>

            <!-- Associated State in Workflow -->
            <div class="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px]">
              <span class="font-semibold text-slate-500 flex items-center gap-1">
                <Workflow class="w-3.5 h-3.5 text-[#4F5AF5]" />
                <span>Asociado a:</span>
              </span>
              <div v-if="getAssociatedNodesForConsent(consent.id, consent.code).length > 0" class="flex flex-wrap gap-1 justify-end max-w-[65%]">
                <span
                  v-for="n in getAssociatedNodesForConsent(consent.id, consent.code)"
                  :key="n.id"
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200"
                >
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                  <span class="truncate max-w-[130px]">{{ n.data?.label || n.id }}</span>
                </span>
              </div>
              <span v-else class="text-[10px] text-slate-400 italic">
                Sin asociar
              </span>
            </div>
          </div>

          <div class="px-5 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
            <button
              type="button"
              @click="openLiveConsentPreview(consent)"
              class="text-xs font-bold text-indigo-600 hover:text-indigo-800 transition-colors flex items-center gap-1 cursor-pointer"
            >
              <span>Probar consentimiento</span>
              <ChevronRight class="w-3.5 h-3.5" />
            </button>

            <button
              type="button"
              @click="handleEditConsent(consent)"
              class="text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-xl transition-all shadow-2xs cursor-pointer"
            >
              Editar texto legal
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 3: GENERADOR DE DOCUMENTOS -->
    <div v-else-if="activeTab === 'documents'">
      <div v-if="isLoading" class="py-16 text-center text-slate-400 text-xs">
        Cargando plantillas...
      </div>

      <div v-else-if="filteredDocuments.length === 0" class="py-16 text-center bg-white rounded-2xl border border-dashed border-slate-200 p-8">
        <FileText class="w-10 h-10 text-slate-300 mx-auto mb-3" />
        <p class="text-sm font-bold text-slate-700">No se encontraron formatos de documentos PDF</p>
        <p class="text-xs text-slate-400 mt-1">Prueba ajustando los criterios de búsqueda o estado.</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div
          v-for="tpl in filteredDocuments"
          :key="tpl.id"
          class="bg-white rounded-2xl border border-slate-200 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between overflow-hidden"
        >
          <div class="p-6 space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200 font-mono">
                  {{ tpl.code }}
                </span>
                <span
                  class="text-[10px] font-bold px-2 py-0.5 rounded-full border"
                  :class="tpl.is_active ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-500 border-slate-200'"
                >
                  {{ tpl.is_active ? 'Activo' : 'Inactivo' }}
                </span>
              </div>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                PDF Oficial
              </span>
            </div>

            <div>
              <h3 class="text-base font-bold text-slate-900">{{ tpl.name }}</h3>
              <p class="text-xs text-slate-500 mt-1 leading-relaxed">{{ tpl.description }}</p>
            </div>

            <!-- Associated State in Workflow -->
            <div class="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <span class="font-semibold text-slate-700 text-[11px]">Etapas vinculadas:</span>
              <div v-if="getAssociatedNodesForDocument(tpl.id, tpl.code).length > 0" class="flex flex-wrap gap-1 justify-end max-w-[65%]">
                <span
                  v-for="n in getAssociatedNodesForDocument(tpl.id, tpl.code)"
                  :key="n.id"
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200"
                >
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                  <span class="truncate max-w-[130px]">{{ n.data?.label || n.id }}</span>
                </span>
              </div>
              <span v-else class="text-[10px] text-slate-400 italic">Sin vincular</span>
            </div>
          </div>

          <div class="px-6 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
            <button
              type="button"
              @click="openPdfPreview(tpl)"
              class="text-xs font-bold text-indigo-600 hover:text-indigo-800 transition-colors flex items-center gap-1 cursor-pointer"
            >
              <span>Generar vista previa</span>
              <ChevronRight class="w-3.5 h-3.5" />
            </button>

            <button
              type="button"
              @click="openTemplateEditor(tpl)"
              class="text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-xl transition-all shadow-2xs cursor-pointer"
            >
              Editar plantilla HTML
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL 1: PROBAR EN VIVO (Live Form Preview) -->
    <div v-if="showLivePreviewModal && activePreviewForm" class="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
        <!-- Header -->
        <div class="px-6 py-4 bg-gradient-to-r from-slate-900 to-indigo-950 text-white flex items-center justify-between shrink-0">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-indigo-300">
              <Eye class="w-4 h-4" />
            </div>
            <div>
              <h3 class="text-sm font-bold text-white">{{ activePreviewForm.name }}</h3>
              <p class="text-[11px] text-indigo-200/70">Simulador interactivo de captura para validación funcional</p>
            </div>
          </div>
          <button @click="showLivePreviewModal = false" class="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors cursor-pointer">
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Body: Interactive Form Fields -->
        <div class="p-6 overflow-y-auto space-y-4 flex-1">
          <div class="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-800 flex items-center gap-2">
            <Info class="w-4 h-4 text-blue-600 shrink-0" />
            <span>Los campos marcados con asterisco (*) son obligatorios según las reglas de negocio de esta etapa.</span>
          </div>

          <div v-if="!activePreviewForm.fields || activePreviewForm.fields.length === 0" class="text-center py-8 text-xs text-slate-400">
            No hay campos configurados en este formulario.
          </div>

          <div v-else class="space-y-4">
            <div
              v-for="field in activePreviewForm.fields"
              :key="field.id || field.key"
              class="space-y-1"
            >
              <!-- Info Banner -->
              <div v-if="field.type === 'info_banner'" class="p-3 bg-indigo-50 border border-indigo-200 rounded-xl text-xs text-indigo-900 font-medium">
                {{ field.label }}
              </div>

              <!-- Other Fields -->
              <template v-else>
                <label class="block text-xs font-bold text-slate-700">
                  {{ field.label }}
                  <span v-if="field.required" class="text-red-500">*</span>
                </label>

                <!-- Text Input -->
                <input
                  v-if="field.type === 'text'"
                  v-model="liveFormData[field.key || field.id]"
                  type="text"
                  :placeholder="field.placeholder || 'Ingrese valor...'"
                  class="w-full text-xs rounded-xl border border-slate-200 px-3 py-2 focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
                />

                <!-- Textarea -->
                <textarea
                  v-else-if="field.type === 'textarea'"
                  v-model="liveFormData[field.key || field.id]"
                  rows="3"
                  :placeholder="field.placeholder || 'Escriba aquí...'"
                  class="w-full text-xs rounded-xl border border-slate-200 px-3 py-2 focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
                ></textarea>

                <!-- Number / Presupuesto -->
                <input
                  v-else-if="field.type === 'number'"
                  v-model="liveFormData[field.key || field.id]"
                  type="number"
                  :placeholder="field.placeholder || '0.00'"
                  class="w-full text-xs rounded-xl border border-slate-200 px-3 py-2 focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
                />

                <!-- Date -->
                <input
                  v-else-if="field.type === 'date'"
                  v-model="liveFormData[field.key || field.id]"
                  type="date"
                  class="w-full text-xs rounded-xl border border-slate-200 px-3 py-2 focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
                />

                <!-- Select (Simple) -->
                <select
                  v-else-if="field.type === 'select' && !field.allow_multiple"
                  v-model="liveFormData[field.key || field.id]"
                  class="w-full text-xs rounded-xl border border-slate-200 px-3 py-2 focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
                >
                  <option value="" disabled>Seleccione una opción...</option>
                  <option v-for="opt in (field.options || [])" :key="opt" :value="opt">
                    {{ opt }}
                  </option>
                </select>

                <!-- MultiSelect / Chips -->
                <div v-else-if="field.type === 'multiselect' || field.allow_multiple" class="space-y-1.5">
                  <div class="flex flex-wrap gap-1.5">
                    <button
                      v-for="opt in (field.options || [])"
                      :key="opt"
                      type="button"
                      @click="toggleMultiSelect(field.key || field.id, opt)"
                      :class="[
                        'px-2.5 py-1 text-xs rounded-lg border font-medium transition-colors cursor-pointer',
                        (liveFormData[field.key || field.id] || []).includes(opt)
                          ? 'bg-[#4F5AF5] text-white border-[#4F5AF5]'
                          : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                      ]"
                    >
                      {{ opt }}
                    </button>
                  </div>
                </div>

                <!-- Checkbox -->
                <label v-else-if="field.type === 'checkbox'" class="flex items-center gap-2 pt-1 cursor-pointer">
                  <input
                    type="checkbox"
                    v-model="liveFormData[field.key || field.id]"
                    class="rounded text-[#4F5AF5] focus:ring-[#4F5AF5]"
                  />
                  <span class="text-xs text-slate-700">{{ field.placeholder || 'Marque para confirmar' }}</span>
                </label>

                <!-- File -->
                <div v-else-if="field.type === 'file'" class="p-3 border border-dashed border-slate-300 rounded-xl text-center bg-slate-50">
                  <Paperclip class="w-5 h-5 text-slate-400 mx-auto mb-1" />
                  <p class="text-xs text-slate-600 font-medium">Adjuntar archivos autorizados</p>
                  <p class="text-[10px] text-slate-400 mt-0.5">Máximo 25 MB por archivo</p>
                </div>

                <!-- Role User -->
                <div v-else-if="field.type === 'role_user'" class="space-y-1">
                  <div class="text-[11px] text-slate-500 font-medium flex items-center gap-1">
                    <UserCheck class="w-3.5 h-3.5 text-indigo-600" />
                    <span>Rol requerido: {{ field.target_role || 'bp_ti' }}</span>
                  </div>
                  <input
                    v-model="liveFormData[field.key || field.id]"
                    type="text"
                    placeholder="Nombre del usuario asignado..."
                    class="w-full text-xs rounded-xl border border-slate-200 px-3 py-2 focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
                  />
                </div>

                <!-- Fallback Text -->
                <input
                  v-else
                  v-model="liveFormData[field.key || field.id]"
                  type="text"
                  :placeholder="field.placeholder || 'Ingrese valor...'"
                  class="w-full text-xs rounded-xl border border-slate-200 px-3 py-2 focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
                />

                <!-- Help Text -->
                <p v-if="field.helpText || field.help_text" class="text-[10px] text-slate-400">
                  {{ field.helpText || field.help_text }}
                </p>
              </template>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-6 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between shrink-0">
          <button
            type="button"
            @click="liveFormData = {}"
            class="text-xs text-slate-500 hover:text-slate-800 font-semibold cursor-pointer"
          >
            Limpiar datos
          </button>

          <div class="flex items-center gap-2">
            <button
              type="button"
              @click="testValidateForm"
              class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-colors cursor-pointer"
            >
              Probar Validación
            </button>
            <button
              type="button"
              @click="showLivePreviewModal = false"
              class="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-semibold rounded-xl transition-colors cursor-pointer"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════════════ -->
    <!-- ── FORM DRAWER (BUILDER) ───────────────────────────────────────────── -->
    <!-- ═══════════════════════════════════════════════════════════════════════ -->
    <div
      v-if="isFormDrawerOpen && editingForm"
      class="fixed inset-0 z-[9999] overflow-hidden bg-slate-900/50 backdrop-blur-xs flex justify-end"
    >
      <div class="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
        <!-- Header -->
        <div class="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50/70 shrink-0">
          <div class="flex items-center gap-2.5">
            <div class="w-9 h-9 rounded-xl bg-rose-50 text-rose-500 border border-rose-100 flex items-center justify-center font-bold">
              <FileCheck2 class="w-5 h-5 stroke-[2.2]" />
            </div>
            <div>
              <h2 class="text-base font-bold text-slate-900">
                {{ editingForm.id ? 'Editar Formulario de Etapa' : 'Nuevo Formulario de Etapa' }}
              </h2>
              <p class="text-xs text-slate-500">
                Define los campos que el responsable de etapa debe completar formalmente.
              </p>
            </div>
          </div>
          <button
            type="button"
            @click="isFormDrawerOpen = false; editingForm = null"
            class="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-y-auto p-6 space-y-6">
          <!-- Estado Asociado en Flujo Oficial Banner -->
          <div class="p-3.5 bg-gradient-to-r from-indigo-50/90 to-blue-50/70 border border-indigo-200/90 rounded-2xl space-y-1.5 shadow-2xs">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-indigo-950 flex items-center gap-1.5">
                <Workflow class="w-4 h-4 text-[#4F5AF5]" />
                <span>Asociación en el Flujo Oficial (IACS)</span>
              </span>
              <span class="text-[10px] font-bold text-indigo-700 bg-white px-2 py-0.5 rounded-full border border-indigo-200">
                {{ getAssociatedNodesForForm(editingForm.id, editingForm.code).length > 0 ? `${getAssociatedNodesForForm(editingForm.id, editingForm.code).length} ${getAssociatedNodesForForm(editingForm.id, editingForm.code).length === 1 ? 'estado asignado' : 'estados asignados'}` : 'Sin asignación' }}
              </span>
            </div>
            <div v-if="getAssociatedNodesForForm(editingForm.id, editingForm.code).length > 0" class="flex flex-wrap gap-1.5 pt-1">
              <span
                v-for="n in getAssociatedNodesForForm(editingForm.id, editingForm.code)"
                :key="n.id"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold bg-white text-indigo-900 border border-indigo-200 shadow-2xs"
              >
                <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>{{ n.data?.label || n.id }}</span>
                <span class="text-[10px] font-mono text-slate-400">({{ n.id }})</span>
              </span>
            </div>
            <p v-else class="text-xs text-slate-500 leading-relaxed">
              Este formulario no está asignado a ningún estado actualmente. Puedes asignarlo desde el
              <NuxtLink to="/admin/workflow-editor" class="text-indigo-600 font-bold hover:underline" target="_blank">
                Editor de Flujos
              </NuxtLink>
              (Pestaña <em>Dictamen</em> de la tarjeta deseada).
            </p>
          </div>

          <!-- Form Metadata -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Código Identificador <span class="text-rose-500">*</span>
              </label>
              <input
                type="text"
                placeholder="ej: form_bp_viabilidad"
                v-model="editingForm.code"
                class="w-full px-3.5 py-2 text-xs sm:text-sm font-mono bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5] focus:outline-none"
              />
              <p class="text-[10px] text-slate-400 mt-1">Identificador único en minúsculas y sin espacios.</p>
            </div>

            <div>
              <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Estado del Formulario
              </label>
              <div class="flex items-center gap-2 pt-1.5">
                <input
                  type="checkbox"
                  id="form_is_active"
                  v-model="editingForm.is_active"
                  class="w-4 h-4 rounded-md text-[#4F5AF5] focus:ring-[#4F5AF5] cursor-pointer"
                />
                <label for="form_is_active" class="text-xs font-semibold text-slate-700 cursor-pointer">
                  Activo para asociar en flujos
                </label>
              </div>
            </div>

            <div class="sm:col-span-2">
              <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Nombre del Formulario <span class="text-rose-500">*</span>
              </label>
              <input
                type="text"
                placeholder="ej: Evaluación y Viabilidad Técnica (BP TI)"
                v-model="editingForm.name"
                class="w-full px-3.5 py-2 text-xs sm:text-sm bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5] focus:outline-none font-semibold text-slate-800"
              />
            </div>

            <div class="sm:col-span-2">
              <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Descripción / Propósito
              </label>
              <textarea
                rows="2"
                placeholder="Explica a los evaluadores el objetivo de esta ficha técnica..."
                v-model="editingForm.description"
                class="w-full px-3.5 py-2 text-xs sm:text-sm bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5] focus:outline-none"
              ></textarea>
            </div>
          </div>

          <!-- Dynamic Field Builder -->
          <div class="border-t border-slate-200 pt-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-sm font-black text-slate-900 flex items-center gap-2">
                  <Sliders class="w-4 h-4 text-rose-500" />
                  <span>Campos de Dictamen ({{ (editingForm.fields || []).length }})</span>
                </h3>
                <p class="text-xs text-slate-400">
                  Arrastra o reordena los campos requeridos en esta evaluación.
                </p>
              </div>
              <button
                type="button"
                @click="handleAddField"
                class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#ffe8e8] text-[#ea384c] hover:bg-[#ffd6d6] transition-colors cursor-pointer"
              >
                <Plus class="w-3.5 h-3.5 stroke-[2.5]" />
                <span>Añadir Campo</span>
              </button>
            </div>

            <!-- Fields List -->
            <div class="space-y-3">
              <div
                v-for="(field, idx) in editingForm.fields || []"
                :key="field.id || idx"
                class="border rounded-2xl transition-all"
                :class="activeFieldEditIndex === idx ? 'border-indigo-400/80 bg-indigo-50/10 shadow-xs' : 'border-slate-200 bg-white hover:border-slate-300'"
              >
                <!-- Field Header Summary -->
                <div class="p-3.5 flex items-center justify-between gap-3">
                  <div class="flex items-center gap-2.5 truncate">
                    <span class="w-7 h-7 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-bold shrink-0">
                      {{ idx + 1 }}
                    </span>
                    <div class="truncate">
                      <div class="flex items-center gap-1.5">
                        <span class="text-xs font-bold text-slate-800 truncate">
                          {{ field.label || 'Campo sin etiqueta' }}
                        </span>
                        <span
                          v-if="field.required"
                          class="text-[10px] text-rose-500 font-bold bg-rose-50 px-2 py-0.5 rounded-md"
                        >
                          Obligatorio
                        </span>
                        <span
                          v-if="field.ask_in_initial_form"
                          class="text-[10px] text-blue-600 font-bold bg-blue-50 px-2 py-0.5 rounded-md border border-blue-200"
                        >
                          Paso 1 Previo
                        </span>
                        <span
                          v-else
                          class="text-[10px] text-purple-600 font-bold bg-purple-50 px-2 py-0.5 rounded-md border border-purple-200"
                        >
                          Conversación IA
                        </span>
                      <div class="flex items-center gap-1.5 flex-wrap">
                        <span class="text-[10px] font-mono text-slate-400">
                          {{ field.key }} • {{ (field.type === 'multiselect' || field.allow_multiple) ? 'multiselect' : field.type }}
                        </span>
                        <span
                          v-if="field.type === 'multiselect' || field.allow_multiple"
                          class="text-[9px] font-bold text-indigo-700 bg-indigo-50 border border-indigo-200 px-1.5 py-0.2 rounded"
                        >
                          Multiselección
                        </span>
                      </div>
                    </div>
                  </div>

                  <div class="flex items-center gap-1 shrink-0">
                    <button
                      type="button"
                      :disabled="idx === 0"
                      @click="handleMoveField(idx, 'up')"
                      class="p-1 text-slate-400 hover:text-slate-600 disabled:opacity-30 cursor-pointer"
                      title="Subir"
                    >
                      <ArrowUp class="w-3.5 h-3.5" />
                    </button>
                    <button
                      type="button"
                      :disabled="idx === (editingForm.fields || []).length - 1"
                      @click="handleMoveField(idx, 'down')"
                      class="p-1 text-slate-400 hover:text-slate-600 disabled:opacity-30 cursor-pointer"
                      title="Bajar"
                    >
                      <ArrowDown class="w-3.5 h-3.5" />
                    </button>
                    <button
                      type="button"
                      @click="activeFieldEditIndex = activeFieldEditIndex === idx ? null : idx"
                      class="px-2.5 py-1 text-xs font-bold text-[#ea384c] hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                    >
                      {{ activeFieldEditIndex === idx ? 'Listo' : 'Editar' }}
                    </button>
                    <button
                      type="button"
                      @click="handleRemoveField(idx)"
                      class="p-1 text-slate-300 hover:text-rose-500 rounded-lg cursor-pointer"
                      title="Eliminar campo"
                    >
                      <Trash2 class="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <!-- Field Edit Subform -->
                <div
                  v-if="activeFieldEditIndex === idx"
                  class="p-4 pt-0 border-t border-indigo-100 mt-2 space-y-3 bg-white rounded-b-2xl"
                >
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3">
                    <div>
                      <label class="block text-[11px] font-bold text-slate-600 mb-1">
                        Etiqueta Visible
                      </label>
                      <input
                        type="text"
                        v-model="field.label"
                        class="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
                      />
                    </div>

                    <div>
                      <label class="block text-[11px] font-bold text-slate-600 mb-1">
                        Clave (Key) en el JSON
                      </label>
                      <input
                        type="text"
                        :value="field.key"
                        @input="field.key = ($event.target as HTMLInputElement).value.toLowerCase().replace(/\s+/g, '_')"
                        class="w-full px-3 py-1.5 text-xs font-mono bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
                      />
                    </div>

                    <div>
                      <label class="block text-[11px] font-bold text-slate-600 mb-1">
                        Tipo de Control
                      </label>
                      <select
                        v-model="field.type"
                        @change="handleFieldTypeChange(field)"
                        class="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5] cursor-pointer"
                      >
                        <option value="text">Texto corto (Input)</option>
                        <option value="textarea">Texto largo (Textarea)</option>
                        <option value="select">Lista de opciones (Select)</option>
                        <option value="multiselect">Selección múltiple (Chips)</option>
                        <option value="number">Numérico / Presupuesto</option>
                        <option value="date">Fecha (DD/MM/AAAA)</option>
                        <option value="checkbox">Casilla de verificación (Sí / No)</option>
                        <option value="file">Multimedia / Archivos adjuntos (PDF, Excel, Word, etc.)</option>
                        <option value="role_user">Responsable por Rol (Usuario asignado)</option>
                      </select>
                    </div>

                    <div class="flex flex-col gap-2 pt-2 sm:pt-4">
                      <div class="flex items-center gap-2">
                        <input
                          type="checkbox"
                          :id="`req_${idx}`"
                          v-model="field.required"
                          class="w-4 h-4 rounded-md text-[#4F5AF5] focus:ring-[#4F5AF5] cursor-pointer"
                        />
                        <label :for="`req_${idx}`" class="text-xs font-bold text-slate-700 cursor-pointer">
                          Campo obligatorio para aprobar
                        </label>
                      </div>

                      <!-- Toggle Permitir Selecciones Múltiples -->
                      <div v-if="field.type === 'select' || field.type === 'multiselect'" class="flex items-center gap-2">
                        <input
                          type="checkbox"
                          :id="`multi_${idx}`"
                          :checked="field.type === 'multiselect' || field.allow_multiple === true"
                          @change="toggleAllowMultiple(field, ($event.target as HTMLInputElement).checked)"
                          class="w-4 h-4 rounded-md text-[#4F5AF5] focus:ring-[#4F5AF5] cursor-pointer"
                        />
                        <label :for="`multi_${idx}`" class="text-xs font-bold text-indigo-700 cursor-pointer flex items-center gap-1.5">
                          <span>Permitir selecciones múltiples</span>
                          <span class="text-[9px] font-bold px-1.5 py-0.2 bg-indigo-50 border border-indigo-200 rounded text-indigo-600">Multiselección</span>
                        </label>
                      </div>
                    </div>

                    <div class="sm:col-span-2 flex items-start gap-2 pt-3 border-t border-slate-100 mt-2">
                      <input
                        type="checkbox"
                        :id="`init_form_${idx}`"
                        v-model="field.ask_in_initial_form"
                        class="w-4 h-4 mt-0.5 rounded-md text-[#4F5AF5] focus:ring-[#4F5AF5] cursor-pointer"
                      />
                      <div>
                        <label :for="`init_form_${idx}`" class="text-xs font-bold text-slate-700 cursor-pointer block">
                          Solicitar en Formulario Previo (Paso 1)
                        </label>
                        <p class="text-[10px] text-slate-400 leading-tight mt-0.5">
                          Si se desmarca, este campo no aparecerá al inicio y la IA (TEO) lo preguntará y completará durante el chat.
                        </p>
                      </div>
                    </div>

                    <!-- Parametrización de Archivos (File Type) -->
                    <div v-if="field.type === 'file'" class="sm:col-span-2 p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-200">
                        <div>
                          <h4 class="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                            <Paperclip class="w-3.5 h-3.5 text-indigo-600" />
                            <span>Parametrización de Archivos y Multimedia</span>
                          </h4>
                          <p class="text-[10px] text-slate-500">
                            Formatos autorizados y límite en MB por archivo (máx 25 MB).
                          </p>
                        </div>
                        <div class="flex items-center gap-2">
                          <label class="text-[11px] font-semibold text-slate-600 flex items-center gap-1.5 cursor-pointer">
                            <input
                              type="checkbox"
                              :checked="field.fileOptions?.allowMultiple !== false"
                              @change="toggleFileMultiple(field, ($event.target as HTMLInputElement).checked)"
                              class="w-3.5 h-3.5 rounded text-indigo-600 cursor-pointer"
                            />
                            <span>Múltiples archivos</span>
                          </label>
                          <div v-if="field.fileOptions?.allowMultiple !== false" class="flex items-center gap-1 text-[10px] text-slate-500 font-medium">
                            <span>(máx</span>
                            <input
                              type="number"
                              min="1"
                              max="10"
                              :value="field.fileOptions?.maxFiles || 5"
                              @input="updateFileMaxFiles(field, parseInt(($event.target as HTMLInputElement).value) || 1)"
                              class="w-10 px-1 py-0.5 text-center text-xs bg-white border border-slate-200 rounded font-bold"
                            />
                            <span>archivos)</span>
                          </div>
                        </div>
                      </div>

                      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <div
                          v-for="ft in fileTypeDefinitions"
                          :key="ft.key"
                          class="p-2 rounded-lg border transition-all flex items-center justify-between gap-2"
                          :class="getFileTypeConfig(field, ft.key).enabled ? 'bg-white border-slate-200 shadow-2xs' : 'bg-slate-100/60 border-slate-200/50 opacity-60'"
                        >
                          <label class="flex items-center gap-2 cursor-pointer flex-1 min-w-0">
                            <input
                              type="checkbox"
                              :checked="getFileTypeConfig(field, ft.key).enabled"
                              @change="updateFileTypeConfig(field, ft.key, { enabled: ($event.target as HTMLInputElement).checked })"
                              class="w-3.5 h-3.5 rounded text-indigo-600 cursor-pointer"
                            />
                            <div class="truncate">
                              <span class="text-[11px] font-bold text-slate-800 block truncate">{{ ft.label }}</span>
                              <span class="inline-block px-1 py-0.2 rounded text-[9px] font-mono border" :class="ft.badgeColor">
                                {{ ft.ext }}
                              </span>
                            </div>
                          </label>

                          <div class="flex items-center gap-1 shrink-0">
                            <input
                              type="number"
                              min="0.5"
                              max="25"
                              step="0.5"
                              :disabled="!getFileTypeConfig(field, ft.key).enabled"
                              :value="getFileTypeConfig(field, ft.key).maxMb"
                              @input="updateFileTypeConfig(field, ft.key, { maxMb: Math.min(25, Math.max(0.5, parseFloat(($event.target as HTMLInputElement).value) || 1)) })"
                              class="w-12 px-1.5 py-0.5 text-xs text-right bg-slate-50 border border-slate-200 rounded font-bold text-slate-700 disabled:opacity-40"
                            />
                            <span class="text-[10px] font-semibold text-slate-400">MB</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- Opciones Disponibles (Select / MultiSelect) -->
                    <div
                      v-if="field.type === 'select' || field.type === 'multiselect' || field.allow_multiple"
                      class="sm:col-span-2 p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-3"
                    >
                      <div class="flex items-center justify-between">
                        <label class="block text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                          <ListPlus class="w-3.5 h-3.5 text-indigo-600" />
                          <span>Opciones Disponibles</span>
                        </label>
                        <div class="flex items-center gap-1.5">
                          <span
                            class="text-[10px] font-bold px-2 py-0.5 rounded-full border"
                            :class="(field.type === 'multiselect' || field.allow_multiple) ? 'bg-indigo-50 text-indigo-700 border-indigo-200' : 'bg-slate-100 text-slate-600 border-slate-200'"
                          >
                            {{ (field.type === 'multiselect' || field.allow_multiple) ? 'Selección Múltiple' : 'Selección Única' }}
                          </span>
                          <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
                            {{ (field.options || []).length }} {{ (field.options || []).length === 1 ? 'opción' : 'opciones' }}
                          </span>
                        </div>
                      </div>

                      <div class="flex gap-2">
                        <input
                          type="text"
                          placeholder="Escribe una opción (o pega una lista) y presiona Agregar..."
                          v-model="newOptionInput"
                          @keydown.enter.prevent="handleAddOption(idx)"
                          class="flex-1 px-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
                        />
                        <button
                          type="button"
                          @click="handleAddOption(idx)"
                          :disabled="!newOptionInput.trim()"
                          class="inline-flex items-center gap-1 px-4 py-1.5 text-xs font-bold text-white bg-[#f87171] hover:bg-[#ef4444] disabled:opacity-40 disabled:cursor-not-allowed rounded-lg transition-colors shadow-xs cursor-pointer"
                        >
                          <Plus class="w-3.5 h-3.5 stroke-[2.5]" />
                          <span>Agregar</span>
                        </button>
                      </div>

                      <div v-if="(field.options || []).length > 0" class="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                        <div
                          v-for="(opt, optIdx) in field.options"
                          :key="`${opt}-${optIdx}`"
                          class="flex items-center justify-between gap-2 px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg group hover:border-indigo-200 transition-colors"
                        >
                          <div class="flex items-center gap-2 min-w-0">
                            <span class="w-5 h-5 flex items-center justify-center text-[10px] font-bold text-slate-400 bg-slate-100 rounded-full shrink-0">
                              {{ optIdx + 1 }}
                            </span>
                            <span class="text-xs text-slate-700 font-medium truncate" :title="opt">
                              {{ opt }}
                            </span>
                          </div>
                          <div class="flex items-center gap-1 shrink-0">
                            <button
                              type="button"
                              title="Subir opción"
                              :disabled="optIdx === 0"
                              @click="handleMoveOption(idx, optIdx, 'up')"
                              class="p-1 text-slate-400 hover:text-indigo-600 disabled:opacity-20 disabled:hover:text-slate-400 rounded transition-colors cursor-pointer"
                            >
                              <ArrowUp class="w-3 h-3" />
                            </button>
                            <button
                              type="button"
                              title="Bajar opción"
                              :disabled="optIdx === field.options.length - 1"
                              @click="handleMoveOption(idx, optIdx, 'down')"
                              class="p-1 text-slate-400 hover:text-indigo-600 disabled:opacity-20 disabled:hover:text-slate-400 rounded transition-colors cursor-pointer"
                            >
                              <ArrowDown class="w-3 h-3" />
                            </button>
                            <button
                              type="button"
                              title="Eliminar opción"
                              @click="handleRemoveOption(idx, optIdx)"
                              class="p-1 text-slate-400 hover:text-rose-600 rounded transition-colors ml-1 cursor-pointer"
                            >
                              <Trash2 class="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      </div>

                      <div v-else class="p-3 text-center border border-dashed border-slate-200 rounded-lg bg-white/50">
                        <p class="text-xs text-slate-400">
                          No hay opciones configuradas. Escribe un valor arriba y presiona <strong>Enter</strong> o <strong>Agregar</strong>.
                        </p>
                      </div>
                    </div>

                    <!-- Responsable por Rol (Role User) -->
                    <div v-if="field.type === 'role_user'" class="sm:col-span-2 p-3.5 bg-indigo-50/60 border border-indigo-200/80 rounded-xl space-y-3">
                      <div>
                        <label class="block text-[11px] font-bold text-slate-800 mb-1 flex items-center gap-1.5">
                          <UserCheck class="w-3.5 h-3.5 text-indigo-600" />
                          <span>Rol del Sistema Requerido</span>
                        </label>
                        <select
                          v-model="field.target_role"
                          class="w-full px-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
                        >
                          <option v-for="r in rolesList" :key="r.code" :value="r.code">
                            {{ r.name }} ({{ r.code }})
                          </option>
                        </select>
                        <p class="text-[10px] text-slate-500 mt-1">
                          Solo se listarán las personas dadas de alta en el sistema con este rol.
                        </p>
                      </div>

                      <div class="flex items-start gap-2 pt-2.5 border-t border-indigo-100">
                        <input
                          type="checkbox"
                          :id="`scope_${idx}`"
                          v-model="field.filter_by_scope"
                          class="w-4 h-4 mt-0.5 rounded-md text-[#4F5AF5] focus:ring-[#4F5AF5] cursor-pointer"
                        />
                        <div>
                          <label :for="`scope_${idx}`" class="text-xs font-bold text-slate-700 cursor-pointer block">
                            Filtrar por Vicepresidencia y Dirección de la iniciativa
                          </label>
                          <p class="text-[10px] text-slate-500 leading-tight mt-0.5">
                            Si está marcado, solo se mostrarán personas con permisos sobre la VP/Dirección solicitante (o alcance transversal). Si solo existe 1 persona, el campo se bloqueará automáticamente con esa persona.
                          </p>
                        </div>
                      </div>
                    </div>

                    <!-- Placeholder & Help Text -->
                    <div>
                      <label class="block text-[11px] font-bold text-slate-600 mb-1">
                        Placeholder sugerido
                      </label>
                      <input
                        type="text"
                        v-model="field.placeholder"
                        class="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
                      />
                    </div>

                    <div>
                      <label class="block text-[11px] font-bold text-slate-600 mb-1">
                        Texto de ayuda o criterio
                      </label>
                      <input
                        type="text"
                        v-model="field.helpText"
                        class="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5]"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="p-4 border-t border-slate-200 bg-white shadow-xl shrink-0 sticky bottom-0 z-20 flex items-center justify-end gap-2.5">
          <button
            type="button"
            @click="isFormDrawerOpen = false; editingForm = null"
            class="px-4 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
          >
            Cancelar
          </button>
          <button
            type="button"
            @click="handleSaveForm"
            :disabled="isSaving"
            class="flex items-center gap-1.5 px-6 py-2.5 text-xs font-bold bg-gradient-to-r from-[#4F5AF5] to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 disabled:opacity-50 text-white rounded-xl shadow-md shadow-indigo-500/20 transition-all cursor-pointer"
          >
            <Check class="w-4 h-4 stroke-[2.5]" />
            <span>{{ isSaving ? 'Guardando...' : 'Guardar Formulario' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════════════ -->
    <!-- ── CONSENT DRAWER (STATEMENT EDITOR) ────────────────────────────────── -->
    <!-- ═══════════════════════════════════════════════════════════════════════ -->
    <div
      v-if="isConsentDrawerOpen && editingConsent"
      class="fixed inset-0 z-[9999] overflow-hidden bg-slate-900/50 backdrop-blur-xs flex justify-end"
    >
      <div class="w-full max-w-xl bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
        <!-- Header -->
        <div class="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50/70 shrink-0">
          <div class="flex items-center gap-2.5">
            <div class="w-9 h-9 rounded-xl bg-indigo-50 text-[#4F5AF5] flex items-center justify-center font-bold">
              <ShieldCheck class="w-5 h-5" />
            </div>
            <div>
              <h2 class="text-base font-bold text-slate-900">
                {{ editingConsent.id ? 'Editar Consentimiento' : 'Nueva Declaración de Consentimiento' }}
              </h2>
              <p class="text-xs text-slate-500">
                Texto legal de aceptación que el evaluador debe certificar obligatoriamente.
              </p>
            </div>
          </div>
          <button
            type="button"
            @click="isConsentDrawerOpen = false; editingConsent = null"
            class="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-y-auto p-6 space-y-5">
          <!-- Estado Asociado en Flujo Oficial Banner -->
          <div class="p-3.5 bg-gradient-to-r from-indigo-50/90 to-blue-50/70 border border-indigo-200/90 rounded-2xl space-y-1.5 shadow-2xs">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-indigo-950 flex items-center gap-1.5">
                <Workflow class="w-4 h-4 text-[#4F5AF5]" />
                <span>Asociación en el Flujo Oficial (IACS)</span>
              </span>
              <span class="text-[10px] font-bold text-indigo-700 bg-white px-2 py-0.5 rounded-full border border-indigo-200">
                {{ getAssociatedNodesForConsent(editingConsent.id, editingConsent.code).length > 0 ? `${getAssociatedNodesForConsent(editingConsent.id, editingConsent.code).length} ${getAssociatedNodesForConsent(editingConsent.id, editingConsent.code).length === 1 ? 'estado asignado' : 'estados asignados'}` : 'Sin asignación' }}
              </span>
            </div>
            <div v-if="getAssociatedNodesForConsent(editingConsent.id, editingConsent.code).length > 0" class="flex flex-wrap gap-1.5 pt-1">
              <span
                v-for="n in getAssociatedNodesForConsent(editingConsent.id, editingConsent.code)"
                :key="n.id"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold bg-white text-indigo-900 border border-indigo-200 shadow-2xs"
              >
                <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>{{ n.data?.label || n.id }}</span>
                <span class="text-[10px] font-mono text-slate-400">({{ n.id }})</span>
              </span>
            </div>
            <p v-else class="text-xs text-slate-500 leading-relaxed">
              Este consentimiento no está asignado a ningún estado actualmente. Puedes asignarlo desde el
              <NuxtLink to="/admin/workflow-editor" class="text-indigo-600 font-bold hover:underline" target="_blank">
                Editor de Flujos
              </NuxtLink>
              (Pestaña <em>Dictamen</em> de la tarjeta deseada).
            </p>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Código Identificador <span class="text-rose-500">*</span>
              </label>
              <input
                type="text"
                placeholder="ej: consent_bp_ti"
                v-model="editingConsent.code"
                class="w-full px-3.5 py-2 text-xs sm:text-sm font-mono bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5] focus:outline-none"
              />
              <p class="text-[10px] text-slate-400 mt-1">Identificador unívoco en minúsculas.</p>
            </div>

            <div>
              <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Versión
              </label>
              <input
                type="number"
                min="1"
                v-model.number="editingConsent.version"
                class="w-full px-3.5 py-2 text-xs sm:text-sm bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5] focus:outline-none"
              />
            </div>

            <div class="sm:col-span-2">
              <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Título de la Declaración <span class="text-rose-500">*</span>
              </label>
              <input
                type="text"
                placeholder="ej: Conformidad y Viabilidad Técnica del Business Partner TI"
                v-model="editingConsent.title"
                class="w-full px-3.5 py-2 text-xs sm:text-sm bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5] focus:outline-none font-semibold text-slate-800"
              />
            </div>

            <div class="sm:col-span-2">
              <div class="flex items-center justify-between mb-1.5">
                <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Texto Legal / Declaración Jurada <span class="text-rose-500">*</span>
                </label>
                <span class="text-[10px] text-slate-400 font-mono">
                  {{ (editingConsent.statement || '').length }} caracteres
                </span>
              </div>
              <textarea
                rows="6"
                placeholder="Escribe el texto de la declaración que se mostrará junto al checkbox de aceptación..."
                v-model="editingConsent.statement"
                class="w-full px-3.5 py-2 text-xs sm:text-sm bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#4F5AF5]/20 focus:border-[#4F5AF5] focus:outline-none leading-relaxed"
              ></textarea>
            </div>

            <div class="sm:col-span-2">
              <div class="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="consent_is_active"
                  v-model="editingConsent.is_active"
                  class="w-4 h-4 rounded-md text-[#4F5AF5] focus:ring-[#4F5AF5] cursor-pointer"
                />
                <label for="consent_is_active" class="text-xs font-semibold text-slate-700 cursor-pointer">
                  Consentimiento activo para uso en flujos
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="p-4 border-t border-slate-200 bg-white shadow-xl shrink-0 sticky bottom-0 z-20 flex items-center justify-end gap-2.5">
          <button
            type="button"
            @click="isConsentDrawerOpen = false; editingConsent = null"
            class="px-4 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
          >
            Cancelar
          </button>
          <button
            type="button"
            @click="handleSaveConsent"
            :disabled="isSaving"
            class="flex items-center gap-1.5 px-6 py-2.5 text-xs font-bold bg-gradient-to-r from-[#4F5AF5] to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 disabled:opacity-50 text-white rounded-xl shadow-md shadow-indigo-500/20 transition-all cursor-pointer"
          >
            <Check class="w-4 h-4 stroke-[2.5]" />
            <span>{{ isSaving ? 'Guardando...' : 'Guardar Consentimiento' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL 3: PROBAR CONSENTIMIENTO (Live Consent Simulator) -->
    <div v-if="showLiveConsentModal && activePreviewConsent" class="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl shadow-2xl max-w-xl w-full border border-slate-200 overflow-hidden">
        <div class="px-6 py-4 bg-gradient-to-r from-purple-900 to-indigo-950 text-white flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-purple-500/20 border border-purple-400/30 flex items-center justify-center text-purple-300">
              <ShieldCheck class="w-4 h-4" />
            </div>
            <div>
              <h3 class="text-sm font-bold text-white">{{ activePreviewConsent.title }}</h3>
              <p class="text-[11px] text-purple-200/70">Verificación de Cadena de Custodia Legal</p>
            </div>
          </div>
          <button @click="showLiveConsentModal = false" class="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors cursor-pointer">
            <X class="w-5 h-5" />
          </button>
        </div>

        <div class="p-6 space-y-4">
          <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
            <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Declaración Jurada</span>
            <p class="text-xs text-slate-800 leading-relaxed font-serif italic">
              "{{ activePreviewConsent.statement }}"
            </p>
          </div>

          <label class="flex items-start gap-3 p-3 rounded-xl border border-indigo-200 bg-indigo-50/50 cursor-pointer">
            <input
              type="checkbox"
              v-model="liveConsentChecked"
              class="mt-0.5 rounded text-indigo-600 focus:ring-indigo-500 cursor-pointer"
            />
            <span class="text-xs font-semibold text-indigo-950">
              He leído y doy mi conformidad expresa en representación de mi rol operativo.
            </span>
          </label>
        </div>

        <div class="px-6 py-3 bg-slate-50 border-t border-slate-200 flex justify-end gap-2">
          <button
            type="button"
            @click="showLiveConsentModal = false"
            class="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-semibold rounded-xl cursor-pointer"
          >
            Cerrar
          </button>
          <button
            type="button"
            :disabled="!liveConsentChecked"
            @click="testConsentSubmit"
            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-sm cursor-pointer"
          >
            Firmar Digitalmente (Prueba)
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { 
  FileCheck2, 
  ShieldCheck, 
  FileText, 
  Search, 
  Plus, 
  Copy, 
  Sliders, 
  Workflow, 
  ChevronRight, 
  Eye, 
  X, 
  Info, 
  Check, 
  Paperclip, 
  Trash2, 
  ArrowUp, 
  ArrowDown, 
  ArrowUpDown,
  CheckCircle2,
  ListPlus,
  UserCheck,
  Edit3
} from 'lucide-vue-next';

const config = useRuntimeConfig();
const apiBase = config.public.apiBase || '/api/v1';

// Tab State
const activeTab = ref<'forms' | 'consents' | 'documents'>('forms');
const isLoading = ref(true);

// Data
const forms = ref<any[]>([]);
const consents = ref<any[]>([]);
const templates = ref<any[]>([]);

// Filter & Sort
const searchQuery = ref('');
const selectedStageFilter = ref('all');
const statusFilter = ref<'all' | 'active' | 'inactive'>('all');
const sortOrder = ref<'workflow_asc' | 'workflow_desc' | 'name_asc' | 'name_desc' | 'fields_count'>('workflow_asc');
const workflowNodes = ref<any[]>([]);

// Modal / Drawer States
const showLivePreviewModal = ref(false);
const activePreviewForm = ref<any>(null);
const liveFormData = ref<Record<string, any>>({});

// Form Drawer State (Matching original WorkflowCatalogManager)
const isFormDrawerOpen = ref(false);
const editingForm = ref<any>(null);
const activeFieldEditIndex = ref<number | null>(null);
const newOptionInput = ref('');
const isSaving = ref(false);

// Consent Drawer State
const isConsentDrawerOpen = ref(false);
const editingConsent = ref<any>(null);
const showLiveConsentModal = ref(false);
const activePreviewConsent = ref<any>(null);
const liveConsentChecked = ref(false);

// File types definitions for file field parameterization
const fileTypeDefinitions: Array<{
  key: 'pdf' | 'docx' | 'xlsx' | 'image' | 'txt';
  label: string;
  ext: string;
  badgeColor: string;
}> = [
  { key: 'pdf', label: 'Archivos PDF', ext: '.pdf', badgeColor: 'bg-rose-50 text-rose-700 border-rose-200' },
  { key: 'docx', label: 'Documentos Word', ext: '.docx', badgeColor: 'bg-blue-50 text-blue-700 border-blue-200' },
  { key: 'xlsx', label: 'Hojas de Cálculo Excel', ext: '.xlsx, .xls', badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  { key: 'image', label: 'Imágenes / Diagramas', ext: '.jpg, .png, .webp', badgeColor: 'bg-violet-50 text-violet-700 border-violet-200' },
  { key: 'txt', label: 'Archivos de Texto Plano', ext: '.txt', badgeColor: 'bg-slate-100 text-slate-700 border-slate-200' },
];

const rolesList = [
  { code: 'bp_ti', name: 'Business Partner de TI (BP TI)' },
  { code: 'business_owner', name: 'Business Owner (Líder Solicitante)' },
  { code: 'vicepresidente_del_negocio', name: 'Vicepresidente del Negocio' },
  { code: 'gestor_de_la_demanda', name: 'Gestor de la Demanda TI' },
  { code: 'lider_de_dominio', name: 'Líder de Dominio de Arquitectura' },
  { code: 'registrador', name: 'Registrador de Iniciativas' },
  { code: 'admin', name: 'Administrador General' },
];

// File Type Helper Functions
const getFileTypeConfig = (field: any, key: 'pdf' | 'docx' | 'xlsx' | 'image' | 'txt') => {
  if (!field.fileOptions) {
    field.fileOptions = {
      allowMultiple: true,
      maxFiles: 5,
      fileTypes: {
        pdf: { enabled: true, maxMb: 10 },
        docx: { enabled: true, maxMb: 10 },
        xlsx: { enabled: true, maxMb: 10 },
        image: { enabled: true, maxMb: 5 },
        txt: { enabled: true, maxMb: 2 },
      },
    };
  }
  if (!field.fileOptions.fileTypes) {
    field.fileOptions.fileTypes = {};
  }
  if (!field.fileOptions.fileTypes[key]) {
    field.fileOptions.fileTypes[key] = { enabled: true, maxMb: 10 };
  }
  return field.fileOptions.fileTypes[key];
};

const updateFileTypeConfig = (field: any, key: 'pdf' | 'docx' | 'xlsx' | 'image' | 'txt', updates: any) => {
  const cfg = getFileTypeConfig(field, key);
  Object.assign(cfg, updates);
};

const toggleFileMultiple = (field: any, allow: boolean) => {
  if (!field.fileOptions) getFileTypeConfig(field, 'pdf');
  field.fileOptions.allowMultiple = allow;
};

const updateFileMaxFiles = (field: any, count: number) => {
  if (!field.fileOptions) getFileTypeConfig(field, 'pdf');
  field.fileOptions.maxFiles = count;
};

// Canonical Workflow Stages
const STAGES_LIST = [
  { key: 'borrador', short: 'REGISTRO', label: '1. Registro de Iniciativa (Borrador)', order: 1 },
  { key: 'eval_bp', short: 'EVAL_BP', label: '2. Evaluación de Viabilidad (BP TI)', order: 2 },
  { key: 'aprob_bo', short: 'APROB_BO', label: '3. Patrocinio Ejecutivo (BO)', order: 3 },
  { key: 'aprob_vp', short: 'APROB_VP', label: '4. Aprobación Vicepresidencia (VP)', order: 4 },
  { key: 'asig_demanda', short: 'ASIG_DEMANDA', label: '5. Asignación de Dominio TI', order: 5 },
  { key: 'ventana_est', short: 'VENTANA_EST', label: '6. Compromiso de Estimación', order: 6 },
  { key: 'est_con_presupuesto', short: 'EST_CON_PPTO', label: '7A. Estimación con Presupuesto', order: 7.1 },
  { key: 'est_sin_presupuesto', short: 'EST_SIN_PPTO', label: '7B. Estimación sin Presupuesto', order: 7.2 },
  { key: 'val_est_bp', short: 'VAL_EST_BP', label: '8A. Validación Estimación BP TI', order: 8.1 },
  { key: 'vobo_est_bo', short: 'VOBO_EST_BO', label: '8B. VoBo Estimación BO', order: 8.2 },
  { key: 'plan_fechas', short: 'PLAN_FECHAS', label: '9. Planificación de Fechas', order: 9 },
  { key: 'val_plan_bp', short: 'VAL_PLAN_BP', label: '10. Validación Planificación BP TI', order: 10 },
  { key: 'aprob_plan_bo', short: 'APROB_PLAN_BO', label: '11. Aprobación Final Fechas BO', order: 11 },
  { key: 'planificacion', short: 'EN_DEMANDA', label: '12. En Demanda / Planificación', order: 12 },
  { key: 'observada', short: 'OBSERVADA', label: '⚠️ Observada / Subsanación', order: 20 },
  { key: 'desestimada', short: 'DESESTIMADA', label: '🗄️ Desestimada / Fin', order: 30 },
];

const getStageShortTag = (stageId: string) => {
  const match = STAGES_LIST.find(s => s.key === stageId);
  return match ? match.short : (stageId || 'ETAPA').toUpperCase().slice(0, 12);
};

// Node Associated Helpers
const getAssociatedNodesForForm = (formId?: string, formCode?: string) => {
  if (!formId && !formCode) return [];
  return (workflowNodes.value || []).filter(
    (n: any) =>
      (formId && (n.data?.form_id === formId || n.data?.formId === formId)) ||
      (formCode && (n.data?.form_id === formCode || n.data?.formId === formCode))
  );
};

const getAssociatedNodesForConsent = (consentId?: string, consentCode?: string) => {
  if (!consentId && !consentCode) return [];
  return (workflowNodes.value || []).filter(
    (n: any) =>
      (consentId && (n.data?.consent_id === consentId || n.data?.consentId === consentId)) ||
      (consentCode && (n.data?.consent_id === consentCode || n.data?.consentId === consentCode))
  );
};

const getAssociatedNodesForDocument = (docId?: string, docCode?: string) => {
  if (!docId && !docCode) return [];
  return (workflowNodes.value || []).filter(
    (n: any) =>
      (docId && (n.data?.document_template_id === docId || n.data?.docTemplateId === docId)) ||
      (docCode && (n.data?.document_template_id === docCode || n.data?.docTemplateId === docCode))
  );
};

const NODE_FLOW_ORDER: Record<string, number> = {
  start: 0,
  borrador: 1,
  ai_chat: 1.5,
  eval_bp: 2,
  aprob_bo: 3,
  aprob_vp: 4,
  asig_demanda: 5,
  ventana_est: 6,
  gw_presupuesto: 6.5,
  est_con_presupuesto: 7.1,
  est_sin_presupuesto: 7.2,
  val_est_bp: 8.1,
  vobo_est_bo: 8.2,
  plan_fechas: 9,
  val_plan_bp: 10,
  aprob_plan_bo: 11,
  planificacion: 12,
  observada: 20,
  desestimada: 30,
  end: 99,
};

const getWorkflowRankForNodes = (nodes: any[]): number => {
  if (!nodes || nodes.length === 0) return 999;
  let minRank = 999;
  for (const node of nodes) {
    if (NODE_FLOW_ORDER[node.id] !== undefined) {
      minRank = Math.min(minRank, NODE_FLOW_ORDER[node.id]);
      continue;
    }
    const match = (node.data?.label || '').match(/^(\d+)([a-zA-Z]?)/);
    if (match) {
      const num = parseInt(match[1], 10);
      const sub = match[2] ? (match[2].toLowerCase().charCodeAt(0) - 96) * 0.1 : 0;
      minRank = Math.min(minRank, num + sub);
    } else {
      minRank = Math.min(minRank, 500);
    }
  }
  return minRank;
};

// Fetch Catalogs
const loadData = async () => {
  isLoading.value = true;
  try {
    const [formsRes, consentsRes, templatesRes, workflowRes] = await Promise.all([
      $fetch<any>(`${apiBase}/stage-forms`),
      $fetch<any>(`${apiBase}/stage-consents`),
      $fetch<any>(`${apiBase}/document-templates`),
      $fetch<any>(`${apiBase}/workflow/active`).catch(() => null),
    ]);
    forms.value = formsRes?.data || formsRes || [];
    consents.value = consentsRes?.data || consentsRes || [];
    templates.value = templatesRes?.data || templatesRes || [];
    if (workflowRes?.data?.graph_json?.nodes) {
      workflowNodes.value = workflowRes.data.graph_json.nodes;
    }
  } catch (err) {
    console.error('Error fetching stage catalog data:', err);
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  loadData();
});

// Filtered and Sorted Forms
const filteredForms = computed(() => {
  let list = forms.value.filter((f) => {
    const matchSearch =
      !searchQuery.value.trim() ||
      (f.name || '').toLowerCase().includes(searchQuery.value.toLowerCase().trim()) ||
      (f.code || '').toLowerCase().includes(searchQuery.value.toLowerCase().trim()) ||
      (f.description && f.description.toLowerCase().includes(searchQuery.value.toLowerCase().trim()));

    const matchStatus =
      statusFilter.value === 'all'
        ? true
        : statusFilter.value === 'active'
        ? f.is_active
        : !f.is_active;

    let matchStage = true;
    if (selectedStageFilter.value !== 'all') {
      const associated = getAssociatedNodesForForm(f.id, f.code);
      const associatedIds = associated.map((n: any) => n.id);
      matchStage =
        f.stage_id === selectedStageFilter.value ||
        associatedIds.includes(selectedStageFilter.value);
    }

    return matchSearch && matchStatus && matchStage;
  });

  return list.sort((a, b) => {
    if (sortOrder.value === 'workflow_asc' || sortOrder.value === 'workflow_desc') {
      const rankA = getWorkflowRankForNodes(getAssociatedNodesForForm(a.id, a.code));
      const rankB = getWorkflowRankForNodes(getAssociatedNodesForForm(b.id, b.code));
      if (rankA !== rankB) {
        return sortOrder.value === 'workflow_asc' ? rankA - rankB : rankB - rankA;
      }
      return (a.name || '').localeCompare(b.name || '');
    }
    if (sortOrder.value === 'name_asc') return (a.name || '').localeCompare(b.name || '');
    if (sortOrder.value === 'name_desc') return (b.name || '').localeCompare(a.name || '');
    if (sortOrder.value === 'fields_count') return (b.fields || []).length - (a.fields || []).length;
    return 0;
  });
});

// Filtered and Sorted Consents
const filteredConsents = computed(() => {
  let list = consents.value.filter((c) => {
    const matchSearch =
      !searchQuery.value.trim() ||
      (c.title || '').toLowerCase().includes(searchQuery.value.toLowerCase().trim()) ||
      (c.code || '').toLowerCase().includes(searchQuery.value.toLowerCase().trim()) ||
      (c.statement && c.statement.toLowerCase().includes(searchQuery.value.toLowerCase().trim()));

    const matchStatus =
      statusFilter.value === 'all'
        ? true
        : statusFilter.value === 'active'
        ? c.is_active
        : !c.is_active;

    let matchStage = true;
    if (selectedStageFilter.value !== 'all') {
      const associated = getAssociatedNodesForConsent(c.id, c.code);
      const associatedIds = associated.map((n: any) => n.id);
      matchStage =
        c.stage_id === selectedStageFilter.value ||
        associatedIds.includes(selectedStageFilter.value);
    }

    return matchSearch && matchStatus && matchStage;
  });

  return list.sort((a, b) => {
    if (sortOrder.value === 'workflow_asc' || sortOrder.value === 'workflow_desc') {
      const rankA = getWorkflowRankForNodes(getAssociatedNodesForConsent(a.id, a.code));
      const rankB = getWorkflowRankForNodes(getAssociatedNodesForConsent(b.id, b.code));
      if (rankA !== rankB) {
        return sortOrder.value === 'workflow_asc' ? rankA - rankB : rankB - rankA;
      }
      return (a.title || '').localeCompare(b.title || '');
    }
    if (sortOrder.value === 'name_asc') return (a.title || '').localeCompare(b.title || '');
    if (sortOrder.value === 'name_desc') return (b.title || '').localeCompare(a.title || '');
    return 0;
  });
});

// Filtered and Sorted Documents
const filteredDocuments = computed(() => {
  let list = templates.value.filter((d) => {
    const matchSearch =
      !searchQuery.value.trim() ||
      (d.name || '').toLowerCase().includes(searchQuery.value.toLowerCase().trim()) ||
      (d.code || '').toLowerCase().includes(searchQuery.value.toLowerCase().trim()) ||
      (d.description && d.description.toLowerCase().includes(searchQuery.value.toLowerCase().trim()));

    const matchStatus =
      statusFilter.value === 'all'
        ? true
        : statusFilter.value === 'active'
        ? d.is_active
        : !d.is_active;

    return matchSearch && matchStatus;
  });

  return list.sort((a, b) => {
    if (sortOrder.value === 'workflow_asc' || sortOrder.value === 'workflow_desc') {
      const rankA = getWorkflowRankForNodes(getAssociatedNodesForDocument(d.id, d.code));
      const rankB = getWorkflowRankForNodes(getAssociatedNodesForDocument(d.id, d.code));
      if (rankA !== rankB) {
        return sortOrder.value === 'workflow_asc' ? rankA - rankB : rankB - rankA;
      }
      return (a.name || '').localeCompare(b.name || '');
    }
    if (sortOrder.value === 'name_asc') return (a.name || '').localeCompare(b.name || '');
    if (sortOrder.value === 'name_desc') return (b.name || '').localeCompare(a.name || '');
    return 0;
  });
});

// Live Preview Form
const openLivePreview = (form: any) => {
  activePreviewForm.value = form;
  liveFormData.value = {};
  showLivePreviewModal.value = true;
};

const toggleMultiSelect = (fieldKey: string, option: string) => {
  if (!liveFormData.value[fieldKey]) {
    liveFormData.value[fieldKey] = [];
  }
  const idx = liveFormData.value[fieldKey].indexOf(option);
  if (idx > -1) {
    liveFormData.value[fieldKey].splice(idx, 1);
  } else {
    liveFormData.value[fieldKey].push(option);
  }
};

const toggleAllowMultiple = (field: any, checked: boolean) => {
  field.allow_multiple = checked;
  if (checked) {
    field.type = 'multiselect';
  } else {
    field.type = 'select';
  }
};

const handleFieldTypeChange = (field: any) => {
  if (field.type === 'multiselect') {
    field.allow_multiple = true;
  } else if (field.type === 'select' && field.allow_multiple) {
    field.allow_multiple = false;
  }
};

const testValidateForm = () => {
  if (!activePreviewForm.value) return;
  const missingFields: string[] = [];
  for (const field of activePreviewForm.value.fields || []) {
    const key = field.key || field.id;
    const val = liveFormData.value[key];
    const isEmpty = val === undefined || val === null || (typeof val === 'string' && val.trim() === '') || (Array.isArray(val) && val.length === 0);
    if (field.required && isEmpty) {
      missingFields.push(field.label || key);
    }
  }

  if (missingFields.length > 0) {
    alert(`Campos obligatorios faltantes:\n• ${missingFields.join('\n• ')}`);
  } else {
    alert('✓ ¡Validación exitosa! Todos los campos requeridos han sido completados correctamente.');
  }
};

// ── Form Drawer Operations (Matching WorkflowCatalogManager) ─────────────────
const handleOpenNewForm = () => {
  editingForm.value = {
    id: '',
    code: '',
    name: '',
    description: '',
    fields: [
      {
        id: 'f1',
        key: 'dictamen_estado',
        label: 'Dictamen de Viabilidad',
        type: 'select',
        required: true,
        options: ['Viable sin observaciones', 'Viable con condiciones', 'No viable'],
        helpText: 'Seleccione el dictamen formal para esta etapa',
        ask_in_initial_form: false,
      },
      {
        id: 'f2',
        key: 'observaciones_tecnicas',
        label: 'Observaciones y Sustento',
        type: 'textarea',
        required: true,
        placeholder: 'Detalle el sustento de su evaluación...',
        ask_in_initial_form: false,
      },
    ],
    is_active: true,
  };
  activeFieldEditIndex.value = 0;
  newOptionInput.value = '';
  isFormDrawerOpen.value = true;
};

const handleEditForm = (form: any) => {
  editingForm.value = JSON.parse(JSON.stringify(form));
  activeFieldEditIndex.value = (editingForm.value.fields && editingForm.value.fields.length > 0) ? 0 : null;
  newOptionInput.value = '';
  isFormDrawerOpen.value = true;
};

const handleDuplicateForm = (form: any) => {
  const duplicated = {
    ...JSON.parse(JSON.stringify(form)),
    id: '',
    code: `${form.code}_copia_${Date.now().toString(36).slice(-4)}`,
    name: `${form.name} (Copia)`,
  };
  editingForm.value = duplicated;
  activeFieldEditIndex.value = 0;
  newOptionInput.value = '';
  isFormDrawerOpen.value = true;
};

const handleDeleteForm = async (form: any) => {
  if (!confirm(`¿Estás seguro de eliminar el formulario "${form.name}"?`)) return;
  try {
    await $fetch(`${apiBase}/stage-forms/${form.id}`, {
      method: 'DELETE',
    });
    await loadData();
  } catch (err: any) {
    alert('Error al eliminar formulario: ' + (err.data?.detail || err.message));
  }
};

const handleAddField = () => {
  if (!editingForm.value) return;
  const count = (editingForm.value.fields || []).length + 1;
  const newField = {
    id: `f_${Date.now().toString(36)}`,
    key: `campo_${count}`,
    label: `Nuevo Campo ${count}`,
    type: 'text',
    required: false,
    placeholder: '',
    helpText: '',
    ask_in_initial_form: false,
    options: ['Opción 1', 'Opción 2'],
  };
  if (!editingForm.value.fields) editingForm.value.fields = [];
  editingForm.value.fields.push(newField);
  activeFieldEditIndex.value = editingForm.value.fields.length - 1;
};

const handleRemoveField = (idx: number) => {
  if (!editingForm.value?.fields) return;
  editingForm.value.fields.splice(idx, 1);
  if (activeFieldEditIndex.value === idx) {
    activeFieldEditIndex.value = null;
  } else if (activeFieldEditIndex.value !== null && activeFieldEditIndex.value > idx) {
    activeFieldEditIndex.value--;
  }
};

const handleMoveField = (idx: number, direction: 'up' | 'down') => {
  if (!editingForm.value?.fields) return;
  const targetIdx = direction === 'up' ? idx - 1 : idx + 1;
  if (targetIdx < 0 || targetIdx >= editingForm.value.fields.length) return;
  const fields = [...editingForm.value.fields];
  const temp = fields[idx];
  fields[idx] = fields[targetIdx];
  fields[targetIdx] = temp;
  editingForm.value.fields = fields;
  activeFieldEditIndex.value = targetIdx;
};

const handleAddOption = (fieldIndex: number) => {
  const val = newOptionInput.value.trim();
  if (!val || fieldIndex === null || !editingForm.value?.fields) return;
  const targetField = editingForm.value.fields[fieldIndex];
  if (!targetField.options) targetField.options = [];
  
  const items = val.split(/[\n,]+/).map((s: string) => s.trim()).filter(Boolean);
  for (const item of items) {
    if (!targetField.options.includes(item)) {
      targetField.options.push(item);
    }
  }
  newOptionInput.value = '';
};

const handleMoveOption = (fieldIndex: number, optIdx: number, dir: 'up' | 'down') => {
  const targetField = editingForm.value?.fields?.[fieldIndex];
  if (!targetField?.options) return;
  const targetIdx = dir === 'up' ? optIdx - 1 : optIdx + 1;
  if (targetIdx < 0 || targetIdx >= targetField.options.length) return;
  const copy = [...targetField.options];
  const temp = copy[optIdx];
  copy[optIdx] = copy[targetIdx];
  copy[targetIdx] = temp;
  targetField.options = copy;
};

const handleRemoveOption = (fieldIndex: number, optIdx: number) => {
  const targetField = editingForm.value?.fields?.[fieldIndex];
  if (!targetField?.options) return;
  targetField.options.splice(optIdx, 1);
};

const handleSaveForm = async () => {
  if (!editingForm.value) return;
  if (!editingForm.value.name?.trim() || !editingForm.value.code?.trim()) {
    alert('Por favor especifica un nombre y un código único para el formulario.');
    return;
  }

  isSaving.value = true;
  try {
    const payload = {
      code: editingForm.value.code.trim().toLowerCase().replace(/\s+/g, '_'),
      name: editingForm.value.name.trim(),
      description: editingForm.value.description?.trim() || null,
      fields: editingForm.value.fields || [],
      is_active: editingForm.value.is_active !== false,
    };

    if (editingForm.value.id) {
      await $fetch(`${apiBase}/stage-forms/${editingForm.value.id}`, {
        method: 'PUT',
        body: payload,
      });
    } else {
      await $fetch(`${apiBase}/stage-forms`, {
        method: 'POST',
        body: payload,
      });
    }

    await loadData();
    isFormDrawerOpen.value = false;
    editingForm.value = null;
  } catch (err: any) {
    alert('Error al guardar formulario: ' + (err.data?.detail || err.message));
  } finally {
    isSaving.value = false;
  }
};

// ── Consent Operations ───────────────────────────────────────────────────────
const handleOpenNewConsent = () => {
  editingConsent.value = {
    id: '',
    code: '',
    title: '',
    statement: 'Yo, en mi calidad de [Rol Responsable], declaro bajo responsabilidad que he revisado de manera íntegra y exhaustiva los antecedentes técnicos, operativos y de negocio de esta iniciativa, otorgando mi conformidad formal para su prosecución en la cadena de demanda TI.',
    version: 1,
    is_active: true,
  };
  isConsentDrawerOpen.value = true;
};

const handleEditConsent = (consent: any) => {
  editingConsent.value = JSON.parse(JSON.stringify(consent));
  isConsentDrawerOpen.value = true;
};

const handleDuplicateConsent = (consent: any) => {
  const duplicated = {
    ...JSON.parse(JSON.stringify(consent)),
    id: '',
    code: `${consent.code}_v${(consent.version || 1) + 1}`,
    title: `${consent.title} (Copia)`,
    version: (consent.version || 1) + 1,
  };
  editingConsent.value = duplicated;
  isConsentDrawerOpen.value = true;
};

const handleDeleteConsent = async (consent: any) => {
  if (!confirm(`¿Estás seguro de eliminar el consentimiento "${consent.title}"?`)) return;
  try {
    await $fetch(`${apiBase}/stage-consents/${consent.id}`, {
      method: 'DELETE',
    });
    await loadData();
  } catch (err: any) {
    alert('Error al eliminar consentimiento: ' + (err.data?.detail || err.message));
  }
};

const handleSaveConsent = async () => {
  if (!editingConsent.value) return;
  if (!editingConsent.value.title?.trim() || !editingConsent.value.code?.trim() || !editingConsent.value.statement?.trim()) {
    alert('Por favor completa el código, título y la declaración formal del consentimiento.');
    return;
  }

  isSaving.value = true;
  try {
    const payload = {
      code: editingConsent.value.code.trim().toLowerCase().replace(/\s+/g, '_'),
      title: editingConsent.value.title.trim(),
      statement: editingConsent.value.statement.trim(),
      version: Number(editingConsent.value.version) || 1,
      is_active: editingConsent.value.is_active !== false,
    };

    if (editingConsent.value.id) {
      await $fetch(`${apiBase}/stage-consents/${editingConsent.value.id}`, {
        method: 'PUT',
        body: payload,
      });
    } else {
      await $fetch(`${apiBase}/stage-consents`, {
        method: 'POST',
        body: payload,
      });
    }

    await loadData();
    isConsentDrawerOpen.value = false;
    editingConsent.value = null;
  } catch (err: any) {
    alert('Error al guardar consentimiento: ' + (err.data?.detail || err.message));
  } finally {
    isSaving.value = false;
  }
};

const openLiveConsentPreview = (consent: any) => {
  activePreviewConsent.value = consent;
  liveConsentChecked.value = false;
  showLiveConsentModal.value = true;
};

const testConsentSubmit = () => {
  alert('✓ Declaración legal registrada con timestamp y firma digital simulada.');
  showLiveConsentModal.value = false;
};

// Document Templates
const openNewTemplateModal = () => {
  alert('Nueva plantilla de exportación');
};
const openPdfPreview = (tpl: any) => {
  alert(`Generando vista previa de ${tpl.name}...`);
};
const openTemplateEditor = (tpl: any) => {
  alert(`Editor de plantilla ${tpl.name}`);
};
</script>
