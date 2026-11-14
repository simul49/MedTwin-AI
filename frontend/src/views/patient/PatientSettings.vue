<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';
import { auth as authApi, patient } from '@/api/endpoints';
import { SUPPORTED_LOCALES, type LocaleCode } from '@/i18n';

const { t } = useI18n();
const auth = useAuthStore();
const ui = useUiStore();

const profile = ref({
  name: auth.user?.name ?? '',
  phone: auth.user?.phone ?? '',
  dateOfBirth: auth.user?.patientProfile?.dateOfBirth ?? '',
  gender: auth.user?.patientProfile?.gender ?? 'UNDISCLOSED',
  city: auth.user?.patientProfile?.city ?? '',
  emergencyContact: auth.user?.patientProfile?.emergencyContact ?? '',
  summary: auth.user?.patientProfile?.summary ?? '',
});

const passwords = ref({ current: '', next: '' });
const showPasswords = ref({ current: false, next: false });
const message = ref<string | null>(null);
const error = ref<string | null>(null);
const savingProfile = ref(false);
const exporting = ref(false);

const initials = computed(() =>
  (auth.user?.name ?? '')
    .split(' ')
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase(),
);

const passwordValid = computed(() => passwords.value.current.length > 0 && passwords.value.next.length >= 8);

watch(
  () => auth.user,
  (user) => {
    if (!user) return;
    profile.value.name = user.name;
    profile.value.phone = user.phone ?? '';
  },
);

function notify(text: string) {
  message.value = text;
  window.setTimeout(() => (message.value = null), 3500);
}

async function saveProfile() {
  error.value = null;
  savingProfile.value = true;
  try {
    await auth.updateProfile({
      name: profile.value.name,
      phone: profile.value.phone,
      patientProfile: {
        dateOfBirth: profile.value.dateOfBirth || null,
        gender: profile.value.gender,
        city: profile.value.city,
        emergencyContact: profile.value.emergencyContact,
        summary: profile.value.summary,
      },
    });
    notify('Profile saved successfully.');
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    savingProfile.value = false;
  }
}

