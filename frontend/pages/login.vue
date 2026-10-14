<script setup lang="ts">
import { ref } from 'vue';
import { LogIn, KeyRound, AlertCircle, CheckCircle2, UserPlus, Loader2 } from 'lucide-vue-next';

const router = useRouter();
const config = useRuntimeConfig();
const apiBase = config.public.apiBase;

const email = ref('');
const password = ref('');
const isSignUp = ref(false);
const loading = ref(false);
const error = ref<string | null>(null);
const success = ref<string | null>(null);

const handleSubmit = async () => {
  loading.value = true;
  error.value = null;
  success.value = null;

  const cleanEmail = email.value.trim().toLowerCase();
  const rawPassword = password.value;

  try {
    if (isSignUp.value) {
      // Modo Activar Acceso (Crear contraseña)
      const data: any = await $fetch(`${apiBase}/auth/signup`, {
        method: 'POST',
        body: {
          email: cleanEmail,
          password: rawPassword,
        },
      });

      if (data?.access_token) {
        if (process.client) {
          localStorage.setItem('iacs_token', data.access_token);
          if (data.user) {
            localStorage.setItem('iacs_user', JSON.stringify(data.user));
          }
        }
        success.value = '¡Acceso activado con éxito! Redirigiendo al sistema...';
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 800);
      }
    } else {
      // Modo Ingresar Normal
      const data: any = await $fetch(`${apiBase}/auth/login`, {
        method: 'POST',
        body: {
          email: cleanEmail,
          password: rawPassword,
        },
      });

      if (data?.access_token) {
        if (process.client) {
          localStorage.setItem('iacs_token', data.access_token);
          if (data.user) {
            localStorage.setItem('iacs_user', JSON.stringify(data.user));
          }
        }
        success.value = '¡Bienvenido! Redirigiendo...';
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 500);
      }
    }
  } catch (err: any) {
    console.error('Error de autenticación:', err);
    error.value = err.data?.detail || err.message || 'Ocurrió un error inesperado al iniciar sesión.';
  } finally {
    loading.value = false;
  }
};

