import { ref } from 'vue';

const aiName = ref('Teo');
const aiAvatar = ref('');
const isLoaded = ref(false);

export function useAiAssistant() {
  const config = useRuntimeConfig();
  const apiBase = config.public.apiBase;

  const loadAiConfig = async (force = false) => {
    if (isLoaded.value && !force) return;
    try {
      const res = await $fetch<any[]>(`${apiBase}/admin/ai-training?layer=settings`).catch(() => []);
      if (Array.isArray(res)) {
        const nameItem = res.find((e: any) => e.title === 'ai_name');
        const avatarItem = res.find((e: any) => e.title === 'ai_avatar');
        if (nameItem?.content) aiName.value = nameItem.content;
        if (avatarItem?.content) aiAvatar.value = avatarItem.content;
        isLoaded.value = true;
      }
    } catch (err) {
      console.warn('Error loading AI assistant config:', err);
    }
  };

  const setAiConfig = (name?: string, avatar?: string) => {
    if (name !== undefined) aiName.value = name;
    if (avatar !== undefined) aiAvatar.value = avatar;
  };

  return {
    aiName,
    aiAvatar,
    loadAiConfig,
    setAiConfig,
  };
}
