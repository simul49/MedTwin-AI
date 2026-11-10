<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import careImage from '@/assets/connected-care.png';

const { t } = useI18n();

const problems = [
  { title: 'Reports are hard to read', body: 'Terminology, units and reference ranges are unfamiliar to most people.' },
  { title: 'Information is scattered', body: 'Results, notes and measurements live in different places and formats.' },
  { title: 'Consultation time is short', body: 'Professionals must review a lot of context before a visit.' },
  { title: 'AI can sound confident and be wrong', body: 'Without grounding and evaluation, generated health text is risky.' },
];

const principles = [
  { key: 'privacy', icon: 'M12 2l7 4v6c0 5-3 8-7 10-4-2-7-5-7-10V6z' },
  { key: 'transparency', icon: 'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z' },
  { key: 'safety', icon: 'M12 3v18M5 8l7-5 7 5' },
  { key: 'oversight', icon: 'M16 19v-2a4 4 0 00-8 0v2M12 11a3 3 0 100-6 3 3 0 000 6z' },
];
</script>

<template>
  <div class="container-page py-16">
    <div class="grid items-center gap-10 lg:grid-cols-2">
      <header v-reveal class="max-w-2xl">
        <span class="section-eyebrow">Why MedTwin AI</span>
        <h1 class="mt-5 text-3xl font-bold tracking-tight sm:text-4xl">{{ t('about.title') }}</h1>
        <p class="mt-3 text-lg leading-relaxed text-ink-600">{{ t('about.lead') }}</p>
      </header>
      <div v-reveal:2 class="overflow-hidden rounded-2xl border border-ink-200 bg-white shadow-card">
        <img
          :src="careImage"
          alt="Illustration of connected, consent-protected health records"
          class="h-auto w-full transition-transform duration-700 hover:scale-[1.03]"
          loading="lazy"
        />
      </div>
    </div>

    <section class="mt-12 grid gap-8 lg:grid-cols-2">
      <div v-reveal class="card card-pad transition-all duration-300 hover:-translate-y-1 hover:shadow-lift">
        <h2 class="text-xl font-bold">{{ t('about.missionTitle') }}</h2>
        <p class="mt-3 leading-relaxed text-ink-600">{{ t('about.missionBody') }}</p>
      </div>
      <div v-reveal:1 class="card card-pad transition-all duration-300 hover:-translate-y-1 hover:shadow-lift">
        <h2 class="text-xl font-bold">{{ t('about.problemsTitle') }}</h2>
        <ul class="mt-3 space-y-3">
          <li v-for="problem in problems" :key="problem.title" class="flex gap-3">
            <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500"></span>
            <div>
              <p class="font-medium">{{ problem.title }}</p>
              <p class="muted mt-0.5">{{ problem.body }}</p>
            </div>
          </li>
        </ul>
      </div>
    </section>

    <section class="mt-12">
      <h2 class="text-xl font-bold">{{ t('about.principlesTitle') }}</h2>
      <div class="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div
          v-for="(principle, index) in principles"
          :key="principle.key"
          v-reveal="index + 1"
          class="card card-pad group transition-all duration-300 hover:-translate-y-1 hover:shadow-lift"
        >
          <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 transition-colors duration-300 group-hover:bg-brand-100">
            <svg class="h-5 w-5 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
            <path :d="principle.icon" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <h3 class="mt-3 font-semibold">{{ t(`about.principle${principle.key.charAt(0).toUpperCase()}${principle.key.slice(1)}`) }}</h3>
          <p class="muted mt-1.5 leading-relaxed">
            {{ t(`about.principle${principle.key.charAt(0).toUpperCase()}${principle.key.slice(1)}Body`) }}
          </p>
        </div>
      </div>
    </section>
  </div>
</template>
