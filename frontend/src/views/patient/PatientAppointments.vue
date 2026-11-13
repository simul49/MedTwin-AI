<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useUiStore } from '@/stores/ui';
import { connect, auth as authApi } from '@/api/endpoints';
import { formatDateTime } from '@/composables/useAsync';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import type { Appointment } from '@/api/types';

const { t } = useI18n();
const ui = useUiStore();

const appointments = ref<Appointment[]>([]);
const doctors = ref<{ id: string; name: string }[]>([]);
const form = ref({ doctorId: '', scheduledAt: '', reason: '' });
const saving = ref(false);
const loading = ref(true);
const error = ref<string | null>(null);
const success = ref(false);

const counts = computed(() => ({
  upcoming: appointments.value.filter((a) => ['REQUESTED', 'CONFIRMED'].includes(a.status)).length,
  completed: appointments.value.filter((a) => a.status === 'COMPLETED').length,
  cancelled: appointments.value.filter((a) => ['CANCELLED', 'DECLINED'].includes(a.status)).length,
}));

const UPCOMING = ['REQUESTED', 'CONFIRMED'];

/** Soonest upcoming first, then most recent past visits. */
const sorted = computed(() => {
  const upcoming = appointments.value
    .filter((a) => UPCOMING.includes(a.status))
    .sort((a, b) => (a.scheduledAt ?? '').localeCompare(b.scheduledAt ?? ''));
  const past = appointments.value
    .filter((a) => !UPCOMING.includes(a.status))
    .sort((a, b) => (b.scheduledAt ?? '').localeCompare(a.scheduledAt ?? ''));
  return [...upcoming, ...past];
});

const nextAppointment = computed(() => sorted.value.find((a) => UPCOMING.includes(a.status)) ?? null);

function tileClass(status: string): string {
  if (status === 'CONFIRMED') return 'border-brand-200 bg-brand-50 text-brand-700';
  if (status === 'REQUESTED') return 'border-lavender-light bg-lavender-light/50 text-lavender-dark';
  if (status === 'COMPLETED') return 'border-ink-200 bg-surface-100 text-ink-600';
  return 'border-rose-200 bg-rose-50 text-rose-500';
}

/** "Today", "Tomorrow", "In 12 days", "8 days ago" — empty beyond that. */
function relativeLabel(value: string | null): string {
  const date = value ? new Date(value) : null;
  if (!date || Number.isNaN(date.getTime())) return '';
  const days = Math.round((date.getTime() - Date.now()) / 86_400_000);
  if (days === 0) return 'Today';
  if (days === 1) return 'Tomorrow';
  if (days > 1 && days <= 30) return `In ${days} days`;
  if (days < 0 && days >= -30) return `${Math.abs(days)} days ago`;
  return '';
}

function calendarParts(value: string | null) {
  const date = value ? new Date(value) : null;
  if (!date || Number.isNaN(date.getTime())) return { day: '—', month: '' };
  return {
    day: String(date.getDate()).padStart(2, '0'),
    month: date.toLocaleString(ui.locale === 'zh' ? 'zh-CN' : 'en-US', { month: 'short' }),
  };
}

