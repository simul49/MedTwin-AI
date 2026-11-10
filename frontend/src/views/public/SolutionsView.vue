<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import extractionImage from '@/assets/document-extraction.png';

const { t } = useI18n();

const solutions = [
  { key: 'twin', icon: 'M12 3a4 4 0 110 8 4 4 0 010-8zM4 21a8 8 0 0116 0', experimental: false },
  { key: 'assistant', icon: 'M4 5h16v11H9l-5 4z', experimental: false },
  { key: 'agents', icon: 'M12 3v6l4 2M12 3a9 9 0 100 18 9 9 0 000-18z', experimental: false },
  { key: 'recommendations', icon: 'M12 3l2.6 5.6 6.1.8-4.5 4.3 1.1 6-5.3-3-5.3 3 1.1-6L3.3 9.4l6.1-.8z', experimental: false },
  { key: 'collaboration', icon: 'M12 2l7 4v6c0 5-3 8-7 10-4-2-7-5-7-10V6z', experimental: false },
  { key: 'trust', icon: 'M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6z', experimental: false },
  { key: 'deepfake', icon: 'M4 4h16v16H4zM9 9h6v6H9z', experimental: true },
];
</script>

<template>
  <div class="container-page py-16">
    <div class="grid items-center gap-10 lg:grid-cols-2">
      <header v-reveal class="max-w-2xl">
        <span class="section-eyebrow">The platform</span>
        <h1 class="mt-5 text-3xl font-bold tracking-tight sm:text-4xl">{{ t('solutions.title') }}</h1>
        <p class="mt-3 text-lg leading-relaxed text-ink-600">{{ t('solutions.lead') }}</p>
      </header>
      <div v-reveal:2 class="overflow-hidden rounded-2xl border border-ink-200 bg-white shadow-card">
        <img
          :src="extractionImage"
          alt="Illustration of structured health data extracted from a medical report"
          class="h-auto w-full transition-transform duration-700 hover:scale-[1.03]"
          loading="lazy"
        />
      </div>
    </div>

    <div class="mt-10 grid gap-5 md:grid-cols-2">
      <article
        v-for="(item, index) in solutions"
        :key="item.key"
        v-reveal="index + 1"
        class="card card-pad group transition-all duration-300 hover:-translate-y-1 hover:shadow-lift"
      >
        <div class="flex items-start gap-4">
          <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-50 transition-colors duration-300 group-hover:bg-brand-100">
            <svg class="h-6 w-6 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
              <path :d="item.icon" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="font-semibold">{{ t(`solutions.${item.key}Title`) }}</h2>
              <span v-if="item.experimental" class="chip bg-amber-100 text-amber-800">{{ t('solutions.experimental') }}</span>
            </div>
            <p class="muted mt-1.5 leading-relaxed">{{ t(`solutions.${item.key}Body`) }}</p>
          </div>
        </div>
      </article>
    </div>

    <p v-reveal class="mt-10 text-xs text-ink-400">{{ t('home.disclaimerNote') }}</p>
  </div>
</template>
