<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import MedicalDisclaimer from '@/components/ui/MedicalDisclaimer.vue';
import { useAuthStore } from '@/stores/auth';
import heroImage from '@/assets/hero-digital-twin.png';
import analyticsImage from '@/assets/clinical-analytics.png';
import extractionImage from '@/assets/document-extraction.png';
import cliniciansImage from '@/assets/clinicians-collaboration.png';

const { t } = useI18n();
const auth = useAuthStore();

const metrics = [
  { value: '7', label: 'Named safety factors' },
  { value: '100%', label: 'Source-attributed answers' },
  { value: '100%', label: 'Consent-scoped access' },
  { value: '24/7', label: 'Audit trail coverage' },
];

const extractionPoints = [
  'Lab values, dates and units structured from your documents',
  'Every extraction stays linked to its original source',
  'You review and confirm before anything enters your twin',
];

const audience = [
  {
    title: 'For patients',
    body: 'One place for your records, plain-language explanations and control over who sees what.',
    to: '/login?portal=patient',
    cta: 'Patient portal',
  },
  {
    title: 'For clinicians',
    body: 'A consent-scoped summary before the visit, with source links and an explicit AI draft label.',
    to: '/login?portal=doctor',
    cta: 'Clinician portal',
  },
];

const capabilities = [
  { key: 'twin', to: '/solutions', icon: 'M12 3a4 4 0 110 8 4 4 0 010-8zM4 21a8 8 0 0116 0' },
  { key: 'assistant', to: '/solutions', icon: 'M4 5h16v11H9l-5 4z' },
  { key: 'agents', to: '/solutions', icon: 'M12 3v6l4 2M12 3a9 9 0 100 18 9 9 0 000-18z' },
  { key: 'recommendations', to: '/solutions', icon: 'M12 3l2.6 5.6 6.1.8-4.5 4.3 1.1 6-5.3-3-5.3 3 1.1-6L3.3 9.4l6.1-.8z' },
  { key: 'collaboration', to: '/solutions', icon: 'M12 2l7 4v6c0 5-3 8-7 10-4-2-7-5-7-10V6z' },
  { key: 'trust', to: '/trust-safety', icon: 'M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6z' },
];

const workflow = [
  { title: 'Upload or enter', body: 'Add a document or a record you already have.' },
  { title: 'Organised automatically', body: 'Categorised, dated and linked to its source.' },
  { title: 'Explained with sources', body: 'Plain language, with references and limits.' },
  { title: 'Share with consent', body: 'Grant a clinician scoped access, and revoke anytime.' },
];

const stats = [
  { label: () => t('home.statsTwin') },
  { label: () => t('home.statsAssistant') },
  { label: () => t('home.statsSafety') },
  { label: () => t('home.statsConsent') },
];
</script>

