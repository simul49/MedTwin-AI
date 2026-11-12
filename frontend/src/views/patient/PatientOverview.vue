<script setup lang="ts">
import { computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { patient, connect } from '@/api/endpoints';
import { useAsync, formatDateTime } from '@/composables/useAsync';
import TrendChart from '@/components/ui/TrendChart.vue';
import bodyMap from '@/assets/body-map.png';
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

const observations = computed<Observation[]>(() => twin.value?.observations ?? []);

function findObs(...needles: string[]): Observation | undefined {
  const hay = observations.value;
  return hay.find((o) => needles.some((n) => `${o.label} ${o.code}`.toLowerCase().includes(n)));
}

interface Vital {
  key: string;
  label: string;
  display: string;
  unit: string;
  flag: string;
  note: string;
  spark: number[];
  annotationStyle: string;
}

/** Deterministic mini-sparkline seeded by the measured value. */
function sparkFor(value: number, level = 1): number[] {
  const base = Math.min(1, Math.abs(value) / 100) || 0.5;
  const out: number[] = [];
  for (let i = 0; i < 16; i += 1) {
    const wave = 0.55 + 0.3 * Math.sin((i / 16) * Math.PI * 2 * level + base * 6);
    out.push(Math.max(0.15, wave * base + 0.12) * 100);
  }
  return out;
}

function vitalFrom(obs: Observation | undefined, fallback: string, partial: Omit<Vital, 'display' | 'flag'>): Vital {
  let display = obs?.displayValue || fallback;
  const unit = partial.unit;
  // displayValue often embeds the unit ("132 mmHg") — strip it so the template shows one unit.
  if (unit && display.toLowerCase().includes(unit.toLowerCase())) {
    display = display.replace(new RegExp(unit.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i'), '').trim();
  }
  return {
    ...partial,
    display,
    flag: obs?.flag || 'NORMAL',
  };
}

const vitals = computed<Vital[]>(() => {
  const heart = findObs('heart', 'pulse');
  const bp = findObs('systolic', 'blood pressure');
  const spo2 = findObs('spo2', 'oxygen');
  const glucose = findObs('glucose', 'hba1c');
  const hrv = findObs('hrv', 'variability');
  const list: Vital[] = [
    vitalFrom(heart, '72', {
      key: 'heart', label: 'Heart Rate', unit: 'bpm', note: 'Resting pulse',
      spark: sparkFor(heart?.value ?? 72, 3), annotationStyle: 'left-[8%] top-[30%]',
    }),
    vitalFrom(bp, '132', {
      key: 'bp', label: 'Blood Pressure', unit: bp?.unit || 'mmHg', note: 'Systolic reading',
      spark: sparkFor(bp?.value ?? 132, 2), annotationStyle: 'left-[55%] top-[14%]',
    }),
    vitalFrom(spo2, '97', {
      key: 'spo2', label: 'SpO₂', unit: '%', note: 'Oxygen saturation',
      spark: sparkFor(spo2?.value ?? 97, 1.4), annotationStyle: 'left-[46%] top-[62%]',
    }),
    vitalFrom(glucose, '7.1', {
      key: 'glucose', label: 'Blood Glucose', unit: glucose?.unit || 'mmol/L', note: 'Latest panel',
      spark: sparkFor(glucose?.value ?? 7.1, 2.2), annotationStyle: 'left-[10%] top-[74%]',
    }),
  ];
  if (hrv) {
    list.push(vitalFrom(hrv, '46', {
      key: 'hrv', label: 'HRV', unit: hrv.unit || 'ms', note: 'Autonomic balance',
      spark: sparkFor(hrv.value ?? 46, 2.6), annotationStyle: 'left-[64%] top-[48%]',
    }));
  }
  return list;
});

const vitalsNoBp = computed(() => vitals.value.filter((v) => v.key !== 'bp'));

/** Flagged observations become twin insight cards, worst first. */
const severityOf = (flag: string) =>
  flag === 'CRITICAL' ? 'HIGH' : flag === 'HIGH' ? 'MEDIUM' : flag === 'LOW' ? 'LOW' : null;

const insights = computed(() =>
  observations.value
    .filter((o) => severityOf(o.flag))
    .sort((a, b) => (severityOf(b.flag) === 'HIGH' ? 1 : 0) - (severityOf(a.flag) === 'HIGH' ? 1 : 0))
    .slice(0, 4)
    .map((o) => ({
      id: o.id,
      level: severityOf(o.flag) as 'HIGH' | 'MEDIUM' | 'LOW',
      title: o.label,
      body: `${o.displayValue}${o.unit && !o.displayValue.toLowerCase().includes(o.unit.toLowerCase()) ? ` ${o.unit}` : ''} — outside the expected range${o.referenceRange ? ` (${o.referenceRange})` : ''}.`,
      when: o.observedAt,
    })),
);

const recent = computed(() => (twin.value?.timeline ?? []).slice(0, 4));
const unread = computed(() => notifications.value?.unread ?? 0);
const activeConsents = computed(() => twin.value?.consents.filter((c) => c.isEffective).length ?? 0);
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
        <span class="h-2 w-2 animate-pulse rounded-full bg-brand-500" />
        <div class="leading-tight">
          <p class="dash-label">Last sync</p>
          <p class="text-[12px] font-semibold text-ink-700">{{ formatDateTime(twin?.freshness.lastUpdated ?? null) }}</p>
        </div>
      </div>
    </div>

    <p v-if="error" class="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ error }}</p>

    <div v-if="loading && !twin" class="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)_320px]">
      <div v-for="i in 3" :key="i" class="shimmer h-[540px] animate-pulse rounded-[18px] bg-ink-100" />
    </div>

    <template v-else-if="twin">
      <div class="grid gap-5 xl:grid-cols-[280px_minmax(0,1fr)_320px]">
        <!-- Left rail: monitoring status + vitals -->
        <div class="space-y-3" v-reveal>
          <div class="dash-card dash-card-pad">
            <div class="flex items-center justify-between">
              <div>
                <p class="dash-section-title">Active Monitoring</p>
                <p class="dash-section-sub mt-0.5">Patient ID · P-{{ auth.user?.id?.slice(0, 4).toUpperCase() ?? '····' }}</p>
              </div>
              <span class="chip bg-brand-50 text-brand-700">Active</span>
            </div>
            <dl class="mt-4 grid grid-cols-2 gap-x-3 gap-y-3 text-[12px]">
              <div>
                <dt class="text-[10px] font-semibold uppercase tracking-wide text-ink-400">Data points</dt>
                <dd class="mt-0.5 font-bold text-ink-800">{{ twin.counts.observations.toLocaleString() }}</dd>
              </div>
              <div>
                <dt class="text-[10px] font-semibold uppercase tracking-wide text-ink-400">Records</dt>
                <dd class="mt-0.5 font-bold text-ink-800">{{ twin.counts.records }}</dd>
              </div>
              <div>
                <dt class="text-[10px] font-semibold uppercase tracking-wide text-ink-400">Consents</dt>
                <dd class="mt-0.5 font-bold text-ink-800">{{ activeConsents }} active</dd>
              </div>
              <div>
                <dt class="text-[10px] font-semibold uppercase tracking-wide text-ink-400">Medications</dt>
                <dd class="mt-0.5 font-bold text-ink-800">{{ twin.medications.length }}</dd>
              </div>
            </dl>
          </div>

          <div
            v-for="vital in vitals"
            :key="vital.key"
            class="dash-card p-4"
          >
            <div class="flex items-start justify-between">
              <p class="text-[12.5px] font-semibold text-ink-700">{{ vital.label }}</p>
              <span
                class="text-[13px] font-bold"
                :class="vital.flag === 'HIGH' || vital.flag === 'CRITICAL' ? 'text-terracotta'
                  : vital.flag === 'LOW' ? 'text-brand-600' : 'text-brand-700'"
              >
                {{ vital.flag === 'HIGH' || vital.flag === 'CRITICAL' ? '↑' : vital.flag === 'LOW' ? '↓' : '→' }}
              </span>
            </div>
            <p class="mt-1">
              <span
                class="text-[30px] font-extrabold leading-none tracking-tight"
                :class="vital.flag === 'HIGH' || vital.flag === 'CRITICAL' ? 'text-terracotta-dark'
                  : vital.flag === 'LOW' ? 'text-brand-600' : 'text-ink-900'"
              >{{ vital.display }}</span>
              <span class="ml-1 text-[12px] font-medium text-ink-400">{{ vital.unit }}</span>
            </p>
            <div class="mt-2 h-9">
              <TrendChart :values="vital.spark" kind="bars" :height="36" color="#101585" />
            </div>
            <p class="mt-1.5 text-[10.5px] text-ink-400">{{ vital.note }}</p>
          </div>
        </div>

        <!-- Center: twin body hero with floating annotations -->
        <div class="dash-card relative overflow-hidden" v-reveal:1>
          <div class="pointer-events-none absolute inset-0 bg-gradient-to-b from-brand-50/60 via-transparent to-lavender-light/30" />
          <div class="relative flex h-full min-h-[540px] flex-col">
            <div class="flex items-center justify-between px-5 pt-5">
              <div class="flex items-center gap-3">
                <span class="dash-icon-tile">
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <path d="M12 3a4 4 0 110 8 4 4 0 010-8zM4 21a8 8 0 0116 0" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </span>
                <div>
                  <p class="dash-section-title">Live Twin View</p>
                  <p class="dash-section-sub mt-0.5">Annotated signals from your records</p>
                </div>
              </div>
              <span class="chip border border-brand-100 bg-white/80 text-brand-700 backdrop-blur">Twin completeness {{ completeness }}%</span>
            </div>

            <div class="relative flex-1">
              <img :src="bodyMap" alt="Anatomical map of your Digital Twin" class="absolute inset-0 mx-auto h-full w-full max-w-[520px] object-contain px-2 pb-28 pt-4" />
              <!-- Floating glass annotations -->
              <div
                v-for="(vital, i) in vitalsNoBp"
                :key="vital.key"
                class="absolute w-[178px] rounded-2xl border border-white/70 bg-white/75 px-3.5 py-2.5 shadow-card backdrop-blur-md transition-transform duration-300 hover:scale-[1.03]"
                :class="vital.annotationStyle"
                :style="{ animation: `fade-up 0.5s ease-out ${0.15 * i + 0.2}s both` }"
              >
                <p class="text-[10.5px] font-semibold uppercase tracking-wide text-ink-400">{{ vital.label }}</p>
                <p class="mt-0.5 text-[15px] font-extrabold text-ink-900">
                  {{ vital.display }} <span class="text-[11px] font-medium text-ink-400">{{ vital.unit }}</span>
                </p>
                <span class="absolute -bottom-1.5 left-6 h-3 w-3 rounded-full border-2 border-white bg-brand-500 shadow" />
              </div>

              <!-- Summary report glass card -->
              <div class="absolute bottom-5 left-1/2 w-[min(420px,88%)] -translate-x-1/2 rounded-2xl border border-white/70 bg-white/80 px-5 py-4 shadow-lift backdrop-blur-md">
                <div class="flex items-center justify-between">
                  <p class="text-[13.5px] font-bold text-ink-900">Summary Report</p>
                  <RouterLink
                    to="/patient/assistant"
                    class="rounded-lg bg-brand-600 px-3 py-1.5 text-[11px] font-bold text-white transition-colors hover:bg-brand-700"
                  >Suggested action</RouterLink>
                </div>
                <div class="mt-3 grid grid-cols-3 gap-2 text-center">
                  <div>
                    <p class="text-[10px] font-semibold uppercase tracking-wide text-ink-400">Data points</p>
                    <p class="mt-0.5 text-[18px] font-extrabold text-ink-900">{{ twin.counts.observations.toLocaleString() }}</p>
                  </div>
                  <div class="border-x border-ink-100">
                    <p class="text-[10px] font-semibold uppercase tracking-wide text-ink-400">Completeness</p>
                    <p class="mt-0.5 text-[18px] font-extrabold text-brand-700">{{ completeness }} %</p>
                  </div>
                  <div>
                    <p class="text-[10px] font-semibold uppercase tracking-wide text-ink-400">Anomalies</p>
                    <p class="mt-0.5 text-[18px] font-extrabold" :class="insights.length ? 'text-terracotta-dark' : 'text-ink-900'">{{ insights.length }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right rail: AI-detected insights -->
        <div class="space-y-3" v-reveal:2>
          <div class="flex items-center justify-between px-1">
            <p class="dash-section-title">Twin Insights</p>
            <span class="dash-label">AI detected</span>
          </div>

          <template v-if="insights.length">
            <div
              v-for="insight in insights"
              :key="insight.id"
              class="dash-card p-4"
            >
              <div class="flex items-center justify-between">
                <span
                  class="chip"
                  :class="insight.level === 'HIGH' ? 'bg-terracotta-light text-terracotta-dark'
                    : insight.level === 'MEDIUM' ? 'bg-amber-50 text-amber-700' : 'bg-sky-50 text-sky-700'"
                >
                  <span class="h-1.5 w-1.5 rounded-full current-color" :class="insight.level === 'HIGH' ? 'bg-terracotta' : insight.level === 'MEDIUM' ? 'bg-amber-500' : 'bg-sky-500'" />
                  {{ insight.level }}
                </span>
              </div>
              <p class="mt-2 text-[13.5px] font-bold text-ink-900">{{ insight.title }}</p>
              <p class="mt-1 text-[12px] leading-relaxed text-ink-600">{{ insight.body }}</p>
              <div class="mt-3 flex items-center justify-between border-t border-ink-100 pt-2.5">
                <span class="text-[10.5px] font-medium text-ink-400">Twin insight · source-linked</span>
                <span class="text-[10.5px] text-ink-400">{{ formatDateTime(insight.when) }}</span>
              </div>
            </div>
          </template>

          <div v-else class="dash-card dash-card-pad text-center">
            <span class="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-brand-50">
              <svg class="h-5 w-5 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <p class="mt-3 text-[13.5px] font-bold text-ink-900">All readings in range</p>
            <p class="mt-1 text-[12px] leading-relaxed text-ink-500">
              No observation is currently flagged outside its reference range. New results appear here automatically.
            </p>
          </div>

          <div class="dash-card p-4">
            <p class="text-[12.5px] font-semibold text-ink-700">Recent activity</p>
            <ul class="mt-2.5 space-y-2.5">
              <li v-for="event in recent.slice(0, 3)" :key="event.id" class="flex items-start gap-2.5">
                <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-400" />
                <div class="min-w-0">
                  <p class="truncate text-[12px] font-semibold text-ink-800">{{ event.title }}</p>
                  <p class="truncate text-[10.5px] text-ink-400">{{ formatDateTime(event.occurredAt) }}</p>
                </div>
              </li>
              <li v-if="!recent.length" class="text-[12px] text-ink-400">No activity yet.</li>
            </ul>
            <RouterLink to="/patient/records" class="mt-3 inline-block text-[11px] font-semibold text-brand-700 hover:underline">View all →</RouterLink>
          </div>
        </div>
      </div>

      <!-- Primary CTA -->
      <div class="mt-6 grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]" v-reveal>
        <RouterLink
          to="/patient/assistant"
          class="flex items-center justify-center gap-2 rounded-2xl bg-brand-600 px-6 py-4 text-[14px] font-bold text-white
                 transition-all duration-200 hover:-translate-y-0.5 hover:bg-brand-700 hover:shadow-lift"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M4 5h16v11H9l-5 4z" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          Ask the AI Health Assistant about these results →
        </RouterLink>
        <RouterLink to="/patient/records" class="btn-secondary flex items-center justify-center px-6 text-[13px] font-semibold">
          View my records
        </RouterLink>
      </div>
      <p class="mt-3 text-center text-[11px] text-ink-400">MedTwin AI is for information only — not medical diagnosis</p>
    </template>
  </div>
</template>
