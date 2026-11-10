<script setup lang="ts">
import { computed, ref } from 'vue';
import { patient } from '@/api/endpoints';
import { useAsync, formatDate } from '@/composables/useAsync';

const { data: twin, loading, error, run } = useAsync(() => patient.digitalTwin());

const tabs = [
  { key: 'profile', label: 'Profile' },
  { key: 'history', label: 'Medical History' },
  { key: 'allergies', label: 'Allergies' },
  { key: 'medications', label: 'Medications' },
  { key: 'labs', label: 'Lab Results' },
  { key: 'notes', label: 'Doctor Notes' },
];
const active = ref('history');
const showAdd = ref(false);
const saving = ref(false);
const form = ref({ title: '', category: 'NOTE', summary: '' });

interface Row {
  name: string;
  start: string;
  end: string;
  dosage: string;
  notes: string;
}

const rows = computed<Row[]>(() => {
  const t = twin.value;
  if (!t) return [];
  switch (active.value) {
    case 'profile':
      return [
        { name: 'Date of birth', start: formatDate(t.profile?.dateOfBirth), end: '—', dosage: t.profile?.gender ?? '—', notes: t.profile?.bloodType || '—' },
        { name: 'Height / Weight', start: `${t.profile?.heightCm ?? '—'} cm`, end: `${t.profile?.weightKg ?? '—'} kg`, dosage: t.profile?.city || '—', notes: t.profile?.emergencyContact || '—' },
        { name: 'Summary', start: '—', end: '—', dosage: '—', notes: t.profile?.summary || '—' },
      ];
    case 'history':
      return t.records
        .filter((r) => ['CONDITION', 'FAMILY_HISTORY', 'PROCEDURE', 'NOTE'].includes(r.category))
        .map((r) => ({ name: r.title, start: formatDate(r.recordedAt), end: r.verificationStatus, dosage: r.category, notes: r.summary || '—' }));
    case 'allergies':
      return t.allergies.map((a) => ({ name: a.substance, start: formatDate(a.createdAt), end: a.status, dosage: a.severity, notes: a.reaction || '—' }));
    case 'medications':
      return t.medications.map((m) => ({ name: m.name, start: formatDate(m.startedAt), end: m.status === 'ACTIVE' ? 'Ongoing' : formatDate(m.endedAt), dosage: m.dose, notes: m.frequency || '—' }));
    case 'labs':
      return t.observations.map((o) => ({ name: o.label, start: formatDate(o.observedAt), end: o.flag, dosage: o.displayValue, notes: o.referenceRange || '—' }));
    case 'notes':
      return t.records
        .filter((r) => r.sourceType === 'CLINICIAN' || r.isAiGenerated)
        .map((r) => ({ name: r.title, start: formatDate(r.createdAt), end: r.verificationStatus, dosage: r.sourceType, notes: r.summary || '—' }));
    default:
      return [];
  }
});

async function addRecord() {
  if (!form.value.title.trim()) return;
  saving.value = true;
  try {
    await patient.createRecord({ ...form.value });
    form.value = { title: '', category: 'NOTE', summary: '' };
    showAdd.value = false;
    await run();
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-2">Health records</p>
        <h1 class="text-[28px] font-bold leading-tight tracking-tight text-ink-900">Your personal medical digital twin</h1>
        <p class="mt-2 text-[14px] text-ink-500">You own your health records. Review, add and verify every entry.</p>
      </div>
      <button class="dash-btn" @click="showAdd = true">＋ Add new record</button>
    </div>

    <!-- Tabs -->
    <div class="mb-4 flex flex-wrap gap-2 rounded-2xl border border-ink-200/70 bg-white p-2">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="dash-tab"
        :class="active === tab.key ? 'dash-tab-active' : ''"
        @click="active = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <p v-if="error" class="mb-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ error }}</p>

    <div class="dash-card overflow-hidden">
      <div class="flex items-center justify-between border-b border-ink-100 px-5 py-4">
        <div class="flex items-center gap-3">
          <span class="dash-icon-tile">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M7 3h10v18l-5-3-5 3z" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <div>
            <p class="dash-section-title">{{ tabs.find((x) => x.key === active)?.label }}</p>
            <p class="dash-section-sub mt-0.5">Source-linked and reviewable</p>
          </div>
        </div>
        <span class="chip bg-surface-100 text-ink-600">{{ rows.length }} entries</span>
      </div>

      <div v-if="loading && !twin" class="h-48 animate-pulse bg-ink-100" />
      <div v-else class="overflow-x-auto">
        <table class="w-full min-w-[720px] table-fixed border-collapse">
          <thead class="bg-surface-50">
            <tr>
              <th class="dash-th w-[22%] min-w-[180px]">Name</th>
              <th class="dash-th w-[14%]">Date</th>
              <th class="dash-th w-[15%]">Status</th>
              <th class="dash-th w-[17%]">Value / Dosage</th>
              <th class="dash-th w-[32%]">Notes</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in rows" :key="`${row.name}-${index}`" class="dash-row">
              <td class="dash-td font-medium text-ink-800">{{ row.name }}</td>
              <td class="dash-td">{{ row.start }}</td>
              <td class="dash-td">{{ row.end }}</td>
              <td class="dash-td">{{ row.dosage }}</td>
              <td class="dash-td max-w-[420px] truncate text-ink-500" :title="row.notes">{{ row.notes }}</td>
            </tr>
            <tr v-if="!rows.length">
              <td colspan="5" class="dash-td py-8 text-center text-ink-400">No entries in this section yet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <p class="mt-3 text-[11px] text-ink-400">
      Every item keeps its source. AI-generated drafts are labelled and require clinician verification.
    </p>

    <!-- Add record modal -->
    <div v-if="showAdd" class="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/40 p-4" @click.self="showAdd = false">
      <div class="w-full max-w-md rounded-2xl border border-ink-200 bg-white p-6 shadow-lift">
        <h2 class="text-lg font-bold text-ink-900">Add a record</h2>
        <p class="mt-1 text-[12px] text-ink-500">The entry is attributed to you and can be edited later.</p>
        <form class="mt-5 space-y-3" @submit.prevent="addRecord">
          <div>
            <label class="label" for="r-title">Title</label>
            <input id="r-title" v-model="form.title" class="input" required placeholder="e.g. Annual check-up" />
          </div>
          <div>
            <label class="label" for="r-category">Category</label>
            <select id="r-category" v-model="form.category" class="input">
              <option value="NOTE">Note</option>
              <option value="CONDITION">Condition</option>
              <option value="LAB">Lab result</option>
              <option value="MEDICATION">Medication</option>
              <option value="VITAL">Vital measurement</option>
            </select>
          </div>
          <div>
            <label class="label" for="r-summary">Notes</label>
            <textarea id="r-summary" v-model="form.summary" class="input min-h-20" />
          </div>
          <div class="flex justify-end gap-2 pt-2">
            <button type="button" class="btn-secondary text-xs" @click="showAdd = false">Cancel</button>
            <button type="submit" class="dash-btn" :disabled="saving">Save record</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
