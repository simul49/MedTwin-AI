<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useUiStore } from '@/stores/ui';
import { connect } from '@/api/endpoints';
import { formatDateTime } from '@/composables/useAsync';
import AppCard from '@/components/ui/AppCard.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import type { NotificationItem } from '@/api/types';

const { t } = useI18n();
const ui = useUiStore();

const items = ref<NotificationItem[]>([]);
const unread = ref(0);
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    const result = await connect.notifications();
    items.value = result.results;
    unread.value = result.unread;
  } finally {
    loading.value = false;
  }
}

async function markRead(item: NotificationItem) {
  await connect.markRead(item.id);
  await load();
}

async function markAll() {
  await connect.markAllRead();
  await load();
}

onMounted(load);
</script>

<template>
  <div>
    <header class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold sm:text-3xl">{{ t('patient.notificationsTitle') }}</h1>
        <p class="muted mt-1">{{ unread }} {{ t('patient.notificationsTitle') }}</p>
      </div>
      <button v-if="unread" class="btn-secondary text-xs" @click="markAll">{{ t('patient.markAllRead') }}</button>
    </header>

    <AppCard>
      <div v-if="loading" class="h-32 animate-pulse rounded-xl bg-ink-100" />
      <EmptyState v-else-if="!items.length" :title="t('common.empty')" icon="◔" />
      <ul v-else class="divide-y divide-ink-100">
        <li
          v-for="item in items"
          :key="item.id"
          class="flex items-start justify-between gap-4 py-3"
          :class="item.isRead ? 'opacity-70' : ''"
        >
          <div class="min-w-0">
            <p class="text-sm font-medium">{{ item.title }}</p>
            <p class="muted mt-0.5">{{ item.body }}</p>
            <p class="mt-1 text-xs text-ink-400">{{ formatDateTime(item.createdAt, ui.locale) }}</p>
          </div>
          <div class="flex shrink-0 items-center gap-2">
            <span v-if="!item.isRead" class="chip bg-brand-100 text-brand-700">new</span>
            <button v-if="!item.isRead" class="btn-ghost text-xs" @click="markRead(item)">{{ t('common.confirm') }}</button>
          </div>
        </li>
      </ul>
    </AppCard>
  </div>
</template>
