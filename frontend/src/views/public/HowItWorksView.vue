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
        <h1 class="section-title">{{ t('how.title') }}</h1>
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

    <ol class="mt-14 space-y-4">
      <li
        v-for="step in steps"
        :key="step"
        v-reveal="step"
        class="card card-pad group flex flex-col gap-3 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-card sm:flex-row sm:items-start sm:gap-6"
      >
        <span
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-600 font-bold text-white
                 transition-transform duration-300 group-hover:scale-110"
        >
          {{ step }}
        </span>
        <div>
          <h2 class="font-semibold">{{ t(`how.step${step}Title`) }}</h2>
          <p class="muted mt-1 leading-relaxed">{{ t(`how.step${step}Body`) }}</p>
        </div>
      </li>
    </ol>

    <div v-reveal class="mt-12 grid gap-6 lg:grid-cols-2">
      <div class="rounded-2xl border border-ink-200 bg-white p-6 transition-shadow duration-300 hover:shadow-card">
        <h2 class="font-semibold">{{ t('trust.emergencyTitle') }}</h2>
        <p class="muted mt-2 leading-relaxed">{{ t('trust.emergencyBody') }}</p>
      </div>
      <div class="rounded-2xl border border-amber-200 bg-amber-50 p-6">
        <h2 class="font-semibold text-amber-900">{{ t('trust.limitsTitle') }}</h2>
        <p class="mt-2 text-sm leading-relaxed text-amber-900">{{ t('trust.limitsBody') }}</p>
      </div>
    </div>
  </div>
</template>