async function changePassword() {
  error.value = null;
  try {
    await authApi.changePassword(passwords.value.current, passwords.value.next);
    passwords.value = { current: '', next: '' };
    notify('Password updated.');
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
}

async function exportData() {
  exporting.value = true;
  try {
    const data = await patient.exportData();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `medtwin-export-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    URL.revokeObjectURL(url);
    notify('Export downloaded — a JSON copy of your health data.');
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    exporting.value = false;
  }
}

async function deleteData() {
  if (!window.confirm(t('patient.deleteConfirm'))) return;
  await patient.deleteData();
  ui.notify(t('patient.dangerZone'), 'info');
}

function pickLocale(code: LocaleCode) {
  ui.setLocale(code);
}
</script>

<template>
  <div>
    <div class="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-1.5">Account &amp; preferences</p>
        <h1 class="text-[26px] font-bold leading-tight tracking-tight text-ink-900">{{ t('patient.settingsTitle') }}</h1>
        <p class="mt-1 text-[13px] text-ink-500">Manage your profile, language, security and personal data.</p>
      </div>
      <div class="flex items-center gap-2 text-[11px] font-semibold">
        <span class="chip bg-surface-100 text-ink-600">
          <svg class="mr-1 inline-block h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M4 6h16v12H4zM4 7l8 6 8-6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          {{ auth.user?.email }}
        </span>
        <span class="chip bg-brand-50 text-brand-700">{{ auth.user?.role?.toLowerCase() ?? 'patient' }}</span>
      </div>
    </div>

    <div v-if="message" class="mb-4 flex items-center gap-2 rounded-xl border border-brand-200 bg-brand-50 px-4 py-3 text-[13px] font-medium text-brand-800">
      <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      {{ message }}
    </div>
    <p v-if="error" class="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-[13px] text-rose-700">{{ error }}</p>

    <div class="grid items-start gap-5 lg:grid-cols-2">
      <!-- Profile -->
      <div class="dash-card overflow-hidden">
        <div class="flex items-start gap-3 border-b border-ink-100 px-5 py-4">
          <span class="dash-icon-tile">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M12 3a4 4 0 110 8 4 4 0 010-8zM4 21a8 8 0 0116 0" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <div>
            <p class="dash-section-title">{{ t('patient.profile') }}</p>
            <p class="dash-section-sub mt-0.5">Personal details used in your Digital Twin</p>
          </div>
        </div>

        <form class="space-y-4 p-5" @submit.prevent="saveProfile">
          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="label" for="s-name">Full name</label>
              <input id="s-name" v-model="profile.name" class="input" />
            </div>
            <div>
              <label class="label" for="s-phone">Phone</label>
              <input id="s-phone" v-model="profile.phone" class="input" placeholder="Optional" />
            </div>
            <div>
              <label class="label" for="s-dob">Date of birth</label>
              <input id="s-dob" v-model="profile.dateOfBirth" class="input" type="date" />
            </div>
            <div>
              <label class="label" for="s-gender">Gender</label>
              <select id="s-gender" v-model="profile.gender" class="input">
                <option value="UNDISCLOSED">{{ t('auth.genderUndisclosed') }}</option>
                <option value="FEMALE">{{ t('auth.genderFemale') }}</option>
                <option value="MALE">{{ t('auth.genderMale') }}</option>
              </select>
            </div>
            <div>
              <label class="label" for="s-city">City</label>
              <input id="s-city" v-model="profile.city" class="input" />
            </div>
            <div>
              <label class="label" for="s-emergency">Emergency contact</label>
              <input id="s-emergency" v-model="profile.emergencyContact" class="input" />
            </div>
          </div>
          <div>
            <label class="label" for="s-summary">About my health</label>
            <textarea id="s-summary" v-model="profile.summary" class="input min-h-20" />
          </div>
          <div class="flex justify-end border-t border-ink-100 pt-4">
            <button class="dash-btn" type="submit" :disabled="savingProfile">
              {{ savingProfile ? 'Saving…' : 'Save profile' }}
            </button>
          </div>
        </form>
      </div>

      <!-- Preferences -->
      <div class="space-y-5">
        <div class="dash-card dash-card-pad">
          <div class="flex items-start gap-3">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a15 15 0 010 18M12 3a15 15 0 000 18" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">{{ t('patient.language') }}</p>
              <p class="dash-section-sub mt-0.5">Language used across the app</p>
            </div>
          </div>
          <div class="mt-4 inline-flex gap-1 rounded-xl border border-ink-200 bg-surface-50 p-1">
            <button
              v-for="option in SUPPORTED_LOCALES"
              :key="option.code"
              class="rounded-lg px-4 py-2 text-[12px] font-semibold transition-all"
              :class="ui.locale === option.code ? 'bg-white text-brand-700 shadow-sm ring-1 ring-brand-200' : 'text-ink-500 hover:text-ink-800'"
              @click="pickLocale(option.code)"
            >
              {{ option.label }}
            </button>
          </div>
        </div>

        <div class="dash-card dash-card-pad">
          <div class="flex items-start gap-3">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 018 0v3" stroke-linecap="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">{{ t('auth.password') }}</p>
              <p class="dash-section-sub mt-0.5">Update your sign-in credentials</p>
            </div>
          </div>
          <form class="mt-4 space-y-4" @submit.prevent="changePassword">
            <div class="grid gap-4 sm:grid-cols-2">
              <div>
                <label class="label" for="s-current">Current password</label>
                <div class="relative">
                  <input
                    id="s-current"
                    v-model="passwords.current"
                    class="input pr-10"
                    :type="showPasswords.current ? 'text' : 'password'"
                    autocomplete="current-password"
                  />
                  <button
                    type="button"
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-ink-400 transition-colors hover:text-ink-700"
                    :aria-label="showPasswords.current ? 'Hide password' : 'Show password'"
                    @click="showPasswords.current = !showPasswords.current"
                  >
                    <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                      <template v-if="showPasswords.current">
                        <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6z" />
                        <circle cx="12" cy="12" r="2.5" />
                        <path d="M4 20 20 4" />
                      </template>
                      <template v-else>
                        <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6z" />
                        <circle cx="12" cy="12" r="2.5" />
                      </template>
                    </svg>
                  </button>
                </div>
              </div>
              <div>
                <label class="label" for="s-next">New password</label>
                <div class="relative">
                  <input
                    id="s-next"
                    v-model="passwords.next"
                    class="input pr-10"
                    :type="showPasswords.next ? 'text' : 'password'"
                    autocomplete="new-password"
                  />
                  <button
                    type="button"
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-ink-400 transition-colors hover:text-ink-700"
                    :aria-label="showPasswords.next ? 'Hide password' : 'Show password'"
                    @click="showPasswords.next = !showPasswords.next"
                  >
                    <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                      <template v-if="showPasswords.next">
                        <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6z" />
                        <circle cx="12" cy="12" r="2.5" />
                        <path d="M4 20 20 4" />
                      </template>
                      <template v-else>
                        <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6z" />
                        <circle cx="12" cy="12" r="2.5" />
                      </template>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            <p class="text-[11px]" :class="passwords.next && passwords.next.length < 8 ? 'font-semibold text-amber-600' : 'text-ink-400'">
              {{ t('auth.passwordHint') }}
            </p>
            <div class="flex justify-end border-t border-ink-100 pt-4">
              <button class="dash-btn" type="submit" :disabled="!passwordValid">Update password</button>
            </div>
          </form>
        </div>

        <div class="dash-card overflow-hidden border-rose-200">
          <div class="flex items-start gap-3 border-b border-rose-100 bg-rose-50/60 px-4 py-3.5">
            <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-rose-100 text-rose-600">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">{{ t('patient.dangerZone') }}</p>
              <p class="dash-section-sub mt-0.5">Download or remove your health data</p>
            </div>
          </div>
          <div class="divide-y divide-ink-100">
            <div class="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
              <div class="min-w-0">
                <p class="text-[13px] font-semibold text-ink-800">{{ t('patient.exportData') }}</p>
                <p class="mt-0.5 text-[11.5px] text-ink-400">A machine-readable JSON copy of everything stored about you.</p>
              </div>
              <button class="btn-secondary shrink-0 px-3 py-1.5 text-xs" :disabled="exporting" @click="exportData">
                <svg class="mr-1 inline-block h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                {{ exporting ? 'Preparing…' : 'Download' }}
              </button>
            </div>
            <div class="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
              <div class="min-w-0">
                <p class="text-[13px] font-semibold text-ink-800">{{ t('patient.deleteData') }}</p>
                <p class="mt-0.5 text-[11.5px] text-ink-400">Permanently removes your health records. This cannot be undone.</p>
              </div>
              <button class="btn-danger shrink-0 px-3 py-1.5 text-xs" @click="deleteData">Delete</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
