<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import MedicalDisclaimer from '@/components/ui/MedicalDisclaimer.vue';

// --- Live platform statistics (real data, refreshed continuously) -----------

interface PlatformStats {
  members: number;
  doctors: number;
  consultations: number;
  consultationsLive: number;
  prescriptions: number;
  messages: number;
  documents: number;
}

const stats = ref<PlatformStats | null>(null);
let statsTimer: number | undefined;

async function loadStats() {
  try {
    const res = await fetch('/api/v1/platform/stats/');
    if (!res.ok) return;
    const data = await res.json();
    stats.value = {
      members: Number(data.members ?? 0),
      doctors: Number(data.doctors ?? 0),
      consultations: Number(data.consultations ?? 0),
      consultationsLive: Number(data.consultationsLive ?? 0),
      prescriptions: Number(data.prescriptions ?? 0),
      messages: Number(data.messages ?? 0),
      documents: Number(data.documents ?? 0),
    };
  } catch {
    // keep the last known values
  }
}

onMounted(() => {
  void loadStats();
  statsTimer = window.setInterval(loadStats, 15000);
});

onUnmounted(() => statsTimer && window.clearInterval(statsTimer));

const liveStats = computed(() =>
  stats.value
    ? [
        { label: stats.value.members + ' members', sub: stats.value.doctors + ' clinicians' },
        { label: stats.value.consultations + ' consultations', sub: stats.value.consultationsLive > 0 ? stats.value.consultationsLive + ' live now' : 'all rooms idle' },
        { label: stats.value.messages + ' messages', sub: 'synced in real time' },
        { label: stats.value.prescriptions + ' prescriptions', sub: stats.value.documents + ' records' },
      ]
    : [],
);

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const portal = computed(() => {
  if (route.query.portal === 'doctor') return 'doctor';
  if (route.query.portal === 'admin') return 'admin';
  return 'patient';
});
const portalLabel = computed(() =>
  portal.value === 'doctor'
    ? t('nav.doctorPortal')
    : portal.value === 'admin'
      ? t('nav.adminPortal')
      : t('nav.patientPortal'),
);
const email = ref('');
const password = ref('');
const error = ref<string | null>(null);

const DEMO = [
  { role: 'patient', email: 'patient@medtwin.dev', label: 'Patient' },
  { role: 'doctor', email: 'doctor@medtwin.dev', label: 'Doctor' },
  { role: 'admin', email: 'admin@medtwin.dev', label: 'Admin' },
];

