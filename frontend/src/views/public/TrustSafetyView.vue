<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import shieldImage from '@/assets/trust-shield.png';

const { t } = useI18n();

const factors = [
  { key: 'source_grounding', body: 'Checks whether claims are supported by retrieved evidence.' },
  { key: 'reference_availability', body: 'Records whether approved sources were available at all.' },
  { key: 'context_match', body: 'Checks consistency with the authorised patient context.' },
  { key: 'contradiction_check', body: 'Looks for conflicts with known or retrieved information.' },
  { key: 'safety_rules', body: 'Checks the answer against defined healthcare safety policies.' },
  { key: 'unsupported_claims', body: 'Flags statements that lack adequate support.' },
  { key: 'risk_routing', body: 'Decides whether refusal, clarification or escalation is needed.' },
];

const policies = [
  { to: '/privacy', label: t('legal.privacy') },
  { to: '/terms', label: t('legal.terms') },
  { to: '/medical-disclaimer', label: t('legal.medical') },
];

const controlIcons = [
  'M9 12l2 2 4-4M12 3l7 4v6c0 5-3 8-7 10-4-2-7-5-7-10V6z',
  'M4 5h16v14H4zM8 9h8M8 13h5M4 9h0',
  'M12 3v18M5 8l7-5 7 5M8 21h8',
  'M12 9v4M12 16h.01M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z',
];
</script>

<template>
  <div class="container-page py-16">
    <div class="grid items-center gap-10 lg:grid-cols-[1fr_auto]">
      <header v-reveal class="max-w-3xl">
        <span class="section-eyebrow">Trust &amp; safety</span>
        <h1 class="section-title mt-5">{{ t('trust.title') }}</h1>
        <p class="mt-3 text-lg leading-relaxed text-ink-600">{{ t('trust.lead') }}</p>
      </header>
      <div v-reveal:2 class="hidden lg:block">
        <img
          :src="shieldImage"
          alt="Illustration of a shield representing layered privacy and safety controls"
          class="animate-float-slow h-44 w-44 object-contain"
          loading="lazy"
        />
      </div>
    </div>

    <!-- Controls -->
    <section class="mt-16">
      <div class="flex items-center gap-4">
        <h2 class="text-[11px] font-bold uppercase tracking-[0.14em] text-brand-700">Controls</h2>
        <span class="h-px flex-1 bg-ink-100" />
        <span class="text-[12px] font-medium text-ink-400">What we check, and what we cannot promise</span>
      </div>
      <div class="mt-6 grid gap-5 md:grid-cols-2">
        <article
          v-for="(control, index) in [
            { title: t('trust.consentTitle'), body: t('trust.consentBody') },
            { title: t('trust.auditTitle'), body: t('trust.auditBody') },
            { title: t('trust.limitsTitle'), body: t('trust.limitsBody') },
          ]"
          :key="control.title"
          v-reveal="index + 1"
          class="card card-pad transition-all duration-300 hover:-translate-y-1 hover:shadow-lift"
        >
          <div class="flex items-start gap-4">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50">
              <svg class="h-5 w-5 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
                <path :d="controlIcons[index]" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <h2 class="text-[15px] font-semibold text-ink-800">{{ control.title }}</h2>
              <p class="muted mt-1.5 text-[13.5px] leading-relaxed">{{ control.body }}</p>
            </div>
          </div>
        </article>
        <article class="rounded-2xl border border-rose-200 bg-rose-50 p-6">
          <div class="flex items-start gap-4">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rose-100">
              <svg class="h-5 w-5 text-rose-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
                <path d="M12 9v4M12 16h.01" stroke-linecap="round" />
                <path d="M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <h2 class="text-[15px] font-semibold text-rose-900">{{ t('trust.emergencyTitle') }}</h2>
              <p class="mt-1.5 text-[13.5px] leading-relaxed text-rose-900">{{ t('trust.emergencyBody') }}</p>
            </div>
          </div>
        </article>
      </div>
    </section>

    <!-- Indicator explanation -->
    <section class="mt-16 grid gap-8 lg:grid-cols-2">
      <div v-reveal>
        <div class="flex items-center gap-4">
          <h2 class="text-[11px] font-bold uppercase tracking-[0.14em] text-brand-700">{{ t('trust.indicatorTitle') }}</h2>
          <span class="h-px flex-1 bg-ink-100" />
        </div>
        <p class="mt-4 leading-relaxed text-ink-600">{{ t('trust.indicatorBody') }}</p>

        <ol class="mt-5 divide-y divide-ink-100">
          <li v-for="(factor, index) in factors" :key="factor.key" class="flex gap-3.5 py-2.5 first:pt-0 last:pb-0">
            <span class="w-7 shrink-0 text-[11px] font-bold tabular-nums text-brand-600">F{{ index + 1 }}</span>
            <div>
              <p class="text-[13.5px] font-semibold text-ink-800">{{ t(`safety.${factor.key}`) }}</p>
              <p class="muted mt-0.5 text-[12.5px]">{{ factor.body }}</p>
            </div>
          </li>
        </ol>
      </div>

      <div class="space-y-5">
        <div class="rounded-2xl border border-amber-200 bg-amber-50 p-5">
          <div class="flex items-start gap-4">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-100">
              <svg class="h-5 w-5 text-amber-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
                <path d="M12 9v4M12 16h.01" stroke-linecap="round" />
                <path d="M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="text-[13.5px] font-bold text-amber-900">{{ t('trust.indicatorTitle') }}</p>
              <p class="mt-1.5 text-[13px] leading-relaxed text-amber-900">{{ t('trust.indicatorWarning') }}</p>
            </div>
          </div>
        </div>
        <div class="card card-pad">
          <div class="flex items-start gap-4">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50">
              <svg class="h-5 w-5 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
                <path d="M4 4h16v16H4zM9 9h6v6H9z" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="text-[13.5px] font-semibold text-ink-800">{{ t('trust.deepfakeTitle') }}</p>
              <p class="muted mt-1.5 text-[13px] leading-relaxed">{{ t('trust.deepfakeBody') }}</p>
            </div>
          </div>
        </div>
        <div class="card card-pad">
          <p class="text-[11px] font-bold uppercase tracking-[0.14em] text-brand-700">{{ t('trust.linksTitle') }}</p>
          <ul class="mt-3 divide-y divide-ink-100">
            <li v-for="policy in policies" :key="policy.to">
              <RouterLink :to="policy.to" class="group flex items-center justify-between py-2 text-[13.5px] font-medium text-ink-700 transition-colors hover:text-brand-700">
                {{ policy.label }}
                <svg class="h-4 w-4 text-ink-300 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path d="M5 12h14M13 6l6 6-6 6" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </RouterLink>
            </li>
          </ul>
        </div>
      </div>
    </section>
  </div>
</template>
