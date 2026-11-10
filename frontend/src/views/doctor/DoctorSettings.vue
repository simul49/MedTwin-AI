<script setup lang="ts">
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import StatusBadge from '@/components/ui/StatusBadge.vue';

const { t } = useI18n();
const auth = useAuthStore();

const profile = ref({
  name: auth.user?.name ?? '',
  phone: auth.user?.phone ?? '',
  specialization: auth.user?.doctorProfile?.specialization ?? '',
  licenseNumber: auth.user?.doctorProfile?.licenseNumber ?? '',
  hospital: auth.user?.doctorProfile?.hospital ?? '',
  department: auth.user?.doctorProfile?.department ?? '',
  bio: auth.user?.doctorProfile?.bio ?? '',
});

const message = ref<string | null>(null);
const error = ref<string | null>(null);
const saving = ref(false);

const verification = computed(() => auth.user?.doctorProfile?.verificationStatus ?? 'PENDING');

async function save() {
  error.value = null;
  saving.value = true;
  try {
    await auth.updateProfile({
      name: profile.value.name,
      phone: profile.value.phone,
      doctorProfile: {
        specialization: profile.value.specialization,
        licenseNumber: profile.value.licenseNumber,
        hospital: profile.value.hospital,
        department: profile.value.department,
        bio: profile.value.bio,
      },
    });
    message.value = 'Professional profile saved successfully.';
    window.setTimeout(() => (message.value = null), 3500);
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-2">Clinician account</p>
        <h1 class="text-[28px] font-bold leading-tight tracking-tight text-ink-900">{{ t('doctor.navSettings') }}</h1>
        <p class="mt-2 text-[14px] text-ink-500">Keep your professional details and credentials up to date.</p>
      </div>
      <div class="flex items-center gap-2 rounded-xl border border-ink-200 bg-white px-3.5 py-2.5">
        <span class="dash-label">Verification</span>
        <StatusBadge :status="verification" />
      </div>
    </div>

    <div v-if="message" class="mb-4 flex items-center gap-2 rounded-xl border border-brand-200 bg-brand-50 px-4 py-3 text-[13px] font-medium text-brand-800">
      <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      {{ message }}
    </div>
    <p v-if="error" class="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-[13px] text-rose-700">{{ error }}</p>

    <div class="grid items-start gap-5 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,0.8fr)]">
      <div class="dash-card overflow-hidden">
        <div class="flex items-start gap-3 border-b border-ink-100 px-5 py-4">
          <span class="dash-icon-tile">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M12 3a4 4 0 110 8 4 4 0 010-8zM4 21a8 8 0 0116 0" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <div>
            <p class="dash-section-title">{{ t('doctor.profile') }}</p>
            <p class="dash-section-sub mt-0.5">Shown to patients when you are granted access</p>
          </div>
        </div>

        <form class="space-y-4 p-5" @submit.prevent="save">
          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="label" for="d-name">Full name</label>
              <input id="d-name" v-model="profile.name" class="input" />
            </div>
            <div>
              <label class="label" for="d-phone">Phone</label>
              <input id="d-phone" v-model="profile.phone" class="input" placeholder="Optional" />
            </div>
            <div>
              <label class="label" for="d-spec">{{ t('auth.specialization') }}</label>
              <input id="d-spec" v-model="profile.specialization" class="input" />
            </div>
            <div>
              <label class="label" for="d-license">{{ t('auth.licenseNumber') }}</label>
              <input id="d-license" v-model="profile.licenseNumber" class="input" />
            </div>
            <div>
              <label class="label" for="d-hospital">{{ t('auth.hospital') }}</label>
              <input id="d-hospital" v-model="profile.hospital" class="input" />
            </div>
            <div>
              <label class="label" for="d-dept">{{ t('auth.department') }}</label>
              <input id="d-dept" v-model="profile.department" class="input" />
            </div>
          </div>
          <div>
            <label class="label" for="d-bio">Professional summary</label>
            <textarea id="d-bio" v-model="profile.bio" class="input min-h-24" />
          </div>
          <div class="flex justify-end border-t border-ink-100 pt-4">
            <button class="dash-btn" type="submit" :disabled="saving">{{ saving ? 'Saving…' : 'Save profile' }}</button>
          </div>
        </form>
      </div>

      <div class="space-y-5">
        <div class="dash-card dash-card-pad">
          <div class="flex items-start gap-3">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M12 2l7 4v6c0 5-3 8-7 10-4-2-7-5-7-10V6z" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">Account status</p>
              <p class="dash-section-sub mt-0.5">Your clinician identity</p>
            </div>
          </div>
          <dl class="mt-4 space-y-3 text-[12px]">
            <div class="flex items-center justify-between border-b border-ink-100 pb-2.5">
              <dt class="text-ink-500">Role</dt>
              <dd class="font-semibold text-ink-800">{{ auth.user?.role }}</dd>
            </div>
            <div class="flex items-center justify-between border-b border-ink-100 pb-2.5">
              <dt class="text-ink-500">Email</dt>
              <dd class="font-semibold text-ink-800">{{ auth.user?.email }}</dd>
            </div>
            <div class="flex items-center justify-between">
              <dt class="text-ink-500">Verification</dt>
              <dd><StatusBadge :status="verification" /></dd>
            </div>
          </dl>
        </div>

        <div class="dash-info">
          Patient records are visible only while consent is active. All access is written to the audit log.
        </div>
      </div>
    </div>
  </div>
</template>
