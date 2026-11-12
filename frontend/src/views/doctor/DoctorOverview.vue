<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { doctor, connect } from '@/api/endpoints';
import { formatDate } from '@/composables/useAsync';
import TrendChart from '@/components/ui/TrendChart.vue';
import bodyMap from '@/assets/body-map.png';
import type { Appointment, DoctorPatient, Observation, TimelineEvent } from '@/api/types';

const patients = ref<DoctorPatient[]>([]);
const appointments = ref<Appointment[]>([]);
const observations = ref<Observation[]>([]);
const timeline = ref<TimelineEvent[]>([]);
const query = ref('');
const loading = ref(true);
const error = ref<string | null>(null);
const lastUpdated = ref<string | null>(null);

const filtered = computed(() =>
  patients.value.filter((p) =>
    `${p.name} ${p.id} ${p.email}`.toLowerCase().includes(query.value.trim().toLowerCase()),
  ),
);

const upcoming = computed(() =>
  appointments.value
    .filter((a) => a.status === 'REQUESTED' || a.status === 'CONFIRMED')
    .slice(0, 4),
);

const flagged = computed(() => observations.value.filter((o) => o.flag && o.flag !== 'NORMAL').length);

const stats = computed(() => [
  {
    label: 'Authorised patients',
    value: String(patients.value.length),
    icon: 'M16 19v-2a4 4 0 00-8 0v2M12 11a3 3 0 100-6 3 3 0 000 6z',
    tone: 'bg-brand-50 text-brand-700',
  },
  {
    label: 'Upcoming appointments',
    value: String(upcoming.value.length),
    icon: 'M8 3v3M16 3v3M4 8h16M5 5h14v14H5zM9 13h6M9 17h3',
    tone: 'bg-sky-50 text-sky-700',
  },
  {
    label: 'Flagged observations',
    value: String(flagged.value),
    icon: 'M12 5c4 3 7 3.4 7 8a7 7 0 11-14 0c0-4.6 3-5 7-8zM12 10v4',
    tone: flagged.value ? 'bg-amber-50 text-amber-700' : 'bg-brand-50 text-brand-700',
  },
  {
    label: 'Timeline events',
    value: String(timeline.value.length),
    icon: 'M4 6h16M4 12h16M4 18h10',
    tone: 'bg-violet-50 text-violet-700',
  },
]);

const labValues = computed(() => {
  const raw = observations.value.map((o) => Math.abs(o.value ?? 0)).filter((v) => v > 0);
  if (!raw.length) return [42, 78, 55, 92, 63, 84, 48, 98];
  // Log scaling keeps small lab values visible next to large ones (e.g. 1.2 vs 132).
  const max = Math.max(...raw);
  return raw.map((v) => 18 + (70 * Math.log1p(v)) / Math.log1p(max));
});
const timelineValues = computed(() => {
  const values = timeline.value.map((_, i) => 30 + ((i * 17) % 55));
  return values.length ? values : [62, 48, 70, 55, 78, 60, 84];
});

