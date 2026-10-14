import { ref } from 'vue';

interface LoaderOptions {
  title?: string;
  subtitle?: string;
  phrases?: string[];
  overlay?: boolean;
  fullscreen?: boolean;
}

const DEFAULT_PHRASES = [
  "Conectando con el motor de gobernanza IACS...",
  "Sincronizando estado con la cadena de custodia...",
  "Validando directrices y políticas de TI...",
  "Cargando trazabilidad y dictámenes técnicos...",
  "Optimizando la cartera estratégica de iniciativas...",
  "Verificando acuerdos y consentimientos digitales..."
];

const isLoading = ref(false);
const title = ref("Iniciando IACS Enterprise");
const subtitle = ref("Verificando credenciales de seguridad y sesión activa...");
const phrases = ref<string[]>(DEFAULT_PHRASES);
const isOverlay = ref(false);
const isFullscreen = ref(false);

export const useGlobalLoader = () => {
  const showLoader = (options?: LoaderOptions) => {
    title.value = options?.title || "Iniciando IACS Enterprise";
    subtitle.value = options?.subtitle || "Verificando credenciales de seguridad y sesión activa...";
    phrases.value = options?.phrases || DEFAULT_PHRASES;
    isOverlay.value = options?.overlay ?? true;
    isFullscreen.value = options?.fullscreen ?? false;
    isLoading.value = true;
  };

  const hideLoader = () => {
    isLoading.value = false;
    isOverlay.value = false;
    isFullscreen.value = false;
  };

  const withLoader = async <T>(
    asyncFn: () => Promise<T>,
    options?: LoaderOptions
  ): Promise<T> => {
    showLoader(options);
    try {
      return await asyncFn();
    } finally {
      hideLoader();
    }
  };

  return {
    isLoading,
    title,
    subtitle,
    phrases,
    isOverlay,
    isFullscreen,
    showLoader,
    hideLoader,
    withLoader,
  };
};
