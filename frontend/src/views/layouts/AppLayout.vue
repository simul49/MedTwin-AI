<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { SUPPORTED_LOCALES, type LocaleCode } from '@/i18n';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';
import { connect } from '@/api/endpoints';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const ui = useUiStore();

const mobileOpen = ref(false);
const langOpen = ref(false);
const notifications = ref<{ unread: number; results: { id: string; title: string; body: string; createdAt: string | null }[] }>({
  unread: 0,
  results: [],
});

const ICONS: Record<string, string> = {
  overview: 'M3 12h6v9H3zM9.5 3h6v18h-6zM16 8h5v13h-5z',
  twin: 'M12 3a4 4 0 110 8 4 4 0 010-8zM4 21a8 8 0 0116 0',
  records: 'M7 3h10v18l-5-3-5 3z',
  documents: 'M6 2h8l4 4v16H6zM14 2v5h5',
  assistant: 'M4 5h16v11H9l-5 4z',
  recommendations: 'M12 3l2.6 5.6 6.1.8-4.5 4.3 1.1 6-5.3-3-5.3 3 1.1-6L3.3 9.4l6.1-.8z',
  consent: 'M12 2l7 4v6c0 5-3 8-7 10-4-2-7-5-7-10V6z',
  appointments: 'M7 2v3M17 2v3M3 8h18M4 5h16v16H4z',
  messages: 'M4 4h16v12H8l-4 4z',
  notifications: 'M6 9a6 6 0 1112 0c0 5 2 6 2 6H4s2-1 2-6M10 19a2 2 0 004 0',
  settings: 'M12 15a3 3 0 100-6 3 3 0 000 6zM19 12a7 7 0 00-.1-1l2-1.5-2-3.4-2.3 1a7 7 0 00-1.7-1L14.5 3h-4l-.4 2.6a7 7 0 00-1.7 1l-2.3-1-2 3.4L6 11a7 7 0 000 2l-2 1.5 2 3.4 2.3-1a7 7 0 001.7 1l.4 2.6h4l.4-2.6a7 7 0 001.7-1l2.3 1 2-3.4L18 13c.07-.33.1-.66.1-1z',
  users: 'M16 19v-2a4 4 0 00-8 0v2M12 11a3 3 0 100-6 3 3 0 000 6zM4 19v-2a3 3 0 013-3M20 19v-2a3 3 0 00-3-3',
  audit: 'M4 4h16v16H4zM8 9h8M8 13h8M8 17h5',
  knowledge: 'M4 4h7v16H4zM13 4h7v16h-7z',
  flags: 'M5 3v18M5 4h11l-2 4 2 4H5',
  health: 'M3 12h4l2-5 3 10 2-5h7',
  safety: 'M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6z',
};

