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
  {
    label: 'Total system users',
    value: (health.value?.counts.users ?? 0).toLocaleString(),
    icon: 'M16 19v-2a4 4 0 00-8 0v2M12 11a3 3 0 100-6 3 3 0 000 6z',
    tone: 'bg-brand-50 text-brand-700',
  },
  {
    label: 'AI assistant queries',
    value: (health.value?.counts.aiInteractions ?? 0).toLocaleString(),
    icon: 'M4 5h16v11H9l-5 4zM8 9h8M8 12h5',
    tone: 'bg-sky-50 text-sky-700',
  },
  {
    label: 'Low-trust responses',
    value: (health.value?.counts.lowTrustResponses ?? 0).toLocaleString(),
    icon: 'M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6z',
    tone: (health.value?.counts.lowTrustResponses ?? 0) > 0 ? 'bg-amber-50 text-amber-700' : 'bg-brand-50 text-brand-700',
  },
  {
    label: 'Knowledge sources',
    value: String(sources.value.length),
    icon: 'M4 4h7v16H4zM13 4h7v16h-7zM6.5 8h2M15.5 8h2',
    tone: 'bg-violet-50 text-violet-700',
  },
]);

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
    <!-- Header -->
    <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-teal-500 text-white shadow-lift">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M12 3l2 5 5 2-5 2-2 5-2-5-5-2 5-2 2-5zM19 15l1 2.5L22.5 18 20 19l-1 2.5L18 19l-2.5-1L18 15.5z" stroke-linejoin="round" />
          </svg>
        </div>
        <div>
          <h1 class="text-[24px] font-bold leading-tight tracking-tight text-ink-900">Administration</h1>
          <p class="mt-0.5 flex items-center gap-1.5 text-[12px] text-ink-500">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            Knowledge governance, safety events and system oversight
          </p>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <span class="chip border border-ink-200 bg-white px-3 py-1.5 text-ink-500">
          <span class="mr-1 inline-block h-1.5 w-1.5 rounded-full" :class="health?.database === 'ok' ? 'bg-brand-500' : 'bg-rose-500'" />
          Database {{ health?.database ?? 'checking…' }}
        </span>
        <span v-if="health?.aiProvider" class="chip border border-ink-200 bg-white px-3 py-1.5 text-ink-500">
          AI: {{ health.aiProvider.name }} · {{ health.aiProvider.mode }}
        </span>
        <button class="btn-secondary text-xs" @click="load">↻ Refresh</button>
      </div>
    </div>

    <p v-if="error" class="mb-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ error }}</p>
    <div v-if="loading" class="h-64 animate-pulse rounded-2xl bg-ink-100" />

    <template v-else>
      <!-- KPI row -->
      <div class="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div v-for="stat in stats" :key="stat.label" class="dash-card flex items-center gap-3.5 p-4">
          <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl" :class="stat.tone">
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
              <path :d="stat.icon" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <div class="min-w-0">
            <p class="truncate text-[11px] font-medium uppercase tracking-wide text-ink-400">{{ stat.label }}</p>
            <p class="mt-0.5 text-[22px] font-extrabold leading-none tracking-tight text-ink-900">{{ stat.value }}</p>
          </div>
        </div>
      </div>

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
              <p class="dash-section-title">Knowledge Sources</p>
              <p class="dash-section-sub mt-0.5">Approved medical sources and ingestion state</p>
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

        <!-- System status column -->
        <div class="space-y-4">
          <div class="dash-card dash-card-pad">
            <div class="flex items-start gap-3">
              <span class="dash-icon-tile">
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                  <path d="M5 12a7 7 0 0114 0 7 7 0 01-14 0zM12 9v3l2 2" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
              <div>
                <p class="dash-section-title">System status</p>
                <p class="dash-section-sub mt-0.5">Runtime components</p>
              </div>
            </div>
            <ul class="mt-4 space-y-2.5 text-[12.5px]">
              <li class="flex items-center justify-between rounded-xl border border-ink-100 bg-surface-50 px-3 py-2.5">
                <span class="text-ink-600">Database</span>
                <span class="chip" :class="health?.database === 'ok' ? 'bg-brand-50 text-brand-700' : 'bg-rose-50 text-rose-600'">
                  {{ health?.database ?? '—' }}
                </span>
              </li>
              <li v-if="health?.aiProvider" class="flex items-center justify-between gap-2 rounded-xl border border-ink-100 bg-surface-50 px-3 py-2.5">
                <span class="shrink-0 text-ink-600">AI provider</span>
                <span class="truncate text-right font-semibold text-ink-800">{{ health.aiProvider.name }}</span>
              </li>
              <li v-if="health" class="flex items-center justify-between rounded-xl border border-ink-100 bg-surface-50 px-3 py-2.5">
                <span class="text-ink-600">Active models</span>
                <span class="font-semibold text-ink-800">{{ health.models.filter((m) => m.isActive).length }} / {{ health.models.length }}</span>
              </li>
              <li v-if="health?.generatedAt" class="flex items-center justify-between rounded-xl border border-ink-100 bg-surface-50 px-3 py-2.5">
                <span class="text-ink-600">Last report</span>
                <span class="font-semibold text-ink-800">{{ formatDate(health.generatedAt) }}</span>
              </li>
            </ul>
          </div>

          <div class="dash-card dash-card-pad">
            <p class="dash-section-title">Quick actions</p>
            <p class="dash-section-sub mt-0.5">Common governance tasks</p>
            <div class="mt-4 grid gap-2">
              <RouterLink to="/admin/knowledge" class="flex items-center justify-between rounded-xl border border-ink-200 bg-white px-3.5 py-2.5 text-[12.5px] font-medium text-ink-700 transition-all hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-card">
                Manage knowledge sources
                <svg viewBox="0 0 20 20" class="h-3.5 w-3.5 text-ink-300" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 10h12m0 0l-4-4m4 4l-4 4" stroke-linecap="round" stroke-linejoin="round" /></svg>
              </RouterLink>
              <RouterLink to="/admin/users" class="flex items-center justify-between rounded-xl border border-ink-200 bg-white px-3.5 py-2.5 text-[12.5px] font-medium text-ink-700 transition-all hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-card">
                User management
                <svg viewBox="0 0 20 20" class="h-3.5 w-3.5 text-ink-300" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 10h12m0 0l-4-4m4 4l-4 4" stroke-linecap="round" stroke-linejoin="round" /></svg>
              </RouterLink>
              <RouterLink to="/admin/audit" class="flex items-center justify-between rounded-xl border border-ink-200 bg-white px-3.5 py-2.5 text-[12.5px] font-medium text-ink-700 transition-all hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-card">
                Full audit trail
                <svg viewBox="0 0 20 20" class="h-3.5 w-3.5 text-ink-300" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 10h12m0 0l-4-4m4 4l-4 4" stroke-linecap="round" stroke-linejoin="round" /></svg>
              </RouterLink>
              <RouterLink to="/admin/consent" class="flex items-center justify-between rounded-xl border border-ink-200 bg-white px-3.5 py-2.5 text-[12.5px] font-medium text-ink-700 transition-all hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-card">
                Consent records
                <svg viewBox="0 0 20 20" class="h-3.5 w-3.5 text-ink-300" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 10h12m0 0l-4-4m4 4l-4 4" stroke-linecap="round" stroke-linejoin="round" /></svg>
              </RouterLink>
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
