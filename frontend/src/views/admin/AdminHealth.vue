<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useUiStore } from '@/stores/ui';
import { admin } from '@/api/endpoints';
import { formatDateTime } from '@/composables/useAsync';
import StatCard from '@/components/ui/StatCard.vue';
import type { SystemHealth } from '@/api/types';

const { t } = useI18n();
const ui = useUiStore();

const health = ref<SystemHealth | null>(null);
const loading = ref(true);

const activeModels = computed(() =>
  health.value ? health.value.models.filter((m) => m.isActive).length : 0,
);

async function load() {
  loading.value = true;
  try {
    health.value = await admin.systemHealth();
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div>
    <header class="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-1.5">Runtime monitoring</p>
        <h1 class="text-[26px] font-bold leading-tight tracking-tight text-ink-900">{{ t('admin.systemHealth') }}</h1>
        <p class="mt-1 text-[13px] text-ink-500">Database, AI provider and model versions at a glance.</p>
      </div>
      <div class="flex items-center gap-2">
        <span class="chip border border-ink-200 bg-white text-ink-500">
          <span class="mr-1 inline-block h-1.5 w-1.5 rounded-full" :class="health?.database === 'ok' ? 'bg-brand-500' : 'bg-rose-500'" />
          Database {{ health?.database ?? '—' }}
        </span>
        <button class="btn-secondary px-3 py-1.5 text-xs" @click="load">{{ t('common.refresh') }}</button>
      </div>
    </header>

    <div v-if="loading" class="shimmer h-40 animate-pulse rounded-2xl bg-ink-100" />

    <template v-else-if="health">
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard :label="t('admin.users')" :value="health.counts.users ?? 0" tone="brand" />
        <StatCard :label="t('admin.knowledgeSources')" :value="health.counts.knowledgeSources ?? 0" />
        <StatCard :label="t('admin.events24h')" :value="health.counts.auditEvents24h ?? 0" />
        <StatCard :label="t('admin.denied24h')" :value="health.counts.deniedEvents24h ?? 0" tone="rose" />
      </div>

      <div class="mt-4 grid items-start gap-4 lg:grid-cols-2">
        <!-- Runtime components -->
        <div class="dash-card px-4 py-3.5">
          <div class="flex items-start gap-3">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M5 12a7 7 0 0114 0 7 7 0 01-14 0zM12 9v3l2 2" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">Runtime components</p>
              <p class="dash-section-sub mt-0.5">{{ t('admin.database') }} &amp; {{ t('admin.aiProvider') }}</p>
            </div>
          </div>
          <ul class="mt-3 space-y-2 text-[12.5px]">
            <li class="flex items-center justify-between rounded-xl border border-ink-100 bg-surface-50 px-3 py-2.5">
              <span class="text-ink-600">{{ t('admin.database') }}</span>
              <span class="chip" :class="health.database === 'ok' ? 'bg-brand-50 text-brand-700' : 'bg-rose-50 text-rose-600'">
                <span class="h-1.5 w-1.5 rounded-full" :class="health.database === 'ok' ? 'bg-brand-500' : 'bg-rose-400'" />
                {{ health.database }}
              </span>
            </li>
            <li class="flex items-center justify-between gap-2 rounded-xl border border-ink-100 bg-surface-50 px-3 py-2.5">
              <span class="shrink-0 text-ink-600">{{ t('admin.aiProvider') }}</span>
              <span class="truncate text-right font-semibold text-ink-800">
                {{ health.aiProvider.name }}
                <span class="ml-1 chip bg-lavender-light text-[10.5px] text-lavender-dark">{{ health.aiProvider.mode }}</span>
              </span>
            </li>
            <li class="flex items-center justify-between rounded-xl border border-ink-100 bg-surface-50 px-3 py-2.5">
              <span class="text-ink-600">{{ t('admin.models') }}</span>
              <span class="font-semibold text-ink-800">{{ activeModels }} / {{ health.models.length }} active</span>
            </li>
            <li class="flex items-center justify-between rounded-xl border border-ink-100 bg-surface-50 px-3 py-2.5">
              <span class="text-ink-600">{{ t('common.date') }}</span>
              <span class="font-semibold text-ink-800">{{ formatDateTime(health.generatedAt, ui.locale) }}</span>
            </li>
          </ul>
        </div>

        <!-- Model versions -->
        <div class="dash-card px-4 py-3.5">
          <div class="flex items-start gap-3">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M12 3l8 4.5v9L12 21l-8-4.5v-9zM12 12l8-4.5M12 12v9M12 12L4 7.5" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">{{ t('admin.models') }}</p>
              <p class="dash-section-sub mt-0.5">Detectors, evaluators and language models</p>
            </div>
          </div>
          <ul class="mt-3 space-y-2">
            <li
              v-for="model in health.models"
              :key="model.id"
              class="flex items-center justify-between gap-3 rounded-xl border border-ink-100 px-3 py-2.5 transition-colors hover:border-brand-200"
              :class="model.isActive ? 'bg-brand-50/40' : ''"
            >
              <div class="min-w-0">
                <p class="text-[13px] font-semibold text-ink-900">{{ model.name }} <span class="font-normal text-ink-400">v{{ model.version }}</span></p>
                <p class="mt-0.5 text-[11px] uppercase tracking-wide text-ink-400">{{ model.kind }} · {{ model.provider || 'built-in' }}</p>
              </div>
              <span class="chip shrink-0" :class="model.isActive ? 'bg-brand-50 text-brand-700' : 'bg-surface-100 text-ink-500'">
                <span class="h-1.5 w-1.5 rounded-full" :class="model.isActive ? 'bg-brand-500' : 'bg-ink-300'" />
                {{ model.isActive ? 'Active' : 'Idle' }}
              </span>
            </li>
          </ul>
        </div>
      </div>
    </template>
  </div>
</template>
