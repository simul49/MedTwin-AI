<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { admin } from '@/api/endpoints';
import type { FeatureFlag } from '@/api/types';

const { t } = useI18n();

const flags = ref<FeatureFlag[]>([]);
const loading = ref(true);

const STATUSES = ['PLANNED', 'IN_DEVELOPMENT', 'IMPLEMENTED', 'EVALUATED', 'RELEASED'];

const TONES: Record<string, string> = {
  PLANNED: 'bg-ink-100 text-ink-600',
  IN_DEVELOPMENT: 'bg-amber-50 text-amber-700',
  IMPLEMENTED: 'bg-brand-50 text-brand-700',
  EVALUATED: 'bg-lavender-light text-lavender-dark',
  RELEASED: 'bg-brand-600 text-white',
};

const releasedCount = computed(() => flags.value.filter((f) => f.status === 'RELEASED').length);
const activeCount = computed(() => flags.value.filter((f) => f.isEnabled).length);

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

onMounted(load);
</script>

<template>
  <div>
    <header class="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-1.5">Platform roadmap</p>
        <h1 class="text-[26px] font-bold leading-tight tracking-tight text-ink-900">{{ t('admin.featureFlags') }}</h1>
        <p class="mt-1 text-[13px] text-ink-500">{{ t('admin.flagHint') }}</p>
      </div>
      <div class="flex items-center gap-2 text-[11px] font-semibold">
        <span class="chip bg-brand-600 text-white">{{ releasedCount }} released</span>
        <span class="chip bg-brand-50 text-brand-700">{{ activeCount }} enabled</span>
        <span class="chip border border-ink-200 bg-white text-ink-600">{{ flags.length }} total</span>
      </div>
    </header>

    <div class="dash-card overflow-hidden">
      <div class="flex items-start gap-3 border-b border-ink-100 px-4 py-3.5">
        <span class="dash-icon-tile">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
            <path d="M4 4h16v16H4zM8 9h8M8 13h5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </span>
        <div>
          <p class="dash-section-title">Feature status</p>
          <p class="dash-section-sub mt-0.5">Roadmap stage and runtime availability per capability</p>
        </div>
      </div>

      <div v-if="loading" class="shimmer h-72 animate-pulse bg-ink-50" />

      <ul v-else class="divide-y divide-ink-100">
        <li v-for="flag in flags" :key="flag.id" class="flex flex-wrap items-center justify-between gap-3 px-4 py-3 transition-colors hover:bg-surface-50/70">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <p class="text-[14px] font-semibold text-ink-900">{{ flag.label || flag.key }}</p>
              <span class="chip text-[10.5px] font-semibold" :class="TONES[flag.status] ?? 'bg-ink-100 text-ink-600'">
                {{ flag.status.replaceAll('_', ' ') }}
              </span>
            </div>
            <p class="mt-0.5 text-[12px] text-ink-400">{{ flag.description }}</p>
          </div>
          <div class="flex shrink-0 flex-wrap items-center justify-end gap-2">
            <select
              class="input w-44 py-1.5 text-xs"
              :value="flag.status"
              @change="setStatus(flag, ($event.target as HTMLSelectElement).value)"
            >
              <option v-for="status in STATUSES" :key="status" :value="status">{{ status.replaceAll('_', ' ') }}</option>
            </select>
            <button
              class="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[11px] font-semibold transition-colors"
              :class="flag.isEnabled ? 'border-brand-300 bg-brand-50 text-brand-700' : 'border-ink-200 bg-white text-ink-500 hover:border-ink-300'"
              @click="toggle(flag)"
            >
              <span class="h-1.5 w-1.5 rounded-full" :class="flag.isEnabled ? 'bg-brand-500' : 'bg-ink-300'" />
              {{ flag.isEnabled ? t('status.ACTIVE') : t('common.none') }}
            </button>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