const selectQuickProfile = (profileEmail: string) => {
  email.value = profileEmail;
  password.value = 'admin';
  isSignUp.value = false;
  handleSubmit();
};
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-[#F7F8FC] p-4 font-sans select-none">
    <div class="w-full max-w-[420px] bg-white rounded-3xl shadow-[0_4px_32px_rgba(13,67,108,.08)] border border-[#D7D9E8] p-8">
      <!-- Logo Superior Laureate Perú -->
      <div class="flex justify-center mb-6">
        <div class="w-14 h-14 bg-gradient-to-br from-[#EB5F46] via-[#B84E52] to-[#0D436C] rounded-2xl flex items-center justify-center shadow-lg shadow-[#EB5F46]/25">
          <span class="font-black text-white text-xl tracking-tighter">LP</span>
        </div>
      </div>

      <!-- Título y Subtítulo -->
      <h1 class="text-2xl font-black text-center text-[#0D436C] mb-1.5 uppercase tracking-wide">
        IT NEEDS MANAGER
      </h1>
      <p class="text-xs text-center text-[#64748B] font-bold tracking-widest uppercase mb-6">
        {{ isSignUp ? 'Activa tu acceso estableciendo una contraseña' : 'LAUREATE PERÚ' }}
      </p>

      <!-- Segmented Control (Pestañas Ingresar / Activar Acceso) -->
      <div class="flex p-1.5 mb-6 bg-[#F7F8FC] rounded-2xl border border-[#D7D9E8]">
        <button
          type="button"
          @click="() => { isSignUp = false; error = null; success = null; }"
          :class="[
            'flex-1 flex justify-center items-center gap-2 py-2 text-xs font-bold uppercase tracking-wider rounded-xl transition-all cursor-pointer',
            !isSignUp ? 'bg-white text-[#EB5F46] shadow-xs border border-slate-200/60' : 'text-[#64748B] hover:text-[#0D436C]'
          ]"
        >
          <LogIn class="w-4 h-4" />
          <span>INGRESAR</span>
        </button>

        <button
          type="button"
          @click="() => { isSignUp = true; error = null; success = null; }"
          :class="[
            'flex-1 flex justify-center items-center gap-2 py-2 text-xs font-bold uppercase tracking-wider rounded-xl transition-all cursor-pointer',
            isSignUp ? 'bg-white text-[#EB5F46] shadow-xs border border-slate-200/60' : 'text-[#64748B] hover:text-[#0D436C]'
          ]"
        >
          <KeyRound class="w-4 h-4" />
          <span>ACTIVAR ACCESO</span>
        </button>
      </div>

      <!-- Alerta de Error -->
      <div v-if="error" class="mb-5 bg-red-50 border border-red-200 p-3.5 rounded-xl flex items-start gap-2.5 text-xs text-red-700 font-medium animate-in fade-in duration-200">
        <AlertCircle class="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
        <p class="leading-relaxed">{{ error }}</p>
      </div>

      <!-- Alerta de Éxito -->
      <div v-if="success" class="mb-5 bg-emerald-50 border border-emerald-200 p-3.5 rounded-xl flex items-start gap-2.5 text-xs text-emerald-700 font-medium animate-in fade-in duration-200">
        <CheckCircle2 class="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
        <p class="leading-relaxed">{{ success }}</p>
      </div>

      <!-- Formulario -->
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-[#4A5568] mb-1.5">
            CORREO ELECTRÓNICO
          </label>
          <input
            type="email"
            required
            v-model="email"
            class="w-full px-4 py-3 bg-[#F8FAFC] border border-[#D7D9E8] rounded-xl text-sm text-[#1A1A2E] placeholder:text-[#94A3B8] outline-none focus:border-[#EB5F46] focus:bg-white focus:ring-2 focus:ring-[#EB5F46]/10 transition-all"
            placeholder="tu@correo.com"
          />
        </div>

        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-[#4A5568] mb-1.5">
            CONTRASEÑA
          </label>
          <input
            type="password"
            required
            v-model="password"
            minlength="6"
            class="w-full px-4 py-3 bg-[#F8FAFC] border border-[#D7D9E8] rounded-xl text-sm text-[#1A1A2E] placeholder:text-[#94A3B8] outline-none focus:border-[#EB5F46] focus:bg-white focus:ring-2 focus:ring-[#EB5F46]/10 transition-all tracking-widest"
            :placeholder="isSignUp ? 'Crea una contraseña segura' : '••••••••'"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-[#EB5F46] hover:bg-[#d94f38] disabled:opacity-50 text-white py-3.5 rounded-xl font-bold uppercase tracking-wider text-xs transition-all flex items-center justify-center gap-2 shadow-md shadow-[#EB5F46]/25 mt-5 cursor-pointer transform active:scale-98"
        >
          <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
          <template v-else-if="isSignUp">
            <UserPlus class="w-4 h-4" />
            <span>GUARDAR CONTRASEÑA Y ENTRAR</span>
          </template>
          <template v-else>
            <LogIn class="w-4 h-4" />
            <span>INGRESAR AL SISTEMA</span>
          </template>
        </button>
      </form>

      <!-- Accesos Rápidos de Demostración para Desarrollo -->
      <div class="mt-6 pt-4 border-t border-[#E2E8F0] space-y-2">
        <span class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider text-center">
          Accesos Rápidos (Entorno Local):
        </span>
        <div class="grid grid-cols-3 gap-1.5 text-[11px]">
          <button
            type="button"
            @click="selectQuickProfile('admin@iacs.empresa.com')"
            class="p-2 text-center rounded-xl border border-slate-200 bg-slate-50 hover:border-[#EB5F46] hover:bg-[#fff0ed] hover:text-[#EB5F46] transition-colors font-bold text-[#0D436C] cursor-pointer"
            title="Administrador General"
          >
            👑 Admin
          </button>
          <button
            type="button"
            @click="selectQuickProfile('cmendoza@iacs.empresa.com')"
            class="p-2 text-center rounded-xl border border-slate-200 bg-slate-50 hover:border-[#0D436C] hover:bg-blue-50 hover:text-[#0D436C] transition-colors font-bold text-blue-700 cursor-pointer"
            title="Carlos Mendoza (BP TI)"
          >
            💼 BP TI
          </button>
          <button
            type="button"
            @click="selectQuickProfile('esther@captcha.com')"
            class="p-2 text-center rounded-xl border border-slate-200 bg-slate-50 hover:border-emerald-500 hover:bg-emerald-50 hover:text-emerald-700 transition-colors font-bold text-emerald-700 cursor-pointer"
            title="Esther (Key User)"
          >
            ✍️ Key User
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
