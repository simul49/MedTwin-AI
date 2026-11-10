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

const counts = computed(() => ({
  upcoming: appointments.value.filter((a) => ['REQUESTED', 'CONFIRMED'].includes(a.status)).length,
  completed: appointments.value.filter((a) => a.status === 'COMPLETED').length,
  cancelled: appointments.value.filter((a) => ['CANCELLED', 'DECLINED'].includes(a.status)).length,
}));

const sorted = computed(() =>
  [...appointments.value].sort((a, b) => (b.scheduledAt ?? '').localeCompare(a.scheduledAt ?? '')),
);

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
  try {
    await connect.createAppointment({
      doctorId: form.value.doctorId,
      scheduledAt: new Date(form.value.scheduledAt).toISOString(),
      reason: form.value.reason,
    });
    form.value = { doctorId: '', scheduledAt: '', reason: '' };
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
        { label: 'Upcoming', value: counts.upcoming, tone: 'bg-brand-50 text-brand-700' },
        { label: 'Completed', value: counts.completed, tone: 'bg-emerald-50 text-emerald-700' },
        { label: 'Cancelled', value: counts.cancelled, tone: 'bg-surface-100 text-ink-600' },
      ]" :key="stat.label" class="dash-card flex items-center justify-between px-5 py-4">
        <div>
          <p class="dash-label">{{ stat.label }}</p>
          <p class="mt-1 text-2xl font-extrabold leading-none tracking-tight text-ink-900">{{ stat.value }}</p>
        </div>
        <span class="dash-icon-tile" :class="stat.tone">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
            <path d="M7 2v3M17 2v3M3 8h18M4 5h16v16H4z" stroke-linecap="round" stroke-linejoin="round" />
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

        <div v-if="loading" class="h-40 animate-pulse bg-ink-100" />
        <div v-else-if="!sorted.length" class="px-5 py-12 text-center">
          <p class="text-[14px] font-semibold text-ink-700">No appointments yet</p>
          <p class="mt-1 text-[12px] text-ink-400">Use the form to request your first visit.</p>
        </div>
        <ul v-else class="divide-y divide-ink-100">
          <li v-for="appointment in sorted" :key="appointment.id" class="flex flex-wrap items-center gap-4 px-5 py-4 transition-colors hover:bg-surface-50/70">
            <div class="flex h-14 w-14 shrink-0 flex-col items-center justify-center rounded-xl border border-brand-100 bg-brand-50 leading-none">
              <span class="text-[17px] font-extrabold text-brand-700">{{ calendarParts(appointment.scheduledAt).day }}</span>
              <span class="mt-0.5 text-[10px] font-bold uppercase tracking-wide text-brand-600">{{ calendarParts(appointment.scheduledAt).month }}</span>
            </div>
            <div class="min-w-[160px] flex-1">
              <p class="text-[14px] font-semibold text-ink-900">{{ appointment.doctorName || 'Clinician' }}</p>
              <p class="mt-0.5 text-[12px] text-ink-500">{{ formatDateTime(appointment.scheduledAt, ui.locale) }}</p>
              <p v-if="appointment.reason" class="mt-1 text-[12px] text-ink-400">{{ appointment.reason }}</p>
            </div>
            <div class="flex shrink-0 items-center gap-2">
              <StatusBadge :status="appointment.status" />
              <button
                v-if="['REQUESTED', 'CONFIRMED'].includes(appointment.status)"
                class="rounded-lg border border-rose-200 px-3 py-1.5 text-[11px] font-semibold text-rose-600 transition-colors hover:bg-rose-50"
                @click="cancel(appointment)"
              >
                Cancel appointment
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
        <div class="dash-info mt-4">Requests stay pending until the clinician confirms them.</div>
      </div>
    </div>
  </div>
</template>
