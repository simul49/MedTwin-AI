<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useUiStore } from '@/stores/ui';
import { admin } from '@/api/endpoints';
import { formatDate } from '@/composables/useAsync';
import AppCard from '@/components/ui/AppCard.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import type { ConsentGrant } from '@/api/types';

const { t } = useI18n();
const ui = useUiStore();

const grants = ref<ConsentGrant[]>([]);
const loading = ref(true);

onMounted(async () => {
  grants.value = (await admin.consentGrants()).results;
  loading.value = false;
});
</script>

<template>
  <div>
    <header class="mb-6">
      <h1 class="text-2xl font-bold sm:text-3xl">{{ t('admin.navConsent') }}</h1>
      <p class="muted mt-1">{{ t('admin.subtitle') }}</p>
    </header>

    <AppCard>
      <div v-if="loading" class="h-40 animate-pulse rounded-xl bg-ink-100" />
      <ul v-else class="divide-y divide-ink-100">
        <li v-for="grant in grants" :key="grant.id" class="flex flex-wrap items-center justify-between gap-3 py-3">
          <div>
            <p class="text-sm font-medium">
              {{ grant.patient?.name ?? '—' }} → {{ grant.doctor?.name ?? '—' }}
            </p>
            <p class="muted mt-0.5">{{ grant.purpose }}</p>
            <div class="mt-1.5 flex flex-wrap gap-1.5">
              <span v-for="key in grant.scope" :key="key" class="chip bg-ink-100 text-ink-600">{{ key }}</span>
            </div>
          </div>
          <div class="text-right">
            <StatusBadge :status="grant.status" />
            <p class="mt-1 text-xs text-ink-400">{{ formatDate(grant.expiresAt, ui.locale) }}</p>
          </div>
        </li>
      </ul>
    </AppCard>
  </div>
</template>
