<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const sections = [
  { title: 'Purpose of the service', body: 'MedTwin AI helps you organise and understand authorised health information. It is an information and workflow tool, not a healthcare provider.' },
  { title: 'Not medical advice', body: 'Content produced by the platform is general information. It does not diagnose, prescribe, or replace advice from a qualified professional who knows your history.' },
  { title: 'Your responsibilities', body: 'You are responsible for the accuracy of information you enter, for keeping your credentials secure, and for using the service within its documented scope.' },
  { title: 'Consent and access', body: 'Access granted to a professional is limited to the scope and duration you choose. Revocation stops future access but cannot retrieve information already exported.' },
  { title: 'Availability', body: 'The service is provided on a best-efforts basis. Scheduled maintenance and incidents may interrupt availability; it is not an emergency channel.' },
  { title: 'Changes', body: 'Material changes to these terms will be reflected on this page before they take effect.' },
];
</script>

<template>
  <div class="container-page max-w-3xl py-16">
    <h1 class="section-title">{{ t('legal.terms') }}</h1>
    <p class="muted mt-2">{{ t('legal.lastUpdated') }}: 2026-10-30</p>

    <div class="mt-6 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      {{ t('legal.placeholder') }}
    </div>

    <div class="mt-8 space-y-5">
      <section v-for="section in sections" :key="section.title" class="card card-pad">
        <h2 class="font-semibold">{{ section.title }}</h2>
        <p class="muted mt-2 leading-relaxed">{{ section.body }}</p>
      </section>
    </div>
  </div>
</template>
