<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import { ApiError } from '@/api/client';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const initialRole = (): 'PATIENT' | 'DOCTOR' | 'ADMIN' => {
  if (route.query.portal === 'admin' || route.query.role === 'ADMIN') return 'ADMIN';
  return route.query.portal === 'doctor' || route.query.role === 'DOCTOR' ? 'DOCTOR' : 'PATIENT';
};
const role = ref<'PATIENT' | 'DOCTOR' | 'ADMIN'>(initialRole());
const form = ref({
  name: '',
  email: '',
  password: '',
  phone: '',
  specialization: '',
  licenseNumber: '',
  hospital: '',
  department: '',
  dateOfBirth: '',
  gender: 'UNDISCLOSED',
  setupCode: '',
});
const acknowledge = ref(false);
const error = ref<string | null>(null);
const fieldErrors = ref<Record<string, string>>({});

const passwordValid = computed(() => /^(?=.*[A-Za-z])(?=.*\d).{8,}$/.test(form.value.password));

async function submit() {
  error.value = null;
  fieldErrors.value = {};
  try {
    await auth.register({
      name: form.value.name,
      email: form.value.email,
      password: form.value.password,
      role: role.value,
      phone: form.value.phone,
      specialization: form.value.specialization,
      licenseNumber: form.value.licenseNumber,
      hospital: form.value.hospital,
      department: form.value.department,
      dateOfBirth: form.value.dateOfBirth || undefined,
      gender: form.value.gender,
      setupCode: form.value.setupCode,
      acknowledge: acknowledge.value,
    });
    router.push(auth.homePath);
  } catch (err) {
    if (err instanceof ApiError && err.body && typeof err.body === 'object' && 'fields' in err.body) {
      fieldErrors.value = (err.body as { fields: Record<string, string> }).fields;
      error.value = String((err.body as { error?: string }).error ?? t('common.error'));
    } else {
      error.value = err instanceof Error ? err.message : t('common.error');
    }
  }
}
</script>

