<template>
  <!-- Fullscreen Mode (Initial App Boot, Full Page Navigation) -->
  <div
    v-if="fullscreen"
    class="fixed inset-0 z-[200] min-h-screen w-full flex items-center justify-center bg-[#F8FAFC] select-none"
  >
    <div class="flex flex-col items-center justify-center text-center p-6 max-w-md w-full">
      <!-- Visual glowing spinner with badge -->
      <div class="relative mb-5 flex items-center justify-center">
        <div class="absolute w-16 h-16 rounded-full bg-indigo-500/15 animate-ping duration-1000"></div>
        <div class="w-14 h-14 rounded-2xl bg-gradient-to-tr from-[#4F5AF5] to-indigo-400 p-0.5 shadow-lg shadow-indigo-500/25 flex items-center justify-center">
          <div class="w-full h-full bg-white rounded-[14px] flex items-center justify-center">
            <Loader2 class="w-6 h-6 text-[#4F5AF5] animate-spin" />
          </div>
        </div>
        <div class="absolute -bottom-1 -right-1 bg-emerald-500 text-white p-1 rounded-full shadow-xs border-2 border-white">
          <ShieldCheck class="w-3 h-3" />
        </div>
      </div>

      <!-- Title & Subtitle -->
      <div class="space-y-1 max-w-sm">
        <h4 class="text-sm font-bold text-slate-800 flex items-center justify-center gap-1.5">
          <span>{{ title }}</span>
          <Sparkles class="w-3.5 h-3.5 text-amber-500" />
        </h4>

        <p v-if="subtitle" class="text-xs text-slate-500 font-medium">
          {{ subtitle }}
        </p>

        <!-- Dynamic rotating institutional phrase -->
        <div class="h-6 flex items-center justify-center overflow-hidden pt-1">
          <Transition name="fade-slide" mode="out-in">
            <p
              :key="phraseIndex"
              class="text-xs font-semibold text-[#EB5F46] tracking-tight"
            >
              {{ currentPhrase }}
            </p>
          </Transition>
        </div>
      </div>
    </div>
  </div>

  <!-- Modal / Overlay Mode (Global async actions, saving, AI thinking) -->
  <div
    v-else-if="overlay"
    class="fixed inset-0 z-[300] bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 transition-all duration-200"
  >
    <div class="bg-white/95 backdrop-blur-md rounded-2xl border border-indigo-100 shadow-2xl p-6 max-w-md w-full animate-in fade-in zoom-in-95 duration-200">
      <div class="flex flex-col items-center justify-center text-center select-none">
        <!-- Visual glowing spinner with badge -->
        <div class="relative mb-5 flex items-center justify-center">
          <div class="absolute w-16 h-16 rounded-full bg-indigo-500/15 animate-ping duration-1000"></div>
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-tr from-[#4F5AF5] to-indigo-400 p-0.5 shadow-lg shadow-indigo-500/25 flex items-center justify-center">
            <div class="w-full h-full bg-white rounded-[14px] flex items-center justify-center">
              <Loader2 class="w-6 h-6 text-[#4F5AF5] animate-spin" />
            </div>
          </div>
          <div class="absolute -bottom-1 -right-1 bg-emerald-500 text-white p-1 rounded-full shadow-xs border-2 border-white">
            <ShieldCheck class="w-3 h-3" />
          </div>
        </div>

        <!-- Title & Subtitle -->
        <div class="space-y-1 max-w-sm">
          <h4 class="text-sm font-bold text-slate-800 flex items-center justify-center gap-1.5">
            <span>{{ title }}</span>
            <Sparkles class="w-3.5 h-3.5 text-amber-500" />
          </h4>

          <p v-if="subtitle" class="text-xs text-slate-500 font-medium">
            {{ subtitle }}
          </p>

          <!-- Dynamic rotating phrase -->
          <div class="h-6 flex items-center justify-center overflow-hidden pt-1">
            <Transition name="fade-slide" mode="out-in">
              <p
                :key="phraseIndex"
                class="text-xs font-semibold text-[#EB5F46] tracking-tight"
              >
                {{ currentPhrase }}
              </p>
            </Transition>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Inline / Embedded Mode (Tables, Cards, Tab Panels) -->
  <div
    v-else
    :class="['flex flex-col items-center justify-center text-center p-8 select-none', className]"
  >
    <!-- Visual glowing spinner with badge -->
    <div class="relative mb-4 flex items-center justify-center">
      <div class="absolute w-14 h-14 rounded-full bg-indigo-500/15 animate-ping duration-1000"></div>
      <div class="w-12 h-12 rounded-2xl bg-gradient-to-tr from-[#4F5AF5] to-indigo-400 p-0.5 shadow-md shadow-indigo-500/20 flex items-center justify-center">
        <div class="w-full h-full bg-white rounded-[14px] flex items-center justify-center">
          <Loader2 class="w-5 h-5 text-[#4F5AF5] animate-spin" />
        </div>
      </div>
      <div class="absolute -bottom-1 -right-1 bg-emerald-500 text-white p-0.5 rounded-full shadow-xs border border-white">
        <ShieldCheck class="w-2.5 h-2.5" />
      </div>
    </div>

    <!-- Title & Subtitle -->
    <div class="space-y-1 max-w-sm">
      <h4 class="text-xs sm:text-sm font-bold text-slate-800 flex items-center justify-center gap-1.5">
        <span>{{ title }}</span>
        <Sparkles class="w-3 h-3 text-amber-500" />
      </h4>

      <p v-if="subtitle" class="text-[11px] text-slate-500 font-medium">
        {{ subtitle }}
      </p>

      <!-- Dynamic rotating phrase -->
      <div class="h-5 flex items-center justify-center overflow-hidden pt-0.5">
        <Transition name="fade-slide" mode="out-in">
          <p
            :key="phraseIndex"
            class="text-[11px] font-semibold text-[#EB5F46] tracking-tight"
          >
            {{ currentPhrase }}
          </p>
        </Transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { Loader2, ShieldCheck, Sparkles } from 'lucide-vue-next';

const DEFAULT_INSTITUTIONAL_PHRASES = [
  "Conectando con el motor de gobernanza IACS...",
  "Sincronizando estado con la cadena de custodia...",
  "Validando directrices y políticas de TI...",
  "Cargando trazabilidad y dictámenes técnicos...",
  "Optimizando la cartera estratégica de iniciativas...",
  "Verificando acuerdos y consentimientos digitales..."
];

const props = withDefaults(
  defineProps<{
    title?: string;
    subtitle?: string;
    phrases?: string[];
    overlay?: boolean;
    fullscreen?: boolean;
    className?: string;
  }>(),
  {
    title: "Iniciando IACS Enterprise",
    subtitle: "Verificando credenciales de seguridad y sesión activa...",
    phrases: () => [
      "Conectando con el motor de gobernanza IACS...",
      "Sincronizando estado con la cadena de custodia...",
      "Validando directrices y políticas de TI...",
      "Cargando trazabilidad y dictámenes técnicos...",
      "Optimizando la cartera estratégica de iniciativas...",
      "Verificando acuerdos y consentimientos digitales..."
    ],
    overlay: false,
    fullscreen: false,
    className: ""
  }
);

const phraseIndex = ref(0);
let timer: any = null;

const currentPhrase = computed(() => {
  if (!props.phrases || props.phrases.length === 0) return '';
  return props.phrases[phraseIndex.value % props.phrases.length];
});

onMounted(() => {
  if (props.phrases && props.phrases.length > 1) {
    timer = setInterval(() => {
      phraseIndex.value = (phraseIndex.value + 1) % props.phrases.length;
    }, 2400);
  }
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>

<style scoped>
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
