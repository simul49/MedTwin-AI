<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import { consultations } from '@/api/endpoints';
import { formatDateTime } from '@/composables/useAsync';
import type { Consultation } from '@/api/types';

const items = ref<Consultation[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

const STATUS_TONE: Record<string, string> = {
  PAYMENT_PENDING: 'bg-amber-50 text-amber-700',
  SCHEDULED: 'bg-surface-100 text-ink-600',
  PAID: 'bg-brand-50 text-brand-700',
  WAITING_ROOM: 'bg-brand-50 text-brand-700',
  LIVE: 'bg-brand-600 text-white',
  COMPLETED: 'bg-surface-100 text-ink-600',
  CANCELLED: 'bg-rose-50 text-rose-600',
};

const actionable = computed(() =>
  items.value.filter((c) => ['PAID', 'WAITING_ROOM', 'LIVE'].includes(c.status)),
);

async function load() {
  loading.value = true;
  try {
    items.value = (await consultations.list()).results;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div>
    <header class="mb-5">
      <p class="dash-kicker mb-1.5">Paid consultations</p>
      <h1 class="text-[26px] font-bold leading-tight tracking-tight text-ink-900">Consultation rooms</h1>
      <p class="mt-1 text-[13px] text-ink-500">Enter paid video consultations and issue prescriptions after the call.</p>
    </header>

    <p v-if="error" class="dash-card mb-4 border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ error }}</p>

    <div class="dash-card overflow-hidden">
      <div class="flex items-center justify-between border-b border-ink-100 bg-surface-50/60 px-4 py-2.5">
        <p class="text-[12px] font-bold uppercase tracking-wide text-ink-500">All consultations</p>
        <span class="chip bg-surface-100 text-[10.5px] text-ink-500">{{ items.length }}</span>
      </div>

      <div v-if="loading" class="shimmer h-40 animate-pulse bg-ink-50" />

      <div v-else-if="!items.length" class="flex flex-col items-center px-5 py-12 text-center">
        <span class="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-600">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
            <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM4 21a8 8 0 0116 0" stroke-linecap="round" />
          </svg>
        </span>
        <p class="mt-3 text-[13.5px] font-semibold text-ink-700">No paid consultations yet</p>
        <p class="mt-1 max-w-sm text-[11.5px] text-ink-400">
          Patients book paid consultations from their appointments page. You will see them here and get a notification.
        </p>
      </div>

      <ul v-else class="divide-y divide-ink-100">
        <li
          v-for="item in items"
          :key="item.id"
          class="flex flex-wrap items-center gap-3 px-4 py-3 transition-colors hover:bg-surface-50/60"
          :class="['PAID', 'WAITING_ROOM', 'LIVE'].includes(item.status) ? 'bg-brand-50/40' : ''"
        >
          <span
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[10.5px] font-bold text-white shadow-card"
            :style="{ backgroundColor: item.patient?.avatarColor ?? '#8B93D6' }"
          >
            {{ item.patient?.name?.split(' ').map((p) => p[0]).slice(0, 2).join('').toUpperCase() || '—' }}
          </span>
          <div class="min-w-[150px] flex-1">
            <p class="text-[13.5px] font-semibold text-ink-900">{{ item.patient?.name ?? 'Patient' }}</p>
            <p class="text-[11px] text-ink-400">
              {{ item.feeCurrency }} {{ item.feeAmount }} · {{ formatDateTime(item.createdAt, 'en') }}
              <span v-if="item.payment?.receiptNo">· receipt {{ item.payment.receiptNo }}</span>
            </p>
          </div>
          <span class="chip shrink-0 font-semibold" :class="STATUS_TONE[item.status] ?? 'bg-surface-100 text-ink-600'">
            {{ item.status.replaceAll('_', ' ').toLowerCase() }}
          </span>
          <div class="flex shrink-0 items-center gap-2">
            <RouterLink
              v-if="actionable.some((c) => c.id === item.id)"
              :to="`/doctor/consultations/${item.id}`"
              class="dash-btn px-3 py-1.5 text-xs"
            >
              {{ item.status === 'LIVE' ? 'Join call' : 'Enter room' }} →
            </RouterLink>
            <span v-if="item.prescriptionNote" class="text-[11px] text-ink-400">✓ prescription sent</span>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
