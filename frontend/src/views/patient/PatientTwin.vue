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
const addError = ref<string | null>(null);
const form = ref<Record<string, string>>({});

interface Row {
  name: string;
  start: string;
  end: string;
  dosage: string;
  notes: string;
}

interface FieldDef {
  key: string;
  label: string;
  type: 'text' | 'textarea' | 'date' | 'select';
  required?: boolean;
  placeholder?: string;
  options?: { value: string; label: string }[];
}

const FIELD_DEFS: Record<string, FieldDef[]> = {
  history: [
    { key: 'title', label: 'Title', type: 'text', required: true, placeholder: 'e.g. Annual check-up' },
    {
      key: 'category', label: 'Category', type: 'select',
      options: [
        { value: 'NOTE', label: 'Note' },
        { value: 'CONDITION', label: 'Condition' },
        { value: 'FAMILY_HISTORY', label: 'Family history' },
        { value: 'PROCEDURE', label: 'Procedure' },
      ],
    },
    { key: 'summary', label: 'Notes', type: 'textarea' },
  ],
  allergies: [
    { key: 'substance', label: 'Substance', type: 'text', required: true, placeholder: 'e.g. Penicillin' },
    {
      key: 'severity', label: 'Severity', type: 'select',
      options: [
        { value: 'MILD', label: 'Mild' },
        { value: 'MODERATE', label: 'Moderate' },
        { value: 'SEVERE', label: 'Severe' },
        { value: 'UNKNOWN', label: 'Unknown' },
      ],
    },
    { key: 'reaction', label: 'Reaction', type: 'text', placeholder: 'e.g. Rash, swelling' },
    {
      key: 'status', label: 'Status', type: 'select',
      options: [
        { value: 'ACTIVE', label: 'Active' },
        { value: 'RESOLVED', label: 'Resolved' },
        { value: 'UNKNOWN', label: 'Unknown' },
      ],
    },
  ],
  medications: [
    { key: 'name', label: 'Medication', type: 'text', required: true, placeholder: 'e.g. Metformin' },
    { key: 'dose', label: 'Dose', type: 'text', placeholder: 'e.g. 500 mg' },
    { key: 'frequency', label: 'Frequency', type: 'text', placeholder: 'e.g. Twice daily' },
    { key: 'route', label: 'Route', type: 'text', placeholder: 'e.g. Oral' },
    {
      key: 'status', label: 'Status', type: 'select',
      options: [
        { value: 'ACTIVE', label: 'Active' },
        { value: 'STOPPED', label: 'Stopped' },
        { value: 'UNKNOWN', label: 'Unknown' },
      ],
    },
    { key: 'startedAt', label: 'Started on', type: 'date' },
  ],
  labs: [
    { key: 'label', label: 'Test name', type: 'text', required: true, placeholder: 'e.g. HbA1c' },
    { key: 'value', label: 'Value', type: 'text', required: true, placeholder: 'e.g. 6.2' },
    { key: 'unit', label: 'Unit', type: 'text', placeholder: 'e.g. %' },
    { key: 'referenceRange', label: 'Reference range', type: 'text', placeholder: 'e.g. 4.0 – 5.6' },
    {
      key: 'flag', label: 'Flag', type: 'select',
      options: [
        { value: 'NORMAL', label: 'Normal' },
        { value: 'LOW', label: 'Low' },
        { value: 'HIGH', label: 'High' },
        { value: 'CRITICAL', label: 'Critical' },
        { value: 'UNKNOWN', label: 'Unknown' },
      ],
    },
    { key: 'observedAt', label: 'Date', type: 'date' },
  ],
  notes: [
    { key: 'title', label: 'Title', type: 'text', required: true, placeholder: 'e.g. Question for my doctor' },
    { key: 'summary', label: 'Notes', type: 'textarea' },
  ],
};

const modalTitle = computed(() => {
  switch (active.value) {
    case 'history': return 'Add a medical history entry';
    case 'allergies': return 'Add an allergy';
    case 'medications': return 'Add a medication';
    case 'labs': return 'Add a lab result';
    case 'notes': return 'Add a note';
    default: return 'Add a record';
  }
});

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
        .filter((r) => r.sourceType === 'CLINICIAN' || r.isAiGenerated || r.category === 'NOTE')
        .map((r) => ({ name: r.title, start: formatDate(r.createdAt), end: r.verificationStatus, dosage: r.sourceType, notes: r.summary || '—' }));
    default:
      return [];
  }
});

function openAdd() {
  form.value = {};
  addError.value = null;
  showAdd.value = true;
}

async function addEntry() {
  const payload: Record<string, unknown> = { ...form.value };
  saving.value = true;
  addError.value = null;
  try {
    switch (active.value) {
      case 'history':
      case 'notes':
        await patient.createRecord({ ...payload, category: payload.category || 'NOTE' });
        break;
      case 'allergies':
        await patient.createAllergy(payload);
        break;
      case 'medications':
        await patient.createMedication(payload);
        break;
      case 'labs':
        await patient.createObservation(payload);
        break;
    }
    form.value = {};
    showAdd.value = false;
    await run();
  } catch (exc) {
    addError.value = exc instanceof Error ? exc.message : 'Could not save the entry.';
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
      <button v-if="active !== 'profile'" class="dash-btn" @click="openAdd">＋ Add new {{ active === 'allergies' ? 'allergy' : active === 'medications' ? 'medication' : active === 'labs' ? 'lab result' : 'record' }}</button>
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

    <!-- Add entry modal (form adapts to the active tab) -->
    <div v-if="showAdd" class="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/40 p-4" @click.self="showAdd = false">
      <div class="w-full max-w-md rounded-2xl border border-ink-200 bg-white p-6 shadow-lift">
        <h2 class="text-lg font-bold text-ink-900">{{ modalTitle }}</h2>
        <p class="mt-1 text-[12px] text-ink-500">The entry is attributed to you and can be edited later.</p>
        <form class="mt-5 space-y-3" @submit.prevent="addEntry">
          <div v-for="field in FIELD_DEFS[active] ?? FIELD_DEFS.history" :key="field.key">
            <label class="label" :for="`f-${field.key}`">{{ field.label }}</label>
            <select
              v-if="field.type === 'select'"
              :id="`f-${field.key}`"
              v-model="form[field.key]"
              class="input"
            >
              <option v-for="opt in field.options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
            <textarea
              v-else-if="field.type === 'textarea'"
              :id="`f-${field.key}`"
              v-model="form[field.key]"
              class="input min-h-20"
            />
            <input
              v-else
              :id="`f-${field.key}`"
              v-model="form[field.key]"
              class="input"
              :type="field.type"
              :required="field.required"
              :placeholder="field.placeholder"
            />
          </div>
          <p v-if="addError" class="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">{{ addError }}</p>
          <div class="flex justify-end gap-2 pt-2">
            <button type="button" class="btn-secondary text-xs" @click="showAdd = false">Cancel</button>
            <button type="submit" class="dash-btn" :disabled="saving">Save entry</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
