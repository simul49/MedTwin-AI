<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useUiStore } from '@/stores/ui';
import { admin } from '@/api/endpoints';
import { formatDateTime } from '@/composables/useAsync';
import StatCard from '@/components/ui/StatCard.vue';
import AppCard from '@/components/ui/AppCard.vue';
import type { SystemHealth } from '@/api/types';

const { t } = useI18n();
const ui = useUiStore();

const health = ref<SystemHealth | null>(null);
const loading = ref(true);

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
    <header class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <h1 class="text-2xl font-bold sm:text-3xl">{{ t('admin.systemHealth') }}</h1>
      <button class="btn-secondary text-xs" @click="load">{{ t('common.refresh') }}</button>
    </header>

    <div v-if="loading" class="h-40 animate-pulse rounded-2xl bg-ink-100" />

    <template v-else-if="health">
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard :label="t('admin.users')" :value="health.counts.users ?? 0" tone="brand" />
        <StatCard :label="t('admin.knowledgeSources')" :value="health.counts.knowledgeSources ?? 0" />
        <StatCard :label="t('admin.events24h')" :value="health.counts.auditEvents24h ?? 0" />
        <StatCard :label="t('admin.denied24h')" :value="health.counts.deniedEvents24h ?? 0" tone="rose" />
      </div>

      <div class="mt-6 grid gap-6 lg:grid-cols-2">
        <AppCard :title="t('admin.database')">
          <dl class="space-y-2 text-sm">
            <div class="flex justify-between"><dt class="muted">{{ t('admin.database') }}</dt><dd>{{ health.database }}</dd></div>
            <div class="flex justify-between">
              <dt class="muted">{{ t('admin.aiProvider') }}</dt>
              <dd>{{ health.aiProvider.name }} ({{ health.aiProvider.mode }})</dd>
            </div>
            <div class="flex justify-between">
              <dt class="muted">{{ t('common.date') }}</dt>
              <dd>{{ formatDateTime(health.generatedAt, ui.locale) }}</dd>
            </div>
          </dl>
        </AppCard>

        <AppCard :title="t('admin.models')">
          <ul class="space-y-2">
            <li v-for="model in health.models" :key="model.id" class="rounded-xl border border-ink-200 px-3 py-2">
              <p class="text-sm font-medium">{{ model.name }} <span class="text-ink-400">v{{ model.version }}</span></p>
              <p class="muted mt-0.5">{{ model.kind }} · {{ model.provider || 'built-in' }}</p>
            </li>
          </ul>
        </AppCard>
      </div>
    </template>
  </div>
</template>