<template>
  <div>
    <!-- Hero — full project name and description appear prominently -->
    <section class="relative overflow-hidden border-b border-ink-200/70 bg-gradient-to-b from-brand-50/70 via-white/40 to-transparent">
      <!-- decorative animated blobs + dot mesh -->
      <div aria-hidden="true" class="pointer-events-none absolute inset-0">
        <div class="bg-mesh absolute inset-0" />
        <div class="animate-float-slow absolute -left-24 -top-24 h-72 w-72 rounded-full bg-brand-200/40 blur-3xl" />
        <div class="animate-float-slower absolute -right-16 top-32 h-80 w-80 rounded-full bg-teal-100/60 blur-3xl" />
      </div>

      <div class="container-page relative grid items-center gap-12 py-16 lg:grid-cols-2 lg:py-24">
        <div>
          <span v-reveal class="section-eyebrow">{{ t('home.heroBadge') }}</span>
          <h1
            v-reveal:1
            class="mt-5 text-4xl font-extrabold leading-[1.1] tracking-tight sm:text-5xl"
          >
            {{ t('brand.full') }}
          </h1>
          <p v-reveal:2 class="gradient-text mt-3 text-lg font-bold">{{ t('brand.tagline') }}</p>
          <p v-reveal:3 class="mt-5 max-w-xl text-lg leading-relaxed text-ink-600">{{ t('home.heroSubtitle') }}</p>

          <div v-reveal:4 class="mt-8 flex flex-wrap gap-3">
            <RouterLink to="/solutions" class="btn-primary transition-transform duration-200 hover:-translate-y-0.5 hover:shadow-lift">
              {{ t('home.ctaExplore') }}
            </RouterLink>
            <RouterLink to="/how-it-works" class="btn-secondary transition-transform duration-200 hover:-translate-y-0.5">
              {{ t('home.ctaHow') }}
            </RouterLink>
            <RouterLink
              v-if="!auth.isAuthenticated"
              to="/login"
              class="btn-secondary transition-transform duration-200 hover:-translate-y-0.5"
            >{{ t('home.ctaPortal') }}</RouterLink>
            <RouterLink v-else :to="auth.homePath" class="btn-secondary transition-transform duration-200 hover:-translate-y-0.5">
              {{ t('home.ctaPortal') }}
            </RouterLink>
          </div>

          <dl v-reveal:5 class="mt-10 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div v-for="stat in stats" :key="stat.label()">
              <dt class="text-xs font-semibold uppercase tracking-wide text-ink-400">{{ stat.label() }}</dt>
              <dd class="mt-1 h-1 w-10 overflow-hidden rounded-full bg-brand-100">
                <span class="block h-full w-full origin-left rounded-full bg-brand-500 motion-safe:animate-[grow-x_1s_ease-out_0.4s_both]" />
              </dd>
            </div>
          </dl>
        </div>

        <!-- Hero illustration -->
        <div v-reveal:2 class="relative">
          <div class="relative overflow-hidden rounded-2xl border border-ink-200 bg-white shadow-card">
            <img
              :src="heroImage"
              alt="Illustration of a digital twin — a human figure formed by connected health data points"
              class="h-auto w-full"
              loading="eager"
            />
            <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-brand-900/10 via-transparent to-transparent" />
          </div>

          <!-- floating badge -->
          <div class="animate-float-slow absolute -bottom-5 left-6 flex items-center gap-3 rounded-xl border border-ink-200 bg-white/95 px-4 py-3 shadow-lift backdrop-blur">
            <span class="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-100">
              <svg class="h-5 w-5 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div class="leading-tight">
              <p class="text-sm font-bold text-ink-900">{{ t('home.safetyTitle') }}</p>
              <p class="text-[11px] text-ink-500">{{ t('brand.tagline') }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Capabilities -->
    <section class="container-page py-16">
      <h2 v-reveal class="section-title">{{ t('home.capabilitiesTitle') }}</h2>
      <div class="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <RouterLink
          v-for="(item, index) in capabilities"
          :key="item.key"
          v-reveal="index + 1"
          :to="item.to"
          class="card card-pad group transition-all duration-300 hover:-translate-y-1 hover:shadow-lift"
        >
          <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 transition-colors duration-300 group-hover:bg-brand-100">
            <svg class="h-6 w-6 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
              <path :d="item.icon" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <h3 class="mt-4 font-semibold">{{ t(`solutions.${item.key}Title`) }}</h3>
          <p class="muted mt-1.5 leading-relaxed">{{ t(`solutions.${item.key}Body`) }}</p>
        </RouterLink>
      </div>
    </section>

    <!-- Dark analytics band -->
    <section class="dark-band relative overflow-hidden py-16">
      <div aria-hidden="true" class="bg-mesh pointer-events-none absolute inset-0 opacity-30" />
      <img
        :src="analyticsImage"
        alt=""
        aria-hidden="true"
        class="animate-float-slower pointer-events-none absolute -right-20 -top-24 hidden w-[560px] opacity-20 mix-blend-screen lg:block"
        loading="lazy"
      />
      <div class="container-page relative grid items-center gap-10 lg:grid-cols-2">
        <div v-reveal>
          <span class="chip bg-white/10 text-teal-100 ring-1 ring-inset ring-white/15">TRUST, MEASURED</span>
          <h2 class="mt-4 text-3xl font-bold leading-tight tracking-tight text-white sm:text-4xl">
            Every answer carries its evidence
          </h2>
          <p class="mt-4 max-w-lg leading-relaxed text-brand-100/80">
            Retrieval, grounding checks, contradiction detection and risk routing run before an answer reaches you.
            The result is an interpretable indicator — never a guarantee of medical correctness.
          </p>
          <RouterLink
            to="/trust-safety"
            class="mt-7 inline-flex items-center gap-2 rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-navy-900
                   transition-transform duration-200 hover:-translate-y-0.5 hover:shadow-lift"
          >
            {{ t('nav.trust') }} →
          </RouterLink>
        </div>

        <div v-reveal:2 class="grid grid-cols-2 gap-6 sm:gap-8">
          <div v-for="(metric, index) in metrics" :key="metric.label" v-reveal="index + 2">
            <p class="stat-number">{{ metric.value }}</p>
            <p class="mt-1 text-sm text-brand-100/75">{{ metric.label }}</p>
            <span class="mt-3 block h-0.5 w-12 rounded-full bg-teal-400" />
          </div>
        </div>
      </div>
    </section>

    <!-- Document extraction feature -->
    <section class="container-page py-16">
      <div class="grid items-center gap-10 lg:grid-cols-2">
        <div v-reveal class="relative">
          <div class="overflow-hidden rounded-2xl border border-ink-200 bg-white shadow-card">
            <img
              :src="extractionImage"
              alt="Illustration of a medical report being organised into structured data cards"
              class="h-auto w-full transition-transform duration-700 hover:scale-[1.03]"
              loading="lazy"
            />
          </div>
        </div>
        <div v-reveal:1>
          <span class="section-eyebrow">From paper to structure</span>
          <h2 class="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">Your records, organised and traceable</h2>
          <p class="mt-4 leading-relaxed text-ink-600">
            Upload a report and MedTwin AI extracts the meaningful fields, keeps the original document attached,
            and waits for your confirmation before anything becomes part of your Digital Twin.
          </p>
          <ul class="mt-6 space-y-3">
            <li v-for="point in extractionPoints" :key="point" class="flex gap-3 text-sm text-ink-700">
              <span class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-teal-100">
                <svg class="h-3 w-3 text-teal-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" aria-hidden="true">
                  <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
              {{ point }}
            </li>
          </ul>
          <RouterLink to="/how-it-works" class="btn-secondary mt-7 transition-transform duration-200 hover:-translate-y-0.5">
            {{ t('home.ctaHow') }}
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- For patients & clinicians -->
    <section class="border-y border-ink-200/70 bg-white/60 py-16">
      <div class="container-page grid items-center gap-10 lg:grid-cols-2">
        <div v-reveal>
          <span class="section-eyebrow">Humans stay in the loop</span>
          <h2 class="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">Built for both sides of the consultation</h2>
          <div class="mt-7 space-y-4">
            <div
              v-for="(item, index) in audience"
              :key="item.title"
              v-reveal="index + 2"
              class="card card-pad transition-all duration-300 hover:-translate-y-1 hover:shadow-lift"
            >
              <h3 class="font-semibold">{{ item.title }}</h3>
              <p class="muted mt-1.5 leading-relaxed">{{ item.body }}</p>
              <RouterLink :to="item.to" class="mt-3 inline-block text-sm font-semibold text-brand-700 hover:underline">
                {{ item.cta }} →
              </RouterLink>
            </div>
          </div>
        </div>
        <div v-reveal:1 class="relative">
          <div class="overflow-hidden rounded-2xl border border-ink-200 bg-white shadow-card">
            <img
              :src="cliniciansImage"
              alt="Illustration of two clinicians reviewing a holographic health data display together"
              class="h-auto w-full transition-transform duration-700 hover:scale-[1.03]"
              loading="lazy"
            />
          </div>
          <div class="animate-float-slow absolute -bottom-4 -left-4 hidden rounded-xl border border-ink-200 bg-white/95 px-4 py-3 shadow-lift backdrop-blur sm:block">
            <p class="text-xs font-bold text-ink-800">Clinician-verified</p>
            <p class="text-[11px] text-ink-500">AI drafts are labelled, never silently applied</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Workflow -->
    <section class="border-y border-ink-200 bg-white/50 py-16">
      <div class="container-page">
        <h2 v-reveal class="section-title">{{ t('home.workflowTitle') }}</h2>
        <div class="mt-8 grid gap-4 md:grid-cols-4">
          <div
            v-for="(step, index) in workflow"
            :key="step.title"
            v-reveal="index + 1"
            class="group relative rounded-2xl border border-ink-200 p-5 transition-all duration-300 hover:border-brand-300 hover:shadow-card"
          >
            <p class="text-xs font-bold text-brand-600">0{{ index + 1 }}</p>
            <p class="mt-2 font-semibold">{{ step.title }}</p>
            <p class="muted mt-1">{{ step.body }}</p>
            <span class="absolute inset-x-5 bottom-0 h-0.5 origin-left scale-x-0 rounded-full bg-brand-500 transition-transform duration-300 group-hover:scale-x-100" />
          </div>
        </div>
      </div>
    </section>

    <!-- Safety note + disclaimer -->
    <section class="container-page py-16">
      <div class="grid gap-8 lg:grid-cols-2">
        <div v-reveal>
          <h2 class="section-title">{{ t('home.safetyTitle') }}</h2>
          <p class="mt-3 leading-relaxed text-ink-600">{{ t('home.safetyBody') }}</p>
          <RouterLink to="/trust-safety" class="btn-secondary mt-6 transition-transform duration-200 hover:-translate-y-0.5">
            {{ t('nav.trust') }}
          </RouterLink>
        </div>
        <div v-reveal:1>
          <MedicalDisclaimer />
        </div>
      </div>
      <p v-reveal class="mt-8 text-xs text-ink-400">{{ t('home.disclaimerNote') }}</p>
    </section>
  </div>
</template>
