<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useUiStore } from '@/stores/ui';
import { doctor } from '@/api/endpoints';
import { formatDate } from '@/composables/useAsync';
import type { DoctorPatient } from '@/api/types';

const { t } = useI18n();
const ui = useUiStore();

const patients = ref<DoctorPatient[]>([]);
const query = ref('');
const loading = ref(true);

const filtered = computed(() =>
  patients.value.filter((p) => p.name.toLowerCase().includes(query.value.toLowerCase())),
);

const totalRecords = computed(() => patients.value.reduce((sum, p) => sum + (p.recordCount ?? 0), 0));
const flaggedPatients = computed(() => patients.value.filter((p) => (p.openFlags ?? 0) > 0).length);

const SCOPE_LABELS: Record<string, string> = {
  profile: 'Profile',
  conditions: 'Conditions',
  medications: 'Medications',
  allergies: 'Allergies',
  lab_results: 'Lab results',
  documents: 'Documents',
  timeline: 'Timeline',
};

function expiresSoon(value?: string | null): boolean {
  if (!value) return false;
  const days = (new Date(value).getTime() - Date.now()) / 86_400_000;
  return days <= 30;
}

onMounted(async () => {
  try {
    patients.value = (await doctor.patients()).results;
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div>
    <header class="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-1.5">Clinical access</p>
        <h1 class="text-[26px] font-bold leading-tight tracking-tight text-ink-900">{{ t('doctor.authorizedPatients') }}</h1>
        <p class="mt-1 text-[13px] text-ink-500">{{ t('doctor.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-2 text-[11px] font-semibold">
        <span class="chip bg-brand-50 text-brand-700">{{ patients.length }} patient{{ patients.length === 1 ? '' : 's' }}</span>
        <span class="chip bg-lavender-light text-lavender-dark">{{ totalRecords }} records</span>
        <span v-if="flaggedPatients" class="chip bg-amber-50 text-amber-700">{{ flaggedPatients }} with open flags</span>
      </div>
    </header>

    <div class="dash-card overflow-hidden">
      <!-- Toolbar -->
      <div class="flex flex-wrap items-center gap-2.5 border-b border-ink-100 bg-surface-50/60 px-4 py-3">
        <div class="relative">
          <svg class="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M15.5 15.5 21 21M10 18a8 8 0 100-16 8 8 0 000 16z" stroke-linecap="round" />
          </svg>
          <input
            v-model="query"
            class="input w-64 py-1.5 text-xs pl-9"
            :placeholder="`${t('common.search')} patient…`"
          />
        </div>
        <p class="ml-auto text-[11px] text-ink-400">
          {{ filtered.length }} of {{ patients.length }} shown
        </p>
      </div>

      <div v-if="loading" class="shimmer h-64 animate-pulse bg-ink-50" />

      <div v-else-if="!filtered.length" class="px-4 py-16 text-center">
        <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-600">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
            <path d="M16 19v-2a4 4 0 00-8 0v2M12 11a3 3 0 100-6 3 3 0 000 6zM3 21h18" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </span>
        <p class="mt-3 text-[14px] font-semibold text-ink-700">{{ t('doctor.noPatients') }}</p>
        <p class="mt-1 text-[12px] text-ink-400">Patients appear here as soon as they share their records with you.</p>
      </div>

      <ul v-else class="divide-y divide-ink-100">
        <li v-for="patient in filtered" :key="patient.id">
          <RouterLink
            :to="`/doctor/patients/${patient.id}`"
            class="group flex flex-wrap items-center gap-3 px-4 py-2.5 transition-colors hover:bg-surface-50/70"
          >
            <span
              class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-white shadow-card"
              :style="{ backgroundColor: patient.avatarColor }"
            >
              {{ patient.initials }}
            </span>
            <div class="min-w-[140px]">
              <p class="truncate text-[13.5px] font-semibold text-ink-900">{{ patient.name }}</p>
              <p class="text-[11px] text-ink-400">{{ patient.age ?? '—' }} years · {{ patient.gender.toLowerCase() }}</p>
            </div>
            <div class="flex flex-wrap gap-1">
              <span
                v-for="key in patient.scope"
                :key="key"
                class="chip bg-brand-50/70 px-2 py-0.5 text-[10px] font-medium text-brand-700"
              >{{ SCOPE_LABELS[key] ?? key }}</span>
            </div>
            <span class="ml-auto shrink-0 text-[11.5px] font-semibold text-ink-600">{{ patient.recordCount }} records</span>
            <span
              v-if="patient.expiresAt"
              class="flex shrink-0 items-center gap-1 text-[11px]"
              :class="expiresSoon(patient.expiresAt) ? 'font-semibold text-amber-600' : 'text-ink-400'"
            >
              <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M12 8v4l2.5 2.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" />
              </svg>
              {{ t('doctor.expires') }} {{ formatDate(patient.expiresAt, ui.locale) }}
            </span>
            <StatusBadge v-if="patient.openFlags" status="HIGH" />
            <svg viewBox="0 0 20 20" class="h-3.5 w-3.5 shrink-0 text-ink-300 transition-colors group-hover:text-brand-600" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 10h12m0 0l-4-4m4 4l-4 4" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </RouterLink>
        </li>
      </ul>
    </div>
  </div>
</template>
