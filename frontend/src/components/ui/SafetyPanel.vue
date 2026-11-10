<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Safety } from '@/api/types';

const props = defineProps<{ safety: Safety; compact?: boolean }>();
const { t, te } = useI18n();

const tone = computed(() => {
  if (props.safety.score >= 80) return { bar: 'bg-emerald-500', text: 'text-emerald-700' };
  if (props.safety.score >= 55) return { bar: 'bg-amber-500', text: 'text-amber-700' };
  return { bar: 'bg-rose-500', text: 'text-rose-700' };
});

const STATUS_TONE: Record<string, string> = {
  pass: 'bg-emerald-50 text-emerald-700',
  warn: 'bg-amber-50 text-amber-700',
  fail: 'bg-rose-50 text-rose-700',
  info: 'bg-ink-100 text-ink-600',
};

function factorLabel(key: string, fallback: string): string {
  const scoped = `safety.${key}`;
  return te(scoped) ? t(scoped) : fallback;
}

function statusLabel(status: string): string {
  const key = `safety.${status}`;
  return te(key) ? t(key) : status;
}

function labelText(label: string): string {
  const key = `safety.${label}`;
  return te(key) ? t(key) : label;
}
</script>

<template>
  <div class="rounded-2xl border border-ink-200 bg-white p-4">
    <div class="flex items-center justify-between gap-4">
      <div>
        <p class="text-xs font-semibold uppercase tracking-wide text-ink-500">{{ t('patient.trustScore') }}</p>
        <p class="mt-0.5 text-xs text-ink-400">{{ t('patient.trustHelp') }}</p>
      </div>
      <p class="text-2xl font-bold" :class="tone.text">{{ safety.score }}<span class="text-sm font-medium text-ink-400">/100</span></p>
    </div>

    <div class="mt-3 h-2 overflow-hidden rounded-full bg-ink-100">
      <div class="h-full rounded-full transition-all" :class="tone.bar" :style="{ width: `${safety.score}%` }" />
    </div>

    <div v-if="safety.labels?.length" class="mt-3 flex flex-wrap gap-1.5">
      <span v-for="label in safety.labels" :key="label" class="chip bg-ink-100 text-ink-600">{{ labelText(label) }}</span>
    </div>

    <ul v-if="!compact" class="mt-4 space-y-2">
      <li v-for="factor in safety.factors" :key="factor.key" class="flex items-start gap-3">
        <span class="chip mt-0.5 shrink-0" :class="STATUS_TONE[factor.status] ?? STATUS_TONE.info">
          {{ statusLabel(factor.status) }}
        </span>
        <div class="min-w-0">
          <p class="text-sm font-medium text-ink-800">
            {{ factorLabel(factor.key, factor.label) }}
            <span class="ml-1 text-xs font-normal text-ink-400">×{{ factor.weight }}</span>
          </p>
          <p class="text-xs leading-relaxed text-ink-500">{{ factor.detail }}</p>
        </div>
      </li>
    </ul>

    <p class="mt-4 border-t border-ink-100 pt-3 text-xs leading-relaxed text-ink-400">
      {{ safety.disclaimer }}
      <span class="ml-1 text-ink-400">v{{ safety.version }}</span>
    </p>
  </div>
</template>
