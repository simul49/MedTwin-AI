<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import flowImage from '@/assets/patient-doctor-consent.png';

const { t } = useI18n();

const steps = [1, 2, 3, 4, 5, 6, 7];
</script>

<template>
  <div class="container-page py-16">
    <div class="grid items-center gap-10 lg:grid-cols-2">
      <header v-reveal class="max-w-2xl">
        <span class="section-eyebrow">How it works</span>
        <h1 class="section-title mt-5">{{ t('how.title') }}</h1>
        <p class="mt-3 text-lg leading-relaxed text-ink-600">{{ t('how.lead') }}</p>
        <RouterLink to="/login" class="btn-primary mt-6 transition-transform duration-200 hover:-translate-y-0.5 hover:shadow-lift">
          {{ t('home.ctaPortal') }}
        </RouterLink>
      </header>
      <div v-reveal:2 class="relative">
        <div class="overflow-hidden rounded-2xl border border-ink-200 bg-white shadow-card">
          <img
            :src="flowImage"
            alt="Illustration of a patient and a clinician connected through a consent-protected platform"
            class="h-auto w-full transition-transform duration-700 hover:scale-[1.03]"
            loading="lazy"
          />
        </div>
      </div>
    </div>

    <!-- Steps: connected vertical timeline -->
    <div class="mt-16">
      <div class="flex items-center gap-4">
        <h2 class="text-[11px] font-bold uppercase tracking-[0.14em] text-brand-700">{{ t('how.journey') }}</h2>
        <span class="h-px flex-1 bg-ink-100" />
        <span class="text-[12px] font-medium text-ink-400">{{ t('how.journeyCaption', { n: steps.length }) }}</span>
      </div>

      <ol class="relative mt-8 space-y-5">
        <span class="absolute bottom-6 left-[19px] top-6 w-px bg-ink-200" aria-hidden="true" />
        <li
          v-for="step in steps"
          :key="step"
          v-reveal="step"
          class="group relative flex items-start gap-5"
        >
          <span
            class="z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-600 text-[13px] font-bold text-white ring-4 ring-white
                   transition-transform duration-300 group-hover:scale-110"
          >
            {{ step }}
          </span>
          <div class="card card-pad min-w-0 flex-1 py-4 transition-all duration-300 group-hover:-translate-y-0.5 group-hover:shadow-lift">
            <h2 class="text-[15px] font-semibold text-ink-800">{{ t(`how.step${step}Title`) }}</h2>
            <p class="muted mt-1 text-[13.5px] leading-relaxed">{{ t(`how.step${step}Body`) }}</p>
          </div>
        </li>
      </ol>
    </div>

    <!-- Safety net -->
    <div class="mt-16">
      <div class="flex items-center gap-4">
        <h2 class="text-[11px] font-bold uppercase tracking-[0.14em] text-brand-700">{{ t('how.safetyNet') }}</h2>
        <span class="h-px flex-1 bg-ink-100" />
      </div>
      <div class="mt-6 grid gap-6 lg:grid-cols-2">
        <div class="card card-pad transition-shadow duration-300 hover:shadow-card">
          <div class="flex items-start gap-4">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50">
              <svg class="h-5 w-5 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
                <path d="M12 21C7 17 3 13.5 3 9.5A5.5 5.5 0 0112 5a5.5 5.5 0 019 4.5c0 4-4 7.5-9 11.5z" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M12 8v4M12 15h.01" stroke-linecap="round" />
              </svg>
            </span>
            <div>
              <h2 class="text-[15px] font-semibold text-ink-800">{{ t('trust.emergencyTitle') }}</h2>
              <p class="muted mt-1.5 text-[13.5px] leading-relaxed">{{ t('trust.emergencyBody') }}</p>
            </div>
          </div>
        </div>
        <div class="card card-pad border border-amber-200 bg-amber-50">
          <div class="flex items-start gap-4">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-100">
              <svg class="h-5 w-5 text-amber-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
                <path d="M12 9v4M12 17h.01" stroke-linecap="round" />
                <path d="M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <h2 class="text-[15px] font-semibold text-amber-900">{{ t('trust.limitsTitle') }}</h2>
              <p class="mt-1.5 text-[13.5px] leading-relaxed text-amber-900">{{ t('trust.limitsBody') }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
