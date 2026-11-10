<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { admin } from '@/api/endpoints';
import { formatDate } from '@/composables/useAsync';
import type { AuditEntry, KnowledgeSource, SystemHealth } from '@/api/types';

const health = ref<SystemHealth | null>(null);
const sources = ref<KnowledgeSource[]>([]);
const logs = ref<AuditEntry[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

const stats = computed(() => [
  { label: 'Total system users', value: (health.value?.counts.users ?? 0).toLocaleString(), icon: 'users' },
  { label: 'AI assistant queries', value: (health.value?.counts.aiInteractions ?? 0).toLocaleString(), icon: 'assistant' },
  { label: 'Low-trust responses', value: (health.value?.counts.lowTrustResponses ?? 0).toLocaleString(), icon: 'safety' },
]);

const ICONS: Record<string, string> = {
  users: 'M16 19v-2a4 4 0 00-8 0v2M12 11a3 3 0 100-6 3 3 0 000 6zM4 19v-2a3 3 0 013-3M20 19v-2a3 3 0 00-3-3',
  assistant: 'M4 5h16v11H9l-5 4z',
  safety: 'M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6z',
};

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const [h, s, l] = await Promise.all([
      admin.systemHealth(),
      admin.knowledgeSources(),
      admin.auditLogs(),
    ]);
    health.value = h;
    sources.value = s.results;
    logs.value = l.results.slice(0, 6);
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

onMounted(load);

function approved(status: string) {
  return status === 'APPROVED' || status === 'ACTIVE' || status === 'VERIFIED';
}
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-2">System oversight</p>
        <h1 class="text-[28px] font-bold leading-tight tracking-tight text-ink-900">Admin Dashboard</h1>
        <p class="mt-2 text-[14px] text-ink-500">Knowledge governance, safety events and system oversight.</p>
      </div>
      <div class="flex items-center gap-2 rounded-xl border border-ink-200 bg-white px-3.5 py-2.5">
        <span class="h-2 w-2 rounded-full" :class="health?.database === 'ok' ? 'bg-brand-500' : 'bg-rose-500'" />
        <div class="leading-tight">
          <p class="dash-label">Database</p>
          <p class="text-[12px] font-semibold text-ink-700">{{ health?.database ?? 'checking…' }}</p>
        </div>
      </div>
    </div>

    <p v-if="error" class="mb-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ error }}</p>
    <div v-if="loading" class="h-64 animate-pulse rounded-2xl bg-ink-100" />

    <template v-else>
      <div class="grid gap-4 xl:grid-cols-[minmax(0,1.8fr)_minmax(0,0.75fr)]">
        <!-- Knowledge sources -->
        <div class="dash-card overflow-hidden">
          <div class="flex items-start gap-3 border-b border-ink-100 px-5 py-4">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M4 4h7v16H4zM13 4h7v16h-7zM6.5 8h2M15.5 8h2" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">Source Title</p>
              <p class="dash-section-sub mt-0.5">Approved medical knowledge sources and ingestion state</p>
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="dash-table-compact w-full min-w-[560px] border-collapse">
              <thead class="bg-surface-50">
                <tr>
                  <th class="dash-th">Source Title</th>
                  <th class="dash-th">Approval Status</th>
                  <th class="dash-th">Ingestion Date</th>
                  <th class="dash-th">Chunk Count</th>
                  <th class="dash-th">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="source in sources" :key="source.id" class="dash-row">
                  <td class="dash-td font-medium text-ink-800">{{ source.title }}</td>
                  <td class="dash-td">
                    <span class="chip" :class="approved(source.reviewStatus) ? 'bg-brand-50 text-brand-700' : 'bg-amber-50 text-amber-700'">
                      {{ approved(source.reviewStatus) ? 'Approved' : source.reviewStatus || 'Pending' }}
                    </span>
                  </td>
                  <td class="dash-td">{{ formatDate(source.ingestedAt ?? source.createdAt) }}</td>
                  <td class="dash-td">{{ source.chunkCount }}</td>
                  <td class="dash-td">
                    <RouterLink to="/admin/knowledge" class="inline-block rounded-lg bg-brand-600 px-3 py-1.5 text-[11px] font-semibold text-white transition-colors hover:bg-brand-700">
                      {{ approved(source.reviewStatus) ? 'View' : 'Review' }}
                    </RouterLink>
                  </td>
                </tr>
                <tr v-if="!sources.length">
                  <td colspan="5" class="dash-td py-8 text-center text-ink-400">No knowledge sources registered.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Stat cards -->
        <div class="space-y-4">
          <div v-for="stat in stats" :key="stat.label" class="dash-card flex items-center gap-4 bg-gradient-to-br from-brand-50/70 to-white p-5">
            <span class="dash-icon-tile h-12 w-12 bg-white">
              <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
                <path :d="ICONS[stat.icon]" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="dash-label">{{ stat.label }}</p>
              <p class="mt-1 text-[26px] font-extrabold leading-none tracking-tight text-ink-900">{{ stat.value }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Safety event log -->
      <div class="dash-card mt-4 overflow-hidden">
        <div class="flex items-center justify-between border-b border-ink-100 px-5 py-4">
          <div class="flex items-center gap-3">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M4 4h16v16H4zM8 9h8M8 13h8M8 17h5" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">Safety Event Log</p>
              <p class="dash-section-sub mt-0.5">Recent audited system activity</p>
            </div>
          </div>
          <RouterLink to="/admin/audit" class="text-xs font-semibold text-brand-700 hover:underline">View all →</RouterLink>
        </div>
        <div class="overflow-x-auto">
          <table class="dash-table-compact w-full min-w-[620px] border-collapse">
            <thead class="bg-surface-50">
              <tr>
                <th class="dash-th">Time</th>
                <th class="dash-th">Event</th>
                <th class="dash-th">Actor</th>
                <th class="dash-th">Level</th>
                <th class="dash-th">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="entry in logs" :key="entry.id" class="dash-row">
                <td class="dash-td">{{ formatDate(entry.createdAt) }}</td>
                <td class="dash-td font-medium text-ink-800">{{ entry.action.replaceAll('_', ' ') }}</td>
                <td class="dash-td text-ink-500">{{ entry.actorEmail || 'system' }}</td>
                <td class="dash-td">{{ entry.resourceType || '—' }}</td>
                <td class="dash-td">
                  <span class="chip" :class="entry.outcome === 'SUCCESS' ? 'bg-brand-50 text-brand-700' : 'bg-rose-50 text-rose-600'">
                    {{ entry.outcome }}
                  </span>
                </td>
              </tr>
              <tr v-if="!logs.length">
                <td colspan="5" class="dash-td py-8 text-center text-ink-400">No recent safety events.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="flex flex-wrap justify-end gap-2 border-t border-ink-100 px-4 py-3">
          <RouterLink to="/admin/knowledge" class="btn-secondary text-xs">＋ Add source</RouterLink>
          <RouterLink to="/admin/knowledge" class="btn-secondary text-xs">↻ Re-index source</RouterLink>
          <RouterLink to="/admin/knowledge" class="dash-btn text-xs">View chunks</RouterLink>
        </div>
      </div>
    </template>
  </div>
</template>