const FEATURES = [
  {
    title: 'AI digital twin',
    body: 'A living model of your health that answers, tracks and predicts with you.',
    icon: 'M12 3a4 4 0 014 4c1.7.6 3 2.2 3 4.2 1.2.8 2 2.1 2 3.6A4.2 4.2 0 0116.8 19c-.7 1.2-2 2-3.5 2h-2.6c-1.5 0-2.8-.8-3.5-2A4.2 4.2 0 013 14.8c0-1.5.8-2.8 2-3.6C5 9.2 6.3 7.6 8 7a4 4 0 014-4z',
  },
  {
    title: 'Encrypted video consultations',
    body: 'Talk face-to-face with your clinician over peer-to-peer encrypted calls.',
    icon: 'M3 6.5A2.5 2.5 0 015.5 4h8A2.5 2.5 0 0116 6.5v7a2.5 2.5 0 01-2.5 2.5h-8A2.5 2.5 0 013 13.5zM16 10l5-3v9l-5-3',
  },
  {
    title: 'Private by design',
    body: 'You decide who sees your records — consent and audit trails on every access.',
    icon: 'M12 3l7 3v6c0 4.4-3 7.6-7 9-4-1.4-7-4.6-7-9V6zM9.5 12l2 2 3.5-3.5',
  },
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

function switchPortal(role: string) {
  const demo = DEMO.find((d) => d.role === role);
  if (demo) useDemo(demo.email);
  router.replace({ query: { ...route.query, portal: role } });
}
</script>

<template>
  <div class="grid min-h-[calc(100vh-64px)] lg:grid-cols-[1.05fr_1fr]">
    <!-- Brand panel -->
    <div class="relative hidden flex-col justify-between overflow-hidden bg-gradient-to-br from-brand-900 via-brand-800 to-brand-600 p-10 text-white lg:flex xl:p-14">
      <!-- decorative glows -->
      <div class="pointer-events-none absolute -left-24 -top-24 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
      <div class="pointer-events-none absolute -bottom-32 -right-16 h-96 w-96 rounded-full bg-brand-400/25 blur-3xl" />
      <div class="pointer-events-none absolute right-1/4 top-1/3 h-40 w-40 rounded-full bg-white/5 blur-2xl" />

      <div class="relative">
        <div class="flex items-center gap-3">
          <span class="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/15 shadow-inner backdrop-blur">
            <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M2 12h4l2-6 4 12 3-8 2 2h5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <p class="text-xl font-extrabold tracking-tight">MedTwin<span class="text-brand-200">.ai</span></p>
        </div>

        <h1 class="mt-12 max-w-lg text-[34px] font-extrabold leading-[1.15] tracking-tight text-white xl:text-[38px]">
          Your health,<br />intelligently connected.
        </h1>
        <p class="mt-4 max-w-md text-[15px] leading-relaxed text-white/70">
          One secure home for your digital twin, medical records, AI assistant and clinician consultations.
        </p>

        <ul class="mt-10 space-y-5">
          <li v-for="feature in FEATURES" :key="feature.title" class="flex items-start gap-4">
            <span class="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/10 ring-1 ring-white/15">
              <svg class="h-5 w-5 text-brand-100" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path :d="feature.icon" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="text-[14.5px] font-bold">{{ feature.title }}</p>
              <p class="mt-0.5 max-w-sm text-[12.5px] leading-relaxed text-white/60">{{ feature.body }}</p>
            </div>
          </li>
        </ul>

        <!-- Live platform statistics -->
        <div v-if="liveStats.length" class="mt-10 rounded-2xl bg-white/10 p-4 ring-1 ring-white/15 backdrop-blur">
          <p class="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.14em] text-brand-100">
            <span class="relative flex h-2 w-2">
              <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-300 opacity-75" />
              <span class="relative inline-flex h-2 w-2 rounded-full bg-emerald-300" />
            </span>
            Live platform activity
          </p>
          <div class="mt-3 grid grid-cols-2 gap-x-6 gap-y-3">
            <div v-for="item in liveStats" :key="item.label">
              <p class="text-[17px] font-extrabold leading-tight text-white tabular-nums">{{ item.label }}</p>
              <p class="text-[11px] text-white/55">{{ item.sub }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="relative mt-10">
          <p class="flex items-center gap-2 text-[12px] font-semibold text-white/80">
            <svg class="h-4 w-4 text-brand-200" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M12 3l7 3v6c0 4.4-3 7.6-7 9-4-1.4-7-4.6-7-9V6z" stroke-linecap="round" stroke-linejoin="round" />
              <path d="M9.5 12l2 2 3.5-3.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            End-to-end encrypted
          </p>
          <p class="mt-2 flex items-center gap-2 text-[12px] font-semibold text-white/80">
            <svg class="h-4 w-4 text-brand-200" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M12 3l7 3v6c0 4.4-3 7.6-7 9-4-1.4-7-4.6-7-9V6z" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            Consent-controlled records
          </p>
          <p class="mt-2 flex items-center gap-2 text-[12px] font-semibold text-white/80">
            <svg class="h-4 w-4 text-brand-200" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <circle cx="12" cy="12" r="9" />
              <path d="M12 8v4l3 2" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            Full audit trail on every access
          </p>
      </div>
    </div>

    <!-- Form panel -->
    <div class="flex items-center justify-center px-5 py-12 sm:px-10">
      <div class="w-full max-w-[420px]">
        <!-- mobile brand -->
        <div class="mb-8 flex items-center gap-3 lg:hidden">
          <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-white">
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M2 12h4l2-6 4 12 3-8 2 2h5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <p class="text-lg font-extrabold tracking-tight text-brand-700">MedTwin<span class="text-brand-500">.ai</span></p>
        </div>

        <h2 class="text-[26px] font-extrabold tracking-tight text-ink-900">Welcome back</h2>
        <p class="mt-1.5 text-[13.5px] text-ink-500">Sign in to continue to your {{ portalLabel.toLowerCase() }} portal.</p>

        <!-- portal tabs -->
        <div class="mt-6 grid grid-cols-3 gap-1 rounded-2xl bg-surface-100 p-1">
          <button
            v-for="demo in DEMO"
            :key="demo.role"
            type="button"
            class="rounded-xl px-3 py-2 text-[12.5px] font-semibold transition-colors"
            :class="portal === demo.role ? 'bg-white text-brand-700 shadow-card' : 'text-ink-500 hover:text-ink-800'"
            @click="switchPortal(demo.role)"
          >{{ demo.label }}</button>
        </div>

        <form class="mt-6 space-y-4" @submit.prevent="submit">
          <div>
            <label class="label" for="email">{{ t('auth.email') }}</label>
            <div class="relative">
              <svg class="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <rect x="3" y="5" width="18" height="14" rx="2.5" />
                <path d="M3.5 7l8.5 6 8.5-6" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <input id="email" v-model="email" class="input pl-10" type="email" autocomplete="email" placeholder="you@example.com" required />
            </div>
          </div>
          <div>
            <label class="label" for="password">{{ t('auth.password') }}</label>
            <div class="relative">
              <svg class="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <rect x="4" y="10" width="16" height="10" rx="2.5" />
                <path d="M8 10V7a4 4 0 018 0v3" stroke-linecap="round" />
              </svg>
              <input id="password" v-model="password" class="input pl-10" type="password" autocomplete="current-password" placeholder="••••••••••" required />
            </div>
          </div>

          <p v-if="error" class="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5 text-[13px] text-rose-700">
            <svg class="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <circle cx="12" cy="12" r="9" />
              <path d="M12 8v4.5M12 16v.5" stroke-linecap="round" />
            </svg>
            {{ error }}
          </p>

          <button class="btn-primary flex w-full items-center justify-center gap-2 py-2.5" type="submit" :disabled="auth.loading">
            <svg v-if="auth.loading" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-opacity="0.25" stroke-width="3" />
              <path d="M21 12a9 9 0 00-9-9" stroke="currentColor" stroke-width="3" stroke-linecap="round" />
            </svg>
            {{ auth.loading ? t('common.loading') : t('auth.signInTitle') }}
            <svg v-if="!auth.loading" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M4 12h15m0 0l-5-5m5 5l-5 5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </form>

        <p class="mt-5 text-center text-[13.5px] text-ink-500">
          {{ t('auth.noAccount') }}
          <RouterLink to="/register" class="font-semibold text-brand-700 hover:underline">Create an account</RouterLink>
        </p>

        <!-- demo accounts -->
        <div class="mt-7 rounded-2xl border border-ink-100 bg-surface-50 p-4">
          <div class="flex items-center justify-between">
            <p class="flex items-center gap-1.5 text-[12px] font-bold uppercase tracking-wide text-ink-400">
              <span class="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Live accounts
            </p>
            <p class="text-[11px] text-ink-400">Password: MedTwin@2026</p>
          </div>
          <div class="mt-2.5 grid grid-cols-3 gap-2">
            <button
              v-for="demo in DEMO"
              :key="demo.email"
              type="button"
              class="rounded-xl border bg-white px-2 py-2 text-[11.5px] font-semibold transition-colors"
              :class="email === demo.email ? 'border-brand-300 text-brand-700 ring-1 ring-brand-200' : 'border-ink-200 text-ink-600 hover:border-brand-300 hover:text-brand-700'"
              :title="demo.email"
              @click="useDemo(demo.email)"
            >{{ demo.label }}</button>
          </div>
          <p class="mt-2 text-[10.5px] leading-relaxed text-ink-400">Fully working accounts on this platform — everything you do syncs in real time.</p>
        </div>

        <div class="mt-5">
          <MedicalDisclaimer compact />
        </div>
      </div>
    </div>
  </div>
</template>
