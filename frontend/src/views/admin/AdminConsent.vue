<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useUiStore } from '@/stores/ui';
import { admin } from '@/api/endpoints';
import { formatDate } from '@/composables/useAsync';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import type { ConsentGrant } from '@/api/types';

const { t } = useI18n();
const ui = useUiStore();

const grants = ref<ConsentGrant[]>([]);
const loading = ref(true);

const activeCount = computed(() => grants.value.filter((g) => g.status === 'ACTIVE').length);
const pendingCount = computed(() => grants.value.filter((g) => g.status === 'PENDING').length);

onMounted(async () => {
  grants.value = (await admin.consentGrants()).results;
  loading.value = false;
});
</script>

<template>
  <div>
    <header class="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-1.5">Consent governance</p>
        <h1 class="text-[26px] font-bold leading-tight tracking-tight text-ink-900">{{ t('admin.navConsent') }}</h1>
        <p class="mt-1 text-[13px] text-ink-500">{{ t('admin.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-2 text-[11px] font-semibold">
        <span class="chip bg-brand-50 text-brand-700">{{ activeCount }} active</span>
        <span class="chip bg-amber-50 text-amber-700">{{ pendingCount }} pending</span>
        <span class="chip border border-ink-200 bg-white text-ink-600">{{ grants.length }} total</span>
      </div>
    </header>

    <div class="dash-card overflow-hidden">
      <div class="flex items-start gap-3 border-b border-ink-100 px-4 py-3.5">
        <span class="dash-icon-tile">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
            <path d="M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6z" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </span>
        <div>
          <p class="dash-section-title">Access grants</p>
          <p class="dash-section-sub mt-0.5">Patient-to-clinician record sharing with scope limits</p>
        </div>
        <span class="ml-auto chip bg-surface-100 text-ink-500">{{ grants.length }}</span>
      </div>

      <div v-if="loading" class="shimmer h-56 animate-pulse bg-ink-50" />

      <div v-else-if="!grants.length" class="px-4 py-14 text-center">
        <p class="text-[14px] font-semibold text-ink-700">No access grants recorded</p>
        <p class="mt-1 text-[12px] text-ink-400">Grants appear when patients share records with clinicians.</p>
      </div>

      <ul v-else class="divide-y divide-ink-100">
        <li v-for="grant in grants" :key="grant.id" class="flex flex-wrap items-center justify-between gap-3 px-4 py-3.5 transition-colors hover:bg-surface-50/70">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <p class="text-[14px] font-semibold text-ink-900">{{ grant.patient?.name ?? '—' }}</p>
              <svg class="h-3.5 w-3.5 text-ink-300" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M4 10h12m0 0l-4-4m4 4l-4 4" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <p class="text-[14px] font-semibold text-ink-900">{{ grant.doctor?.name ?? '—' }}</p>
            </div>
            <p v-if="grant.purpose" class="mt-0.5 text-[12px] text-ink-500">{{ grant.purpose }}</p>
            <div class="mt-2 flex flex-wrap gap-1.5">
              <span v-for="key in grant.scope" :key="key" class="chip bg-surface-100 text-[10.5px] text-ink-500">{{ key }}</span>
            </div>
          </div>
          <div class="shrink-0 text-right">
            <StatusBadge :status="grant.status" />
            <p class="mt-1.5 text-[11px] text-ink-400">Expires {{ formatDate(grant.expiresAt, ui.locale) }}</p>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
