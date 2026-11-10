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
</script>

<template>
  <div class="container-page py-16">
    <div class="grid items-center gap-10 lg:grid-cols-[1fr_auto]">
      <header v-reveal class="max-w-3xl">
        <h1 class="section-title">{{ t('trust.title') }}</h1>
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

    <section class="mt-12 grid gap-5 md:grid-cols-2">
      <article v-reveal class="card card-pad transition-all duration-300 hover:-translate-y-1 hover:shadow-lift">
        <h2 class="font-semibold">{{ t('trust.consentTitle') }}</h2>
        <p class="muted mt-2 leading-relaxed">{{ t('trust.consentBody') }}</p>
      </article>
      <article v-reveal:1 class="card card-pad transition-all duration-300 hover:-translate-y-1 hover:shadow-lift">
        <h2 class="font-semibold">{{ t('trust.auditTitle') }}</h2>
        <p class="muted mt-2 leading-relaxed">{{ t('trust.auditBody') }}</p>
      </article>
      <article v-reveal:2 class="card card-pad transition-all duration-300 hover:-translate-y-1 hover:shadow-lift">
        <h2 class="font-semibold">{{ t('trust.limitsTitle') }}</h2>
        <p class="muted mt-2 leading-relaxed">{{ t('trust.limitsBody') }}</p>
      </article>
      <article class="rounded-2xl border border-rose-200 bg-rose-50 p-6">
        <h2 class="font-semibold text-rose-900">{{ t('trust.emergencyTitle') }}</h2>
        <p class="mt-2 text-sm leading-relaxed text-rose-900">{{ t('trust.emergencyBody') }}</p>
      </article>
    </section>

    <!-- Indicator explanation -->
    <section class="mt-12 grid gap-8 lg:grid-cols-2">
      <div v-reveal>
        <h2 class="text-xl font-bold">{{ t('trust.indicatorTitle') }}</h2>
        <p class="mt-3 leading-relaxed text-ink-600">{{ t('trust.indicatorBody') }}</p>

        <ul class="mt-5 space-y-2">
          <li v-for="factor in factors" :key="factor.key" class="rounded-xl border border-ink-200 px-4 py-3">
            <p class="text-sm font-semibold">{{ t(`safety.${factor.key}`) }}</p>
            <p class="muted mt-0.5">{{ factor.body }}</p>
          </li>
        </ul>
      </div>

      <div class="space-y-5">
        <div class="rounded-2xl border border-amber-200 bg-amber-50 p-5">
          <p class="text-sm font-semibold text-amber-900">{{ t('trust.indicatorTitle') }}</p>
          <p class="mt-2 text-sm leading-relaxed text-amber-900">{{ t('trust.indicatorWarning') }}</p>
        </div>
        <div class="rounded-2xl border border-ink-200 bg-white p-5">
          <p class="text-sm font-semibold">{{ t('trust.deepfakeTitle') }}</p>
          <p class="muted mt-2 leading-relaxed">{{ t('trust.deepfakeBody') }}</p>
        </div>
        <div class="rounded-2xl border border-ink-200 bg-white p-5">
          <p class="text-sm font-semibold">{{ t('trust.linksTitle') }}</p>
          <ul class="mt-2 space-y-1.5">
            <li v-for="policy in policies" :key="policy.to">
              <RouterLink :to="policy.to" class="text-sm text-brand-700 hover:underline">{{ policy.label }}</RouterLink>
            </li>
          </ul>
        </div>
      </div>
    </section>
  </div>
</template>