const items = computed(() => {
  if (auth.isPatient) {
    return [
      { to: '/patient', label: t('patient.navOverview'), icon: 'overview' },
      { to: '/patient/twin', label: t('patient.navTwin'), icon: 'twin' },
      { to: '/patient/records', label: t('patient.navRecords'), icon: 'records' },
      { to: '/patient/documents', label: t('patient.navDocuments'), icon: 'documents' },
      { to: '/patient/assistant', label: t('patient.navAssistant'), icon: 'assistant' },
      { to: '/patient/recommendations', label: t('patient.navRecommendations'), icon: 'recommendations' },
      { to: '/patient/consent', label: t('patient.navConsent'), icon: 'consent' },
      { to: '/patient/appointments', label: t('patient.navAppointments'), icon: 'appointments' },
      { to: '/patient/messages', label: t('patient.navMessages'), icon: 'messages' },
      { to: '/patient/notifications', label: t('patient.navNotifications'), icon: 'notifications' },
      { to: '/patient/settings', label: t('patient.navSettings'), icon: 'settings' },
    ];
  }
  if (auth.isDoctor) {
    return [
      { to: '/doctor', label: t('doctor.navOverview'), icon: 'overview' },
      { to: '/doctor/patients', label: t('doctor.navPatients'), icon: 'users' },
      { to: '/doctor/appointments', label: t('doctor.navAppointments'), icon: 'appointments' },
      { to: '/doctor/messages', label: t('doctor.navMessages'), icon: 'messages' },
      { to: '/doctor/safety', label: t('doctor.safetyEvaluate'), icon: 'safety' },
      { to: '/doctor/settings', label: t('doctor.navSettings'), icon: 'settings' },
    ];
  }
  return [
    { to: '/admin', label: t('admin.navOverview'), icon: 'overview' },
    { to: '/admin/users', label: t('admin.navUsers'), icon: 'users' },
    { to: '/admin/consent', label: t('admin.navConsent'), icon: 'consent' },
    { to: '/admin/knowledge', label: t('admin.navKnowledge'), icon: 'knowledge' },
    { to: '/admin/audit', label: t('admin.navAudit'), icon: 'audit' },
    { to: '/admin/flags', label: t('admin.navFlags'), icon: 'flags' },
    { to: '/admin/health', label: t('admin.navHealth'), icon: 'health' },
  ];
});

const roleLabel = computed(() =>
  auth.isPatient ? 'Patient portal' : auth.isDoctor ? 'Clinician workspace' : 'Administration',
);

const pageTitle = computed(() => {
  const match = items.value.find((i) => i.to === route.path);
  if (match) return match.label;
  if (auth.isDoctor) return 'Doctor Dashboard';
  if (auth.isAdmin) return 'Admin Dashboard';
  return 'Dashboard';
});

const isActive = (to: string) =>
  route.path === to || (to !== '/patient' && to !== '/doctor' && to !== '/admin' && route.path.startsWith(`${to}/`));

async function loadNotifications() {
  try {
    notifications.value = await connect.notifications();
  } catch {
    notifications.value = { unread: 0, results: [] };
  }
}

async function signOut() {
  await auth.logout();
  router.push('/');
}

function pickLocale(code: LocaleCode) {
  ui.setLocale(code);
  langOpen.value = false;
}

onMounted(loadNotifications);
</script>

