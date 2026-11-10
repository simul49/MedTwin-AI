<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { admin } from '@/api/endpoints';
import type { KnowledgeSource } from '@/api/types';
import AppCard from '@/components/ui/AppCard.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';

const { t } = useI18n();

const sources = ref<KnowledgeSource[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const form = ref({ title: '', publisher: '', sourceUrl: '', category: '', licenseStatus: 'OPEN', reviewStatus: 'PENDING' });

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
    <header class="mb-6">
      <h1 class="text-2xl font-bold sm:text-3xl">{{ t('admin.knowledgeSources') }}</h1>
      <p class="muted mt-1">{{ t('admin.subtitle') }}</p>
    </header>

    <div class="grid gap-6 lg:grid-cols-3">
      <AppCard class="lg:col-span-2" :title="t('admin.knowledgeSources')">
        <p v-if="error" class="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ error }}</p>
        <div v-else-if="loading" class="h-40 animate-pulse rounded-xl bg-ink-100" />

        <ul v-else class="divide-y divide-ink-100">
          <li v-for="source in sources" :key="source.id" class="flex flex-wrap items-center justify-between gap-3 py-3">
            <div class="min-w-0">
              <p class="text-sm font-medium">{{ source.title }}</p>
              <p class="muted mt-0.5">{{ source.publisher }} · {{ source.category }}</p>
              <p class="mt-1 text-xs text-ink-400">{{ source.chunkCount }} {{ t('admin.chunkCount') }}</p>
            </div>
            <div class="flex shrink-0 flex-wrap items-center gap-2">
              <StatusBadge :status="source.reviewStatus" />
              <select
                class="input max-w-36 py-1.5 text-xs"
                :value="source.reviewStatus"
                @change="setReview(source, ($event.target as HTMLSelectElement).value)"
              >
                <option value="PENDING">{{ t('status.PENDING') }}</option>
                <option value="APPROVED">{{ t('admin.approved') }}</option>
                <option value="REJECTED">{{ t('status.REJECTED') }}</option>
              </select>
              <button class="btn-ghost text-xs text-rose-600" @click="remove(source)">{{ t('common.delete') }}</button>
            </div>
          </li>
        </ul>
      </AppCard>

      <AppCard :title="t('admin.addSource')">
        <form class="space-y-3" @submit.prevent="create">
          <div>
            <label class="label" for="k-title">{{ t('common.details') }}</label>
            <input id="k-title" v-model="form.title" class="input" required />
          </div>
          <div>
            <label class="label" for="k-publisher">Publisher</label>
            <input id="k-publisher" v-model="form.publisher" class="input" />
          </div>
          <div>
            <label class="label" for="k-url">URL</label>
            <input id="k-url" v-model="form.sourceUrl" class="input" />
          </div>
          <div>
            <label class="label" for="k-category">{{ t('common.filter') }}</label>
            <input id="k-category" v-model="form.category" class="input" />
          </div>
          <button class="btn-primary w-full text-sm" type="submit">{{ t('admin.addSource') }}</button>
        </form>
      </AppCard>
    </div>
  </div>
</template>
