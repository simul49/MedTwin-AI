<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const points = [
  'MedTwin AI is not a substitute for professional medical advice, diagnosis, or treatment.',
  'Never disregard or delay seeking medical advice because of something you read here.',
  'AI answers can be incomplete or wrong, even when sources are shown and the safety indicator is high.',
  'Extracted document values are candidates until you confirm them.',
  'In an emergency, contact your local emergency number (for example 911 / 120) immediately.',
];
</script>

<template>
  <div class="container-page max-w-3xl py-16">
    <h1 class="section-title">{{ t('legal.medical') }}</h1>
    <p class="muted mt-2">{{ t('legal.lastUpdated') }}: 2026-10-30</p>

    <div class="mt-6 rounded-2xl border border-rose-200 bg-rose-50 p-5">
      <p class="font-semibold text-rose-900">{{ t('brand.full') }}</p>
      <p class="mt-2 text-sm leading-relaxed text-rose-900">{{ t('brand.disclaimer') }}</p>
    </div>

    <ul class="mt-8 space-y-3">
      <li v-for="point in points" :key="point" class="card card-pad flex gap-3">
        <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-500"></span>
        <p class="text-sm leading-relaxed text-ink-700">{{ point }}</p>
      </li>
    </ul>

    <p class="mt-8 text-xs text-ink-400">{{ t('legal.placeholder') }}</p>
  </div>
</template>