async function load() {
  error.value = null;
  loading.value = true;
  try {
    appointments.value = (await connect.appointments()).results;
    doctors.value = (await authApi.doctors()).results;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

async function create() {
  if (!form.value.doctorId || !form.value.scheduledAt) return;
  saving.value = true;
  error.value = null;
  success.value = false;
  try {
    await connect.createAppointment({
      doctorId: form.value.doctorId,
      scheduledAt: new Date(form.value.scheduledAt).toISOString(),
      reason: form.value.reason,
    });
    form.value = { doctorId: '', scheduledAt: '', reason: '' };
    success.value = true;
    setTimeout(() => (success.value = false), 5000);
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    saving.value = false;
  }
}

async function cancel(appointment: Appointment) {
  if (!window.confirm(t('common.confirm'))) return;
  await connect.updateAppointment(appointment.id, { status: 'CANCELLED' });
  await load();
}

onMounted(load);
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-2">Care schedule</p>
        <h1 class="text-[28px] font-bold leading-tight tracking-tight text-ink-900">{{ t('patient.appointmentsTitle') }}</h1>
        <p class="mt-2 text-[14px] text-ink-500">Request a visit and keep track of upcoming consultations.</p>
      </div>
      <span class="chip border border-ink-200 bg-white text-ink-600">{{ appointments.length }} total</span>
    </div>

    <p v-if="error" class="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ error }}</p>

    <!-- Summary strip -->
    <div class="mb-5 grid gap-4 sm:grid-cols-3">
      <div v-for="stat in [
        { label: 'Upcoming', value: counts.upcoming, tone: 'bg-brand-50 text-brand-700', icon: 'M7 2v3M17 2v3M3 8h18M4 5h16v16H4z' },
        { label: 'Completed', value: counts.completed, tone: 'bg-lavender-light/50 text-lavender-dark', icon: 'M4 5h16v11H9l-5 4zM9 10l2 2 4-4' },
        { label: 'Cancelled', value: counts.cancelled, tone: 'bg-surface-100 text-ink-600', icon: 'M6 6l12 12M18 6L6 18' },
      ]" :key="stat.label" class="dash-card flex items-center justify-between px-5 py-4">
        <div>
          <p class="dash-label">{{ stat.label }}</p>
          <p class="mt-1 text-2xl font-extrabold leading-none tracking-tight text-ink-900">{{ stat.value }}</p>
        </div>
        <span class="dash-icon-tile" :class="stat.tone">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
            <path :d="stat.icon" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </span>
      </div>
    </div>

    <div class="grid items-start gap-5 lg:grid-cols-[minmax(0,1.55fr)_minmax(0,1fr)]">
      <!-- Appointment list -->
      <div class="dash-card overflow-hidden">
        <div class="flex items-start gap-3 border-b border-ink-100 px-5 py-4">
          <span class="dash-icon-tile">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M7 2v3M17 2v3M3 8h18M4 5h16v16H4z" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <div>
            <p class="dash-section-title">{{ t('patient.appointmentsTitle') }}</p>
            <p class="dash-section-sub mt-0.5">Your consultation history</p>
          </div>
        </div>

        <div v-if="loading" class="shimmer h-40 animate-pulse bg-ink-100" />
        <div v-else-if="!sorted.length" class="px-5 py-12 text-center">
          <p class="text-[14px] font-semibold text-ink-700">No appointments yet</p>
          <p class="mt-1 text-[12px] text-ink-400">Use the form to request your first visit.</p>
        </div>
        <ul v-else class="divide-y divide-ink-100">
          <li
            v-for="appointment in sorted"
            :key="appointment.id"
            class="flex flex-wrap items-center gap-4 px-5 py-3.5 transition-colors hover:bg-surface-50/70"
            :class="appointment.id === nextAppointment?.id ? 'bg-brand-50/40' : ''"
          >
            <div class="flex h-14 w-14 shrink-0 flex-col items-center justify-center rounded-xl border leading-none" :class="tileClass(appointment.status)">
              <span class="text-[17px] font-extrabold">{{ calendarParts(appointment.scheduledAt).day }}</span>
              <span class="mt-0.5 text-[10px] font-bold uppercase tracking-wide">{{ calendarParts(appointment.scheduledAt).month }}</span>
            </div>
            <div class="min-w-[160px] flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <p class="text-[14px] font-semibold text-ink-900">{{ appointment.doctorName || 'Clinician' }}</p>
                <span
                  v-if="appointment.id === nextAppointment?.id"
                  class="rounded-full bg-brand-600 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white"
                >Next visit</span>
              </div>
              <p class="mt-0.5 text-[12px] text-ink-500">
                {{ formatDateTime(appointment.scheduledAt, ui.locale) }}
                <span v-if="relativeLabel(appointment.scheduledAt)" class="font-semibold text-brand-700">· {{ relativeLabel(appointment.scheduledAt) }}</span>
              </p>
              <p v-if="appointment.reason" class="mt-1 text-[12px] text-ink-400">{{ appointment.reason }}</p>
            </div>
            <div class="flex shrink-0 items-center gap-2">
              <StatusBadge :status="appointment.status" />
              <button
                v-if="['REQUESTED', 'CONFIRMED'].includes(appointment.status)"
                class="rounded-lg border border-rose-200 px-3 py-1.5 text-[11px] font-semibold text-rose-600 transition-colors hover:bg-rose-50"
                @click="cancel(appointment)"
              >
                Cancel
              </button>
            </div>
          </li>
        </ul>
      </div>

      <!-- Request form -->
      <div class="dash-card dash-card-pad">
        <div class="flex items-start gap-3">
          <span class="dash-icon-tile">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M12 5v14M5 12h14" stroke-linecap="round" />
            </svg>
          </span>
          <div>
            <p class="dash-section-title">{{ t('patient.requestAppointment') }}</p>
            <p class="dash-section-sub mt-0.5">Choose a clinician and a preferred time</p>
          </div>
        </div>

        <form class="mt-5 space-y-4" @submit.prevent="create">
          <div>
            <label class="label" for="a-doctor">Select a professional</label>
            <select id="a-doctor" v-model="form.doctorId" class="input" required>
              <option value="">Choose a clinician</option>
              <option v-for="doctor in doctors" :key="doctor.id" :value="doctor.id">{{ doctor.name }}</option>
            </select>
          </div>
          <div>
            <label class="label" for="a-when">Date &amp; time</label>
            <input id="a-when" v-model="form.scheduledAt" class="input" type="datetime-local" required />
          </div>
          <div>
            <label class="label" for="a-reason">Reason for visit</label>
            <textarea id="a-reason" v-model="form.reason" class="input min-h-24" placeholder="Briefly describe what you would like to discuss" />
          </div>
          <button class="dash-btn w-full" type="submit" :disabled="saving">
            {{ saving ? 'Sending request…' : t('patient.requestAppointment') }}
          </button>
        </form>
        <div v-if="success" class="mt-3 flex items-center gap-2 rounded-xl border border-brand-200 bg-brand-50 px-3.5 py-2.5 text-[12px] font-semibold text-brand-700">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">
            <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          Request sent — your clinician will confirm shortly.
        </div>
        <div class="dash-info mt-4">Requests stay pending until the clinician confirms them.</div>
      </div>
    </div>
  </div>
</template>
