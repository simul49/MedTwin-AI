<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import MedicalDisclaimer from '@/components/ui/MedicalDisclaimer.vue';
import signinVisual from '@/assets/signin-visual.png';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const portal = computed(() => (route.query.portal === 'doctor' ? 'doctor' : 'patient'));
const email = ref('');
const password = ref('');
const error = ref<string | null>(null);

const DEMO = [
  { role: 'patient', email: 'patient@medtwin.dev' },
  { role: 'doctor', email: 'doctor@medtwin.dev' },
  { role: 'admin', email: 'admin@medtwin.dev' },
];

async function submit() {
  error.value = null;
  try {
    await auth.login(email.value.trim(), password.value);
    const next = typeof route.query.next === 'string' ? route.query.next : null;
    router.push(next ?? auth.homePath);
  } catch (err) {
    error.value = err instanceof Error ? err.message : t('auth.invalidCredentials');
  }
}

function useDemo(demoEmail: string) {
  email.value = demoEmail;
  password.value = 'MedTwin@2026';
}
</script>

<template>
  <div class="container-page grid items-center gap-10 py-14 lg:grid-cols-2">
    <div class="hidden lg:block">
      <p v-reveal class="section-eyebrow">{{ t('brand.full') }}</p>
      <h1 v-reveal:1 class="mt-4 text-4xl font-extrabold leading-tight">{{ t('auth.signInTitle') }}</h1>
      <p v-reveal:2 class="mt-3 max-w-md text-ink-600">{{ t('auth.signInSubtitle') }}</p>
      <div v-reveal:3 class="mt-7 overflow-hidden rounded-2xl border border-ink-200 bg-white shadow-card">
        <img :src="signinVisual" alt="Illustration of a patient using a health dashboard" class="h-auto w-full" loading="lazy" />
      </div>
      <div v-reveal:4 class="mt-7 rounded-2xl border border-ink-200 bg-white p-5">
        <p class="text-sm font-semibold">{{ t('auth.demoTitle') }}</p>
        <p class="muted mt-1">{{ t('auth.demoBody') }}</p>
        <ul class="mt-3 space-y-2">
          <li v-for="demo in DEMO" :key="demo.email">
            <button class="btn-secondary w-full justify-between text-xs" @click="useDemo(demo.email)">
              <span>{{ demo.role }}</span>
              <span class="text-ink-500">{{ demo.email }}</span>
            </button>
          </li>
        </ul>
        <p class="mt-3 text-xs text-ink-400">Password: MedTwin@2026</p>
      </div>
    </div>

    <div class="card card-pad">
      <h2 class="text-2xl font-bold">{{ t('auth.signInTitle') }}</h2>
      <p class="muted mt-1">
        {{ portal === 'doctor' ? t('nav.doctorPortal') : t('nav.patientPortal') }} · {{ t('nav.portal') }}
      </p>

      <form class="mt-6 space-y-4" @submit.prevent="submit">
        <div>
          <label class="label" for="email">{{ t('auth.email') }}</label>
          <input id="email" v-model="email" class="input" type="email" autocomplete="email" required />
        </div>
        <div>
          <label class="label" for="password">{{ t('auth.password') }}</label>
          <input id="password" v-model="password" class="input" type="password" autocomplete="current-password" required />
        </div>

        <p v-if="error" class="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {{ error }}
        </p>

        <button class="btn-primary w-full" type="submit" :disabled="auth.loading">
          {{ auth.loading ? t('common.loading') : t('auth.signInTitle') }}
        </button>
      </form>

      <div class="mt-5 flex items-center justify-between text-sm">
        <RouterLink to="/register" class="text-brand-700 hover:underline">{{ t('auth.noAccount') }}</RouterLink>
        <button class="text-ink-500 hover:text-ink-800" @click="useDemo('patient@medtwin.dev')">
          {{ t('auth.demoTitle') }}
        </button>
      </div>

      <div class="mt-6">
        <MedicalDisclaimer compact />
      </div>
    </div>
  </div>
</template>
