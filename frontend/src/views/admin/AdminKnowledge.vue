<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { admin } from '@/api/endpoints';
import type { KnowledgeSource } from '@/api/types';
import StatusBadge from '@/components/ui/StatusBadge.vue';

const { t } = useI18n();

const sources = ref<KnowledgeSource[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const success = ref(false);
const form = ref({ title: '', publisher: '', sourceUrl: '', category: '', licenseStatus: 'OPEN', reviewStatus: 'PENDING' });

const approvedCount = computed(() => sources.value.filter((s) => s.reviewStatus === 'APPROVED').length);
const pendingCount = computed(() => sources.value.filter((s) => s.reviewStatus === 'PENDING').length);
const totalChunks = computed(() => sources.value.reduce((sum, s) => sum + (s.chunkCount ?? 0), 0));

async function load() {
  loading.value = true;
  try {
    sources.value = (await admin.knowledgeSources()).results;
  } finally {
    loading.value = false;
  }
}

async function create() {
  if (!form.value.title) return;
  error.value = null;
  try {
    await admin.createKnowledgeSource({ ...form.value });
    form.value = { title: '', publisher: '', sourceUrl: '', category: '', licenseStatus: 'OPEN', reviewStatus: 'PENDING' };
    success.value = true;
    setTimeout(() => (success.value = false), 4000);
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
}

async function setReview(source: KnowledgeSource, reviewStatus: string) {
  await admin.updateKnowledgeSource(source.id, { reviewStatus });
  await load();
}

async function remove(source: KnowledgeSource) {
  if (!window.confirm(t('common.confirm'))) return;
  await admin.deleteKnowledgeSource(source.id);
  await load();
}

onMounted(load);
</script>

<template>
  <div>
    <header class="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-1.5">Knowledge governance</p>
        <h1 class="text-[26px] font-bold leading-tight tracking-tight text-ink-900">{{ t('admin.knowledgeSources') }}</h1>
        <p class="mt-1 text-[13px] text-ink-500">{{ t('admin.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-2 text-[11px] font-semibold">
        <span class="chip bg-brand-50 text-brand-700">{{ approvedCount }} approved</span>
        <span class="chip bg-amber-50 text-amber-700">{{ pendingCount }} pending</span>
        <span class="chip bg-surface-100 text-ink-600">{{ totalChunks }} chunks indexed</span>
      </div>
    </header>

    <div class="grid items-start gap-4 lg:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
      <!-- Source list -->
      <div class="dash-card overflow-hidden">
        <div class="flex items-start gap-3 border-b border-ink-100 px-4 py-3.5">
          <span class="dash-icon-tile">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M4 4h7v16H4zM13 4h7v16h-7zM6.5 8h2M15.5 8h2" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <div>
            <p class="dash-section-title">Registered sources</p>
            <p class="dash-section-sub mt-0.5">Approved material feeds every grounded AI answer</p>
          </div>
          <span class="ml-auto chip bg-surface-100 text-ink-500">{{ sources.length }}</span>
        </div>

        <div v-if="loading" class="shimmer h-64 animate-pulse bg-ink-50" />

        <div v-else-if="!sources.length" class="px-4 py-14 text-center">
          <p class="text-[14px] font-semibold text-ink-700">No knowledge sources yet</p>
          <p class="mt-1 text-[12px] text-ink-400">Register the first source to ground the assistant.</p>
        </div>

        <ul v-else class="divide-y divide-ink-100">
          <li v-for="source in sources" :key="source.id" class="flex flex-wrap items-center justify-between gap-3 px-4 py-3.5 transition-colors hover:bg-surface-50/70">
            <div class="min-w-0">
              <p class="text-[14px] font-semibold text-ink-900">{{ source.title }}</p>
              <p class="mt-0.5 text-[12px] text-ink-400">{{ source.publisher }} · {{ source.category || 'Uncategorised' }}</p>
              <span class="mt-1.5 inline-block chip bg-surface-100 text-[10.5px] text-ink-500">{{ source.chunkCount }} chunks</span>
            </div>
            <div class="flex shrink-0 flex-wrap items-center justify-end gap-2">
              <StatusBadge :status="source.reviewStatus" />
              <select
                class="input w-32 py-1.5 text-xs"
                :class="source.reviewStatus === 'APPROVED' ? 'border-brand-300' : ''"
                :value="source.reviewStatus"
                @change="setReview(source, ($event.target as HTMLSelectElement).value)"
              >
                <option value="PENDING">{{ t('status.PENDING') }}</option>
                <option value="APPROVED">{{ t('admin.approved') }}</option>
                <option value="REJECTED">{{ t('status.REJECTED') }}</option>
              </select>
              <button
                class="rounded-lg border border-rose-200 px-3 py-1.5 text-[11px] font-semibold text-rose-600 transition-colors hover:bg-rose-50"
                @click="remove(source)"
              >Delete</button>
            </div>
          </li>
        </ul>
      </div>

      <!-- Register form -->
      <div class="dash-card px-4 py-3.5">
        <div class="flex items-start gap-3">
          <span class="dash-icon-tile">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M12 5v14M5 12h14" stroke-linecap="round" />
            </svg>
          </span>
          <div>
            <p class="dash-section-title">{{ t('admin.addSource') }}</p>
            <p class="dash-section-sub mt-0.5">New sources start as pending review</p>
          </div>
        </div>

        <form class="mt-3 space-y-3" @submit.prevent="create">
          <div>
            <label class="label" for="k-title">{{ t('common.details') }}</label>
            <input id="k-title" v-model="form.title" class="input py-2 text-[13px]" required />
          </div>
          <div>
            <label class="label" for="k-publisher">Publisher</label>
            <input id="k-publisher" v-model="form.publisher" class="input py-2 text-[13px]" />
          </div>
          <div>
            <label class="label" for="k-url">URL</label>
            <input id="k-url" v-model="form.sourceUrl" class="input py-2 text-[13px]" type="url" placeholder="https://…" />
          </div>
          <div>
            <label class="label" for="k-category">{{ t('common.filter') }}</label>
            <input id="k-category" v-model="form.category" class="input py-2 text-[13px]" />
          </div>
          <button class="dash-btn w-full py-2 text-xs" type="submit">{{ t('admin.addSource') }}</button>
          <div v-if="success" class="flex items-center gap-2 rounded-xl border border-brand-200 bg-brand-50 px-3 py-2 text-[11.5px] font-semibold text-brand-700">
            <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">
              <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            Source registered — pending review.
          </div>
          <p v-else-if="!error" class="text-[11px] text-ink-400">Only approved sources are used by the AI assistant.</p>
        </form>
      </div>
    </div>
  </div>
</template>