<template>
  <div class="container-page py-14">
    <div class="mx-auto w-full max-w-2xl">
      <h1 class="section-title">{{ t('auth.registerTitle') }}</h1>
      <p class="muted mt-1">{{ t('auth.registerSubtitle') }}</p>

      <form class="card card-pad mt-6 space-y-5" @submit.prevent="submit">
        <div>
          <span class="label">{{ t('auth.role') }}</span>
          <div class="grid grid-cols-3 gap-3">
            <button
              type="button"
              class="rounded-xl border px-4 py-3 text-sm font-medium transition-colors"
              :class="role === 'PATIENT' ? 'border-brand-500 bg-brand-50 text-brand-700' : 'border-ink-200 text-ink-600 hover:bg-ink-50'"
              @click="role = 'PATIENT'"
            >
              {{ t('auth.rolePatient') }}
            </button>
            <button
              type="button"
              class="rounded-xl border px-4 py-3 text-sm font-medium transition-colors"
              :class="role === 'DOCTOR' ? 'border-brand-500 bg-brand-50 text-brand-700' : 'border-ink-200 text-ink-600 hover:bg-ink-50'"
              @click="role = 'DOCTOR'"
            >
              {{ t('auth.roleDoctor') }}
            </button>
            <button
              type="button"
              class="rounded-xl border px-4 py-3 text-sm font-medium transition-colors"
              :class="role === 'ADMIN' ? 'border-brand-500 bg-brand-50 text-brand-700' : 'border-ink-200 text-ink-600 hover:bg-ink-50'"
              @click="role = 'ADMIN'"
            >
              {{ t('auth.roleAdmin') }}
            </button>
          </div>
        </div>

        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label class="label" for="name">{{ t('auth.name') }}</label>
            <input id="name" v-model="form.name" class="input" required />
            <p v-if="fieldErrors.name" class="mt-1 text-xs text-rose-600">{{ fieldErrors.name }}</p>
          </div>
          <div>
            <label class="label" for="email">{{ t('auth.email') }}</label>
            <input id="email" v-model="form.email" class="input" type="email" autocomplete="email" required />
            <p v-if="fieldErrors.email" class="mt-1 text-xs text-rose-600">{{ fieldErrors.email }}</p>
          </div>
          <div>
            <label class="label" for="password">{{ t('auth.password') }}</label>
            <input id="password" v-model="form.password" class="input" type="password" autocomplete="new-password" required />
            <p v-if="form.password && !passwordValid" class="mt-1 text-xs text-amber-600">{{ t('auth.passwordHint') }}</p>
            <p v-if="fieldErrors.password" class="mt-1 text-xs text-rose-600">{{ fieldErrors.password }}</p>
          </div>
          <div>
            <label class="label" for="phone">{{ t('auth.phone') }} · {{ t('common.optional') }}</label>
            <input id="phone" v-model="form.phone" class="input" />
          </div>

          <template v-if="role === 'PATIENT'">
            <div>
              <label class="label" for="dob">{{ t('auth.dateOfBirth') }} · {{ t('common.optional') }}</label>
              <input id="dob" v-model="form.dateOfBirth" class="input" type="date" />
            </div>
            <div>
              <label class="label" for="gender">{{ t('auth.gender') }}</label>
              <select id="gender" v-model="form.gender" class="input">
                <option value="UNDISCLOSED">{{ t('auth.genderUndisclosed') }}</option>
                <option value="FEMALE">{{ t('auth.genderFemale') }}</option>
                <option value="MALE">{{ t('auth.genderMale') }}</option>
              </select>
            </div>
          </template>

          <template v-else-if="role === 'DOCTOR'">
            <div>
              <label class="label" for="spec">{{ t('auth.specialization') }}</label>
              <input id="spec" v-model="form.specialization" class="input" required />
              <p v-if="fieldErrors.specialization" class="mt-1 text-xs text-rose-600">{{ fieldErrors.specialization }}</p>
            </div>
            <div>
              <label class="label" for="license">{{ t('auth.licenseNumber') }} · {{ t('common.optional') }}</label>
              <input id="license" v-model="form.licenseNumber" class="input" />
            </div>
            <div>
              <label class="label" for="hospital">{{ t('auth.hospital') }} · {{ t('common.optional') }}</label>
              <input id="hospital" v-model="form.hospital" class="input" />
            </div>
            <div>
              <label class="label" for="dept">{{ t('auth.department') }} · {{ t('common.optional') }}</label>
              <input id="dept" v-model="form.department" class="input" />
            </div>
          </template>

          <template v-else>
            <div class="sm:col-span-2">
              <label class="label" for="setupCode">{{ t('auth.adminSetupCode') }}</label>
              <input id="setupCode" v-model="form.setupCode" class="input" required />
              <p class="mt-1 text-xs text-ink-500">{{ t('auth.adminSetupHint') }}</p>
              <p v-if="fieldErrors.setupCode" class="mt-1 text-xs text-rose-600">{{ fieldErrors.setupCode }}</p>
            </div>
          </template>
        </div>

        <label class="flex items-start gap-3 rounded-xl border border-ink-200 bg-ink-50 p-3 text-sm text-ink-700">
          <input v-model="acknowledge" type="checkbox" class="mt-0.5 h-4 w-4" required />
          <span>{{ t('auth.acknowledge') }}</span>
        </label>
        <p v-if="fieldErrors.acknowledge" class="-mt-3 text-xs text-rose-600">{{ fieldErrors.acknowledge }}</p>

        <p v-if="error" class="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ error }}</p>

        <button class="btn-primary w-full" type="submit" :disabled="auth.loading || !acknowledge">
          {{ auth.loading ? t('common.loading') : t('auth.registerTitle') }}
        </button>

        <p class="text-center text-sm text-ink-500">
          {{ t('auth.haveAccount') }}
          <RouterLink to="/login" class="font-medium text-brand-700 hover:underline">{{ t('nav.signIn') }}</RouterLink>
        </p>
      </form>
    </div>
  </div>
</template>
