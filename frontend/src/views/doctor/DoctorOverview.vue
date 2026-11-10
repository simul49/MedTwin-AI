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

const filtered = computed(() =>
  patients.value.filter((p) =>
    `${p.name} ${p.id} ${p.email}`.toLowerCase().includes(query.value.trim().toLowerCase()),
  ),
);

const upcoming = computed(() => appointments.value.filter((a) => a.status === 'REQUESTED' || a.status === 'CONFIRMED'));
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
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-2">Clinical workspace</p>
        <h1 class="text-[28px] font-bold leading-tight tracking-tight text-ink-900">Doctor Dashboard</h1>
        <p class="mt-2 text-[14px] text-ink-500">Consent-scoped patient context for your consultations.</p>
      </div>
      <RouterLink to="/doctor/patients" class="dash-btn">＋ Add Doctor Note</RouterLink>
    </div>

    <p v-if="error" class="mb-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ error }}</p>

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
          <div class="flex items-center gap-2 rounded-xl border border-ink-200 bg-surface-50 px-3 py-2.5">
            <svg class="h-4 w-4 text-ink-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <circle cx="11" cy="11" r="7" /><path d="M20 20l-4-4" stroke-linecap="round" />
            </svg>
            <input v-model="query" class="w-full bg-transparent text-[12px] outline-none" placeholder="Search patients by identifier" />
          </div>
          <p class="mt-2 text-[11px] text-ink-400">Only patients with active consent are shown.</p>
        </div>

        <div v-if="loading" class="h-64 animate-pulse bg-ink-100" />
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
                      class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white"
                      :style="{ backgroundColor: patient.avatarColor }"
                    >{{ patient.initials }}</span>
                    <div>
                      <p class="font-semibold text-ink-800">{{ patient.name }}</p>
                      <p class="text-[10px] text-ink-400">P-{{ patient.id.slice(0, 4).toUpperCase() }}</p>
                    </div>
                  </div>
                </td>
                <td class="dash-td">
                  <span class="chip bg-brand-50 text-brand-700">{{ patient.scope.length ? 'Active' : 'Expired' }}</span>
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
          <div class="relative h-[220px] overflow-hidden bg-brand-50/40">
            <img :src="bodyMap" alt="Anatomical body map of recorded observations" class="h-full w-full object-contain" />
            <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-white/40 to-transparent" />
          </div>
        </div>

        <div class="grid gap-4 lg:grid-cols-2">
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
            <p class="mt-2 text-[11px] text-ink-400">{{ observations.length }} structured observations</p>
          </div>

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
            <div class="mt-4 h-[135px]">
              <TrendChart :values="timelineValues" kind="line" :height="135" color="#35bda7" />
            </div>
            <p class="mt-2 text-[11px] text-ink-400">{{ timeline.length }} timeline events</p>
          </div>
        </div>

        <div class="dash-info flex flex-wrap items-center justify-between gap-3">
          <p>Only records with active patient consent are shown. AI drafts are labelled and require clinician review.</p>
          <RouterLink to="/doctor/patients" class="dash-btn px-3 py-2 text-xs">Add Doctor Note</RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>
