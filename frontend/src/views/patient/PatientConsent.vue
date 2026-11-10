<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { consent as consentApi, auth as authApi } from '@/api/endpoints';
import { formatDate } from '@/composables/useAsync';
import type { ConsentGrant } from '@/api/types';

const { t } = useI18n();

const grants = ref<ConsentGrant[]>([]);
const scopeOptions = ref<string[]>([]);
const doctors = ref<{ id: string; name: string; specialization: string }[]>([]);
const form = ref({ doctorId: '', scope: ['profile', 'conditions'], purpose: '', durationDays: 90 });
const saving = ref(false);
const error = ref<string | null>(null);
const showGrant = ref(false);

const pending = computed(() => grants.value.filter((g) => g.status === 'PENDING'));
const others = computed(() => grants.value.filter((g) => g.status !== 'PENDING'));

async function load() {
  error.value = null;
  try {
    const result = await consentApi.list();
    grants.value = result.results;
    scopeOptions.value = result.scopeOptions;
    doctors.value = (await authApi.doctors()).results;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
}

async function grant() {
  if (!form.value.doctorId) return;
  saving.value = true;
  try {
    await consentApi.grant({ ...form.value });
    form.value = { doctorId: '', scope: ['profile', 'conditions'], purpose: '', durationDays: 90 };
    showGrant.value = false;
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    saving.value = false;
  }
}

async function decide(item: ConsentGrant, decision: 'GRANT' | 'REJECT') {
  await consentApi.decide(item.id, decision);
  await load();
}

async function revoke(item: ConsentGrant) {
  if (!window.confirm(t('patient.revokeConfirm'))) return;
  await consentApi.revoke(item.id);
  await load();
}

onMounted(load);
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-2">Privacy &amp; access</p>
        <h1 class="text-[28px] font-bold leading-tight tracking-tight text-ink-900">Consent Management</h1>
        <p class="mt-2 text-[14px] text-ink-500">You control who can see your Digital Twin — and can revoke access at any time.</p>
      </div>
      <div class="flex gap-2">
        <button class="btn-secondary text-xs" @click="load()">↻ Refresh</button>
        <button class="dash-btn" @click="showGrant = true">＋ Grant new access</button>
      </div>
    </div>

    <p v-if="error" class="mb-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ error }}</p>

    <!-- Pending requests -->
    <div v-if="pending.length" class="dash-card dash-card-pad mb-4">
      <p class="text-sm font-bold text-ink-800">Pending requests</p>
      <div class="mt-3 space-y-2">
        <div v-for="item in pending" :key="item.id" class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
          <div>
            <p class="text-[13px] font-semibold text-ink-800">{{ item.doctor?.name }}</p>
            <p class="text-[11px] text-ink-500">{{ item.purpose || 'Access request' }} · {{ item.scope.join(', ') }}</p>
          </div>
          <div class="flex gap-2">
            <button class="dash-btn px-3 py-1.5 text-xs" @click="decide(item, 'GRANT')">Approve</button>
            <button class="btn-secondary px-3 py-1.5 text-xs" @click="decide(item, 'REJECT')">Decline</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Access table -->
    <div class="dash-card overflow-hidden">
      <div class="flex items-start gap-3 border-b border-ink-100 px-5 py-4">
        <span class="dash-icon-tile">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
            <path d="M12 2l7 4v6c0 5-3 8-7 10-4-2-7-5-7-10V6z" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </span>
        <div>
          <p class="dash-section-title">Access Scope</p>
          <p class="dash-section-sub mt-0.5">Clinicians with current or past access</p>
        </div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full min-w-[640px] border-collapse">
          <thead class="bg-surface-50">
            <tr>
              <th class="dash-th">Doctor</th>
              <th class="dash-th">Access scope</th>
              <th class="dash-th">Status</th>
              <th class="dash-th">Updated</th>
              <th class="dash-th">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in others" :key="item.id" class="dash-row">
              <td class="dash-td">
                <div class="flex items-center gap-2.5">
                  <span
                    class="flex h-8 w-8 items-center justify-center rounded-full text-[10px] font-bold text-white"
                    :style="{ backgroundColor: item.doctor?.avatarColor ?? '#0e9180' }"
                  >
                    {{ item.doctor?.initials ?? 'DR' }}
                  </span>
                  <div>
                    <p class="font-semibold text-ink-800">{{ item.doctor?.name ?? 'Clinician' }}</p>
                    <p class="text-[11px] text-ink-400">{{ item.doctor?.specialization }}</p>
                  </div>
                </div>
              </td>
              <td class="dash-td text-ink-500">{{ item.scope.join(', ') }}</td>
              <td class="dash-td">
                <span class="chip" :class="item.status === 'ACTIVE' ? 'bg-brand-50 text-brand-700' : 'bg-rose-50 text-rose-600'">
                  {{ item.status === 'ACTIVE' ? 'Active' : item.status === 'REVOKED' ? 'Revoked' : item.status }}
                </span>
              </td>
              <td class="dash-td">{{ formatDate(item.grantedAt ?? item.createdAt) }}</td>
              <td class="dash-td">
                <button v-if="item.status === 'ACTIVE'" class="text-[12px] font-semibold text-rose-600 hover:underline" @click="revoke(item)">
                  Revoke access
                </button>
                <span v-else class="text-[11px] text-ink-400">—</span>
              </td>
            </tr>
            <tr v-if="!others.length">
              <td colspan="5" class="dash-td py-8 text-center text-ink-400">No access grants yet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="dash-info mt-4">
      Only scoped records are visible to a clinician, and only while consent is active. Every grant and revocation is written to the audit log.
    </div>

    <!-- Grant modal -->
    <div v-if="showGrant" class="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/40 p-4" @click.self="showGrant = false">
      <div class="w-full max-w-md rounded-2xl border border-ink-200 bg-white p-6 shadow-lift">
        <div class="flex items-start justify-between">
          <div>
            <h2 class="text-lg font-bold text-ink-900">Grant Doctor Access</h2>
            <p class="mt-1 text-[12px] text-ink-500">You control access to your digital twin; you can revoke at any time.</p>
          </div>
          <button class="text-ink-400 hover:text-ink-800" aria-label="Close" @click="showGrant = false">✕</button>
        </div>

        <form class="mt-5 space-y-4" @submit.prevent="grant">
          <div>
            <label class="label" for="g-doctor">Doctor identifier</label>
            <select id="g-doctor" v-model="form.doctorId" class="input" required>
              <option value="">Select a clinician</option>
              <option v-for="doctor in doctors" :key="doctor.id" :value="doctor.id">
                {{ doctor.name }} — {{ doctor.specialization }}
              </option>
            </select>
          </div>

          <div>
            <span class="label">Access scope</span>
            <div class="grid grid-cols-2 gap-2">
              <label v-for="option in scopeOptions" :key="option" class="flex items-center gap-2 text-[12px] capitalize text-ink-700">
                <input v-model="form.scope" type="checkbox" :value="option" class="h-4 w-4 accent-brand-600" />
                {{ option.replaceAll('_', ' ') }}
              </label>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="label" for="g-duration">Duration (days)</label>
              <input id="g-duration" v-model.number="form.durationDays" class="input" type="number" min="1" max="365" />
            </div>
            <div>
              <label class="label" for="g-purpose">Purpose</label>
              <input id="g-purpose" v-model="form.purpose" class="input" placeholder="Optional" />
            </div>
          </div>

          <div class="flex justify-end gap-2 pt-1">
            <button type="button" class="btn-secondary text-xs" @click="showGrant = false">Cancel</button>
            <button type="submit" class="dash-btn" :disabled="saving">Grant access</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
