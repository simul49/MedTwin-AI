<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import analyticsImage from '@/assets/clinical-analytics.png';

const { t } = useI18n();

const stages = [
  { name: 'Intent detection', io: 'user message → intent + risk category' },
  { name: 'Medical context', io: 'message → entities and context slots' },
  { name: 'Digital Twin retrieval', io: 'authorised scope → structured records' },
  { name: 'Knowledge / RAG', io: 'query → ranked approved passages' },
  { name: 'Safety & Trust', io: 'draft answer → factor scores + routing' },
  { name: 'Response generation', io: 'context + findings → cited answer' },
];

const metrics = [
  'Retrieval relevance on a labelled question set',
  'Citation correctness (cited passage supports the claim)',
  'Groundedness and unsupported-claim rate',
  'Refusal and escalation behaviour on high-risk prompts',
  'Prompt-injection and adversarial robustness',
];
</script>

<template>
  <div class="container-page py-16">
    <div class="grid items-center gap-10 lg:grid-cols-2">
      <header v-reveal class="max-w-2xl">
        <span class="section-eyebrow">Evaluation first</span>
        <h1 class="mt-5 text-3xl font-bold tracking-tight sm:text-4xl">{{ t('research.title') }}</h1>
        <p class="mt-3 text-lg leading-relaxed text-ink-600">{{ t('research.lead') }}</p>
      </header>
      <div v-reveal:2 class="overflow-hidden rounded-2xl border border-navy-700/30 shadow-card">
        <img
          :src="analyticsImage"
          alt="Illustration of clinical analytics panels and evaluation charts"
          class="h-auto w-full transition-transform duration-700 hover:scale-[1.03]"
          loading="lazy"
        />
      </div>
    </div>

    <section class="mt-12 grid gap-8 lg:grid-cols-2">
      <div v-reveal class="card card-pad transition-all duration-300 hover:-translate-y-1 hover:shadow-lift">
        <h2 class="text-xl font-bold">{{ t('research.architectureTitle') }}</h2>
        <p class="mt-3 leading-relaxed text-ink-600">{{ t('research.architectureBody') }}</p>

        <ul class="mt-5 space-y-2">
          <li v-for="stage in stages" :key="stage.name" class="rounded-xl border border-ink-200 px-4 py-3">
            <p class="text-sm font-semibold">{{ stage.name }}</p>
            <p class="muted mt-0.5 font-mono text-xs">{{ stage.io }}</p>
          </li>
        </ul>
      </div>

      <div v-reveal:1 class="card card-pad transition-all duration-300 hover:-translate-y-1 hover:shadow-lift">
        <h2 class="text-xl font-bold">{{ t('research.evaluationTitle') }}</h2>
        <p class="mt-3 leading-relaxed text-ink-600">{{ t('research.evaluationBody') }}</p>

        <ul class="mt-5 space-y-2">
          <li v-for="metric in metrics" :key="metric" class="flex gap-3 text-sm text-ink-700">
            <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500"></span>
            {{ metric }}
          </li>
        </ul>

        <div class="mt-6 rounded-xl bg-ink-50 p-4">
          <p class="text-xs font-semibold uppercase tracking-wide text-ink-500">{{ t('research.statusTitle') }}</p>
          <div class="mt-2 flex flex-wrap gap-2">
            <span class="chip bg-ink-100 text-ink-700">{{ t('research.statusPlanned') }}</span>
            <span class="chip bg-amber-100 text-amber-800">{{ t('research.statusWip') }}</span>
            <span class="chip bg-ink-100 text-ink-700">{{ t('research.statusPreprint') }}</span>
            <span class="chip bg-ink-100 text-ink-700">{{ t('research.statusPeerReviewed') }}</span>
          </div>
        </div>
      </div>
    </section>

    <p class="mt-10 text-xs text-ink-400">{{ t('research.note') }}</p>
  </div>
</template>
