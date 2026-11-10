<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { admin } from '@/api/endpoints';
import type { FeatureFlag } from '@/api/types';
import AppCard from '@/components/ui/AppCard.vue';

const { t } = useI18n();

const flags = ref<FeatureFlag[]>([]);
const loading = ref(true);

const STATUSES = ['PLANNED', 'IN_DEVELOPMENT', 'IMPLEMENTED', 'EVALUATED', 'RELEASED'];

async function load() {
  loading.value = true;
  try {
    flags.value = (await admin.featureFlags()).results;
  } finally {
    loading.value = false;
  }
}

async function toggle(flag: FeatureFlag) {
  await admin.updateFeatureFlag(flag.id, { isEnabled: !flag.isEnabled });
  await load();
}

async function setStatus(flag: FeatureFlag, status: string) {
  await admin.updateFeatureFlag(flag.id, { status });
  await load();
}

const TONES: Record<string, string> = {
  PLANNED: 'bg-ink-100 text-ink-600',
  IN_DEVELOPMENT: 'bg-amber-50 text-amber-700',
  IMPLEMENTED: 'bg-sky-50 text-sky-700',
  EVALUATED: 'bg-violet-50 text-violet-700',
  RELEASED: 'bg-emerald-50 text-emerald-700',
};

onMounted(load);
</script>

<template>
  <div>
    <header class="mb-6">
      <h1 class="text-2xl font-bold sm:text-3xl">{{ t('admin.featureFlags') }}</h1>
      <p class="muted mt-1">{{ t('admin.flagHint') }}</p>
    </header>

    <AppCard>
      <div v-if="loading" class="h-40 animate-pulse rounded-xl bg-ink-100" />
      <ul v-else class="divide-y divide-ink-100">
        <li v-for="flag in flags" :key="flag.id" class="flex flex-wrap items-center justify-between gap-3 py-3">
          <div class="min-w-0">
            <p class="text-sm font-medium">{{ flag.label || flag.key }}</p>
            <p class="muted mt-0.5">{{ flag.description }}</p>
          </div>
          <div class="flex shrink-0 flex-wrap items-center gap-2">
            <span class="chip" :class="TONES[flag.status] ?? 'bg-ink-100 text-ink-600'">{{ flag.status }}</span>
            <select
              class="input max-w-44 py-1.5 text-xs"
              :value="flag.status"
              @change="setStatus(flag, ($event.target as HTMLSelectElement).value)"
            >
              <option v-for="status in STATUSES" :key="status" :value="status">{{ status }}</option>
            </select>
            <button
              class="btn-secondary px-3 py-1.5 text-xs"
              :class="flag.isEnabled ? 'border-brand-500 text-brand-700' : ''"
              @click="toggle(flag)"
            >
              {{ flag.isEnabled ? t('status.ACTIVE') : t('common.none') }}
            </button>
          </div>
        </li>
      </ul>
    </AppCard>
  </div>
</template>
