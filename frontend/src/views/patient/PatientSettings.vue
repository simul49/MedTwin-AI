<script setup lang="ts">
import { ref, watch } from 'vue';
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
const message = ref<string | null>(null);
const error = ref<string | null>(null);
const savingProfile = ref(false);

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
  const data = await patient.exportData();
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'medtwin-export.json';
  link.click();
  URL.revokeObjectURL(url);
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
    <div class="mb-6">
      <p class="dash-kicker mb-2">Account &amp; preferences</p>
      <h1 class="text-[28px] font-bold leading-tight tracking-tight text-ink-900">{{ t('patient.settingsTitle') }}</h1>
      <p class="mt-2 text-[14px] text-ink-500">Manage your profile, language, security and personal data.</p>
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
                <input id="s-current" v-model="passwords.current" class="input" type="password" autocomplete="current-password" />
              </div>
              <div>
                <label class="label" for="s-next">New password</label>
                <input id="s-next" v-model="passwords.next" class="input" type="password" autocomplete="new-password" />
              </div>
            </div>
            <p class="text-[11px] text-ink-400">{{ t('auth.passwordHint') }}</p>
            <div class="flex justify-end border-t border-ink-100 pt-4">
              <button class="dash-btn" type="submit">Update password</button>
            </div>
          </form>
        </div>

        <div class="dash-card dash-card-pad">
          <div class="flex items-start gap-3">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6z" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">{{ t('patient.dangerZone') }}</p>
              <p class="dash-section-sub mt-0.5">Download or remove your health data</p>
            </div>
          </div>
          <div class="mt-4 flex flex-wrap gap-2">
            <button class="btn-secondary text-xs" @click="exportData">{{ t('patient.exportData') }}</button>
            <button class="btn-danger text-xs" @click="deleteData">{{ t('patient.deleteData') }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
