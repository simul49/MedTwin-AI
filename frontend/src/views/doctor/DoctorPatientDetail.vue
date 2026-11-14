<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useUiStore } from '@/stores/ui';
import { doctor } from '@/api/endpoints';
import { formatDate } from '@/composables/useAsync';
import EmptyState from '@/components/ui/EmptyState.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import type { HealthRecord } from '@/api/types';

const { t } = useI18n();
const route = useRoute();
const ui = useUiStore();

const patientId = computed(() => String(route.params.id));
const summary = ref<Awaited<ReturnType<typeof doctor.summary>> | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const draft = ref<HealthRecord | null>(null);
const generating = ref(false);

const SCOPE_LABELS: Record<string, string> = {
  profile: 'Profile',
  conditions: 'Conditions',
  medications: 'Medications',
  allergies: 'Allergies',
  lab_results: 'Lab results',
  documents: 'Documents',
  timeline: 'Timeline',
};

const initials = computed(() =>
  (summary.value?.patient.name ?? '')
    .split(' ')
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase(),
);

const tabs = [
  { key: 'records', label: t('doctor.records') },
  { key: 'observations', label: t('patient.openFlags') },
  { key: 'medications', label: t('patient.activeMeds') },
  { key: 'allergies', label: t('patient.allergies') },
  { key: 'documents', label: t('doctor.documents') },
  { key: 'timeline', label: t('doctor.timeline') },
];
const tab = ref('records');

