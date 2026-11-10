<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const sections = [
  { title: 'What we collect', body: 'Account details you provide, the health information you choose to enter or upload, and the minimum operational logs needed to keep the service secure.' },
  { title: 'Why we collect it', body: 'To build your Digital Twin, answer your questions with authorised context, and record access so you can see who viewed what.' },
  { title: 'Sharing', body: 'Nothing is shared with a healthcare professional unless you grant access with an explicit scope. You can revoke it at any time; information already exported cannot be recalled.' },
  { title: 'AI providers', body: 'No third-party language model is called in the default configuration. When a provider is enabled, what is sent to it, and under which terms, is documented before the feature is used.' },
  { title: 'Retention and deletion', body: 'You can export everything in your account and delete your health records, documents and timeline. Backups expire on their documented schedule.' },
  { title: 'Your rights', body: 'Access, correction, export and deletion are available from your account settings. Contact us for anything this page does not cover.' },
];
</script>

<template>
  <div class="container-page max-w-3xl py-16">
    <h1 class="section-title">{{ t('legal.privacy') }}</h1>
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