async function load() {
  loading.value = true;
  error.value = null;
  try {
    patients.value = (await doctor.patients()).results;
    appointments.value = (await connect.appointments()).results;
    const first = patients.value[0];
    if (first) {
      const summary = await doctor.summary(first.id);
      observations.value = summary.observations;
      timeline.value = summary.timeline;
    }
    lastUpdated.value = new Date().toISOString();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-teal-500 text-white shadow-lift">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M12 4v16M4 12h16" stroke-linecap="round" />
          </svg>
        </div>
        <div>
          <h1 class="text-[24px] font-bold leading-tight tracking-tight text-ink-900">Clinical Workspace</h1>
          <p class="mt-0.5 flex items-center gap-1.5 text-[12px] text-ink-500">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            Consent-scoped patient context · never a diagnosis
          </p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="lastUpdated" class="chip border border-ink-200 bg-white px-3 py-1.5 text-ink-500">
          Updated {{ formatDate(lastUpdated) }}
        </span>
        <RouterLink to="/doctor/patients" class="dash-btn">＋ Add Doctor Note</RouterLink>
      </div>
    </div>

    <p v-if="error" class="mb-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ error }}</p>

    <!-- KPI row -->
    <div class="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
      <div v-for="stat in stats" :key="stat.label" class="dash-card flex items-center gap-3.5 p-4">
        <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl" :class="stat.tone">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
            <path :d="stat.icon" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </span>
        <div class="min-w-0">
          <p class="truncate text-[11px] font-medium uppercase tracking-wide text-ink-400">{{ stat.label }}</p>
          <p class="mt-0.5 text-[22px] font-extrabold leading-none tracking-tight text-ink-900">{{ stat.value }}</p>
        </div>
      </div>
    </div>

    <div class="grid gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.35fr)]">
      <!-- Patient list -->
      <div class="dash-card overflow-hidden">
        <div class="border-b border-ink-100 p-5">
          <div class="mb-4 flex items-center gap-3">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M16 19v-2a4 4 0 00-8 0v2M12 11a3 3 0 100-6 3 3 0 000 6z" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">Patient List</p>
              <p class="dash-section-sub mt-0.5">Authorised by active consent</p>
            </div>
          </div>
          <div class="flex items-center gap-2 rounded-xl border border-ink-200 bg-surface-50 px-3 py-2.5 transition-colors focus-within:border-brand-400 focus-within:bg-white">
            <svg class="h-4 w-4 text-ink-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <circle cx="11" cy="11" r="7" /><path d="M20 20l-4-4" stroke-linecap="round" />
            </svg>
            <input v-model="query" class="w-full bg-transparent text-[12px] outline-none" placeholder="Search patients by identifier" />
          </div>
          <p class="mt-2 text-[11px] text-ink-400">Only patients with active consent are shown.</p>
        </div>

        <div v-if="loading" class="shimmer h-64 animate-pulse rounded-b-[18px] bg-ink-100" />
        <div v-else class="overflow-x-auto">
          <table class="dash-table-compact w-full min-w-[340px] border-collapse">
            <thead class="bg-surface-50">
              <tr>
                <th class="dash-th">Patient ID</th>
                <th class="dash-th">Consent Status</th>
                <th class="dash-th">Last Updated</th>
                <th class="dash-th">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="patient in filtered" :key="patient.id" class="dash-row">
                <td class="dash-td">
                  <div class="flex items-center gap-2.5">
                    <span
                      class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white shadow-card"
                      :style="{ backgroundColor: patient.avatarColor }"
                    >{{ patient.initials }}</span>
                    <div>
                      <p class="font-semibold text-ink-800">{{ patient.name }}</p>
                      <p class="text-[10px] text-ink-400">P-{{ patient.id.slice(0, 4).toUpperCase() }}</p>
                    </div>
                  </div>
                </td>
                <td class="dash-td">
                  <span class="chip" :class="patient.scope.length ? 'bg-brand-50 text-brand-700' : 'bg-surface-100 text-ink-500'">
                    {{ patient.scope.length ? 'Active' : 'Expired' }}
                  </span>
                </td>
                <td class="dash-td">{{ formatDate(patient.lastActivity) }}</td>
                <td class="dash-td">
                  <RouterLink :to="`/doctor/patients/${patient.id}`" class="font-semibold text-brand-700 hover:underline">View Twin</RouterLink>
                </td>
              </tr>
              <tr v-if="!filtered.length">
                <td colspan="4" class="dash-td py-8 text-center text-ink-400">No matching patients.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="border-t border-ink-100 px-4 py-3">
          <p class="text-[11px] text-ink-400">{{ filtered.length }} authorised patient{{ filtered.length === 1 ? '' : 's' }} · {{ upcoming.length }} upcoming appointment{{ upcoming.length === 1 ? '' : 's' }}</p>
        </div>
      </div>

      <!-- Clinical panels -->
      <div class="space-y-4">
        <div class="grid gap-4 lg:grid-cols-2">
          <!-- Next appointments -->
          <div class="dash-card dash-card-pad">
            <div class="flex items-start gap-3">
              <span class="dash-icon-tile">
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                  <path d="M8 3v3M16 3v3M4 8h16M5 5h14v14H5zM9 13h6M9 17h3" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
              <div>
                <p class="dash-section-title">Next appointments</p>
                <p class="dash-section-sub mt-0.5">Requested and confirmed</p>
              </div>
            </div>
            <ul v-if="upcoming.length" class="mt-4 space-y-2.5">
              <li v-for="appt in upcoming" :key="appt.id" class="flex items-center gap-3 rounded-xl border border-ink-100 bg-surface-50 px-3 py-2.5">
                <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-50 text-[10px] font-bold text-brand-700">
                  {{ appt.patientName.slice(0, 2).toUpperCase() }}
                </span>
                <div class="min-w-0 flex-1">
                  <p class="truncate text-[12.5px] font-semibold text-ink-800">{{ appt.patientName }}</p>
                  <p class="text-[10.5px] text-ink-400">{{ formatDate(appt.scheduledAt) }} · {{ appt.durationMin }} min</p>
                </div>
                <span class="chip" :class="appt.status === 'CONFIRMED' ? 'bg-brand-50 text-brand-700' : 'bg-amber-50 text-amber-700'">
                  {{ appt.status === 'CONFIRMED' ? 'Confirmed' : 'Requested' }}
                </span>
              </li>
            </ul>
            <p v-else class="mt-4 rounded-xl border border-dashed border-ink-200 px-3 py-6 text-center text-[12px] text-ink-400">
              No upcoming appointments.
            </p>
          </div>

          <!-- Lab results -->
          <div class="dash-card dash-card-pad">
            <div class="flex items-start gap-3">
              <span class="dash-icon-tile">
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                  <path d="M9 3h6v4l3 8a4 4 0 01-4 5h-4a4 4 0 01-4-5l3-8z" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
              <div>
                <p class="dash-section-title">Lab Results</p>
                <p class="dash-section-sub mt-0.5">Log-scaled latest values</p>
              </div>
            </div>
            <div class="mt-4 h-[135px]">
              <TrendChart :values="labValues" kind="bars" :height="135" />
            </div>
            <p class="mt-2 text-[11px] text-ink-400">{{ observations.length }} structured observations · {{ flagged }} flagged</p>
          </div>
        </div>

        <!-- Body map -->
        <div class="dash-card overflow-hidden">
          <div class="flex items-center justify-between border-b border-ink-100 px-5 py-4">
            <div class="flex items-center gap-3">
              <span class="dash-icon-tile">
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                  <path d="M12 3a4 4 0 110 8 4 4 0 010-8zM4 21a8 8 0 0116 0" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
              <div>
                <p class="dash-section-title">Medical History</p>
                <p class="dash-section-sub mt-0.5">Body map of consented observations</p>
              </div>
            </div>
            <span class="chip bg-brand-50 text-brand-700">Consent-scoped</span>
          </div>
          <div class="relative h-[200px] overflow-hidden bg-brand-50/40">
            <img :src="bodyMap" alt="Anatomical body map of recorded observations" class="h-full w-full object-contain" />
            <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-white/40 to-transparent" />
          </div>
        </div>

        <!-- Timeline chart -->
        <div class="dash-card dash-card-pad">
          <div class="flex items-start gap-3">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M3 12h4l2-5 3 10 2-5h7" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">Timeline</p>
              <p class="dash-section-sub mt-0.5">Recent clinical events</p>
            </div>
          </div>
          <div class="mt-4 h-[110px]">
            <TrendChart :values="timelineValues" kind="line" :height="110" color="#35bda7" />
          </div>
          <p class="mt-2 text-[11px] text-ink-400">{{ timeline.length }} timeline events</p>
        </div>
      </div>
    </div>

    <div class="dash-info mt-4 flex flex-wrap items-center justify-between gap-3">
      <p>Only records with active patient consent are shown. AI drafts are labelled and require clinician review.</p>
      <RouterLink to="/doctor/patients" class="dash-btn px-3 py-2 text-xs">Add Doctor Note</RouterLink>
    </div>
  </div>
</template>
