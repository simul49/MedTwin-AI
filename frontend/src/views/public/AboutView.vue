<script setup lang="ts">
import { computed } from 'vue';
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

const commitments = computed(() => [
  t('about.commitment1'),
  t('about.commitment2'),
  t('about.commitment3'),
]);
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

    <section class="mt-14 grid gap-8 lg:grid-cols-2">
      <!-- Mission -->
      <div v-reveal class="card card-pad flex flex-col transition-all duration-300 hover:-translate-y-1 hover:shadow-lift">
        <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50">
          <svg class="h-5 w-5 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
            <circle cx="12" cy="12" r="9" />
            <circle cx="12" cy="12" r="4.5" />
            <circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" />
          </svg>
        </span>
        <h2 class="mt-4 text-[11px] font-bold uppercase tracking-[0.14em] text-brand-700">{{ t('about.missionTitle') }}</h2>
        <p class="mt-3 text-[17px] font-medium leading-relaxed text-ink-800">
          Make authorised health information easier to organise and understand — while keeping qualified
          healthcare professionals at the centre of every decision.
        </p>
        <ul class="mt-6 space-y-3 border-t border-ink-100 pt-5">
          <li v-for="commitment in commitments" :key="commitment" class="flex gap-2.5 text-[13px] leading-relaxed text-ink-600">
            <svg class="mt-0.5 h-4 w-4 shrink-0 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            {{ commitment }}
          </li>
        </ul>
      </div>

      <!-- Problems -->
      <div v-reveal:1 class="card card-pad transition-all duration-300 hover:-translate-y-1 hover:shadow-lift">
        <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-terracotta-50">
          <svg class="h-5 w-5 text-terracotta-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
            <path d="M12 9v4M12 17h.01" stroke-linecap="round" />
            <path d="M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" stroke-linejoin="round" />
          </svg>
        </span>
        <h2 class="mt-4 text-[11px] font-bold uppercase tracking-[0.14em] text-terracotta-600">{{ t('about.problemsTitle') }}</h2>
        <ol class="mt-3 divide-y divide-ink-100">
          <li v-for="(problem, index) in problems" :key="problem.title" class="flex gap-4 py-3.5 first:pt-1 last:pb-0">
            <span class="text-[12px] font-bold tabular-nums text-ink-300">{{ String(index + 1).padStart(2, '0') }}</span>
            <div>
              <p class="text-[14px] font-semibold text-ink-800">{{ problem.title }}</p>
              <p class="muted mt-0.5 text-[13px] leading-relaxed">{{ problem.body }}</p>
            </div>
          </li>
        </ol>
      </div>
    </section>

    <!-- Principles -->
    <section class="mt-16">
      <div class="flex items-center gap-4">
        <h2 class="text-[11px] font-bold uppercase tracking-[0.14em] text-brand-700">Principles</h2>
        <span class="h-px flex-1 bg-ink-100" />
        <span class="text-[12px] font-medium text-ink-400">{{ t('about.howWeBuild') }}</span>
      </div>
      <div class="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div
          v-for="(principle, index) in principles"
          :key="principle.key"
          v-reveal="index + 1"
          class="card card-pad group relative transition-all duration-300 hover:-translate-y-1 hover:shadow-lift"
        >
          <span class="absolute right-4 top-4 text-[11px] font-bold tabular-nums text-ink-200">{{ String(index + 1).padStart(2, '0') }}</span>
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
