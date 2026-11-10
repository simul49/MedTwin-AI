<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useUiStore } from '@/stores/ui';
import { doctor } from '@/api/endpoints';
import { formatDateTime } from '@/composables/useAsync';
import AppCard from '@/components/ui/AppCard.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import type { DoctorPatient } from '@/api/types';

const { t } = useI18n();
const ui = useUiStore();

const patients = ref<DoctorPatient[]>([]);
const query = ref('');
const loading = ref(true);

const filtered = computed(() =>
  patients.value.filter((p) => p.name.toLowerCase().includes(query.value.toLowerCase())),
);

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
    <header class="mb-6">
      <h1 class="text-2xl font-bold sm:text-3xl">{{ t('doctor.authorizedPatients') }}</h1>
      <p class="muted mt-1">{{ t('doctor.subtitle') }}</p>
    </header>

    <AppCard>
      <template #actions>
        <input v-model="query" class="input max-w-56" :placeholder="t('common.search')" />
      </template>

      <div v-if="loading" class="h-40 animate-pulse rounded-xl bg-ink-100" />
      <EmptyState v-else-if="!filtered.length" :title="t('doctor.noPatients')" icon="◇" />

      <div v-else class="grid gap-4 sm:grid-cols-2">
        <RouterLink
          v-for="patient in filtered"
          :key="patient.id"
          :to="`/doctor/patients/${patient.id}`"
          class="card card-pad transition-shadow hover:shadow-lift"
        >
          <div class="flex items-center gap-3">
            <span
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white"
              :style="{ backgroundColor: patient.avatarColor }"
            >
              {{ patient.initials }}
            </span>
            <div class="min-w-0">
              <p class="font-medium">{{ patient.name }}</p>
              <p class="muted mt-0.5">{{ patient.age ?? '—' }} · {{ patient.gender }}</p>
            </div>
          </div>

          <div class="mt-3 flex flex-wrap gap-1.5">
            <span v-for="key in patient.scope" :key="key" class="chip bg-ink-100 text-ink-600">{{ key }}</span>
          </div>

          <div class="mt-3 flex items-center justify-between text-xs text-ink-500">
            <span>{{ patient.recordCount }} {{ t('doctor.records') }}</span>
            <StatusBadge v-if="patient.openFlags" status="HIGH" />
          </div>
          <p v-if="patient.expiresAt" class="mt-1 text-xs text-ink-400">
            {{ t('doctor.expires') }}: {{ formatDateTime(patient.expiresAt, ui.locale) }}
          </p>
        </RouterLink>
      </div>
    </AppCard>
  </div>
</template>