async function load() {
  loading.value = true;
  error.value = null;
  try {
    summary.value = await doctor.summary(patientId.value);
    draft.value = summary.value.draftSummary;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

async function generateDraft() {
  generating.value = true;
  try {
    draft.value = await doctor.createDraftSummary(patientId.value);
  } finally {
    generating.value = false;
  }
}

function download(documentId: string) {
  window.open(`/api/v1/patient/documents/${documentId}/file/`, '_blank');
}

watch(patientId, load);
onMounted(load);
</script>

<template>
  <div>
    <!-- Patient header -->
    <header class="dash-card mb-4 flex flex-wrap items-center gap-4 px-4 py-3.5">
      <RouterLink
        to="/doctor/patients"
        class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-ink-200 bg-white text-ink-500 transition-colors hover:border-brand-300 hover:text-brand-700"
        :aria-label="t('doctor.authorizedPatients')"
      >
        <svg class="h-4 w-4" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12.5 4 7 10l5.5 6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </RouterLink>

      <span
        v-if="initials"
        class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-700 to-brand-500 text-[13px] font-bold text-white shadow-card"
      >
        {{ initials }}
      </span>
      <div class="min-w-0">
        <p class="dash-kicker mb-0.5">Patient chart</p>
        <h1 class="text-[22px] font-bold leading-tight tracking-tight text-ink-900">
          {{ summary?.patient.name ?? t('common.loading') }}
        </h1>
        <div v-if="summary" class="mt-1 flex flex-wrap items-center gap-1.5">
          <span
            v-for="key in summary.scope"
            :key="key"
            class="chip bg-brand-50/70 px-2 py-0.5 text-[10.5px] font-medium text-brand-700"
          >{{ SCOPE_LABELS[key] ?? key }}</span>
        </div>
      </div>

      <button class="dash-btn ml-auto shrink-0 px-4 py-2 text-xs" :disabled="generating" @click="generateDraft">
        <svg class="mr-1.5 inline-block h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
          <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5zM19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z" stroke-linejoin="round" />
        </svg>
        {{ generating ? t('common.loading') : t('doctor.generateDraft') }}
      </button>
    </header>

    <p v-if="error" class="dash-card mb-4 border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ error }}</p>
    <div v-else-if="loading" class="shimmer h-48 animate-pulse rounded-2xl bg-ink-100" />

    <template v-else-if="summary">
      <!-- AI draft summary -->
      <div v-if="draft" class="dash-card mb-4 overflow-hidden border-lavender bg-lavender-light/25 px-4 py-3.5">
        <div class="flex flex-wrap items-center gap-2.5 border-b border-lavender pb-2.5">
          <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-lavender-dark text-white">
            <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5zM19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z" stroke-linejoin="round" />
            </svg>
          </span>
          <p class="text-[13px] font-bold text-lavender-dark">{{ draft.title }}</p>
          <StatusBadge status="AI_GENERATED" />
        </div>
        <p class="mt-3 whitespace-pre-wrap text-[13px] leading-relaxed text-ink-800">{{ draft.summary }}</p>
        <p class="mt-3 flex items-start gap-1.5 rounded-lg bg-lavender-light px-3 py-2 text-[11.5px] font-semibold text-lavender-dark">
          <svg class="mt-0.5 h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          {{ t('doctor.draftWarning') }}
        </p>
      </div>

      <!-- Tabs -->
      <div class="mb-3 flex flex-wrap gap-1.5">
        <button
          v-for="item in tabs"
          :key="item.key"
          class="rounded-lg px-3 py-1.5 text-[11.5px] font-semibold transition-colors"
          :class="tab === item.key ? 'bg-brand-600 text-white shadow-card' : 'bg-white text-ink-600 ring-1 ring-ink-200 hover:ring-ink-300'"
          @click="tab = item.key"
        >
          {{ item.label }}
        </button>
      </div>

      <div class="dash-card overflow-hidden">
        <!-- Records -->
        <EmptyState v-if="tab === 'records' && !summary.records.length" :title="t('common.empty')" icon="◍" />
        <ul v-else-if="tab === 'records'" class="divide-y divide-ink-100">
          <li v-for="record in summary.records" :key="record.id" class="flex flex-wrap items-start justify-between gap-3 px-4 py-2.5 transition-colors hover:bg-surface-50/70">
            <div class="min-w-0">
              <p class="text-[13.5px] font-semibold text-ink-900">{{ record.title }}</p>
              <p v-if="record.summary" class="mt-0.5 text-[12px] text-ink-500">{{ record.summary }}</p>
            </div>
            <div class="flex shrink-0 items-center gap-2">
              <span class="text-[11px] text-ink-400">{{ formatDate(record.recordedAt, ui.locale) }}</span>
              <StatusBadge :status="record.verificationStatus" />
            </div>
          </li>
        </ul>

        <!-- Out-of-range observations -->
        <EmptyState v-else-if="tab === 'observations' && !summary.observations.length" :title="t('common.empty')" icon="◍" />
        <ul v-else-if="tab === 'observations'" class="divide-y divide-ink-100">
          <li v-for="obs in summary.observations" :key="obs.id" class="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 transition-colors hover:bg-surface-50/70">
            <div class="min-w-0">
              <p class="text-[13.5px] font-semibold text-ink-900">{{ obs.label }}</p>
              <p class="text-[11px] text-ink-400">{{ formatDate(obs.observedAt, ui.locale) }}</p>
            </div>
            <div class="flex shrink-0 items-center gap-2.5">
              <span class="text-[13px] font-bold text-ink-800">{{ obs.displayValue }}</span>
              <StatusBadge :status="obs.flag" />
            </div>
          </li>
        </ul>

        <!-- Medications -->
        <EmptyState v-else-if="tab === 'medications' && !summary.medications.length" :title="t('common.empty')" icon="◍" />
        <ul v-else-if="tab === 'medications'" class="divide-y divide-ink-100">
          <li v-for="med in summary.medications" :key="med.id" class="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 transition-colors hover:bg-surface-50/70">
            <div class="flex min-w-0 items-center gap-2.5">
              <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                  <path d="M10.5 20.5 3.5 13.5a2.1 2.1 0 010-3l7-7 7 7-7 10zM7 7l10 10" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
              <div>
                <p class="text-[13.5px] font-semibold text-ink-900">{{ med.name }} <span class="font-normal text-ink-500">{{ med.dose }}</span></p>
                <p class="text-[11.5px] text-ink-400">{{ med.frequency }}</p>
              </div>
            </div>
            <span class="chip shrink-0 bg-brand-50 text-[10.5px] font-semibold text-brand-700">Active</span>
          </li>
        </ul>

        <!-- Allergies -->
        <EmptyState v-else-if="tab === 'allergies' && !summary.allergies.length" :title="t('common.empty')" icon="◍" />
        <ul v-else-if="tab === 'allergies'" class="divide-y divide-ink-100">
          <li v-for="allergy in summary.allergies" :key="allergy.id" class="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 transition-colors hover:bg-rose-50/50">
            <div class="flex min-w-0 items-center gap-2.5">
              <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-rose-100 text-rose-600">
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                  <path d="M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
              <div>
                <p class="text-[13.5px] font-semibold text-ink-900">{{ allergy.substance }}</p>
                <p class="text-[11.5px] text-ink-500">{{ allergy.reaction }}</p>
              </div>
            </div>
            <span class="chip shrink-0 bg-rose-50 text-[10.5px] font-semibold text-rose-600">On file</span>
          </li>
        </ul>

        <!-- Documents -->
        <EmptyState v-else-if="tab === 'documents' && !summary.documents.length" :title="t('common.empty')" icon="◍" />
        <ul v-else-if="tab === 'documents'" class="divide-y divide-ink-100">
          <li v-for="document in summary.documents" :key="document.id" class="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 transition-colors hover:bg-surface-50/70">
            <div class="flex min-w-0 items-center gap-2.5">
              <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-surface-100 text-ink-500">
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                  <path d="M14 3H7a1 1 0 00-1 1v16a1 1 0 001 1h10a1 1 0 001-1V7zM14 3v4h4M9 13h6M9 17h4" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
              <p class="truncate text-[13.5px] font-semibold text-ink-900">{{ document.name }}</p>
            </div>
            <button class="btn-secondary shrink-0 px-3 py-1.5 text-[11px]" @click="download(document.id)">
              <svg class="mr-1 inline-block h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              {{ t('common.download') }}
            </button>
          </li>
        </ul>

        <!-- Timeline -->
        <EmptyState v-else-if="!summary.timeline.length" :title="t('common.empty')" icon="◍" />
        <ul v-else class="px-4 py-3">
          <li v-for="(event, index) in summary.timeline" :key="event.id" class="relative flex gap-3 pb-4 last:pb-0">
            <span
              v-if="index < summary.timeline.length - 1"
              class="absolute left-[7px] top-4 h-full w-px bg-ink-100"
              aria-hidden="true"
            />
            <span class="relative mt-1 h-3.5 w-3.5 shrink-0 rounded-full border-2 border-brand-500 bg-white" />
            <div class="min-w-0">
              <p class="text-[13.5px] font-semibold text-ink-900">{{ event.title }}</p>
              <p v-if="event.description" class="mt-0.5 text-[12px] text-ink-500">{{ event.description }}</p>
              <p class="mt-0.5 text-[11px] text-ink-400">{{ formatDate(event.occurredAt, ui.locale) }}</p>
            </div>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>
