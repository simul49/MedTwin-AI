<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps<{ status: string; fallback?: string }>();
const { t, te } = useI18n();

const TONES: Record<string, string> = {
  ACTIVE: 'bg-emerald-50 text-emerald-700',
  CONFIRMED: 'bg-emerald-50 text-emerald-700',
  PROCESSED: 'bg-emerald-50 text-emerald-700',
  VERIFIED: 'bg-emerald-50 text-emerald-700',
  COMPLETED: 'bg-emerald-50 text-emerald-700',
  NORMAL: 'bg-emerald-50 text-emerald-700',
  PENDING: 'bg-amber-50 text-amber-700',
  PROCESSING: 'bg-amber-50 text-amber-700',
  UNVERIFIED: 'bg-amber-50 text-amber-700',
  REQUESTED: 'bg-amber-50 text-amber-700',
  EXPIRED: 'bg-ink-100 text-ink-600',
  REVOKED: 'bg-rose-50 text-rose-700',
  REJECTED: 'bg-rose-50 text-rose-700',
  FAILED: 'bg-rose-50 text-rose-700',
  HIGH: 'bg-amber-50 text-amber-700',
  CRITICAL: 'bg-rose-50 text-rose-700',
  LOW: 'bg-sky-50 text-sky-700',
  AI_GENERATED: 'bg-violet-50 text-violet-700',
  CLINICIAN: 'bg-brand-50 text-brand-700',
};

const label = computed(() => {
  const key = `status.${props.status}`;
  if (te(key)) return t(key);
  return props.fallback ?? props.status.replace(/_/g, ' ').toLowerCase();
});

const tone = computed(() => TONES[props.status] ?? 'bg-ink-100 text-ink-600');
</script>

<template>
  <span class="chip" :class="tone">{{ label }}</span>
</template>
