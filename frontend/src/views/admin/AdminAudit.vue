<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useUiStore } from '@/stores/ui';
import { admin } from '@/api/endpoints';
import { formatDateTime } from '@/composables/useAsync';
import AppCard from '@/components/ui/AppCard.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import type { AuditEntry } from '@/api/types';

const { t } = useI18n();
const ui = useUiStore();

const entries = ref<AuditEntry[]>([]);
const action = ref('');
const deniedOnly = ref(false);
const loading = ref(true);

async function load() {
  loading.value = true;
  try {
    entries.value = (await admin.auditLogs({ action: action.value || undefined, outcome: deniedOnly.value ? 'DENIED' : undefined })).results;
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div>
    <header class="mb-6">
      <h1 class="text-2xl font-bold sm:text-3xl">{{ t('admin.auditLogs') }}</h1>
      <p class="muted mt-1">{{ t('admin.auditHint') }}</p>
    </header>

    <AppCard>
      <template #actions>
        <input v-model="action" class="input max-w-44" :placeholder="t('common.filter')" @keyup.enter="load" />
        <label class="flex items-center gap-2 text-xs text-ink-600">
          <input v-model="deniedOnly" type="checkbox" class="h-4 w-4" @change="load" />
          {{ t('admin.deniedOnly') }}
        </label>
      </template>

      <div v-if="loading" class="h-40 animate-pulse rounded-xl bg-ink-100" />

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead class="text-xs uppercase tracking-wide text-ink-500">
            <tr>
              <th class="pb-2">{{ t('common.date') }}</th>
              <th class="pb-2">{{ t('common.actions') }}</th>
              <th class="pb-2">{{ t('admin.users') }}</th>
              <th class="pb-2">{{ t('common.status') }}</th>
              <th class="pb-2">{{ t('common.details') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-ink-100">
            <tr v-for="entry in entries" :key="entry.id">
              <td class="py-2 text-xs text-ink-500">{{ formatDateTime(entry.createdAt, ui.locale) }}</td>
              <td class="py-2 font-medium">{{ entry.action }}</td>
              <td class="py-2 text-ink-600">{{ entry.actorEmail || '—' }}</td>
              <td class="py-2"><StatusBadge :status="entry.outcome" /></td>
              <td class="py-2 text-xs text-ink-400">
                {{ entry.resourceType }}<span v-if="entry.resourceId"> · {{ entry.resourceId.slice(0, 8) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </AppCard>
  </div>
</template>
