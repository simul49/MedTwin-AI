<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useUiStore } from '@/stores/ui';
import { doctor } from '@/api/endpoints';
import { formatDate } from '@/composables/useAsync';
import AppCard from '@/components/ui/AppCard.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
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
    <header class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <RouterLink to="/doctor/patients" class="muted hover:underline">← {{ t('doctor.authorizedPatients') }}</RouterLink>
        <h1 class="mt-1 text-2xl font-bold sm:text-3xl">{{ summary?.patient.name ?? t('common.loading') }}</h1>
        <div v-if="summary" class="mt-2 flex flex-wrap gap-1.5">
          <span class="text-xs text-ink-500">{{ t('doctor.scopeLabel') }}:</span>
          <span v-for="key in summary.scope" :key="key" class="chip bg-ink-100 text-ink-600">{{ key }}</span>
        </div>
      </div>
      <button class="btn-secondary text-xs" :disabled="generating" @click="generateDraft">
        {{ generating ? t('common.loading') : t('doctor.generateDraft') }}
      </button>
    </header>

    <p v-if="error" class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ error }}</p>
    <div v-else-if="loading" class="h-40 animate-pulse rounded-2xl bg-ink-100" />

    <template v-else-if="summary">
      <div v-if="draft" class="mb-6 rounded-2xl border border-violet-200 bg-violet-50 p-5">
        <div class="flex items-center justify-between gap-3">
          <p class="text-sm font-semibold text-violet-900">{{ draft.title }}</p>
          <StatusBadge status="AI_GENERATED" />
        </div>
        <p class="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-violet-900">{{ draft.summary }}</p>
        <p class="mt-3 text-xs font-semibold uppercase tracking-wide text-violet-700">{{ t('doctor.draftWarning') }}</p>
      </div>

      <div class="mb-4 flex flex-wrap gap-2">
        <button
          v-for="item in tabs"
          :key="item.key"
          class="chip"
          :class="tab === item.key ? 'bg-brand-600 text-white' : 'bg-ink-100 text-ink-600'"
          @click="tab = item.key"
        >
          {{ item.label }}
        </button>
      </div>

      <AppCard>
        <EmptyState v-if="tab === 'records' && !summary.records.length" :title="t('common.empty')" icon="◍" />
        <ul v-else-if="tab === 'records'" class="divide-y divide-ink-100">
          <li v-for="record in summary.records" :key="record.id" class="flex items-start justify-between gap-4 py-3">
            <div>
              <p class="text-sm font-medium">{{ record.title }}</p>
              <p class="muted mt-0.5">{{ record.summary }}</p>
              <p class="mt-1 text-xs text-ink-400">{{ formatDate(record.recordedAt, ui.locale) }}</p>
            </div>
            <StatusBadge :status="record.verificationStatus" />
          </li>
        </ul>

        <ul v-else-if="tab === 'observations'" class="divide-y divide-ink-100">
          <li v-for="obs in summary.observations" :key="obs.id" class="flex items-center justify-between gap-3 py-3">
            <div>
              <p class="text-sm font-medium">{{ obs.label }}</p>
              <p class="muted mt-0.5">{{ formatDate(obs.observedAt, ui.locale) }}</p>
            </div>
            <div class="text-right">
              <p class="text-sm font-semibold">{{ obs.displayValue }}</p>
              <StatusBadge class="mt-1" :status="obs.flag" />
            </div>
          </li>
        </ul>

        <ul v-else-if="tab === 'medications'" class="space-y-2">
          <li v-for="med in summary.medications" :key="med.id" class="rounded-xl border border-ink-200 px-3 py-2">
            <p class="text-sm font-medium">{{ med.name }} {{ med.dose }}</p>
            <p class="muted mt-0.5">{{ med.frequency }}</p>
          </li>
        </ul>

        <ul v-else-if="tab === 'allergies'" class="space-y-2">
          <li v-for="allergy in summary.allergies" :key="allergy.id" class="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2">
            <p class="text-sm font-medium text-rose-900">{{ allergy.substance }}</p>
            <p class="text-xs text-rose-800">{{ allergy.reaction }}</p>
          </li>
        </ul>

        <ul v-else-if="tab === 'documents'" class="divide-y divide-ink-100">
          <li v-for="document in summary.documents" :key="document.id" class="flex items-center justify-between gap-3 py-3">
            <div>
              <p class="text-sm font-medium">{{ document.name }}</p>
              <p class="muted mt-0.5">{{ t('doctor.documents') }}</p>
            </div>
            <button class="btn-secondary text-xs" @click="download(document.id)">{{ t('common.download') }}</button>
          </li>
        </ul>

        <ul v-else class="divide-y divide-ink-100">
          <li v-for="event in summary.timeline" :key="event.id" class="py-3">
            <p class="text-sm font-medium">{{ event.title }}</p>
            <p class="muted mt-0.5">{{ event.description }}</p>
            <p class="mt-1 text-xs text-ink-400">{{ formatDate(event.occurredAt, ui.locale) }}</p>
          </li>
        </ul>
      </AppCard>
    </template>
  </div>
</template>
