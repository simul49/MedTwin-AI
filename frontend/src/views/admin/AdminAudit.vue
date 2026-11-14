<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useUiStore } from '@/stores/ui';
import { admin } from '@/api/endpoints';
import { formatDateTime } from '@/composables/useAsync';
import type { AuditEntry } from '@/api/types';

const { t } = useI18n();
const ui = useUiStore();

const entries = ref<AuditEntry[]>([]);
const action = ref('');
const deniedOnly = ref(false);
const loading = ref(true);

const successCount = computed(() => entries.value.filter((e) => e.outcome === 'SUCCESS').length);
const deniedCount = computed(() => entries.value.filter((e) => e.outcome !== 'SUCCESS').length);

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
    <header class="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-1.5">Security &amp; compliance</p>
        <h1 class="text-[26px] font-bold leading-tight tracking-tight text-ink-900">{{ t('admin.auditLogs') }}</h1>
        <p class="mt-1 text-[13px] text-ink-500">{{ t('admin.auditHint') }}</p>
      </div>
      <div class="flex items-center gap-2 text-[11px] font-semibold">
        <span class="chip bg-brand-50 text-brand-700">{{ successCount }} success</span>
        <span class="chip" :class="deniedCount ? 'bg-rose-50 text-rose-600' : 'bg-surface-100 text-ink-500'">{{ deniedCount }} denied</span>
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
            v-model="action"
            class="input w-48 py-1.5 text-xs pl-9"
            :placeholder="t('common.filter')"
            @keyup.enter="load"
          />
        </div>
        <button
          class="rounded-lg border px-3 py-1.5 text-[11px] font-semibold transition-colors"
          :class="deniedOnly ? 'border-rose-300 bg-rose-50 text-rose-600' : 'border-ink-200 bg-white text-ink-600 hover:border-ink-300'"
          @click="deniedOnly = !deniedOnly; load()"
        >
          <span class="mr-1 inline-block h-1.5 w-1.5 rounded-full" :class="deniedOnly ? 'bg-rose-500' : 'bg-ink-300'" />
          {{ t('admin.deniedOnly') }}
        </button>
        <button class="btn-secondary ml-auto px-3 py-1.5 text-xs" @click="load">{{ t('common.refresh') }}</button>
      </div>

      <div v-if="loading" class="shimmer h-72 animate-pulse bg-ink-50" />

      <div v-else-if="!entries.length" class="px-4 py-14 text-center">
        <p class="text-[14px] font-semibold text-ink-700">No audit entries match this filter</p>
        <p class="mt-1 text-[12px] text-ink-400">Clear the filter or search for a different action.</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="dash-table-compact w-full min-w-[640px] border-collapse">
          <thead class="bg-surface-50">
            <tr>
              <th class="dash-th">{{ t('common.date') }}</th>
              <th class="dash-th">{{ t('common.actions') }}</th>
              <th class="dash-th">{{ t('admin.users') }}</th>
              <th class="dash-th">{{ t('common.status') }}</th>
              <th class="dash-th">{{ t('common.details') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in entries" :key="entry.id" class="dash-row">
              <td class="dash-td whitespace-nowrap text-ink-500">{{ formatDateTime(entry.createdAt, ui.locale) }}</td>
              <td class="dash-td font-semibold text-ink-800">{{ entry.action.replaceAll('_', ' ') }}</td>
              <td class="dash-td text-ink-500">{{ entry.actorEmail || 'system' }}</td>
              <td class="dash-td">
                <span
                  class="chip font-semibold"
                  :class="entry.outcome === 'SUCCESS' ? 'bg-brand-50 text-brand-700' : 'bg-rose-50 text-rose-600'"
                >
                  <span class="h-1.5 w-1.5 rounded-full" :class="entry.outcome === 'SUCCESS' ? 'bg-brand-500' : 'bg-rose-400'" />
                  {{ entry.outcome }}
                </span>
              </td>
              <td class="dash-td text-ink-400">
                {{ entry.resourceType }}<span v-if="entry.resourceId"> · {{ entry.resourceId.slice(0, 8) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
