<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useUiStore } from '@/stores/ui';
import { patient } from '@/api/endpoints';
import { formatDate } from '@/composables/useAsync';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import type { HealthRecord } from '@/api/types';

const { t } = useI18n();
const ui = useUiStore();

const category = ref('');
const query = ref('');
const records = ref<HealthRecord[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const expanded = ref<string | null>(null);

const CATEGORIES = ['CONDITION', 'ALLERGY', 'MEDICATION', 'LAB_RESULT', 'PROCEDURE', 'IMMUNIZATION', 'NOTE', 'FAMILY_HISTORY', 'VITAL'];

const newRecord = ref({ title: '', category: 'NOTE', summary: '' });
const saving = ref(false);

const filtered = computed(() => records.value);

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const result = await patient.records({ category: category.value || undefined, q: query.value || undefined });
    records.value = result.results;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

async function add() {
  if (!newRecord.value.title.trim()) return;
  saving.value = true;
  error.value = null;
  try {
    await patient.createRecord({ ...newRecord.value });
    newRecord.value = { title: '', category: 'NOTE', summary: '' };
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    saving.value = false;
  }
}

async function remove(record: HealthRecord) {
  if (!window.confirm(t('common.confirm'))) return;
  await patient.deleteRecord(record.id);
  await load();
}

function toggle(id: string) {
  expanded.value = expanded.value === id ? null : id;
}

onMounted(load);
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-2">Digital Twin</p>
        <h1 class="text-[28px] font-bold leading-tight tracking-tight text-ink-900">{{ t('patient.recordsTitle') }}</h1>
        <p class="mt-2 text-[14px] text-ink-500">Every item shows where it came from and who confirmed it.</p>
      </div>
      <span class="chip border border-ink-200 bg-white text-ink-600">{{ records.length }} records</span>
    </div>

    <p v-if="error" class="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-[13px] text-rose-700">{{ error }}</p>

    <div class="grid items-start gap-5 lg:grid-cols-[minmax(0,1.95fr)_minmax(0,0.85fr)]">
      <!-- Records table -->
      <div class="dash-card overflow-hidden">
        <div class="flex flex-wrap items-center justify-between gap-3 border-b border-ink-100 px-5 py-4">
          <div class="flex items-center gap-3">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M7 3h10v18l-5-3-5 3z" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">Health records</p>
              <p class="dash-section-sub mt-0.5">Filter and review your entries</p>
            </div>
          </div>
          <button class="btn-secondary text-xs" @click="load">↻ Refresh</button>
        </div>

        <div class="flex flex-wrap gap-3 border-b border-ink-100 px-5 py-4">
          <select v-model="category" class="input max-w-52 text-xs" aria-label="Category" @change="load">
            <option value="">All categories</option>
            <option v-for="option in CATEGORIES" :key="option" :value="option">{{ option.replaceAll('_', ' ') }}</option>
          </select>
          <input v-model="query" class="input max-w-64 text-xs" :placeholder="t('common.search')" @keyup.enter="load" />
          <button class="dash-btn dash-btn-soft px-4 py-2 text-xs" @click="load">Search</button>
        </div>

        <div v-if="loading" class="h-40 animate-pulse bg-ink-100" />
        <div v-else-if="!filtered.length" class="px-5 py-12 text-center">
          <p class="text-[14px] font-semibold text-ink-700">No records found</p>
          <p class="mt-1 text-[12px] text-ink-400">Try a different filter or add a new record.</p>
        </div>
        <div v-else class="dash-scroll overflow-x-auto">
          <table class="dash-table-compact w-full min-w-[560px] border-collapse">
            <thead>
              <tr>
                <th class="dash-th">Record</th>
                <th class="dash-th">Category</th>
                <th class="dash-th">Source</th>
                <th class="dash-th">Status</th>
                <th class="dash-th">Date</th>
                <th class="dash-th">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="record in filtered" :key="record.id" class="dash-row">
                <td class="dash-td w-[34%]">
                  <p class="block truncate font-semibold text-ink-900" :title="record.title">{{ record.title }}</p>
                  <p class="mt-1 text-[11px] leading-relaxed text-ink-500" :class="expanded === record.id ? '' : 'clamp-2'">
                    {{ record.summary || 'No additional notes.' }}
                  </p>
                  <button
                    v-if="record.summary && record.summary.length > 120"
                    class="mt-1 text-[11px] font-semibold text-brand-700 hover:underline"
                    @click="toggle(record.id)"
                  >
                    {{ expanded === record.id ? 'Show less' : 'Show more' }}
                  </button>
                </td>
                <td class="dash-td"><span class="chip bg-surface-100 text-ink-600">{{ record.category.replaceAll('_', ' ') }}</span></td>
                <td class="dash-td"><StatusBadge :status="record.sourceType" /></td>
                <td class="dash-td"><StatusBadge :status="record.verificationStatus" /></td>
                <td class="dash-td whitespace-nowrap">{{ formatDate(record.recordedAt, ui.locale) }}</td>
                <td class="dash-td">
                  <button class="text-[11px] font-semibold text-rose-600 hover:underline" @click="remove(record)">Delete</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Add record -->
      <div class="dash-card dash-card-pad">
        <div class="flex items-start gap-3">
          <span class="dash-icon-tile">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M12 5v14M5 12h14" stroke-linecap="round" />
            </svg>
          </span>
          <div>
            <p class="dash-section-title">Add a record</p>
            <p class="dash-section-sub mt-0.5">Attributed to you and editable later</p>
          </div>
        </div>

        <form class="mt-5 space-y-4" @submit.prevent="add">
          <div>
            <label class="label" for="r-title">Title</label>
            <input id="r-title" v-model="newRecord.title" class="input" required placeholder="e.g. Annual check-up" />
          </div>
          <div>
            <label class="label" for="r-category">Category</label>
            <select id="r-category" v-model="newRecord.category" class="input">
              <option v-for="option in CATEGORIES" :key="option" :value="option">{{ option.replaceAll('_', ' ') }}</option>
            </select>
          </div>
          <div>
            <label class="label" for="r-summary">Notes</label>
            <textarea id="r-summary" v-model="newRecord.summary" class="input min-h-24" placeholder="Optional details" />
          </div>
          <button class="dash-btn w-full" type="submit" :disabled="saving">{{ saving ? 'Saving…' : 'Save record' }}</button>
        </form>
        <div class="dash-info mt-4">AI-generated drafts are always labelled and require clinician verification before use.</div>
      </div>
    </div>
  </div>
</template>
