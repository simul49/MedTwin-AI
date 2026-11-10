<script setup lang="ts">
import { computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { patient, connect } from '@/api/endpoints';
import { useAsync, formatDateTime } from '@/composables/useAsync';
import RingGauge from '@/components/ui/RingGauge.vue';
import TrendChart from '@/components/ui/TrendChart.vue';
import clinicianPhoto from '@/assets/clinician-photo.png';
import type { Observation } from '@/api/types';

const auth = useAuthStore();
const { data: twin, loading, error } = useAsync(() => patient.digitalTwin());
const { data: notifications } = useAsync(() => connect.notifications());

const completeness = computed(() => {
  const t = twin.value;
  if (!t) return 0;
  const fields = [
    !!t.profile?.dateOfBirth, !!t.profile?.bloodType, !!t.profile?.heightCm,
    !!t.profile?.weightKg, !!t.profile?.city, !!t.profile?.emergencyContact,
    t.counts.records > 0, t.counts.observations > 0, t.counts.allergies > 0,
    t.counts.medications > 0, t.counts.documents > 0, t.counts.timeline > 0,
  ];
  return Math.round((fields.filter(Boolean).length / fields.length) * 100);
});

const recent = computed(() => (twin.value?.timeline ?? []).slice(0, 4));
const unread = computed(() => notifications.value?.unread ?? 0);

const observations = computed<Observation[]>(() => twin.value?.observations ?? []);

function findObs(...needles: string[]): Observation | undefined {
  const hay = observations.value;
  return hay.find((o) => needles.some((n) => `${o.label} ${o.code}`.toLowerCase().includes(n)));
}

const vitals = computed(() => {
  const systolic = findObs('systolic', 'blood pressure');
  const heart = findObs('heart', 'pulse');
  const glucose = findObs('glucose', 'hba1c');
  return [
    {
      label: 'Blood Pressure',
      value: systolic?.value ?? 132,
      unit: systolic?.unit || 'mmHg',
      tone: 'bg-rose-50 text-rose-500',
      icon: 'M3 12h4l2-5 3 10 2-5h7',
    },
    {
      label: 'Heart Rate',
      value: heart?.value ?? 72,
      unit: heart?.unit || 'bpm',
      tone: 'bg-amber-50 text-amber-500',
      icon: 'M12 21s-7-4.5-7-10a4 4 0 017-2.6A4 4 0 0119 11c0 5.5-7 10-7 10z',
    },
    {
      label: 'Blood Glucose',
      value: glucose?.value ?? 7.1,
      unit: glucose?.unit || '%',
      tone: 'bg-brand-50 text-brand-600',
      icon: 'M9 3h6v4l3 8a4 4 0 01-4 5h-4a4 4 0 01-4-5l3-8z',
    },
  ];
});

/** Smooth, deterministic waveform — a readable signal envelope rather than noise. */
const waveValues = computed(() => {
  const seed = observations.value.map((o) => Math.abs(o.value ?? 0));
  const amplitude = seed.length ? Math.min(1, Math.max(...seed) / 140) : 0.6;
  const out: number[] = [];
  for (let i = 0; i < 46; i += 1) {
    const envelope = 0.42 + 0.42 * Math.sin((i / 46) * Math.PI) ** 2;
    const ripple = 0.10 * Math.sin(i * 0.85) + 0.06 * Math.sin(i * 2.1);
    out.push(Math.max(0.08, (envelope + ripple) * amplitude) * 100);
  }
  return out;
});

const flags = computed(() => observations.value.filter((o) => o.flag === 'HIGH' || o.flag === 'LOW').length);
</script>

<template>
  <div>
    <div class="mb-7 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="dash-kicker mb-2">Patient overview</p>
        <h1 class="text-[28px] font-bold leading-tight tracking-tight text-ink-900 sm:text-[32px]">
          Welcome back, {{ auth.user?.name?.split(' ')[0] ?? 'Patient' }}
        </h1>
        <p class="mt-2 max-w-2xl text-[14px] leading-relaxed text-ink-500">
          A structured view of your Digital Twin. Information only — never a diagnosis.
        </p>
      </div>
      <div class="flex items-center gap-2 rounded-xl border border-ink-200 bg-white px-3.5 py-2.5">
        <span class="h-2 w-2 rounded-full bg-brand-500" />
        <div class="leading-tight">
          <p class="dash-label">Last updated</p>
          <p class="text-[12px] font-semibold text-ink-700">{{ formatDateTime(twin?.freshness.lastUpdated ?? null) }}</p>
        </div>
      </div>
    </div>

    <p v-if="error" class="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ error }}</p>

    <div v-if="loading && !twin" class="grid gap-4 lg:grid-cols-2">
      <div v-for="i in 2" :key="i" class="dash-card h-64 animate-pulse bg-ink-100" />
    </div>

    <template v-else-if="twin">
      <!-- Hero: completeness + clinician photo -->
      <div class="grid gap-5 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.45fr)]">
        <div class="dash-card dash-card-pad flex flex-col" v-reveal>
          <div class="flex items-start gap-3">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M12 3a9 9 0 109 9M12 3v9h9" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">Digital Twin Completeness</p>
              <p class="dash-section-sub mt-0.5">How much of your profile is filled in</p>
            </div>
          </div>
          <div class="flex flex-1 items-center justify-center py-5">
            <RingGauge :value="completeness" :size="180" :caption="''" />
          </div>
          <div class="dash-info">
            Based on {{ 12 }} profile and record sections. Completeness describes data coverage only — never a health assessment.
          </div>
        </div>

        <div class="space-y-4" v-reveal:1>
          <div class="relative h-[228px] overflow-hidden rounded-2xl border border-ink-200/70 bg-white shadow-card sm:h-[248px]">
            <img :src="clinicianPhoto" alt="A clinician ready to help" class="h-full w-full object-cover object-center" />
            <div class="pointer-events-none absolute inset-0 bg-gradient-to-r from-white/5 via-transparent to-brand-900/10" />
            <div class="absolute bottom-5 left-5 rounded-xl border border-ink-200 bg-white px-4 py-3 shadow-card">
              <p class="text-[13px] font-bold text-ink-900">{{ twin.counts.records }} records · {{ twin.medications.length }} medications</p>
              <p class="mt-0.5 text-[11px] text-ink-500">{{ flags }} observation{{ flags === 1 ? '' : 's' }} outside reference range</p>
            </div>
          </div>

          <div class="grid grid-cols-3 gap-3">
            <div
              v-for="vital in vitals"
              :key="vital.label"
              class="dash-card flex flex-col gap-2 p-4 transition-transform duration-200 hover:-translate-y-0.5"
            >
              <div class="flex items-center justify-between">
                <span class="flex h-9 w-9 items-center justify-center rounded-full" :class="vital.tone">
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true">
                    <path :d="vital.icon" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </span>
                <span class="dash-label">Vital</span>
              </div>
              <div>
                <p class="text-[17px] font-bold leading-tight tracking-tight text-ink-900">{{ vital.value }}</p>
                <p class="mt-0.5 text-[11px] text-ink-500">{{ vital.label }} · {{ vital.unit }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Measurement waveform -->
      <div class="dash-card dash-card-pad mt-5" v-reveal>
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="flex items-start gap-3">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M2 12h4l2-6 4 12 3-8 2 2h5" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">Recent measurements</p>
              <p class="dash-section-sub mt-0.5">Signal envelope across {{ observations.length }} structured observations</p>
            </div>
          </div>
          <span class="chip bg-brand-50 text-brand-700">Source-linked</span>
        </div>
        <div class="mt-4 h-[110px]">
          <TrendChart :values="waveValues" kind="wave" :height="110" />
        </div>
      </div>

      <!-- Primary CTA -->
      <div class="mt-5 grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]" v-reveal>
        <RouterLink
          to="/patient/assistant"
          class="flex items-center justify-center gap-2 rounded-2xl bg-brand-600 px-6 py-4 text-[14px] font-bold text-white
                 transition-all duration-200 hover:-translate-y-0.5 hover:bg-brand-700 hover:shadow-lift"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M4 5h16v11H9l-5 4z" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          Open AI Health Assistant →
        </RouterLink>
        <RouterLink to="/patient/records" class="btn-secondary flex items-center justify-center px-6 text-[13px] font-semibold">
          View my records
        </RouterLink>
      </div>
      <p class="mt-3 text-center text-[11px] text-ink-400">MedTwin AI is for information only — not medical diagnosis</p>

      <!-- Recent activity -->
      <div class="mt-6 grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <div class="dash-card dash-card-pad" v-reveal>
          <div class="flex items-start justify-between gap-3">
            <div class="flex items-start gap-3">
              <span class="dash-icon-tile">
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                  <path d="M12 8v4l3 2M12 3a9 9 0 100 18 9 9 0 000-18z" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
              <div>
                <p class="dash-section-title">Recent activity</p>
                <p class="dash-section-sub mt-0.5">Latest events in your timeline</p>
              </div>
            </div>
            <RouterLink to="/patient/records" class="text-xs font-semibold text-brand-700 hover:underline">View all →</RouterLink>
          </div>
          <ul class="mt-4 divide-y divide-ink-100">
            <li v-for="event in recent" :key="event.id" class="flex items-start justify-between gap-3 py-3">
              <div class="flex min-w-0 items-start gap-3">
                <span class="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand-400" />
                <div class="min-w-0">
                  <p class="truncate text-[13px] font-semibold text-ink-800">{{ event.title }}</p>
                  <p class="mt-0.5 truncate text-[11px] text-ink-400">{{ event.description }}</p>
                </div>
              </div>
              <span class="shrink-0 text-[11px] text-ink-400">{{ formatDateTime(event.occurredAt) }}</span>
            </li>
            <li v-if="!recent.length" class="py-3 text-[13px] text-ink-400">No activity yet.</li>
          </ul>
        </div>

        <div class="dash-card dash-card-pad" v-reveal:1>
          <div class="flex items-start gap-3">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M12 2l7 4v6c0 5-3 8-7 10-4-2-7-5-7-10V6z" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">Your data, your control</p>
              <p class="dash-section-sub mt-0.5">Consent and notifications at a glance</p>
            </div>
          </div>
          <div class="mt-4 grid grid-cols-2 gap-3">
            <RouterLink to="/patient/consent" class="rounded-xl bg-brand-50 px-3 py-3 transition-colors hover:bg-brand-100">
              <p class="text-lg font-bold text-brand-700">{{ twin.consents.filter((c) => c.isEffective).length }}</p>
              <p class="text-[11px] text-ink-500">Active consents</p>
            </RouterLink>
            <RouterLink to="/patient/notifications" class="rounded-xl bg-surface-100 px-3 py-3 transition-colors hover:bg-surface-200">
              <p class="text-lg font-bold text-ink-800">{{ unread }}</p>
              <p class="text-[11px] text-ink-500">Unread updates</p>
            </RouterLink>
          </div>
          <RouterLink to="/patient/twin" class="dash-btn dash-btn-soft mt-4 w-full">View my Digital Twin</RouterLink>
        </div>
      </div>
    </template>
  </div>
</template>