<template>
  <div class="flex min-h-screen bg-transparent">
    <!-- Sidebar -->
    <aside
      class="fixed inset-y-0 left-0 z-40 flex w-[248px] flex-col border-r border-ink-200/70 bg-white transition-transform duration-300 lg:translate-x-0"
      :class="mobileOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <div class="flex h-[76px] items-center gap-3 border-b border-ink-100 px-5">
        <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-white shadow-[0_8px_18px_-10px_rgba(14,145,128,0.9)]">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M2 12h4l2-6 4 12 3-8 2 2h5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </span>
        <div class="leading-tight">
          <p class="text-[16px] font-extrabold tracking-tight text-brand-700">MedTwin<span class="text-brand-500">.ai</span></p>
          <p class="mt-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-ink-400">{{ roleLabel }}</p>
        </div>
      </div>

      <nav class="dash-scroll flex-1 space-y-1.5 overflow-y-auto px-4 py-6">
        <p class="dash-label mb-3 px-3">Workspace</p>
        <RouterLink
          v-for="item in items"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-[13.5px] font-medium transition-all duration-200"
          :class="isActive(item.to)
            ? 'bg-brand-600 text-white shadow-[0_8px_20px_-10px_rgba(14,145,128,0.9)]'
            : 'text-ink-600 hover:bg-brand-50 hover:text-brand-800'"
          @click="mobileOpen = false"
        >
          <svg class="h-[17px] w-[17px] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
            <path :d="ICONS[item.icon]" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <span class="truncate">{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="border-t border-ink-100 p-3">
        <RouterLink
          to="/trust-safety"
          class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium text-ink-500 transition-colors hover:bg-ink-50 hover:text-ink-800"
        >
          <svg class="h-[17px] w-[17px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
            <path d="M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6z" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          {{ t('nav.trust') }}
        </RouterLink>
      </div>
    </aside>

    <div v-if="mobileOpen" class="fixed inset-0 z-30 bg-ink-900/40 lg:hidden" @click="mobileOpen = false" />

    <!-- Content -->
    <div class="flex min-w-0 flex-1 flex-col lg:pl-[248px]">
      <header class="sticky top-0 z-20 flex h-[76px] items-center justify-between gap-3 border-b border-ink-200/70 bg-white/95 px-5 backdrop-blur sm:px-8">
        <div class="flex items-center gap-3">
          <button class="btn-ghost px-2 lg:hidden" :aria-label="t('nav.menu')" @click="mobileOpen = !mobileOpen">☰</button>
          <div class="flex items-center gap-3">
            <RouterLink to="/" class="hidden rounded-xl border border-ink-200 px-3 py-2 text-[11px] font-semibold text-ink-500 transition-colors hover:border-brand-300 hover:text-brand-700 sm:inline-flex">
              MedTwin AI
            </RouterLink>
            <span class="hidden text-ink-300 sm:inline">/</span>
            <div>
              <p class="dash-label hidden sm:block">{{ roleLabel }}</p>
              <h1 class="text-[16px] font-bold tracking-tight text-ink-900">{{ pageTitle }}</h1>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <div class="relative">
            <button class="btn-secondary px-3 py-2 text-xs" :aria-expanded="langOpen" @click="langOpen = !langOpen">
              {{ ui.locale === 'zh' ? '中文' : 'EN' }} <span aria-hidden="true">▾</span>
            </button>
            <Transition name="pop">
              <div v-if="langOpen" class="absolute right-0 mt-2 w-28 overflow-hidden rounded-xl border border-ink-200 bg-white shadow-card">
                <button
                  v-for="option in SUPPORTED_LOCALES"
                  :key="option.code"
                  class="block w-full px-3 py-2 text-left text-sm hover:bg-ink-100"
                  :class="ui.locale === option.code ? 'font-semibold text-brand-700' : 'text-ink-700'"
                  @click="pickLocale(option.code)"
                >
                  {{ option.label }}
                </button>
              </div>
            </Transition>
          </div>

          <RouterLink to="/patient/notifications" class="btn-ghost relative px-2 py-2" :aria-label="t('patient.navNotifications')">
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
              <path :d="ICONS.notifications" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <span
              v-if="notifications.unread"
              class="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white"
            >
              {{ notifications.unread }}
            </span>
          </RouterLink>

          <div class="flex items-center gap-2 rounded-xl border border-ink-200 px-2 py-1.5">
            <span
              class="flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold text-white"
              :style="{ backgroundColor: auth.user?.avatarColor ?? '#0e9180' }"
            >
              {{ auth.user?.initials ?? '—' }}
            </span>
            <div class="hidden leading-tight sm:block">
              <p class="text-xs font-semibold text-ink-800">{{ auth.user?.name }}</p>
              <p class="text-[11px] text-ink-400">{{ auth.user?.role }}</p>
            </div>
          </div>

          <button class="btn-ghost px-2 py-2 text-xs" @click="signOut">{{ t('auth.signOut') }}</button>
        </div>
      </header>

      <main class="flex-1 px-5 py-7 sm:px-8 sm:py-9">
        <div class="mx-auto w-full max-w-[1440px]">
          <RouterView v-slot="{ Component, route: current }">
            <Transition name="page" appear>
              <component :is="Component" :key="current.path" />
            </Transition>
          </RouterView>
        </div>
      </main>

      <footer class="border-t border-ink-200/70 bg-white/60 px-5 py-3.5 sm:px-8">
        <p class="text-[11px] text-ink-400">{{ t('footer.medicalNotice') }}</p>
      </footer>
    </div>
  </div>
</template>
