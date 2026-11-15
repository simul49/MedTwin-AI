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

    <section class="mt-16 grid gap-8 lg:grid-cols-2">
      <!-- Architecture pipeline -->
      <div v-reveal class="card card-pad transition-all duration-300 hover:-translate-y-1 hover:shadow-lift">
        <div class="flex items-start gap-4">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50">
            <svg class="h-5 w-5 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
              <rect x="3" y="3" width="7" height="7" rx="1.5" />
              <rect x="14" y="3" width="7" height="7" rx="1.5" />
              <rect x="8.5" y="14" width="7" height="7" rx="1.5" />
              <path d="M6.5 10v2.5h11V10M12 12.5V14" stroke-linecap="round" />
            </svg>
          </span>
          <div>
            <h2 class="text-[11px] font-bold uppercase tracking-[0.14em] text-brand-700">System architecture</h2>
            <p class="mt-2 text-[13.5px] leading-relaxed text-ink-600">{{ t('research.architectureBody') }}</p>
          </div>
        </div>

        <ol class="relative mt-6 space-y-3">
          <span class="absolute bottom-5 left-[13px] top-5 w-px bg-brand-100" aria-hidden="true" />
          <li v-for="(stage, index) in stages" :key="stage.name" class="group relative flex items-start gap-3.5">
            <span class="z-10 flex h-[27px] w-[27px] shrink-0 items-center justify-center rounded-full bg-brand-600 text-[11px] font-bold text-white ring-4 ring-white transition-transform duration-300 group-hover:scale-110">
              {{ index + 1 }}
            </span>
            <div class="min-w-0 flex-1 rounded-xl border border-ink-200 bg-white px-4 py-2.5 transition-colors duration-300 group-hover:border-brand-300">
              <p class="text-[13px] font-semibold text-ink-800">{{ stage.name }}</p>
              <p class="mt-0.5 font-mono text-[11px] text-ink-500">{{ stage.io }}</p>
            </div>
          </li>
        </ol>
      </div>

      <!-- Evaluation methodology -->
      <div v-reveal:1 class="card card-pad transition-all duration-300 hover:-translate-y-1 hover:shadow-lift">
        <div class="flex items-start gap-4">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50">
            <svg class="h-5 w-5 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
              <path d="M9 3h6M10 3v5.5L4.5 18a2 2 0 001.8 3h11.4a2 2 0 001.8-3L14 8.5V3" stroke-linecap="round" stroke-linejoin="round" />
              <path d="M7 14h10" stroke-linecap="round" />
            </svg>
          </span>
          <div>
            <h2 class="text-[11px] font-bold uppercase tracking-[0.14em] text-brand-700">Evaluation methodology</h2>
            <p class="mt-2 text-[13.5px] leading-relaxed text-ink-600">{{ t('research.evaluationBody') }}</p>
          </div>
        </div>

        <ul class="mt-5 divide-y divide-ink-100">
          <li v-for="(metric, index) in metrics" :key="metric" class="flex gap-3 py-2.5 first:pt-0 last:pb-0 text-[13px] text-ink-700">
            <span class="w-5 shrink-0 text-[11px] font-bold tabular-nums text-brand-600">M{{ index + 1 }}</span>
            {{ metric }}
          </li>
        </ul>

        <div class="mt-6 rounded-xl bg-ink-50 p-4">
          <p class="text-[10.5px] font-bold uppercase tracking-[0.14em] text-ink-500">{{ t('research.statusTitle') }}</p>
          <div class="mt-2.5 flex flex-wrap gap-2">
            <span class="rounded-full border border-ink-200 bg-white px-2.5 py-1 text-[10.5px] font-semibold text-ink-500">{{ t('research.statusPlanned') }}</span>
            <span class="flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[10.5px] font-bold text-amber-800">
              <span class="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-500" />
              {{ t('research.statusWip') }}
            </span>
            <span class="rounded-full border border-ink-200 bg-white px-2.5 py-1 text-[10.5px] font-semibold text-ink-500">{{ t('research.statusPreprint') }}</span>
            <span class="rounded-full border border-ink-200 bg-white px-2.5 py-1 text-[10.5px] font-semibold text-ink-500">{{ t('research.statusPeerReviewed') }}</span>
          </div>
        </div>
      </div>
    </section>

    <p class="mt-10 border-t border-ink-100 pt-5 text-xs leading-relaxed text-ink-400">{{ t('research.note') }}</p>
  </div>
</template>
