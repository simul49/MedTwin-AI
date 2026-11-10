<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useUiStore } from '@/stores/ui';
import { connect } from '@/api/endpoints';
import { formatDateTime } from '@/composables/useAsync';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import type { Appointment } from '@/api/types';

const { t } = useI18n();
const ui = useUiStore();

const appointments = ref<Appointment[]>([]);
const loading = ref(true);
const busy = ref<string | null>(null);
const error = ref<string | null>(null);
const filter = ref('ALL');

const counts = computed(() => ({
  ALL: appointments.value.length,
  REQUESTED: appointments.value.filter((a) => a.status === 'REQUESTED').length,
  CONFIRMED: appointments.value.filter((a) => a.status === 'CONFIRMED').length,
  COMPLETED: appointments.value.filter((a) => a.status === 'COMPLETED').length,
}));

const visible = computed(() =>
  filter.value === 'ALL' ? appointments.value : appointments.value.filter((a) => a.status === filter.value),
);

async function load() {
  loading.value = true;
  error.value = null;
  try {
    appointments.value = (await connect.appointments()).results;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

async function setStatus(appointment: Appointment, status: string) {
  busy.value = appointment.id;
  try {
    await connect.updateAppointment(appointment.id, { status });
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    busy.value = null;
  }
}

onMounted(load);
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-2">Clinical schedule</p>
        <h1 class="text-[28px] font-bold leading-tight tracking-tight text-ink-900">{{ t('doctor.navAppointments') }}</h1>
        <p class="mt-2 text-[14px] text-ink-500">Review patient requests and manage consultation status.</p>
      </div>
      <span class="chip border border-ink-200 bg-white text-ink-600">{{ appointments.length }} appointments</span>
    </div>

    <p v-if="error" class="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-[13px] text-rose-700">{{ error }}</p>

    <div class="dash-card overflow-hidden">
      <div class="flex flex-wrap items-center justify-between gap-3 border-b border-ink-100 px-5 py-4">
        <div class="flex items-center gap-3">
          <span class="dash-icon-tile">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M7 2v3M17 2v3M3 8h18M4 5h16v16H4z" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <div>
            <p class="dash-section-title">Appointment requests</p>
            <p class="dash-section-sub mt-0.5">Only consented patients appear here</p>
          </div>
        </div>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="option in ['ALL', 'REQUESTED', 'CONFIRMED', 'COMPLETED']"
            :key="option"
            class="dash-tab text-[11px]"
            :class="filter === option ? 'dash-tab-active' : 'bg-surface-50'"
            @click="filter = option"
          >
            {{ option === 'ALL' ? 'All' : option.charAt(0) + option.slice(1).toLowerCase() }} ({{ counts[option as keyof typeof counts] }})
          </button>
        </div>
      </div>

      <div v-if="loading" class="h-40 animate-pulse bg-ink-100" />
      <div v-else-if="!visible.length" class="px-5 py-14 text-center">
        <p class="text-[14px] font-semibold text-ink-700">No appointments in this view</p>
        <p class="mt-1 text-[12px] text-ink-400">Switch the filter to see other requests.</p>
      </div>
      <div v-else class="dash-scroll overflow-x-auto">
        <table class="dash-table-compact w-full min-w-[700px] border-collapse">
          <thead>
            <tr>
              <th class="dash-th">Patient</th>
              <th class="dash-th">Date &amp; time</th>
              <th class="dash-th">Reason</th>
              <th class="dash-th">Status</th>
              <th class="dash-th">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="appointment in visible" :key="appointment.id" class="dash-row">
              <td class="dash-td">
                <div class="flex items-center gap-2.5">
                  <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-[10px] font-bold text-brand-700">
                    {{ (appointment.patientName || 'P').split(' ').map((p) => p[0]).slice(0, 2).join('') }}
                  </span>
                  <span class="font-semibold text-ink-900">{{ appointment.patientName }}</span>
                </div>
              </td>
              <td class="dash-td">{{ formatDateTime(appointment.scheduledAt, ui.locale) }}</td>
              <td class="dash-td max-w-[220px] truncate text-ink-500" :title="appointment.reason">{{ appointment.reason || '—' }}</td>
              <td class="dash-td"><StatusBadge :status="appointment.status" /></td>
              <td class="dash-td">
                <div class="flex flex-wrap gap-1.5">
                  <template v-if="appointment.status === 'REQUESTED'">
                    <button class="dash-btn px-3 py-1.5 text-[11px]" :disabled="busy === appointment.id" @click="setStatus(appointment, 'CONFIRMED')">Confirm</button>
                    <button class="btn-secondary px-3 py-1.5 text-[11px]" :disabled="busy === appointment.id" @click="setStatus(appointment, 'DECLINED')">Decline</button>
                  </template>
                  <button
                    v-else-if="appointment.status === 'CONFIRMED'"
                    class="btn-secondary px-3 py-1.5 text-[11px]"
                    :disabled="busy === appointment.id"
                    @click="setStatus(appointment, 'COMPLETED')"
                  >
                    Mark completed
                  </button>
                  <span v-else class="text-[11px] text-ink-400">No action needed</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="dash-info m-5">
        Appointment actions are recorded in the audit log. Only patients with active consent can be scheduled.
      </div>
    </div>
  </div>
</template>
